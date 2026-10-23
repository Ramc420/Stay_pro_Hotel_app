import enum
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey, Enum, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class PaymentRecordStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_reference = Column(String(100), unique=True, index=True, nullable=False)
    idempotency_key = Column(String(255), unique=True, index=True, nullable=False)
    stripe_session_id = Column(String(255), nullable=True, index=True)
    stripe_payment_intent_id = Column(String(255), nullable=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="usd", nullable=False)
    status = Column(Enum(PaymentRecordStatus), default=PaymentRecordStatus.PENDING, nullable=False, index=True)
    payment_method = Column(String(50), default="stripe_checkout", nullable=False)
    receipt_url = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    booking = relationship("Booking", back_populates="payments")
    invoices = relationship("Invoice", back_populates="payment")
