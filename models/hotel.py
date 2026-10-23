import enum
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime,
    ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class HotelStatus(str, enum.Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    name = Column(String(200), index=True, nullable=False)
    description = Column(Text, nullable=True)
    property_type = Column(String(50), default="HOTEL", index=True, nullable=False)
    star_rating = Column(Float, default=0.0, nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    website = Column(String(255), nullable=True)
    
    # Address
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), index=True, nullable=False)
    state = Column(String(100), index=True, nullable=False)
    country = Column(String(100), index=True, nullable=False)
    postal_code = Column(String(20), nullable=False)
    latitude = Column(Float, nullable=True, index=True)
    longitude = Column(Float, nullable=True, index=True)

    # Policies & Rules
    check_in_time = Column(String(20), default="14:00", nullable=False)
    check_out_time = Column(String(20), default="11:00", nullable=False)
    cancellation_policy = Column(Text, nullable=True)
    house_rules = Column(Text, nullable=True)

    # Verification and Status
    is_approved = Column(Boolean, default=False, index=True, nullable=False)
    status = Column(Enum(HotelStatus), default=HotelStatus.PENDING_APPROVAL, index=True, nullable=False)
    rejection_reason = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="hotels")
    documents = relationship("HotelVerificationDocument", back_populates="hotel", cascade="all, delete-orphan")
    images = relationship("HotelImage", back_populates="hotel", cascade="all, delete-orphan")
    room_types = relationship("RoomType", back_populates="hotel", cascade="all, delete-orphan")
    rooms = relationship("Room", back_populates="hotel", cascade="all, delete-orphan")
    amenities = relationship("HotelAmenity", back_populates="hotel", cascade="all, delete-orphan")
    staff = relationship("HotelStaff", back_populates="hotel", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="hotel", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="hotel", cascade="all, delete-orphan")
    refund_requests = relationship("RefundRequest", back_populates="hotel", cascade="all, delete-orphan")
    coupons = relationship("Coupon", back_populates="hotel", cascade="all, delete-orphan")
    wishlist_items = relationship("Wishlist", back_populates="hotel", cascade="all, delete-orphan")


class HotelVerificationDocument(Base):
    __tablename__ = "hotel_verification_documents"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(100), nullable=False)
    document_url = Column(String(500), nullable=False)
    document_number = Column(String(100), nullable=True)
    verification_status = Column(String(50), default="PENDING", nullable=False)
    remarks = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=func.now(), nullable=False)

    hotel = relationship("Hotel", back_populates="documents")


class HotelImage(Base):
    __tablename__ = "hotel_images"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url = Column(String(500), nullable=False)
    title = Column(String(200), nullable=True)
    caption = Column(String(255), nullable=True)
    image_type = Column(String(50), default="GALLERY", nullable=False)  # GALLERY, FACADE, ROOM, LOBBY, AMENITY, DINING, OTHER
    is_primary = Column(Boolean, default=False, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    uploaded_at = Column(DateTime, default=func.now(), nullable=False)

    hotel = relationship("Hotel", back_populates="images")

