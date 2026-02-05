"""
Admin API endpoints - SPO, operators, specialty templates, settings management.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db, get_current_admin
from app.models import User, UserRole, SPO, SpecialtyTemplate, Specialty, Student
from app.schemas import (
    SPOCreate, SPOUpdate, SPOResponse, SPOWithStats,
    UserCreate, UserResponse, UserWithPassword,
    SpecialtyTemplateCreate, SpecialtyTemplateUpdate, SpecialtyTemplateResponse, SpecialtyTemplateWithUsage,
    SpecialtyAssign, QuotaUpdate, SpecialtyResponse, SpecialtyWithStats,
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
    Each SPO can have only one operator.
    """
    # Check if SPO exists
    spo = db.query(SPO).filter(SPO.id == user_data.spo_id).first()
    if not spo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Учреждение не найдено"
        )

    # Check if SPO already has an operator
    existing_operator = db.query(User).filter(
        User.spo_id == user_data.spo_id,
        User.role == UserRole.OPERATOR
    ).first()
    if existing_operator:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="У этого учреждения уже есть оператор"
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


# ==================== Specialty Templates (Catalog) Management ====================

@router.get("/specialty-templates", response_model=List[SpecialtyTemplateWithUsage])
def list_specialty_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get list of all specialty templates with usage count.
    """
    # Subquery: count SPOs using each template
    usage_subq = (
        db.query(
            Specialty.template_id,
            func.count(func.distinct(Specialty.spo_id)).label("spo_count")
        )
        .filter(Specialty.template_id.isnot(None))
        .group_by(Specialty.template_id)
        .subquery()
    )

    result = (
        db.query(
            SpecialtyTemplate.id,
            SpecialtyTemplate.code,
            SpecialtyTemplate.name,
            SpecialtyTemplate.created_at,
            func.coalesce(usage_subq.c.spo_count, 0).label("spo_count")
        )
        .outerjoin(usage_subq, SpecialtyTemplate.id == usage_subq.c.template_id)
        .order_by(SpecialtyTemplate.code)
        .all()
    )

    return [
        SpecialtyTemplateWithUsage(
            id=row.id,
            code=row.code,
            name=row.name,
            created_at=row.created_at,
            spo_count=row.spo_count
        )
        for row in result
    ]


@router.post("/specialty-templates", response_model=SpecialtyTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_specialty_template(
    template_data: SpecialtyTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create new specialty template in the global catalog.
    """
    # Check for duplicate code
    existing = db.query(SpecialtyTemplate).filter(
        SpecialtyTemplate.code == template_data.code
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Специальность/профессия с кодом '{template_data.code}' уже существует"
        )

    template = SpecialtyTemplate(
        code=template_data.code,
        name=template_data.name
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.put("/specialty-templates/{template_id}", response_model=SpecialtyTemplateResponse)
def update_specialty_template(
    template_id: int,
    template_data: SpecialtyTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update specialty template.
    """
    template = db.query(SpecialtyTemplate).filter(SpecialtyTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Специальность/профессия не найдена в справочнике"
        )

    if template_data.code is not None:
        # Check for duplicate code
        existing = db.query(SpecialtyTemplate).filter(
            SpecialtyTemplate.code == template_data.code,
            SpecialtyTemplate.id != template_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Специальность/профессия с кодом '{template_data.code}' уже существует"
            )
        template.code = template_data.code

    if template_data.name is not None:
        template.name = template_data.name

    # Update all assigned specialties to sync name/code
    if template_data.code is not None or template_data.name is not None:
        db.query(Specialty).filter(Specialty.template_id == template_id).update({
            Specialty.code: template.code,
            Specialty.name: template.name
        })

    db.commit()
    db.refresh(template)
    return template


@router.delete("/specialty-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_specialty_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete specialty template. Also removes all assignments to SPOs (and their students).
    """
    template = db.query(SpecialtyTemplate).filter(SpecialtyTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Специальность/профессия не найдена в справочнике"
        )

    db.delete(template)
    db.commit()


# ==================== Specialties Assignment Management ====================

@router.get("/specialties", response_model=List[SpecialtyWithStats])
def list_all_specialties(
    spo_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get list of all assigned specialties with stats.
    Optionally filter by spo_id.
    """
    query = db.query(Specialty)
    if spo_id is not None:
        query = query.filter(Specialty.spo_id == spo_id)

    specialties = query.all()

    result = []
    for specialty in specialties:
        students_count = db.query(func.count(Student.id)).filter(
            Student.specialty_id == specialty.id
        ).scalar()

        spo_name = specialty.spo.name if specialty.spo else None

        result.append(SpecialtyWithStats(
            id=specialty.id,
            spo_id=specialty.spo_id,
            template_id=specialty.template_id,
            code=specialty.code,
            name=specialty.name,
            quota=specialty.quota,
            created_at=specialty.created_at,
            students_count=students_count,
            available_slots=max(0, specialty.quota - students_count),
            spo_name=spo_name
        ))

    return result


@router.post("/specialties", response_model=SpecialtyResponse, status_code=status.HTTP_201_CREATED)
def assign_specialty_to_spo(
    data: SpecialtyAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Assign specialty template to SPO with quota.
    """
    # Check template exists
    template = db.query(SpecialtyTemplate).filter(SpecialtyTemplate.id == data.template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Специальность/профессия не найдена в справочнике"
        )

    # Check SPO exists
    spo = db.query(SPO).filter(SPO.id == data.spo_id).first()
    if not spo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Учреждение не найдено"
        )

    # Check if already assigned
    existing = db.query(Specialty).filter(
        Specialty.spo_id == data.spo_id,
        Specialty.template_id == data.template_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Эта специальность/профессия уже прикреплена к данному учреждению"
        )

    # Get quota from settings if not provided
    quota = data.quota if data.quota is not None else get_base_quota(db)

    specialty = Specialty(
        spo_id=data.spo_id,
        template_id=data.template_id,
        code=template.code,
        name=template.name,
        quota=quota
    )
    db.add(specialty)
    db.commit()
    db.refresh(specialty)
    return specialty


@router.delete("/specialties/{specialty_id}", status_code=status.HTTP_204_NO_CONTENT)
def unassign_specialty_from_spo(
    specialty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Remove specialty assignment from SPO. Also deletes all students in this specialty.
    """
    specialty = db.query(Specialty).filter(Specialty.id == specialty_id).first()
    if not specialty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Специальность/профессия не найдена"
        )

    db.delete(specialty)
    db.commit()
