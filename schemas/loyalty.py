from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class LoyaltyAccountResponse(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    points_balance: int
    lifetime_points: int
    tier: str
    tier_multiplier: float
    tier_benefits: List[str]
    referral_code: str
    referred_by_id: Optional[int] = None
    created_at: datetime


class LoyaltyLedgerResponse(BaseModel):
    id: int
    user_id: int
    booking_id: Optional[int] = None
    transaction_type: str
    points: int
    balance_after: int
    description: str
    idempotency_key: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AwardBookingPointsRequest(BaseModel):
    booking_id: int
    idempotency_key: Optional[str] = None


class RedeemPointsRequest(BaseModel):
    points: int = Field(..., gt=0, description="Number of points to redeem")
    booking_id: Optional[int] = None


class RedeemPointsResponse(BaseModel):
    points_redeemed: int
    discount_amount: float
    new_balance: int
    message: str


class ApplyReferralRequest(BaseModel):
    referral_code: str


class TierBenefitInfo(BaseModel):
    tier: str
    min_points: int
    multiplier: float
    benefits: List[str]
