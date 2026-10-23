from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SecurityAlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: str
    status: str
    user_id: Optional[int] = None
    hotel_id: Optional[int] = None
    ip_address: Optional[str] = None
    title: str
    details: str
    resolution_notes: Optional[str] = None
    resolved_by_admin_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertResolveRequest(BaseModel):
    status: str = "RESOLVED"  # RESOLVED, FALSE_POSITIVE, DISMISSED
    resolution_notes: str = Field(..., min_length=3)


class LoginRiskEvaluationRequest(BaseModel):
    user_email: str
    ip_address: str
    failed_attempts_in_window: int = 0


class LoginRiskEvaluationResponse(BaseModel):
    risk_level: str  # LOW, MEDIUM, HIGH, BLOCKED
    is_suspicious: bool
    recommended_action: str  # ALLOW, REQUIRE_2FA, CAPTCHA, TEMPORARY_LOCK
    message: str


class FraudScanResponse(BaseModel):
    scanned_bookings_count: int
    scanned_payments_count: int
    new_alerts_flagged: int
    alerts: List[SecurityAlertResponse]


class SecurityMetricsResponse(BaseModel):
    total_open_alerts: int
    critical_alerts_count: int
    high_alerts_count: int
    medium_alerts_count: int
    resolved_alerts_count: int
    last_scan_at: Optional[datetime] = None
