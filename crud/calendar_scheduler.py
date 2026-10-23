from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from models import (
    Hotel, Room, RoomType, Booking, BookingStatus,
    RoomAvailability, AvailabilityStatus,
    ScheduledJobLog, JobType, JobStatus,
    Notification, NotificationType, User
)


def check_room_overlap(
    db: Session,
    room_id: int,
    check_in: date,
    check_out: date,
    exclude_booking_id: Optional[int] = None
) -> Dict[str, Any]:
    """Prevent overlapping room reservations and double-bookings."""
    if check_out <= check_in:
        raise ValueError("Check-out date must be strictly after check-in date.")

    query = db.query(Booking).filter(
        Booking.room_id == room_id,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]),
        Booking.check_in_date < check_out,
        Booking.check_out_date > check_in
    )

    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)

    conflicts = query.all()
    has_conflict = len(conflicts) > 0

    conflicting_list = [
        {
            "booking_id": b.id,
            "booking_reference": b.booking_reference,
            "guest_name": b.user.full_name if b.user else "Guest",
            "check_in": b.check_in_date.isoformat(),
            "check_out": b.check_out_date.isoformat(),
            "status": b.status.value
        }
        for b in conflicts
    ]

    return {
        "room_id": room_id,
        "has_conflict": has_conflict,
        "is_available": not has_conflict,
        "conflicting_bookings": conflicting_list,
        "message": "Room is available for requested dates." if not has_conflict else f"Conflict detected with {len(conflicts)} existing booking(s)."
    }


def get_calendar_grid(
    db: Session,
    hotel_id: int,
    start_date: date,
    end_date: date
) -> Dict[str, Any]:
    """Retrieve full matrix of room availabilities day-by-day."""
    if end_date < start_date:
        raise ValueError("End date cannot be earlier than start date.")

    # Max 60 days to prevent oversized responses
    if (end_date - start_date).days > 60:
        end_date = start_date + timedelta(days=60)

    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise ValueError(f"Hotel with ID {hotel_id} not found")

    rooms = db.query(Room).filter(Room.hotel_id == hotel_id).all()

    # Pre-fetch active bookings overlapping the range
    bookings = db.query(Booking).filter(
        Booking.hotel_id == hotel_id,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]),
        Booking.check_in_date <= end_date,
        Booking.check_out_date >= start_date
    ).all()

    # Pre-fetch custom availabilities
    availabilities = db.query(RoomAvailability).filter(
        RoomAvailability.date >= start_date,
        RoomAvailability.date <= end_date
    ).all()
    avail_map = {(a.room_id, a.date): a for a in availabilities}

    # Build booking map by (room_id, date)
    booking_map = {}
    for b in bookings:
        if b.room_id:
            curr = max(start_date, b.check_in_date)
            last = min(end_date, b.check_out_date)
            while curr < last:
                booking_map[(b.room_id, curr)] = b
                curr += timedelta(days=1)

    result_rows = []
    for r in rooms:
        type_name = r.room_type.name if r.room_type else "Standard Room"
        base_rate = getattr(r.room_type, "base_price_per_night", 100.0) if r.room_type else 100.0

        days_data = []
        curr_day = start_date
        while curr_day <= end_date:
            b = booking_map.get((r.id, curr_day))
            custom_av = avail_map.get((r.id, curr_day))

            if b:
                status = "BOOKED"
                b_id = b.id
                b_ref = b.booking_reference
                guest = b.user.full_name if b.user else "Guest"
                price = b.total_amount
            elif custom_av:
                status = custom_av.status.value if hasattr(custom_av.status, "value") else str(custom_av.status)
                b_id = None
                b_ref = None
                guest = None
                price = custom_av.price_override or base_rate
            else:
                status = "AVAILABLE"
                b_id = None
                b_ref = None
                guest = None
                price = base_rate

            days_data.append({
                "date": curr_day,
                "status": status,
                "booking_id": b_id,
                "booking_ref": b_ref,
                "guest_name": guest,
                "nightly_price": price
            })
            curr_day += timedelta(days=1)

        result_rows.append({
            "room_id": r.id,
            "room_number": r.room_number,
            "room_type_id": r.room_type_id,
            "room_type_name": type_name,
            "days": days_data
        })

    return {
        "hotel_id": hotel_id,
        "start_date": start_date,
        "end_date": end_date,
        "total_rooms": len(rooms),
        "rooms": result_rows
    }


