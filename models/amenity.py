from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class Amenity(Base):
    __tablename__ = "amenities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    category = Column(String(100), default="GENERAL", nullable=False)
    icon = Column(String(100), nullable=True)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    hotel_associations = relationship("HotelAmenity", back_populates="amenity", cascade="all, delete-orphan")


class HotelAmenity(Base):
    __tablename__ = "hotel_amenities"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    amenity_id = Column(Integer, ForeignKey("amenities.id", ondelete="CASCADE"), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("hotel_id", "amenity_id", name="uq_hotel_amenity"),
    )

    hotel = relationship("Hotel", back_populates="amenities")
    amenity = relationship("Amenity", back_populates="hotel_associations")
