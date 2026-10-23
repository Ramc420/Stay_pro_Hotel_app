import time
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from models import (
    User, UserRole, Hotel, HotelStatus, Booking, BookingStatus,
    PlatformPolicy, SecurityAlert, AlertStatus, AuditLog
)
from crud.audit_logs import log_audit_event


DEFAULT_POLICIES = [
    {
        "policy_type": "TERMS_OF_SERVICE",
        "title": "Platform Terms of Service",
        "content": "All guests and hotel partners agree to standard safety, integrity, and verified booking protocols.",
        "version": "1.0"
    },
    {
        "policy_type": "CANCELLATION_POLICY",
        "title": "Universal Cancellation & Refund Guidelines",
        "content": "Standard cancellations up to 48 hours prior to check-in are eligible for a 100% refund less processing fees.",
        "version": "1.0"
    },
    {
        "policy_type": "PRIVACY_POLICY",
        "title": "Data Privacy and Guest Information Security",
        "content": "StayNest adheres to global privacy protection standards. Guest information is never sold to third parties.",
        "version": "1.0"
    }
]


def seed_default_policies(db: Session):
    """Seed default platform legal policies if not present."""
    for p in DEFAULT_POLICIES:
        existing = db.query(PlatformPolicy).filter(PlatformPolicy.policy_type == p["policy_type"]).first()
        if not existing:
            pol = PlatformPolicy(
                policy_type=p["policy_type"],
                title=p["title"],
                content=p["content"],
                version=p["version"],
                is_active=True
            )
            db.add(pol)
    db.commit()


def update_user_account_status(
    db: Session,
    target_user_id: int,
    is_active: bool,
    admin_id: int,
    reason: Optional[str] = None
) -> User:
    """Activate, deactivate, or suspend a user account with audit logging."""
    user = db.query(User).filter(User.id == target_user_id).first()
    if not user:
        raise ValueError(f"User {target_user_id} not found")

    old_status = "ACTIVE" if user.is_active else "INACTIVE"
    new_status = "ACTIVE" if is_active else "INACTIVE"
    user.is_active = is_active

    # Audit log
    log_audit_event(
        db=db,
        user_id=admin_id,
        event_type="ADMIN_ACTION",
        action="USER_STATUS_UPDATE",
        description=f"Admin #{admin_id} changed User #{target_user_id} status from {old_status} to {new_status}. Reason: {reason or 'Administrative decision'}",
        details={"target_user_id": target_user_id, "is_active": is_active, "reason": reason}
    )

    db.commit()
    db.refresh(user)
    return user


def override_hotel_status(
    db: Session,
    hotel_id: int,
    status_str: str,
    is_active: bool,
    admin_id: int,
    reason: str
) -> Hotel:
    """Administrative override of hotel status (APPROVED, SUSPENDED, REJECTED)."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise ValueError(f"Hotel {hotel_id} not found")

    old_status = hotel.status.value
    hotel.status = HotelStatus(status_str.upper())
    hotel.is_active = is_active
    hotel.is_approved = (hotel.status == HotelStatus.APPROVED)

    log_audit_event(
        db=db,
        user_id=admin_id,
        event_type="ADMIN_ACTION",
        action="HOTEL_STATUS_OVERRIDE",
        description=f"Admin #{admin_id} modified Hotel #{hotel_id} status to {hotel.status.value}. Reason: {reason}",
        details={"hotel_id": hotel_id, "old_status": old_status, "new_status": hotel.status.value, "reason": reason}
    )

    db.commit()
    db.refresh(hotel)
    return hotel


def emergency_override_booking_status(
    db: Session,
    booking_id: int,
    new_status_str: str,
    admin_id: int,
    reason: str
) -> Booking:
    """Administrative emergency status override for a reservation with audit trail."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise ValueError(f"Booking {booking_id} not found")

    old_status = booking.status.value
    booking.status = BookingStatus(new_status_str.upper())

    log_audit_event(
        db=db,
        user_id=admin_id,
        event_type="ADMIN_ACTION",
        action="BOOKING_STATUS_OVERRIDE",
        description=f"Admin #{admin_id} overrode Booking #{booking_id} ({booking.booking_reference}) from {old_status} to {booking.status.value}. Reason: {reason}",
        details={"booking_id": booking_id, "old_status": old_status, "new_status": booking.status.value, "reason": reason}
    )

    db.commit()
    db.refresh(booking)
    return booking


def get_platform_policies(db: Session) -> List[PlatformPolicy]:
    """Retrieve all standard platform policies."""
    return db.query(PlatformPolicy).order_by(PlatformPolicy.policy_type.asc()).all()


def update_platform_policy(
    db: Session,
    policy_type: str,
    content: str,
    admin_id: int,
    title: Optional[str] = None,
    version: Optional[str] = "1.0",
    is_active: Optional[bool] = True
) -> PlatformPolicy:
    """Create or update platform policy with versioning and audit record."""
    policy = db.query(PlatformPolicy).filter(PlatformPolicy.policy_type == policy_type.upper()).first()
    if not policy:
        policy = PlatformPolicy(
            policy_type=policy_type.upper(),
            title=title or policy_type.replace("_", " ").title(),
            content=content,
            version=version or "1.0",
            is_active=is_active if is_active is not None else True,
            updated_by_id=admin_id
        )
        db.add(policy)
    else:
        if title:
            policy.title = title
        policy.content = content
        if version:
            policy.version = version
        if is_active is not None:
            policy.is_active = is_active
        policy.updated_by_id = admin_id

    log_audit_event(
        db=db,
        user_id=admin_id,
        event_type="ADMIN_ACTION",
        action="POLICY_UPDATE",
        description=f"Admin #{admin_id} updated policy {policy_type.upper()} to version {policy.version}.",
        details={"policy_type": policy_type, "version": policy.version}
    )

    db.commit()
    db.refresh(policy)
    return policy


def perform_system_health_check(db: Session) -> Dict[str, Any]:
    """Diagnostic operational check: database latency, table discovery, and health metrics."""
    # Measure DB latency
    t0 = time.time()
    db.execute(text("SELECT 1")).scalar()
    latency_ms = round((time.time() - t0) * 1000.0, 2)

    db_status = "HEALTHY" if latency_ms < 500.0 else "DEGRADED"

    # Inspect tables
    inspector = inspect(db.bind)
    table_names = inspector.get_table_names()

    active_users = db.query(User).filter(User.is_active == True).count()
    active_hotels = db.query(Hotel).filter(Hotel.is_active == True, Hotel.is_approved == True).count()
    pending_bookings = db.query(Booking).filter(Booking.status == BookingStatus.PENDING).count()
    open_alerts = db.query(SecurityAlert).filter(SecurityAlert.status == AlertStatus.OPEN).count()

    overall = "HEALTHY"
    if latency_ms > 1000.0 or open_alerts > 20:
        overall = "WARNING"

    return {
        "timestamp": datetime.utcnow(),
        "overall_status": overall,
        "database": {
            "service_name": "MySQL Relational Engine",
            "status": db_status,
            "latency_ms": latency_ms,
            "details": f"Connected to {len(table_names)} database tables."
        },
        "active_users_count": active_users,
        "active_hotels_count": active_hotels,
        "pending_bookings_count": pending_bookings,
        "open_security_alerts": open_alerts,
        "total_db_tables": len(table_names)
    }
