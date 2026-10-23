"""
Module 43: Loyalty and Rewards
Point accrual, redemptions, ledger tracking, membership tier benefits, and referral bonuses.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.dependencies import get_current_user, require_roles
from utils.response import api_response
from schemas.loyalty import (
    AwardBookingPointsRequest, RedeemPointsRequest, ApplyReferralRequest
)
from crud import loyalty as crud_loyalty

router = APIRouter(prefix="/loyalty", tags=["Module 43: Loyalty and Rewards"])


@router.get("/my-account", summary="Retrieve current user's loyalty status and benefits")
def get_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = crud_loyalty.get_or_create_loyalty_account(db, current_user.id)
    tier_info = crud_loyalty.TIER_CONFIG[account.tier]
    return api_response(
        success=True,
        message="Loyalty account retrieved",
        data={
            "id": account.id,
            "user_id": account.user_id,
            "user_name": current_user.full_name,
            "points_balance": account.points_balance,
            "lifetime_points": account.lifetime_points,
            "tier": account.tier.value,
            "tier_multiplier": tier_info["multiplier"],
            "tier_benefits": tier_info["benefits"],
            "referral_code": account.referral_code,
            "referred_by_id": account.referred_by_id,
            "created_at": account.created_at.isoformat()
        }
    )


@router.get("/ledger", summary="Retrieve points earning and redemption history")
def get_ledger(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entries = crud_loyalty.get_user_loyalty_ledger(db, current_user.id)
    return api_response(
        success=True,
        message="Loyalty ledger entries retrieved",
        data=[
            {
                "id": e.id,
                "user_id": e.user_id,
                "booking_id": e.booking_id,
                "transaction_type": e.transaction_type.value,
                "points": e.points,
                "balance_after": e.balance_after,
                "description": e.description,
                "idempotency_key": e.idempotency_key,
                "created_at": e.created_at.isoformat()
            }
            for e in entries
        ]
    )


@router.post("/award-booking", summary="Award loyalty points for completed booking")
def award_points(
    request: AwardBookingPointsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = crud_loyalty.award_booking_points(
            db=db,
            user_id=current_user.id,
            booking_id=request.booking_id,
            idempotency_key=request.idempotency_key
        )
        return api_response(
            success=True,
            message="Loyalty points awarded successfully",
            data=result,
            status_code=status.HTTP_201_CREATED
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/redeem", summary="Redeem loyalty points for booking discount")
def redeem_points(
    request: RedeemPointsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = crud_loyalty.redeem_loyalty_points(
            db=db,
            user_id=current_user.id,
            points_to_redeem=request.points,
            booking_id=request.booking_id
        )
        return api_response(
            success=True,
            message=result["message"],
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/referral", summary="Apply friend's referral code for bonus points")
def apply_referral(
    request: ApplyReferralRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = crud_loyalty.apply_referral_reward(
            db=db,
            new_user_id=current_user.id,
            referral_code=request.referral_code
        )
        return api_response(
            success=True,
            message="Referral code applied successfully. Bonus points credited!",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/tiers", summary="Retrieve all membership tiers and benefit guidelines")
def list_tiers():
    tiers = crud_loyalty.get_tier_benefits_catalog()
    return api_response(
        success=True,
        message="Loyalty tiers retrieved",
        data=tiers
    )
