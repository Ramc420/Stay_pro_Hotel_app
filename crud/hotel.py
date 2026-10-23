from typing import Optional, List
from sqlalchemy.orm import Session
from models.hotel import Hotel, HotelStatus, HotelVerificationDocument, HotelImage


def get_hotel_by_id(db: Session, hotel_id: int) -> Optional[Hotel]:
    return db.query(Hotel).filter(Hotel.id == hotel_id).first()


def list_hotels_by_owner(db: Session, owner_id: int) -> List[Hotel]:
    return db.query(Hotel).filter(Hotel.owner_id == owner_id).all()


def list_all_hotels(db: Session) -> List[Hotel]:
    return db.query(Hotel).all()


def list_pending_hotels(db: Session) -> List[Hotel]:
    return db.query(Hotel).filter(Hotel.status == HotelStatus.PENDING_APPROVAL).all()


def create_hotel(db: Session, owner_id: int, hotel_data: dict) -> Hotel:
    hotel = Hotel(
        owner_id=owner_id,
        status=HotelStatus.PENDING_APPROVAL,
        is_approved=False,
        is_active=True,
        **hotel_data
    )
    db.add(hotel)
    db.commit()
    db.refresh(hotel)
    return hotel


def update_hotel(db: Session, hotel: Hotel, update_data: dict) -> Hotel:
    for field, value in update_data.items():
        setattr(hotel, field, value)
    db.commit()
    db.refresh(hotel)
    return hotel


def submit_hotel_for_approval(db: Session, hotel: Hotel) -> Hotel:
    hotel.status = HotelStatus.PENDING_APPROVAL
    db.commit()
    db.refresh(hotel)
    return hotel


def moderate_hotel(
    db: Session,
    hotel: Hotel,
    status: HotelStatus,
    rejection_reason: Optional[str] = None
) -> Hotel:
    hotel.status = status
    hotel.is_approved = (status == HotelStatus.APPROVED)
    if status == HotelStatus.REJECTED:
        hotel.rejection_reason = rejection_reason
    else:
        hotel.rejection_reason = None
        # Mark verification docs as VERIFIED
        db.query(HotelVerificationDocument).filter(
            HotelVerificationDocument.hotel_id == hotel.id
        ).update({"verification_status": "VERIFIED"})
    db.commit()
    db.refresh(hotel)
    return hotel


def set_hotel_suspension(db: Session, hotel: Hotel, suspend: bool) -> Hotel:
    if suspend:
        hotel.status = HotelStatus.SUSPENDED
        hotel.is_active = False
    else:
        hotel.status = HotelStatus.APPROVED
        hotel.is_active = True
    db.commit()
    db.refresh(hotel)
    return hotel


# Verification Documents
def add_verification_document(
    db: Session,
    hotel_id: int,
    document_type: str,
    document_url: str,
    document_number: Optional[str] = None
) -> HotelVerificationDocument:
    doc = HotelVerificationDocument(
        hotel_id=hotel_id,
        document_type=document_type.upper(),
        document_url=document_url,
        document_number=document_number,
        verification_status="PENDING"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_verification_documents(db: Session, hotel_id: int) -> List[HotelVerificationDocument]:
    return db.query(HotelVerificationDocument).filter(HotelVerificationDocument.hotel_id == hotel_id).all()


def count_verification_documents(db: Session, hotel_id: int) -> int:
    return db.query(HotelVerificationDocument).filter(HotelVerificationDocument.hotel_id == hotel_id).count()


# Images
def add_hotel_image(
    db: Session,
    hotel_id: int,
    image_url: str,
    is_primary: bool = False,
    caption: Optional[str] = None,
    title: Optional[str] = None,
    image_type: str = "GALLERY",
    display_order: int = 0
) -> HotelImage:
    if is_primary:
        db.query(HotelImage).filter(HotelImage.hotel_id == hotel_id).update({"is_primary": False})

    hotel_image = HotelImage(
        hotel_id=hotel_id,
        image_url=image_url,
        title=title,
        caption=caption,
        image_type=image_type or "GALLERY",
        is_primary=is_primary,
        display_order=display_order
    )
    db.add(hotel_image)
    db.commit()
    db.refresh(hotel_image)
    return hotel_image


def update_hotel_image(
    db: Session,
    hotel_id: int,
    image_id: int,
    title: Optional[str] = None,
    caption: Optional[str] = None,
    image_type: Optional[str] = None,
    is_primary: Optional[bool] = None,
    display_order: Optional[int] = None
) -> Optional[HotelImage]:
    img = db.query(HotelImage).filter(HotelImage.id == image_id, HotelImage.hotel_id == hotel_id).first()
    if not img:
        return None
    if is_primary:
        db.query(HotelImage).filter(HotelImage.hotel_id == hotel_id).update({"is_primary": False})
        img.is_primary = True
    elif is_primary is False:
        img.is_primary = False
    if title is not None:
        img.title = title
    if caption is not None:
        img.caption = caption
    if image_type is not None:
        img.image_type = image_type
    if display_order is not None:
        img.display_order = display_order
    db.commit()
    db.refresh(img)
    return img


def get_hotel_images(db: Session, hotel_id: int) -> List[HotelImage]:
    return db.query(HotelImage).filter(HotelImage.hotel_id == hotel_id).order_by(HotelImage.display_order).all()


def get_hotel_primary_image(db: Session, hotel_id: int) -> Optional[HotelImage]:
    img = db.query(HotelImage).filter(HotelImage.hotel_id == hotel_id, HotelImage.is_primary == True).first()
    if not img:
        img = db.query(HotelImage).filter(HotelImage.hotel_id == hotel_id).first()
    return img


def delete_hotel_image(db: Session, hotel_id: int, image_id: int) -> bool:
    img = db.query(HotelImage).filter(HotelImage.id == image_id, HotelImage.hotel_id == hotel_id).first()
    if img:
        db.delete(img)
        db.commit()
        return True
    return False

