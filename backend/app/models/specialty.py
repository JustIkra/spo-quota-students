"""
Specialty model for educational programs.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Specialty(Base):
    """Specialty model - educational program within SPO."""
    __tablename__ = "specialties"

    id = Column(Integer, primary_key=True, index=True)
    spo_id = Column(Integer, ForeignKey("spo.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True)
    quota = Column(Integer, nullable=False, default=25)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    spo = relationship("SPO", back_populates="specialties")
    students = relationship("Student", back_populates="specialty", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Specialty(id={self.id}, name={self.name}, quota={self.quota})>"
