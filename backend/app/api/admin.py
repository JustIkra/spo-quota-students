"""
Admin API endpoints - SPO, operators, specialty templates, settings management.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.core.cache import cached, invalidate


router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ==================== SPO Management ====================

@router.get("/spo", response_model=List[SPOWithStats])
@cached("admin:spo")
async def list_spo(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get list of all SPO with statistics.
    Optimized to use aggregated subqueries instead of N+1 queries.
    """
    # Subquery: count specialties per SPO
    specialties_subq = (
        select(
            Specialty.spo_id,
            func.count(Specialty.id).label("specialties_count")
        )
        .group_by(Specialty.spo_id)
        .subquery()
    )

    # Subquery: count students per SPO (via specialty)
    students_subq = (
        select(
            Specialty.spo_id,
            func.count(Student.id).label("students_count")
        )
        .join(Student, Student.specialty_id == Specialty.id)
        .group_by(Specialty.spo_id)
        .subquery()
    )

    # Subquery: count operators per SPO
    operators_subq = (
        select(
            User.spo_id,
            func.count(User.id).label("operators_count")
        )
        .where(User.role == UserRole.OPERATOR)
        .group_by(User.spo_id)
        .subquery()
    )

    # Main query with all counts in single query
    stmt = (
        select(
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
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        SPOWithStats(
            id=row.id,
            name=row.name,
            created_at=row.created_at,
            specialties_count=row.specialties_count,
            students_count=row.students_count,
            operators_count=row.operators_count
        )
        for row in rows
    ]


@router.post("/spo", response_model=SPOResponse, status_code=status.HTTP_201_CREATED)
async def create_spo(
    spo_data: SPOCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create new SPO.
    """
    spo = SPO(name=spo_data.name)
    db.add(spo)
    await db.commit()
    await db.refresh(spo)
    await invalidate("admin:spo", "stats")
    return spo


@router.get("/spo/{spo_id}", response_model=SPOWithStats)
async def get_spo(
    spo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get SPO by ID with statistics.
    """
    result = await db.execute(select(SPO).where(SPO.id == spo_id))
    spo = result.scalars().first()
    if not spo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SPO not found"
        )

    spec_count_result = await db.execute(
        select(func.count(Specialty.id)).where(Specialty.spo_id == spo.id)
    )
    specialties_count = spec_count_result.scalar()

    stud_count_result = await db.execute(
        select(func.count(Student.id)).join(Specialty).where(Specialty.spo_id == spo.id)
    )
    students_count = stud_count_result.scalar()

    op_count_result = await db.execute(
        select(func.count(User.id)).where(User.spo_id == spo.id, User.role == UserRole.OPERATOR)
    )
    operators_count = op_count_result.scalar()

    return SPOWithStats(
        id=spo.id,
        name=spo.name,
        created_at=spo.created_at,
        specialties_count=specialties_count,
        students_count=students_count,
        operators_count=operators_count
    )


@router.put("/spo/{spo_id}", response_model=SPOResponse)
async def update_spo(
    spo_id: int,
    spo_data: SPOUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update SPO by ID.
    """
    result = await db.execute(select(SPO).where(SPO.id == spo_id))
    spo = result.scalars().first()
    if not spo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SPO not found"
        )

    if spo_data.name is not None:
        spo.name = spo_data.name

    await db.commit()
    await db.refresh(spo)
    await invalidate("admin:spo", "stats")
    return spo


@router.delete("/spo/{spo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_spo(
    spo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete SPO by ID. Also removes associated specialties, students, and operators.
    """
    result = await db.execute(select(SPO).where(SPO.id == spo_id))
    spo = result.scalars().first()
    if not spo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SPO not found"
        )

    # Remove operators assigned to this SPO
    await db.execute(delete(User).where(User.spo_id == spo_id))

    # SPO deletion will cascade to specialties and students
    await db.delete(spo)
    await db.commit()
    await invalidate("admin:spo", "stats")


# ==================== Operators Management ====================

@router.get("/operators", response_model=List[UserResponse])
async def list_operators(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get list of all operators.
    """
    result = await db.execute(select(User).where(User.role == UserRole.OPERATOR))
    operators = result.scalars().all()
    return operators


@router.post("/operators", response_model=UserWithPassword, status_code=status.HTTP_201_CREATED)
async def create_operator_endpoint(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create new operator for SPO. Returns generated login and password.
    Each SPO can have only one operator.
    """
    # Check if SPO exists
    result = await db.execute(select(SPO).where(SPO.id == user_data.spo_id))
    spo = result.scalars().first()
    if not spo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Учреждение не найдено"
        )

    # Check if SPO already has an operator
    result = await db.execute(
        select(User).where(User.spo_id == user_data.spo_id, User.role == UserRole.OPERATOR)
    )
    existing_operator = result.scalars().first()
    if existing_operator:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="У этого учреждения уже есть оператор"
        )

    # Create operator with generated credentials
    user, password = await create_operator(db, user_data.spo_id, spo.name)

    await invalidate("admin:spo")
    return UserWithPassword(
        id=user.id,
        login=user.login,
        role=user.role,
        spo_id=user.spo_id,
        created_at=user.created_at,
        generated_password=password
    )


