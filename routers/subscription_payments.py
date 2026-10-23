"""
Module 41: Hotel Subscription Payments
Stripe subscription billing, checkout sessions, plan upgrades/downgrades, and webhook processing.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.dependencies import verify_hotel_access, require_roles
from utils.response import api_response
from schemas.subscription_payment import (
    CheckoutSessionCreate, PlanUpgradeDowngradeRequest, WebhookEventRequest
)
from crud import subscription_payments as crud_sub_pay

router = APIRouter(prefix="/subscription-payments", tags=["Module 41: Hotel Subscription Payments"])


@router.post("/checkout-session", summary="Initiate Stripe subscription billing checkout session")
def create_checkout_session(
    request: CheckoutSessionCreate,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(request.hotel_id, current_user, db)
    try:
        data = crud_sub_pay.create_subscription_checkout_session(
            db=db,
            hotel_id=request.hotel_id,
            plan_id=request.plan_id,
            success_url=request.success_url,
            cancel_url=request.cancel_url
        )
        return api_response(
            success=True,
            message="Subscription checkout session initiated",
            data=data,
            status_code=status.HTTP_201_CREATED
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/webhook", summary="Process Stripe subscription webhooks")
def process_webhook(
    payload: WebhookEventRequest,
    db: Session = Depends(get_db)
):
    result = crud_sub_pay.process_subscription_webhook(
        db=db,
        event_type=payload.event_type,
        session_id=payload.session_id,
        subscription_id=payload.subscription_id,
        hotel_id=payload.hotel_id,
        plan_id=payload.plan_id,
        amount_paid=payload.amount_paid,
        metadata=payload.metadata
    )
    return api_response(
        success=True,
        message="Webhook processed successfully",
        data=result
    )


@router.post("/hotels/{hotel_id}/upgrade-downgrade", summary="Upgrade or downgrade hotel subscription tier")
def upgrade_downgrade_plan(
    hotel_id: int,
    request: PlanUpgradeDowngradeRequest,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    try:
        data = crud_sub_pay.upgrade_or_downgrade_subscription(
            db=db,
            hotel_id=hotel_id,
            new_plan_id=request.new_plan_id,
            immediate=request.immediate
        )
        return api_response(
            success=True,
            message=f"Subscription changed to {data['new_plan']} successfully",
            data=data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/hotels/{hotel_id}/history", summary="Retrieve subscription billing and payment history")
def get_payment_history(
    hotel_id: int,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    history = crud_sub_pay.get_hotel_payment_history(db, hotel_id)
    return api_response(
        success=True,
        message="Subscription payment history retrieved",
        data=[
            {
                "id": h.id,
                "hotel_id": h.hotel_id,
                "plan_id": h.plan_id,
                "plan_name": h.plan.name if h.plan else None,
                "amount": h.amount,
                "currency": h.currency,
                "billing_cycle": h.billing_cycle,
                "status": h.status.value,
                "stripe_session_id": h.stripe_session_id,
                "stripe_subscription_id": h.stripe_subscription_id,
                "invoice_url": h.invoice_url,
                "notes": h.notes,
                "paid_at": h.paid_at.isoformat() if h.paid_at else None,
                "created_at": h.created_at.isoformat()
            }
            for h in history
        ]
    )
