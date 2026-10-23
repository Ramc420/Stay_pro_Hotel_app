from typing import Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict
from schemas.user import UserResponse


class CustomerProfileBase(BaseModel):
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    travel_preferences: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {"smoking": False, "dietary": "None", "room_floor": "high", "bed_preference": "King"}
    )
    profile_picture_url: Optional[str] = None


class CustomerProfileCreate(CustomerProfileBase):
    pass


class CustomerProfileUpdate(BaseModel):
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    travel_preferences: Optional[Dict[str, Any]] = None
    profile_picture_url: Optional[str] = None


class CustomerProfileResponse(CustomerProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    user: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)
