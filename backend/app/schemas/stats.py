"""
Pydantic schemas for statistics.
"""
from typing import List, Optional

from pydantic import BaseModel


class SpecialtyStats(BaseModel):
    """Statistics for a single specialty."""
    specialty_id: int
    specialty_name: str
    specialty_code: Optional[str] = None
    spo_id: int
    spo_name: str
    quota: int
    students_count: int
    available_slots: int


class SPOStats(BaseModel):
    """Statistics for a single SPO."""
    spo_id: int
    spo_name: str
    total_quota: int
    total_students: int
    specialties: List[SpecialtyStats]


class OverallStats(BaseModel):
    """Overall statistics response."""
    total_spo: int
    total_specialties: int
    total_students: int
    total_quota: int
    spo_list: List[SPOStats]
