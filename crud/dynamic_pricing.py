from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from models import (
    DynamicPricingRule, PricingRuleType, PriceAdjustmentType,
    Hotel, RoomType
)


def create_pricing_rule(
    db: Session,
    hotel_id: int,
    rule_name: str,
    rule_type: str,
    adjustment_type: str,
    adjustment_value: float,
    room_type_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    days_of_week: Optional[str] = None,
    priority: int = 1,
    is_active: bool = True
) -> DynamicPricingRule:
    """Create dynamic pricing rule with conflict prevention."""
    # Validate hotel
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise ValueError(f"Hotel with ID {hotel_id} not found")

    if room_type_id:
        room_type = db.query(RoomType).filter(RoomType.id == room_type_id).first()
        if not room_type or room_type.hotel_id != hotel_id:
            raise ValueError(f"Room type {room_type_id} does not belong to hotel {hotel_id}")

    # Conflict prevention: check for exact duplicate date ranges with same priority & rule type
    if start_date and end_date:
        conflicts = db.query(DynamicPricingRule).filter(
            DynamicPricingRule.hotel_id == hotel_id,
            DynamicPricingRule.room_type_id == room_type_id,
            DynamicPricingRule.rule_type == PricingRuleType(rule_type.upper()),
            DynamicPricingRule.priority == priority,
            DynamicPricingRule.is_active == True,
            DynamicPricingRule.start_date <= end_date,
            DynamicPricingRule.end_date >= start_date
        ).first()
        if conflicts:
            raise ValueError(
                f"Conflicting pricing rule '{conflicts.rule_name}' already exists for this date range with priority {priority}. Use a different priority."
            )

    rule = DynamicPricingRule(
        hotel_id=hotel_id,
        room_type_id=room_type_id,
        rule_name=rule_name,
        rule_type=PricingRuleType(rule_type.upper()),
        adjustment_type=PriceAdjustmentType(adjustment_type.upper()),
        adjustment_value=adjustment_value,
        start_date=start_date,
        end_date=end_date,
        days_of_week=days_of_week,
        priority=priority,
        is_active=is_active
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def get_pricing_rules(
    db: Session,
    hotel_id: int,
    active_only: bool = False
) -> List[DynamicPricingRule]:
    """Retrieve all dynamic pricing rules configured for a hotel."""
    query = db.query(DynamicPricingRule).filter(DynamicPricingRule.hotel_id == hotel_id)
    if active_only:
        query = query.filter(DynamicPricingRule.is_active == True)
    return query.order_by(DynamicPricingRule.priority.desc(), DynamicPricingRule.created_at.desc()).all()


def get_pricing_rule_by_id(db: Session, rule_id: int) -> Optional[DynamicPricingRule]:
    """Retrieve rule by primary key."""
    return db.query(DynamicPricingRule).filter(DynamicPricingRule.id == rule_id).first()


def update_pricing_rule(
    db: Session,
    rule_id: int,
    **updates
) -> Optional[DynamicPricingRule]:
    """Update rule parameters."""
    rule = get_pricing_rule_by_id(db, rule_id)
    if not rule:
        return None

    for key, value in updates.items():
        if value is not None and hasattr(rule, key):
            setattr(rule, key, value)

    db.commit()
    db.refresh(rule)
    return rule


def delete_pricing_rule(db: Session, rule_id: int) -> bool:
    """Delete a dynamic pricing rule."""
    rule = get_pricing_rule_by_id(db, rule_id)
    if not rule:
        return False
    db.delete(rule)
    db.commit()
    return True


def calculate_booking_price(
    db: Session,
    hotel_id: int,
    room_type_id: int,
    check_in: date,
    check_out: date
) -> Dict[str, Any]:
    """Calculate date-specific room pricing and final total consistently."""
    if check_out <= check_in:
        raise ValueError("Check-out date must be after check-in date")

    room_type = db.query(RoomType).filter(
        RoomType.id == room_type_id,
        RoomType.hotel_id == hotel_id
    ).first()
    if not room_type:
        raise ValueError(f"Room type {room_type_id} not found for hotel {hotel_id}")

    base_nightly_price = getattr(room_type, "base_price_per_night", getattr(room_type, "base_price", 100.0))
    rules = get_pricing_rules(db, hotel_id, active_only=True)

    daily_breakdown = []
    total_final = 0.0
    total_base = 0.0

    current = check_in
    while current < check_out:
        day_price = base_nightly_price
        applied_names = []
        weekday_idx = current.weekday()  # 0=Monday, 6=Sunday

        # Find matching rules for this date
        matching_rules = []
        for r in rules:
            # Check room type match
            if r.room_type_id is not None and r.room_type_id != room_type_id:
                continue

            # Check date range
            if r.start_date and current < r.start_date:
                continue
            if r.end_date and current > r.end_date:
                continue

            # Check day of week
            if r.days_of_week:
                allowed_days = [int(d.strip()) for d in r.days_of_week.split(",") if d.strip().isdigit()]
                if weekday_idx not in allowed_days:
                    continue

            matching_rules.append(r)

        # Sort rules by priority descending
        matching_rules.sort(key=lambda x: x.priority, reverse=True)

        for r in matching_rules:
            if r.adjustment_type == PriceAdjustmentType.FIXED_PRICE:
                day_price = r.adjustment_value
                applied_names.append(f"{r.rule_name} (Fixed ${r.adjustment_value:.2f})")
            elif r.adjustment_type == PriceAdjustmentType.PERCENTAGE_INCREASE:
                adj = base_nightly_price * (r.adjustment_value / 100.0)
                day_price += adj
                applied_names.append(f"{r.rule_name} (+{r.adjustment_value}%)")
            elif r.adjustment_type == PriceAdjustmentType.PERCENTAGE_DECREASE:
                adj = base_nightly_price * (r.adjustment_value / 100.0)
                day_price = max(0.0, day_price - adj)
                applied_names.append(f"{r.rule_name} (-{r.adjustment_value}%)")
            elif r.adjustment_type == PriceAdjustmentType.FIXED_ADJUSTMENT:
                day_price = max(0.0, day_price + r.adjustment_value)
                applied_names.append(f"{r.rule_name} ({'+' if r.adjustment_value >= 0 else ''}${r.adjustment_value:.2f})")

        day_price = round(day_price, 2)
        total_final += day_price
        total_base += base_nightly_price

        daily_breakdown.append({
            "date": current,
            "day_name": current.strftime("%A"),
            "base_price": round(base_nightly_price, 2),
            "final_price": round(day_price, 2),
            "applied_rules": applied_names
        })

        current += timedelta(days=1)

    nights = len(daily_breakdown)
    avg_rate = (total_final / nights) if nights > 0 else 0.0

    return {
        "hotel_id": hotel_id,
        "room_type_id": room_type_id,
        "room_type_name": room_type.name,
        "check_in_date": check_in,
        "check_out_date": check_out,
        "nights": nights,
        "base_total": round(total_base, 2),
        "final_total": round(total_final, 2),
        "total_adjustment": round(total_final - total_base, 2),
        "average_nightly_rate": round(avg_rate, 2),
        "daily_breakdown": daily_breakdown
    }
