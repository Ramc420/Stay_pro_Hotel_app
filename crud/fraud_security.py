from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import (
    SecurityAlert, AlertType, AlertSeverity, AlertStatus,
    Booking, BookingStatus, Payment, PaymentStatus, User, Hotel
)


def create_security_alert(
    db: Session,
    alert_type: str,
    severity: str,
    title: str,
    details: str,
    user_id: Optional[int] = None,
    hotel_id: Optional[int] = None,
    ip_address: Optional[str] = None
) -> SecurityAlert:
    """Record a new security alert with severity classification."""
    alert = SecurityAlert(
        alert_type=AlertType(alert_type.upper()),
        severity=AlertSeverity(severity.upper()),
        status=AlertStatus.OPEN,
        user_id=user_id,
        hotel_id=hotel_id,
        ip_address=ip_address,
        title=title,
        details=details
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def get_security_alerts(
    db: Session,
    status_filter: Optional[str] = None,
    severity_filter: Optional[str] = None,
    limit: int = 50
) -> List[SecurityAlert]:
    """Retrieve filtered list of security incidents."""
    query = db.query(SecurityAlert)
    if status_filter:
        query = query.filter(SecurityAlert.status == AlertStatus(status_filter.upper()))
    if severity_filter:
        query = query.filter(SecurityAlert.severity == AlertSeverity(severity_filter.upper()))
    return query.order_by(SecurityAlert.created_at.desc()).limit(limit).all()


def resolve_security_alert(
    db: Session,
    alert_id: int,
    admin_id: int,
    status: str = "RESOLVED",
    resolution_notes: Optional[str] = None
) -> SecurityAlert:
    """Resolve or dismiss an alert with administrative review notes."""
    alert = db.query(SecurityAlert).filter(SecurityAlert.id == alert_id).first()
    if not alert:
        raise ValueError(f"Security alert {alert_id} not found")

    alert.status = AlertStatus(status.upper())
    alert.resolved_by_admin_id = admin_id
    alert.resolution_notes = resolution_notes
    alert.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(alert)
    return alert


def evaluate_login_risk(
    db: Session,
    user_email: str,
    ip_address: str,
    failed_attempts_in_window: int = 0
) -> Dict[str, Any]:
    """Evaluate login risk based on rapid failures and suspicious IP."""
    if failed_attempts_in_window >= 5:
        # High risk: trigger security alert
        user = db.query(User).filter(User.email == user_email).first()
        create_security_alert(
            db=db,
            alert_type="SUSPICIOUS_LOGIN",
            severity="HIGH",
            title=f"Brute force login alert for {user_email}",
            details=f"{failed_attempts_in_window} consecutive failed login attempts detected from IP {ip_address}.",
            user_id=user.id if user else None,
            ip_address=ip_address
        )
        return {
            "risk_level": "HIGH",
            "is_suspicious": True,
            "recommended_action": "TEMPORARY_LOCK",
            "message": "Account temporarily locked due to repeated failed logins. High security risk."
        }
    elif failed_attempts_in_window >= 3:
        return {
            "risk_level": "MEDIUM",
            "is_suspicious": True,
            "recommended_action": "REQUIRE_2FA",
            "message": "Elevated failed login attempts. Two-factor authentication verification recommended."
        }

    return {
        "risk_level": "LOW",
        "is_suspicious": False,
        "recommended_action": "ALLOW",
        "message": "Normal login behavior detected."
    }


def scan_and_flag_fraud_patterns(db: Session, window_hours: int = 24) -> Dict[str, Any]:
    """Scan recent transactions to automatically flag duplicate bookings, rapid attempts, and failed payments."""
    now = datetime.utcnow()
    window_start = now - timedelta(hours=window_hours)

    new_alerts = []

    # 1. Detect duplicate bookings (same user, same hotel, overlapping dates created recently)
    recent_bookings = db.query(Booking).filter(Booking.created_at >= window_start).all()
    user_bookings_map = {}
    for b in recent_bookings:
        user_bookings_map.setdefault(b.user_id, []).append(b)

    for uid, b_list in user_bookings_map.items():
        if len(b_list) >= 4:
            # Rapid bookings threshold
            alert = create_security_alert(
                db=db,
                alert_type="RAPID_BOOKINGS",
                severity="HIGH",
                title=f"Rapid booking spike by User #{uid}",
                details=f"User #{uid} placed {len(b_list)} bookings within {window_hours} hours.",
                user_id=uid
            )
            new_alerts.append(alert)

        # Check duplicate intervals
        for i in range(len(b_list)):
            for j in range(i + 1, len(b_list)):
                b1 = b_list[i]
                b2 = b_list[j]
                if b1.hotel_id == b2.hotel_id and b1.check_in_date == b2.check_in_date and b1.room_type_id == b2.room_type_id:
                    alert = create_security_alert(
                        db=db,
                        alert_type="DUPLICATE_BOOKINGS",
                        severity="MEDIUM",
                        title=f"Potential duplicate reservation by User #{uid}",
                        details=f"Identical stay dates ({b1.check_in_date}) booked twice: Ref {b1.booking_reference} and Ref {b2.booking_reference}.",
                        user_id=uid,
                        hotel_id=b1.hotel_id
                    )
                    new_alerts.append(alert)

    # 2. Repeated failed payments
    failed_payments = db.query(Payment).filter(
        Payment.status == "FAILED",
        Payment.created_at >= window_start
    ).all()

    if len(failed_payments) >= 3:
        alert = create_security_alert(
            db=db,
            alert_type="FAILED_PAYMENTS",
            severity="HIGH",
            title=f"Multiple failed payment attempts detected",
            details=f"Detected {len(failed_payments)} failed payment transactions in the past {window_hours} hours."
        )
        new_alerts.append(alert)

    # Scanned counts
    b_count = len(recent_bookings)
    p_count = db.query(Payment).filter(Payment.created_at >= window_start).count()

    return {
        "scanned_bookings_count": b_count,
        "scanned_payments_count": p_count,
        "new_alerts_flagged": len(new_alerts),
        "alerts": [
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
                "created_at": a.created_at
            }
            for a in new_alerts
        ]
    }


def get_security_metrics(db: Session) -> Dict[str, Any]:
    """Summary metrics of platform security and fraud posture."""
    total_open = db.query(SecurityAlert).filter(SecurityAlert.status == AlertStatus.OPEN).count()
    crit_count = db.query(SecurityAlert).filter(
        SecurityAlert.status == AlertStatus.OPEN,
        SecurityAlert.severity == AlertSeverity.CRITICAL
    ).count()
    high_count = db.query(SecurityAlert).filter(
        SecurityAlert.status == AlertStatus.OPEN,
        SecurityAlert.severity == AlertSeverity.HIGH
    ).count()
    med_count = db.query(SecurityAlert).filter(
        SecurityAlert.status == AlertStatus.OPEN,
        SecurityAlert.severity == AlertSeverity.MEDIUM
    ).count()
    resolved_count = db.query(SecurityAlert).filter(SecurityAlert.status == AlertStatus.RESOLVED).count()

    return {
        "total_open_alerts": total_open,
        "critical_alerts_count": crit_count,
        "high_alerts_count": high_count,
        "medium_alerts_count": med_count,
        "resolved_alerts_count": resolved_count,
        "last_scan_at": datetime.utcnow()
    }
