from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas.recommendation import HotelRecommendationResponse
from auth.dependencies import get_current_user, get_optional_current_user
from crud import recommendation as crud_recommendation
from utils.response import api_response

router = APIRouter(prefix="/recommendations", tags=["Module 21: AI Hotel Recommendation Engine"])


@router.get("/personalized", summary="Retrieve AI personalized hotel recommendations for customer")
def get_personalized_recommendations(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recommendations = crud_recommendation.get_personalized_recommendations(
        db=db,
        user_id=current_user.id,
        limit=limit
    )

    return api_response(
        success=True,
        message="Personalized hotel recommendations generated successfully",
        data=recommendations
    )


@router.get("/budget-location", summary="Generate budget-based and location-based hotel suggestions")
def get_budget_and_location_recommendations(
    city: Optional[str] = Query(None, description="Target city destination"),
    country: Optional[str] = Query(None, description="Target country"),
    min_budget: Optional[float] = Query(None, ge=0, description="Minimum price per night"),
    max_budget: Optional[float] = Query(None, ge=0, description="Maximum price per night"),
    guests_count: int = Query(1, ge=1, le=20, description="Number of guests"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    recommendations = crud_recommendation.get_budget_and_location_recommendations(
        db=db,
        city=city,
        country=country,
        min_budget=min_budget,
        max_budget=max_budget,
        guests_count=guests_count,
        limit=limit
    )

    return api_response(
        success=True,
        message="Budget and location based suggestions generated successfully",
        data=recommendations
    )


@router.get("/similar/{hotel_id}", summary="Provide similar-hotel recommendations based on property features")
def get_similar_hotels(
    hotel_id: int,
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db)
):
    recommendations = crud_recommendation.get_similar_hotels(
        db=db,
        hotel_id=hotel_id,
        limit=limit
    )

    return api_response(
        success=True,
        message="Similar hotel suggestions retrieved successfully",
        data=recommendations
    )
