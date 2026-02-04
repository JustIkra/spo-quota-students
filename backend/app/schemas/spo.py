"""
Pydantic schemas for SPO model.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SPOBase(BaseModel):
    """Base SPO schema."""
    name: str = Field(..., min_length=1, max_length=255)


class SPOCreate(SPOBase):
    """Schema for creating SPO."""
    pass


class SPOUpdate(BaseModel):
    """Schema for updating SPO."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class SPOResponse(SPOBase):
    """Schema for SPO response."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SPOWithStats(SPOResponse):
    """Schema for SPO with statistics."""
    specialties_count: int = 0
    students_count: int = 0
    operators_count: int = 0