@router.delete("/operators/{operator_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_operator(
    operator_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete operator by ID.
    """
    result = await db.execute(
        select(User).where(User.id == operator_id, User.role == UserRole.OPERATOR)
    )
    operator = result.scalars().first()

    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator not found"
        )

    await db.delete(operator)
    await db.commit()
    await invalidate("admin:spo")


@router.post("/operators/{operator_id}/reset-password", response_model=UserWithPassword)
async def reset_operator_password(
    operator_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Reset operator password. Returns new generated password.
    """
    result = await db.execute(
        select(User).where(User.id == operator_id, User.role == UserRole.OPERATOR)
    )
    operator = result.scalars().first()

    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operator not found"
        )

    user, password = await reset_password(db, operator_id)

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
async def update_specialty_quota(
    specialty_id: int,
    quota_data: QuotaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update specialty quota.
    """
    result = await db.execute(select(Specialty).where(Specialty.id == specialty_id))
    specialty = result.scalars().first()
    if not specialty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specialty not found"
        )

    specialty.quota = quota_data.quota
    await db.commit()
    await db.refresh(specialty)
    await invalidate("admin:specialties", "op:specialties", "stats")
    return specialty


# ==================== Settings Management ====================

@router.get("/settings", response_model=SettingsResponse)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get application settings.
    """
    base_quota = await get_base_quota(db)
    return SettingsResponse(base_quota=base_quota)


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(
    settings_data: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update application settings.
    """
    base_quota = await set_base_quota(db, settings_data.base_quota)
    await invalidate("stats")
    return SettingsResponse(base_quota=base_quota)


# ==================== Specialty Templates (Catalog) Management ====================

@router.get("/specialty-templates", response_model=List[SpecialtyTemplateWithUsage])
@cached("admin:templates", ttl=600)
async def list_specialty_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get list of all specialty templates with usage count.
    """
    # Get all templates
    result = await db.execute(select(SpecialtyTemplate).order_by(SpecialtyTemplate.code))
    templates = result.scalars().all()

    # Get SPO names grouped by template_id
    stmt = (
        select(Specialty.template_id, SPO.name)
        .join(SPO, Specialty.spo_id == SPO.id)
        .where(Specialty.template_id.isnot(None))
        .distinct()
    )
    result = await db.execute(stmt)
    spo_by_template = result.all()

    # Build mapping: template_id -> list of SPO names
    spo_names_map = {}
    for template_id, spo_name in spo_by_template:
        spo_names_map.setdefault(template_id, []).append(spo_name)

    return [
        SpecialtyTemplateWithUsage(
            id=t.id,
            code=t.code,
            name=t.name,
            created_at=t.created_at,
            spo_count=len(spo_names_map.get(t.id, [])),
            spo_names=sorted(spo_names_map.get(t.id, []))
        )
        for t in templates
    ]


@router.post("/specialty-templates", response_model=SpecialtyTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_specialty_template(
    template_data: SpecialtyTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create new specialty template in the global catalog.
    """
    # Check for duplicate code
    result = await db.execute(
        select(SpecialtyTemplate).where(SpecialtyTemplate.code == template_data.code)
    )
    existing = result.scalars().first()
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
    await db.commit()
    await db.refresh(template)
    await invalidate("admin:templates")
    return template


@router.put("/specialty-templates/{template_id}", response_model=SpecialtyTemplateResponse)
async def update_specialty_template(
    template_id: int,
    template_data: SpecialtyTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update specialty template.
    """
    result = await db.execute(select(SpecialtyTemplate).where(SpecialtyTemplate.id == template_id))
    template = result.scalars().first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Специальность/профессия не найдена в справочнике"
        )

    if template_data.code is not None:
        # Check for duplicate code
        result = await db.execute(
            select(SpecialtyTemplate).where(
                SpecialtyTemplate.code == template_data.code,
                SpecialtyTemplate.id != template_id
            )
        )
        existing = result.scalars().first()
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
        await db.execute(
            update(Specialty)
            .where(Specialty.template_id == template_id)
            .values(code=template.code, name=template.name)
        )

    await db.commit()
    await db.refresh(template)
    await invalidate("admin:templates", "admin:specialties", "op:specialties", "stats")
    return template


@router.delete("/specialty-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_specialty_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Delete specialty template. Also removes all assignments to SPOs (and their students).
    """
    result = await db.execute(select(SpecialtyTemplate).where(SpecialtyTemplate.id == template_id))
    template = result.scalars().first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Специальность/профессия не найдена в справочнике"
        )

    await db.delete(template)
    await db.commit()
    await invalidate("admin:templates", "admin:specialties", "op:specialties", "stats", "admin:spo")


# ==================== Specialties Assignment Management ====================

@router.get("/specialties", response_model=List[SpecialtyWithStats])
@cached("admin:specialties")
async def list_all_specialties(
    spo_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Get list of all assigned specialties with stats.
    Optionally filter by spo_id.
    """
    stmt = select(Specialty)
    if spo_id is not None:
        stmt = stmt.where(Specialty.spo_id == spo_id)

    result = await db.execute(stmt)
    specialties = result.scalars().all()

    items = []
    for specialty in specialties:
        count_result = await db.execute(
            select(func.count(Student.id)).where(Student.specialty_id == specialty.id)
        )
        students_count = count_result.scalar()

        # Load SPO name explicitly to avoid lazy loading
        spo_result = await db.execute(select(SPO.name).where(SPO.id == specialty.spo_id))
        spo_name = spo_result.scalar()

        items.append(SpecialtyWithStats(
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

    return items


@router.post("/specialties", response_model=SpecialtyResponse, status_code=status.HTTP_201_CREATED)
async def assign_specialty_to_spo(
    data: SpecialtyAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Assign specialty template to SPO with quota.
    """
    # Check template exists
    result = await db.execute(select(SpecialtyTemplate).where(SpecialtyTemplate.id == data.template_id))
    template = result.scalars().first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Специальность/профессия не найдена в справочнике"
        )

    # Check SPO exists
    result = await db.execute(select(SPO).where(SPO.id == data.spo_id))
    spo = result.scalars().first()
    if not spo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Учреждение не найдено"
        )

    # Check if already assigned
    result = await db.execute(
        select(Specialty).where(Specialty.spo_id == data.spo_id, Specialty.template_id == data.template_id)
    )
    existing = result.scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Эта специальность/профессия уже прикреплена к данному учреждению"
        )

    # Get quota from settings if not provided
    quota = data.quota if data.quota is not None else await get_base_quota(db)

    specialty = Specialty(
        spo_id=data.spo_id,
        template_id=data.template_id,
        code=template.code,
        name=template.name,
        quota=quota
    )
    db.add(specialty)
    await db.commit()
    await db.refresh(specialty)
    await invalidate("admin:specialties", "op:specialties", "stats", "admin:spo")
    return specialty


@router.delete("/specialties/{specialty_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unassign_specialty_from_spo(
    specialty_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Remove specialty assignment from SPO. Also deletes all students in this specialty.
    """
    result = await db.execute(select(Specialty).where(Specialty.id == specialty_id))
    specialty = result.scalars().first()
    if not specialty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Специальность/профессия не найдена"
        )

    await db.delete(specialty)
    await db.commit()
    await invalidate("admin:specialties", "op:specialties", "stats", "admin:spo")
