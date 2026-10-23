from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Room, RoomStatus, Booking, BookingStatus, Hotel


def get_live_occupancy(db: Session, hotel_id: int) -> Dict[str, Any]:
    """Retrieve real-time room occupancy snapshot for a hotel."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    hotel_name = hotel.name if hotel else f"Hotel #{hotel_id}"

    rooms = db.query(Room).filter(Room.hotel_id == hotel_id, Room.is_active == True).all()
    total_rooms = len(rooms)

    occupied = sum(1 for r in rooms if r.status == RoomStatus.OCCUPIED)
    available = sum(1 for r in rooms if r.status == RoomStatus.AVAILABLE)
    cleaning = sum(1 for r in rooms if r.status == RoomStatus.CLEANING)
    maintenance = sum(1 for r in rooms if r.status == RoomStatus.MAINTENANCE)

    occupancy_rate = round((occupied / total_rooms * 100.0), 2) if total_rooms > 0 else 0.0

    return {
        "hotel_id": hotel_id,
        "hotel_name": hotel_name,
        "total_rooms": total_rooms,
        "occupied_rooms": occupied,
        "available_rooms": available,
        "cleaning_rooms": cleaning,
        "maintenance_rooms": maintenance,
        "occupancy_rate": occupancy_rate
    }


def get_occupancy_summary(
    db: Session,
    hotel_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict[str, Any]:
    """Calculate average occupancy rate across a date range."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    total_rooms = db.query(Room).filter(Room.hotel_id == hotel_id, Room.is_active == True).count()

    s_date = start_date or (date.today() - timedelta(days=30))
    e_date = end_date or date.today()

    num_days = max(1, (e_date - s_date).days + 1)
    total_room_nights_capacity = total_rooms * num_days

    # Bookings that overlap with the date range
    active_bookings = db.query(Booking).filter(
        Booking.hotel_id == hotel_id,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT, BookingStatus.COMPLETED]),
        Booking.check_in_date <= e_date,
        Booking.check_out_date >= s_date
    ).all()

    occupied_nights = 0
    for b in active_bookings:
        # Overlapping days calculation
        overlap_start = max(b.check_in_date, s_date)
        overlap_end = min(b.check_out_date, e_date)
        nights = max(0, (overlap_end - overlap_start).days)
        occupied_nights += nights

    occupancy_rate = round((occupied_nights / total_room_nights_capacity * 100.0), 2) if total_room_nights_capacity > 0 else 0.0

    return {
        "hotel_id": hotel_id,
        "start_date": s_date.isoformat(),
        "end_date": e_date.isoformat(),
        "total_rooms": total_rooms,
        "total_days": num_days,
        "total_available_room_nights": total_room_nights_capacity,
        "total_occupied_room_nights": occupied_nights,
        "average_occupancy_rate": occupancy_rate
    }


def get_peak_periods(
    db: Session,
    hotel_id: int,
    days_back: int = 30,
    limit: int = 7
) -> List[Dict[str, Any]]:
    """Identify peak booking periods and days with highest occupancy."""
    total_rooms = db.query(Room).filter(Room.hotel_id == hotel_id, Room.is_active == True).count()
    today = date.today()

    daily_occupancy = []
    for i in range(days_back):
        d = today - timedelta(days=i)
        count = db.query(Booking).filter(
            Booking.hotel_id == hotel_id,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN, BookingStatus.COMPLETED]),
            Booking.check_in_date <= d,
            Booking.check_out_date > d
        ).count()

        rate = round((count / total_rooms * 100.0), 2) if total_rooms > 0 else 0.0
        daily_occupancy.append({
            "date": d.isoformat(),
            "day_of_week": d.strftime("%A"),
            "occupied_count": count,
            "occupancy_rate": rate
        })

    # Sort descending by occupied count / rate
    daily_occupancy.sort(key=lambda x: x["occupied_count"], reverse=True)
    return daily_occupancy[:limit]
