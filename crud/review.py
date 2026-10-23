from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from models.review import Review
from models.hotel import Hotel
from models.booking import Booking, BookingStatus
from models.user import User, UserRole


def recalculate_hotel_rating(db: Session, hotel_id: int):
    """
    Recalculates the average star rating for a hotel using all active/approved reviews.
    """
    avg_rating = (
        db.query(func.avg(Review.rating))
        .filter(
            Review.hotel_id == hotel_id,
            Review.is_hidden == False
        )
        .scalar()
    )
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if hotel:
        hotel.star_rating = round(float(avg_rating), 1) if avg_rating is not None else 0.0
        db.commit()


def get_review_by_id(db: Session, review_id: int) -> Optional[Review]:
    return db.query(Review).filter(Review.id == review_id).first()


def create_hotel_review(
    db: Session,
    hotel_id: Optional[int],
    user_id: int,
    rating: float,
    comment: Optional[str] = None,
    booking_id: Optional[int] = None
) -> Review:
    # 1. Eligibility Check: If booking_id is provided, verify stay completion
    target_hotel_id = hotel_id

    if booking_id:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

        if booking.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only review your own completed stays")

        # Check stay status
        if booking.status not in [BookingStatus.CHECKED_OUT, BookingStatus.COMPLETED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only completed or checked-out stays can be reviewed (Current status: {booking.status.value})"
            )

        # Duplicate check: prevent duplicate reviews for the same stay
        existing = db.query(Review).filter(Review.booking_id == booking_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A review has already been submitted for this stay reservation"
            )

        target_hotel_id = booking.hotel_id

    if not target_hotel_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="hotel_id or valid booking_id is required")

    hotel = db.query(Hotel).filter(Hotel.id == target_hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Hotel with ID {target_hotel_id} not found")

    review = Review(
        hotel_id=target_hotel_id,
        user_id=user_id,
        booking_id=booking_id,
        rating=round(float(rating), 1),
        comment=comment,
        is_reported=False,
        is_hidden=False,
        moderation_status="APPROVED"
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    # Recalculate average star rating
    recalculate_hotel_rating(db, target_hotel_id)

    return review


def update_hotel_review(
    db: Session,
    review: Review,
    rating: Optional[float] = None,
    comment: Optional[str] = None
) -> Review:
    if rating is not None:
        review.rating = round(float(rating), 1)
    if comment is not None:
        review.comment = comment
    review.updated_at = datetime.now()

    db.commit()
    db.refresh(review)

    recalculate_hotel_rating(db, review.hotel_id)
    return review


def delete_hotel_review(db: Session, review: Review) -> bool:
    hotel_id = review.hotel_id
    db.delete(review)
    db.commit()

    recalculate_hotel_rating(db, hotel_id)
    return True


def report_hotel_review(
    db: Session,
    review: Review,
    reason: str
) -> Review:
    review.is_reported = True
    review.report_reason = reason
    review.reported_at = datetime.now()
    review.moderation_status = "REPORTED"
    db.commit()
    db.refresh(review)
    return review


def moderate_hotel_review(
    db: Session,
    review: Review,
    action: str,
    moderator: User,
    notes: Optional[str] = None
) -> Review:
    action_upper = action.upper().strip()
    if action_upper not in ["APPROVE", "HIDE", "REMOVE"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Moderation action must be one of: 'APPROVE', 'HIDE', 'REMOVE'"
        )

    review.moderated_by_id = moderator.id
    review.moderated_at = datetime.now()
    review.moderation_notes = notes

    if action_upper == "APPROVE":
        review.is_reported = False
        review.is_hidden = False
        review.moderation_status = "APPROVED"
        db.commit()
        db.refresh(review)
        recalculate_hotel_rating(db, review.hotel_id)
    elif action_upper == "HIDE":
        review.is_hidden = True
        review.moderation_status = "HIDDEN"
        db.commit()
        db.refresh(review)
        recalculate_hotel_rating(db, review.hotel_id)
    elif action_upper == "REMOVE":
        hotel_id = review.hotel_id
        db.delete(review)
        db.commit()
        recalculate_hotel_rating(db, hotel_id)
        return review

    return review


def list_hotel_reviews(
    db: Session,
    hotel_id: int,
    include_hidden: bool = False,
    skip: int = 0,
    limit: int = 20
) -> List[Review]:
    query = db.query(Review).filter(Review.hotel_id == hotel_id)
    if not include_hidden:
        query = query.filter(Review.is_hidden == False)
    return query.order_by(Review.created_at.desc()).offset(skip).limit(limit).all()


def list_user_reviews(db: Session, user_id: int) -> List[Review]:
    return db.query(Review).filter(Review.user_id == user_id).order_by(Review.created_at.desc()).all()


def list_reported_reviews(
    db: Session,
    hotel_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50
) -> List[Review]:
    query = db.query(Review).filter(Review.is_reported == True)
    if hotel_id is not None:
        query = query.filter(Review.hotel_id == hotel_id)
    return query.order_by(Review.reported_at.desc()).offset(skip).limit(limit).all()


def get_hotel_reviews_summary(db: Session, hotel_id: int) -> Dict[str, Any]:
    reviews = db.query(Review).filter(
        Review.hotel_id == hotel_id,
        Review.is_hidden == False
    ).all()
    total = len(reviews)
    if total == 0:
        return {
            "total_reviews": 0,
            "average_rating": 0.0,
            "rating_breakdown": {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        }

    avg_rating = sum(r.rating for r in reviews) / total
    breakdown = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for r in reviews:
        star = int(round(r.rating))
        if star in breakdown:
            breakdown[star] += 1

    return {
        "total_reviews": total,
        "average_rating": round(avg_rating, 1),
        "rating_breakdown": breakdown
    }
