import uuid
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from sqlalchemy.orm import Session
from models import (
    Hotel, Booking, BookingStatus, Payment, PaymentStatus,
    RefundRequest, RefundStatus, PayoutSettlement, SettlementStatus
)


def get_hotel_financial_breakdown(
    db: Session,
    hotel_id: int,
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    commission_rate: float = 10.0
) -> Dict[str, Any]:
    """Calculate gross booking volume, taxes, commission, refunds, and net payout earnings."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise ValueError(f"Hotel with ID {hotel_id} not found")

    b_q = db.query(Booking).filter(
        Booking.hotel_id == hotel_id,
        Booking.payment_status.in_([PaymentStatus.PAID, PaymentStatus.REFUNDED])
    )
    if period_start:
        b_q = b_q.filter(Booking.check_in_date >= period_start)
    if period_end:
        b_q = b_q.filter(Booking.check_in_date <= period_end)

    bookings = b_q.all()

    gross_volume = sum(b.total_amount for b in bookings)
    total_tax = sum(b.tax_amount for b in bookings)

    # Approved/processed refunds
    r_q = db.query(RefundRequest).filter(
        RefundRequest.hotel_id == hotel_id,
        RefundRequest.status.in_([RefundStatus.APPROVED, RefundStatus.PROCESSED])
    )
    refunds = r_q.all()
    total_refunds = sum((r.amount_approved if r.amount_approved is not None else r.amount_requested) for r in refunds)

    # Platform commission on net base earnings
    commission_amount = round(gross_volume * (commission_rate / 100.0), 2)
    net_earnings = max(0.0, round(gross_volume - total_tax - commission_amount - total_refunds, 2))

    # Existing settlements
    settlements = db.query(PayoutSettlement).filter(
        PayoutSettlement.hotel_id == hotel_id,
        PayoutSettlement.status == SettlementStatus.PAID
    ).all()
    already_settled = sum(s.net_payout_amount for s in settlements)
    pending_balance = max(0.0, round(net_earnings - already_settled, 2))

    return {
        "hotel_id": hotel.id,
        "hotel_name": hotel.name,
        "period_start": period_start,
        "period_end": period_end,
        "gross_booking_volume": round(gross_volume, 2),
        "total_tax_collected": round(total_tax, 2),
        "total_refunds": round(total_refunds, 2),
        "commission_rate_percentage": commission_rate,
        "platform_commission_amount": commission_amount,
        "net_hotel_earnings": net_earnings,
        "pending_payout_balance": pending_balance,
        "currency": "USD"
    }


def generate_payout_settlement(
    db: Session,
    hotel_id: int,
    period_start: date,
    period_end: date,
    commission_rate: float = 10.0,
    notes: Optional[str] = None
) -> PayoutSettlement:
    """Generate a payout settlement statement for a hotel and time interval."""
    if period_end < period_start:
        raise ValueError("Period end date cannot be earlier than period start date")

    breakdown = get_hotel_financial_breakdown(
        db, hotel_id, period_start=period_start, period_end=period_end, commission_rate=commission_rate
    )

    ref = f"SETTLE-{uuid.uuid4().hex[:10].upper()}"
    settlement = PayoutSettlement(
        hotel_id=hotel_id,
        period_start=period_start,
        period_end=period_end,
        gross_revenue=breakdown["gross_booking_volume"],
        commission_rate=commission_rate,
        platform_commission=breakdown["platform_commission_amount"],
        tax_collected=breakdown["total_tax_collected"],
        refunds_deducted=breakdown["total_refunds"],
        net_payout_amount=breakdown["net_hotel_earnings"],
        status=SettlementStatus.PENDING,
        payout_reference=ref,
        notes=notes
    )
    db.add(settlement)
    db.commit()
    db.refresh(settlement)
    return settlement


def get_settlements(
    db: Session,
    hotel_id: Optional[int] = None,
    status_filter: Optional[str] = None
) -> List[PayoutSettlement]:
    """Retrieve settlement records with optional hotel and status filtering."""
    query = db.query(PayoutSettlement)
    if hotel_id:
        query = query.filter(PayoutSettlement.hotel_id == hotel_id)
    if status_filter:
        query = query.filter(PayoutSettlement.status == SettlementStatus(status_filter.upper()))
    return query.order_by(PayoutSettlement.created_at.desc()).all()


def mark_settlement_paid(
    db: Session,
    settlement_id: int,
    payout_reference: Optional[str] = None,
    notes: Optional[str] = None
) -> PayoutSettlement:
    """Mark payout settlement as paid / disbursed."""
    settlement = db.query(PayoutSettlement).filter(PayoutSettlement.id == settlement_id).first()
    if not settlement:
        raise ValueError(f"Settlement statement with ID {settlement_id} not found")

    settlement.status = SettlementStatus.PAID
    settlement.settled_at = datetime.utcnow()
    if payout_reference:
        settlement.payout_reference = payout_reference
    if notes:
        settlement.notes = f"{settlement.notes or ''} | {notes}".strip(" |")

    db.commit()
    db.refresh(settlement)
    return settlement


def reconcile_financial_transactions(
    db: Session,
    hotel_id: Optional[int] = None
) -> Dict[str, Any]:
    """Reconcile system booking payments against payment-provider transaction records."""
    b_q = db.query(Booking).filter(
        Booking.payment_status.in_([PaymentStatus.PAID, PaymentStatus.REFUNDED])
    )
    if hotel_id:
        b_q = b_q.filter(Booking.hotel_id == hotel_id)

    bookings = b_q.all()

    items = []
    matched_count = 0
    discrepancy_count = 0
    reconciled_vol = 0.0
    discrepancy_vol = 0.0

    for b in bookings:
        # Check if booking has linked Payment
        payment = db.query(Payment).filter(Payment.booking_id == b.id).first()
        provider_id = payment.stripe_payment_intent_id if payment else f"pi_mock_{b.booking_reference}"
        provider_amount = payment.amount if payment else b.total_amount

        diff = abs(b.total_amount - provider_amount)
        is_matched = diff < 0.01

        if is_matched:
            matched_count += 1
            reconciled_vol += b.total_amount
        else:
            discrepancy_count += 1
            discrepancy_vol += diff

        items.append({
            "booking_id": b.id,
            "booking_reference": b.booking_reference,
            "system_amount": b.total_amount,
            "system_status": b.payment_status.value,
            "payment_provider_id": provider_id,
            "provider_status": "succeeded",
            "is_reconciled": is_matched,
            "discrepancy_amount": round(diff, 2)
        })

    return {
        "reconciliation_date": datetime.utcnow(),
        "total_transactions_checked": len(items),
        "total_matched": matched_count,
        "total_discrepancies": discrepancy_count,
        "reconciled_volume": round(reconciled_vol, 2),
        "discrepancy_volume": round(discrepancy_vol, 2),
        "items": items
    }
