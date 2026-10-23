from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from models.amenity import Amenity, HotelAmenity
from models.hotel import Hotel


def get_amenity_by_id(db: Session, amenity_id: int) -> Optional[Amenity]:
    return db.query(Amenity).filter(Amenity.id == amenity_id).first()


def get_amenity_by_name(db: Session, name: str) -> Optional[Amenity]:
    return db.query(Amenity).filter(Amenity.name.ilike(name.strip())).first()


def create_amenity(
    db: Session,
    name: str,
    category: str = "GENERAL",
    icon: Optional[str] = None,
    description: Optional[str] = None
) -> Amenity:
    amenity = Amenity(
        name=name.strip(),
        category=category.upper(),
        icon=icon,
        description=description,
        is_active=True
    )
    db.add(amenity)
    db.commit()
    db.refresh(amenity)
    return amenity


def update_amenity(db: Session, amenity: Amenity, update_data: dict) -> Amenity:
    for field, value in update_data.items():
        if field == "category" and value:
            setattr(amenity, field, value.upper())
        else:
            setattr(amenity, field, value)
    db.commit()
    db.refresh(amenity)
    return amenity


def delete_amenity(db: Session, amenity: Amenity) -> None:
    amenity.is_active = False
    db.commit()


def list_amenities(db: Session, category: Optional[str] = None) -> List[Amenity]:
    query = db.query(Amenity).filter(Amenity.is_active == True)
    if category:
        query = query.filter(Amenity.category == category.upper())
    return query.all()


# Hotel-Amenity association
def associate_amenity_with_hotel(db: Session, hotel_id: int, amenity_id: int) -> bool:
    amenity = db.query(Amenity).filter(Amenity.id == amenity_id, Amenity.is_active == True).first()
    if not amenity:
        return False
    exists = db.query(HotelAmenity).filter(
        HotelAmenity.hotel_id == hotel_id,
        HotelAmenity.amenity_id == amenity_id
    ).first()
    if not exists:
        ha = HotelAmenity(hotel_id=hotel_id, amenity_id=amenity_id)
        db.add(ha)
        db.commit()
        return True
    return False


def disassociate_amenity_from_hotel(db: Session, hotel_id: int, amenity_id: int) -> bool:
    ha = db.query(HotelAmenity).filter(
        HotelAmenity.hotel_id == hotel_id,
        HotelAmenity.amenity_id == amenity_id
    ).first()
    if ha:
        db.delete(ha)
        db.commit()
        return True
    return False


def get_hotel_amenities(db: Session, hotel_id: int) -> List[Amenity]:
    return (
        db.query(Amenity)
        .join(HotelAmenity, HotelAmenity.amenity_id == Amenity.id)
        .filter(HotelAmenity.hotel_id == hotel_id, Amenity.is_active == True)
        .all()
    )


def filter_hotels_by_amenity_ids(db: Session, amenity_ids: List[int]) -> List[Hotel]:
    subq = (
        select(HotelAmenity.hotel_id)
        .filter(HotelAmenity.amenity_id.in_(amenity_ids))
        .group_by(HotelAmenity.hotel_id)
        .having(func.count(HotelAmenity.amenity_id) == len(amenity_ids))
    )
    return db.query(Hotel).filter(
        Hotel.id.in_(subq),
        Hotel.is_approved == True,
        Hotel.is_active == True
    ).all()
