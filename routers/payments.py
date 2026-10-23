import json
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from sqlalchemy.orm import Session
import stripe

from config import settings
from database import get_db
from models import Payment, PaymentRecordStatus, Booking, BookingStatus, PaymentStatus, User, UserRole
from schemas.payment import (
    CreatePaymentSessionRequest, ConfirmPaymentRequest,
    StripeCheckoutSessionResponse, PaymentResponse
)
from auth.dependencies import get_current_user, require_roles
from crud import payment as crud_payment, booking as crud_booking, invoice as crud_invoice
from utils.response import api_response

router = APIRouter(prefix="/payments", tags=["Module 15: Stripe Payment Integration"])


def _serialize_payment(p: Payment) -> dict:
    return {
        "id": p.id,
        "booking_id": p.booking_id,
        "payment_reference": p.payment_reference,
        "idempotency_key": p.idempotency_key,
        "stripe_session_id": p.stripe_session_id,
        "stripe_payment_intent_id": p.stripe_payment_intent_id,
        "amount": p.amount,
        "currency": p.currency,
        "status": p.status.value,
        "payment_method": p.payment_method,
        "receipt_url": p.receipt_url,
        "error_message": p.error_message,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None
    }


# ---------------------------------------------------------
# Module 15: Stripe Payment Integration
# ---------------------------------------------------------

@router.post("/create-checkout-session", summary="Create Stripe Checkout Session with idempotency")
def create_checkout_session(
    request: CreatePaymentSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = crud_booking.get_booking_by_id(db, request.booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    # Authorize: booking owner or admin
    if booking.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to pay for this booking")

    if booking.status == BookingStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot pay for a cancelled reservation")

    if booking.payment_status == PaymentStatus.PAID:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reservation is already paid in full")

    payment, session_meta = crud_payment.create_stripe_checkout_session(
        db=db,
        booking=booking,
        idempotency_key=request.idempotency_key
    )

    return api_response(
        success=True,
        message="Stripe checkout session initialized successfully",
        data={
            "session_id": session_meta["session_id"],
            "checkout_url": session_meta["checkout_url"],
            "payment_reference": payment.payment_reference,
            "idempotency_key": payment.idempotency_key,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status.value,
            "is_duplicate_prevented": session_meta.get("is_duplicate", False)
        },
        status_code=status.HTTP_201_CREATED if not session_meta.get("is_duplicate") else status.HTTP_200_OK
    )


@router.post("/confirm", summary="Confirm payment result manually or after client checkout")
def confirm_payment(
    request: ConfirmPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = crud_booking.get_booking_by_id(db, request.booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to confirm payment for this booking")

    # If idempotency key provided, check for existing successful payment
    if request.idempotency_key:
        existing = crud_payment.get_payment_by_idempotency_key(db, request.idempotency_key)
        if existing and existing.status == PaymentRecordStatus.SUCCEEDED:
            return api_response(
                success=True,
                message="Payment already confirmed (idempotent response)",
                data=_serialize_payment(existing)
            )

    payment = crud_payment.get_payment_by_booking_id(db, booking.id)
    if not payment:
        # Create a confirmed payment record directly
        ref = f"PAY-DIR-{booking.id}"
        payment = Payment(
            booking_id=booking.id,
            payment_reference=ref,
            idempotency_key=request.idempotency_key or f"dir_{booking.id}",
            amount=booking.total_amount,
            currency="usd",
            status=PaymentRecordStatus.PENDING,
            payment_method="card"
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

    intent_id = request.payment_intent_id or f"pi_test_{booking.id}"
    confirmed_payment = crud_payment.handle_payment_success(
        db=db,
        payment=payment,
        stripe_intent_id=intent_id,
        receipt_url=f"https://pay.stripe.com/receipts/{intent_id}"
    )

    return api_response(
        success=True,
        message="Payment confirmed successfully",
        data=_serialize_payment(confirmed_payment)
    )


@router.post("/webhook", summary="Stripe webhook listener for asynchronous event processing")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db)
):
    body = await request.body()
    event = None

    # If signing secret is set and real key is used, verify signature
    if settings.STRIPE_WEBHOOK_SECRET and stripe_signature and not settings.STRIPE_WEBHOOK_SECRET.startswith("whsec_staynest_sample"):
        try:
            event = stripe.Webhook.construct_event(
                payload=body,
                sig_header=stripe_signature,
                secret=settings.STRIPE_WEBHOOK_SECRET
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Webhook signature verification failed: {str(e)}")
    else:
        try:
            event = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")

    event_type = event.get("type", "")
    event_data = event.get("data", {}).get("object", {})

    if event_type in ["checkout.session.completed", "payment_intent.succeeded"]:
        session_id = event_data.get("id")
        client_ref = event_data.get("client_reference_id")

        payment = None
        if session_id:
            payment = db.query(Payment).filter(Payment.stripe_session_id == session_id).first()
        if not payment and client_ref:
            try:
                booking_id = int(client_ref)
                payment = crud_payment.get_payment_by_booking_id(db, booking_id)
            except ValueError:
                pass

        if payment and payment.status != PaymentRecordStatus.SUCCEEDED:
            crud_payment.handle_payment_success(
                db=db,
                payment=payment,
                stripe_intent_id=event_data.get("payment_intent") or event_data.get("id"),
                receipt_url=event_data.get("receipt_url")
            )

    elif event_type in ["payment_intent.payment_failed", "charge.failed"]:
        session_id = event_data.get("id")
        payment = db.query(Payment).filter(Payment.stripe_session_id == session_id).first()
        if payment:
            err = event_data.get("last_payment_error", {}).get("message", "Payment failed")
            crud_payment.handle_payment_failure(db, payment, error_message=err)

    return {"received": True, "event": event_type}


@router.get("/booking/{booking_id}", summary="Retrieve payment history and status for a reservation")
def get_booking_payment(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = crud_booking.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view payments for this booking")

    payments = db.query(Payment).filter(Payment.booking_id == booking_id).order_by(Payment.created_at.desc()).all()
    return api_response(
        success=True,
        message="Payment records retrieved successfully",
        data=[_serialize_payment(p) for p in payments]
    )


@router.get("/{payment_id}", summary="Retrieve payment by ID")
def get_payment_by_id(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    booking = payment.booking
    if booking and booking.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this payment")

    return api_response(
        success=True,
        message="Payment retrieved successfully",
        data=_serialize_payment(payment)
    )
