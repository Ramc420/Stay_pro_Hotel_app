from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.coupon import Coupon, CouponUsage, DiscountType, DiscountCategory
from models.booking import Booking, BookingHistory
from models.hotel import Hotel
from models.user import User


def get_coupon_by_code(db: Session, code: str) -> Optional[Coupon]:
    return db.query(Coupon).filter(Coupon.code == code.upper().strip()).first()


def get_coupon_by_id(db: Session, coupon_id: int) -> Optional[Coupon]:
    return db.query(Coupon).filter(Coupon.id == coupon_id).first()


def create_coupon(
    db: Session,
    code: str,
    discount_type: DiscountType,
    discount_value: float,
    start_date: datetime,
    expiry_date: datetime,
    description: Optional[str] = None,
    max_discount_amount: Optional[float] = None,
    min_booking_amount: float = 0.0,
    max_uses: Optional[int] = None,
    max_uses_per_user: int = 1,
    is_active: bool = True,
    hotel_id: Optional[int] = None,
    discount_category: DiscountCategory = DiscountCategory.PROMOTIONAL,
    min_advance_days: int = 0
) -> Coupon:
    clean_code = code.upper().strip()
    existing = get_coupon_by_code(db, clean_code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Coupon code '{clean_code}' already exists"
        )

    if expiry_date <= start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="expiry_date must be strictly after start_date"
        )

    if discount_type == DiscountType.PERCENTAGE and (discount_value <= 0 or discount_value > 100):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Percentage discount must be between 0.1% and 100%"
        )

    if hotel_id is not None:
        hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
        if not hotel:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Hotel with ID {hotel_id} not found")

    coupon = Coupon(
        code=clean_code,
        description=description,
        discount_type=discount_type,
        discount_value=discount_value,
        max_discount_amount=max_discount_amount,
        min_booking_amount=min_booking_amount,
        start_date=start_date,
        expiry_date=expiry_date,
        max_uses=max_uses,
        used_count=0,
        max_uses_per_user=max_uses_per_user,
        is_active=is_active,
        hotel_id=hotel_id,
        discount_category=discount_category,
        min_advance_days=min_advance_days
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


def update_coupon(
    db: Session,
    coupon: Coupon,
    update_data: Dict[str, Any]
) -> Coupon:
    for key, value in update_data.items():
        if value is not None and hasattr(coupon, key):
            setattr(coupon, key, value)
    
    if coupon.expiry_date <= coupon.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="expiry_date must be strictly after start_date"
        )

    coupon.updated_at = datetime.now()
    db.commit()
    db.refresh(coupon)
    return coupon


def delete_coupon(db: Session, coupon: Coupon) -> bool:
    db.delete(coupon)
    db.commit()
    return True


def validate_coupon_applicability(
    db: Session,
    code: str,
    hotel_id: int,
    booking_amount: float,
    user_id: Optional[int] = None,
    check_in_date: Optional[date] = None
) -> Tuple[bool, str, float, Optional[Coupon]]:
    """
    Validates coupon code against all business rules:
    - Active status
    - Current datetime within start_date and expiry_date
    - Hotel scope (platform-wide vs specific hotel)
    - Minimum booking amount threshold
    - Advance booking requirement (EARLY_BIRD)
    - Global max uses limit
    - Per-user max uses limit
    Returns: (is_valid, message, discount_amount, coupon_obj)
    """
    coupon = get_coupon_by_code(db, code)
    if not coupon:
        return False, f"Coupon code '{code}' does not exist", 0.0, None

    if not coupon.is_active:
        return False, "This coupon is currently inactive or disabled", 0.0, coupon

    now = datetime.now()
    if now < coupon.start_date:
        return False, f"Coupon is not valid until {coupon.start_date.strftime('%Y-%m-%d')}", 0.0, coupon

    if now > coupon.expiry_date:
        return False, f"Coupon expired on {coupon.expiry_date.strftime('%Y-%m-%d')}", 0.0, coupon

    # Scope check: Hotel specific
    if coupon.hotel_id is not None and coupon.hotel_id != hotel_id:
        return False, "This coupon is not valid for the selected hotel", 0.0, coupon

    # Minimum booking amount
    if booking_amount < coupon.min_booking_amount:
        return False, f"Booking amount (${booking_amount:.2f}) does not meet the minimum requirement of ${coupon.min_booking_amount:.2f}", 0.0, coupon

    # Global max uses
    if coupon.max_uses is not None and coupon.used_count >= coupon.max_uses:
        return False, "This coupon has reached its maximum global usage limit", 0.0, coupon

    # Per-user limit
    if user_id is not None:
        user_uses = db.query(CouponUsage).filter(
            CouponUsage.coupon_id == coupon.id,
            CouponUsage.user_id == user_id
        ).count()
        if user_uses >= coupon.max_uses_per_user:
            return False, f"You have reached the maximum allowed uses ({coupon.max_uses_per_user}) for this coupon", 0.0, coupon

    # Early bird / advance booking requirement
    if coupon.min_advance_days > 0 and check_in_date is not None:
        today = date.today()
        advance_days = (check_in_date - today).days
        if advance_days < coupon.min_advance_days:
            return False, f"Early-bird coupon requires booking at least {coupon.min_advance_days} days in advance (currently {advance_days} days)", 0.0, coupon

    # Calculate discount amount
    discount = 0.0
    if coupon.discount_type == DiscountType.PERCENTAGE:
        discount = (coupon.discount_value / 100.0) * booking_amount
        if coupon.max_discount_amount is not None:
            discount = min(discount, coupon.max_discount_amount)
    else:  # FIXED
        discount = min(coupon.discount_value, booking_amount)

    discount = round(discount, 2)
    return True, "Coupon applied successfully", discount, coupon


