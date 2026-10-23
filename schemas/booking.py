from typing import Optional, List, Any
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from models.booking import BookingStatus, PaymentStatus


class GuestInput(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    id_type: str = Field(default="PASSPORT", description="PASSPORT, NATIONAL_ID, DRIVING_LICENSE, OTHER")
    id_number: Optional[str] = Field(None, min_length=3, max_length=100)
    is_primary: bool = False
    guest_type: str = Field(default="ADULT", description="ADULT, CHILD")
    age: Optional[int] = Field(None, ge=0, le=120)
    special_requests: Optional[str] = None


class GuestResponse(BaseModel):
    id: int
    booking_id: int
    full_name: str
    email: Optional[str] = None
    phone_number: Optional[str] = None
    id_type: str
    id_number: Optional[str] = None
    is_primary: bool
    guest_type: str
    age: Optional[int] = None
    special_requests: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookingCreateRequest(BaseModel):
    hotel_id: int
    room_type_id: int
    room_id: Optional[int] = None  # If not provided, an available room will be auto-allocated
    check_in_date: date
    check_out_date: date
    guests: List[GuestInput] = Field(default=[], description="List of guests for the reservation")
    special_requests: Optional[str] = None

    @field_validator("check_out_date")
    def validate_dates(cls, v, info):
        if "check_in_date" in info.data and v <= info.data["check_in_date"]:
            raise ValueError("check_out_date must be strictly after check_in_date")
        return v


class BookingModifyRequest(BaseModel):
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    room_id: Optional[int] = None
    special_requests: Optional[str] = None


class BookingCancelRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=500)


class BookingStatusUpdateRequest(BaseModel):
    status: BookingStatus
    notes: Optional[str] = None


class BookingHistoryResponse(BaseModel):
    id: int
    booking_id: int
    action: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    changed_by_user_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookingResponse(BaseModel):
    id: int
    booking_reference: str
    user_id: int
    hotel_id: int
    hotel_name: Optional[str] = None
    room_id: int
    room_number: Optional[str] = None
    room_type_id: int
    room_type_name: Optional[str] = None
    check_in_date: date
    check_out_date: date
    total_nights: int
    nightly_price: float
    base_amount: float
    tax_amount: float
    total_amount: float
    status: BookingStatus
    payment_status: PaymentStatus
    special_requests: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    guests: List[GuestResponse] = []

    model_config = ConfigDict(from_attributes=True)
