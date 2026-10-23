from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole, Amenity, HotelAmenity, Hotel
from schemas import AmenityCreate, AmenityUpdate, AssociateAmenitiesRequest
from auth.dependencies import get_current_user, require_roles, verify_hotel_access
from utils.response import api_response

router = APIRouter(prefix="/amenities", tags=["Module 7: Hotel Amenities Management"])


@router.post("/", summary="Create a new global amenity (Admin only)")
def create_amenity(request: AmenityCreate, current_admin: User = Depends(require_roles(UserRole.ADMIN)), db: Session = Depends(get_db)):
    existing = db.query(Amenity).filter(Amenity.name.ilike(request.name.strip())).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Amenity with name '{request.name}' already exists")

    amenity = Amenity(name=request.name.strip(), category=request.category.upper(), icon=request.icon, description=request.description, is_active=True)
    db.add(amenity)
    db.commit()
    db.refresh(amenity)

    return api_response(success=True, message=f"Amenity '{amenity.name}' created successfully", data={"id": amenity.id, "name": amenity.name, "category": amenity.category, "icon": amenity.icon, "description": amenity.description},status_code=status.HTTP_201_CREATED)


@router.get("/", summary="List all available amenities")
def list_amenities(category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Amenity).filter(Amenity.is_active == True)
    if category:
        query = query.filter(Amenity.category == category.upper())
    amenities = query.all()

    return api_response(success=True, message="Amenities retrieved successfully", data=[
            {
                "id": a.id,
                "name": a.name,
                "category": a.category,
                "icon": a.icon,
                "description": a.description
            } for a in amenities
        ]
    )


@router.put("/{amenity_id}", summary="Update an existing amenity (Admin only)")
def update_amenity(amenity_id: int, request: AmenityUpdate, current_admin: User = Depends(require_roles(UserRole.ADMIN)), db: Session = Depends(get_db)):
    amenity = db.query(Amenity).filter(Amenity.id == amenity_id).first()
    if not amenity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Amenity not found")

    for field, value in request.model_dump(exclude_unset=True).items():
        if field == "category" and value:
            setattr(amenity, field, value.upper())
        else:
            setattr(amenity, field, value)

    db.commit()
    db.refresh(amenity)

    return api_response(
        success=True,
        message="Amenity updated successfully",
        data={
            "id": amenity.id,
            "name": amenity.name,
            "category": amenity.category,
            "icon": amenity.icon,
            "description": amenity.description,
            "is_active": amenity.is_active
        }
    )


@router.delete("/{amenity_id}", summary="Delete or deactivate an amenity (Admin only)")
def delete_amenity(amenity_id: int, current_admin: User = Depends(require_roles(UserRole.ADMIN)), db: Session = Depends(get_db)):
    amenity = db.query(Amenity).filter(Amenity.id == amenity_id).first()
    if not amenity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Amenity not found")

    amenity.is_active = False
    db.commit()

    return api_response(success=True, message=f"Amenity '{amenity.name}' deactivated successfully")


@router.post("/hotel/{hotel_id}/associate", summary="Associate amenities with a hotel")
def associate_hotel_amenities(hotel_id: int, request: AssociateAmenitiesRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    hotel = verify_hotel_access(hotel_id, current_user, db)

    added_count = 0
    for a_id in request.amenity_ids:
        amenity = db.query(Amenity).filter(Amenity.id == a_id, Amenity.is_active == True).first()
        if not amenity:
            continue
        exists = db.query(HotelAmenity).filter(
            HotelAmenity.hotel_id == hotel.id,
            HotelAmenity.amenity_id == a_id
        ).first()
        if not exists:
            ha = HotelAmenity(hotel_id=hotel.id, amenity_id=a_id)
            db.add(ha)
            added_count += 1

    db.commit()

    return api_response(
        success=True,
        message=f"{added_count} amenities associated with hotel successfully"
    )


class DirectAssociateRequest(AssociateAmenitiesRequest):
    hotel_id: Optional[int] = None


@router.post("/associate", summary="Associate amenities with a hotel (direct route)")
def associate_amenities_direct(
    request: DirectAssociateRequest,
    hotel_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_hotel_id = hotel_id or request.hotel_id
    if not target_hotel_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="hotel_id must be provided")

    return associate_hotel_amenities(
        hotel_id=target_hotel_id,
        request=request,
        current_user=current_user,
        db=db
    )



@router.delete("/hotel/{hotel_id}/amenity/{amenity_id}", summary="Disassociate an amenity from a hotel")
def disassociate_hotel_amenity(hotel_id: int, amenity_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    hotel = verify_hotel_access(hotel_id, current_user, db)

    ha = db.query(HotelAmenity).filter(
        HotelAmenity.hotel_id == hotel.id,
        HotelAmenity.amenity_id == amenity_id
    ).first()
    if not ha:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Amenity is not associated with this hotel")

    db.delete(ha)
    db.commit()

    return api_response(success=True, message="Amenity removed from hotel successfully")


@router.get("/hotel/{hotel_id}", summary="Retrieve all amenities associated with a hotel")
def get_hotel_amenities(hotel_id: int, db: Session = Depends(get_db)):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hotel not found")

    amenities = (
        db.query(Amenity)
        .join(HotelAmenity, HotelAmenity.amenity_id == Amenity.id)
        .filter(HotelAmenity.hotel_id == hotel_id, Amenity.is_active == True)
        .all()
    )

    return api_response(
        success=True,
        message="Hotel amenities retrieved successfully",
        data=[
            {
                "id": a.id,
                "name": a.name,
                "category": a.category,
                "icon": a.icon,
                "description": a.description
            } for a in amenities
        ]
    )


@router.get("/filter/hotels", summary="Filter hotels that have specific amenities")
def filter_hotels_by_amenities(
    amenity_ids: str,  # Comma separated e.g. "1,2,3"
    db: Session = Depends(get_db)
):
    try:
        id_list = [int(i.strip()) for i in amenity_ids.split(",") if i.strip()]
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="amenity_ids must be comma-separated integers")

    if not id_list:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one amenity_id required")

    from sqlalchemy import func, select
    subq = (
        select(HotelAmenity.hotel_id)
        .filter(HotelAmenity.amenity_id.in_(id_list))
        .group_by(HotelAmenity.hotel_id)
        .having(func.count(HotelAmenity.amenity_id) == len(id_list))
    )

    hotels = db.query(Hotel).filter(Hotel.id.in_(subq), Hotel.is_approved == True, Hotel.is_active == True).all()

    return api_response(
        success=True,
        message=f"Found {len(hotels)} hotels with selected amenities",
        data=[
            {
                "id": h.id,
                "name": h.name,
                "city": h.city,
                "star_rating": h.star_rating,
                "property_type": h.property_type
            } for h in hotels
        ]
    )
