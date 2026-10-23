from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from models.payment import PaymentRecordStatus


class CreatePaymentSessionRequest(BaseModel):
    booking_id: int
    idempotency_key: Optional[str] = Field(None, description="Client idempotency key to prevent double charge")
    payment_method: str = Field(default="stripe_checkout", description="stripe_checkout, card, etc.")


class ConfirmPaymentRequest(BaseModel):
    booking_id: int
    payment_intent_id: Optional[str] = None
    idempotency_key: Optional[str] = None


class StripeCheckoutSessionResponse(BaseModel):
    session_id: str
    checkout_url: str
    booking_id: int
    amount: float
    currency: str


class PaymentResponse(BaseModel):
    id: int
    booking_id: int
    payment_reference: str
    idempotency_key: str
    stripe_session_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    amount: float
    currency: str
    status: PaymentRecordStatus
    payment_method: str
    receipt_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
