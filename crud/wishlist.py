from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.wishlist import Wishlist
from models.hotel import Hotel
from models.room import Room, RoomType


def add_to_wishlist(
    db: Session,
    user_id: int,
    hotel_id: int,
    room_id: Optional[int] = None,
    room_type_id: Optional[int] = None,
    notes: Optional[str] = None
) -> Wishlist:
    # Validate hotel
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id, Hotel.is_active == True).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Active hotel with ID {hotel_id} not found")

    # Validate room if provided
    if room_id:
        room = db.query(Room).filter(Room.id == room_id, Room.hotel_id == hotel_id).first()
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Room with ID {room_id} not found in this hotel")

    # Validate room type if provided
    if room_type_id:
        rt = db.query(RoomType).filter(RoomType.id == room_type_id, RoomType.hotel_id == hotel_id).first()
        if not rt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Room type with ID {room_type_id} not found in this hotel")

    # Check for duplicate
    existing = db.query(Wishlist).filter(
        Wishlist.user_id == user_id,
        Wishlist.hotel_id == hotel_id,
        Wishlist.room_id == room_id,
        Wishlist.room_type_id == room_type_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This property/room is already saved in your wishlist"
        )

    item = Wishlist(
        user_id=user_id,
        hotel_id=hotel_id,
        room_id=room_id,
        room_type_id=room_type_id,
        notes=notes
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove_from_wishlist_by_id(db: Session, wishlist_id: int, user_id: int) -> bool:
    item = db.query(Wishlist).filter(Wishlist.id == wishlist_id, Wishlist.user_id == user_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist item not found")

    db.delete(item)
    db.commit()
    return True


def remove_from_wishlist_by_hotel(db: Session, hotel_id: int, user_id: int) -> int:
    deleted_count = db.query(Wishlist).filter(
        Wishlist.hotel_id == hotel_id,
        Wishlist.user_id == user_id
    ).delete(synchronize_session=False)
    db.commit()
    return deleted_count


def get_user_wishlist(db: Session, user_id: int) -> List[Wishlist]:
    return (
        db.query(Wishlist)
        .filter(Wishlist.user_id == user_id)
        .order_by(Wishlist.created_at.desc())
        .all()
    )


def check_is_hotel_wishlisted(db: Session, user_id: int, hotel_id: int) -> Tuple[bool, Optional[int]]:
    item = db.query(Wishlist).filter(
        Wishlist.user_id == user_id,
        Wishlist.hotel_id == hotel_id
    ).first()
    if item:
        return True, item.id
    return False, None