def get_daily_schedule(
    db: Session,
    hotel_id: int,
    target_date: date
) -> Dict[str, Any]:
    """Retrieve arrival and departure timetables for the day."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise ValueError(f"Hotel with ID {hotel_id} not found")

    arrivals = db.query(Booking).filter(
        Booking.hotel_id == hotel_id,
        Booking.check_in_date == target_date,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN])
    ).all()

    departures = db.query(Booking).filter(
        Booking.hotel_id == hotel_id,
        Booking.check_out_date == target_date,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT])
    ).all()

    arrival_list = [
        {
            "booking_id": b.id,
            "booking_reference": b.booking_reference,
            "guest_name": b.user.full_name if b.user else "Guest",
            "guest_phone": b.user.phone_number if b.user else None,
            "room_number": b.room.room_number if b.room else "Unassigned",
            "room_type": b.room_type.name if b.room_type else "Standard",
            "scheduled_type": "ARRIVAL",
            "date": target_date,
            "expected_time": hotel.check_in_time or "14:00",
            "status": b.status.value
        }
        for b in arrivals
    ]

    departure_list = [
        {
            "booking_id": b.id,
            "booking_reference": b.booking_reference,
            "guest_name": b.user.full_name if b.user else "Guest",
            "guest_phone": b.user.phone_number if b.user else None,
            "room_number": b.room.room_number if b.room else "Unassigned",
            "room_type": b.room_type.name if b.room_type else "Standard",
            "scheduled_type": "DEPARTURE",
            "date": target_date,
            "expected_time": hotel.check_out_time or "11:00",
            "status": b.status.value
        }
        for b in departures
    ]

    return {
        "hotel_id": hotel_id,
        "target_date": target_date,
        "total_arrivals": len(arrival_list),
        "total_departures": len(departure_list),
        "arrivals": arrival_list,
        "departures": departure_list
    }


def run_scheduled_background_jobs(db: Session) -> Dict[str, Any]:
    """Execute scheduled reminders, expired hold releases, and automated alerts."""
    now = datetime.utcnow()
    today = date.today()
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)

    executed_jobs = []
    succeeded = 0
    failed = 0

    # 1. Release expired holds (PENDING bookings older than 24h)
    cutoff = now - timedelta(hours=24)
    expired_bookings = db.query(Booking).filter(
        Booking.status == BookingStatus.PENDING,
        Booking.created_at <= cutoff
    ).all()

    for b in expired_bookings:
        b.status = BookingStatus.CANCELLED
        log = ScheduledJobLog(
            job_type=JobType.EXPIRED_HOLD_RELEASE,
            target_id=b.id,
            status=JobStatus.COMPLETED,
            scheduled_for=now,
            executed_at=now,
            result_message=f"Automatically released expired pending booking {b.booking_reference}."
        )
        db.add(log)
        executed_jobs.append({"type": "EXPIRED_HOLD_RELEASE", "target_id": b.id, "status": "COMPLETED"})
        succeeded += 1

    # 2. Check-in reminders for tomorrow's arrivals
    upcoming_arrivals = db.query(Booking).filter(
        Booking.check_in_date == tomorrow,
        Booking.status == BookingStatus.CONFIRMED
    ).all()

    for b in upcoming_arrivals:
        # Check if already notified
        already_sent = db.query(ScheduledJobLog).filter(
            ScheduledJobLog.job_type == JobType.CHECKIN_REMINDER,
            ScheduledJobLog.target_id == b.id
        ).first()

        if not already_sent:
            notif = Notification(
                user_id=b.user_id,
                title="Upcoming Stay Reminder",
                message=f"Your stay at {b.hotel.name} begins tomorrow! Check-in starts at {b.hotel.check_in_time}.",
                notification_type=NotificationType.CHECK_IN_REMINDER,
                is_read=False
            )
            db.add(notif)
            log = ScheduledJobLog(
                job_type=JobType.CHECKIN_REMINDER,
                target_id=b.id,
                status=JobStatus.COMPLETED,
                scheduled_for=now,
                executed_at=now,
                result_message=f"Check-in reminder notification dispatched for booking {b.booking_reference}."
            )
            db.add(log)
            executed_jobs.append({"type": "CHECKIN_REMINDER", "target_id": b.id, "status": "COMPLETED"})
            succeeded += 1

    # 3. Review invitation for departures from yesterday
    past_departures = db.query(Booking).filter(
        Booking.check_out_date == yesterday,
        Booking.status.in_([BookingStatus.CHECKED_OUT, BookingStatus.CONFIRMED])
    ).all()

    for b in past_departures:
        already_sent = db.query(ScheduledJobLog).filter(
            ScheduledJobLog.job_type == JobType.REVIEW_INVITATION,
            ScheduledJobLog.target_id == b.id
        ).first()

        if not already_sent:
            notif = Notification(
                user_id=b.user_id,
                title="How was your stay?",
                message=f"Thank you for staying at {b.hotel.name}. We would love to hear your feedback!",
                notification_type=NotificationType.BOOKING_CONFIRMATION,
                is_read=False
            )
            db.add(notif)
            log = ScheduledJobLog(
                job_type=JobType.REVIEW_INVITATION,
                target_id=b.id,
                status=JobStatus.COMPLETED,
                scheduled_for=now,
                executed_at=now,
                result_message=f"Review invitation dispatched for booking {b.booking_reference}."
            )
            db.add(log)
            executed_jobs.append({"type": "REVIEW_INVITATION", "target_id": b.id, "status": "COMPLETED"})
            succeeded += 1

    db.commit()

    return {
        "jobs_executed": len(executed_jobs),
        "jobs_succeeded": succeeded,
        "jobs_failed": failed,
        "executed_jobs": executed_jobs
    }
