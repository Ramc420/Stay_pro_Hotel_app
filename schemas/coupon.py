from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict
from models.coupon import DiscountType, DiscountCategory


class CouponCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=50, description="Unique coupon code, e.g. SUMMER25")
    description: Optional[str] = Field(None, max_length=255)
    discount_type: DiscountType = Field(..., description="PERCENTAGE or FIXED")
    discount_value: float = Field(..., gt=0, description="Discount amount (e.g. 20 for 20% or $20)")
    max_discount_amount: Optional[float] = Field(None, gt=0, description="Cap on percentage discounts")
    min_booking_amount: float = Field(0.0, ge=0, description="Minimum booking amount required to redeem coupon")
    start_date: datetime = Field(..., description="Coupon validity start datetime")
    expiry_date: datetime = Field(..., description="Coupon expiration datetime")
    max_uses: Optional[int] = Field(None, ge=1, description="Maximum total uses (null for unlimited)")
    max_uses_per_user: int = Field(1, ge=1, description="Maximum uses allowed per user")
    is_active: bool = Field(True, description="Whether coupon is immediately active")
    hotel_id: Optional[int] = Field(None, description="Hotel-specific coupon ID (null for platform-wide)")
    discount_category: DiscountCategory = Field(DiscountCategory.PROMOTIONAL, description="PROMOTIONAL, SEASONAL, EARLY_BIRD, LAST_MINUTE")
    min_advance_days: int = Field(0, ge=0, description="Minimum advance booking days required (e.g. for EARLY_BIRD)")


class CouponUpdate(BaseModel):
    description: Optional[str] = None
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[float] = Field(None, gt=0)
    max_discount_amount: Optional[float] = None
    min_booking_amount: Optional[float] = Field(None, ge=0)
    start_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    max_uses: Optional[int] = Field(None, ge=1)
    max_uses_per_user: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None
    hotel_id: Optional[int] = None
    discount_category: Optional[DiscountCategory] = None
    min_advance_days: Optional[int] = Field(None, ge=0)


class CouponResponse(BaseModel):
    id: int
    code: str
    description: Optional[str] = None
    discount_type: DiscountType
    discount_value: float
    max_discount_amount: Optional[float] = None
    min_booking_amount: float
    start_date: datetime
    expiry_date: datetime
    max_uses: Optional[int] = None
    used_count: int
    max_uses_per_user: int
    is_active: bool
    hotel_id: Optional[int] = None
    hotel_name: Optional[str] = None
    discount_category: DiscountCategory
    min_advance_days: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CouponValidateRequest(BaseModel):
    code: str = Field(..., description="Coupon code to validate")
    hotel_id: int = Field(..., description="Target hotel ID")
    booking_amount: float = Field(..., gt=0, description="Total or base booking amount")
    check_in_date: Optional[date] = Field(None, description="Booking check-in date for advance/seasonal checks")


class CouponValidateResponse(BaseModel):
    valid: bool
    code: str
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    discount_amount: float = 0.0
    final_amount: float
    message: str


class CouponApplyRequest(BaseModel):
    booking_id: int = Field(..., description="Booking ID to apply coupon to")
    code: str = Field(..., description="Coupon code to redeem")


class CouponApplyResponse(BaseModel):
    applied: bool
    booking_id: int
    coupon_code: str
    discount_amount: float
    original_total: float
    new_total_amount: float
    message: str


class CouponUsageResponse(BaseModel):
    id: int
    coupon_id: int
    coupon_code: Optional[str] = None
    user_id: int
    user_name: Optional[str] = None
    booking_id: Optional[int] = None
    booking_reference: Optional[str] = None
    discount_amount: float
    used_at: datetime

    model_config = ConfigDict(from_attributes=True)
