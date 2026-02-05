"""
Specialty model for educational programs assigned to SPO.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class Specialty(Base):
    """Specialty model - specialty/profession assigned to SPO with quota."""
    __tablename__ = "specialties"

    id = Column(Integer, primary_key=True, index=True)
    spo_id = Column(Integer, ForeignKey("spo.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("specialty_templates.id", ondelete="CASCADE"), nullable=True, index=True)
    # Keep name/code for backwards compatibility and denormalization
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True)
    quota = Column(Integer, nullable=False, default=25)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Unique constraint: one template can be assigned to SPO only once
    __table_args__ = (
        UniqueConstraint('spo_id', 'template_id', name='uq_specialty_spo_template'),
    )

    # Relationships
    spo = relationship("SPO", back_populates="specialties")
    template = relationship("SpecialtyTemplate", back_populates="specialties")
    students = relationship("Student", back_populates="specialty", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Specialty(id={self.id}, name={self.name}, quota={self.quota})>"
