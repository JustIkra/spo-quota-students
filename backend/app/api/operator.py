"""
Operator API endpoints - specialties and students management.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db, get_current_operator
from app.models import User, Specialty, Student
from app.schemas import (
    SpecialtyCreate, SpecialtyResponse, SpecialtyWithStats,
    StudentCreate, StudentResponse, StudentWithSpecialty
)
from app.services import get_base_quota


router = APIRouter(prefix="/api", tags=["Operator"])


# ==================== Specialties Management ====================

@router.get("/specialties", response_model=List[SpecialtyWithStats])
def list_specialties(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_operator)
):
    """
    Get list of specialties for operator's SPO.
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
            name=specialty.name,
            quota=specialty.quota,
            created_at=specialty.created_at,
            students_count=students_count,
            available_slots=max(0, specialty.quota - students_count)
        ))

    return result


@router.post("/specialties", response_model=SpecialtyResponse, status_code=status.HTTP_201_CREATED)
def create_specialty(
    specialty_data: SpecialtyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_operator)
):
    """
    Create new specialty for operator's SPO.
    Quota is taken from settings.base_quota.
    """
    base_quota = get_base_quota(db)

    specialty = Specialty(
        spo_id=current_user.spo_id,
        name=specialty_data.name,
        quota=base_quota
    )
    db.add(specialty)
    db.commit()
    db.refresh(specialty)
    return specialty


@router.delete("/specialties/{specialty_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_specialty(
    specialty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_operator)
):
    """
    Delete specialty by ID (only from operator's SPO).
    """
    specialty = db.query(Specialty).filter(
        Specialty.id == specialty_id,
        Specialty.spo_id == current_user.spo_id
    ).first()

    if not specialty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specialty not found or does not belong to your SPO"
        )

    db.delete(specialty)
    db.commit()


# ==================== Students Management ====================

@router.get("/students", response_model=List[StudentWithSpecialty])
def list_students(
    specialty_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_operator)
):
    """
    Get list of students for operator's SPO.
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

    students = query.all()

    result = []
    for student in students:
        specialty = student.specialty
        spo_name = specialty.spo.name if specialty.spo else None

        result.append(StudentWithSpecialty(
            id=student.id,
            specialty_id=student.specialty_id,
            full_name=student.full_name,
            attestat_number=student.attestat_number,
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
    # Verify specialty belongs to operator's SPO
    specialty = db.query(Specialty).filter(
        Specialty.id == student_data.specialty_id,
        Specialty.spo_id == current_user.spo_id
    ).first()

    if not specialty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specialty not found or does not belong to your SPO"
        )

    # Check quota availability
    students_count = db.query(func.count(Student.id)).filter(
        Student.specialty_id == specialty.id
    ).scalar()

    if students_count >= specialty.quota:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Quota exceeded. Current: {students_count}, Quota: {specialty.quota}"
        )

    # Check global uniqueness of attestat_number
    existing_student = db.query(Student).filter(
        Student.attestat_number == student_data.attestat_number
    ).first()

    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student with this attestat number already exists"
        )

    student = Student(
        specialty_id=student_data.specialty_id,
        full_name=student_data.full_name,
        attestat_number=student_data.attestat_number
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
