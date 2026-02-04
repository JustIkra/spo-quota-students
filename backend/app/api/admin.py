"""
Admin API endpoints - SPO, operators, settings management.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db, get_current_admin
from app.models import User, UserRole, SPO, Specialty, Student
from app.schemas import (
    SPOCreate, SPOUpdate, SPOResponse, SPOWithStats,
    UserCreate, UserResponse, UserWithPassword,
    QuotaUpdate, SpecialtyResponse,
    SettingsResponse, SettingsUpdate
)
from app.services import create_operator, reset_password, get_base_quota, set_base_quota


router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ==================== SPO Management ====================

@router.get("/spo", response_model=List[SPOWithStats])
def list_spo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get list of all SPO with statistics.
    Optimized to use aggregated subqueries instead of N+1 queries.
    """
    # Subquery: count specialties per SPO
    specialties_subq = (
        db.query(
            Specialty.spo_id,
            func.count(Specialty.id).label("specialties_count")
        )
        .group_by(Specialty.spo_id)
        .subquery()
    )

    # Subquery: count students per SPO (via specialty)
    students_subq = (
        db.query(
            Specialty.spo_id,
            func.count(Student.id).label("students_count")
        )
        .join(Student, Student.specialty_id == Specialty.id)
        .group_by(Specialty.spo_id)
        .subquery()
    )

    # Subquery: count operators per SPO
    operators_subq = (
        db.query(
            User.spo_id,
            func.count(User.id).label("operators_count")
        )
        .filter(User.role == UserRole.OPERATOR)
        .group_by(User.spo_id)
        .subquery()
    )

    # Main query with all counts in single query
    result = (
        db.query(
            SPO.id,
            SPO.name,
            SPO.created_at,
            func.coalesce(specialties_subq.c.specialties_count, 0).label("specialties_count"),
            func.coalesce(students_subq.c.students_count, 0).label("students_count"),
            func.coalesce(operators_subq.c.operators_count, 0).label("operators_count")
        )
        .outerjoin(specialties_subq, SPO.id == specialties_subq.c.spo_id)
        .outerjoin(students_subq, SPO.id == students_subq.c.spo_id)
        .outerjoin(operators_subq, SPO.id == operators_subq.c.spo_id)
        .all()
    )

    return [
        SPOWithStats(
            id=row.id,
            name=row.name,
            created_at=row.created_at,
            specialties_count=row.specialties_count,
            students_count=row.students_count,
            operators_count=row.operators_count
        )
        for row in result
    ]


@router.post("/spo", response_model=SPOResponse, status_code=status.HTTP_201_CREATED)
def create_spo(
    spo_data: SPOCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create new SPO.
    """
    spo = SPO(name=spo_data.name)
    db.add(spo)
    db.commit()
    db.refresh(spo)
    return spo


@router.get("/spo/{spo_id}", response_model=SPOWithStats)
def get_spo(
    spo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get SPO by ID with statistics.
    """
    spo = db.query(SPO).filter(SPO.id == spo_id).first()
    if not spo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SPO not found"
        )

    specialties_count = db.query(func.count(Specialty.id)).filter(
        Specialty.spo_id == spo.id
    ).scalar()

    students_count = db.query(func.count(Student.id)).join(Specialty).filter(
        Specialty.spo_id == spo.id
    ).scalar()

    operators_count = db.query(func.count(User.id)).filter(
        User.spo_id == spo.id,
        User.role == UserRole.OPERATOR
    ).scalar()

    return SPOWithStats(
        id=spo.id,
        name=spo.name,
        created_at=spo.created_at,
        specialties_count=specialties_count,
        students_count=students_count,
        operators_count=operators_count
    )


@router.put("/spo/{spo_id}", response_model=SPOResponse)
def update_spo(
    spo_id: int,
    spo_data: SPOUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update SPO by ID.
    """
    spo = db.query(SPO).filter(SPO.id == spo_id).first()
    if not spo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SPO not found"
        )

    if spo_data.name is not None:
        spo.name = spo_data.name

    db.commit()
    db.refresh(spo)
    return spo


@router.delete("/spo/{spo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_spo(
    spo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete SPO by ID. Also removes associated specialties, students, and operators.
    """
    spo = db.query(SPO).filter(SPO.id == spo_id).first()
    if not spo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SPO not found"
        )

    # Remove operators assigned to this SPO
    db.query(User).filter(User.spo_id == spo_id).delete()

    # SPO deletion will cascade to specialties and students
    db.delete(spo)
    db.commit()


# ==================== Operators Management ====================

@router.get("/operators", response_model=List[UserResponse])
def list_operators(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get list of all operators.
    """
    operators = db.query(User).filter(User.role == UserRole.OPERATOR).all()
    return operators


@router.post("/operators", response_model=UserWithPassword, status_code=status.HTTP_201_CREATED)
def create_operator_endpoint(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create new operator for SPO. Returns generated login and password.
    """
    # Check if SPO exists
    spo = db.query(SPO).filter(SPO.id == user_data.spo_id).first()
    if not spo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SPO not found"
        )

    # Create operator with generated credentials
    user, password = create_operator(db, user_data.spo_id, spo.name)

    return UserWithPassword(
        id=user.id,
        login=user.login,
        role=user.role,
        spo_id=user.spo_id,
        created_at=user.created_at,
        generated_password=password
    )


@router.delete("/operators/{operator_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_operator(
    operator_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete operator by ID.
    """
    operator = db.query(User).filter(
        User.id == operator_id,
        User.role == UserRole.OPERATOR
    ).first()

    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator not found"
        )

    db.delete(operator)
    db.commit()


@router.post("/operators/{operator_id}/reset-password", response_model=UserWithPassword)
def reset_operator_password(
    operator_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Reset operator password. Returns new generated password.
    """
    operator = db.query(User).filter(
        User.id == operator_id,
        User.role == UserRole.OPERATOR
    ).first()

    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator not found"
        )

    user, password = reset_password(db, operator_id)

    return UserWithPassword(
        id=user.id,
        login=user.login,
        role=user.role,
        spo_id=user.spo_id,
        created_at=user.created_at,
        generated_password=password
    )


# ==================== Specialty Quota Management ====================

@router.put("/specialties/{specialty_id}/quota", response_model=SpecialtyResponse)
def update_specialty_quota(
    specialty_id: int,
    quota_data: QuotaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update specialty quota.
    """
    specialty = db.query(Specialty).filter(Specialty.id == specialty_id).first()
    if not specialty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specialty not found"
        )

    specialty.quota = quota_data.quota
    db.commit()
    db.refresh(specialty)
    return specialty


# ==================== Settings Management ====================

@router.get("/settings", response_model=SettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get application settings.
    """
    base_quota = get_base_quota(db)
    return SettingsResponse(base_quota=base_quota)


@router.put("/settings", response_model=SettingsResponse)
def update_settings(
    settings_data: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update application settings.
    """
    base_quota = set_base_quota(db, settings_data.base_quota)
    return SettingsResponse(base_quota=base_quota)
