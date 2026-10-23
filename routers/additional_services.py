"""
Module 29: Additional Services Management
Configures and manages additional hotel services (laundry, spa, airport pickup, extra bed) and guest service requests.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole, Booking
from auth.dependencies import get_current_user, verify_hotel_access, require_roles
from utils.response import api_response
from schemas.additional_service import (
    ServiceCreate, ServiceUpdate, ServiceRequestCreate
)
from crud import additional_service as crud_service

router = APIRouter(prefix="/services", tags=["Module 29: Additional Services Management"])


@router.post("/hotels/{hotel_id}", summary="Add service offering to hotel catalog")
def add_service(
    hotel_id: int,
    request: ServiceCreate,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)

    service = crud_service.create_hotel_service(
        db=db,
        hotel_id=hotel_id,
        name=request.name,
        category=request.category,
        price=request.price,
        description=request.description
    )

    return api_response(
        success=True,
        message=f"Service '{service.name}' added successfully",
        data={
            "id": service.id,
            "hotel_id": service.hotel_id,
            "name": service.name,
            "category": service.category,
            "price": service.price,
            "description": service.description,
            "is_active": service.is_active
        },
        status_code=status.HTTP_201_CREATED
    )


@router.get("/hotels/{hotel_id}", summary="List available services for hotel")
def list_services(
    hotel_id: int,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    services = crud_service.get_hotel_services(db, hotel_id, active_only=active_only)

    return api_response(
        success=True,
        message="Hotel services retrieved",
        data=[
            {
                "id": s.id,
                "name": s.name,
                "category": s.category,
                "price": s.price,
                "description": s.description,
                "is_active": s.is_active
            }
            for s in services
        ]
    )


@router.put("/{service_id}", summary="Update service details or pricing")
def update_service(
    service_id: int,
    request: ServiceUpdate,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    service = crud_service.get_service_by_id(db, service_id)
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    verify_hotel_access(service.hotel_id, current_user, db)

    updated = crud_service.update_hotel_service(
        db=db,
        service=service,
        name=request.name,
        category=request.category,
        price=request.price,
        description=request.description,
        is_active=request.is_active
    )

    return api_response(
        success=True,
        message="Service updated successfully",
        data={
            "id": updated.id,
            "name": updated.name,
            "category": updated.category,
            "price": updated.price,
            "is_active": updated.is_active
        }
    )


@router.post("/requests", summary="Guest requests an additional service")
def request_service(
    request: ServiceRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == request.booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if current_user.role != UserRole.ADMIN and booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot order service for another user's booking")

    req = crud_service.request_service_for_booking(
        db=db,
        booking_id=request.booking_id,
        service_id=request.service_id,
        quantity=request.quantity or 1,
        special_instructions=request.special_instructions
    )

    return api_response(
        success=True,
        message=f"Service request submitted. Total: ${req.total_price:.2f}",
        data={
            "request_id": req.id,
            "booking_id": req.booking_id,
            "service_id": req.service_id,
            "service_name": req.service.name if req.service else None,
            "quantity": req.quantity,
            "unit_price": req.unit_price,
            "total_price": req.total_price,
            "status": req.status,
            "requested_at": req.requested_at.isoformat()
        },
        status_code=status.HTTP_201_CREATED
    )


@router.get("/requests/booking/{booking_id}", summary="Get service requests for a booking")
def get_booking_requests(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if current_user.role not in [UserRole.ADMIN, UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF] and booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    requests = crud_service.get_booking_service_requests(db, booking_id)
    total_charges = sum(r.total_price for r in requests if r.status != "CANCELLED")

    return api_response(
        success=True,
        message="Service requests retrieved",
        data=[
            {
                "id": r.id,
                "service_id": r.service_id,
                "service_name": r.service.name if r.service else None,
                "quantity": r.quantity,
                "total_price": r.total_price,
                "status": r.status,
                "special_instructions": r.special_instructions,
                "requested_at": r.requested_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None
            }
            for r in requests
        ],
        meta={"total_service_charges": total_charges}
    )


@router.patch("/requests/{request_id}/status", summary="Update service request status")
def update_request_status(
    request_id: int,
    new_status: str,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    req = db.query(crud_service.ServiceRequest).filter(crud_service.ServiceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found")

    verify_hotel_access(req.hotel_id, current_user, db)
    updated = crud_service.update_service_request_status(db, req, new_status)

    return api_response(
        success=True,
        message=f"Service request status updated to {updated.status}",
        data={"id": updated.id, "status": updated.status}
    )
