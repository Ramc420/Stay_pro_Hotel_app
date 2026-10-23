from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Booking, BookingStatus, BookingGuest, BookingHistory, User, UserRole, HotelStaff, RoomType, Hotel
from schemas.booking import (
    BookingCreateRequest, BookingModifyRequest, BookingCancelRequest,
    BookingStatusUpdateRequest, BookingResponse, BookingHistoryResponse,
    GuestInput, GuestResponse
)
from schemas.common import ApiResponse
from auth.dependencies import get_current_user, require_roles, verify_hotel_access
from crud import booking as crud_booking
from utils.response import api_response, paginated_response

router = APIRouter(prefix="/bookings", tags=["Module 12: Bookings & Guest Management"])


def _verify_booking_view_or_manage_permission(booking: Booking, user: User, db: Session, require_manage: bool = False):
    """
    Ensures user is booking owner, hotel owner, assigned hotel staff, or admin.
    """
    if user.role == UserRole.ADMIN:
        return

    # Booking owner can view, cancel, or modify their own booking
    if booking.user_id == user.id:
        return

    # Hotel owner
    if user.role == UserRole.HOTEL_OWNER and booking.hotel.owner_id == user.id:
        return

    # Hotel staff
    if user.role == UserRole.HOTEL_STAFF:
        staff_entry = db.query(HotelStaff).filter(
            HotelStaff.hotel_id == booking.hotel_id,
            HotelStaff.user_id == user.id,
            HotelStaff.is_active == True
        ).first()
        if staff_entry:
            return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access or manage this reservation"
    )


def _serialize_booking(b: Booking) -> dict:
    return {
        "id": b.id,
        "booking_reference": b.booking_reference,
        "user_id": b.user_id,
        "hotel_id": b.hotel_id,
        "hotel_name": b.hotel.name if b.hotel else None,
        "room_id": b.room_id,
        "room_number": b.room.room_number if b.room else None,
        "room_type_id": b.room_type_id,
        "room_type_name": b.room_type.name if b.room_type else None,
        "check_in_date": b.check_in_date.isoformat(),
        "check_out_date": b.check_out_date.isoformat(),
        "total_nights": b.total_nights,
        "nightly_price": b.nightly_price,
        "base_amount": b.base_amount,
        "tax_amount": b.tax_amount,
        "total_amount": b.total_amount,
        "status": b.status.value,
        "payment_status": b.payment_status.value,
        "special_requests": b.special_requests,
        "cancellation_reason": b.cancellation_reason,
        "cancelled_at": b.cancelled_at.isoformat() if b.cancelled_at else None,
        "created_at": b.created_at.isoformat() if b.created_at else None,
        "updated_at": b.updated_at.isoformat() if b.updated_at else None,
        "guests": [
            {
                "id": g.id,
                "booking_id": g.booking_id,
                "full_name": g.full_name,
                "email": g.email,
                "phone_number": g.phone_number,
                "id_type": g.id_type,
                "id_number": g.id_number,
                "is_primary": g.is_primary,
                "guest_type": g.guest_type,
                "age": g.age,
                "special_requests": g.special_requests,
                "created_at": g.created_at.isoformat() if g.created_at else None
            }
            for g in b.guests
        ]
    }


# ---------------------------------------------------------
# Module 12: Room Booking Creation & History
# ---------------------------------------------------------

