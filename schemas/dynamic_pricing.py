from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field


class DynamicPricingRuleCreate(BaseModel):
    hotel_id: int
    room_type_id: Optional[int] = None
    rule_name: str
    rule_type: str  # SEASONAL, WEEKEND, HOLIDAY, PROMOTIONAL
    adjustment_type: str  # PERCENTAGE_INCREASE, PERCENTAGE_DECREASE, FIXED_PRICE, FIXED_ADJUSTMENT
    adjustment_value: float
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    days_of_week: Optional[str] = None  # e.g. "4,5,6" (Fri, Sat, Sun)
    priority: int = 1
    is_active: bool = True


class DynamicPricingRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    adjustment_type: Optional[str] = None
    adjustment_value: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    days_of_week: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class DynamicPricingRuleResponse(BaseModel):
    id: int
    hotel_id: int
    room_type_id: Optional[int] = None
    rule_name: str
    rule_type: str
    adjustment_type: str
    adjustment_value: float
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    days_of_week: Optional[str] = None
    priority: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DailyPriceDetail(BaseModel):
    date: date
    day_name: str
    base_price: float
    final_price: float
    applied_rules: List[str] = []


class PriceCalculationRequest(BaseModel):
    hotel_id: int
    room_type_id: int
    check_in_date: date
    check_out_date: date


class PriceCalculationResponse(BaseModel):
    hotel_id: int
    room_type_id: int
    room_type_name: str
    check_in_date: date
    check_out_date: date
    nights: int
    base_total: float
    final_total: float
    total_adjustment: float
    average_nightly_rate: float
    daily_breakdown: List[DailyPriceDetail]
