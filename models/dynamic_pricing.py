import enum
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class PricingRuleType(str, enum.Enum):
    SEASONAL = "SEASONAL"        # Summer/Winter rates
    WEEKEND = "WEEKEND"          # Friday / Saturday surges
    HOLIDAY = "HOLIDAY"          # Christmas / New Year / National Holidays
    PROMOTIONAL = "PROMOTIONAL"  # Early bird or flash sales


class PriceAdjustmentType(str, enum.Enum):
    PERCENTAGE_INCREASE = "PERCENTAGE_INCREASE"
    PERCENTAGE_DECREASE = "PERCENTAGE_DECREASE"
    FIXED_PRICE = "FIXED_PRICE"
    FIXED_ADJUSTMENT = "FIXED_ADJUSTMENT"


class DynamicPricingRule(Base):
    """Dynamic pricing rules for seasonal, weekend, holiday and promo pricing."""
    __tablename__ = "dynamic_pricing_rules"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    room_type_id = Column(Integer, ForeignKey("room_types.id", ondelete="CASCADE"), nullable=True, index=True)
    
    rule_name = Column(String(100), nullable=False)
    rule_type = Column(Enum(PricingRuleType), nullable=False, index=True)
    adjustment_type = Column(Enum(PriceAdjustmentType), nullable=False)
    adjustment_value = Column(Float, nullable=False)  # e.g. 20.0 for +20% or 150.0 for fixed price
    
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    days_of_week = Column(String(50), nullable=True)  # Comma separated e.g. "4,5,6" (0=Mon, 6=Sun)
    
    priority = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    hotel = relationship("Hotel")
    room_type = relationship("RoomType")
