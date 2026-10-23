from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict
from models.refund import RefundStatus, CancellationPolicyType


class CancellationPolicyQuoteRequest(BaseModel):
    booking_id: int = Field(..., description="Target booking ID to evaluate cancellation refund quote")
    cancellation_date: Optional[date] = Field(None, description="Simulated cancellation date (defaults to today)")


class CancellationPolicyQuoteResponse(BaseModel):
    booking_id: int
    booking_reference: str
    hotel_id: int
    hotel_name: str
    check_in_date: date
    check_out_date: date
    days_until_check_in: int
    cancellation_policy: str
    total_amount: float
    penalty_percentage: float
    penalty_amount: float
    refundable_amount: float
    currency: str = "usd"
    is_eligible_for_refund: bool
    explanation: str


class RefundRequestCreate(BaseModel):
    booking_id: int = Field(..., description="Booking ID to request refund for")
    reason: str = Field(..., min_length=5, max_length=1000, description="Reason for requesting refund")


class RefundApprovalRequest(BaseModel):
    amount_approved: Optional[float] = Field(None, ge=0.0, description="Approved refund amount (defaults to policy calculated or requested amount)")
    admin_notes: Optional[str] = Field(None, max_length=1000, description="Administrative notes regarding the approval")


class RefundRejectionRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=5, max_length=1000, description="Reason for rejecting the refund request")


class RefundRequestResponse(BaseModel):
    id: int
    booking_id: int
    booking_reference: Optional[str] = None
    user_id: int
    user_name: Optional[str] = None
    hotel_id: int
    hotel_name: Optional[str] = None
    payment_id: Optional[int] = None
    amount_requested: float
    amount_approved: Optional[float] = None
    penalty_amount: float
    currency: str
    reason: str
    status: RefundStatus
    cancellation_policy_applied: Optional[str] = None
    admin_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    stripe_refund_id: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
