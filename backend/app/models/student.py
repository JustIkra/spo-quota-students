"""
Student model for enrolled students.
"""
from datetime import datetime, timezone, timedelta

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base

MSK = timezone(timedelta(hours=3))


class Student(Base):
    """Student model - enrolled student in a specialty."""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    specialty_id = Column(Integer, ForeignKey("specialties.id", ondelete="CASCADE"), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    certificate_number = Column(String(50), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(MSK).replace(tzinfo=None), nullable=False)

    # Relationships
    specialty = relationship("Specialty", back_populates="students", lazy="raise")

    @property
    def full_name(self) -> str:
        """Compute full name from name parts."""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)

    def __repr__(self):
        return f"<Student(id={self.id}, full_name={self.full_name})>"
