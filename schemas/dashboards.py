from typing import Optional, List, Dict, Any
from pydantic import BaseModel


# Module 34: Hotel Owner Dashboard
class OwnerDashboardResponse(BaseModel):
    hotel_id: int
    hotel_name: str
    today_arrivals_count: int
    today_departures_count: int
    current_guest_count: int
    total_rooms: int
    occupied_rooms: int
    occupancy_rate: float
    today_revenue: float
    month_revenue: float
    total_revenue: float
    average_rating: float
    total_reviews: int
    pending_check_ins: List[Dict[str, Any]] = []
    recent_reviews: List[Dict[str, Any]] = []
    action_items: Dict[str, Any] = {}


# Module 35: Customer Dashboard
class CustomerDashboardResponse(BaseModel):
    user_id: int
    full_name: str
    upcoming_bookings: List[Dict[str, Any]] = []
    past_bookings_count: int
    total_spent: float
    wishlist_count: int
    unread_notifications_count: int
    recent_payments: List[Dict[str, Any]] = []
    recommended_hotels: List[Dict[str, Any]] = []


# Module 36: Admin Dashboard
class AdminDashboardResponse(BaseModel):
    total_customers: int
    total_hotel_owners: int
    total_hotels: int
    approved_hotels: int
    pending_hotels_count: int
    total_rooms: int
    total_bookings: int
    active_reservations: int
    total_platform_revenue: float
    total_refunds_processed: float
    net_platform_volume: float
    pending_moderation_items: int
    recent_registrations: List[Dict[str, Any]] = []
