from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole, Hotel, RoomType
from schemas import RoomTypeCreate, RoomTypeUpdate, RoomTypeResponse
from auth.dependencies import get_current_user, require_roles, verify_hotel_access
from utils.response import api_response

router = APIRouter(prefix="/room-types", tags=["Module 6: Room Type Management"])


@router.post("/hotel/{hotel_id}", summary="Create a new room type for a hotel")
def create_room_type(
    hotel_id: int,
    request: RoomTypeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    hotel = verify_hotel_access(hotel_id, current_user, db)

    # Validate duplicate code within the hotel
    existing = db.query(RoomType).filter(
        RoomType.hotel_id == hotel.id,
        RoomType.code == request.code.upper()
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Room type code '{request.code}' already exists for this hotel"
        )

    # Validate pricing and capacity
    if request.base_price_per_night <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Base price per night must be greater than 0")
    if request.max_occupancy <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Max occupancy must be greater than 0")
    if request.max_adults <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Max adults must be at least 1")

    room_type = RoomType(
        hotel_id=hotel.id,
        name=request.name,
        code=request.code.upper(),
        description=request.description,
        base_price_per_night=request.base_price_per_night,
        max_occupancy=request.max_occupancy,
        max_adults=request.max_adults,
        max_children=request.max_children,
        bed_type=request.bed_type,
        room_size_sqft=request.room_size_sqft,
        amenities_included=request.amenities_included or [],
        image_urls=request.image_urls or [],
        is_active=True
    )
    db.add(room_type)
    db.commit()
    db.refresh(room_type)

    return api_response(
        success=True,
        message=f"Room type '{room_type.name}' created successfully",
        data={
            "id": room_type.id,
            "hotel_id": room_type.hotel_id,
            "name": room_type.name,
            "code": room_type.code,
            "base_price_per_night": room_type.base_price_per_night,
            "max_occupancy": room_type.max_occupancy,
            "max_adults": room_type.max_adults,
            "max_children": room_type.max_children,
            "bed_type": room_type.bed_type,
            "amenities_included": room_type.amenities_included,
            "image_urls": room_type.image_urls
        },
        status_code=status.HTTP_201_CREATED
    )


@router.get("/hotel/{hotel_id}", summary="List all room types for a hotel")
def list_room_types_by_hotel(hotel_id: int, db: Session = Depends(get_db)):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Hotel {hotel_id} not found")

    room_types = db.query(RoomType).filter(
        RoomType.hotel_id == hotel_id,
        RoomType.is_active == True
    ).all()

    return api_response(
        success=True,
        message="Room types retrieved successfully",
        data=[
            {
                "id": rt.id,
                "hotel_id": rt.hotel_id,
                "name": rt.name,
                "code": rt.code,
                "description": rt.description,
                "base_price_per_night": rt.base_price_per_night,
                "max_occupancy": rt.max_occupancy,
                "max_adults": rt.max_adults,
                "max_children": rt.max_children,
                "bed_type": rt.bed_type,
                "room_size_sqft": rt.room_size_sqft,
                "amenities_included": rt.amenities_included,
                "image_urls": rt.image_urls,
                "is_active": rt.is_active
            } for rt in room_types
        ]
    )


@router.get("/{room_type_id}", summary="Get room type details by ID")
def get_room_type(room_type_id: int, db: Session = Depends(get_db)):
    rt = db.query(RoomType).filter(RoomType.id == room_type_id).first()
    if not rt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room type not found")

    return api_response(
        success=True,
        message="Room type details retrieved successfully",
        data={
            "id": rt.id,
            "hotel_id": rt.hotel_id,
            "name": rt.name,
            "code": rt.code,
            "description": rt.description,
            "base_price_per_night": rt.base_price_per_night,
            "max_occupancy": rt.max_occupancy,
            "max_adults": rt.max_adults,
            "max_children": rt.max_children,
            "bed_type": rt.bed_type,
            "room_size_sqft": rt.room_size_sqft,
            "amenities_included": rt.amenities_included,
            "image_urls": rt.image_urls,
            "is_active": rt.is_active
        }
    )


@router.put("/{room_type_id}", summary="Update room type information")
def update_room_type(
    room_type_id: int,
    request: RoomTypeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rt = db.query(RoomType).filter(RoomType.id == room_type_id).first()
    if not rt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room type not found")

    verify_hotel_access(rt.hotel_id, current_user, db)

    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(rt, field, value)

    db.commit()
    db.refresh(rt)

    return api_response(
        success=True,
        message="Room type updated successfully",
        data={
            "id": rt.id,
            "name": rt.name,
            "code": rt.code,
            "base_price_per_night": rt.base_price_per_night,
            "max_occupancy": rt.max_occupancy,
            "max_adults": rt.max_adults,
            "max_children": rt.max_children,
            "bed_type": rt.bed_type,
            "amenities_included": rt.amenities_included
        }
    )


@router.delete("/{room_type_id}", summary="Deactivate or delete room type")
def delete_room_type(
    room_type_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rt = db.query(RoomType).filter(RoomType.id == room_type_id).first()
    if not rt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room type not found")

    verify_hotel_access(rt.hotel_id, current_user, db)

    # Soft delete / deactivate
    rt.is_active = False
    db.commit()

    return api_response(success=True, message=f"Room type '{rt.name}' deactivated successfully")
