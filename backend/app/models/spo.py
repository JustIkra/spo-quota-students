"""
SPO (Secondary Professional Organization) model.
"""
from datetime import datetime, timezone, timedelta

from sqlalchemy import Column, Integer, String, DateTime

MSK = timezone(timedelta(hours=3))
from sqlalchemy.orm import relationship

from app.core.database import Base


class SPO(Base):
    """SPO - educational organization model."""
    __tablename__ = "spo"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(MSK).replace(tzinfo=None), nullable=False)

    # Relationships
    operators = relationship("User", back_populates="spo")
    specialties = relationship("Specialty", back_populates="spo", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SPO(id={self.id}, name={self.name})>"
