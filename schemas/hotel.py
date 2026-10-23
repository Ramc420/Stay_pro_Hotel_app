from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from models.hotel import HotelStatus


class HotelRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    property_type: str = Field(default="HOTEL", description="HOTEL, RESORT, VILLA, APARTMENT, BOUTIQUE, MOTEL")
    email: EmailStr
    phone: str = Field(..., min_length=5, max_length=50)
    website: Optional[str] = None
    address_line1: str = Field(..., min_length=3)
    address_line2: Optional[str] = None
    city: str = Field(..., min_length=2)
    state: str = Field(..., min_length=2)
    country: str = Field(..., min_length=2)
    postal_code: str = Field(..., min_length=2)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    check_in_time: str = Field(default="14:00")
    check_out_time: str = Field(default="11:00")
    cancellation_policy: Optional[str] = None
    house_rules: Optional[str] = None


class HotelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    property_type: Optional[str] = None
    star_rating: Optional[float] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    cancellation_policy: Optional[str] = None
    house_rules: Optional[str] = None
    is_active: Optional[bool] = None


class HotelVerificationDocCreate(BaseModel):
    document_type: str = Field(..., description="BUSINESS_LICENSE, FIRE_SAFETY_CERTIFICATE, TAX_REGISTRATION, PROPERTY_DEED")
    document_url: str
    document_number: Optional[str] = None


class HotelVerificationDocResponse(BaseModel):
    id: int
    hotel_id: int
    document_type: str
    document_url: str
    document_number: Optional[str] = None
    verification_status: str
    remarks: Optional[str] = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HotelApprovalAction(BaseModel):
    status: HotelStatus = Field(..., description="APPROVED or REJECTED")
    rejection_reason: Optional[str] = None


class HotelSuspendAction(BaseModel):
    suspend: bool = Field(..., description="True to suspend, False to reactivate")
    reason: Optional[str] = None


class HotelImageCreate(BaseModel):
    image_url: str
    title: Optional[str] = None
    caption: Optional[str] = None
    image_type: Optional[str] = "GALLERY"
    is_primary: bool = False
    display_order: int = 0


class HotelImageUpdate(BaseModel):
    title: Optional[str] = None
    caption: Optional[str] = None
    image_type: Optional[str] = None
    is_primary: Optional[bool] = None
    display_order: int = None


class HotelImageResponse(BaseModel):
    id: int
    hotel_id: int
    image_url: str
    title: Optional[str] = None
    caption: Optional[str] = None
    image_type: str = "GALLERY"
    is_primary: bool
    display_order: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)



class HotelResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    description: Optional[str] = None
    property_type: str
    star_rating: float
    email: str
    phone: str
    website: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    country: str
    postal_code: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    check_in_time: str
    check_out_time: str
    cancellation_policy: Optional[str] = None
    house_rules: Optional[str] = None
    is_approved: bool
    status: HotelStatus
    rejection_reason: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    images: List[HotelImageResponse] = []
    amenities: List[Any] = []

    model_config = ConfigDict(from_attributes=True)


class HotelPolicyResponse(BaseModel):
    check_in_time: str = "14:00"
    check_out_time: str = "11:00"
    cancellation_policy: Optional[str] = None
    house_rules: Optional[str] = None


class HotelReviewSummary(BaseModel):
    total_reviews: int = 0
    average_rating: float = 0.0
    rating_breakdown: dict = Field(default_factory=dict)


class HotelDetailsResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    description: Optional[str] = None
    property_type: str
    star_rating: float
    email: str
    phone: str
    website: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    country: str
    postal_code: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    policies: HotelPolicyResponse
    is_approved: bool
    status: HotelStatus
    rejection_reason: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    images: List[HotelImageResponse] = []
    amenities: List[Any] = []
    room_types: List[Any] = []
    reviews_summary: Optional[HotelReviewSummary] = None
    reviews: List[Any] = []

    model_config = ConfigDict(from_attributes=True)

