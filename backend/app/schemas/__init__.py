"""Schemas module - Pydantic schemas for request/response validation."""
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    UserWithPassword,
    TokenResponse,
    CurrentUser
)
from app.schemas.spo import (
    SPOBase,
    SPOCreate,
    SPOUpdate,
    SPOResponse,
    SPOWithStats
)
from app.schemas.specialty_template import (
    SpecialtyTemplateBase,
    SpecialtyTemplateCreate,
    SpecialtyTemplateUpdate,
    SpecialtyTemplateResponse,
    SpecialtyTemplateWithUsage
)
from app.schemas.specialty import (
    SpecialtyBase,
    SpecialtyCreate,
    SpecialtyUpdate,
    QuotaUpdate,
    SpecialtyResponse,
    SpecialtyWithStats,
    SpecialtyAssign
)
from app.schemas.student import (
    StudentBase,
    StudentCreate,
    StudentResponse,
    StudentWithSpecialty
)
from app.schemas.settings import (
    SettingsBase,
    SettingsUpdate,
    SettingsResponse
)
from app.schemas.stats import (
    SpecialtyStats,
    SPOStats,
    OverallStats
)

__all__ = [
    "UserBase", "UserCreate", "UserLogin", "UserResponse", "UserWithPassword",
    "TokenResponse", "CurrentUser",
    "SPOBase", "SPOCreate", "SPOUpdate", "SPOResponse", "SPOWithStats",
    "SpecialtyTemplateBase", "SpecialtyTemplateCreate", "SpecialtyTemplateUpdate",
    "SpecialtyTemplateResponse", "SpecialtyTemplateWithUsage",
    "SpecialtyBase", "SpecialtyCreate", "SpecialtyUpdate", "QuotaUpdate",
    "SpecialtyResponse", "SpecialtyWithStats", "SpecialtyAssign",
    "StudentBase", "StudentCreate", "StudentResponse", "StudentWithSpecialty",
    "SettingsBase", "SettingsUpdate", "SettingsResponse",
    "SpecialtyStats", "SPOStats", "OverallStats"
]
