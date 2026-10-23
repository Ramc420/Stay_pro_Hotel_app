from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class MenuItemCreate(BaseModel):
    name: str
    category: str = "MAIN_COURSE"  # BREAKFAST, APPETIZER, MAIN_COURSE, DESSERT, BEVERAGE
    price: float
    description: Optional[str] = None
    is_vegetarian: Optional[bool] = False


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    is_vegetarian: Optional[bool] = None
    is_available: Optional[bool] = None


class MenuItemResponse(BaseModel):
    id: int
    hotel_id: int
    name: str
    category: str
    price: float
    description: Optional[str] = None
    is_vegetarian: bool
    is_available: bool
    created_at: datetime

    class Config:
        from_attributes = True


class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int = 1


class OrderItemResponse(BaseModel):
    id: int
    menu_item_id: int
    item_name: str
    quantity: int
    unit_price: float
    total_price: float

    class Config:
        from_attributes = True


class RoomServiceOrderCreate(BaseModel):
    booking_id: int
    items: List[OrderItemCreate]
    notes: Optional[str] = None


class RoomServiceOrderResponse(BaseModel):
    id: int
    booking_id: int
    hotel_id: int
    room_id: int
    status: str
    subtotal: float
    service_charge: float
    total_amount: float
    notes: Optional[str] = None
    created_at: datetime
    delivered_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True
