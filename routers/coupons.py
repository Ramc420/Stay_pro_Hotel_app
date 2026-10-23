from typing import Optional, List
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import Coupon, CouponUsage, User, UserRole
from schemas.coupon import (
    CouponCreate, CouponUpdate, CouponResponse,
    CouponValidateRequest, CouponValidateResponse,
    CouponApplyRequest, CouponApplyResponse,
    CouponUsageResponse
)
from auth.dependencies import get_current_user, require_roles, verify_hotel_access
from crud import coupon as crud_coupon
from utils.response import api_response

router = APIRouter(prefix="/coupons", tags=["Module 18: Coupon and Discount Management"])


def _serialize_coupon(c: Coupon) -> dict:
    return {
        "id": c.id,
        "code": c.code,
        "description": c.description,
        "discount_type": c.discount_type.value,
        "discount_value": c.discount_value,
        "max_discount_amount": c.max_discount_amount,
        "min_booking_amount": c.min_booking_amount,
        "start_date": c.start_date.isoformat(),
        "expiry_date": c.expiry_date.isoformat(),
        "max_uses": c.max_uses,
        "used_count": c.used_count,
        "max_uses_per_user": c.max_uses_per_user,
        "is_active": c.is_active,
        "hotel_id": c.hotel_id,
        "hotel_name": c.hotel.name if c.hotel else "Platform-wide (All Hotels)",
        "discount_category": c.discount_category.value,
        "min_advance_days": c.min_advance_days,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None
    }


def _verify_coupon_manage_permission(coupon: Coupon, user: User, db: Session):
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.HOTEL_OWNER and coupon.hotel_id and coupon.hotel.owner_id == user.id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to manage this coupon"
    )


# ---------------------------------------------------------
# Coupon Creation & Management (Admin / Hotel Owner)
# ---------------------------------------------------------

@router.post("", summary="Create a new fixed-value or percentage coupon (Admin / Hotel Owner)", status_code=status.HTTP_201_CREATED)
def create_coupon(
    request: CouponCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOTEL_OWNER)),
    db: Session = Depends(get_db)
):
    # Hotel Owner can only create coupons for their own hotel
    if current_user.role == UserRole.HOTEL_OWNER:
        if not request.hotel_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hotel owners must specify their hotel_id when creating a coupon"
            )
        verify_hotel_access(request.hotel_id, current_user, db)

    coupon = crud_coupon.create_coupon(
        db=db,
        code=request.code,
        discount_type=request.discount_type,
        discount_value=request.discount_value,
        start_date=request.start_date,
        expiry_date=request.expiry_date,
        description=request.description,
        max_discount_amount=request.max_discount_amount,
        min_booking_amount=request.min_booking_amount,
        max_uses=request.max_uses,
        max_uses_per_user=request.max_uses_per_user,
        is_active=request.is_active,
        hotel_id=request.hotel_id,
        discount_category=request.discount_category,
        min_advance_days=request.min_advance_days
    )

    return api_response(
        success=True,
        message=f"Coupon '{coupon.code}' created successfully",
        data=_serialize_coupon(coupon),
        status_code=status.HTTP_201_CREATED
    )


