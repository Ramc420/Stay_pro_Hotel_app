"""
Module 28: Check-In and Check-Out Management
Verifies reservations, assigns rooms, handles early/late fees, and manages the guest arrival/departure lifecycle.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole, Booking
from auth.dependencies import get_current_user, verify_hotel_access, require_roles
from utils.response import api_response
from schemas.check_in_out import VerifyBookingRequest, CheckInRequest, CheckOutRequest
from crud import check_in_out as crud_check

router = APIRouter(prefix="/check-in-out", tags=["Module 28: Check-In and Check-Out Management"])


@router.post("/verify", summary="Verify reservation details before check-in")
def verify_reservation(
    request: VerifyBookingRequest,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    booking = crud_check.verify_booking_for_check_in(
        db, booking_reference=request.booking_reference, booking_id=request.booking_id
    )
    verify_hotel_access(booking.hotel_id, current_user, db)

    return api_response(
        success=True,
        message="Reservation verified and ready for check-in",
        data={
            "booking_id": booking.id,
            "booking_reference": booking.booking_reference,
            "guest_name": booking.user.full_name if booking.user else None,
            "guest_email": booking.user.email if booking.user else None,
            "hotel_id": booking.hotel_id,
            "hotel_name": booking.hotel.name if booking.hotel else None,
            "assigned_room_id": booking.room_id,
            "room_number": booking.room.room_number if booking.room else None,
            "check_in_date": booking.check_in_date.isoformat(),
            "check_out_date": booking.check_out_date.isoformat(),
            "total_nights": booking.total_nights,
            "booking_status": booking.status.value,
            "payment_status": booking.payment_status.value,
            "total_amount": booking.total_amount
        }
    )


@router.post("/check-in", summary="Process guest check-in")
def check_in_guest(
    request: CheckInRequest,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == request.booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    verify_hotel_access(booking.hotel_id, current_user, db)

    record = crud_check.process_check_in(
        db=db,
        booking=booking,
        assigned_room_id=request.room_id,
        early_check_in_hours=request.early_check_in_hours or 0.0,
        early_check_in_fee=request.early_check_in_fee or 0.0,
        processed_by_staff_id=current_user.id,
        notes=request.notes
    )

    return api_response(
        success=True,
        message="Guest checked in successfully",
        data={
            "record_id": record.id,
            "booking_id": record.booking_id,
            "room_id": record.room_id,
            "room_number": record.room.room_number if record.room else None,
            "check_in_time": record.check_in_time.isoformat(),
            "early_check_in_fee": record.early_check_in_fee,
            "booking_status": booking.status.value,
            "room_status": record.room.status.value if record.room else None
        }
    )


@router.post("/check-out", summary="Process guest check-out")
def check_out_guest(
    request: CheckOutRequest,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == request.booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    verify_hotel_access(booking.hotel_id, current_user, db)

    record = crud_check.process_check_out(
        db=db,
        booking=booking,
        late_check_out_hours=request.late_check_out_hours or 0.0,
        late_check_out_fee=request.late_check_out_fee or 0.0,
        processed_by_staff_id=current_user.id,
        notes=request.notes
    )

    return api_response(
        success=True,
        message="Guest checked out successfully. Housekeeping has been notified.",
        data={
            "record_id": record.id,
            "booking_id": record.booking_id,
            "room_id": record.room_id,
            "check_out_time": record.check_out_time.isoformat(),
            "late_check_out_fee": record.late_check_out_fee,
            "booking_status": booking.status.value,
            "room_status": record.room.status.value if record.room else None
        }
    )


@router.get("/today/{hotel_id}", summary="Get today's scheduled arrivals and departures")
def get_today_arrivals_departures(
    hotel_id: int,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    data = crud_check.get_today_arrivals_and_departures(db, hotel_id)
    return api_response(
        success=True,
        message="Today's front-desk schedule retrieved",
        data=data
    )
