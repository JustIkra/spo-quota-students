"""
Operator API endpoints - specialties viewing and students management.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db, get_current_operator
from app.models import User, Specialty, Student
from app.schemas import (
    SpecialtyWithStats,
    StudentCreate, StudentResponse, StudentWithSpecialty
)


router = APIRouter(prefix="/api", tags=["Operator"])


# ==================== Specialties Viewing (Read-Only) ====================

@router.get("/specialties", response_model=List[SpecialtyWithStats])
def list_specialties(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_operator)
):
    """
    Get list of specialties assigned to operator's SPO (read-only).
    Specialty management is done by admin.
    """
    specialties = db.query(Specialty).filter(
        Specialty.spo_id == current_user.spo_id
    ).all()

    result = []
    for specialty in specialties:
        students_count = db.query(func.count(Student.id)).filter(
            Student.specialty_id == specialty.id
        ).scalar()

        result.append(SpecialtyWithStats(
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

    return result


# ==================== Students Management ====================

@router.get("/students", response_model=List[StudentWithSpecialty])
def list_students(
    specialty_id: Optional[int] = None,
    skip: int = Query(0, ge=0, description="Number of records to skip (pagination)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_operator)
):
    """
    Get list of students for operator's SPO.
    Supports pagination with skip/limit parameters.
    Optional filter by specialty_id.
    """
    # Get all specialties of operator's SPO
    spo_specialty_ids = db.query(Specialty.id).filter(
        Specialty.spo_id == current_user.spo_id
    ).subquery()

    query = db.query(Student).filter(
        Student.specialty_id.in_(spo_specialty_ids)
    )

    if specialty_id is not None:
        # Verify specialty belongs to operator's SPO
        specialty = db.query(Specialty).filter(
            Specialty.id == specialty_id,
            Specialty.spo_id == current_user.spo_id
        ).first()
        if not specialty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specialty not found or does not belong to your SPO"
            )
        query = query.filter(Student.specialty_id == specialty_id)

    # Apply pagination (SUGGEST-001)
    students = query.offset(skip).limit(limit).all()

    result = []
    for student in students:
        specialty = student.specialty
        spo_name = specialty.spo.name if specialty.spo else None

        result.append(StudentWithSpecialty(
            id=student.id,
            specialty_id=student.specialty_id,
            first_name=student.first_name,
            last_name=student.last_name,
            middle_name=student.middle_name,
            certificate_number=student.certificate_number,
            created_at=student.created_at,
            specialty_name=specialty.name,
            spo_name=spo_name
        ))

    return result


@router.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_operator)
):
    """
    Create new student in a specialty.
    - Specialty must belong to operator's SPO
    - Attestat number must be globally unique
    - Must have available quota slots
    """
    # Lock the specialty row with FOR UPDATE to prevent race conditions (TOCTOU)
    # This ensures the quota check and insert are atomic within the transaction
    specialty = db.query(Specialty).filter(
        Specialty.id == student_data.specialty_id,
        Specialty.spo_id == current_user.spo_id
    ).with_for_update().first()

    if not specialty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specialty not found or does not belong to your SPO"
        )

    # Check quota availability (now safe from race conditions due to row lock)
    students_count = db.query(func.count(Student.id)).filter(
        Student.specialty_id == specialty.id
    ).scalar()

    if students_count >= specialty.quota:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Quota exceeded. Current: {students_count}, Quota: {specialty.quota}"
        )

    # Check global uniqueness of certificate_number
    existing_student = db.query(Student).filter(
        Student.certificate_number == student_data.certificate_number
    ).first()

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
    db.commit()
    db.refresh(student)
    return student


@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_operator)
):
    """
    Delete student by ID (only from operator's SPO).
    """
    # Get all specialties of operator's SPO
    spo_specialty_ids = db.query(Specialty.id).filter(
        Specialty.spo_id == current_user.spo_id
    ).subquery()

    student = db.query(Student).filter(
        Student.id == student_id,
        Student.specialty_id.in_(spo_specialty_ids)
    ).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or does not belong to your SPO"
        )

    db.delete(student)
    db.commit()
