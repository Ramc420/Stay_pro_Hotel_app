from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models import FoodMenuItem, RoomServiceOrder, RoomServiceOrderItem, Booking


def add_menu_item(
    db: Session,
    hotel_id: int,
    name: str,
    category: str,
    price: float,
    description: Optional[str] = None,
    is_vegetarian: bool = False
) -> FoodMenuItem:
    """Add a new dish or beverage to a hotel's room service menu."""
    item = FoodMenuItem(
        hotel_id=hotel_id,
        name=name,
        category=category.upper(),
        price=price,
        description=description,
        is_vegetarian=is_vegetarian,
        is_available=True
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_menu_item(
    db: Session,
    item: FoodMenuItem,
    name: Optional[str] = None,
    category: Optional[str] = None,
    price: Optional[float] = None,
    description: Optional[str] = None,
    is_vegetarian: Optional[bool] = None,
    is_available: Optional[bool] = None
) -> FoodMenuItem:
    """Update details or availability of a menu item."""
    if name is not None:
        item.name = name
    if category is not None:
        item.category = category.upper()
    if price is not None:
        item.price = price
    if description is not None:
        item.description = description
    if is_vegetarian is not None:
        item.is_vegetarian = is_vegetarian
    if is_available is not None:
        item.is_available = is_available

    db.commit()
    db.refresh(item)
    return item


def get_menu_items(
    db: Session,
    hotel_id: int,
    category: Optional[str] = None,
    available_only: bool = True
) -> List[FoodMenuItem]:
    """Retrieve food menu items for a hotel."""
    query = db.query(FoodMenuItem).filter(FoodMenuItem.hotel_id == hotel_id)
    if available_only:
        query = query.filter(FoodMenuItem.is_available == True)
    if category:
        query = query.filter(FoodMenuItem.category == category.upper())
    return query.order_by(FoodMenuItem.category, FoodMenuItem.name).all()


def get_menu_item_by_id(db: Session, item_id: int) -> Optional[FoodMenuItem]:
    """Retrieve single menu item by ID."""
    return db.query(FoodMenuItem).filter(FoodMenuItem.id == item_id).first()


def place_room_service_order(
    db: Session,
    booking_id: int,
    order_items: List[Dict[str, int]],  # [{"menu_item_id": int, "quantity": int}]
    notes: Optional[str] = None,
    service_charge_percent: float = 0.10  # 10% room service fee
) -> RoomServiceOrder:
    """
    Create a room-service order:
    - Resolves hotel & room from booking
    - Validates menu items
    - Computes item subtotal and service charges
    - Creates order items and order header
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} not found"
        )

    if not order_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must contain at least one menu item"
        )

    subtotal = 0.0
    prepared_items = []

    for item_data in order_items:
        menu_item_id = item_data.get("menu_item_id")
        qty = max(1, item_data.get("quantity", 1))

        menu_item = db.query(FoodMenuItem).filter(
            FoodMenuItem.id == menu_item_id,
            FoodMenuItem.hotel_id == booking.hotel_id,
            FoodMenuItem.is_available == True
        ).first()

        if not menu_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Menu item {menu_item_id} is unavailable or does not belong to this hotel"
            )

        item_total = menu_item.price * qty
        subtotal += item_total
        prepared_items.append({
            "menu_item_id": menu_item.id,
            "item_name": menu_item.name,
            "quantity": qty,
            "unit_price": menu_item.price,
            "total_price": item_total
        })

    service_charge = round(subtotal * service_charge_percent, 2)
    total_amount = round(subtotal + service_charge, 2)

    order = RoomServiceOrder(
        booking_id=booking.id,
        hotel_id=booking.hotel_id,
        room_id=booking.room_id,
        status="PLACED",
        subtotal=subtotal,
        service_charge=service_charge,
        total_amount=total_amount,
        notes=notes
    )
    db.add(order)
    db.flush()

    for p in prepared_items:
        order_item = RoomServiceOrderItem(
            order_id=order.id,
            menu_item_id=p["menu_item_id"],
            item_name=p["item_name"],
            quantity=p["quantity"],
            unit_price=p["unit_price"],
            total_price=p["total_price"]
        )
        db.add(order_item)

    db.commit()
    db.refresh(order)
    return order


def get_orders_by_booking(db: Session, booking_id: int) -> List[RoomServiceOrder]:
    """Retrieve room service order history for a booking."""
    return db.query(RoomServiceOrder).filter(
        RoomServiceOrder.booking_id == booking_id
    ).order_by(RoomServiceOrder.created_at.desc()).all()


def get_orders_by_hotel(
    db: Session,
    hotel_id: int,
    status: Optional[str] = None
) -> List[RoomServiceOrder]:
    """Retrieve all room service orders for hotel kitchen/staff."""
    query = db.query(RoomServiceOrder).filter(RoomServiceOrder.hotel_id == hotel_id)
    if status:
        query = query.filter(RoomServiceOrder.status == status.upper())
    return query.order_by(RoomServiceOrder.created_at.desc()).all()


def get_order_by_id(db: Session, order_id: int) -> Optional[RoomServiceOrder]:
    """Retrieve single order by ID."""
    return db.query(RoomServiceOrder).filter(RoomServiceOrder.id == order_id).first()


def update_order_status(db: Session, order: RoomServiceOrder, new_status: str) -> RoomServiceOrder:
    """Update order status: PLACED -> PREPARING -> OUT_FOR_DELIVERY -> DELIVERED -> CANCELLED."""
    order.status = new_status.upper()
    if order.status == "DELIVERED":
        order.delivered_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    return order