def apply_coupon_to_booking(
    db: Session,
    booking_id: int,
    code: str,
    user_id: int
) -> Dict[str, Any]:
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot apply coupon to another customer's booking")

    # Check if a coupon is already applied to this booking
    existing_usage = db.query(CouponUsage).filter(CouponUsage.booking_id == booking_id).first()
    if existing_usage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A coupon has already been redeemed for this reservation"
        )

    is_valid, msg, discount_amt, coupon = validate_coupon_applicability(
        db=db,
        code=code,
        hotel_id=booking.hotel_id,
        booking_amount=booking.base_amount,
        user_id=user_id,
        check_in_date=booking.check_in_date
    )

    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    # Record usage
    usage = CouponUsage(
        coupon_id=coupon.id,
        user_id=user_id,
        booking_id=booking.id,
        discount_amount=discount_amt
    )
    db.add(usage)

    # Update coupon stats
    coupon.used_count += 1

    # Recalculate booking total
    orig_total = booking.total_amount
    new_total = max(0.0, round(orig_total - discount_amt, 2))
    booking.total_amount = new_total

    # Log history
    history = BookingHistory(
        booking_id=booking.id,
        action="COUPON_APPLIED",
        old_status=booking.status.value,
        new_status=booking.status.value,
        changed_by_user_id=user_id,
        notes=f"Coupon '{coupon.code}' applied for a discount of ${discount_amt:.2f}. Total changed from ${orig_total:.2f} to ${new_total:.2f}."
    )
    db.add(history)
    db.commit()
    db.refresh(booking)

    return {
        "applied": True,
        "booking_id": booking.id,
        "coupon_code": coupon.code,
        "discount_amount": discount_amt,
        "original_total": orig_total,
        "new_total_amount": new_total,
        "message": f"Coupon {coupon.code} applied successfully"
    }


def list_coupons(
    db: Session,
    hotel_id: Optional[int] = None,
    only_active: bool = False,
    skip: int = 0,
    limit: int = 50
) -> List[Coupon]:
    query = db.query(Coupon)
    if hotel_id is not None:
        query = query.filter((Coupon.hotel_id == hotel_id) | (Coupon.hotel_id == None))
    if only_active:
        now = datetime.now()
        query = query.filter(Coupon.is_active == True, Coupon.start_date <= now, Coupon.expiry_date >= now)
    return query.order_by(Coupon.created_at.desc()).offset(skip).limit(limit).all()


def list_coupon_usages(
    db: Session,
    coupon_id: Optional[int] = None,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50
) -> List[CouponUsage]:
    query = db.query(CouponUsage)
    if coupon_id is not None:
        query = query.filter(CouponUsage.coupon_id == coupon_id)
    if user_id is not None:
        query = query.filter(CouponUsage.user_id == user_id)
    return query.order_by(CouponUsage.used_at.desc()).offset(skip).limit(limit).all()