@router.get("", summary="List currently active promotional coupons (Public / Customer)")
def list_active_coupons(
    hotel_id: Optional[int] = Query(None, description="Filter by hotel ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    coupons = crud_coupon.list_coupons(db, hotel_id=hotel_id, only_active=True, skip=skip, limit=limit)
    return api_response(
        success=True,
        message="Active promotional coupons retrieved successfully",
        data=[_serialize_coupon(c) for c in coupons]
    )


@router.get("/admin", summary="List all coupons including inactive and expired (Admin / Hotel Owner)")
def list_all_coupons_admin(
    hotel_id: Optional[int] = Query(None, description="Filter by hotel ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOTEL_OWNER)),
    db: Session = Depends(get_db)
):
    target_hotel_id = hotel_id
    if current_user.role == UserRole.HOTEL_OWNER and not target_hotel_id:
        # Filter to owner's hotels
        owned_hotel_ids = [h.id for h in current_user.hotels]
        coupons = db.query(Coupon).filter(Coupon.hotel_id.in_(owned_hotel_ids)).offset(skip).limit(limit).all()
        return api_response(
            success=True,
            message="Coupons retrieved successfully",
            data=[_serialize_coupon(c) for c in coupons]
        )

    coupons = crud_coupon.list_coupons(db, hotel_id=target_hotel_id, only_active=False, skip=skip, limit=limit)
    return api_response(
        success=True,
        message="All coupons retrieved successfully",
        data=[_serialize_coupon(c) for c in coupons]
    )


@router.get("/{coupon_id}", summary="Retrieve coupon details by ID")
def get_coupon_by_id(
    coupon_id: int,
    db: Session = Depends(get_db)
):
    coupon = crud_coupon.get_coupon_by_id(db, coupon_id)
    if not coupon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found")

    return api_response(
        success=True,
        message="Coupon details retrieved successfully",
        data=_serialize_coupon(coupon)
    )


@router.put("/{coupon_id}", summary="Update coupon parameters (Admin / Hotel Owner)")
def update_coupon(
    coupon_id: int,
    request: CouponUpdate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOTEL_OWNER)),
    db: Session = Depends(get_db)
):
    coupon = crud_coupon.get_coupon_by_id(db, coupon_id)
    if not coupon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found")

    _verify_coupon_manage_permission(coupon, current_user, db)

    updated_coupon = crud_coupon.update_coupon(
        db=db,
        coupon=coupon,
        update_data=request.model_dump(exclude_unset=True)
    )

    return api_response(
        success=True,
        message=f"Coupon '{updated_coupon.code}' updated successfully",
        data=_serialize_coupon(updated_coupon)
    )


@router.delete("/{coupon_id}", summary="Delete coupon (Admin / Hotel Owner)")
def delete_coupon(
    coupon_id: int,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOTEL_OWNER)),
    db: Session = Depends(get_db)
):
    coupon = crud_coupon.get_coupon_by_id(db, coupon_id)
    if not coupon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found")

    _verify_coupon_manage_permission(coupon, current_user, db)
    crud_coupon.delete_coupon(db, coupon)

    return api_response(
        success=True,
        message=f"Coupon '{coupon.code}' deleted successfully"
    )


# ---------------------------------------------------------
# Coupon Validation & Redemption
# ---------------------------------------------------------

@router.post("/validate", summary="Validate coupon code against booking parameters and calculate discount")
def validate_coupon(
    request: CouponValidateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    is_valid, message, discount, coupon = crud_coupon.validate_coupon_applicability(
        db=db,
        code=request.code,
        hotel_id=request.hotel_id,
        booking_amount=request.booking_amount,
        user_id=current_user.id,
        check_in_date=request.check_in_date
    )

    final_amount = max(0.0, round(request.booking_amount - discount, 2))

    return api_response(
        success=is_valid,
        message=message,
        data={
            "valid": is_valid,
            "code": request.code.upper().strip(),
            "discount_type": coupon.discount_type.value if coupon else None,
            "discount_value": coupon.discount_value if coupon else None,
            "discount_amount": discount,
            "original_amount": request.booking_amount,
            "final_amount": final_amount,
            "message": message
        },
        status_code=status.HTTP_200_OK if is_valid else status.HTTP_400_BAD_REQUEST
    )


@router.post("/apply", summary="Redeem and apply coupon discount to a reservation")
def apply_coupon(
    request: CouponApplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = crud_coupon.apply_coupon_to_booking(
        db=db,
        booking_id=request.booking_id,
        code=request.code,
        user_id=current_user.id
    )

    return api_response(
        success=True,
        message=result["message"],
        data=result
    )


@router.get("/{coupon_id}/usages", summary="Retrieve usage history for a coupon (Admin / Hotel Owner)")
def get_coupon_usages(
    coupon_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOTEL_OWNER)),
    db: Session = Depends(get_db)
):
    coupon = crud_coupon.get_coupon_by_id(db, coupon_id)
    if not coupon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found")

    _verify_coupon_manage_permission(coupon, current_user, db)

    usages = crud_coupon.list_coupon_usages(db, coupon_id=coupon_id, skip=skip, limit=limit)

    return api_response(
        success=True,
        message="Coupon usage history retrieved successfully",
        data=[
            {
                "id": u.id,
                "coupon_id": u.coupon_id,
                "coupon_code": u.coupon.code if u.coupon else None,
                "user_id": u.user_id,
                "user_name": u.user.full_name if u.user else None,
                "booking_id": u.booking_id,
                "booking_reference": u.booking.booking_reference if u.booking else None,
                "discount_amount": u.discount_amount,
                "used_at": u.used_at.isoformat() if u.used_at else None
            }
            for u in usages
        ]
    )
