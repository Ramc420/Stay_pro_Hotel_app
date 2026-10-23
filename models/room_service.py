from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class FoodMenuItem(Base):
    __tablename__ = "food_menu_items"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    category = Column(String(50), default="MAIN_COURSE", nullable=False)  # BREAKFAST, APPETIZER, MAIN_COURSE, DESSERT, BEVERAGE
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    is_vegetarian = Column(Boolean, default=False, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    hotel = relationship("Hotel")


class RoomServiceOrder(Base):
    __tablename__ = "room_service_orders"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(String(50), default="PLACED", nullable=False)  # PLACED, PREPARING, OUT_FOR_DELIVERY, DELIVERED, CANCELLED
    subtotal = Column(Float, nullable=False)
    service_charge = Column(Float, default=0.0, nullable=False)
    total_amount = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    delivered_at = Column(DateTime, nullable=True)

    booking = relationship("Booking")
    hotel = relationship("Hotel")
    room = relationship("Room")
    items = relationship("RoomServiceOrderItem", back_populates="order", cascade="all, delete-orphan")


class RoomServiceOrderItem(Base):
    __tablename__ = "room_service_order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("room_service_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    menu_item_id = Column(Integer, ForeignKey("food_menu_items.id", ondelete="RESTRICT"), nullable=False)
    item_name = Column(String(150), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    order = relationship("RoomServiceOrder", back_populates="items")
    menu_item = relationship("FoodMenuItem")
