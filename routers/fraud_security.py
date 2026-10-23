"""
Module 48: Fraud Detection and Security
Fraud pattern scanning, suspicious booking flags, failed payment tracking, and security alerts.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.dependencies import require_roles
from utils.response import api_response
from schemas.fraud_security import (
    AlertResolveRequest, LoginRiskEvaluationRequest
)
from crud import fraud_security as crud_sec

router = APIRouter(prefix="/security", tags=["Module 48: Fraud Detection and Security"])


@router.get("/alerts", summary="Retrieve platform security alerts (Admin only)")
def list_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    alerts = crud_sec.get_security_alerts(
        db, status_filter=status, severity_filter=severity, limit=limit
    )
    return api_response(
        success=True,
        message="Security alerts retrieved",
        data=[
            {
                "id": a.id,
                "alert_type": a.alert_type.value,
                "severity": a.severity.value,
                "status": a.status.value,
                "user_id": a.user_id,
                "hotel_id": a.hotel_id,
                "ip_address": a.ip_address,
                "title": a.title,
                "details": a.details,
                "resolution_notes": a.resolution_notes,
                "resolved_by_admin_id": a.resolved_by_admin_id,
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
                "created_at": a.created_at.isoformat()
            }
            for a in alerts
        ]
    )


@router.post("/scan-transactions", summary="Execute automated fraud detection scan across recent bookings & payments (Admin only)")
def run_fraud_scan(
    window_hours: int = 24,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    report = crud_sec.scan_and_flag_fraud_patterns(db, window_hours=window_hours)
    return api_response(
        success=True,
        message=f"Fraud scan completed. {report['new_alerts_flagged']} new alert(s) flagged.",
        data=report
    )


@router.post("/alerts/{alert_id}/resolve", summary="Resolve or dismiss security alert (Admin only)")
def resolve_alert(
    alert_id: int,
    request: AlertResolveRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    try:
        alert = crud_sec.resolve_security_alert(
            db=db,
            alert_id=alert_id,
            admin_id=current_user.id,
            status=request.status,
            resolution_notes=request.resolution_notes
        )
        return api_response(
            success=True,
            message=f"Alert #{alert_id} updated to {alert.status.value}",
            data={
                "id": alert.id,
                "status": alert.status.value,
                "resolution_notes": alert.resolution_notes,
                "resolved_at": alert.resolved_at.isoformat()
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/check-login-risk", summary="Evaluate login attempt risk and suspicious patterns")
def check_login(
    request: LoginRiskEvaluationRequest,
    db: Session = Depends(get_db)
):
    evaluation = crud_sec.evaluate_login_risk(
        db=db,
        user_email=request.user_email,
        ip_address=request.ip_address,
        failed_attempts_in_window=request.failed_attempts_in_window
    )
    return api_response(
        success=True,
        message=evaluation["message"],
        data=evaluation
    )


@router.get("/metrics", summary="Retrieve high-level security metrics and posture summary (Admin only)")
def get_metrics(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    metrics = crud_sec.get_security_metrics(db)
    return api_response(
        success=True,
        message="Security metrics retrieved",
        data=metrics
    )
