from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class HousekeepingTaskCreate(BaseModel):
    hotel_id: int
    room_id: int
    assigned_staff_id: Optional[int] = None
    task_type: Optional[str] = "CLEANING"  # CLEANING, MAINTENANCE, INSPECTION
    priority: Optional[str] = "MEDIUM"      # LOW, MEDIUM, HIGH, URGENT
    notes: Optional[str] = None


class HousekeepingStatusUpdate(BaseModel):
    status: str  # DIRTY, CLEANING, CLEAN, INSPECTION, MAINTENANCE
    notes: Optional[str] = None


class HousekeepingInspectionCreate(BaseModel):
    is_passed: bool = True
    rating: Optional[float] = 5.0
    checklist: Optional[Dict[str, Any]] = None
    comments: Optional[str] = None


class HousekeepingTaskResponse(BaseModel):
    id: int
    hotel_id: int
    room_id: int
    assigned_staff_id: Optional[int] = None
    task_type: str
    status: str
    priority: str
    notes: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
