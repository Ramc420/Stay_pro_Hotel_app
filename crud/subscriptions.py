from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import (
    SubscriptionPlan, HotelSubscription, SubscriptionTier, BillingCycle, Hotel
)


def seed_default_plans(db: Session):
    """Seed initial tiers: FREE, BASIC, PREMIUM, ENTERPRISE."""
    defaults = [
        {"name": "Starter Free", "tier": SubscriptionTier.FREE, "billing_cycle": BillingCycle.MONTHLY, "price": 0.0, "max_rooms": 5, "commission_rate": 18.0, "has_analytics": False, "has_featured_badge": False, "has_priority_support": False},
        {"name": "Standard Growth", "tier": SubscriptionTier.BASIC, "billing_cycle": BillingCycle.MONTHLY, "price": 49.0, "max_rooms": 20, "commission_rate": 14.0, "has_analytics": True, "has_featured_badge": False, "has_priority_support": False},
        {"name": "Premium Resort", "tier": SubscriptionTier.PREMIUM, "billing_cycle": BillingCycle.MONTHLY, "price": 129.0, "max_rooms": 60, "commission_rate": 10.0, "has_analytics": True, "has_featured_badge": True, "has_priority_support": True},
        {"name": "Enterprise Luxury", "tier": SubscriptionTier.ENTERPRISE, "billing_cycle": BillingCycle.YEARLY, "price": 999.0, "max_rooms": 200, "commission_rate": 7.5, "has_analytics": True, "has_featured_badge": True, "has_priority_support": True},
    ]

    for item in defaults:
        existing = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == item["name"]).first()
        if not existing:
            plan = SubscriptionPlan(**item, is_active=True)
            db.add(plan)
    db.commit()


def get_all_plans(db: Session, active_only: bool = True) -> List[SubscriptionPlan]:
    """Retrieve available subscription plans."""
    query = db.query(SubscriptionPlan)
    if active_only:
        query = query.filter(SubscriptionPlan.is_active == True)
    return query.order_by(SubscriptionPlan.price.asc()).all()


def get_plan_by_id(db: Session, plan_id: int) -> Optional[SubscriptionPlan]:
    """Retrieve plan by primary key."""
    return db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()


def create_subscription_plan(
    db: Session,
    name: str,
    tier: str,
    billing_cycle: str,
    price: float,
    max_rooms: int = 15,
    commission_rate: float = 12.0,
    has_analytics: bool = True,
    has_featured_badge: bool = False,
    has_priority_support: bool = False
) -> SubscriptionPlan:
    """Create a new subscription plan."""
    plan = SubscriptionPlan(
        name=name,
        tier=SubscriptionTier(tier.upper()),
        billing_cycle=BillingCycle(billing_cycle.upper()),
        price=price,
        max_rooms=max_rooms,
        commission_rate=commission_rate,
        has_analytics=has_analytics,
        has_featured_badge=has_featured_badge,
        has_priority_support=has_priority_support,
        is_active=True
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def subscribe_hotel(
    db: Session,
    hotel_id: int,
    plan_id: int,
    auto_renew: bool = True
) -> HotelSubscription:
    """Subscribe a hotel to a plan or upgrade its existing subscription."""
    plan = get_plan_by_id(db, plan_id)
    if not plan:
        raise ValueError(f"Subscription plan with ID {plan_id} not found")

    # Term duration based on billing cycle
    days = 365 if plan.billing_cycle == BillingCycle.YEARLY else 30
    now = datetime.utcnow()
    end_date = now + timedelta(days=days)

    # Cancel previous active subscription if present
    db.query(HotelSubscription).filter(
        HotelSubscription.hotel_id == hotel_id,
        HotelSubscription.status == "ACTIVE"
    ).update({"status": "SUPERSEDED"}, synchronize_session=False)

    subscription = HotelSubscription(
        hotel_id=hotel_id,
        plan_id=plan.id,
        status="ACTIVE",
        start_date=now,
        end_date=end_date,
        auto_renew=auto_renew
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


def get_active_hotel_subscription(db: Session, hotel_id: int) -> Optional[HotelSubscription]:
    """Retrieve currently active subscription for a hotel."""
    return db.query(HotelSubscription).filter(
        HotelSubscription.hotel_id == hotel_id,
        HotelSubscription.status == "ACTIVE"
    ).order_by(HotelSubscription.start_date.desc()).first()


def cancel_hotel_subscription(db: Session, hotel_id: int) -> Optional[HotelSubscription]:
    """Cancel subscription auto-renewal."""
    sub = get_active_hotel_subscription(db, hotel_id)
    if sub:
        sub.auto_renew = False
        db.commit()
        db.refresh(sub)
    return sub
