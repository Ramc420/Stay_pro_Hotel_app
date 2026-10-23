"""
Module 37: Hotel Verification and Moderation
Administrative review, approval, rejection, and suspension workflows for hotel properties.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.dependencies import require_roles
from utils.response import api_response
from schemas.hotel_moderation import HotelModerationActionRequest
from crud import hotel_moderation as crud_mod

router = APIRouter(prefix="/moderation/hotels", tags=["Module 37: Hotel Verification and Moderation"])


@router.get("/pending", summary="List hotels pending verification")
def list_pending_hotels(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    hotels = crud_mod.get_pending_verification_hotels(db)
    return api_response(
        success=True,
        message="Pending hotels retrieved",
        data=[
            {
                "id": h.id,
                "name": h.name,
                "owner_id": h.owner_id,
                "city": h.city,
                "country": h.country,
                "status": h.status.value,
                "created_at": h.created_at.isoformat()
            }
            for h in hotels
        ]
    )


@router.post("/{hotel_id}/approve", summary="Approve hotel application")
def approve_hotel_endpoint(
    hotel_id: int,
    request: Optional[HotelModerationActionRequest] = None,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    try:
        hotel = crud_mod.approve_hotel(
            db=db,
            hotel_id=hotel_id,
            admin_id=current_user.id,
            notes=request.notes if request else None
        )
        return api_response(
            success=True,
            message=f"Hotel '{hotel.name}' approved successfully",
            data={"id": hotel.id, "status": hotel.status.value, "is_approved": hotel.is_approved}
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{hotel_id}/reject", summary="Reject hotel application")
def reject_hotel_endpoint(
    hotel_id: int,
    request: HotelModerationActionRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    try:
        hotel = crud_mod.reject_hotel(
            db=db,
            hotel_id=hotel_id,
            admin_id=current_user.id,
            reason=request.reason,
            notes=request.notes
        )
        return api_response(
            success=True,
            message=f"Hotel '{hotel.name}' rejected",
            data={"id": hotel.id, "status": hotel.status.value, "rejection_reason": hotel.rejection_reason}
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{hotel_id}/suspend", summary="Suspend hotel property")
def suspend_hotel_endpoint(
    hotel_id: int,
    request: HotelModerationActionRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    try:
        hotel = crud_mod.suspend_hotel(
            db=db,
            hotel_id=hotel_id,
            admin_id=current_user.id,
            reason=request.reason,
            notes=request.notes
        )
        return api_response(
            success=True,
            message=f"Hotel '{hotel.name}' has been suspended",
            data={"id": hotel.id, "status": hotel.status.value, "is_active": hotel.is_active}
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{hotel_id}/reactivate", summary="Reactivate suspended hotel")
def reactivate_hotel_endpoint(
    hotel_id: int,
    request: Optional[HotelModerationActionRequest] = None,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    try:
        hotel = crud_mod.reactivate_hotel(
            db=db,
            hotel_id=hotel_id,
            admin_id=current_user.id,
            notes=request.notes if request else None
        )
        return api_response(
            success=True,
            message=f"Hotel '{hotel.name}' reactivated",
            data={"id": hotel.id, "status": hotel.status.value, "is_active": hotel.is_active}
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{hotel_id}/history", summary="View moderation decision history")
def get_moderation_history(
    hotel_id: int,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    logs = crud_mod.get_moderation_logs(db, hotel_id)
    return api_response(
        success=True,
        message="Moderation history retrieved",
        data=[
            {
                "id": l.id,
                "action": l.action,
                "reason": l.reason,
                "notes": l.notes,
                "admin_id": l.admin_id,
                "created_at": l.created_at.isoformat()
            }
            for l in logs
        ]
    )
