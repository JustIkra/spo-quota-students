"""
Statistics API endpoints.
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_db, get_current_user
from app.models import User, UserRole, SPO, Specialty, Student
from app.schemas import SpecialtyStats, SPOStats, OverallStats


router = APIRouter(prefix="/api", tags=["Statistics"])


@router.get("/stats", response_model=OverallStats)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics about quotas and enrolled students.
    - Admin sees all SPO
    - Operator sees only their SPO
    """
    # Filter SPO based on user role
    if current_user.role == UserRole.ADMIN:
        spo_list = db.query(SPO).all()
    else:
        # Operator sees only their SPO
        spo_list = db.query(SPO).filter(SPO.id == current_user.spo_id).all()

    result_spo_list: List[SPOStats] = []
    total_spo = len(spo_list)
    total_specialties = 0
    total_students = 0
    total_quota = 0

    for spo in spo_list:
        specialties = db.query(Specialty).filter(Specialty.spo_id == spo.id).all()
        spo_total_quota = 0
        spo_total_students = 0
        specialty_stats_list: List[SpecialtyStats] = []

        for specialty in specialties:
            students_count = db.query(func.count(Student.id)).filter(
                Student.specialty_id == specialty.id
            ).scalar()

            specialty_stats = SpecialtyStats(
                specialty_id=specialty.id,
                specialty_name=specialty.name,
                spo_id=spo.id,
                spo_name=spo.name,
                quota=specialty.quota,
                students_count=students_count,
                available_slots=max(0, specialty.quota - students_count)
            )
            specialty_stats_list.append(specialty_stats)

            spo_total_quota += specialty.quota
            spo_total_students += students_count

        spo_stats = SPOStats(
            spo_id=spo.id,
            spo_name=spo.name,
            total_quota=spo_total_quota,
            total_students=spo_total_students,
            specialties=specialty_stats_list
        )
        result_spo_list.append(spo_stats)

        total_specialties += len(specialties)
        total_students += spo_total_students
        total_quota += spo_total_quota

    return OverallStats(
        total_spo=total_spo,
        total_specialties=total_specialties,
        total_students=total_students,
        total_quota=total_quota,
        spo_list=result_spo_list
    )
