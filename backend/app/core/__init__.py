"""Core module - configuration, security, database."""
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)

# Note: get_db is exported from app.api.deps to avoid circular imports
