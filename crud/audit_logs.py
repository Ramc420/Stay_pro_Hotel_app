from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from models import AuditLog


def log_audit_event(
    db: Session,
    event_type: str,  # LOGIN, LOGOUT, BOOKING_CREATE, PAYMENT, MODERATION, SECURITY
    action: str,
    description: str,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """
    Append-only audit logger.
    Logs are strictly immutable to prevent unauthorized modification.
    """
    log = AuditLog(
        user_id=user_id,
        event_type=event_type.upper(),
        action=action.upper(),
        description=description,
        ip_address=ip_address,
        details=details or {},
        created_at=datetime.utcnow()
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_audit_logs(
    db: Session,
    event_type: Optional[str] = None,
    user_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0
) -> List[AuditLog]:
    """Retrieve audit events with optional filtering."""
    query = db.query(AuditLog)
    if event_type:
        query = query.filter(AuditLog.event_type == event_type.upper())
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()


def get_security_events(db: Session, limit: int = 50) -> List[AuditLog]:
    """Retrieve security-critical events (failed logins, permission warnings, suspicious changes)."""
    return db.query(AuditLog).filter(
        AuditLog.event_type.in_(["SECURITY", "SECURITY_ALERT", "AUTH_FAILURE", "PERMISSION_DENIED"])
    ).order_by(AuditLog.created_at.desc()).limit(limit).all()
