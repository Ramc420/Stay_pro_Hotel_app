"""
Module 35: Customer Dashboard APIs
Provides personalized overview of upcoming stays, booking history, wishlist, and payments.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User
from auth.dependencies import get_current_user
from utils.response import api_response
from crud import dashboards as crud_dash

router = APIRouter(prefix="/dashboards/customer", tags=["Module 35: Customer Dashboard APIs"])


@router.get("/", summary="Get personalized customer dashboard")
def get_customer_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dashboard_data = crud_dash.get_customer_dashboard(db, current_user.id)
    return api_response(
        success=True,
        message="Customer dashboard loaded successfully",
        data=dashboard_data
    )
