from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from models import Notification, NotificationType


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: NotificationType = NotificationType.SYSTEM,
    data: Optional[Dict[str, Any]] = None
) -> Notification:
    """Create and persist a new in-app notification."""
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        is_read=False,
        data=data or {}
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def get_user_notifications(
    db: Session,
    user_id: int,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0
) -> List[Notification]:
    """Retrieve notifications for a user, sorted newest first."""
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    return query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()


def get_unread_count(db: Session, user_id: int) -> int:
    """Return count of unread notifications for a user."""
    return db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).count()


def mark_notification_as_read(db: Session, notification_id: int, user_id: int) -> Optional[Notification]:
    """Mark a specific notification as read if owned by the user."""
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    if notif:
        notif.is_read = True
        db.commit()
        db.refresh(notif)
    return notif


def mark_all_as_read(db: Session, user_id: int) -> int:
    """Mark all unread notifications for a user as read. Returns count updated."""
    updated = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()
    return updated


# Helper generators for automated business notifications
def notify_booking_created(db: Session, user_id: int, booking_ref: str, hotel_name: str) -> Notification:
    return create_notification(
        db, user_id,
        title="Reservation Confirmed",
        message=f"Your booking {booking_ref} at {hotel_name} has been placed successfully.",
        notification_type=NotificationType.BOOKING,
        data={"booking_ref": booking_ref}
    )


def notify_payment_success(db: Session, user_id: int, amount: float, booking_ref: str) -> Notification:
    return create_notification(
        db, user_id,
        title="Payment Successful",
        message=f"We received your payment of ${amount:.2f} for reservation {booking_ref}.",
        notification_type=NotificationType.PAYMENT,
        data={"booking_ref": booking_ref, "amount": amount}
    )


def notify_cancellation(db: Session, user_id: int, booking_ref: str) -> Notification:
    return create_notification(
        db, user_id,
        title="Reservation Cancelled",
        message=f"Your reservation {booking_ref} has been cancelled.",
        notification_type=NotificationType.CANCELLATION,
        data={"booking_ref": booking_ref}
    )


def notify_refund_processed(db: Session, user_id: int, refund_amount: float, booking_ref: str) -> Notification:
    return create_notification(
        db, user_id,
        title="Refund Processed",
        message=f"A refund of ${refund_amount:.2f} has been processed for booking {booking_ref}.",
        notification_type=NotificationType.REFUND,
        data={"booking_ref": booking_ref, "refund_amount": refund_amount}
    )


def notify_check_in_reminder(db: Session, user_id: int, booking_ref: str, hotel_name: str, check_in_date: str) -> Notification:
    return create_notification(
        db, user_id,
        title="Check-In Reminder",
        message=f"Your stay at {hotel_name} begins on {check_in_date}. Standard check-in starts at 14:00.",
        notification_type=NotificationType.CHECK_IN_REMINDER,
        data={"booking_ref": booking_ref}
    )


def notify_check_out_reminder(db: Session, user_id: int, booking_ref: str, hotel_name: str, check_out_date: str) -> Notification:
    return create_notification(
        db, user_id,
        title="Check-Out Reminder",
        message=f"Reminder: Check-out at {hotel_name} is scheduled for {check_out_date} by 11:00.",
        notification_type=NotificationType.CHECK_OUT_REMINDER,
        data={"booking_ref": booking_ref}
    )
