import enum
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class NotificationType(str, enum.Enum):
    BOOKING = "BOOKING"
    PAYMENT = "PAYMENT"
    CANCELLATION = "CANCELLATION"
    REFUND = "REFUND"
    CHECK_IN_REMINDER = "CHECK_IN_REMINDER"
    CHECK_OUT_REMINDER = "CHECK_OUT_REMINDER"
    SYSTEM = "SYSTEM"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(Enum(NotificationType), default=NotificationType.SYSTEM, nullable=False, index=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    user = relationship("User")
