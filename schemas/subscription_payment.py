from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class CheckoutSessionCreate(BaseModel):
    hotel_id: int
    plan_id: int
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutSessionResponse(BaseModel):
    session_id: str
    checkout_url: str
    hotel_id: int
    plan_id: int
    plan_name: str
    amount: float
    currency: str


class PlanUpgradeDowngradeRequest(BaseModel):
    new_plan_id: int
    immediate: bool = True


class SubscriptionPaymentResponse(BaseModel):
    id: int
    hotel_id: int
    plan_id: int
    plan_name: Optional[str] = None
    amount: float
    currency: str
    billing_cycle: str
    status: str
    stripe_session_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    stripe_invoice_id: Optional[str] = None
    invoice_url: Optional[str] = None
    notes: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookEventRequest(BaseModel):
    event_type: str  # e.g. "invoice.payment_succeeded", "customer.subscription.deleted"
    session_id: Optional[str] = None
    subscription_id: Optional[str] = None
    hotel_id: Optional[int] = None
    plan_id: Optional[int] = None
    amount_paid: Optional[float] = None
    currency: Optional[str] = "usd"
    metadata: Optional[Dict[str, Any]] = None
