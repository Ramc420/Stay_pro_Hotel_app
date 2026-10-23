from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class CoordinatesUpdate(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    formatted_address: Optional[str] = None


class HotelAttractionCreate(BaseModel):
    name: str
    category: str = "LANDMARK"  # BEACH, LANDMARK, AIRPORT, DINING, SHOPPING
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    description: Optional[str] = None
    icon: Optional[str] = "map-pin"


class HotelAttractionResponse(BaseModel):
    id: int
    hotel_id: int
    name: str
    category: str
    latitude: float
    longitude: float
    distance_km: Optional[float] = None
    distance_miles: Optional[float] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DistanceCalculationRequest(BaseModel):
    origin_lat: float = Field(..., ge=-90.0, le=90.0)
    origin_lon: float = Field(..., ge=-180.0, le=180.0)
    destination_lat: float = Field(..., ge=-90.0, le=90.0)
    destination_lon: float = Field(..., ge=-180.0, le=180.0)


class DistanceCalculationResponse(BaseModel):
    distance_km: float
    distance_miles: float
    estimated_drive_minutes: int
    provider: str
    status: str


class NearbyHotelResponse(BaseModel):
    hotel_id: int
    hotel_name: str
    address: str
    city: str
    latitude: float
    longitude: float
    distance_km: float
    distance_miles: float
    star_rating: float
    property_type: str
