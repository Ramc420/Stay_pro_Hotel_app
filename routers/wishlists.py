from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Wishlist, User
from schemas.wishlist import WishlistCreate, WishlistResponse, WishlistCheckResponse
from auth.dependencies import get_current_user
from crud import wishlist as crud_wishlist
from crud.recommendation import _get_hotel_primary_image
from utils.response import api_response

router = APIRouter(prefix="/wishlist", tags=["Module 20: Wishlist and Favorite Hotels"])


def _serialize_wishlist(w: Wishlist) -> dict:
    return {
        "id": w.id,
        "user_id": w.user_id,
        "hotel_id": w.hotel_id,
        "hotel_name": w.hotel.name if w.hotel else None,
        "hotel_city": w.hotel.city if w.hotel else None,
        "hotel_country": w.hotel.country if w.hotel else None,
        "hotel_star_rating": w.hotel.star_rating if w.hotel else None,
        "hotel_primary_image": _get_hotel_primary_image(w.hotel) if w.hotel else None,
        "room_id": w.room_id,
        "room_number": w.room.room_number if w.room else None,
        "room_type_id": w.room_type_id,
        "room_type_name": w.room_type.name if w.room_type else None,
        "notes": w.notes,
        "created_at": w.created_at.isoformat() if w.created_at else None
    }


@router.post("", summary="Add a hotel or specific room to wishlist favorites", status_code=status.HTTP_201_CREATED)
def add_to_wishlist(
    request: WishlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = crud_wishlist.add_to_wishlist(
        db=db,
        user_id=current_user.id,
        hotel_id=request.hotel_id,
        room_id=request.room_id,
        room_type_id=request.room_type_id,
        notes=request.notes
    )

    return api_response(
        success=True,
        message="Property added to your wishlist successfully",
        data=_serialize_wishlist(item),
        status_code=status.HTTP_201_CREATED
    )


@router.get("", summary="Retrieve the logged-in customer's saved favorite hotels and rooms")
def get_my_wishlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    items = crud_wishlist.get_user_wishlist(db, current_user.id)
    return api_response(
        success=True,
        message="Wishlist favorites retrieved successfully",
        data=[_serialize_wishlist(i) for i in items]
    )


@router.get("/check/{hotel_id}", summary="Check if a specific hotel is in the user's favorites")
def check_hotel_in_wishlist(
    hotel_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    is_fav, wishlist_id = crud_wishlist.check_is_hotel_wishlisted(db, current_user.id, hotel_id)
    return api_response(
        success=True,
        message="Wishlist status checked",
        data={
            "hotel_id": hotel_id,
            "is_favorite": is_fav,
            "wishlist_id": wishlist_id
        }
    )


@router.delete("/{wishlist_id}", summary="Remove a favorite item from wishlist by wishlist ID")
def remove_from_wishlist_by_id(
    wishlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    crud_wishlist.remove_from_wishlist_by_id(db, wishlist_id=wishlist_id, user_id=current_user.id)
    return api_response(
        success=True,
        message="Item removed from wishlist successfully"
    )


@router.delete("/hotel/{hotel_id}", summary="Remove a hotel from favorites by hotel ID")
def remove_from_wishlist_by_hotel(
    hotel_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    count = crud_wishlist.remove_from_wishlist_by_hotel(db, hotel_id=hotel_id, user_id=current_user.id)
    return api_response(
        success=True,
        message=f"Hotel removed from wishlist successfully ({count} entries deleted)"
    )
