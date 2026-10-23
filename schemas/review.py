from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ReviewCreate(BaseModel):
    hotel_id: Optional[int] = Field(None, description="Hotel ID (optional if booking_id provided, resolved from booking)")
    booking_id: Optional[int] = Field(None, description="Booking ID for the completed stay")
    rating: float = Field(..., ge=1.0, le=5.0, description="Rating from 1.0 to 5.0")
    comment: Optional[str] = Field(None, max_length=2000, description="Review feedback comment")


class ReviewUpdate(BaseModel):
    rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="Updated rating from 1.0 to 5.0")
    comment: Optional[str] = Field(None, max_length=2000, description="Updated feedback comment")


class ReviewReportRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=1000, description="Reason for reporting this review as inappropriate")


class ReviewModerationRequest(BaseModel):
    action: str = Field(..., description="Moderation action: 'APPROVE' (keep and clear flag), 'HIDE' (hide from public), or 'REMOVE' (delete)")
    notes: Optional[str] = Field(None, max_length=1000, description="Moderator notes")


class ReviewResponse(BaseModel):
    id: int
    hotel_id: int
    hotel_name: Optional[str] = None
    user_id: int
    user_name: Optional[str] = None
    booking_id: Optional[int] = None
    rating: float
    comment: Optional[str] = None
    is_reported: bool = False
    report_reason: Optional[str] = None
    reported_at: Optional[datetime] = None
    is_hidden: bool = False
    moderation_status: str = "APPROVED"
    moderation_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HotelReviewBreakdownResponse(BaseModel):
    hotel_id: int
    hotel_name: Optional[str] = None
    total_reviews: int
    average_rating: float
    rating_breakdown: Dict[int, int]
