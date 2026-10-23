from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models import (
    Booking, BookingStatus, PaymentStatus, Room, RoomStatus,
    CheckInOutRecord, HousekeepingTask, HousekeepingStatus
)
from crud.notification import notify_check_in_reminder, notify_check_out_reminder, create_notification


def verify_booking_for_check_in(
    db: Session,
    booking_reference: Optional[str] = None,
    booking_id: Optional[int] = None
) -> Booking:
    """Verify booking details before check-in."""
    query = db.query(Booking)
    if booking_reference:
        query = query.filter(Booking.booking_reference == booking_reference.strip().upper())
    elif booking_id:
        query = query.filter(Booking.id == booking_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either booking_reference or booking_id must be provided"
        )

    booking = query.first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )

    if booking.status == BookingStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot check in: this reservation is CANCELLED"
        )

    return booking


def process_check_in(
    db: Session,
    booking: Booking,
    assigned_room_id: Optional[int] = None,
    early_check_in_hours: float = 0.0,
    early_check_in_fee: float = 0.0,
    processed_by_staff_id: Optional[int] = None,
    notes: Optional[str] = None
) -> CheckInOutRecord:
    """
    Process guest check-in:
    - Verifies booking is in CONFIRMED or PENDING state
    - Assigns or verifies room
    - Validates room is ready/available
    - Applies early check-in fee if any
    - Updates booking status to CHECKED_IN
    - Updates room status to OCCUPIED
    - Logs CheckInOutRecord
    """
    if booking.status == BookingStatus.CHECKED_IN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Guest is already checked in for this booking"
        )
    if booking.status in [BookingStatus.CHECKED_OUT, BookingStatus.COMPLETED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reservation has already been completed"
        )

    target_room_id = assigned_room_id or booking.room_id
    room = db.query(Room).filter(Room.id == target_room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with ID {target_room_id} not found"
        )

    # Room must belong to the booking hotel
    if room.hotel_id != booking.hotel_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Specified room does not belong to this hotel"
        )

    # Assign room and change statuses
    booking.room_id = room.id
    booking.status = BookingStatus.CHECKED_IN
    room.status = RoomStatus.OCCUPIED

    if early_check_in_fee > 0:
        booking.total_amount += early_check_in_fee

    now = datetime.utcnow()
    record = CheckInOutRecord(
        booking_id=booking.id,
        hotel_id=booking.hotel_id,
        room_id=room.id,
        check_in_time=now,
        early_check_in_hours=early_check_in_hours,
        early_check_in_fee=early_check_in_fee,
        processed_by_staff_id=processed_by_staff_id,
        notes=notes
    )
    db.add(record)

    # In-app notification to guest
    create_notification(
        db, booking.user_id,
        title="Checked In Successfully",
        message=f"Welcome to {booking.hotel.name}! You are checked into Room {room.room_number}.",
        data={"booking_ref": booking.booking_reference, "room_number": room.room_number}
    )

    db.commit()
    db.refresh(record)
    return record


def process_check_out(
    db: Session,
    booking: Booking,
    late_check_out_hours: float = 0.0,
    late_check_out_fee: float = 0.0,
    processed_by_staff_id: Optional[int] = None,
    notes: Optional[str] = None
) -> CheckInOutRecord:
    """
    Process guest check-out:
    - Verifies booking is currently CHECKED_IN
    - Applies late check-out fee if any
    - Updates booking status to CHECKED_OUT (or COMPLETED)
    - Updates room status to CLEANING
    - Creates housekeeping cleaning task automatically
    - Updates CheckInOutRecord
    """
    if booking.status != BookingStatus.CHECKED_IN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot check out: Booking status is {booking.status.value}, expected CHECKED_IN"
        )

    booking.status = BookingStatus.CHECKED_OUT

    if late_check_out_fee > 0:
        booking.total_amount += late_check_out_fee

    now = datetime.utcnow()

    # Find existing record or create new
    record = db.query(CheckInOutRecord).filter(CheckInOutRecord.booking_id == booking.id).first()
    if record:
        record.check_out_time = now
        record.late_check_out_hours = late_check_out_hours
        record.late_check_out_fee = late_check_out_fee
        if notes:
            record.notes = f"{record.notes or ''} | {notes}".strip(" | ")
    else:
        record = CheckInOutRecord(
            booking_id=booking.id,
            hotel_id=booking.hotel_id,
            room_id=booking.room_id,
            check_out_time=now,
            late_check_out_hours=late_check_out_hours,
            late_check_out_fee=late_check_out_fee,
            processed_by_staff_id=processed_by_staff_id,
            notes=notes
        )
        db.add(record)

    # Release room and mark for housekeeping cleaning
    room = db.query(Room).filter(Room.id == booking.room_id).first()
    if room:
        room.status = RoomStatus.CLEANING
        # Create housekeeping task
        clean_task = HousekeepingTask(
            hotel_id=booking.hotel_id,
            room_id=room.id,
            task_type="CLEANING",
            status=HousekeepingStatus.DIRTY,
            priority="HIGH",
            notes=f"Auto-generated after check-out for booking {booking.booking_reference}"
        )
        db.add(clean_task)

    # In-app notification to guest
    create_notification(
        db, booking.user_id,
        title="Checked Out Successfully",
        message=f"Thank you for staying at {booking.hotel.name}. We hope to welcome you again soon!",
        data={"booking_ref": booking.booking_reference}
    )

    db.commit()
    db.refresh(record)
    return record


def get_today_arrivals_and_departures(db: Session, hotel_id: int) -> Dict[str, Any]:
    """Get today's arrivals and departures for front desk operations."""
    today = date.today()

    arrivals = db.query(Booking).filter(
        Booking.hotel_id == hotel_id,
        Booking.check_in_date == today,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING])
    ).all()

    departures = db.query(Booking).filter(
        Booking.hotel_id == hotel_id,
        Booking.check_out_date == today,
        Booking.status == BookingStatus.CHECKED_IN
    ).all()

    return {
        "date": today.isoformat(),
        "arrivals_count": len(arrivals),
        "departures_count": len(departures),
        "arrivals": [
            {
                "booking_id": b.id,
                "booking_reference": b.booking_reference,
                "guest_name": b.user.full_name if b.user else "Guest",
                "room_id": b.room_id,
                "status": b.status.value,
                "payment_status": b.payment_status.value
            } for b in arrivals
        ],
        "departures": [
            {
                "booking_id": b.id,
                "booking_reference": b.booking_reference,
                "guest_name": b.user.full_name if b.user else "Guest",
                "room_id": b.room_id,
                "status": b.status.value,
                "payment_status": b.payment_status.value
            } for b in departures
        ]
    }
