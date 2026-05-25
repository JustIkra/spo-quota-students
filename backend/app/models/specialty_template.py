"""
SpecialtyTemplate model - global catalog of specialties/professions.
"""
from datetime import datetime, timezone, timedelta

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base

MSK = timezone(timedelta(hours=3))


class SpecialtyTemplate(Base):
    """SpecialtyTemplate - global catalog entry for specialty/profession."""
    __tablename__ = "specialty_templates"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(MSK).replace(tzinfo=None), nullable=False)

    specialties = relationship(
        "Specialty",
        back_populates="template",
        cascade="all, delete",
        passive_deletes=True,
        lazy="raise",
    )

    def __repr__(self):
        return f"<SpecialtyTemplate(id={self.id}, code={self.code}, name={self.name})>"
