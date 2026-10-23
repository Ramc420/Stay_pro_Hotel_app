from typing import Optional, List
from sqlalchemy.orm import Session
from models.room import Room, RoomType, RoomStatus


# Room Type CRUD
def get_room_type_by_id(db: Session, room_type_id: int) -> Optional[RoomType]:
    return db.query(RoomType).filter(RoomType.id == room_type_id).first()


def get_room_type_by_code(db: Session, hotel_id: int, code: str) -> Optional[RoomType]:
    return db.query(RoomType).filter(
        RoomType.hotel_id == hotel_id,
        RoomType.code == code.upper()
    ).first()


def create_room_type(db: Session, hotel_id: int, rt_data: dict) -> RoomType:
    data = rt_data.copy()
    data["code"] = data["code"].upper()
    room_type = RoomType(hotel_id=hotel_id, is_active=True, **data)
    db.add(room_type)
    db.commit()
    db.refresh(room_type)
    return room_type


def update_room_type(db: Session, room_type: RoomType, update_data: dict) -> RoomType:
    for field, value in update_data.items():
        if field == "code" and value:
            setattr(room_type, field, value.upper())
        else:
            setattr(room_type, field, value)
    db.commit()
    db.refresh(room_type)
    return room_type


def delete_room_type(db: Session, room_type: RoomType) -> None:
    room_type.is_active = False
    db.commit()


def list_room_types_by_hotel(db: Session, hotel_id: int) -> List[RoomType]:
    return db.query(RoomType).filter(RoomType.hotel_id == hotel_id, RoomType.is_active == True).all()


# Room CRUD
def get_room_by_id(db: Session, room_id: int) -> Optional[Room]:
    return db.query(Room).filter(Room.id == room_id).first()


def get_room_by_number(db: Session, hotel_id: int, room_number: str) -> Optional[Room]:
    return db.query(Room).filter(
        Room.hotel_id == hotel_id,
        Room.room_number == room_number.strip()
    ).first()


def create_room(
    db: Session,
    hotel_id: int,
    room_type_id: int,
    room_number: str,
    floor_number: Optional[int] = None,
    status: RoomStatus = RoomStatus.AVAILABLE
) -> Room:
    room = Room(
        hotel_id=hotel_id,
        room_type_id=room_type_id,
        room_number=room_number.strip(),
        floor_number=floor_number,
        status=status,
        is_active=True
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


def update_room(db: Session, room: Room, update_data: dict) -> Room:
    for field, value in update_data.items():
        if field == "room_number" and value:
            setattr(room, field, value.strip())
        else:
            setattr(room, field, value)
    db.commit()
    db.refresh(room)
    return room


def update_room_status(db: Session, room: Room, status: RoomStatus) -> Room:
    room.status = status
    db.commit()
    db.refresh(room)
    return room


def delete_room(db: Session, room: Room) -> None:
    room.is_active = False
    db.commit()


def list_rooms(
    db: Session,
    hotel_id: int,
    status_filter: Optional[RoomStatus] = None,
    floor: Optional[int] = None,
    room_type_id: Optional[int] = None
) -> List[Room]:
    query = db.query(Room).filter(Room.hotel_id == hotel_id, Room.is_active == True)
    if status_filter:
        query = query.filter(Room.status == status_filter)
    if floor is not None:
        query = query.filter(Room.floor_number == floor)
    if room_type_id is not None:
        query = query.filter(Room.room_type_id == room_type_id)
    return query.all()
