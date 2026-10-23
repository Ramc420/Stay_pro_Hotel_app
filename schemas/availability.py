from typing import Optional
from datetime import date
from pydantic import BaseModel, Field, field_validator, ConfigDict
from models.availability import AvailabilityStatus


class RoomAvailabilitySet(BaseModel):
    room_id: int
    date: date
    status: AvailabilityStatus = AvailabilityStatus.AVAILABLE
    price_override: Optional[float] = None


class RoomAvailabilityBulkSet(BaseModel):
    room_id: int
    start_date: date
    end_date: date
    status: AvailabilityStatus = AvailabilityStatus.AVAILABLE
    price_override: Optional[float] = None

    @field_validator("end_date")
    def validate_dates(cls, v, info):
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be greater than or equal to start_date")
        return v


class RoomAvailabilityResponse(BaseModel):
    id: int
    room_id: int
    date: date
    status: AvailabilityStatus
    price_override: Optional[float] = None
    booking_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
