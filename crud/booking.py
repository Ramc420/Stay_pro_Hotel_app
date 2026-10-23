import uuid
from datetime import date, timedelta, datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status

from models.booking import Booking, BookingStatus, PaymentStatus, BookingGuest, BookingHistory
from models.room import Room, RoomType, RoomStatus
from models.hotel import Hotel, HotelStatus
from models.availability import RoomAvailability, AvailabilityStatus


def generate_booking_reference(db: Session) -> str:
    """Generates a guaranteed unique uppercase booking reference code: BK-YYYYMMDD-XXXX."""
    today_str = datetime.now().strftime("%Y%m%d")
    while True:
        suffix = uuid.uuid4().hex[:6].upper()
        ref = f"BK-{today_str}-{suffix}"
        exists = db.query(Booking).filter(Booking.booking_reference == ref).first()
        if not exists:
            return ref


def check_room_availability_conflict(
    db: Session,
    room_id: int,
    check_in_date: date,
    check_out_date: date,
    exclude_booking_id: Optional[int] = None
) -> List[date]:
    """
    Checks if there are any conflicting BOOKED, BLOCKED, or MAINTENANCE records for the given room and dates.
    Returns list of conflicting dates.
    """
    query = db.query(RoomAvailability).filter(
        RoomAvailability.room_id == room_id,
        RoomAvailability.date >= check_in_date,
        RoomAvailability.date < check_out_date,
        RoomAvailability.status.in_([
            AvailabilityStatus.BOOKED,
            AvailabilityStatus.BLOCKED,
            AvailabilityStatus.MAINTENANCE
        ])
    )
    if exclude_booking_id:
        query = query.filter(
            or_(
                RoomAvailability.booking_id != exclude_booking_id,
                RoomAvailability.booking_id == None
            )
        )
    conflicts = query.all()
    return [c.date for c in conflicts]


def find_available_room(
    db: Session,
    hotel_id: int,
    room_type_id: int,
    check_in_date: date,
    check_out_date: date
) -> Optional[Room]:
    """
    Finds the first active room of the requested room type that is available for the full duration.
    """
    candidate_rooms = db.query(Room).filter(
        Room.hotel_id == hotel_id,
        Room.room_type_id == room_type_id,
        Room.is_active == True
    ).all()

    for room in candidate_rooms:
        conflicts = check_room_availability_conflict(db, room.id, check_in_date, check_out_date)
        if not conflicts:
            return room
    return None


def calculate_pricing(
    db: Session,
    room: Room,
    room_type: RoomType,
    check_in_date: date,
    check_out_date: date,
    tax_rate: float = 10.0
) -> Dict[str, float]:
    """
    Calculates nightly pricing, subtotal, tax amount, and total amount.
    Respects daily price overrides in RoomAvailability.
    """
    nights = (check_out_date - check_in_date).days
    if nights <= 0:
        nights = 1

    daily_prices = []
    curr = check_in_date
    while curr < check_out_date:
        avail = db.query(RoomAvailability).filter(
            RoomAvailability.room_id == room.id,
            RoomAvailability.date == curr
        ).first()
        if avail and avail.price_override is not None:
            daily_prices.append(avail.price_override)
        else:
            daily_prices.append(room_type.base_price_per_night)
        curr += timedelta(days=1)

    base_amount = sum(daily_prices)
    nightly_avg = base_amount / len(daily_prices)
    tax_amount = round(base_amount * (tax_rate / 100.0), 2)
    total_amount = round(base_amount + tax_amount, 2)

    return {
        "total_nights": nights,
        "nightly_price": round(nightly_avg, 2),
        "base_amount": round(base_amount, 2),
        "tax_amount": round(tax_amount, 2),
        "total_amount": round(total_amount, 2)
    }


def block_room_dates(
    db: Session,
    room_id: int,
    check_in_date: date,
    check_out_date: date,
    booking_id: int,
    status: AvailabilityStatus = AvailabilityStatus.BOOKED
) -> None:
    """Marks dates in RoomAvailability as BOOKED for the given booking."""
    curr = check_in_date
    while curr < check_out_date:
        avail = db.query(RoomAvailability).filter(
            RoomAvailability.room_id == room_id,
            RoomAvailability.date == curr
        ).first()
        if not avail:
            avail = RoomAvailability(
                room_id=room_id,
                date=curr,
                status=status,
                booking_id=booking_id
            )
            db.add(avail)
        else:
            avail.status = status
            avail.booking_id = booking_id
        curr += timedelta(days=1)
    db.commit()


def release_room_dates(
    db: Session,
    room_id: int,
    check_in_date: date,
    check_out_date: date,
    booking_id: int
) -> None:
    """Releases dates in RoomAvailability back to AVAILABLE when booking is cancelled/modified."""
    db.query(RoomAvailability).filter(
        RoomAvailability.room_id == room_id,
        RoomAvailability.booking_id == booking_id,
        RoomAvailability.date >= check_in_date,
        RoomAvailability.date < check_out_date
    ).update({
        "status": AvailabilityStatus.AVAILABLE,
        "booking_id": None
    })
    db.commit()


