from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class ServiceCreate(BaseModel):
    name: str
    category: str = "OTHER"  # LAUNDRY, SPA, RESTAURANT, AIRPORT_PICKUP, EXTRA_BED, OTHER
    price: float
    description: Optional[str] = None


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ServiceResponse(BaseModel):
    id: int
    hotel_id: int
    name: str
    category: str
    price: float
    description: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ServiceRequestCreate(BaseModel):
    booking_id: int
    service_id: int
    quantity: Optional[int] = 1
    special_instructions: Optional[str] = None


class ServiceRequestResponse(BaseModel):
    id: int
    booking_id: int
    hotel_id: int
    service_id: int
    quantity: int
    unit_price: float
    total_price: float
    status: str
    special_instructions: Optional[str] = None
    requested_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
