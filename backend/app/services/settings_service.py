"""
Settings service - business logic for application settings.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Settings
from app.core.config import settings as app_settings


async def get_base_quota(db: AsyncSession) -> int:
    """Get base quota from database settings."""
    result = await db.execute(select(Settings).where(Settings.key == "base_quota"))
    setting = result.scalars().first()
    if setting:
        return int(setting.value)
    return app_settings.DEFAULT_BASE_QUOTA


async def set_base_quota(db: AsyncSession, value: int) -> int:
    """Set base quota in database settings."""
    result = await db.execute(select(Settings).where(Settings.key == "base_quota"))
    setting = result.scalars().first()
    if setting:
        setting.value = str(value)
    else:
        setting = Settings(key="base_quota", value=str(value))
        db.add(setting)
    await db.commit()
    return value


async def init_settings(db: AsyncSession) -> None:
    """Initialize default settings if not exist."""
    result = await db.execute(select(Settings).where(Settings.key == "base_quota"))
    existing = result.scalars().first()
    if not existing:
        setting = Settings(key="base_quota", value=str(app_settings.DEFAULT_BASE_QUOTA))
        db.add(setting)
        await db.commit()
