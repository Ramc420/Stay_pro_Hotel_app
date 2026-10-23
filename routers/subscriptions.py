
"""
Module 40: Hotel Subscription Plans
Manages hotel listing subscription tiers (FREE, BASIC, PREMIUM, ENTERPRISE), billing cycles, and feature access.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.dependencies import verify_hotel_access, require_roles
from utils.response import api_response
from schemas.subscription import SubscriptionPlanCreate, HotelSubscribeRequest
from crud import subscriptions as crud_sub

router = APIRouter(prefix="/subscriptions", tags=["Module 40: Hotel Subscription Plans"])


@router.get("/plans", summary="List available subscription plans")
def list_plans(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    plans = crud_sub.get_all_plans(db, active_only=active_only)
    return api_response(
        success=True,
        message="Subscription plans retrieved",
        data=[
            {
                "id": p.id,
                "name": p.name,
                "tier": p.tier.value,
                "billing_cycle": p.billing_cycle.value,
                "price": p.price,
                "max_rooms": p.max_rooms,
                "commission_rate": p.commission_rate,
                "has_analytics": p.has_analytics,
                "has_featured_badge": p.has_featured_badge,
                "has_priority_support": p.has_priority_support,
                "is_active": p.is_active
            }
            for p in plans
        ]
    )


@router.post("/plans", summary="Create subscription plan tier (Admin only)")
def create_plan(
    request: SubscriptionPlanCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    plan = crud_sub.create_subscription_plan(
        db=db,
        name=request.name,
        tier=request.tier,
        billing_cycle=request.billing_cycle,
        price=request.price,
        max_rooms=request.max_rooms,
        commission_rate=request.commission_rate,
        has_analytics=request.has_analytics,
        has_featured_badge=request.has_featured_badge,
        has_priority_support=request.has_priority_support
    )

    return api_response(
        success=True,
        message=f"Plan '{plan.name}' created successfully",
        data={"id": plan.id, "name": plan.name, "tier": plan.tier.value, "price": plan.price},
        status_code=status.HTTP_201_CREATED
    )


@router.post("/hotels/{hotel_id}/subscribe", summary="Subscribe hotel to a plan")
def subscribe_hotel(
    hotel_id: int,
    request: HotelSubscribeRequest,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)

    try:
        sub = crud_sub.subscribe_hotel(
            db=db,
            hotel_id=hotel_id,
            plan_id=request.plan_id,
            auto_renew=request.auto_renew
        )
        return api_response(
            success=True,
            message=f"Hotel subscribed to {sub.plan.name} successfully",
            data={
                "subscription_id": sub.id,
                "hotel_id": sub.hotel_id,
                "plan_id": sub.plan_id,
                "plan_name": sub.plan.name,
                "tier": sub.plan.tier.value,
                "price": sub.plan.price,
                "status": sub.status,
                "start_date": sub.start_date.isoformat(),
                "end_date": sub.end_date.isoformat(),
                "auto_renew": sub.auto_renew
            },
            status_code=status.HTTP_201_CREATED
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/hotels/{hotel_id}/current", summary="Get hotel's active subscription")
def get_current_subscription(
    hotel_id: int,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    sub = crud_sub.get_active_hotel_subscription(db, hotel_id)
    if not sub:
        return api_response(
            success=True,
            message="No active subscription found (Default: FREE tier)",
            data={"hotel_id": hotel_id, "status": "FREE", "has_analytics": False}
        )

    return api_response(
        success=True,
        message="Active subscription retrieved",
        data={
            "subscription_id": sub.id,
            "hotel_id": sub.hotel_id,
            "plan_name": sub.plan.name if sub.plan else "N/A",
            "tier": sub.plan.tier.value if sub.plan else "FREE",
            "price": sub.plan.price if sub.plan else 0.0,
            "status": sub.status,
            "start_date": sub.start_date.isoformat(),
            "end_date": sub.end_date.isoformat(),
            "auto_renew": sub.auto_renew,
            "benefits": {
                "max_rooms": sub.plan.max_rooms if sub.plan else 10,
                "commission_rate": sub.plan.commission_rate if sub.plan else 15.0,
                "has_analytics": sub.plan.has_analytics if sub.plan else False,
                "has_featured_badge": sub.plan.has_featured_badge if sub.plan else False
            }
        }
    )


@router.post("/hotels/{hotel_id}/cancel", summary="Cancel subscription auto-renewal")
def cancel_subscription(
    hotel_id: int,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    sub = crud_sub.cancel_hotel_subscription(db, hotel_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription to cancel")

    return api_response(
        success=True,
        message="Subscription auto-renewal has been cancelled",
        data={"hotel_id": hotel_id, "auto_renew": sub.auto_renew, "active_until": sub.end_date.isoformat()}
    )
