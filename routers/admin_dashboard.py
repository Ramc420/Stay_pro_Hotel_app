"""
Module 36: Admin Dashboard APIs
Platform-wide administrative overview of users, hotels, revenue, and active operations.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.dependencies import require_roles
from utils.response import api_response
from crud import dashboards as crud_dash

router = APIRouter(prefix="/dashboards/admin", tags=["Module 36: Admin Dashboard APIs"])


@router.get("/", summary="Get platform-wide admin dashboard")
def get_admin_dashboard(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    dashboard_data = crud_dash.get_admin_dashboard(db)
    return api_response(
        success=True,
        message="Admin platform dashboard loaded successfully",
        data=dashboard_data
    )
