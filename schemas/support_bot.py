from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class SupportChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    booking_reference: Optional[str] = None


class SupportMessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender: str
    message: str
    booking_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SupportConversationResponse(BaseModel):
    id: int
    user_id: int
    subject: str
    status: str
    created_at: datetime
    messages: List[SupportMessageResponse] = []

    class Config:
        from_attributes = True