def create_booking(
    db: Session,
    user_id: int,
    hotel_id: int,
    room_type_id: int,
    check_in_date: date,
    check_out_date: date,
    guests_data: Optional[List[dict]] = None,
    room_id: Optional[int] = None,
    special_requests: Optional[str] = None
) -> Booking:
    # 1. Validate dates
    today = date.today()
    if check_in_date < today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="check_in_date cannot be in the past"
        )
    if check_out_date <= check_in_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="check_out_date must be strictly after check_in_date"
        )

    # 2. Validate Hotel & RoomType
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id, Hotel.is_active == True, Hotel.is_approved == True).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approved active hotel not found")

    room_type = db.query(RoomType).filter(
        RoomType.id == room_type_id,
        RoomType.hotel_id == hotel_id,
        RoomType.is_active == True
    ).first()
    if not room_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room type not found in this hotel")

    # 3. Validate Guest Count
    guests_list = guests_data or []
    if len(guests_list) > room_type.max_occupancy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Guest count ({len(guests_list)}) exceeds room type maximum occupancy ({room_type.max_occupancy})"
        )

    # 4. Resolve Room
    target_room = None
    if room_id:
        target_room = db.query(Room).filter(
            Room.id == room_id,
            Room.hotel_id == hotel_id,
            Room.room_type_id == room_type_id,
            Room.is_active == True
        ).first()
        if not target_room:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected room is not valid for this room type")
        conflicts = check_room_availability_conflict(db, target_room.id, check_in_date, check_out_date)
        if conflicts:
            conflict_strs = [d.isoformat() for d in conflicts]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Room {target_room.room_number} is unavailable on: {', '.join(conflict_strs)}"
            )
    else:
        target_room = find_available_room(db, hotel_id, room_type_id, check_in_date, check_out_date)
        if not target_room:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No rooms available for room type '{room_type.name}' on selected dates"
            )

    # 5. Calculate Pricing
    pricing = calculate_pricing(db, target_room, room_type, check_in_date, check_out_date)

    # 6. Generate Unique Reference
    reference = generate_booking_reference(db)

    # 7. Create Booking Record
    booking = Booking(
        booking_reference=reference,
        user_id=user_id,
        hotel_id=hotel_id,
        room_id=target_room.id,
        room_type_id=room_type_id,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        total_nights=pricing["total_nights"],
        nightly_price=pricing["nightly_price"],
        base_amount=pricing["base_amount"],
        tax_amount=pricing["tax_amount"],
        total_amount=pricing["total_amount"],
        status=BookingStatus.CONFIRMED,
        payment_status=PaymentStatus.UNPAID,
        special_requests=special_requests
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    # 8. Create Guests
    for idx, g in enumerate(guests_list):
        is_primary = g.get("is_primary", idx == 0)
        guest = BookingGuest(
            booking_id=booking.id,
            full_name=g["full_name"],
            email=g.get("email"),
            phone_number=g.get("phone_number"),
            id_type=g.get("id_type", "PASSPORT"),
            id_number=g.get("id_number"),
            is_primary=is_primary,
            guest_type=g.get("guest_type", "ADULT"),
            age=g.get("age"),
            special_requests=g.get("special_requests")
        )
        db.add(guest)

    # 9. Block Dates in Room Availability
    block_room_dates(db, target_room.id, check_in_date, check_out_date, booking.id)

    # 10. Record History Log
    history = BookingHistory(
        booking_id=booking.id,
        action="CREATED",
        old_status=None,
        new_status=BookingStatus.CONFIRMED.value,
        changed_by_user_id=user_id,
        notes=f"Reservation created for {pricing['total_nights']} nights in room {target_room.room_number}"
    )
    db.add(history)
    db.commit()
    db.refresh(booking)

    return booking


def modify_booking(
    db: Session,
    booking: Booking,
    new_check_in: Optional[date] = None,
    new_check_out: Optional[date] = None,
    new_room_id: Optional[int] = None,
    special_requests: Optional[str] = None,
    changed_by_user_id: Optional[int] = None
) -> Booking:
    if booking.status in [BookingStatus.CANCELLED, BookingStatus.CHECKED_OUT, BookingStatus.COMPLETED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot modify booking with status '{booking.status.value}'"
        )

    target_check_in = new_check_in or booking.check_in_date
    target_check_out = new_check_out or booking.check_out_date
    target_room_id = new_room_id or booking.room_id

    if target_check_out <= target_check_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="check_out_date must be strictly after check_in_date"
        )

    # Check conflicts excluding current booking
    conflicts = check_room_availability_conflict(
        db, target_room_id, target_check_in, target_check_out, exclude_booking_id=booking.id
    )
    if conflicts:
        conflict_strs = [d.isoformat() for d in conflicts]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Room is unavailable on: {', '.join(conflict_strs)}"
        )

    # Release old dates
    release_room_dates(db, booking.room_id, booking.check_in_date, booking.check_out_date, booking.id)

    # Update room & dates
    booking.room_id = target_room_id
    booking.check_in_date = target_check_in
    booking.check_out_date = target_check_out
    if special_requests is not None:
        booking.special_requests = special_requests

    # Recalculate totals
    room = db.query(Room).filter(Room.id == target_room_id).first()
    room_type = db.query(RoomType).filter(RoomType.id == room.room_type_id).first()
    pricing = calculate_pricing(db, room, room_type, target_check_in, target_check_out)

    booking.total_nights = pricing["total_nights"]
    booking.nightly_price = pricing["nightly_price"]
    booking.base_amount = pricing["base_amount"]
    booking.tax_amount = pricing["tax_amount"]
    booking.total_amount = pricing["total_amount"]

    # Block new dates
    block_room_dates(db, target_room_id, target_check_in, target_check_out, booking.id)

    # Record history
    history = BookingHistory(
        booking_id=booking.id,
        action="MODIFIED",
        old_status=booking.status.value,
        new_status=booking.status.value,
        changed_by_user_id=changed_by_user_id,
        notes=f"Dates updated to {target_check_in} -> {target_check_out}, Room: {room.room_number}"
    )
    db.add(history)
    db.commit()
    db.refresh(booking)

    return booking


