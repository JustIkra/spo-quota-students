"""
Pydantic schemas for User model.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema."""
    login: str = Field(..., min_length=3, max_length=100)


class UserCreate(BaseModel):
    """Schema for creating a user (admin creates operator). Login is auto-generated."""
    spo_id: int = Field(..., description="SPO ID for the operator")


class UserLogin(BaseModel):
    """Schema for user login."""
    login: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    role: UserRole
    spo_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserWithPassword(UserResponse):
    """Schema for operator creation response with generated password."""
    generated_password: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class CurrentUser(BaseModel):
    """Schema for current user info."""
    id: int
    login: str
    role: UserRole
    spo_id: Optional[int] = None
    spo_name: Optional[str] = None

    class Config:
        from_attributes = True
