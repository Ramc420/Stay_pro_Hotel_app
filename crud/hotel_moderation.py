from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from models import Hotel, HotelStatus, HotelModerationLog, HotelVerificationDocument


def get_pending_verification_hotels(db: Session) -> List[Hotel]:
    """Retrieve hotels awaiting verification approval."""
    return db.query(Hotel).filter(
        Hotel.status == HotelStatus.PENDING_APPROVAL
    ).order_by(Hotel.created_at.desc()).all()


def approve_hotel(
    db: Session,
    hotel_id: int,
    admin_id: int,
    notes: Optional[str] = None
) -> Hotel:
    """Approve a hotel application and log the administrative decision."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise ValueError(f"Hotel with ID {hotel_id} not found")

    prev_status = str(hotel.status.value) if hasattr(hotel.status, "value") else str(hotel.status)
    hotel.is_approved = True
    hotel.status = HotelStatus.APPROVED
    hotel.rejection_reason = None

    log = HotelModerationLog(
        hotel_id=hotel.id,
        admin_id=admin_id,
        action="APPROVED",
        previous_status=prev_status,
        new_status=HotelStatus.APPROVED.value,
        reason="Verification documents verified successfully",
        notes=notes
    )
    db.add(log)
    db.commit()
    db.refresh(hotel)
    return hotel


def reject_hotel(
    db: Session,
    hotel_id: int,
    admin_id: int,
    reason: str,
    notes: Optional[str] = None
) -> Hotel:
    """Reject a hotel onboarding application with recorded reason."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise ValueError(f"Hotel with ID {hotel_id} not found")

    prev_status = str(hotel.status.value) if hasattr(hotel.status, "value") else str(hotel.status)
    hotel.is_approved = False
    hotel.status = HotelStatus.REJECTED
    hotel.rejection_reason = reason

    log = HotelModerationLog(
        hotel_id=hotel.id,
        admin_id=admin_id,
        action="REJECTED",
        previous_status=prev_status,
        new_status=HotelStatus.REJECTED.value,
        reason=reason,
        notes=notes
    )
    db.add(log)
    db.commit()
    db.refresh(hotel)
    return hotel


def suspend_hotel(
    db: Session,
    hotel_id: int,
    admin_id: int,
    reason: str,
    notes: Optional[str] = None
) -> Hotel:
    """Suspend a hotel due to policy violations or complaints."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise ValueError(f"Hotel with ID {hotel_id} not found")

    prev_status = str(hotel.status.value) if hasattr(hotel.status, "value") else str(hotel.status)
    hotel.status = HotelStatus.SUSPENDED
    hotel.is_active = False

    log = HotelModerationLog(
        hotel_id=hotel.id,
        admin_id=admin_id,
        action="SUSPENDED",
        previous_status=prev_status,
        new_status=HotelStatus.SUSPENDED.value,
        reason=reason,
        notes=notes
    )
    db.add(log)
    db.commit()
    db.refresh(hotel)
    return hotel


def reactivate_hotel(
    db: Session,
    hotel_id: int,
    admin_id: int,
    notes: Optional[str] = None
) -> Hotel:
    """Lift suspension and reactivate hotel."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise ValueError(f"Hotel with ID {hotel_id} not found")

    prev_status = str(hotel.status.value) if hasattr(hotel.status, "value") else str(hotel.status)
    hotel.status = HotelStatus.APPROVED
    hotel.is_active = True

    log = HotelModerationLog(
        hotel_id=hotel.id,
        admin_id=admin_id,
        action="REACTIVATED",
        previous_status=prev_status,
        new_status=HotelStatus.APPROVED.value,
        reason="Suspension lifted after review",
        notes=notes
    )
    db.add(log)
    db.commit()
    db.refresh(hotel)
    return hotel


def get_moderation_logs(db: Session, hotel_id: int) -> List[HotelModerationLog]:
    """Retrieve decision audit history for a hotel."""
    return db.query(HotelModerationLog).filter(
        HotelModerationLog.hotel_id == hotel_id
    ).order_by(HotelModerationLog.created_at.desc()).all()
