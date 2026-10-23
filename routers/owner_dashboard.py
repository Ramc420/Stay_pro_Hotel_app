"""
Module 34: Hotel Owner Dashboard APIs
Provides consolidated single-call overview of today's bookings, guests, revenue, and occupancy.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.dependencies import verify_hotel_access, require_roles
from utils.response import api_response
from crud import dashboards as crud_dash

router = APIRouter(prefix="/dashboards/owner", tags=["Module 34: Hotel Owner Dashboard APIs"])


@router.get("/{hotel_id}", summary="Get consolidated Hotel Owner Dashboard")
def get_owner_dashboard(
    hotel_id: int,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    dashboard_data = crud_dash.get_owner_dashboard(db, hotel_id)
    return api_response(
        success=True,
        message="Owner dashboard data loaded successfully",
        data=dashboard_data
    )
