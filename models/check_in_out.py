from sqlalchemy import Column, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class CheckInOutRecord(Base):
    __tablename__ = "check_in_out_records"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="RESTRICT"), nullable=False, index=True)
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    early_check_in_hours = Column(Float, default=0.0, nullable=False)
    early_check_in_fee = Column(Float, default=0.0, nullable=False)
    late_check_out_hours = Column(Float, default=0.0, nullable=False)
    late_check_out_fee = Column(Float, default=0.0, nullable=False)
    processed_by_staff_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    booking = relationship("Booking")
    hotel = relationship("Hotel")
    room = relationship("Room")
    processed_by = relationship("User")
