from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Review(Base):
    __tablename__ = "hotel_reviews"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True, unique=True)
    rating = Column(Float, nullable=False)
    comment = Column(Text, nullable=True)
    
    # Moderation & Reporting
    is_reported = Column(Boolean, default=False, nullable=False)
    report_reason = Column(Text, nullable=True)
    reported_at = Column(DateTime, nullable=True)
    is_hidden = Column(Boolean, default=False, nullable=False)
    moderation_status = Column(String(50), default="APPROVED", nullable=False)  # APPROVED, REPORTED, HIDDEN, REJECTED
    moderation_notes = Column(Text, nullable=True)
    moderated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    moderated_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    hotel = relationship("Hotel", back_populates="reviews")
    user = relationship("User", foreign_keys=[user_id], back_populates="reviews")
    booking = relationship("Booking", back_populates="review")
    moderated_by = relationship("User", foreign_keys=[moderated_by_id])
