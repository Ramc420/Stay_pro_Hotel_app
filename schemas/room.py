from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from models.room import RoomStatus


class RoomTypeCreate(BaseModel):
    name: str = Field(..., description="Single, Double, Deluxe, Suite, Family, etc.")
    code: str = Field(..., description="Short code e.g. SGL, DBL, DLX, SUI, FAM")
    description: Optional[str] = None
    base_price_per_night: float = Field(..., gt=0)
    max_occupancy: int = Field(default=2, gt=0)
    max_adults: int = Field(default=2, gt=0)
    max_children: int = Field(default=1, ge=0)
    bed_type: str = Field(default="Queen")
    room_size_sqft: Optional[float] = None
    amenities_included: Optional[List[str]] = None
    image_urls: Optional[List[str]] = None


class RoomTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_price_per_night: Optional[float] = Field(None, gt=0)
    max_occupancy: Optional[int] = Field(None, gt=0)
    max_adults: Optional[int] = Field(None, gt=0)
    max_children: Optional[int] = Field(None, ge=0)
    bed_type: Optional[str] = None
    room_size_sqft: Optional[float] = None
    amenities_included: Optional[List[str]] = None
    image_urls: Optional[List[str]] = None
    is_active: Optional[bool] = None


class RoomTypeResponse(BaseModel):
    id: int
    hotel_id: int
    name: str
    code: str
    description: Optional[str] = None
    base_price_per_night: float
    max_occupancy: int
    max_adults: int
    max_children: int
    bed_type: str
    room_size_sqft: Optional[float] = None
    amenities_included: Optional[List[str]] = None
    image_urls: Optional[List[str]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoomCreate(BaseModel):
    hotel_id: int
    room_type_id: int
    room_number: str = Field(..., min_length=1, max_length=50)
    floor_number: Optional[int] = None
    status: RoomStatus = RoomStatus.AVAILABLE


class RoomUpdate(BaseModel):
    room_type_id: Optional[int] = None
    room_number: Optional[str] = None
    floor_number: Optional[int] = None
    status: Optional[RoomStatus] = None
    is_active: Optional[bool] = None


class RoomStatusUpdate(BaseModel):
    status: RoomStatus


class RoomResponse(BaseModel):
    id: int
    hotel_id: int
    room_type_id: int
    room_number: str
    floor_number: Optional[int] = None
    status: RoomStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime
    room_type: Optional[RoomTypeResponse] = None

    model_config = ConfigDict(from_attributes=True)
