"""
Module 50: Advanced Platform Administration
Customer & hotel account governance, policy configuration, emergency booking overrides, and system diagnostics.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.dependencies import require_roles
from utils.response import api_response
from schemas.platform_admin import (
    UserAccountStatusUpdateRequest, HotelStatusOverrideRequest,
    BookingEmergencyOverrideRequest, PlatformPolicyUpdateRequest
)
from crud import platform_admin as crud_admin

router = APIRouter(prefix="/admin", tags=["Module 50: Advanced Platform Administration"])


@router.get("/platform-overview", summary="Retrieve platform health, active counts, and operational status (Admin only)")
def get_overview(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    overview = crud_admin.perform_system_health_check(db)
    return api_response(
        success=True,
        message="Platform operational status retrieved",
        data=overview
    )


@router.put("/users/{user_id}/status", summary="Activate or deactivate user account with audit logging (Admin only)")
def update_user_status(
    user_id: int,
    request: UserAccountStatusUpdateRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    try:
        user = crud_admin.update_user_account_status(
            db=db,
            target_user_id=user_id,
            is_active=request.is_active,
            admin_id=current_user.id,
            reason=request.reason
        )
        return api_response(
            success=True,
            message=f"User #{user_id} active status updated to {user.is_active}",
            data={
                "user_id": user.id,
                "email": user.email,
                "is_active": user.is_active
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/hotels/{hotel_id}/status", summary="Administrative override of hotel active/approval status (Admin only)")
def update_hotel_status(
    hotel_id: int,
    request: HotelStatusOverrideRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    try:
        hotel = crud_admin.override_hotel_status(
            db=db,
            hotel_id=hotel_id,
            status_str=request.status,
            is_active=request.is_active,
            admin_id=current_user.id,
            reason=request.reason
        )
        return api_response(
            success=True,
            message=f"Hotel #{hotel_id} status updated to {hotel.status.value}",
            data={
                "hotel_id": hotel.id,
                "status": hotel.status.value,
                "is_active": hotel.is_active,
                "is_approved": hotel.is_approved
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/bookings/{booking_id}/override-status", summary="Administrative emergency override of booking status with audit logging (Admin only)")
def override_booking(
    booking_id: int,
    request: BookingEmergencyOverrideRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    try:
        booking = crud_admin.emergency_override_booking_status(
            db=db,
            booking_id=booking_id,
            new_status_str=request.new_status,
            admin_id=current_user.id,
            reason=request.reason
        )
        return api_response(
            success=True,
            message=f"Booking #{booking_id} status overridden to {booking.status.value}",
            data={
                "booking_id": booking.id,
                "booking_reference": booking.booking_reference,
                "status": booking.status.value
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/policies", summary="Retrieve platform legal and operational policies (Admin or Public)")
def list_policies(db: Session = Depends(get_db)):
    policies = crud_admin.get_platform_policies(db)
    return api_response(
        success=True,
        message="Platform policies retrieved",
        data=[
            {
                "id": p.id,
                "policy_type": p.policy_type,
                "title": p.title,
                "content": p.content,
                "version": p.version,
                "is_active": p.is_active,
                "updated_at": p.updated_at.isoformat()
            }
            for p in policies
        ]
    )


@router.put("/policies/{policy_type}", summary="Create or update platform policy with audit logging (Admin only)")
def update_policy(
    policy_type: str,
    request: PlatformPolicyUpdateRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    policy = crud_admin.update_platform_policy(
        db=db,
        policy_type=policy_type,
        content=request.content,
        admin_id=current_user.id,
        title=request.title,
        version=request.version,
        is_active=request.is_active
    )
    return api_response(
        success=True,
        message=f"Policy '{policy.policy_type}' updated to v{policy.version}",
        data={
            "id": policy.id,
            "policy_type": policy.policy_type,
            "title": policy.title,
            "version": policy.version,
            "is_active": policy.is_active,
            "updated_at": policy.updated_at.isoformat()
        }
    )


@router.get("/system-health-check", summary="Deep system diagnostic health check (Admin only)")
def deep_health_check(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    health = crud_admin.perform_system_health_check(db)
    return api_response(
        success=True,
        message="System diagnostics completed",
        data=health
    )
