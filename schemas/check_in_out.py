from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class VerifyBookingRequest(BaseModel):
    booking_reference: Optional[str] = None
    booking_id: Optional[int] = None


class CheckInRequest(BaseModel):
    booking_id: int
    room_id: Optional[int] = None
    early_check_in_hours: Optional[float] = 0.0
    early_check_in_fee: Optional[float] = 0.0
    notes: Optional[str] = None


class CheckOutRequest(BaseModel):
    booking_id: int
    late_check_out_hours: Optional[float] = 0.0
    late_check_out_fee: Optional[float] = 0.0
    notes: Optional[str] = None


class CheckInOutResponse(BaseModel):
    id: int
    booking_id: int
    hotel_id: int
    room_id: int
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    early_check_in_hours: float = 0.0
    early_check_in_fee: float = 0.0
    late_check_out_hours: float = 0.0
    late_check_out_fee: float = 0.0
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
