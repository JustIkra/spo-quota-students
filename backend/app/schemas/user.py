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


class OperatorCredential(BaseModel):
    """Single created operator credential with SPO name."""
    spo_id: int
    spo_name: str
    login: str
    password: str


class BulkOperatorCreateResponse(BaseModel):
    """Response for bulk operator creation."""
    created: list[OperatorCredential]
    skipped_spo_ids: list[int] = Field(default_factory=list)


class DocxExportRequest(BaseModel):
    """Payload for exporting a list of credentials to .docx."""
    items: list[OperatorCredential] = Field(..., min_length=1)


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
