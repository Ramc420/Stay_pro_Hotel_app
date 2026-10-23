from datetime import date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from models.availability import RoomAvailability, AvailabilityStatus
from models.room import Room, RoomType, RoomStatus
from models.hotel import Hotel, HotelStatus


def get_room_availability_on_date(db: Session, room_id: int, target_date: date) -> Optional[RoomAvailability]:
    return db.query(RoomAvailability).filter(
        RoomAvailability.room_id == room_id,
        RoomAvailability.date == target_date
    ).first()


def set_single_date_availability(
    db: Session,
    room_id: int,
    target_date: date,
    status: AvailabilityStatus,
    price_override: Optional[float] = None
) -> RoomAvailability:
    avail = get_room_availability_on_date(db, room_id, target_date)
    if not avail:
        avail = RoomAvailability(
            room_id=room_id,
            date=target_date,
            status=status,
            price_override=price_override
        )
        db.add(avail)
    else:
        avail.status = status
        if price_override is not None:
            avail.price_override = price_override
    db.commit()
    db.refresh(avail)
    return avail


def get_conflicting_booked_dates(db: Session, room_id: int, start_date: date, end_date: date) -> List[date]:
    conflicts = db.query(RoomAvailability).filter(
        RoomAvailability.room_id == room_id,
        RoomAvailability.date >= start_date,
        RoomAvailability.date <= end_date,
        RoomAvailability.status == AvailabilityStatus.BOOKED
    ).all()
    return [c.date for c in conflicts]


def set_range_availability(
    db: Session,
    room_id: int,
    start_date: date,
    end_date: date,
    status: AvailabilityStatus,
    price_override: Optional[float] = None
) -> int:
    curr = start_date
    count = 0
    while curr <= end_date:
        avail = get_room_availability_on_date(db, room_id, curr)
        if not avail:
            avail = RoomAvailability(
                room_id=room_id,
                date=curr,
                status=status,
                price_override=price_override
            )
            db.add(avail)
        else:
            avail.status = status
            if price_override is not None:
                avail.price_override = price_override
        count += 1
        curr += timedelta(days=1)
    db.commit()
    return count


def get_room_calendar(db: Session, room: Room, start_date: date, end_date: date) -> List[Dict[str, Any]]:
    existing_avails = {
        av.date: av for av in db.query(RoomAvailability).filter(
            RoomAvailability.room_id == room.id,
            RoomAvailability.date >= start_date,
            RoomAvailability.date <= end_date
        ).all()
    }
    base_price = room.room_type.base_price_per_night if room.room_type else 0.0

    calendar = []
    curr = start_date
    while curr <= end_date:
        if curr in existing_avails:
            av = existing_avails[curr]
            cal_status = av.status.value
            price = av.price_override if av.price_override is not None else base_price
            booking_id = av.booking_id
        else:
            cal_status = "AVAILABLE" if room.status == RoomStatus.AVAILABLE else room.status.value
            price = base_price
            booking_id = None

        calendar.append({
            "date": curr.isoformat(),
            "status": cal_status,
            "price": price,
            "is_available": cal_status == "AVAILABLE",
            "booking_id": booking_id
        })
        curr += timedelta(days=1)
    return calendar


def get_available_rooms_for_dates(
    db: Session,
    hotel_id: int,
    check_in: date,
    check_out: date,
    guests: int = 1
) -> List[Dict[str, Any]]:
    num_nights = (check_out - check_in).days
    rooms = (
        db.query(Room)
        .join(RoomType, RoomType.id == Room.room_type_id)
        .filter(
            Room.hotel_id == hotel_id,
            Room.is_active == True,
            Room.status == RoomStatus.AVAILABLE,
            RoomType.max_occupancy >= guests
        )
        .all()
    )

    available = []
    for r in rooms:
        unavail = db.query(RoomAvailability).filter(
            RoomAvailability.room_id == r.id,
            RoomAvailability.date >= check_in,
            RoomAvailability.date < check_out,
            RoomAvailability.status.in_([
                AvailabilityStatus.BOOKED,
                AvailabilityStatus.BLOCKED,
                AvailabilityStatus.MAINTENANCE
            ])
        ).first()

        if not unavail:
            total_price = r.room_type.base_price_per_night * num_nights
            available.append({
                "room_id": r.id,
                "room_number": r.room_number,
                "floor_number": r.floor_number,
                "room_type_id": r.room_type_id,
                "room_type_name": r.room_type.name,
                "bed_type": r.room_type.bed_type,
                "max_occupancy": r.room_type.max_occupancy,
                "price_per_night": r.room_type.base_price_per_night,
                "total_nights": num_nights,
                "total_estimated_price": round(total_price, 2)
            })
    return available
