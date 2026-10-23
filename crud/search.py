from datetime import date, timedelta
from typing import Optional, List, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, select
from fastapi import HTTPException, status

from models.hotel import Hotel, HotelStatus, HotelImage, HotelVerificationDocument
from models.room import Room, RoomType, RoomStatus
from models.amenity import Amenity, HotelAmenity
from models.availability import RoomAvailability, AvailabilityStatus
from utils.geo import haversine_distance


def validate_search_filter_params(
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    check_in: Optional[date] = None,
    check_out: Optional[date] = None,
    guests: Optional[int] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[float] = None,
    page: Optional[int] = None,
    limit: Optional[int] = None,
    sort_by: Optional[str] = None
) -> None:
    """
    Validates all search and filter query parameters and raises HTTPException(400) if invalid.
    """
    # 1. Price validations
    if min_price is not None and min_price < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price cannot be negative"
        )
    if max_price is not None and max_price < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_price cannot be negative"
        )
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price cannot be greater than max_price"
        )

    # 2. Rating validations (0 to 5 scale)
    if min_rating is not None and (min_rating < 0 or min_rating > 5.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_rating must be between 0 and 5"
        )
    if max_rating is not None and (max_rating < 0 or max_rating > 5.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_rating must be between 0 and 5"
        )
    if min_rating is not None and max_rating is not None and min_rating > max_rating:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_rating cannot be greater than max_rating"
        )

    # 3. Check-in and check-out date validations
    if (check_in and not check_out) or (check_out and not check_in):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both check_in and check_out dates must be provided together"
        )
    if check_in and check_out and check_out <= check_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="check_out date must be strictly after check_in date"
        )

    # 4. Guest capacity validation
    if guests is not None and guests < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="guests must be at least 1"
        )

    # 5. Geolocation coordinates validation
    if (latitude is not None and longitude is None) or (longitude is not None and latitude is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both latitude and longitude must be provided together"
        )
    if latitude is not None and (latitude < -90.0 or latitude > 90.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="latitude must be between -90 and 90"
        )
    if longitude is not None and (longitude < -180.0 or longitude > 180.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="longitude must be between -180 and 180"
        )
    if radius_km is not None and radius_km <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="radius_km must be greater than 0"
        )

    # 6. Pagination validations
    if page is not None and page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="page must be greater than or equal to 1"
        )
    if limit is not None and limit < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit must be greater than or equal to 1"
        )

    # 7. Sorting validation
    valid_sorts = [
        "price_asc", "price_desc", "rating_desc", "rating_asc",
        "name_asc", "name_desc", "distance_asc", "distance_desc"
    ]
    if sort_by and sort_by not in valid_sorts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort_by option '{sort_by}'. Allowed options: {', '.join(valid_sorts)}"
        )


def parse_amenity_filters(db: Session, amenity_ids_raw: Optional[str], amenities_raw: Optional[str]) -> List[int]:
    """
    Parses comma-separated amenity IDs or names into a list of unique integer amenity IDs.
    Raises HTTPException(400) if format is invalid.
    """
    target_ids = set()

    # Parse amenity_ids_raw (e.g. "1,2,5")
    if amenity_ids_raw:
        for item in amenity_ids_raw.split(","):
            val = item.strip()
            if not val:
                continue
            if val.isdigit():
                target_ids.add(int(val))
            else:
                # Try finding by amenity name
                amenity = db.query(Amenity).filter(Amenity.name.ilike(val), Amenity.is_active == True).first()
                if amenity:
                    target_ids.add(amenity.id)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"amenity_ids must be a comma-separated list of integers"
                    )

    # Parse amenities_raw (e.g. "Free Wi-Fi, Pool" or "1,2")
    if amenities_raw:
        for item in amenities_raw.split(","):
            val = item.strip()
            if not val:
                continue
            if val.isdigit():
                target_ids.add(int(val))
            else:
                amenity = db.query(Amenity).filter(Amenity.name.ilike(val), Amenity.is_active == True).first()
                if amenity:
                    target_ids.add(amenity.id)
                else:
                    # If an amenity name is given that does not exist in the system,
                    # return a non-existent ID so zero hotels will match (relational division)
                    target_ids.add(-999999)

    return list(target_ids)


