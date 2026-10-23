import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class SubscriptionPaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class SubscriptionPaymentHistory(Base):
    """Stores billing history and webhook events for hotel subscription plans."""
    __tablename__ = "subscription_payment_history"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    billing_cycle = Column(String(20), default="MONTHLY", nullable=False)
    status = Column(Enum(SubscriptionPaymentStatus), default=SubscriptionPaymentStatus.PENDING, nullable=False, index=True)
    
    stripe_session_id = Column(String(255), nullable=True, index=True)
    stripe_subscription_id = Column(String(255), nullable=True, index=True)
    stripe_invoice_id = Column(String(255), nullable=True)
    
    invoice_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    hotel = relationship("Hotel")
    plan = relationship("SubscriptionPlan")
