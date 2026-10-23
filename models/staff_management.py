from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class StaffAttendance(Base):
    __tablename__ = "staff_attendance"

    id = Column(Integer, primary_key=True, index=True)
    staff_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, default=func.current_date(), nullable=False, index=True)
    clock_in = Column(DateTime, nullable=True)
    clock_out = Column(DateTime, nullable=True)
    status = Column(String(50), default="PRESENT", nullable=False)  # PRESENT, LATE, HALF_DAY, ABSENT
    total_hours = Column(Float, default=0.0, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    staff_user = relationship("User")
    hotel = relationship("Hotel")


class StaffActivityLog(Base):
    __tablename__ = "staff_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    staff_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(100), nullable=False)  # CHECK_IN, CHECK_OUT, CLEANING_DONE, ROOM_SERVICE, INSPECTION, ETC.
    description = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)

    staff_user = relationship("User")
    hotel = relationship("Hotel")
