"""
Module 30: Room Service Management
Manages food menu items, room service orders, preparation/delivery status tracking, and charges.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole, Booking
from auth.dependencies import get_current_user, verify_hotel_access, require_roles
from utils.response import api_response
from schemas.room_service import (
    MenuItemCreate, MenuItemUpdate, RoomServiceOrderCreate
)
from crud import room_service as crud_rs

router = APIRouter(prefix="/room-service", tags=["Module 30: Room Service Management"])


@router.post("/menu/{hotel_id}", summary="Add item to hotel food menu")
def add_menu_item(
    hotel_id: int,
    request: MenuItemCreate,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)

    item = crud_rs.add_menu_item(
        db=db,
        hotel_id=hotel_id,
        name=request.name,
        category=request.category,
        price=request.price,
        description=request.description,
        is_vegetarian=request.is_vegetarian or False
    )

    return api_response(
        success=True,
        message=f"Menu item '{item.name}' added successfully",
        data={
            "id": item.id,
            "hotel_id": item.hotel_id,
            "name": item.name,
            "category": item.category,
            "price": item.price,
            "is_vegetarian": item.is_vegetarian,
            "is_available": item.is_available
        },
        status_code=status.HTTP_201_CREATED
    )


@router.get("/menu/{hotel_id}", summary="Get hotel food menu")
def get_menu(
    hotel_id: int,
    category: Optional[str] = None,
    available_only: bool = True,
    db: Session = Depends(get_db)
):
    items = crud_rs.get_menu_items(db, hotel_id, category=category, available_only=available_only)

    return api_response(
        success=True,
        message="Menu items retrieved",
        data=[
            {
                "id": i.id,
                "name": i.name,
                "category": i.category,
                "price": i.price,
                "description": i.description,
                "is_vegetarian": i.is_vegetarian,
                "is_available": i.is_available
            }
            for i in items
        ]
    )


@router.put("/menu/{item_id}", summary="Update menu item")
def update_menu(
    item_id: int,
    request: MenuItemUpdate,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    item = crud_rs.get_menu_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")

    verify_hotel_access(item.hotel_id, current_user, db)

    updated = crud_rs.update_menu_item(
        db=db,
        item=item,
        name=request.name,
        category=request.category,
        price=request.price,
        description=request.description,
        is_vegetarian=request.is_vegetarian,
        is_available=request.is_available
    )

    return api_response(
        success=True,
        message="Menu item updated",
        data={
            "id": updated.id,
            "name": updated.name,
            "price": updated.price,
            "is_available": updated.is_available
        }
    )


@router.post("/orders", summary="Place a room-service order")
def place_order(
    request: RoomServiceOrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == request.booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if current_user.role != UserRole.ADMIN and booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot place order for another user's booking")

    order_items_data = [item.dict() for item in request.items]
    order = crud_rs.place_room_service_order(
        db=db,
        booking_id=request.booking_id,
        order_items=order_items_data,
        notes=request.notes
    )

    return api_response(
        success=True,
        message=f"Room service order placed! Total: ${order.total_amount:.2f}",
        data={
            "order_id": order.id,
            "booking_id": order.booking_id,
            "room_id": order.room_id,
            "status": order.status,
            "subtotal": order.subtotal,
            "service_charge": order.service_charge,
            "total_amount": order.total_amount,
            "items_count": len(order.items),
            "created_at": order.created_at.isoformat()
        },
        status_code=status.HTTP_201_CREATED
    )


@router.get("/orders/booking/{booking_id}", summary="Get orders for a booking")
def get_booking_orders(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if current_user.role not in [UserRole.ADMIN, UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF] and booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    orders = crud_rs.get_orders_by_booking(db, booking_id)

    return api_response(
        success=True,
        message="Room service orders retrieved",
        data=[
            {
                "id": o.id,
                "status": o.status,
                "subtotal": o.subtotal,
                "service_charge": o.service_charge,
                "total_amount": o.total_amount,
                "notes": o.notes,
                "created_at": o.created_at.isoformat(),
                "delivered_at": o.delivered_at.isoformat() if o.delivered_at else None,
                "items": [
                    {
                        "item_name": item.item_name,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "total_price": item.total_price
                    }
                    for item in o.items
                ]
            }
            for o in orders
        ]
    )


@router.get("/orders/hotel/{hotel_id}", summary="Get all room service orders for hotel staff/kitchen")
def get_hotel_orders(
    hotel_id: int,
    status: Optional[str] = None,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    orders = crud_rs.get_orders_by_hotel(db, hotel_id, status=status)

    return api_response(
        success=True,
        message="Hotel room service orders retrieved",
        data=[
            {
                "id": o.id,
                "booking_id": o.booking_id,
                "room_id": o.room_id,
                "room_number": o.room.room_number if o.room else None,
                "status": o.status,
                "total_amount": o.total_amount,
                "items_count": len(o.items),
                "created_at": o.created_at.isoformat()
            }
            for o in orders
        ]
    )


@router.patch("/orders/{order_id}/status", summary="Update order status (PLACED, PREPARING, OUT_FOR_DELIVERY, DELIVERED, CANCELLED)")
def update_status(
    order_id: int,
    new_status: str,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    order = crud_rs.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    verify_hotel_access(order.hotel_id, current_user, db)
    updated = crud_rs.update_order_status(db, order, new_status)

    return api_response(
        success=True,
        message=f"Order status updated to {updated.status}",
        data={
            "id": updated.id,
            "status": updated.status,
            "delivered_at": updated.delivered_at.isoformat() if updated.delivered_at else None
        }
    )
