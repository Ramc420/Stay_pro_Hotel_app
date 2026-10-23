import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class LoyaltyTier(str, enum.Enum):
    BRONZE = "BRONZE"       # 0 - 999 pts (1.0x points multiplier)
    SILVER = "SILVER"       # 1,000 - 4,999 pts (1.25x points multiplier + late checkout)
    GOLD = "GOLD"           # 5,000 - 9,999 pts (1.5x points multiplier + free breakfast)
    PLATINUM = "PLATINUM"   # 10,000+ pts (2.0x points multiplier + room upgrade + VIP support)


class LoyaltyTransactionType(str, enum.Enum):
    EARNED_BOOKING = "EARNED_BOOKING"
    REDEEMED = "REDEEMED"
    REFERRAL_BONUS = "REFERRAL_BONUS"
    WELCOME_BONUS = "WELCOME_BONUS"
    MANUAL_ADJUST = "MANUAL_ADJUST"


class LoyaltyAccount(Base):
    """Member loyalty account tracking tier status, balances and referral codes."""
    __tablename__ = "loyalty_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    points_balance = Column(Integer, default=0, nullable=False)
    lifetime_points = Column(Integer, default=0, nullable=False)
    tier = Column(Enum(LoyaltyTier), default=LoyaltyTier.BRONZE, nullable=False, index=True)
    
    referral_code = Column(String(50), unique=True, nullable=False, index=True)
    referred_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    referred_by = relationship("User", foreign_keys=[referred_by_id])
    ledger_entries = relationship("LoyaltyLedger", back_populates="account", cascade="all, delete-orphan")


class LoyaltyLedger(Base):
    """Immutable ledger of all points earned and redeemed."""
    __tablename__ = "loyalty_ledger"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("loyalty_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True, index=True)
    
    transaction_type = Column(Enum(LoyaltyTransactionType), nullable=False, index=True)
    points = Column(Integer, nullable=False)  # positive for credit, negative for redemption
    balance_after = Column(Integer, nullable=False)
    
    idempotency_key = Column(String(100), unique=True, nullable=True, index=True)  # prevents duplicate credits
    description = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    account = relationship("LoyaltyAccount", back_populates="ledger_entries")
    booking = relationship("Booking")
    user = relationship("User")
