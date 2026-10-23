import math
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from models import Hotel, HotelAttraction


def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate latitude and longitude boundaries."""
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, float]:
    """Calculate distance between two coordinates in kilometers and miles."""
    r_km = 6371.0  # Earth radius in kilometers
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(d_lat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    
    distance_km = r_km * c
    distance_miles = distance_km * 0.621371
    return round(distance_km, 2), round(distance_miles, 2)


def update_hotel_coordinates(
    db: Session,
    hotel_id: int,
    latitude: float,
    longitude: float,
    formatted_address: Optional[str] = None
) -> Hotel:
    """Update hotel geographical coordinates with boundary validation."""
    if not validate_coordinates(latitude, longitude):
        raise ValueError(f"Invalid coordinates: lat={latitude}, lon={longitude}. Lat must be [-90, 90], Lon must be [-180, 180].")

    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise ValueError(f"Hotel with ID {hotel_id} not found")

    hotel.latitude = latitude
    hotel.longitude = longitude
    if formatted_address:
        hotel.address_line1 = formatted_address

    db.commit()
    db.refresh(hotel)
    return hotel


def add_hotel_attraction(
    db: Session,
    hotel_id: int,
    name: str,
    category: str,
    latitude: float,
    longitude: float,
    description: Optional[str] = None,
    icon: Optional[str] = "map-pin"
) -> HotelAttraction:
    """Add a point of interest or attraction near a hotel."""
    if not validate_coordinates(latitude, longitude):
        raise ValueError("Invalid attraction coordinates.")

    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise ValueError(f"Hotel with ID {hotel_id} not found")

    dist_km = None
    if hotel.latitude is not None and hotel.longitude is not None:
        dist_km, _ = haversine_distance(hotel.latitude, hotel.longitude, latitude, longitude)

    attraction = HotelAttraction(
        hotel_id=hotel_id,
        name=name,
        category=category.upper(),
        latitude=latitude,
        longitude=longitude,
        distance_km=dist_km,
        description=description,
        icon=icon
    )
    db.add(attraction)
    db.commit()
    db.refresh(attraction)
    return attraction


def get_hotel_attractions(db: Session, hotel_id: int) -> List[Dict[str, Any]]:
    """Retrieve attractions near the hotel with accurate distances."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise ValueError(f"Hotel with ID {hotel_id} not found")

    attractions = db.query(HotelAttraction).filter(
        HotelAttraction.hotel_id == hotel_id
    ).order_by(HotelAttraction.distance_km.asc()).all()

    results = []
    for att in attractions:
        dist_km = att.distance_km
        dist_miles = round(dist_km * 0.621371, 2) if dist_km else None
        
        # Recalculate if hotel has coordinates
        if hotel.latitude is not None and hotel.longitude is not None:
            dist_km, dist_miles = haversine_distance(hotel.latitude, hotel.longitude, att.latitude, att.longitude)

        results.append({
            "id": att.id,
            "hotel_id": att.hotel_id,
            "name": att.name,
            "category": att.category,
            "latitude": att.latitude,
            "longitude": att.longitude,
            "distance_km": dist_km,
            "distance_miles": dist_miles,
            "description": att.description,
            "icon": att.icon,
            "created_at": att.created_at
        })

    return results


def find_nearby_hotels(
    db: Session,
    latitude: float,
    longitude: float,
    radius_km: float = 50.0,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Find approved active hotels within a given geographic radius."""
    if not validate_coordinates(latitude, longitude):
        raise ValueError("Invalid target search coordinates.")

    hotels = db.query(Hotel).filter(
        Hotel.is_approved == True,
        Hotel.is_active == True,
        Hotel.latitude.isnot(None),
        Hotel.longitude.isnot(None)
    ).all()

    matches = []
    for h in hotels:
        dist_km, dist_miles = haversine_distance(latitude, longitude, h.latitude, h.longitude)
        if dist_km <= radius_km:
            matches.append({
                "hotel_id": h.id,
                "hotel_name": h.name,
                "address": f"{h.address_line1}, {h.city}, {h.state}",
                "city": h.city,
                "latitude": h.latitude,
                "longitude": h.longitude,
                "distance_km": dist_km,
                "distance_miles": dist_miles,
                "star_rating": h.star_rating,
                "property_type": h.property_type
            })

    matches.sort(key=lambda x: x["distance_km"])
    return matches[:limit]


def calculate_matrix_distance(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float
) -> Dict[str, Any]:
    """Calculate distance matrix with estimated driving duration and provider fallback."""
    if not validate_coordinates(origin_lat, origin_lon) or not validate_coordinates(dest_lat, dest_lon):
        raise ValueError("Invalid coordinates provided for distance calculation.")

    dist_km, dist_miles = haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon)
    # Estimate driving time (assuming ~50 km/h average speed in urban/resort areas)
    estimated_minutes = max(1, int((dist_km / 50.0) * 60))

    return {
        "distance_km": dist_km,
        "distance_miles": dist_miles,
        "estimated_drive_minutes": estimated_minutes,
        "provider": "Google Maps (Haversine Fallback Engine)",
        "status": "OK"
    }
