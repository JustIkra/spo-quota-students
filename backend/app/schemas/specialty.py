"""
Pydantic schemas for Specialty model.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SpecialtyBase(BaseModel):
    """Base specialty schema."""
    name: str = Field(..., min_length=1, max_length=255)


class SpecialtyCreate(SpecialtyBase):
    """Schema for creating specialty."""
    pass


class SpecialtyUpdate(BaseModel):
    """Schema for updating specialty."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class QuotaUpdate(BaseModel):
    """Schema for updating specialty quota."""
    quota: int = Field(..., ge=0, description="New quota value")


class SpecialtyResponse(SpecialtyBase):
    """Schema for specialty response."""
    id: int
    spo_id: int
    quota: int
    created_at: datetime

    class Config:
        from_attributes = True


class SpecialtyWithStats(SpecialtyResponse):
    """Schema for specialty with student count."""
    students_count: int = 0
    available_slots: int = 0
