"""
Module 47: Business Intelligence APIs
Growth analytics, top performers, destination demand, occupancy trends, and monthly business summaries.
"""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.dependencies import require_roles
from utils.response import api_response
from crud import business_intelligence as crud_bi

router = APIRouter(prefix="/business-intelligence", tags=["Module 47: Business Intelligence APIs"])


@router.get("/growth-metrics", summary="Calculate platform growth metrics for revenue, bookings, and customer acquisitions")
def get_growth(
    days: int = 30,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    metrics = crud_bi.get_platform_growth_metrics(db, days=days)
    return api_response(
        success=True,
        message="Platform growth metrics calculated",
        data=metrics
    )


@router.get("/top-performers", summary="Identify top-performing hotels and popular destinations")
def get_top_performers(
    limit: int = 5,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    performers = crud_bi.get_top_performers(db, limit=limit)
    return api_response(
        success=True,
        message="Top performers and destination trends retrieved",
        data=performers
    )


@router.get("/occupancy-trends", summary="Track monthly occupancy trends and room-nights capacity")
def get_trends(
    hotel_id: Optional[int] = None,
    months_count: int = 6,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOTEL_OWNER)),
    db: Session = Depends(get_db)
):
    trends = crud_bi.get_occupancy_trends(db, hotel_id=hotel_id, months_count=months_count)
    return api_response(
        success=True,
        message="Occupancy trends retrieved",
        data=trends
    )


@router.get("/monthly-summary", summary="Generate executive monthly business summary")
def get_monthly_summary(
    year: Optional[int] = None,
    month: Optional[int] = None,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    today = date.today()
    y = year or today.year
    m = month or today.month
    summary = crud_bi.get_executive_monthly_summary(db, year=y, month=m)
    return api_response(
        success=True,
        message=f"Executive business summary for {summary['month_name']} generated",
        data=summary
    )
