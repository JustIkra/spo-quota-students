"""
Operator API endpoints - specialties viewing and students management.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_operator
from app.models import User, Specialty, Student, SPO
from app.schemas import (
    SpecialtyWithStats,
    StudentCreate, StudentUpdate, StudentResponse, StudentWithSpecialty
)
from app.core.cache import cached, invalidate


router = APIRouter(prefix="/api", tags=["Operator"])


# ==================== Specialties Viewing (Read-Only) ====================

@router.get("/specialties", response_model=List[SpecialtyWithStats])
@cached("op:specialties")
async def list_specialties(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_operator)
):
    """
    Get list of specialties assigned to operator's SPO (read-only).
    Specialty management is done by admin.
    """
    result = await db.execute(
        select(Specialty).where(Specialty.spo_id == current_user.spo_id)
    )
    specialties = result.scalars().all()

    items = []
    for specialty in specialties:
        count_result = await db.execute(
            select(func.count(Student.id)).where(Student.specialty_id == specialty.id)
        )
        students_count = count_result.scalar()

        items.append(SpecialtyWithStats(
            id=specialty.id,
            spo_id=specialty.spo_id,
            template_id=specialty.template_id,
            code=specialty.code,
            name=specialty.name,
            quota=specialty.quota,
            created_at=specialty.created_at,
            students_count=students_count,
            available_slots=max(0, specialty.quota - students_count)
        ))

    return items


# ==================== Students Management ====================

@router.get("/students", response_model=List[StudentWithSpecialty])
@cached("op:students", ttl=120)
async def list_students(
    specialty_id: Optional[int] = None,
    skip: int = Query(0, ge=0, description="Number of records to skip (pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_operator)
):
    """
    Get list of students for operator's SPO.
    Supports pagination with skip/limit parameters.
    Optional filter by specialty_id.
    """
    # Get all specialties of operator's SPO
    spo_specialty_ids = select(Specialty.id).where(Specialty.spo_id == current_user.spo_id)

    stmt = select(Student).where(Student.specialty_id.in_(spo_specialty_ids))

    if specialty_id is not None:
        # Verify specialty belongs to operator's SPO
        spec_result = await db.execute(
            select(Specialty).where(
                Specialty.id == specialty_id,
                Specialty.spo_id == current_user.spo_id
            )
        )
        specialty = spec_result.scalars().first()
        if not specialty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specialty not found or does not belong to your SPO"
            )
        stmt = select(Student).where(Student.specialty_id == specialty_id)

    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    students = result.scalars().all()

    items = []
    for student in students:
        # Load specialty and SPO explicitly
        spec_result = await db.execute(
            select(Specialty).where(Specialty.id == student.specialty_id)
        )
        specialty = spec_result.scalars().first()

        spo_name = None
        if specialty:
            spo_result = await db.execute(select(SPO.name).where(SPO.id == specialty.spo_id))
            spo_name = spo_result.scalar()

        items.append(StudentWithSpecialty(
            id=student.id,
            specialty_id=student.specialty_id,
            first_name=student.first_name,
            last_name=student.last_name,
            middle_name=student.middle_name,
            certificate_number=student.certificate_number,
            created_at=student.created_at,
            specialty_name=specialty.name if specialty else None,
            spo_name=spo_name
        ))

    return items


@router.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: StudentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_operator)
):
    """
    Create new student in a specialty.
    - Specialty must belong to operator's SPO
    - Attestat number must be globally unique
    - Must have available quota slots
    """
    # Lock the specialty row with FOR UPDATE to prevent race conditions (TOCTOU)
    result = await db.execute(
        select(Specialty)
        .where(Specialty.id == student_data.specialty_id, Specialty.spo_id == current_user.spo_id)
        .with_for_update()
    )
    specialty = result.scalars().first()

    if not specialty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specialty not found or does not belong to your SPO"
        )

    # Check quota availability (now safe from race conditions due to row lock)
    count_result = await db.execute(
        select(func.count(Student.id)).where(Student.specialty_id == specialty.id)
    )
    students_count = count_result.scalar()

    if students_count >= specialty.quota:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Quota exceeded. Current: {students_count}, Quota: {specialty.quota}"
        )

    # Check global uniqueness of certificate_number
    existing_result = await db.execute(
        select(Student).where(Student.certificate_number == student_data.certificate_number)
    )
    existing_student = existing_result.scalars().first()

    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Студент с таким номером аттестата уже зарегистрирован в системе"
        )

    student = Student(
        specialty_id=student_data.specialty_id,
        first_name=student_data.first_name,
        last_name=student_data.last_name,
        middle_name=student_data.middle_name,
        certificate_number=student_data.certificate_number
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)
    await invalidate("op:students", "op:specialties", "stats", "admin:spo")
    return student


@router.put("/students/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    student_data: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_operator)
):
    """
    Update student by ID (only from operator's SPO).
    - If changing specialty, new specialty must belong to operator's SPO
    - If changing certificate_number, must remain globally unique
    """
    # Get all specialties of operator's SPO
    spo_specialty_ids = select(Specialty.id).where(Specialty.spo_id == current_user.spo_id)

    result = await db.execute(
        select(Student).where(
            Student.id == student_id,
            Student.specialty_id.in_(spo_specialty_ids)
        )
    )
    student = result.scalars().first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or does not belong to your SPO"
        )

    update_data = student_data.model_dump(exclude_unset=True)

    # If changing specialty, verify it belongs to operator's SPO and has quota
    if 'specialty_id' in update_data and update_data['specialty_id'] != student.specialty_id:
        new_spec_result = await db.execute(
            select(Specialty)
            .where(Specialty.id == update_data['specialty_id'], Specialty.spo_id == current_user.spo_id)
            .with_for_update()
        )
        new_specialty = new_spec_result.scalars().first()

        if not new_specialty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specialty not found or does not belong to your SPO"
            )

        count_result = await db.execute(
            select(func.count(Student.id)).where(Student.specialty_id == new_specialty.id)
        )
        students_count = count_result.scalar()

        if students_count >= new_specialty.quota:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Quota exceeded. Current: {students_count}, Quota: {new_specialty.quota}"
            )

    # If changing certificate_number, check global uniqueness
    if 'certificate_number' in update_data and update_data['certificate_number'] != student.certificate_number:
        existing_result = await db.execute(
            select(Student).where(
                Student.certificate_number == update_data['certificate_number'],
                Student.id != student_id
            )
        )
        existing = existing_result.scalars().first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Студент с таким номером аттестата уже зарегистрирован в системе"
            )

    for key, value in update_data.items():
        setattr(student, key, value)

    await db.commit()
    await db.refresh(student)
    await invalidate("op:students", "op:specialties", "stats", "admin:spo")
    return student


@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_operator)
):
    """
    Delete student by ID (only from operator's SPO).
    """
    # Get all specialties of operator's SPO
    spo_specialty_ids = select(Specialty.id).where(Specialty.spo_id == current_user.spo_id)

    result = await db.execute(
        select(Student).where(
            Student.id == student_id,
            Student.specialty_id.in_(spo_specialty_ids)
        )
    )
    student = result.scalars().first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or does not belong to your SPO"
        )

    await db.delete(student)
    await db.commit()
    await invalidate("op:students", "op:specialties", "stats", "admin:spo")
