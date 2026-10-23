"""
Module 45: Calendar and Booking Scheduler
Room-availability calendar matrix, check-in/out timetables, conflict prevention, and background tasks.
"""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.dependencies import verify_hotel_access, require_roles
from utils.response import api_response
from schemas.calendar_scheduler import RoomConflictCheckRequest
from crud import calendar_scheduler as crud_cal

router = APIRouter(prefix="/calendar", tags=["Module 45: Calendar and Booking Scheduler"])


@router.get("/hotels/{hotel_id}/availability", summary="Retrieve room availability calendar matrix for date range")
def get_availability_calendar(
    hotel_id: int,
    start_date: date,
    end_date: date,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    try:
        matrix = crud_cal.get_calendar_grid(
            db=db,
            hotel_id=hotel_id,
            start_date=start_date,
            end_date=end_date
        )
        return api_response(
            success=True,
            message="Availability calendar grid retrieved successfully",
            data=matrix
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/hotels/{hotel_id}/schedule", summary="Retrieve daily check-in and check-out schedule")
def get_schedule(
    hotel_id: int,
    target_date: Optional[date] = None,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    day = target_date or date.today()
    try:
        schedule = crud_cal.get_daily_schedule(db=db, hotel_id=hotel_id, target_date=day)
        return api_response(
            success=True,
            message=f"Schedule for {day.isoformat()} retrieved",
            data=schedule
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/check-conflict", summary="Check and prevent overlapping room reservations")
def check_conflict(
    request: RoomConflictCheckRequest,
    db: Session = Depends(get_db)
):
    try:
        result = crud_cal.check_room_overlap(
            db=db,
            room_id=request.room_id,
            check_in=request.check_in_date,
            check_out=request.check_out_date,
            exclude_booking_id=request.exclude_booking_id
        )
        return api_response(
            success=True,
            message=result["message"],
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/run-scheduled-jobs", summary="Execute automated background reminders and expired hold cleanup")
def run_jobs(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    result = crud_cal.run_scheduled_background_jobs(db)
    return api_response(
        success=True,
        message=f"Executed {result['jobs_executed']} scheduled background job(s)",
        data=result
    )
