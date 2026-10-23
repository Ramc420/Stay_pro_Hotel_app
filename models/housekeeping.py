import enum
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class HousekeepingStatus(str, enum.Enum):
    DIRTY = "DIRTY"
    CLEANING = "CLEANING"
    CLEAN = "CLEAN"
    INSPECTION = "INSPECTION"
    MAINTENANCE = "MAINTENANCE"


class HousekeepingTask(Base):
    __tablename__ = "housekeeping_tasks"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_staff_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    task_type = Column(String(50), default="CLEANING", nullable=False)  # CLEANING, MAINTENANCE, INSPECTION
    status = Column(Enum(HousekeepingStatus), default=HousekeepingStatus.DIRTY, nullable=False, index=True)
    priority = Column(String(20), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, URGENT
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    hotel = relationship("Hotel")
    room = relationship("Room")
    assigned_staff = relationship("User")
    inspections = relationship("HousekeepingInspection", back_populates="task", cascade="all, delete-orphan")


class HousekeepingInspection(Base):
    __tablename__ = "housekeeping_inspections"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("housekeeping_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    inspector_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_passed = Column(Boolean, default=True, nullable=False)
    rating = Column(Float, default=5.0, nullable=False)
    checklist = Column(JSON, nullable=True)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    task = relationship("HousekeepingTask", back_populates="inspections")
    room = relationship("Room")
    inspector = relationship("User")
