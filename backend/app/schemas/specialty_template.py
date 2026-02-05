"""
Pydantic schemas for SpecialtyTemplate model (global catalog).
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SpecialtyTemplateBase(BaseModel):
    """Base specialty template schema."""
    code: str = Field(..., min_length=1, max_length=50, description="Код специальности/профессии")
    name: str = Field(..., min_length=1, max_length=255, description="Название специальности/профессии")


class SpecialtyTemplateCreate(SpecialtyTemplateBase):
    """Schema for creating specialty template."""
    pass


class SpecialtyTemplateUpdate(BaseModel):
    """Schema for updating specialty template."""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class SpecialtyTemplateResponse(SpecialtyTemplateBase):
    """Schema for specialty template response."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SpecialtyTemplateWithUsage(SpecialtyTemplateResponse):
    """Schema for specialty template with usage count."""
    spo_count: int = 0  # Number of SPOs using this template
