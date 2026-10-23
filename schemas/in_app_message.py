from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class ConversationCreate(BaseModel):
    hotel_id: Optional[int] = None
    subject: str = "General Inquiry"
    conversation_type: Optional[str] = "HOTEL"  # HOTEL, SUPPORT
    initial_message: Optional[str] = None


class ChatMessageCreate(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    message: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: int
    customer_id: int
    hotel_id: Optional[int] = None
    subject: str
    conversation_type: str
    last_message_at: datetime
    created_at: datetime
    unread_count: Optional[int] = 0

    class Config:
        from_attributes = True
