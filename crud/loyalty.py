import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from models import (
    LoyaltyAccount, LoyaltyLedger, LoyaltyTier,
    LoyaltyTransactionType, User, Booking, BookingStatus
)


TIER_CONFIG = {
    LoyaltyTier.BRONZE: {
        "min_points": 0,
        "multiplier": 1.0,
        "benefits": ["Standard Points (1 pt / $1)", "Member Exclusive Discount"]
    },
    LoyaltyTier.SILVER: {
        "min_points": 1000,
        "multiplier": 1.25,
        "benefits": ["25% Bonus Points", "Late Check-out until 1:00 PM", "Welcome Drink"]
    },
    LoyaltyTier.GOLD: {
        "min_points": 5000,
        "multiplier": 1.5,
        "benefits": ["50% Bonus Points", "Complimentary Breakfast", "Priority Early Check-in"]
    },
    LoyaltyTier.PLATINUM: {
        "min_points": 10000,
        "multiplier": 2.0,
        "benefits": ["Double Points (2.0x)", "Complimentary Room Upgrade", "VIP Concierge Line"]
    }
}


def get_or_create_loyalty_account(db: Session, user_id: int) -> LoyaltyAccount:
    """Retrieve existing loyalty account or initialize one with unique referral code."""
    account = db.query(LoyaltyAccount).filter(LoyaltyAccount.user_id == user_id).first()
    if not account:
        referral_code = f"STAY-{uuid.uuid4().hex[:8].upper()}"
        account = LoyaltyAccount(
            user_id=user_id,
            points_balance=0,
            lifetime_points=0,
            tier=LoyaltyTier.BRONZE,
            referral_code=referral_code
        )
        db.add(account)
        db.commit()
        db.refresh(account)
    return account


def recalculate_tier(account: LoyaltyAccount):
    """Update tier based on lifetime points earned."""
    lifetime = account.lifetime_points
    if lifetime >= TIER_CONFIG[LoyaltyTier.PLATINUM]["min_points"]:
        account.tier = LoyaltyTier.PLATINUM
    elif lifetime >= TIER_CONFIG[LoyaltyTier.GOLD]["min_points"]:
        account.tier = LoyaltyTier.GOLD
    elif lifetime >= TIER_CONFIG[LoyaltyTier.SILVER]["min_points"]:
        account.tier = LoyaltyTier.SILVER
    else:
        account.tier = LoyaltyTier.BRONZE


def award_booking_points(
    db: Session,
    user_id: int,
    booking_id: int,
    idempotency_key: Optional[str] = None
) -> Dict[str, Any]:
    """Award loyalty points for completed booking, preventing duplicate credits."""
    account = get_or_create_loyalty_account(db, user_id)

    # 1. Prevent duplicate credit by idempotency key or booking_id
    effective_key = idempotency_key or f"earn_booking_{booking_id}"
    duplicate = db.query(LoyaltyLedger).filter(
        LoyaltyLedger.idempotency_key == effective_key
    ).first()
    if duplicate:
        raise ValueError(f"Points for booking {booking_id} have already been awarded (Ledger ID: {duplicate.id}).")

    # 2. Fetch booking
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise ValueError(f"Booking {booking_id} not found")

    # 3. Calculate points based on amount and tier multiplier
    multiplier = TIER_CONFIG[account.tier]["multiplier"]
    base_points = int(booking.total_amount)
    awarded_points = max(1, int(base_points * multiplier))

    # 4. Update balance and lifetime
    account.points_balance += awarded_points
    account.lifetime_points += awarded_points
    recalculate_tier(account)

    # 5. Record ledger transaction
    ledger = LoyaltyLedger(
        account_id=account.id,
        user_id=user_id,
        booking_id=booking_id,
        transaction_type=LoyaltyTransactionType.EARNED_BOOKING,
        points=awarded_points,
        balance_after=account.points_balance,
        idempotency_key=effective_key,
        description=f"Earned {awarded_points} points for booking {booking.booking_reference} ({account.tier.value} {multiplier}x)"
    )
    db.add(ledger)
    db.commit()
    db.refresh(account)

    return {
        "booking_id": booking_id,
        "points_awarded": awarded_points,
        "new_balance": account.points_balance,
        "lifetime_points": account.lifetime_points,
        "tier": account.tier.value,
        "ledger_id": ledger.id
    }


