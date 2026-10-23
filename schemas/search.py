from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class HotelSearchResult(BaseModel):
    id: int
    name: str
    property_type: str
    star_rating: float
    city: str
    state: str
    country: str
    address_line1: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_km: Optional[float] = None
    min_price_per_night: Optional[float] = None
    primary_image: Optional[str] = None
    available_room_types: List[str] = []
    amenities: List[str] = []
    check_in_time: str
    check_out_time: str

    model_config = ConfigDict(from_attributes=True)
