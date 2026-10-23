from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from utils.response import paginated_response
from crud.search import search_and_filter_hotels

router = APIRouter(prefix="/filters", tags=["Module 10: Advanced Hotel Filters"])


@router.get("", summary="Filter hotels (root alias)")
@router.get("/", summary="Filter hotels (slash alias)")
@router.get("/hotels", summary="Advanced multi-criteria filtering for hotels")
def filter_hotels(
    min_price: Optional[float] = Query(None, description="Minimum price per night"),
    max_price: Optional[float] = Query(None, description="Maximum price per night"),
    min_rating: Optional[float] = Query(None, description="Minimum star rating (0-5)"),
    max_rating: Optional[float] = Query(None, description="Maximum star rating (0-5)"),
    rating: Optional[float] = Query(None, description="Alias for min_rating"),
    star_rating: Optional[float] = Query(None, description="Alias for min_rating"),
    property_type: Optional[str] = Query(None, description="HOTEL, RESORT, VILLA, APARTMENT, etc. (comma-separated for multiple)"),
    amenity_ids: Optional[str] = Query(None, description="Comma-separated amenity IDs e.g. '1,2,5'"),
    amenities: Optional[str] = Query(None, description="Comma-separated amenity IDs or names"),
    check_in: Optional[date] = Query(None, description="Check-in date (YYYY-MM-DD)"),
    check_out: Optional[date] = Query(None, description="Check-out date (YYYY-MM-DD)"),
    guests: Optional[int] = Query(None, description="Number of guests required"),
    city: Optional[str] = Query(None, description="Filter by city name"),
    state: Optional[str] = Query(None, description="Filter by state name"),
    country: Optional[str] = Query(None, description="Filter by country name"),
    location: Optional[str] = Query(None, description="Filter by general location"),
    name: Optional[str] = Query(None, description="Filter by hotel name"),
    q: Optional[str] = Query(None, description="Keyword search"),
    latitude: Optional[float] = Query(None, description="User latitude"),
    longitude: Optional[float] = Query(None, description="User longitude"),
    radius_km: Optional[float] = Query(50.0, description="Search radius in kilometers"),
    sort_by: Optional[str] = Query("price_asc", description="price_asc, price_desc, rating_desc, rating_asc, name_asc, name_desc, distance_asc, distance_desc"),
    page: int = Query(1, description="Page number (1-indexed)"),
    limit: int = Query(10, description="Items per page"),
    db: Session = Depends(get_db)
):
    # Support rating aliases
    effective_min_rating = min_rating
    if effective_min_rating is None:
        if rating is not None:
            effective_min_rating = rating
        elif star_rating is not None:
            effective_min_rating = star_rating

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
        message=f"Found {result['total']} hotels matching filter criteria"
    )

