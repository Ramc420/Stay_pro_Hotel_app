"""
Module 44: Location Services
Coordinates storage, mapping integration, distance calculation, nearby attractions, and radius search.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.dependencies import verify_hotel_access, require_roles
from utils.response import api_response
from schemas.location import (
    CoordinatesUpdate, HotelAttractionCreate, DistanceCalculationRequest
)
from crud import location as crud_loc

router = APIRouter(prefix="/locations", tags=["Module 44: Location Services"])


@router.put("/hotels/{hotel_id}/coordinates", summary="Update and validate hotel latitude/longitude coordinates")
def set_coordinates(
    hotel_id: int,
    request: CoordinatesUpdate,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    try:
        hotel = crud_loc.update_hotel_coordinates(
            db=db,
            hotel_id=hotel_id,
            latitude=request.latitude,
            longitude=request.longitude,
            formatted_address=request.formatted_address
        )
        return api_response(
            success=True,
            message="Hotel coordinates verified and stored successfully",
            data={
                "hotel_id": hotel.id,
                "latitude": hotel.latitude,
                "longitude": hotel.longitude,
                "address": hotel.address_line1
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/hotels/{hotel_id}/attractions", summary="Retrieve local attractions and landmarks near hotel")
def list_attractions(
    hotel_id: int,
    db: Session = Depends(get_db)
):
    try:
        attractions = crud_loc.get_hotel_attractions(db, hotel_id)
        return api_response(
            success=True,
            message="Nearby attractions retrieved",
            data=attractions
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/hotels/{hotel_id}/attractions", summary="Add a nearby landmark or attraction to hotel")
def add_attraction(
    hotel_id: int,
    request: HotelAttractionCreate,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    try:
        attraction = crud_loc.add_hotel_attraction(
            db=db,
            hotel_id=hotel_id,
            name=request.name,
            category=request.category,
            latitude=request.latitude,
            longitude=request.longitude,
            description=request.description,
            icon=request.icon
        )
        return api_response(
            success=True,
            message="Attraction added successfully",
            data={
                "id": attraction.id,
                "hotel_id": attraction.hotel_id,
                "name": attraction.name,
                "category": attraction.category,
                "latitude": attraction.latitude,
                "longitude": attraction.longitude,
                "distance_km": attraction.distance_km,
                "created_at": attraction.created_at.isoformat()
            },
            status_code=status.HTTP_201_CREATED
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/nearby-hotels", summary="Search verified hotels within radius of coordinates")
def search_nearby(
    latitude: float,
    longitude: float,
    radius_km: float = 50.0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    try:
        hotels = crud_loc.find_nearby_hotels(
            db=db,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            limit=limit
        )
        return api_response(
            success=True,
            message=f"Found {len(hotels)} hotel(s) within {radius_km} km",
            data=hotels
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/distance-matrix", summary="Calculate distance and drive duration between two points")
def get_distance_matrix(
    request: DistanceCalculationRequest
):
    try:
        result = crud_loc.calculate_matrix_distance(
            origin_lat=request.origin_lat,
            origin_lon=request.origin_lon,
            dest_lat=request.destination_lat,
            dest_lon=request.destination_lon
        )
        return api_response(
            success=True,
            message="Distance and route calculated",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