def search_and_filter_hotels(
    db: Session,
    q: Optional[str] = None,
    name: Optional[str] = None,
    location: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
    property_type: Optional[str] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    amenity_ids: Optional[str] = None,
    amenities: Optional[str] = None,
    room_type: Optional[str] = None,
    guests: Optional[int] = None,
    check_in: Optional[date] = None,
    check_out: Optional[date] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[float] = 50.0,
    sort_by: Optional[str] = "rating_desc",
    page: int = 1,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Comprehensive search and filter engine covering all Module 9 and Module 10 requirements.
    """
    # 1. Parameter Validation
    validate_search_filter_params(
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        max_rating=max_rating,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        page=page,
        limit=limit,
        sort_by=sort_by
    )

    # 2. Base Query: Approved and Active Hotels
    query = db.query(Hotel).filter(
        Hotel.is_approved == True,
        Hotel.is_active == True,
        Hotel.status == HotelStatus.APPROVED
    )

    # 3. Text & Location Filtering
    if q:
        keyword = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Hotel.name.ilike(keyword),
                Hotel.city.ilike(keyword),
                Hotel.state.ilike(keyword),
                Hotel.country.ilike(keyword),
                Hotel.address_line1.ilike(keyword),
                Hotel.description.ilike(keyword)
            )
        )

    if name:
        query = query.filter(Hotel.name.ilike(f"%{name.strip()}%"))

    if location:
        loc_kw = f"%{location.strip()}%"
        query = query.filter(
            or_(
                Hotel.city.ilike(loc_kw),
                Hotel.state.ilike(loc_kw),
                Hotel.country.ilike(loc_kw),
                Hotel.address_line1.ilike(loc_kw)
            )
        )

    if city:
        query = query.filter(Hotel.city.ilike(f"%{city.strip()}%"))

    if state:
        query = query.filter(Hotel.state.ilike(f"%{state.strip()}%"))

    if country:
        query = query.filter(Hotel.country.ilike(f"%{country.strip()}%"))

    # 4. Property Type Filtering (supports comma-separated list like "HOTEL,RESORT")
    if property_type:
        types = [t.strip() for t in property_type.split(",") if t.strip()]
        if types:
            query = query.filter(or_(*[Hotel.property_type.ilike(f"%{t}%") for t in types]))

    # 5. Rating Filtering
    if min_rating is not None:
        query = query.filter(Hotel.star_rating >= min_rating)
    if max_rating is not None:
        query = query.filter(Hotel.star_rating <= max_rating)

    # 6. Amenity Filtering (Hotels must possess ALL specified amenities)
    resolved_amenity_ids = parse_amenity_filters(db, amenity_ids, amenities)
    if resolved_amenity_ids:
        subq = (
            select(HotelAmenity.hotel_id)
            .filter(HotelAmenity.amenity_id.in_(resolved_amenity_ids))
            .group_by(HotelAmenity.hotel_id)
            .having(func.count(HotelAmenity.amenity_id) == len(resolved_amenity_ids))
        )
        query = query.filter(Hotel.id.in_(subq))

    # 7. Room Type & Guest Capacity (SQL pre-filter)
    if room_type or (guests and not (check_in and check_out)):
        rt_query = db.query(RoomType.hotel_id).filter(RoomType.is_active == True)
        if room_type:
            rt_query = rt_query.filter(
                or_(
                    RoomType.name.ilike(f"%{room_type.strip()}%"),
                    RoomType.code.ilike(f"%{room_type.strip()}%")
                )
            )
        if guests:
            rt_query = rt_query.filter(RoomType.max_occupancy >= guests)
        hotel_ids_with_room = [r[0] for r in rt_query.distinct().all()]
        query = query.filter(Hotel.id.in_(hotel_ids_with_room))

    candidate_hotels = query.all()

    # 8. Room Pricing, Date Availability, and Geolocation Filtering
    results = []
    has_coords = (latitude is not None and longitude is not None)
    search_radius = radius_km if radius_km is not None else 50.0

    for h in candidate_hotels:
        # Distance calculation
        dist = None
        if has_coords:
            if h.latitude is None or h.longitude is None:
                # Exclude hotels with no coordinates when coordinate search is requested
                continue
            dist = haversine_distance(latitude, longitude, h.latitude, h.longitude)
            if dist > search_radius:
                continue

        # Fetch active room types for this hotel
        rt_q = db.query(RoomType).filter(RoomType.hotel_id == h.id, RoomType.is_active == True)
        all_room_types = rt_q.all()

        # If price filter or guest capacity filter is active
        matching_rts = all_room_types
        if room_type:
            matching_rts = [
                rt for rt in matching_rts
                if room_type.lower() in rt.name.lower() or room_type.lower() in rt.code.lower()
            ]
        if guests:
            matching_rts = [rt for rt in matching_rts if rt.max_occupancy >= guests]
        if min_price is not None:
            matching_rts = [rt for rt in matching_rts if rt.base_price_per_night >= min_price]
        if max_price is not None:
            matching_rts = [rt for rt in matching_rts if rt.base_price_per_night <= max_price]

        # If any price, room_type, or guest filter was specified, hotel must have matching room types
        if (min_price is not None or max_price is not None or room_type or guests) and not matching_rts:
            continue

        # Compute minimum price per night
        if matching_rts:
            min_price_per_night = min(rt.base_price_per_night for rt in matching_rts)
        elif all_room_types:
            min_price_per_night = min(rt.base_price_per_night for rt in all_room_types)
        else:
            min_price_per_night = 0.0

        # Check date range availability if dates are provided
        if check_in and check_out:
            candidate_rt_ids = [rt.id for rt in (matching_rts if matching_rts else all_room_types)]
            if not candidate_rt_ids:
                continue

            # Find active rooms in these room types
            candidate_rooms = db.query(Room).filter(
                Room.hotel_id == h.id,
                Room.room_type_id.in_(candidate_rt_ids),
                Room.is_active == True
            ).all()

            if not candidate_rooms:
                continue

            available_room_found = False
            for r in candidate_rooms:
                # Check for booking/blocking conflict in the date range
                conflict = db.query(RoomAvailability).filter(
                    RoomAvailability.room_id == r.id,
                    RoomAvailability.date >= check_in,
                    RoomAvailability.date < check_out,
                    RoomAvailability.status.in_([
                        AvailabilityStatus.BOOKED,
                        AvailabilityStatus.BLOCKED,
                        AvailabilityStatus.MAINTENANCE
                    ])
                ).first()
                if not conflict:
                    available_room_found = True
                    break

            if not available_room_found:
                continue

        # Fetch Primary Image or first image
        primary_img = db.query(HotelImage).filter(
            HotelImage.hotel_id == h.id,
            HotelImage.is_primary == True
        ).first()
        if not primary_img:
            primary_img = db.query(HotelImage).filter(
                HotelImage.hotel_id == h.id
            ).order_by(HotelImage.display_order).first()

        # Fetch Amenity Names
        amenity_names = [
            a.name for a in (
                db.query(Amenity)
                .join(HotelAmenity, HotelAmenity.amenity_id == Amenity.id)
                .filter(HotelAmenity.hotel_id == h.id, Amenity.is_active == True)
                .all()
            )
        ]

        # Room Type Names to display
        rt_names_to_show = [rt.name for rt in (matching_rts if matching_rts else all_room_types)]

        results.append({
            "id": h.id,
            "name": h.name,
            "description": h.description,
            "property_type": h.property_type,
            "star_rating": h.star_rating,
            "city": h.city,
            "state": h.state,
            "country": h.country,
            "address_line1": h.address_line1,
            "latitude": h.latitude,
            "longitude": h.longitude,
            "distance_km": dist,
            "min_price_per_night": min_price_per_night,
            "primary_image": primary_img.image_url if primary_img else None,
            "available_room_types": rt_names_to_show,
            "amenities": amenity_names,
            "check_in_time": h.check_in_time,
            "check_out_time": h.check_out_time
        })

    # 9. Sorting
    effective_sort = sort_by or "rating_desc"
    if effective_sort == "price_asc":
        results.sort(key=lambda x: x["min_price_per_night"] if x["min_price_per_night"] is not None else float("inf"))
    elif effective_sort == "price_desc":
        results.sort(key=lambda x: x["min_price_per_night"] if x["min_price_per_night"] is not None else -1, reverse=True)
    elif effective_sort == "rating_desc":
        results.sort(key=lambda x: x["star_rating"], reverse=True)
    elif effective_sort == "rating_asc":
        results.sort(key=lambda x: x["star_rating"])
    elif effective_sort == "name_asc":
        results.sort(key=lambda x: x["name"].lower())
    elif effective_sort == "name_desc":
        results.sort(key=lambda x: x["name"].lower(), reverse=True)
    elif effective_sort == "distance_asc":
        results.sort(key=lambda x: x["distance_km"] if x["distance_km"] is not None else float("inf"))
    elif effective_sort == "distance_desc":
        results.sort(key=lambda x: x["distance_km"] if x["distance_km"] is not None else -1, reverse=True)

    # 10. Pagination
    total = len(results)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_items = results[start_idx:end_idx]

    return {
        "items": paginated_items,
        "total": total,
        "page": page,
        "limit": limit
    }
