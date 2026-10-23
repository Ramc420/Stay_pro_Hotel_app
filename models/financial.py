import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class SettlementStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PAID = "PAID"
    FAILED = "FAILED"


class PayoutSettlement(Base):
    """Tracks hotel earnings, platform commissions, collected taxes, and net disbursements."""
    __tablename__ = "payout_settlements"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    gross_revenue = Column(Float, default=0.0, nullable=False)
    commission_rate = Column(Float, default=10.0, nullable=False)  # % e.g. 10%
    platform_commission = Column(Float, default=0.0, nullable=False)
    tax_collected = Column(Float, default=0.0, nullable=False)
    refunds_deducted = Column(Float, default=0.0, nullable=False)
    net_payout_amount = Column(Float, default=0.0, nullable=False)
    
    status = Column(Enum(SettlementStatus), default=SettlementStatus.PENDING, nullable=False, index=True)
    payout_reference = Column(String(100), unique=True, nullable=True, index=True)
    notes = Column(Text, nullable=True)
    settled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    hotel = relationship("Hotel")
