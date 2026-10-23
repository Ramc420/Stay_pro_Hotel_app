import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class JobType(str, enum.Enum):
    CHECKIN_REMINDER = "CHECKIN_REMINDER"
    CHECKOUT_REMINDER = "CHECKOUT_REMINDER"
    REVIEW_INVITATION = "REVIEW_INVITATION"
    EXPIRED_HOLD_RELEASE = "EXPIRED_HOLD_RELEASE"


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ScheduledJobLog(Base):
    """Tracks background jobs, scheduled guest reminders, and maintenance operations."""
    __tablename__ = "scheduled_job_logs"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(Enum(JobType), nullable=False, index=True)
    target_id = Column(Integer, nullable=True, index=True)  # e.g., booking_id or hotel_id
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    
    scheduled_for = Column(DateTime, nullable=False, index=True)
    executed_at = Column(DateTime, nullable=True)
    result_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
