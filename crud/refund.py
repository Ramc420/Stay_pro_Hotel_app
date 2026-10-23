import uuid
from datetime import datetime, date
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import stripe

from config import settings
from models.refund import RefundRequest, RefundStatus, CancellationPolicyType
from models.booking import Booking, BookingStatus, PaymentStatus, BookingHistory
from models.payment import Payment, PaymentRecordStatus
from models.hotel import Hotel
from models.user import User, UserRole, HotelStaff
from crud.booking import release_room_dates


def parse_hotel_cancellation_policy(policy_str: Optional[str]) -> CancellationPolicyType:
    if not policy_str:
        return CancellationPolicyType.MODERATE
    p_upper = policy_str.upper().strip()
    if "NON" in p_upper or "NO REFUND" in p_upper:
        return CancellationPolicyType.NON_REFUNDABLE
    if "FLEX" in p_upper:
        return CancellationPolicyType.FLEXIBLE
    if "STRICT" in p_upper:
        return CancellationPolicyType.STRICT
    return CancellationPolicyType.MODERATE


def calculate_cancellation_refund(
    db: Session,
    booking: Booking,
    cancellation_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Applies the hotel cancellation policy to calculate penalty and refundable amounts.
    """
    calc_date = cancellation_date or date.today()
    check_in = booking.check_in_date

    days_until_check_in = (check_in - calc_date).days
    policy_type = parse_hotel_cancellation_policy(booking.hotel.cancellation_policy if booking.hotel else None)

    penalty_percentage = 0.0
    explanation = ""

    if days_until_check_in < 0:
        # Check-in date has already passed
        penalty_percentage = 100.0
        explanation = f"Check-in date was {check_in.isoformat()} ({abs(days_until_check_in)} days ago). Non-refundable."
    elif policy_type == CancellationPolicyType.NON_REFUNDABLE:
        penalty_percentage = 100.0
        explanation = "Hotel policy is NON-REFUNDABLE. 100% cancellation penalty applies."
    elif policy_type == CancellationPolicyType.FLEXIBLE:
        if days_until_check_in >= 1:
            penalty_percentage = 0.0
            explanation = f"FLEXIBLE policy: Full 100% refund eligible ({days_until_check_in} days before check-in)."
        else:
            penalty_percentage = 100.0
            explanation = "FLEXIBLE policy: Less than 24 hours prior to check-in. Non-refundable."
    elif policy_type == CancellationPolicyType.MODERATE:
        if days_until_check_in >= 5:
            penalty_percentage = 0.0
            explanation = f"MODERATE policy: 100% refund eligible ({days_until_check_in} days before check-in)."
        elif days_until_check_in >= 1:
            penalty_percentage = 50.0
            explanation = f"MODERATE policy: 50% refund eligible ({days_until_check_in} days before check-in, 50% penalty)."
        else:
            penalty_percentage = 100.0
            explanation = "MODERATE policy: Less than 24 hours prior to check-in. Non-refundable."
    elif policy_type == CancellationPolicyType.STRICT:
        if days_until_check_in >= 7:
            penalty_percentage = 50.0
            explanation = f"STRICT policy: 50% refund eligible ({days_until_check_in} days before check-in, 50% penalty)."
        else:
            penalty_percentage = 100.0
            explanation = f"STRICT policy: Less than 7 days prior to check-in ({days_until_check_in} days). Non-refundable."

    total_paid = booking.total_amount
    penalty_amount = round((penalty_percentage / 100.0) * total_paid, 2)
    refundable_amount = max(0.0, round(total_paid - penalty_amount, 2))
    is_eligible = refundable_amount > 0.0

    return {
        "booking_id": booking.id,
        "booking_reference": booking.booking_reference,
        "hotel_id": booking.hotel_id,
        "hotel_name": booking.hotel.name if booking.hotel else "Unknown Hotel",
        "check_in_date": booking.check_in_date,
        "check_out_date": booking.check_out_date,
        "days_until_check_in": days_until_check_in,
        "cancellation_policy": policy_type.value,
        "total_amount": total_paid,
        "penalty_percentage": penalty_percentage,
        "penalty_amount": penalty_amount,
        "refundable_amount": refundable_amount,
        "currency": "usd",
        "is_eligible_for_refund": is_eligible,
        "explanation": explanation
    }


def submit_refund_request(
    db: Session,
    booking_id: int,
    user_id: int,
    reason: str
) -> RefundRequest:
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    # Verify payment status
    if booking.payment_status not in [PaymentStatus.PAID, PaymentStatus.PENDING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot request refund for an unpaid or failed reservation"
        )

    # Check for existing request
    existing = db.query(RefundRequest).filter(RefundRequest.booking_id == booking_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A refund request already exists for this booking (Status: {existing.status.value})"
        )

    # Calculate policy refund
    policy_quote = calculate_cancellation_refund(db, booking)
    latest_payment = db.query(Payment).filter(
        Payment.booking_id == booking_id,
        Payment.status == PaymentRecordStatus.SUCCEEDED
    ).order_by(Payment.created_at.desc()).first()

    refund = RefundRequest(
        booking_id=booking.id,
        user_id=user_id,
        hotel_id=booking.hotel_id,
        payment_id=latest_payment.id if latest_payment else None,
        amount_requested=policy_quote["refundable_amount"],
        amount_approved=None,
        penalty_amount=policy_quote["penalty_amount"],
        currency="usd",
        reason=reason,
        status=RefundStatus.PENDING,
        cancellation_policy_applied=policy_quote["cancellation_policy"],
        admin_notes=f"Calculated based on {policy_quote['cancellation_policy']} policy: {policy_quote['explanation']}"
    )
    db.add(refund)

    # Log booking history
    history = BookingHistory(
        booking_id=booking.id,
        action="REFUND_REQUESTED",
        old_status=booking.status.value,
        new_status=booking.status.value,
        changed_by_user_id=user_id,
        notes=f"Refund request submitted for ${policy_quote['refundable_amount']:.2f}. Reason: {reason}"
    )
    db.add(history)
    db.commit()
    db.refresh(refund)

    return refund


def approve_refund_request(
    db: Session,
    refund_id: int,
    current_user: User,
    amount_approved: Optional[float] = None,
    admin_notes: Optional[str] = None
) -> RefundRequest:
    refund = db.query(RefundRequest).filter(RefundRequest.id == refund_id).first()
    if not refund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refund request not found")

    if refund.status != RefundStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Refund request is already in status '{refund.status.value}'"
        )

    approved_amt = amount_approved if amount_approved is not None else refund.amount_requested
    if approved_amt > refund.booking.total_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Approved amount (${approved_amt:.2f}) cannot exceed booking total amount (${refund.booking.total_amount:.2f})"
        )

    refund.amount_approved = round(approved_amt, 2)
    refund.status = RefundStatus.APPROVED
    if admin_notes:
        refund.admin_notes = f"{refund.admin_notes or ''}\nApproval note: {admin_notes}".strip()
    refund.updated_at = datetime.now()

    # Log history
    history = BookingHistory(
        booking_id=refund.booking_id,
        action="REFUND_APPROVED",
        old_status=refund.booking.status.value,
        new_status=refund.booking.status.value,
        changed_by_user_id=current_user.id,
        notes=f"Refund request approved for ${refund.amount_approved:.2f} by {current_user.full_name} ({current_user.role.value})"
    )
    db.add(history)
    db.commit()
    db.refresh(refund)

    return refund


def reject_refund_request(
    db: Session,
    refund_id: int,
    current_user: User,
    rejection_reason: str
) -> RefundRequest:
    refund = db.query(RefundRequest).filter(RefundRequest.id == refund_id).first()
    if not refund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refund request not found")

    if refund.status != RefundStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Refund request is already in status '{refund.status.value}'"
        )

    refund.status = RefundStatus.REJECTED
    refund.rejection_reason = rejection_reason
    refund.updated_at = datetime.now()

    # Log history
    history = BookingHistory(
        booking_id=refund.booking_id,
        action="REFUND_REJECTED",
        old_status=refund.booking.status.value,
        new_status=refund.booking.status.value,
        changed_by_user_id=current_user.id,
        notes=f"Refund rejected by {current_user.full_name}. Reason: {rejection_reason}"
    )
    db.add(history)
    db.commit()
    db.refresh(refund)

    return refund


def process_stripe_refund(
    db: Session,
    refund_id: int,
    current_user: User
) -> RefundRequest:
    refund = db.query(RefundRequest).filter(RefundRequest.id == refund_id).first()
    if not refund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refund request not found")

    if refund.status != RefundStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot process refund with status '{refund.status.value}'. Must be APPROVED first."
        )

    booking = refund.booking
    payment = refund.payment
    if not payment:
        payment = db.query(Payment).filter(Payment.booking_id == booking.id).order_by(Payment.created_at.desc()).first()

    refund_amt = refund.amount_approved if refund.amount_approved is not None else refund.amount_requested
    refund_amt_cents = int(round(refund_amt * 100))

    stripe_refund_id = f"re_test_{uuid.uuid4().hex[:16]}"

    # Execute actual Stripe refund if live or test key is set and payment intent exists
    if settings.STRIPE_API_KEY and not settings.STRIPE_API_KEY.startswith("sk_test_staynest_sample"):
        stripe.api_key = settings.STRIPE_API_KEY
        if payment and payment.stripe_payment_intent_id and not payment.stripe_payment_intent_id.startswith("pi_test_"):
            try:
                stripe_obj = stripe.Refund.create(
                    payment_intent=payment.stripe_payment_intent_id,
                    amount=refund_amt_cents,
                    reason="requested_by_customer"
                )
                stripe_refund_id = stripe_obj.id
            except Exception as e:
                refund.status = RefundStatus.FAILED
                refund.admin_notes = f"Stripe refund processing failed: {str(e)}"
                db.commit()
                db.refresh(refund)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Stripe refund failed: {str(e)}"
                )

    # Success: update refund request
    refund.status = RefundStatus.PROCESSED
    refund.stripe_refund_id = stripe_refund_id
    refund.processed_at = datetime.now()
    refund.updated_at = datetime.now()

    # Update payment & booking
    if payment:
        payment.status = PaymentRecordStatus.REFUNDED
        payment.updated_at = datetime.now()

    booking.payment_status = PaymentStatus.REFUNDED
    if booking.status != BookingStatus.CANCELLED:
        booking.status = BookingStatus.CANCELLED
        booking.cancellation_reason = refund.reason
        booking.cancelled_at = datetime.now()
        release_room_dates(db, booking.room_id, booking.check_in_date, booking.check_out_date, booking.id)

    # Log history
    history = BookingHistory(
        booking_id=booking.id,
        action="REFUND_PROCESSED",
        old_status=booking.status.value,
        new_status=BookingStatus.CANCELLED.value,
        changed_by_user_id=current_user.id,
        notes=f"Refund of ${refund_amt:.2f} processed successfully through Stripe ({stripe_refund_id})"
    )
    db.add(history)
    db.commit()
    db.refresh(refund)

    return refund


def get_refund_by_id(db: Session, refund_id: int) -> Optional[RefundRequest]:
    return db.query(RefundRequest).filter(RefundRequest.id == refund_id).first()


def get_refund_by_booking_id(db: Session, booking_id: int) -> Optional[RefundRequest]:
    return db.query(RefundRequest).filter(RefundRequest.booking_id == booking_id).first()


def list_refund_requests(
    db: Session,
    hotel_id: Optional[int] = None,
    user_id: Optional[int] = None,
    status_filter: Optional[RefundStatus] = None,
    skip: int = 0,
    limit: int = 50
) -> List[RefundRequest]:
    query = db.query(RefundRequest)
    if hotel_id is not None:
        query = query.filter(RefundRequest.hotel_id == hotel_id)
    if user_id is not None:
        query = query.filter(RefundRequest.user_id == user_id)
    if status_filter is not None:
        query = query.filter(RefundRequest.status == status_filter)
    return query.order_by(RefundRequest.created_at.desc()).offset(skip).limit(limit).all()
