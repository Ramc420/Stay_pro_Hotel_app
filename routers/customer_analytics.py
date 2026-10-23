"""
Module 33: Customer Analytics
Analyzes customer booking frequency, repeat guests, destination demand, and retention.
"""
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.dependencies import require_roles
from utils.response import api_response
from crud import customer_analytics as crud_cust

router = APIRouter(prefix="/analytics/customers", tags=["Module 33: Customer Analytics"])


@router.get("/summary", summary="Get overall customer analytics summary")
def get_customer_summary(
    hotel_id: Optional[int] = None,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    summary = crud_cust.get_customer_analytics_summary(db, hotel_id=hotel_id)
    return api_response(
        success=True,
        message="Customer analytics summary retrieved",
        data=summary
    )


@router.get("/repeat", summary="Identify repeat customers and spending")
def get_repeat_guests(
    hotel_id: Optional[int] = None,
    min_bookings: int = 2,
    limit: int = 50,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    repeat = crud_cust.get_repeat_customers(db, hotel_id=hotel_id, min_bookings=min_bookings, limit=limit)
    return api_response(
        success=True,
        message="Repeat customers retrieved",
        data=repeat
    )


@router.get("/destinations", summary="Analyze popular destinations by demand")
def get_popular_destinations(
    limit: int = 10,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    destinations = crud_cust.get_popular_destinations(db, limit=limit)
    return api_response(
        success=True,
        message="Top travel destinations retrieved",
        data=destinations
    )
