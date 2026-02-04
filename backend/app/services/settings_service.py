"""
Settings service - business logic for application settings.
"""
from sqlalchemy.orm import Session

from app.models import Settings
from app.core.config import settings as app_settings


def get_base_quota(db: Session) -> int:
    """Get base quota from database settings."""
    setting = db.query(Settings).filter(Settings.key == "base_quota").first()
    if setting:
        return int(setting.value)
    return app_settings.DEFAULT_BASE_QUOTA


def set_base_quota(db: Session, value: int) -> int:
    """Set base quota in database settings."""
    setting = db.query(Settings).filter(Settings.key == "base_quota").first()
    if setting:
        setting.value = str(value)
    else:
        setting = Settings(key="base_quota", value=str(value))
        db.add(setting)
    db.commit()
    return value


def init_settings(db: Session) -> None:
    """Initialize default settings if not exist."""
    existing = db.query(Settings).filter(Settings.key == "base_quota").first()
    if not existing:
        setting = Settings(key="base_quota", value=str(app_settings.DEFAULT_BASE_QUOTA))
        db.add(setting)
        db.commit()
