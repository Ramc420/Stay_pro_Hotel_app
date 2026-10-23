from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from utils.response import paginated_response
from crud.search import search_and_filter_hotels

router = APIRouter(prefix="/search", tags=["Module 9: Hotel Search System"])


@router.get("", summary="Search hotels (root alias)")
@router.get("/", summary="Search hotels (slash alias)")
@router.get("/hotels", summary="Search hotels by keyword, name, location, guest capacity, and coordinates")
def search_hotels(
    q: Optional[str] = Query(None, description="Search keyword matching hotel name, city, state, country, or description"),
    name: Optional[str] = Query(None, description="Filter specifically by hotel name"),
    location: Optional[str] = Query(None, description="Filter by location (city, state, country, address)"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state/province"),
    country: Optional[str] = Query(None, description="Filter by country"),
    room_type: Optional[str] = Query(None, description="Filter by room type name or code e.g. Deluxe, Suite"),
    guests: Optional[int] = Query(None, description="Minimum guest capacity required"),
    latitude: Optional[float] = Query(None, description="User latitude for nearby distance calculation"),
    longitude: Optional[float] = Query(None, description="User longitude for nearby distance calculation"),
    radius_km: Optional[float] = Query(50.0, description="Search radius in kilometers when coordinates are supplied"),
    min_price: Optional[float] = Query(None, description="Minimum price per night"),
    max_price: Optional[float] = Query(None, description="Maximum price per night"),
    min_rating: Optional[float] = Query(None, description="Minimum star rating (0-5)"),
    max_rating: Optional[float] = Query(None, description="Maximum star rating (0-5)"),
    property_type: Optional[str] = Query(None, description="HOTEL, RESORT, VILLA, APARTMENT, etc."),
    amenity_ids: Optional[str] = Query(None, description="Comma-separated amenity IDs e.g. '1,2,5'"),
    amenities: Optional[str] = Query(None, description="Comma-separated amenity IDs or names"),
    check_in: Optional[date] = Query(None, description="Check-in date (YYYY-MM-DD)"),
    check_out: Optional[date] = Query(None, description="Check-out date (YYYY-MM-DD)"),
    sort_by: Optional[str] = Query("rating_desc", description="price_asc, price_desc, rating_desc, rating_asc, name_asc, name_desc, distance_asc, distance_desc"),
    page: int = Query(1, description="Page number (1-indexed)"),
    limit: int = Query(10, description="Items per page"),
    db: Session = Depends(get_db)
):
    result = search_and_filter_hotels(
        db=db,
        q=q,
        name=name,
        location=location,
        city=city,
        state=state,
        country=country,
        property_type=property_type,
        min_rating=min_rating,
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
        message=f"Found {result['total']} hotels matching search criteria"
    )

