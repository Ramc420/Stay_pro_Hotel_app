from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class SubscriptionPlanCreate(BaseModel):
    name: str
    tier: str = "BASIC"  # FREE, BASIC, PREMIUM, ENTERPRISE
    billing_cycle: str = "MONTHLY"  # MONTHLY, YEARLY
    price: float
    max_rooms: int = 15
    commission_rate: float = 12.0
    has_analytics: bool = True
    has_featured_badge: bool = False
    has_priority_support: bool = False


class SubscriptionPlanResponse(BaseModel):
    id: int
    name: str
    tier: str
    billing_cycle: str
    price: float
    max_rooms: int
    commission_rate: float
    has_analytics: bool
    has_featured_badge: bool
    has_priority_support: bool
    is_active: bool

    class Config:
        from_attributes = True


class HotelSubscribeRequest(BaseModel):
    plan_id: int
    auto_renew: bool = True


class HotelSubscriptionResponse(BaseModel):
    id: int
    hotel_id: int
    plan_id: int
    plan_name: str
    tier: str
    billing_cycle: str
    price: float
    status: str
    start_date: datetime
    end_date: datetime
    auto_renew: bool
    created_at: datetime

    class Config:
        from_attributes = True
