"""
User model for authentication and authorization.
"""
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, PyEnum):
    """User roles enumeration."""
    ADMIN = "admin"
    OPERATOR = "operator"


class User(Base):
    """User model for admin and operator accounts."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.OPERATOR)
    spo_id = Column(Integer, ForeignKey("spo.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    spo = relationship("SPO", back_populates="operators")

    def __repr__(self):
        return f"<User(id={self.id}, login={self.login}, role={self.role})>"
