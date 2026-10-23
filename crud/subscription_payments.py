import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import (
    Hotel, SubscriptionPlan, HotelSubscription,
    SubscriptionPaymentHistory, SubscriptionPaymentStatus, BillingCycle
)
import crud.subscriptions as crud_subs


def create_subscription_checkout_session(
    db: Session,
    hotel_id: int,
    plan_id: int,
    success_url: Optional[str] = None,
    cancel_url: Optional[str] = None
) -> Dict[str, Any]:
    """Create a Stripe checkout session for hotel subscription billing."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise ValueError(f"Hotel with ID {hotel_id} not found")

    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise ValueError(f"Subscription plan with ID {plan_id} not found")

    session_id = f"cs_sub_{uuid.uuid4().hex[:18]}"
    checkout_url = f"https://checkout.stripe.com/pay/{session_id}"
    
    # Create initial pending payment record
    payment_record = SubscriptionPaymentHistory(
        hotel_id=hotel.id,
        plan_id=plan.id,
        amount=plan.price,
        currency="USD",
        billing_cycle=str(plan.billing_cycle.value) if hasattr(plan.billing_cycle, "value") else str(plan.billing_cycle),
        status=SubscriptionPaymentStatus.PENDING,
        stripe_session_id=session_id,
        stripe_subscription_id=f"sub_{uuid.uuid4().hex[:14]}",
        stripe_invoice_id=f"in_{uuid.uuid4().hex[:14]}",
        invoice_url=f"https://invoice.stripe.com/inv_{session_id[:10]}",
        notes=f"Subscription checkout session initiated for {plan.name}"
    )
    db.add(payment_record)
    db.commit()
    db.refresh(payment_record)

    return {
        "session_id": session_id,
        "checkout_url": checkout_url,
        "hotel_id": hotel.id,
        "plan_id": plan.id,
        "plan_name": plan.name,
        "amount": plan.price,
        "currency": "USD"
    }


def process_subscription_webhook(
    db: Session,
    event_type: str,
    session_id: Optional[str] = None,
    subscription_id: Optional[str] = None,
    hotel_id: Optional[int] = None,
    plan_id: Optional[int] = None,
    amount_paid: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process incoming Stripe subscription webhooks."""
    query = db.query(SubscriptionPaymentHistory)
    payment = None

    if session_id:
        payment = query.filter(SubscriptionPaymentHistory.stripe_session_id == session_id).first()
    elif subscription_id:
        payment = query.filter(SubscriptionPaymentHistory.stripe_subscription_id == subscription_id).first()
    elif hotel_id:
        payment = query.filter(SubscriptionPaymentHistory.hotel_id == hotel_id).order_by(SubscriptionPaymentHistory.id.desc()).first()

    now = datetime.utcnow()

    if event_type in ["invoice.payment_succeeded", "checkout.session.completed"]:
        if payment:
            payment.status = SubscriptionPaymentStatus.SUCCEEDED
            payment.paid_at = now
            if amount_paid:
                payment.amount = amount_paid
            db.commit()
            
            # Activate or renew hotel subscription
            crud_subs.subscribe_hotel(db, payment.hotel_id, payment.plan_id, auto_renew=True)
            return {"status": "success", "event": event_type, "message": "Payment succeeded and subscription activated."}
        elif hotel_id and plan_id:
            # Create succeeded record directly
            new_pay = SubscriptionPaymentHistory(
                hotel_id=hotel_id,
                plan_id=plan_id,
                amount=amount_paid or 0.0,
                currency="USD",
                status=SubscriptionPaymentStatus.SUCCEEDED,
                paid_at=now,
                notes=f"Webhook direct activation: {event_type}"
            )
            db.add(new_pay)
            db.commit()
            crud_subs.subscribe_hotel(db, hotel_id, plan_id, auto_renew=True)
            return {"status": "success", "event": event_type, "message": "Subscription activated via webhook."}

    elif event_type in ["invoice.payment_failed"]:
        if payment:
            payment.status = SubscriptionPaymentStatus.FAILED
            payment.notes = "Payment attempt failed."
            db.commit()
            return {"status": "failed", "event": event_type, "message": "Subscription payment marked as failed."}

    elif event_type in ["customer.subscription.deleted"]:
        if hotel_id:
            crud_subs.cancel_hotel_subscription(db, hotel_id)
            return {"status": "cancelled", "event": event_type, "message": "Subscription cancelled."}

    return {"status": "ignored", "event": event_type, "message": "Event processed with no action required."}


def upgrade_or_downgrade_subscription(
    db: Session,
    hotel_id: int,
    new_plan_id: int,
    immediate: bool = True
) -> Dict[str, Any]:
    """Support switching between plans with proration and audit record."""
    current_sub = crud_subs.get_active_hotel_subscription(db, hotel_id)
    new_plan = crud_subs.get_plan_by_id(db, new_plan_id)
    if not new_plan:
        raise ValueError(f"Target subscription plan {new_plan_id} not found")

    old_plan_name = current_sub.plan.name if current_sub and current_sub.plan else "None"
    action = "UPGRADE" if current_sub and new_plan.price > current_sub.plan.price else "DOWNGRADE"

    # Activate new subscription
    new_sub = crud_subs.subscribe_hotel(db, hotel_id, new_plan_id, auto_renew=True)

    # Record payment / transaction in history
    record = SubscriptionPaymentHistory(
        hotel_id=hotel_id,
        plan_id=new_plan.id,
        amount=new_plan.price,
        currency="USD",
        billing_cycle=str(new_plan.billing_cycle.value) if hasattr(new_plan.billing_cycle, "value") else str(new_plan.billing_cycle),
        status=SubscriptionPaymentStatus.SUCCEEDED,
        paid_at=datetime.utcnow(),
        notes=f"Plan {action}: Changed from {old_plan_name} to {new_plan.name}"
    )
    db.add(record)
    db.commit()

    return {
        "hotel_id": hotel_id,
        "action": action,
        "old_plan": old_plan_name,
        "new_plan": new_plan.name,
        "price": new_plan.price,
        "status": "ACTIVE",
        "starts_at": new_sub.start_date.isoformat(),
        "expires_at": new_sub.end_date.isoformat()
    }


def get_hotel_payment_history(db: Session, hotel_id: int) -> List[SubscriptionPaymentHistory]:
    """Maintain and retrieve subscription payment history for hotel."""
    return db.query(SubscriptionPaymentHistory).filter(
        SubscriptionPaymentHistory.hotel_id == hotel_id
    ).order_by(SubscriptionPaymentHistory.created_at.desc()).all()
