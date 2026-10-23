from typing import Optional, List, Dict, Any
from datetime import date
from pydantic import BaseModel


# Module 31: Revenue Analytics
class DailyRevenueItem(BaseModel):
    date: str
    booking_revenue: float
    service_revenue: float
    room_service_revenue: float
    refund_amount: float
    net_revenue: float
    bookings_count: int


class MonthlyRevenueItem(BaseModel):
    month: str  # YYYY-MM
    booking_revenue: float
    service_revenue: float
    room_service_revenue: float
    refund_amount: float
    net_revenue: float
    bookings_count: int


class RevenueSummaryResponse(BaseModel):
    hotel_id: int
    hotel_name: str
    total_gross_revenue: float
    total_service_revenue: float
    total_room_service_revenue: float
    total_refunded: float
    net_revenue: float
    total_completed_bookings: int
    average_booking_value: float


# Module 32: Occupancy Analytics
class LiveOccupancyResponse(BaseModel):
    hotel_id: int
    hotel_name: str
    total_rooms: int
    occupied_rooms: int
    available_rooms: int
    cleaning_rooms: int
    maintenance_rooms: int
    occupancy_rate: float


class PeakPeriodItem(BaseModel):
    date: str
    day_of_week: str
    occupied_count: int
    occupancy_rate: float


# Module 33: Customer Analytics
class RepeatCustomerItem(BaseModel):
    user_id: int
    full_name: str
    email: str
    bookings_count: int
    total_spend: float
    average_spend: float


class DestinationDemandItem(BaseModel):
    city: str
    country: str
    hotels_count: int
    total_bookings: int
    total_revenue: float


class CustomerAnalyticsSummary(BaseModel):
    total_registered_customers: int
    repeat_customers_count: int
    retention_rate: float
    average_bookings_per_customer: float
    average_customer_lifetime_value: float
