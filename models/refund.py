import enum
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class RefundStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class CancellationPolicyType(str, enum.Enum):
    FLEXIBLE = "FLEXIBLE"          # 100% refund up to 24h before check-in, 0% thereafter
    MODERATE = "MODERATE"          # 100% refund up to 5 days before, 50% up to 24h, 0% thereafter
    STRICT = "STRICT"              # 50% refund up to 7 days before, 0% thereafter
    NON_REFUNDABLE = "NON_REFUNDABLE"  # 0% refund


class RefundRequest(Base):
    __tablename__ = "refund_requests"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True, index=True)
    amount_requested = Column(Float, nullable=False)
    amount_approved = Column(Float, nullable=True)
    penalty_amount = Column(Float, default=0.0, nullable=False)
    currency = Column(String(10), default="usd", nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(Enum(RefundStatus), default=RefundStatus.PENDING, nullable=False, index=True)
    cancellation_policy_applied = Column(String(100), nullable=True)
    admin_notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    stripe_refund_id = Column(String(255), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    booking = relationship("Booking", back_populates="refund_request")
    user = relationship("User", back_populates="refund_requests")
    hotel = relationship("Hotel", back_populates="refund_requests")
    payment = relationship("Payment")