def cancel_booking(
    db: Session,
    booking: Booking,
    reason: Optional[str] = None,
    changed_by_user_id: Optional[int] = None
) -> Booking:
    if booking.status in [BookingStatus.CANCELLED, BookingStatus.CHECKED_OUT, BookingStatus.COMPLETED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Booking is already in '{booking.status.value}' state"
        )

    old_status = booking.status.value
    booking.status = BookingStatus.CANCELLED
    booking.cancellation_reason = reason
    booking.cancelled_at = datetime.now()

    # Release dates
    release_room_dates(db, booking.room_id, booking.check_in_date, booking.check_out_date, booking.id)

    # Log history
    history = BookingHistory(
        booking_id=booking.id,
        action="CANCELLED",
        old_status=old_status,
        new_status=BookingStatus.CANCELLED.value,
        changed_by_user_id=changed_by_user_id,
        notes=reason or "Booking cancelled by customer or administrator"
    )
    db.add(history)
    db.commit()
    db.refresh(booking)

    return booking


def transition_booking_status(
    db: Session,
    booking: Booking,
    new_status: BookingStatus,
    changed_by_user_id: Optional[int] = None,
    notes: Optional[str] = None
) -> Booking:
    valid_transitions = {
        BookingStatus.PENDING: [BookingStatus.CONFIRMED, BookingStatus.CANCELLED],
        BookingStatus.CONFIRMED: [BookingStatus.CHECKED_IN, BookingStatus.CANCELLED],
        BookingStatus.CHECKED_IN: [BookingStatus.CHECKED_OUT],
        BookingStatus.CHECKED_OUT: [BookingStatus.COMPLETED],
        BookingStatus.CANCELLED: [],
        BookingStatus.COMPLETED: []
    }

    if new_status not in valid_transitions.get(booking.status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition from '{booking.status.value}' to '{new_status.value}'"
        )

    old_status = booking.status.value
    booking.status = new_status

    if new_status == BookingStatus.CANCELLED:
        release_room_dates(db, booking.room_id, booking.check_in_date, booking.check_out_date, booking.id)

    history = BookingHistory(
        booking_id=booking.id,
        action="STATUS_CHANGED",
        old_status=old_status,
        new_status=new_status.value,
        changed_by_user_id=changed_by_user_id,
        notes=notes or f"Status changed to {new_status.value}"
    )
    db.add(history)
    db.commit()
    db.refresh(booking)

    return booking


def get_booking_by_id(db: Session, booking_id: int) -> Optional[Booking]:
    return db.query(Booking).filter(Booking.id == booking_id).first()


def get_booking_by_reference(db: Session, reference: str) -> Optional[Booking]:
    return db.query(Booking).filter(Booking.booking_reference == reference.strip().upper()).first()


def list_user_bookings(db: Session, user_id: int) -> List[Booking]:
    return db.query(Booking).filter(Booking.user_id == user_id).order_by(Booking.created_at.desc()).all()


def list_hotel_bookings(
    db: Session,
    hotel_id: int,
    status: Optional[BookingStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Booking]:
    query = db.query(Booking).filter(Booking.hotel_id == hotel_id)
    if status:
        query = query.filter(Booking.status == status)
    if start_date:
        query = query.filter(Booking.check_in_date >= start_date)
    if end_date:
        query = query.filter(Booking.check_out_date <= end_date)
    return query.order_by(Booking.created_at.desc()).all()


def list_all_bookings(
    db: Session,
    status: Optional[BookingStatus] = None,
    page: int = 1,
    limit: int = 10
) -> Tuple[List[Booking], int]:
    query = db.query(Booking)
    if status:
        query = query.filter(Booking.status == status)
    total = query.count()
    items = query.order_by(Booking.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return items, total
