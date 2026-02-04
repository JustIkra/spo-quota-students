"""
Statistics API endpoints.
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
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

    Optimized to avoid N+1 queries using aggregated subqueries.
    """
    # Build base SPO filter
    spo_filter = SPO.id == current_user.spo_id if current_user.role != UserRole.ADMIN else True

    # Subquery: count students per specialty
    students_per_specialty = (
        db.query(
            Student.specialty_id,
            func.count(Student.id).label("students_count")
        )
        .group_by(Student.specialty_id)
        .subquery()
    )

    # Main query: get specialties with student counts in a single query
    specialties_with_counts = (
        db.query(
            Specialty.id,
            Specialty.spo_id,
            Specialty.name,
            Specialty.code,
            Specialty.quota,
            SPO.name.label("spo_name"),
            func.coalesce(students_per_specialty.c.students_count, 0).label("students_count")
        )
        .join(SPO, Specialty.spo_id == SPO.id)
        .outerjoin(students_per_specialty, Specialty.id == students_per_specialty.c.specialty_id)
        .filter(spo_filter)
        .all()
    )

    # Group by SPO
    spo_data: dict = {}
    for row in specialties_with_counts:
        spo_id = row.spo_id
        if spo_id not in spo_data:
            spo_data[spo_id] = {
                "spo_id": spo_id,
                "spo_name": row.spo_name,
                "total_quota": 0,
                "total_students": 0,
                "specialties": []
            }

        students_count = row.students_count or 0
        spo_data[spo_id]["total_quota"] += row.quota
        spo_data[spo_id]["total_students"] += students_count
        spo_data[spo_id]["specialties"].append(
            SpecialtyStats(
                specialty_id=row.id,
                specialty_name=row.name,
                specialty_code=row.code,
                spo_id=spo_id,
                spo_name=row.spo_name,
                quota=row.quota,
                students_count=students_count,
                available_slots=max(0, row.quota - students_count)
            )
        )

    # Also include SPOs without specialties
    if current_user.role == UserRole.ADMIN:
        all_spo = db.query(SPO).all()
    else:
        all_spo = db.query(SPO).filter(SPO.id == current_user.spo_id).all()

    for spo in all_spo:
        if spo.id not in spo_data:
            spo_data[spo.id] = {
                "spo_id": spo.id,
                "spo_name": spo.name,
                "total_quota": 0,
                "total_students": 0,
                "specialties": []
            }

    # Build response
    result_spo_list = [
        SPOStats(
            spo_id=data["spo_id"],
            spo_name=data["spo_name"],
            total_quota=data["total_quota"],
            total_students=data["total_students"],
            specialties=data["specialties"]
        )
        for data in spo_data.values()
    ]

    total_spo = len(result_spo_list)
    total_specialties = sum(len(spo.specialties) for spo in result_spo_list)
    total_students = sum(spo.total_students for spo in result_spo_list)
    total_quota = sum(spo.total_quota for spo in result_spo_list)

    return OverallStats(
        total_spo=total_spo,
        total_specialties=total_specialties,
        total_students=total_students,
        total_quota=total_quota,
        spo_list=result_spo_list
    )
