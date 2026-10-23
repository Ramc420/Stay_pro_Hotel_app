from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class PlatformPolicy(Base):
    """Platform-wide policies, terms of service, cancellation standards, and legal agreements."""
    __tablename__ = "platform_policies"

    id = Column(Integer, primary_key=True, index=True)
    policy_type = Column(String(50), unique=True, nullable=False, index=True)  # TERMS_OF_SERVICE, CANCELLATION_POLICY, PRIVACY_POLICY, REFUND_POLICY
    title = Column(String(150), nullable=False)
    content = Column(Text, nullable=False)
    version = Column(String(20), default="1.0", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    updated_by = relationship("User")
