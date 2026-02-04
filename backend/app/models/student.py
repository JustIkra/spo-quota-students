"""
Student model for enrolled students.
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Student(Base):
    """Student model - enrolled student in a specialty."""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    specialty_id = Column(Integer, ForeignKey("specialties.id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String(255), nullable=False)
    attestat_number = Column(String(50), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    specialty = relationship("Specialty", back_populates="students")

    def __repr__(self):
        return f"<Student(id={self.id}, full_name={self.full_name})>"
