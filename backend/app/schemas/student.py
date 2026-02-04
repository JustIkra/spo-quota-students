"""
Pydantic schemas for Student model.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, computed_field


class StudentBase(BaseModel):
    """Base student schema."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    certificate_number: str = Field(..., min_length=1, max_length=50)


class StudentCreate(StudentBase):
    """Schema for creating student."""
    specialty_id: int = Field(..., description="Specialty ID")


class StudentResponse(StudentBase):
    """Schema for student response."""
    id: int
    specialty_id: int
    created_at: datetime

    @computed_field
    @property
    def full_name(self) -> str:
        """Compute full name from name parts for backwards compatibility."""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)

    class Config:
        from_attributes = True


class StudentWithSpecialty(StudentResponse):
    """Schema for student with specialty info."""
    specialty_name: Optional[str] = None
    spo_name: Optional[str] = None
