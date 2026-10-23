import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class AlertType(str, enum.Enum):
    FAILED_PAYMENTS = "FAILED_PAYMENTS"
    RAPID_BOOKINGS = "RAPID_BOOKINGS"
    DUPLICATE_BOOKINGS = "DUPLICATE_BOOKINGS"
    SUSPICIOUS_LOGIN = "SUSPICIOUS_LOGIN"
    HIGH_RISK_CANCEL = "HIGH_RISK_CANCEL"


class AlertSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, enum.Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    DISMISSED = "DISMISSED"


class SecurityAlert(Base):
    """Fraud detection and security alerts for suspicious transactions and activities."""
    __tablename__ = "security_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(Enum(AlertType), nullable=False, index=True)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.MEDIUM, nullable=False, index=True)
    status = Column(Enum(AlertStatus), default=AlertStatus.OPEN, nullable=False, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="SET NULL"), nullable=True, index=True)
    ip_address = Column(String(50), nullable=True)
    
    title = Column(String(200), nullable=False)
    details = Column(Text, nullable=False)
    resolution_notes = Column(Text, nullable=True)
    resolved_by_admin_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)

    user = relationship("User", foreign_keys=[user_id])
    hotel = relationship("Hotel", foreign_keys=[hotel_id])
    resolver = relationship("User", foreign_keys=[resolved_by_admin_id])