def redeem_loyalty_points(
    db: Session,
    user_id: int,
    points_to_redeem: int,
    booking_id: Optional[int] = None
) -> Dict[str, Any]:
    """Redeem points for discount on booking (100 points = $1.00)."""
    if points_to_redeem <= 0:
        raise ValueError("Points to redeem must be greater than zero")

    account = get_or_create_loyalty_account(db, user_id)

    # Check sufficient balance
    if account.points_balance < points_to_redeem:
        raise ValueError(
            f"Insufficient points. Available: {account.points_balance}, Requested: {points_to_redeem}"
        )

    # Calculate discount
    discount_amount = round(points_to_redeem / 100.0, 2)
    account.points_balance -= points_to_redeem

    # Record ledger
    ledger = LoyaltyLedger(
        account_id=account.id,
        user_id=user_id,
        booking_id=booking_id,
        transaction_type=LoyaltyTransactionType.REDEEMED,
        points=-points_to_redeem,
        balance_after=account.points_balance,
        idempotency_key=f"redeem_{uuid.uuid4().hex[:12]}",
        description=f"Redeemed {points_to_redeem} points for ${discount_amount:.2f} discount"
    )
    db.add(ledger)
    db.commit()
    db.refresh(account)

    return {
        "points_redeemed": points_to_redeem,
        "discount_amount": discount_amount,
        "new_balance": account.points_balance,
        "message": f"Successfully redeemed {points_to_redeem} points for ${discount_amount:.2f} discount."
    }


def apply_referral_reward(
    db: Session,
    new_user_id: int,
    referral_code: str
) -> Dict[str, Any]:
    """Apply referral code: award welcome bonus to new user and reward to referrer."""
    new_user_acc = get_or_create_loyalty_account(db, new_user_id)
    if new_user_acc.referred_by_id:
        raise ValueError("User has already applied a referral code.")

    referrer_acc = db.query(LoyaltyAccount).filter(
        LoyaltyAccount.referral_code == referral_code.strip()
    ).first()
    if not referrer_acc:
        raise ValueError(f"Invalid referral code: '{referral_code}'")

    if referrer_acc.user_id == new_user_id:
        raise ValueError("Users cannot refer themselves.")

    new_user_acc.referred_by_id = referrer_acc.user_id

    # Award welcome bonus to new user (250 points)
    new_user_acc.points_balance += 250
    new_user_acc.lifetime_points += 250
    recalculate_tier(new_user_acc)

    new_ledger = LoyaltyLedger(
        account_id=new_user_acc.id,
        user_id=new_user_id,
        transaction_type=LoyaltyTransactionType.WELCOME_BONUS,
        points=250,
        balance_after=new_user_acc.points_balance,
        idempotency_key=f"welcome_ref_{new_user_id}",
        description="Welcome bonus for joining with referral code"
    )
    db.add(new_ledger)

    # Award referral bonus to referrer (500 points)
    referrer_acc.points_balance += 500
    referrer_acc.lifetime_points += 500
    recalculate_tier(referrer_acc)

    ref_ledger = LoyaltyLedger(
        account_id=referrer_acc.id,
        user_id=referrer_acc.user_id,
        transaction_type=LoyaltyTransactionType.REFERRAL_BONUS,
        points=500,
        balance_after=referrer_acc.points_balance,
        idempotency_key=f"referral_reward_{new_user_id}_{referrer_acc.user_id}",
        description="Referral reward for inviting a new member"
    )
    db.add(ref_ledger)
    db.commit()

    return {
        "status": "success",
        "welcome_bonus_points": 250,
        "new_balance": new_user_acc.points_balance,
        "referrer_user_id": referrer_acc.user_id
    }


def get_user_loyalty_ledger(db: Session, user_id: int) -> List[LoyaltyLedger]:
    """Retrieve complete points ledger history."""
    return db.query(LoyaltyLedger).filter(
        LoyaltyLedger.user_id == user_id
    ).order_by(LoyaltyLedger.created_at.desc()).all()


def get_tier_benefits_catalog() -> List[Dict[str, Any]]:
    """Retrieve full catalog of membership tiers and perks."""
    return [
        {
            "tier": tier.value,
            "min_points": data["min_points"],
            "multiplier": data["multiplier"],
            "benefits": data["benefits"]
        }
        for tier, data in TIER_CONFIG.items()
    ]
