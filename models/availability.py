import enum
from sqlalchemy import Column, Integer, Date, Float, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class AvailabilityStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BOOKED = "BOOKED"
    BLOCKED = "BLOCKED"
    MAINTENANCE = "MAINTENANCE"


class RoomAvailability(Base):
    __tablename__ = "room_availabilities"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    status = Column(Enum(AvailabilityStatus), default=AvailabilityStatus.AVAILABLE, nullable=False)
    price_override = Column(Float, nullable=True)
    booking_id = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint("room_id", "date", name="uq_room_date_availability"),
    )

    room = relationship("Room", back_populates="availabilities")
