"""
Module 32: Hotel Occupancy Analytics
Tracks room availability, calculates occupancy rates, and analyzes peak booking periods.
"""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.dependencies import verify_hotel_access, require_roles
from utils.response import api_response
from crud import occupancy_analytics as crud_occ

router = APIRouter(prefix="/analytics/occupancy", tags=["Module 32: Hotel Occupancy Analytics"])


@router.get("/hotels/{hotel_id}/live", summary="Get real-time room occupancy snapshot")
def get_live_occupancy(
    hotel_id: int,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    live_data = crud_occ.get_live_occupancy(db, hotel_id)
    return api_response(
        success=True,
        message="Live occupancy snapshot retrieved",
        data=live_data
    )


@router.get("/hotels/{hotel_id}/summary", summary="Get occupancy rate summary for date range")
def get_occupancy_summary(
    hotel_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    summary = crud_occ.get_occupancy_summary(db, hotel_id, start_date=start_date, end_date=end_date)
    return api_response(
        success=True,
        message="Occupancy summary calculated",
        data=summary
    )


@router.get("/hotels/{hotel_id}/peak-periods", summary="Identify peak booking periods")
def get_peak_periods(
    hotel_id: int,
    limit: int = 7,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    peak = crud_occ.get_peak_periods(db, hotel_id, limit=limit)
    return api_response(
        success=True,
        message="Peak booking periods identified",
        data=peak
    )
