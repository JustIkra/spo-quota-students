"""
Pydantic schemas for Student model.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class StudentBase(BaseModel):
    """Base student schema."""
    full_name: str = Field(..., min_length=1, max_length=255)
    attestat_number: str = Field(..., min_length=1, max_length=50)


class StudentCreate(StudentBase):
    """Schema for creating student."""
    specialty_id: int = Field(..., description="Specialty ID")


class StudentResponse(StudentBase):
    """Schema for student response."""
    id: int
    specialty_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class StudentWithSpecialty(StudentResponse):
    """Schema for student with specialty info."""
    specialty_name: Optional[str] = None
    spo_name: Optional[str] = None
