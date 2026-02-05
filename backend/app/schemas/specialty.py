"""
Pydantic schemas for Specialty model.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SpecialtyBase(BaseModel):
    """Base specialty schema."""
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)


class SpecialtyCreate(SpecialtyBase):
    """Schema for creating specialty (deprecated - use SpecialtyAssign)."""
    pass


class SpecialtyAssign(BaseModel):
    """Schema for assigning specialty template to SPO."""
    template_id: int = Field(..., description="ID шаблона специальности/профессии")
    spo_id: int = Field(..., description="ID учреждения")
    quota: Optional[int] = Field(None, ge=0, description="Квота (если не указана, берётся из настроек)")


class SpecialtyUpdate(BaseModel):
    """Schema for updating specialty."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)


class QuotaUpdate(BaseModel):
    """Schema for updating specialty quota."""
    quota: int = Field(..., ge=0, description="New quota value")


class SpecialtyResponse(SpecialtyBase):
    """Schema for specialty response."""
    id: int
    spo_id: int
    template_id: Optional[int] = None
    quota: int
    created_at: datetime

    class Config:
        from_attributes = True


class SpecialtyWithStats(SpecialtyResponse):
    """Schema for specialty with student count."""
    students_count: int = 0
    available_slots: int = 0
    spo_name: Optional[str] = None
