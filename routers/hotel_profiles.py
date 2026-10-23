from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Request

from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole, Hotel, HotelImage, HotelAmenity, Amenity
from schemas import HotelUpdate, HotelImageCreate
from auth.dependencies import get_current_user, require_roles, verify_hotel_access
from utils.response import api_response, paginated_response
from utils.file_upload import save_upload_file
from config import settings
from crud.search import search_and_filter_hotels

router = APIRouter(prefix="/hotels", tags=["Module 4: Hotel Profile Management"])


@router.get("", summary="List / Search / Filter all approved hotels")
@router.get("/", summary="List / Search / Filter all approved hotels")
@router.get("/search", summary="Search hotels under /hotels/search")
@router.get("/filters", summary="Filter hotels under /hotels/filters")
def list_and_filter_hotels(
    q: Optional[str] = Query(None, description="Search keyword"),
    name: Optional[str] = Query(None, description="Filter by hotel name"),
    location: Optional[str] = Query(None, description="Filter by location"),
    city: Optional[str] = Query(None, description="Filter by city name"),
    state: Optional[str] = Query(None, description="Filter by state name"),
    country: Optional[str] = Query(None, description="Filter by country name"),
    property_type: Optional[str] = Query(None, description="HOTEL, RESORT, VILLA, etc."),
    min_rating: Optional[float] = Query(None, description="Minimum star rating (0-5)"),
    max_rating: Optional[float] = Query(None, description="Maximum star rating (0-5)"),
    rating: Optional[float] = Query(None, description="Alias for min_rating"),
    star_rating: Optional[float] = Query(None, description="Alias for min_rating"),
    min_price: Optional[float] = Query(None, description="Minimum price per night"),
    max_price: Optional[float] = Query(None, description="Maximum price per night"),
    amenity_ids: Optional[str] = Query(None, description="Comma-separated amenity IDs"),
    amenities: Optional[str] = Query(None, description="Comma-separated amenity IDs or names"),
    room_type: Optional[str] = Query(None, description="Filter by room type name or code"),
    guests: Optional[int] = Query(None, description="Guest capacity"),
    check_in: Optional[date] = Query(None, description="Check-in date (YYYY-MM-DD)"),
    check_out: Optional[date] = Query(None, description="Check-out date (YYYY-MM-DD)"),
    latitude: Optional[float] = Query(None, description="User latitude"),
    longitude: Optional[float] = Query(None, description="User longitude"),
    radius_km: Optional[float] = Query(50.0, description="Search radius in kilometers"),
    sort_by: Optional[str] = Query("rating_desc", description="Sorting option"),
    page: int = Query(1, description="Page number"),
    limit: int = Query(10, description="Items per page"),
    db: Session = Depends(get_db)
):
    effective_min_rating = min_rating or rating or star_rating
    result = search_and_filter_hotels(
        db=db,
        q=q,
        name=name,
        location=location,
        city=city,
        state=state,
        country=country,
        property_type=property_type,
        min_rating=effective_min_rating,
        max_rating=max_rating,
        min_price=min_price,
        max_price=max_price,
        amenity_ids=amenity_ids,
        amenities=amenities,
        room_type=room_type,
        guests=guests,
        check_in=check_in,
        check_out=check_out,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        sort_by=sort_by,
        page=page,
        limit=limit
    )

    return paginated_response(
        items=result["items"],
        total=result["total"],
        page=result["page"],
        limit=result["limit"],
        message=f"Found {result['total']} hotels matching criteria"
    )


