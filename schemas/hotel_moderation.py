from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class HotelModerationActionRequest(BaseModel):
    reason: str
    notes: Optional[str] = None


class HotelModerationLogResponse(BaseModel):
    id: int
    hotel_id: int
    admin_id: Optional[int] = None
    action: str
    reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
