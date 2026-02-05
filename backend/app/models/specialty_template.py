"""
SpecialtyTemplate model - global catalog of specialties/professions.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base


class SpecialtyTemplate(Base):
    """SpecialtyTemplate - global catalog entry for specialty/profession."""
    __tablename__ = "specialty_templates"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    specialties = relationship("Specialty", back_populates="template", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SpecialtyTemplate(id={self.id}, code={self.code}, name={self.name})>"
