"""
Application configuration loaded from environment variables.
"""
from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional


# Default values that should NOT be used in production
_DEFAULT_SECRET_KEY = "your-secret-key-change-in-production"
_DEFAULT_ADMIN_LOGIN = "admin"
_DEFAULT_ADMIN_PASSWORD = "admin123"


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Environment
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/spo_quota"

    # JWT
    SECRET_KEY: str = _DEFAULT_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour (reduced from 24h for security, ISSUE-007)

    # Admin credentials for initial setup
    ADMIN_LOGIN: str = _DEFAULT_ADMIN_LOGIN
    ADMIN_PASSWORD: str = _DEFAULT_ADMIN_PASSWORD

    # Default quota
    DEFAULT_BASE_QUOTA: int = 25

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:9010"

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """Ensure default secrets are not used in production environment."""
        if self.ENVIRONMENT.lower() == "production":
            errors = []

            if self.SECRET_KEY == _DEFAULT_SECRET_KEY:
                errors.append("SECRET_KEY must be changed from default in production")

            if self.ADMIN_LOGIN == _DEFAULT_ADMIN_LOGIN:
                errors.append("ADMIN_LOGIN must be changed from default in production")

            if self.ADMIN_PASSWORD == _DEFAULT_ADMIN_PASSWORD:
                errors.append("ADMIN_PASSWORD must be changed from default in production")

            if errors:
                raise ValueError(
                    "Production security validation failed:\n- " + "\n- ".join(errors)
                )

        return self

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