@router.post("", summary="Create a new hotel room reservation", status_code=status.HTTP_201_CREATED)
def create_reservation(
    request: BookingCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    guests_dicts = [g.model_dump() for g in request.guests]

    # Validate identification requirement if provided
    for g in guests_dicts:
        if g.get("id_type") and not g.get("id_number"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"id_number is required when id_type is '{g.get('id_type')}'"
            )

    booking = crud_booking.create_booking(
        db=db,
        user_id=current_user.id,
        hotel_id=request.hotel_id,
        room_type_id=request.room_type_id,
        check_in_date=request.check_in_date,
        check_out_date=request.check_out_date,
        guests_data=guests_dicts,
        room_id=request.room_id,
        special_requests=request.special_requests
    )

    return api_response(
        success=True,
        message="Reservation confirmed successfully",
        data=_serialize_booking(booking),
        status_code=status.HTTP_201_CREATED
    )


@router.get("/my-bookings", summary="Retrieve booking history for current logged-in customer")
def get_my_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bookings = crud_booking.list_user_bookings(db, current_user.id)
    return api_response(
        success=True,
        message="Bookings history retrieved successfully",
        data=[_serialize_booking(b) for b in bookings]
    )


@router.get("/reference/{reference}", summary="Retrieve booking details by unique reference code")
def get_booking_by_ref(
    reference: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = crud_booking.get_booking_by_reference(db, reference)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking with reference '{reference}' not found")

    _verify_booking_view_or_manage_permission(booking, current_user, db)
    return api_response(
        success=True,
        message="Booking retrieved successfully",
        data=_serialize_booking(booking)
    )


@router.get("/{booking_id}", summary="Retrieve booking details by ID")
def get_booking_by_id(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = crud_booking.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking with ID {booking_id} not found")

    _verify_booking_view_or_manage_permission(booking, current_user, db)
    return api_response(
        success=True,
        message="Booking retrieved successfully",
        data=_serialize_booking(booking)
    )


# ---------------------------------------------------------
# Module 14: Booking Management (Modify, Cancel, Lifecycle)
# ---------------------------------------------------------

@router.patch("/{booking_id}/modify", summary="Modify booking dates, room, or special requests")
@router.put("/{booking_id}", summary="Modify booking (alias)")
def modify_reservation(
    booking_id: int,
    request: BookingModifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = crud_booking.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking with ID {booking_id} not found")

    _verify_booking_view_or_manage_permission(booking, current_user, db)

    updated_booking = crud_booking.modify_booking(
        db=db,
        booking=booking,
        new_check_in=request.check_in_date,
        new_check_out=request.check_out_date,
        new_room_id=request.room_id,
        special_requests=request.special_requests,
        changed_by_user_id=current_user.id
    )

    return api_response(
        success=True,
        message="Reservation modified successfully",
        data=_serialize_booking(updated_booking)
    )


@router.post("/{booking_id}/cancel", summary="Cancel reservation and release room dates")
def cancel_reservation(
    booking_id: int,
    request: Optional[BookingCancelRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = crud_booking.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking with ID {booking_id} not found")

    _verify_booking_view_or_manage_permission(booking, current_user, db)

    reason = request.reason if request else "Cancelled by guest"
    cancelled_booking = crud_booking.cancel_booking(
        db=db,
        booking=booking,
        reason=reason,
        changed_by_user_id=current_user.id
    )

    return api_response(
        success=True,
        message="Reservation cancelled successfully and dates released",
        data=_serialize_booking(cancelled_booking)
    )


@router.patch("/{booking_id}/status", summary="Transition booking lifecycle status (CHECKED_IN, CHECKED_OUT, COMPLETED)")
def update_booking_status(
    booking_id: int,
    request: BookingStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = crud_booking.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking with ID {booking_id} not found")

    # Only hotel owner, staff, or admin can trigger lifecycle transitions
    if current_user.role != UserRole.ADMIN and booking.hotel.owner_id != current_user.id:
        staff_entry = db.query(HotelStaff).filter(
            HotelStaff.hotel_id == booking.hotel_id,
            HotelStaff.user_id == current_user.id,
            HotelStaff.is_active == True
        ).first()
        if not staff_entry:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only authorized hotel staff or administrators can update booking lifecycle status"
            )

    updated_booking = crud_booking.transition_booking_status(
        db=db,
        booking=booking,
        new_status=request.status,
        changed_by_user_id=current_user.id,
        notes=request.notes
    )

    return api_response(
        success=True,
        message=f"Booking status transitioned to {request.status.value}",
        data=_serialize_booking(updated_booking)
    )


@router.get("/{booking_id}/history", summary="Retrieve complete audit history logs for booking")
def get_booking_history(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = crud_booking.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking with ID {booking_id} not found")

    _verify_booking_view_or_manage_permission(booking, current_user, db)

    history_logs = db.query(BookingHistory).filter(BookingHistory.booking_id == booking_id).order_by(BookingHistory.created_at.asc()).all()
    return api_response(
        success=True,
        message="Booking history logs retrieved successfully",
        data=[
            {
                "id": h.id,
                "booking_id": h.booking_id,
                "action": h.action,
                "old_status": h.old_status,
                "new_status": h.new_status,
                "changed_by_user_id": h.changed_by_user_id,
                "notes": h.notes,
                "created_at": h.created_at.isoformat() if h.created_at else None
            }
            for h in history_logs
        ]
    )


# ---------------------------------------------------------
# Module 13: Guest Management
# ---------------------------------------------------------

@router.post("/{booking_id}/guests", summary="Add a guest to reservation with identification details")
def add_guest_to_booking(
    booking_id: int,
    request: GuestInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = crud_booking.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking with ID {booking_id} not found")

    _verify_booking_view_or_manage_permission(booking, current_user, db)

    # Validate identification requirements
    if request.id_type and not request.id_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"id_number is required for identification type '{request.id_type}'"
        )

    # Check capacity limit
    current_guests_count = len(booking.guests)
    room_type = booking.room_type
    if room_type and current_guests_count >= room_type.max_occupancy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot add guest: maximum capacity of {room_type.max_occupancy} reached"
        )

    guest = BookingGuest(
        booking_id=booking.id,
        full_name=request.full_name,
        email=request.email,
        phone_number=request.phone_number,
        id_type=request.id_type,
        id_number=request.id_number,
        is_primary=request.is_primary,
        guest_type=request.guest_type,
        age=request.age,
        special_requests=request.special_requests
    )
    db.add(guest)
    db.commit()
    db.refresh(guest)

    return api_response(
        success=True,
        message="Guest details added successfully",
        data={
            "id": guest.id,
            "booking_id": guest.booking_id,
            "full_name": guest.full_name,
            "email": guest.email,
            "phone_number": guest.phone_number,
            "id_type": guest.id_type,
            "id_number": guest.id_number,
            "is_primary": guest.is_primary,
            "guest_type": guest.guest_type,
            "age": guest.age,
            "special_requests": guest.special_requests,
            "created_at": guest.created_at.isoformat() if guest.created_at else None
        },
        status_code=status.HTTP_201_CREATED
    )


@router.get("/{booking_id}/guests", summary="Retrieve all guests linked to a reservation")
def get_booking_guests(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = crud_booking.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking with ID {booking_id} not found")

    _verify_booking_view_or_manage_permission(booking, current_user, db)

    return api_response(
        success=True,
        message="Booking guests retrieved successfully",
        data=[
            {
                "id": g.id,
                "booking_id": g.booking_id,
                "full_name": g.full_name,
                "email": g.email,
                "phone_number": g.phone_number,
                "id_type": g.id_type,
                "id_number": g.id_number,
                "is_primary": g.is_primary,
                "guest_type": g.guest_type,
                "age": g.age,
                "special_requests": g.special_requests,
                "created_at": g.created_at.isoformat() if g.created_at else None
            }
            for g in booking.guests
        ]
    )


# ---------------------------------------------------------
# Hotel Guest History & Hotel Reservations List
# ---------------------------------------------------------

@router.get("/hotel/{hotel_id}/guests", summary="Retrieve guest history for a specific hotel (authorized)")
def get_hotel_guest_history(
    hotel_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)

    # Get all guests for this hotel
    guests = (
        db.query(BookingGuest)
        .join(Booking, Booking.id == BookingGuest.booking_id)
        .filter(Booking.hotel_id == hotel_id)
        .order_by(BookingGuest.created_at.desc())
        .all()
    )

    data = [
        {
            "id": g.id,
            "booking_id": g.booking_id,
            "booking_reference": g.booking.booking_reference if g.booking else None,
            "full_name": g.full_name,
            "email": g.email,
            "phone_number": g.phone_number,
            "id_type": g.id_type,
            "id_number": g.id_number,
            "is_primary": g.is_primary,
            "guest_type": g.guest_type,
            "age": g.age,
            "check_in_date": g.booking.check_in_date.isoformat() if g.booking else None,
            "check_out_date": g.booking.check_out_date.isoformat() if g.booking else None,
            "status": g.booking.status.value if g.booking else None,
            "created_at": g.created_at.isoformat() if g.created_at else None
        }
        for g in guests
    ]

    return api_response(
        success=True,
        message="Hotel guest history retrieved successfully",
        data=data
    )


@router.get("/hotel/{hotel_id}", summary="Retrieve all reservations for a hotel (authorized)")
def get_hotel_reservations(
    hotel_id: int,
    status: Optional[BookingStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)

    bookings = crud_booking.list_hotel_bookings(
        db=db,
        hotel_id=hotel_id,
        status=status,
        start_date=start_date,
        end_date=end_date
    )

    return api_response(
        success=True,
        message="Hotel reservations retrieved successfully",
        data=[_serialize_booking(b) for b in bookings]
    )


@router.get("", summary="List all bookings platform-wide (Admin only)")
def list_all_bookings(
    status: Optional[BookingStatus] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    bookings, total = crud_booking.list_all_bookings(db, status=status, page=page, limit=limit)
    return paginated_response(
        items=[_serialize_booking(b) for b in bookings],
        total=total,
        page=page,
        limit=limit,
        message="Bookings retrieved successfully"
    )
