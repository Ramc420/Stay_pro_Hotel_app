from datetime import date, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database import get_db
from models import User, UserRole, Hotel, Room, RoomType, RoomAvailability, AvailabilityStatus, RoomStatus
from schemas import RoomAvailabilitySet, RoomAvailabilityBulkSet, RoomAvailabilityResponse
from auth.dependencies import get_current_user, require_roles, verify_hotel_access
from utils.response import api_response

router = APIRouter(prefix="/availability", tags=["Module 8: Room Availability Management"])


@router.post("/set-date", summary="Set or update availability status for a room on a single date")
def set_single_date_availability(
    request: RoomAvailabilitySet,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == request.room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    verify_hotel_access(room.hotel_id, current_user, db)

    avail = db.query(RoomAvailability).filter(
        RoomAvailability.room_id == request.room_id,
        RoomAvailability.date == request.date
    ).first()

    if not avail:
        avail = RoomAvailability(
            room_id=request.room_id,
            date=request.date,
            status=request.status,
            price_override=request.price_override
        )
        db.add(avail)
    else:
        # If already booked, prevent overlapping override
        if avail.status == AvailabilityStatus.BOOKED and request.status != AvailabilityStatus.BOOKED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot change status for date {request.date}: room already has an active confirmed booking."
            )
        avail.status = request.status
        if request.price_override is not None:
            avail.price_override = request.price_override

    db.commit()
    db.refresh(avail)

    return api_response(
        success=True,
        message=f"Availability for room {room.room_number} on {request.date} set to {request.status.value}",
        data={
            "room_id": avail.room_id,
            "date": avail.date.isoformat(),
            "status": avail.status.value,
            "price_override": avail.price_override
        }
    )


@router.post("/set-range", summary="Bulk set availability/block rooms for a date range (e.g. maintenance)")
def set_range_availability(
    request: RoomAvailabilityBulkSet,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == request.room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    verify_hotel_access(room.hotel_id, current_user, db)

    # Check for existing BOOKED dates in the range
    conflicts = db.query(RoomAvailability).filter(
        RoomAvailability.room_id == request.room_id,
        RoomAvailability.date >= request.start_date,
        RoomAvailability.date <= request.end_date,
        RoomAvailability.status == AvailabilityStatus.BOOKED
    ).all()

    if conflicts and request.status != AvailabilityStatus.BOOKED:
        conflict_dates = [c.date.isoformat() for c in conflicts]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Conflict: Dates already have confirmed bookings: {', '.join(conflict_dates)}"
        )

    # Upsert each date
    curr = request.start_date
    updated_count = 0
    while curr <= request.end_date:
        avail = db.query(RoomAvailability).filter(
            RoomAvailability.room_id == request.room_id,
            RoomAvailability.date == curr
        ).first()

        if not avail:
            avail = RoomAvailability(
                room_id=request.room_id,
                date=curr,
                status=request.status,
                price_override=request.price_override
            )
            db.add(avail)
        else:
            avail.status = request.status
            if request.price_override is not None:
                avail.price_override = request.price_override

        updated_count += 1
        curr += timedelta(days=1)

    db.commit()

    return api_response(
        success=True,
        message=f"Availability updated for {updated_count} dates ({request.start_date} to {request.end_date})",
        data={
            "room_id": room.id,
            "status": request.status.value,
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "updated_days": updated_count
        }
    )


@router.get("/room/{room_id}", summary="Get calendar availability for a room across a date range")
def get_room_availability_calendar(
    room_id: int,
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    if end_date < start_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_date must be >= start_date")

    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    existing_avails = {
        av.date: av for av in db.query(RoomAvailability).filter(
            RoomAvailability.room_id == room_id,
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
            # Default room status
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

    return api_response(
        success=True,
        message="Room availability calendar retrieved successfully",
        data={
            "room_id": room.id,
            "room_number": room.room_number,
            "hotel_id": room.hotel_id,
            "calendar": calendar
        }
    )


@router.get("/hotel/{hotel_id}/search", summary="Search available rooms in a hotel for specific dates and guest count")
def search_hotel_room_availability(
    hotel_id: int,
    check_in: date = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: date = Query(..., description="Check-out date (YYYY-MM-DD)"),
    guests: int = Query(1, ge=1, description="Number of guests"),
    db: Session = Depends(get_db)
):
    if check_out <= check_in:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="check_out must be after check_in")

    hotel = db.query(Hotel).filter(Hotel.id == hotel_id, Hotel.is_approved == True, Hotel.is_active == True).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approved active hotel not found")

    # Get active rooms that accommodate requested guests
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

    available_rooms = []
    # Total nights
    num_nights = (check_out - check_in).days

    for r in rooms:
        # Check if any date between check_in and check_out is unavailable (BOOKED, BLOCKED, MAINTENANCE)
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
            available_rooms.append({
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

    return api_response(
        success=True,
        message=f"Found {len(available_rooms)} available rooms for selected dates",
        data={
            "hotel_id": hotel.id,
            "hotel_name": hotel.name,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "guests": guests,
            "available_rooms": available_rooms
        }
    )
