import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class SupportSender(str, enum.Enum):
    USER = "USER"
    BOT = "BOT"
    AGENT = "AGENT"


class SupportConversation(Base):
    __tablename__ = "support_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject = Column(String(200), default="Customer Support Inquiry", nullable=False)
    status = Column(String(50), default="OPEN", nullable=False)  # OPEN, RESOLVED, CLOSED
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")
    messages = relationship("SupportMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="SupportMessage.created_at")


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("support_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(Enum(SupportSender), default=SupportSender.USER, nullable=False)
    message = Column(Text, nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    conversation = relationship("SupportConversation", back_populates="messages")
    booking = relationship("Booking")
