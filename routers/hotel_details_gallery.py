from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Hotel, HotelStatus, HotelImage, Amenity, HotelAmenity, RoomType, User, UserRole, HotelStaff
from schemas.hotel import (
    HotelDetailsResponse, HotelImageCreate, HotelImageUpdate, HotelImageResponse,
    HotelPolicyResponse, HotelReviewSummary
)
from schemas.review import ReviewCreate, ReviewResponse
from auth.dependencies import get_current_user, get_optional_current_user, require_roles, verify_hotel_access
from crud import hotel as crud_hotel, review as crud_review
from utils.response import api_response

router = APIRouter(prefix="/hotels", tags=["Module 11: Hotel Details & Gallery"])


def _check_hotel_view_permission(hotel: Hotel, user: Optional[User], db: Session):
    """
    Checks whether the user is permitted to view hotel information.
    Published and approved hotels are public.
    Unpublished, inactive, or unapproved hotels can only be viewed by owner, staff, or admin.
    """
    is_published = hotel.is_approved and hotel.status == HotelStatus.APPROVED and hotel.is_active
    if is_published:
        return

    # Hotel is unpublished/unapproved/inactive
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Hotel is not published or approved"
        )

    if user.role == UserRole.ADMIN:
        return

    if user.role == UserRole.HOTEL_OWNER and hotel.owner_id == user.id:
        return

    if user.role == UserRole.HOTEL_STAFF:
        staff_entry = db.query(HotelStaff).filter(
            HotelStaff.hotel_id == hotel.id,
            HotelStaff.user_id == user.id,
            HotelStaff.is_active == True
        ).first()
        if staff_entry:
            return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: Hotel is not published or approved"
    )


# ---------------------------------------------------------
# Module 11: Complete Hotel Details
# ---------------------------------------------------------

