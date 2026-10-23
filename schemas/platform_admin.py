from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class UserAccountStatusUpdateRequest(BaseModel):
    is_active: bool
    reason: Optional[str] = None


class HotelStatusOverrideRequest(BaseModel):
    is_active: bool
    status: str  # APPROVED, SUSPENDED, REJECTED, PENDING_APPROVAL
    reason: str = Field(..., min_length=3)


class BookingEmergencyOverrideRequest(BaseModel):
    new_status: str  # CONFIRMED, CHECKED_IN, CHECKED_OUT, CANCELLED, COMPLETED
    reason: str = Field(..., min_length=3)


class PlatformPolicyResponse(BaseModel):
    id: int
    policy_type: str
    title: str
    content: str
    version: str
    is_active: bool
    updated_by_id: Optional[int] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class PlatformPolicyUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: str
    version: Optional[str] = "1.0"
    is_active: Optional[bool] = True


class SystemServiceStatus(BaseModel):
    service_name: str
    status: str  # HEALTHY, DEGRADED, DOWN
    latency_ms: float
    details: Optional[str] = None


class SystemHealthOverview(BaseModel):
    timestamp: datetime
    overall_status: str  # HEALTHY, WARNING, CRITICAL
    database: SystemServiceStatus
    active_users_count: int
    active_hotels_count: int
    pending_bookings_count: int
    open_security_alerts: int
    total_db_tables: int
