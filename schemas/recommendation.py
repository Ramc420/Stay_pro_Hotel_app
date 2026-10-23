from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class HotelRecommendationItem(BaseModel):
    hotel_id: int
    name: str
    property_type: str
    star_rating: float
    city: str
    country: str
    starting_price: Optional[float] = None
    primary_image_url: Optional[str] = None
    similarity_score: float
    match_percentage: int
    recommendation_reasons: List[str]
    amenities: List[str]

    model_config = ConfigDict(from_attributes=True)


class HotelRecommendationResponse(BaseModel):
    recommendations: List[HotelRecommendationItem]
    total: int
    algorithm_applied: str
    ai_enhanced: bool
    context_notes: Optional[str] = None
