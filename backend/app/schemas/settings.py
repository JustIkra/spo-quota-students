"""
Pydantic schemas for Settings model.
"""
from pydantic import BaseModel, Field


class SettingsBase(BaseModel):
    """Base settings schema."""
    base_quota: int = Field(..., ge=0, description="Base quota for new specialties")


class SettingsUpdate(SettingsBase):
    """Schema for updating settings."""
    pass


class SettingsResponse(SettingsBase):
    """Schema for settings response."""
    pass
