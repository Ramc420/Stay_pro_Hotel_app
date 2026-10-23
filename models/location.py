from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class HotelAttraction(Base):
    """Local points of interest, landmarks, beaches, and attractions near a hotel."""
    __tablename__ = "hotel_attractions"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(150), nullable=False)
    category = Column(String(50), default="LANDMARK", nullable=False)  # BEACH, LANDMARK, AIRPORT, DINING, SHOPPING
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    distance_km = Column(Float, nullable=True)  # Precomputed or stored distance
    description = Column(Text, nullable=True)
    icon = Column(String(50), default="map-pin", nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)

    hotel = relationship("Hotel")
