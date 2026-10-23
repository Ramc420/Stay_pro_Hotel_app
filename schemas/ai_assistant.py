from typing import Optional, List, Any, Dict
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict


class TripPlanRequest(BaseModel):
    destination: str = Field(..., min_length=2, max_length=100, description="City, region, or country of travel")
    budget: Optional[float] = Field(None, gt=0, description="Total budget in USD for the trip")
    start_date: Optional[date] = Field(None, description="Trip planned start date")
    end_date: Optional[date] = Field(None, description="Trip planned end date")
    travel_style: Optional[str] = Field("balanced", description="Travel style: 'luxury', 'budget', 'romantic', 'family', 'adventure', 'wellness'")
    preferred_amenities: Optional[List[str]] = Field(None, description="Preferred amenities like Swimming Pool, Free Wi-Fi, Spa")
    guests_count: int = Field(1, ge=1, le=20, description="Number of travelers")
    special_preferences: Optional[str] = Field(None, max_length=500, description="Specific dietary, activity, or accommodation requests")


class DayItineraryItem(BaseModel):
    day: int
    title: str
    morning: str
    afternoon: str
    evening: str
    recommended_dining: List[str]
    local_tip: Optional[str] = None


class TripPlanResponse(BaseModel):
    destination: str
    duration_days: int
    travel_style: str
    estimated_budget: Optional[float] = None
    trip_summary: str
    daily_itinerary: List[DayItineraryItem]
    suggested_hotels: List[Dict[str, Any]]
    packing_and_travel_tips: List[str]
    ai_provider_used: str


class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User's query or instruction for the AI assistant")
    conversation_id: Optional[int] = Field(None, description="Existing conversation ID to continue context, or None to start a new conversation")
    destination: Optional[str] = Field(None, description="Optional destination focus")


class AIChatResponse(BaseModel):
    conversation_id: int
    conversation_title: str
    reply: str
    suggested_hotels: Optional[List[Dict[str, Any]]] = None
    itinerary_data: Optional[Dict[str, Any]] = None
    provider: str


class AIMessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    suggested_hotels: Optional[Any] = None
    itinerary_data: Optional[Any] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIConversationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    destination: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[AIMessageResponse]] = None

    model_config = ConfigDict(from_attributes=True)
