from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class WishlistCreate(BaseModel):
    hotel_id: int = Field(..., description="Hotel ID to add to favorites")
    room_id: Optional[int] = Field(None, description="Optional specific room ID")
    room_type_id: Optional[int] = Field(None, description="Optional specific room type ID")
    notes: Optional[str] = Field(None, max_length=255, description="Personal travel note (e.g. 'Saved for anniversary trip')")


class WishlistResponse(BaseModel):
    id: int
    user_id: int
    hotel_id: int
    hotel_name: Optional[str] = None
    hotel_city: Optional[str] = None
    hotel_country: Optional[str] = None
    hotel_star_rating: Optional[float] = None
    hotel_primary_image: Optional[str] = None
    room_id: Optional[int] = None
    room_number: Optional[str] = None
    room_type_id: Optional[int] = None
    room_type_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WishlistCheckResponse(BaseModel):
    hotel_id: int
    is_favorite: bool
    wishlist_id: Optional[int] = None
