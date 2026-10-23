from typing import Optional, List, Dict, Any
from datetime import date
from pydantic import BaseModel


class GrowthMetric(BaseModel):
    metric_name: str
    current_period_value: float
    previous_period_value: float
    growth_percentage: float
    trend: str  # UP, DOWN, FLAT


class GrowthMetricsResponse(BaseModel):
    period: str
    revenue_growth: GrowthMetric
    bookings_growth: GrowthMetric
    customer_growth: GrowthMetric


class TopHotelPerformance(BaseModel):
    hotel_id: int
    hotel_name: str
    city: str
    total_bookings: int
    gross_revenue: float
    average_rating: float


class TopDestination(BaseModel):
    city: str
    state: str
    country: str
    total_bookings: int
    total_revenue: float


class TopPerformersResponse(BaseModel):
    top_hotels: List[TopHotelPerformance]
    top_destinations: List[TopDestination]


class MonthlyTrendPoint(BaseModel):
    month: str
    occupancy_rate_percentage: float
    total_nights_sold: int
    total_bookings: int
    revenue: float


class OccupancyTrendsResponse(BaseModel):
    hotel_id: Optional[int] = None
    period_months: int
    trends: List[MonthlyTrendPoint]


class ExecutiveMonthlySummary(BaseModel):
    year: int
    month: int
    month_name: str
    total_revenue: float
    total_bookings: float
    total_active_hotels: int
    total_new_customers: int
    average_booking_value: float
    platform_commission_earned: float
    top_city: Optional[str] = None
