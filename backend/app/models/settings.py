"""
Settings model for application configuration stored in database.
"""
from sqlalchemy import Column, Integer, String

from app.core.database import Base


class Settings(Base):
    """Settings model for key-value configuration."""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(String(255), nullable=False)

    def __repr__(self):
        return f"<Settings(key={self.key}, value={self.value})>"
