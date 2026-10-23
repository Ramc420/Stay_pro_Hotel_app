from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole, Hotel, Room, RoomType, RoomStatus
from schemas import RoomCreate, RoomUpdate, RoomStatusUpdate
from auth.dependencies import get_current_user, require_roles, verify_hotel_access
from utils.response import api_response

router = APIRouter(prefix="/rooms", tags=["Module 5: Room Management"])


@router.post("/", summary="Create a new room in a hotel")
def create_room(
    request: RoomCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_hotel_access(request.hotel_id, current_user, db)

    # Validate room_type exists and belongs to hotel
    room_type = db.query(RoomType).filter(
        RoomType.id == request.room_type_id,
        RoomType.hotel_id == request.hotel_id
    ).first()
    if not room_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Room type {request.room_type_id} does not belong to hotel {request.hotel_id}"
        )

    # Prevent duplicate room numbers within the hotel
    duplicate = db.query(Room).filter(
        Room.hotel_id == request.hotel_id,
        Room.room_number == request.room_number.strip()
    ).first()
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Room number '{request.room_number}' already exists in this hotel"
        )

    room = Room(
        hotel_id=request.hotel_id,
        room_type_id=request.room_type_id,
        room_number=request.room_number.strip(),
        floor_number=request.floor_number,
        status=request.status,
        is_active=True
    )
    db.add(room)
    db.commit()
    db.refresh(room)

    return api_response(
        success=True,
        message=f"Room '{room.room_number}' created successfully",
        data={
            "id": room.id,
            "hotel_id": room.hotel_id,
            "room_type_id": room.room_type_id,
            "room_number": room.room_number,
            "floor_number": room.floor_number,
            "status": room.status.value,
            "is_active": room.is_active
        },
        status_code=status.HTTP_201_CREATED
    )


@router.get("/hotel/{hotel_id}", summary="List all rooms for a hotel")
def list_rooms_by_hotel(
    hotel_id: int,
    status_filter: Optional[RoomStatus] = None,
    floor: Optional[int] = None,
    room_type_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hotel not found")

    query = db.query(Room).filter(Room.hotel_id == hotel_id, Room.is_active == True)
    if status_filter:
        query = query.filter(Room.status == status_filter)
    if floor is not None:
        query = query.filter(Room.floor_number == floor)
    if room_type_id is not None:
        query = query.filter(Room.room_type_id == room_type_id)

    rooms = query.all()

    return api_response(
        success=True,
        message="Rooms retrieved successfully",
        data=[
            {
                "id": r.id,
                "hotel_id": r.hotel_id,
                "room_type_id": r.room_type_id,
                "room_type_name": r.room_type.name if r.room_type else None,
                "room_number": r.room_number,
                "floor_number": r.floor_number,
                "status": r.status.value,
                "price_per_night": r.room_type.base_price_per_night if r.room_type else None,
                "max_occupancy": r.room_type.max_occupancy if r.room_type else None,
                "is_active": r.is_active
            } for r in rooms
        ]
    )


@router.get("/{room_id}", summary="Retrieve room details by ID")
def get_room_details(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    return api_response(
        success=True,
        message="Room details retrieved successfully",
        data={
            "id": room.id,
            "hotel_id": room.hotel_id,
            "room_type_id": room.room_type_id,
            "room_type_name": room.room_type.name if room.room_type else None,
            "room_number": room.room_number,
            "floor_number": room.floor_number,
            "status": room.status.value,
            "base_price": room.room_type.base_price_per_night if room.room_type else None,
            "max_occupancy": room.room_type.max_occupancy if room.room_type else None,
            "is_active": room.is_active
        }
    )


@router.put("/{room_id}", summary="Update room details")
def update_room(
    room_id: int,
    request: RoomUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    verify_hotel_access(room.hotel_id, current_user, db)

    if request.room_number and request.room_number.strip() != room.room_number:
        # Check duplicate
        dup = db.query(Room).filter(
            Room.hotel_id == room.hotel_id,
            Room.room_number == request.room_number.strip(),
            Room.id != room.id
        ).first()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Room number '{request.room_number}' already exists in this hotel"
            )
        room.room_number = request.room_number.strip()

    if request.room_type_id:
        rt = db.query(RoomType).filter(
            RoomType.id == request.room_type_id,
            RoomType.hotel_id == room.hotel_id
        ).first()
        if not rt:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid room type for this hotel")
        room.room_type_id = request.room_type_id

    if request.floor_number is not None:
        room.floor_number = request.floor_number
    if request.status:
        room.status = request.status
    if request.is_active is not None:
        room.is_active = request.is_active

    db.commit()
    db.refresh(room)

    return api_response(
        success=True,
        message="Room updated successfully",
        data={
            "id": room.id,
            "room_number": room.room_number,
            "status": room.status.value,
            "floor_number": room.floor_number,
            "is_active": room.is_active
        }
    )


@router.patch("/{room_id}/status", summary="Quickly update room operational status")
def update_room_status(
    room_id: int,
    request: RoomStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    verify_hotel_access(room.hotel_id, current_user, db)

    room.status = request.status
    db.commit()
    db.refresh(room)

    return api_response(
        success=True,
        message=f"Room {room.room_number} status updated to {room.status.value}",
        data={"id": room.id, "room_number": room.room_number, "status": room.status.value}
    )


@router.delete("/{room_id}", summary="Delete or deactivate room")
def delete_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

    verify_hotel_access(room.hotel_id, current_user, db)

    # Soft delete / deactivate
    room.is_active = False
    db.commit()

    return api_response(success=True, message=f"Room '{room.room_number}' deleted successfully")
