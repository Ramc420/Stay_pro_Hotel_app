"""
Module 31: Hotel Revenue Analytics
Calculates daily/monthly revenue, aggregates booking & service earnings, and accounts for refunds.
"""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.dependencies import verify_hotel_access, require_roles
from utils.response import api_response
from crud import revenue_analytics as crud_rev

router = APIRouter(prefix="/analytics/revenue", tags=["Module 31: Hotel Revenue Analytics"])


@router.get("/hotels/{hotel_id}/summary", summary="Get comprehensive revenue summary")
def get_revenue_summary(
    hotel_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    summary = crud_rev.get_hotel_revenue_summary(db, hotel_id, start_date=start_date, end_date=end_date)
    return api_response(
        success=True,
        message="Revenue summary calculated successfully",
        data=summary
    )


@router.get("/hotels/{hotel_id}/daily", summary="Get daily revenue trend")
def get_daily_revenue(
    hotel_id: int,
    days: int = 14,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    daily_data = crud_rev.get_daily_revenue_breakdown(db, hotel_id, days=days)
    return api_response(
        success=True,
        message="Daily revenue trend retrieved",
        data=daily_data
    )


@router.get("/hotels/{hotel_id}/monthly", summary="Get monthly revenue breakdown")
def get_monthly_revenue(
    hotel_id: int,
    months: int = 6,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    monthly_data = crud_rev.get_monthly_revenue_breakdown(db, hotel_id, months_count=months)
    return api_response(
        success=True,
        message="Monthly revenue breakdown retrieved",
        data=monthly_data
    )
