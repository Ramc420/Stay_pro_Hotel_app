from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class AuditLogCreate(BaseModel):
    event_type: str  # LOGIN, LOGOUT, BOOKING_CREATE, PAYMENT, MODERATION, SECURITY
    action: str
    description: str
    ip_address: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    event_type: str
    action: str
    ip_address: Optional[str] = None
    description: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
