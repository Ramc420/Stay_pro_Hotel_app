from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import Review, Hotel, Booking, User, UserRole
from schemas.review import (
    ReviewCreate, ReviewUpdate, ReviewResponse,
    ReviewReportRequest, ReviewModerationRequest, HotelReviewBreakdownResponse
)
from auth.dependencies import get_current_user, require_roles
from crud import review as crud_review
from utils.response import api_response

router = APIRouter(prefix="/reviews", tags=["Module 19: Reviews and Ratings"])


def _serialize_review(r: Review) -> dict:
    return {
        "id": r.id,
        "hotel_id": r.hotel_id,
        "hotel_name": r.hotel.name if r.hotel else None,
        "user_id": r.user_id,
        "user_name": r.user.full_name if r.user else "Anonymous",
        "booking_id": r.booking_id,
        "rating": r.rating,
        "comment": r.comment,
        "is_reported": r.is_reported,
        "report_reason": r.report_reason,
        "reported_at": r.reported_at.isoformat() if r.reported_at else None,
        "is_hidden": r.is_hidden,
        "moderation_status": r.moderation_status,
        "moderation_notes": r.moderation_notes,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None
    }


# ---------------------------------------------------------
# Create, Update, Delete Authorized Reviews
# ---------------------------------------------------------

@router.post("", summary="Submit a hotel review for a completed stay", status_code=status.HTTP_201_CREATED)
def create_review(
    request: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    review = crud_review.create_hotel_review(
        db=db,
        hotel_id=request.hotel_id,
        user_id=current_user.id,
        rating=request.rating,
        comment=request.comment,
        booking_id=request.booking_id
    )

    return api_response(
        success=True,
        message="Review submitted successfully and average rating updated",
        data=_serialize_review(review),
        status_code=status.HTTP_201_CREATED
    )


@router.put("/{review_id}", summary="Update an authorized review (Author only)")
def update_review(
    review_id: int,
    request: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    review = crud_review.get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    if review.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only edit your own reviews")

    updated = crud_review.update_hotel_review(
        db=db,
        review=review,
        rating=request.rating,
        comment=request.comment
    )

    return api_response(
        success=True,
        message="Review updated successfully",
        data=_serialize_review(updated)
    )


@router.delete("/{review_id}", summary="Delete a review (Author or Admin)")
def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    review = crud_review.get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    if review.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete this review")

    crud_review.delete_hotel_review(db, review)

    return api_response(
        success=True,
        message="Review deleted successfully and hotel rating recalculated"
    )


# ---------------------------------------------------------
# Query Reviews
# ---------------------------------------------------------

@router.get("/hotel/{hotel_id}", summary="Retrieve reviews and rating breakdown for a hotel")
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
    reviews = crud_review.list_hotel_reviews(db, hotel_id, include_hidden=False, skip=skip, limit=limit)

    return api_response(
        success=True,
        message="Hotel reviews retrieved successfully",
        data={
            "hotel_id": hotel_id,
            "hotel_name": hotel.name,
            "summary": summary,
            "reviews": [_serialize_review(r) for r in reviews]
        }
    )


@router.get("/my-reviews", summary="Retrieve all reviews submitted by the logged-in user")
def get_my_reviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reviews = crud_review.list_user_reviews(db, current_user.id)
    return api_response(
        success=True,
        message="Your reviews retrieved successfully",
        data=[_serialize_review(r) for r in reviews]
    )


@router.get("/{review_id}", summary="Retrieve review details by ID")
def get_review_by_id(
    review_id: int,
    db: Session = Depends(get_db)
):
    review = crud_review.get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    return api_response(
        success=True,
        message="Review retrieved successfully",
        data=_serialize_review(review)
    )


# ---------------------------------------------------------
# Reporting & Moderation
# ---------------------------------------------------------

@router.post("/{review_id}/report", summary="Report an inappropriate or abusive review")
def report_review(
    review_id: int,
    request: ReviewReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    review = crud_review.get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    reported_review = crud_review.report_hotel_review(db, review, request.reason)

    return api_response(
        success=True,
        message="Review reported successfully and flagged for administrator moderation",
        data=_serialize_review(reported_review)
    )


@router.get("/moderation/reported", summary="List all reported reviews flagged for moderation (Admin only)")
def list_reported_reviews(
    hotel_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    reviews = crud_review.list_reported_reviews(db, hotel_id=hotel_id, skip=skip, limit=limit)
    return api_response(
        success=True,
        message="Reported reviews retrieved successfully",
        data=[_serialize_review(r) for r in reviews]
    )


@router.post("/{review_id}/moderate", summary="Moderate a reported review: APPROVE, HIDE, or REMOVE (Admin only)")
def moderate_review(
    review_id: int,
    request: ReviewModerationRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    review = crud_review.get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    moderated_review = crud_review.moderate_hotel_review(
        db=db,
        review=review,
        action=request.action,
        moderator=current_user,
        notes=request.notes
    )

    action_msg = {
        "APPROVE": "Review approved and report flag dismissed",
        "HIDE": "Review hidden from public view",
        "REMOVE": "Review permanently removed"
    }.get(request.action.upper(), "Review moderation updated")

    return api_response(
        success=True,
        message=action_msg,
        data=_serialize_review(moderated_review) if request.action.upper() != "REMOVE" else None
    )
