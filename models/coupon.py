import enum
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class DiscountType(str, enum.Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED = "FIXED"


class DiscountCategory(str, enum.Enum):
    PROMOTIONAL = "PROMOTIONAL"
    SEASONAL = "SEASONAL"
    EARLY_BIRD = "EARLY_BIRD"
    LAST_MINUTE = "LAST_MINUTE"


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    discount_type = Column(Enum(DiscountType), nullable=False)
    discount_value = Column(Float, nullable=False)
    max_discount_amount = Column(Float, nullable=True)
    min_booking_amount = Column(Float, default=0.0, nullable=False)
    start_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    max_uses = Column(Integer, nullable=True)  # Null means unlimited
    used_count = Column(Integer, default=0, nullable=False)
    max_uses_per_user = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, index=True, nullable=False)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=True, index=True)
    discount_category = Column(Enum(DiscountCategory), default=DiscountCategory.PROMOTIONAL, nullable=False)
    min_advance_days = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    hotel = relationship("Hotel", back_populates="coupons")
    usages = relationship("CouponUsage", back_populates="coupon", cascade="all, delete-orphan")


class CouponUsage(Base):
    __tablename__ = "coupon_usages"

    id = Column(Integer, primary_key=True, index=True)
    coupon_id = Column(Integer, ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True, index=True)
    discount_amount = Column(Float, nullable=False)
    used_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    coupon = relationship("Coupon", back_populates="usages")
    user = relationship("User", back_populates="coupons_used")
    booking = relationship("Booking", back_populates="coupon_usages")
