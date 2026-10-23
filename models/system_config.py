from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class SystemConfig(Base):
    """Platform system settings, tax rates, commissions, currencies, and notifications."""
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    category = Column(String(50), default="GENERAL", nullable=False, index=True)  # FINANCIAL, EMAIL, PAYMENT, GENERAL, SECURITY
    is_secret = Column(Boolean, default=False, nullable=False)  # If true, masked in responses
    description = Column(String(255), nullable=True)
    
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    updated_by = relationship("User")