@router.get("/my-hotels", summary="Retrieve all hotels owned by current logged in owner")
def get_my_hotels(
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    query = db.query(Hotel)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(Hotel.owner_id == current_user.id)
    hotels = query.all()

    data = []
    for h in hotels:
        primary_img = db.query(HotelImage).filter(
            HotelImage.hotel_id == h.id, HotelImage.is_primary == True
        ).first()
        data.append({
            "id": h.id,
            "name": h.name,
            "property_type": h.property_type,
            "city": h.city,
            "state": h.state,
            "country": h.country,
            "status": h.status.value,
            "is_approved": h.is_approved,
            "is_active": h.is_active,
            "star_rating": h.star_rating,
            "primary_image": primary_img.image_url if primary_img else None
        })

    return api_response(
        success=True,
        message="Hotels retrieved successfully",
        data=data
    )


@router.get("/{hotel_id}", summary="Retrieve full hotel profile by ID")
def get_hotel_profile(hotel_id: int, db: Session = Depends(get_db)):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Hotel with ID {hotel_id} not found")

    images = db.query(HotelImage).filter(HotelImage.hotel_id == hotel.id).order_by(HotelImage.display_order).all()
    amenities = (
        db.query(Amenity)
        .join(HotelAmenity, HotelAmenity.amenity_id == Amenity.id)
        .filter(HotelAmenity.hotel_id == hotel.id, Amenity.is_active == True)
        .all()
    )

    return api_response(
        success=True,
        message="Hotel profile retrieved successfully",
        data={
            "id": hotel.id,
            "owner_id": hotel.owner_id,
            "name": hotel.name,
            "description": hotel.description,
            "property_type": hotel.property_type,
            "star_rating": hotel.star_rating,
            "email": hotel.email,
            "phone": hotel.phone,
            "website": hotel.website,
            "city": hotel.city,
            "state": hotel.state,
            "country": hotel.country,
            "address": {
                "address_line1": hotel.address_line1,
                "address_line2": hotel.address_line2,
                "city": hotel.city,
                "state": hotel.state,
                "country": hotel.country,
                "postal_code": hotel.postal_code,
                "latitude": hotel.latitude,
                "longitude": hotel.longitude,
            },
            "policies": {
                "check_in_time": hotel.check_in_time,
                "check_out_time": hotel.check_out_time,
                "cancellation_policy": hotel.cancellation_policy,
                "house_rules": hotel.house_rules,
            },
            "status": hotel.status.value,
            "is_approved": hotel.is_approved,
            "is_active": hotel.is_active,
            "images": [
                {
                    "id": img.id,
                    "image_url": img.image_url,
                    "is_primary": img.is_primary,
                    "caption": img.caption,
                    "display_order": img.display_order
                } for img in images
            ],
            "amenities": [
                {
                    "id": a.id,
                    "name": a.name,
                    "category": a.category,
                    "icon": a.icon
                } for a in amenities
            ],
            "created_at": hotel.created_at.isoformat() if hotel.created_at else None
        }
    )


@router.put("/{hotel_id}", summary="Update hotel profile, addresses, contacts and rules")
def update_hotel_profile(
    hotel_id: int,
    request: HotelUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    hotel = verify_hotel_access(hotel_id, current_user, db)

    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(hotel, field, value)

    db.commit()
    db.refresh(hotel)

    return api_response(
        success=True,
        message="Hotel profile updated successfully",
        data={
            "id": hotel.id,
            "name": hotel.name,
            "property_type": hotel.property_type,
            "city": hotel.city,
            "status": hotel.status.value,
            "check_in_time": hotel.check_in_time,
            "check_out_time": hotel.check_out_time
        }
    )


@router.post("/{hotel_id}/images", summary="Upload or add hotel gallery image")
async def upload_hotel_image(
    hotel_id: int,
    request: Request,
    is_primary: bool = Form(False),
    caption: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    image_type: Optional[str] = Form("GALLERY"),
    image_url: Optional[str] = Form(None),
    display_order: int = Form(0),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    hotel = verify_hotel_access(hotel_id, current_user, db)

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            body = {}
        target_url = body.get("image_url")
        target_title = body.get("title")
        target_caption = body.get("caption")
        target_type = body.get("image_type", "GALLERY")
        target_primary = body.get("is_primary", False)
        target_order = body.get("display_order", 0)
    else:
        if file:
            target_url = save_upload_file(
                upload_file=file,
                subfolder="hotels",
                allowed_extensions=settings.ALLOWED_IMAGE_EXTENSIONS
            )
        else:
            target_url = image_url

        target_title = title
        target_caption = caption
        target_type = image_type or "GALLERY"
        target_primary = is_primary
        target_order = display_order

    if not target_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either a file upload or an image_url must be provided"
        )

    if target_primary:
        db.query(HotelImage).filter(HotelImage.hotel_id == hotel.id).update({"is_primary": False})

    hotel_image = HotelImage(
        hotel_id=hotel.id,
        image_url=target_url,
        title=target_title,
        caption=target_caption,
        image_type=target_type or "GALLERY",
        is_primary=target_primary,
        display_order=target_order
    )
    db.add(hotel_image)
    db.commit()
    db.refresh(hotel_image)

    return api_response(
        success=True,
        message="Hotel image uploaded successfully",
        data={
            "id": hotel_image.id,
            "hotel_id": hotel_image.hotel_id,
            "image_url": hotel_image.image_url,
            "title": hotel_image.title,
            "caption": hotel_image.caption,
            "image_type": hotel_image.image_type,
            "is_primary": hotel_image.is_primary,
            "display_order": hotel_image.display_order
        },
        status_code=status.HTTP_201_CREATED
    )


@router.delete("/{hotel_id}/images/{image_id}", summary="Delete hotel gallery image")

def delete_hotel_image(
    hotel_id: int,
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    hotel = verify_hotel_access(hotel_id, current_user, db)

    image = db.query(HotelImage).filter(
        HotelImage.id == image_id, HotelImage.hotel_id == hotel.id
    ).first()
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    db.delete(image)
    db.commit()

    return api_response(success=True, message="Hotel image deleted successfully")