@router.get("/{hotel_id}/details", summary="Retrieve complete hotel details, rooms, amenities, reviews, and policies")
def get_complete_hotel_details(
    hotel_id: int,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Hotel with ID {hotel_id} not found")

    _check_hotel_view_permission(hotel, current_user, db)

    # Images
    images = crud_hotel.get_hotel_images(db, hotel.id)
    images_data = [
        {
            "id": img.id,
            "hotel_id": img.hotel_id,
            "image_url": img.image_url,
            "title": img.title,
            "caption": img.caption,
            "image_type": img.image_type or "GALLERY",
            "is_primary": img.is_primary,
            "display_order": img.display_order,
            "uploaded_at": img.uploaded_at
        }
        for img in images
    ]

    # Amenities
    amenities = (
        db.query(Amenity)
        .join(HotelAmenity, HotelAmenity.amenity_id == Amenity.id)
        .filter(HotelAmenity.hotel_id == hotel.id, Amenity.is_active == True)
        .all()
    )
    amenities_data = [
        {
            "id": a.id,
            "name": a.name,
            "category": a.category,
            "icon": a.icon,
            "description": a.description
        }
        for a in amenities
    ]

    # Room Types
    room_types = db.query(RoomType).filter(RoomType.hotel_id == hotel.id, RoomType.is_active == True).all()
    room_types_data = [
        {
            "id": rt.id,
            "hotel_id": rt.hotel_id,
            "name": rt.name,
            "code": rt.code,
            "description": rt.description,
            "base_price_per_night": rt.base_price_per_night,
            "max_occupancy": rt.max_occupancy,
            "max_adults": rt.max_adults,
            "max_children": rt.max_children,
            "bed_type": rt.bed_type,
            "room_size_sqft": rt.room_size_sqft,
            "amenities_included": rt.amenities_included,
            "image_urls": rt.image_urls
        }
        for rt in room_types
    ]

    # Reviews and Summary
    reviews_summary = crud_review.get_hotel_reviews_summary(db, hotel.id)
    recent_reviews = crud_review.list_hotel_reviews(db, hotel.id, skip=0, limit=10)
    reviews_data = [
        {
            "id": r.id,
            "hotel_id": r.hotel_id,
            "user_id": r.user_id,
            "user_name": r.user.full_name if r.user else "Anonymous",
            "rating": r.rating,
            "comment": r.comment,
            "booking_id": r.booking_id,
            "created_at": r.created_at
        }
        for r in recent_reviews
    ]

    # Policies
    policies = {
        "check_in_time": hotel.check_in_time or "14:00",
        "check_out_time": hotel.check_out_time or "11:00",
        "cancellation_policy": hotel.cancellation_policy,
        "house_rules": hotel.house_rules
    }

    response_data = {
        "id": hotel.id,
        "owner_id": hotel.owner_id,
        "name": hotel.name,
        "description": hotel.description,
        "property_type": hotel.property_type,
        "star_rating": hotel.star_rating,
        "email": hotel.email,
        "phone": hotel.phone,
        "website": hotel.website,
        "address_line1": hotel.address_line1,
        "address_line2": hotel.address_line2,
        "city": hotel.city,
        "state": hotel.state,
        "country": hotel.country,
        "postal_code": hotel.postal_code,
        "latitude": hotel.latitude,
        "longitude": hotel.longitude,
        "policies": policies,
        "is_approved": hotel.is_approved,
        "status": hotel.status.value,
        "rejection_reason": hotel.rejection_reason,
        "is_active": hotel.is_active,
        "created_at": hotel.created_at,
        "updated_at": hotel.updated_at,
        "images": images_data,
        "amenities": amenities_data,
        "room_types": room_types_data,
        "reviews_summary": reviews_summary,
        "reviews": reviews_data
    }

    return api_response(
        success=True,
        message="Complete hotel details retrieved successfully",
        data=response_data
    )


# ---------------------------------------------------------
# Image Metadata & Gallery Management
# ---------------------------------------------------------

@router.post("/{hotel_id}/images", summary="Add hotel gallery image with metadata")
@router.post("/{hotel_id}/gallery", summary="Add hotel gallery image record (alias)")
def add_gallery_image(
    hotel_id: int,
    request: HotelImageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)

    image = crud_hotel.add_hotel_image(
        db=db,
        hotel_id=hotel_id,
        image_url=request.image_url,
        title=request.title,
        caption=request.caption,
        image_type=request.image_type or "GALLERY",
        is_primary=request.is_primary,
        display_order=request.display_order
    )

    return api_response(
        success=True,
        message="Gallery image added successfully",
        data={
            "id": image.id,
            "hotel_id": image.hotel_id,
            "image_url": image.image_url,
            "title": image.title,
            "caption": image.caption,
            "image_type": image.image_type,
            "is_primary": image.is_primary,
            "display_order": image.display_order,
            "uploaded_at": image.uploaded_at
        },
        status_code=status.HTTP_201_CREATED
    )


@router.get("/{hotel_id}/images", summary="List all images in hotel gallery")
@router.get("/{hotel_id}/gallery", summary="List hotel gallery records (alias)")
def list_gallery_images(
    hotel_id: int,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Hotel with ID {hotel_id} not found")

    _check_hotel_view_permission(hotel, current_user, db)

    images = crud_hotel.get_hotel_images(db, hotel_id)
    return api_response(
        success=True,
        message="Gallery images retrieved successfully",
        data=[
            {
                "id": img.id,
                "hotel_id": img.hotel_id,
                "image_url": img.image_url,
                "title": img.title,
                "caption": img.caption,
                "image_type": img.image_type or "GALLERY",
                "is_primary": img.is_primary,
                "display_order": img.display_order,
                "uploaded_at": img.uploaded_at
            }
            for img in images
        ]
    )


@router.put("/{hotel_id}/images/{image_id}", summary="Update hotel gallery image metadata")
@router.patch("/{hotel_id}/images/{image_id}", summary="Update hotel gallery image metadata (alias)")
@router.put("/{hotel_id}/gallery/{image_id}", summary="Update hotel gallery image metadata (alias)")
def update_gallery_image(
    hotel_id: int,
    image_id: int,
    request: HotelImageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)

    img = crud_hotel.update_hotel_image(
        db=db,
        hotel_id=hotel_id,
        image_id=image_id,
        title=request.title,
        caption=request.caption,
        image_type=request.image_type,
        is_primary=request.is_primary,
        display_order=request.display_order
    )
    if not img:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gallery image not found")

    return api_response(
        success=True,
        message="Gallery image metadata updated successfully",
        data={
            "id": img.id,
            "hotel_id": img.hotel_id,
            "image_url": img.image_url,
            "title": img.title,
            "caption": img.caption,
            "image_type": img.image_type,
            "is_primary": img.is_primary,
            "display_order": img.display_order,
            "uploaded_at": img.uploaded_at
        }
    )


@router.delete("/{hotel_id}/images/{image_id}", summary="Delete hotel gallery image")
@router.delete("/{hotel_id}/gallery/{image_id}", summary="Delete hotel gallery image (alias)")
def delete_gallery_image(
    hotel_id: int,
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)

    deleted = crud_hotel.delete_hotel_image(db, hotel_id, image_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gallery image not found")

    return api_response(success=True, message="Gallery image deleted successfully")


# ---------------------------------------------------------
# Reviews & Ratings
# ---------------------------------------------------------

@router.post("/{hotel_id}/reviews", summary="Submit a review and rating for hotel")
def submit_hotel_review(
    hotel_id: int,
    request: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Hotel with ID {hotel_id} not found")

    review = crud_review.create_hotel_review(
        db=db,
        hotel_id=hotel_id,
        user_id=current_user.id,
        rating=request.rating,
        comment=request.comment,
        booking_id=request.booking_id
    )

    return api_response(
        success=True,
        message="Review submitted successfully",
        data={
            "id": review.id,
            "hotel_id": review.hotel_id,
            "user_id": review.user_id,
            "user_name": current_user.full_name,
            "rating": review.rating,
            "comment": review.comment,
            "booking_id": review.booking_id,
            "hotel_new_star_rating": hotel.star_rating,
            "created_at": review.created_at
        },
        status_code=status.HTTP_201_CREATED
    )


@router.get("/{hotel_id}/reviews", summary="Retrieve hotel reviews and rating breakdown")
def get_hotel_reviews(
    hotel_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Hotel with ID {hotel_id} not found")

    summary = crud_review.get_hotel_reviews_summary(db, hotel_id)
    reviews = crud_review.list_hotel_reviews(db, hotel_id, skip=skip, limit=limit)

    return api_response(
        success=True,
        message="Hotel reviews retrieved successfully",
        data={
            "summary": summary,
            "reviews": [
                {
                    "id": r.id,
                    "hotel_id": r.hotel_id,
                    "user_id": r.user_id,
                    "user_name": r.user.full_name if r.user else "Anonymous",
                    "rating": r.rating,
                    "comment": r.comment,
                    "booking_id": r.booking_id,
                    "created_at": r.created_at
                }
                for r in reviews
            ]
        }
    )
