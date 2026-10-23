from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models import HotelService, ServiceRequest, Booking


def create_hotel_service(
    db: Session,
    hotel_id: int,
    name: str,
    category: str,
    price: float,
    description: Optional[str] = None
) -> HotelService:
    """Add a new service offering to a hotel's catalog."""
    service = HotelService(
        hotel_id=hotel_id,
        name=name,
        category=category.upper(),
        price=price,
        description=description,
        is_active=True
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


def update_hotel_service(
    db: Session,
    service: HotelService,
    name: Optional[str] = None,
    category: Optional[str] = None,
    price: Optional[float] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None
) -> HotelService:
    """Update service price, details, or active status."""
    if name is not None:
        service.name = name
    if category is not None:
        service.category = category.upper()
    if price is not None:
        service.price = price
    if description is not None:
        service.description = description
    if is_active is not None:
        service.is_active = is_active

    db.commit()
    db.refresh(service)
    return service


def get_hotel_services(db: Session, hotel_id: int, active_only: bool = True) -> List[HotelService]:
    """List available services for a hotel."""
    query = db.query(HotelService).filter(HotelService.hotel_id == hotel_id)
    if active_only:
        query = query.filter(HotelService.is_active == True)
    return query.order_by(HotelService.category, HotelService.name).all()


def get_service_by_id(db: Session, service_id: int) -> Optional[HotelService]:
    """Retrieve service by ID."""
    return db.query(HotelService).filter(HotelService.id == service_id).first()


def request_service_for_booking(
    db: Session,
    booking_id: int,
    service_id: int,
    quantity: int = 1,
    special_instructions: Optional[str] = None
) -> ServiceRequest:
    """Create a guest service request (laundry, spa, transport, etc.) and calculate total charge."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} not found"
        )

    service = db.query(HotelService).filter(
        HotelService.id == service_id,
        HotelService.hotel_id == booking.hotel_id,
        HotelService.is_active == True
    ).first()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with ID {service_id} not available for this hotel"
        )

    unit_price = service.price
    total_price = unit_price * max(1, quantity)

    req = ServiceRequest(
        booking_id=booking.id,
        hotel_id=booking.hotel_id,
        service_id=service.id,
        quantity=quantity,
        unit_price=unit_price,
        total_price=total_price,
        status="PENDING",
        special_instructions=special_instructions
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def get_booking_service_requests(db: Session, booking_id: int) -> List[ServiceRequest]:
    """Retrieve service history and charges for a booking."""
    return db.query(ServiceRequest).filter(
        ServiceRequest.booking_id == booking_id
    ).order_by(ServiceRequest.requested_at.desc()).all()


def update_service_request_status(
    db: Session,
    request: ServiceRequest,
    new_status: str
) -> ServiceRequest:
    """Update request status: PENDING, IN_PROGRESS, COMPLETED, CANCELLED."""
    request.status = new_status.upper()
    if request.status == "COMPLETED":
        request.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(request)
    return request
