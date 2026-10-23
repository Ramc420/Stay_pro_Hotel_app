from typing import Optional, List, Any
from datetime import datetime, date
from pydantic import BaseModel


class StaffCreate(BaseModel):
    user_id: int
    hotel_id: int
    department: Optional[str] = "Front Desk"
    position: Optional[str] = "Staff"
    permissions: Optional[List[str]] = ["FRONT_DESK"]


class StaffUpdate(BaseModel):
    department: Optional[str] = None
    position: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None


class StaffResponse(BaseModel):
    id: int
    user_id: int
    hotel_id: int
    department: Optional[str] = None
    position: Optional[str] = None
    permissions: Optional[Any] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AttendanceClockRequest(BaseModel):
    action: str  # CLOCK_IN, CLOCK_OUT
    notes: Optional[str] = None


class AttendanceResponse(BaseModel):
    id: int
    staff_user_id: int
    hotel_id: int
    date: date
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    status: str
    total_hours: float
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ActivityLogResponse(BaseModel):
    id: int
    staff_user_id: int
    hotel_id: int
    action: str
    description: str
    timestamp: datetime

    class Config:
        from_attributes = True
