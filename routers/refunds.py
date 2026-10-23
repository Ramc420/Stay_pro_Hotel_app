from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import RefundRequest, RefundStatus, Booking, User, UserRole, HotelStaff
from schemas.refund import (
    CancellationPolicyQuoteRequest, CancellationPolicyQuoteResponse,
    RefundRequestCreate, RefundApprovalRequest, RefundRejectionRequest,
    RefundRequestResponse
)
from auth.dependencies import get_current_user, require_roles, verify_hotel_access
from crud import refund as crud_refund, booking as crud_booking
from utils.response import api_response

router = APIRouter(prefix="/refunds", tags=["Module 17: Cancellation and Refund Management"])


def _serialize_refund(r: RefundRequest) -> dict:
    return {
        "id": r.id,
        "booking_id": r.booking_id,
        "booking_reference": r.booking.booking_reference if r.booking else None,
        "user_id": r.user_id,
        "user_name": r.user.full_name if r.user else None,
        "hotel_id": r.hotel_id,
        "hotel_name": r.hotel.name if r.hotel else None,
        "payment_id": r.payment_id,
        "amount_requested": r.amount_requested,
        "amount_approved": r.amount_approved,
        "penalty_amount": r.penalty_amount,
        "currency": r.currency,
        "reason": r.reason,
        "status": r.status.value,
        "cancellation_policy_applied": r.cancellation_policy_applied,
        "admin_notes": r.admin_notes,
        "rejection_reason": r.rejection_reason,
        "stripe_refund_id": r.stripe_refund_id,
        "processed_at": r.processed_at.isoformat() if r.processed_at else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None
    }


def _verify_refund_manage_permission(refund: RefundRequest, user: User, db: Session):
    """Verifies that user is Admin, Hotel Owner, or assigned Hotel Staff for the hotel."""
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.HOTEL_OWNER and refund.hotel and refund.hotel.owner_id == user.id:
        return
    if user.role == UserRole.HOTEL_STAFF:
        staff_entry = db.query(HotelStaff).filter(
            HotelStaff.hotel_id == refund.hotel_id,
            HotelStaff.user_id == user.id,
            HotelStaff.is_active == True
        ).first()
        if staff_entry:
            return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to review or manage refunds for this hotel"
    )


# ---------------------------------------------------------
# Cancellation Policy & Quote
# ---------------------------------------------------------

@router.post("/policy-quote", summary="Calculate cancellation refund quote based on hotel policy")
@router.get("/policy-quote/{booking_id}", summary="Calculate cancellation refund quote (GET)")
def get_cancellation_policy_quote(
    booking_id: Optional[int] = None,
    request: Optional[CancellationPolicyQuoteRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_id = booking_id or (request.booking_id if request else None)
    if not target_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="booking_id is required")

    booking = crud_booking.get_booking_by_id(db, target_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    # Access check: owner, hotel manager, or admin
    if booking.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        if current_user.role != UserRole.HOTEL_OWNER or booking.hotel.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view cancellation quote for this booking")

    simulated_date = request.cancellation_date if request else None
    quote = crud_refund.calculate_cancellation_refund(db, booking, cancellation_date=simulated_date)

    return api_response(
        success=True,
        message="Cancellation refund quote calculated successfully",
        data=quote
    )


# ---------------------------------------------------------
# Submit Refund Request
# ---------------------------------------------------------

@router.post("/request", summary="Submit a refund request for a paid booking", status_code=status.HTTP_201_CREATED)
def submit_refund_request(
    request: RefundRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = crud_booking.get_booking_by_id(db, request.booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only request refunds for your own reservations")

    refund = crud_refund.submit_refund_request(
        db=db,
        booking_id=request.booking_id,
        user_id=current_user.id,
        reason=request.reason
    )

    return api_response(
        success=True,
        message="Refund request submitted successfully and is pending review",
        data=_serialize_refund(refund),
        status_code=status.HTTP_201_CREATED
    )


# ---------------------------------------------------------
# Query & List Refund Requests
# ---------------------------------------------------------

@router.get("/my-requests", summary="Retrieve all refund requests submitted by current customer")
def get_my_refund_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    requests = crud_refund.list_refund_requests(db, user_id=current_user.id)
    return api_response(
        success=True,
        message="Your refund requests retrieved successfully",
        data=[_serialize_refund(r) for r in requests]
    )


@router.get("/hotel/{hotel_id}", summary="Retrieve all refund requests for a specific hotel (Owner/Staff/Admin)")
def get_hotel_refund_requests(
    hotel_id: int,
    status_filter: Optional[RefundStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    requests = crud_refund.list_refund_requests(db, hotel_id=hotel_id, status_filter=status_filter, skip=skip, limit=limit)
    return api_response(
        success=True,
        message="Hotel refund requests retrieved successfully",
        data=[_serialize_refund(r) for r in requests]
    )


@router.get("", summary="List all platform refund requests (Admin only)")
def list_all_refund_requests(
    hotel_id: Optional[int] = None,
    status_filter: Optional[RefundStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    requests = crud_refund.list_refund_requests(db, hotel_id=hotel_id, status_filter=status_filter, skip=skip, limit=limit)
    return api_response(
        success=True,
        message="All refund requests retrieved successfully",
        data=[_serialize_refund(r) for r in requests]
    )


@router.get("/{refund_id}", summary="Retrieve refund request details by ID")
def get_refund_request_details(
    refund_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    refund = crud_refund.get_refund_by_id(db, refund_id)
    if not refund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refund request not found")

    # Verify access: request owner, hotel staff/owner, or admin
    if refund.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        _verify_refund_manage_permission(refund, current_user, db)

    return api_response(
        success=True,
        message="Refund request details retrieved successfully",
        data=_serialize_refund(refund)
    )


# ---------------------------------------------------------
# Review & Moderate Refund Requests (Approve / Reject)
# ---------------------------------------------------------

@router.post("/{refund_id}/approve", summary="Approve a pending refund request (Owner/Staff/Admin)")
def approve_refund(
    refund_id: int,
    request: Optional[RefundApprovalRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    refund = crud_refund.get_refund_by_id(db, refund_id)
    if not refund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refund request not found")

    _verify_refund_manage_permission(refund, current_user, db)

    amount_approved = request.amount_approved if request else None
    admin_notes = request.admin_notes if request else None

    approved_refund = crud_refund.approve_refund_request(
        db=db,
        refund_id=refund_id,
        current_user=current_user,
        amount_approved=amount_approved,
        admin_notes=admin_notes
    )

    return api_response(
        success=True,
        message=f"Refund request approved for ${approved_refund.amount_approved:.2f}",
        data=_serialize_refund(approved_refund)
    )


@router.post("/{refund_id}/reject", summary="Reject a pending refund request (Owner/Staff/Admin)")
def reject_refund(
    refund_id: int,
    request: RefundRejectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    refund = crud_refund.get_refund_by_id(db, refund_id)
    if not refund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refund request not found")

    _verify_refund_manage_permission(refund, current_user, db)

    rejected_refund = crud_refund.reject_refund_request(
        db=db,
        refund_id=refund_id,
        current_user=current_user,
        rejection_reason=request.rejection_reason
    )

    return api_response(
        success=True,
        message="Refund request rejected successfully",
        data=_serialize_refund(rejected_refund)
    )


# ---------------------------------------------------------
# Process Stripe Refund
# ---------------------------------------------------------

@router.post("/{refund_id}/process", summary="Process approved refund through Stripe payment gateway")
def process_refund_via_stripe(
    refund_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    refund = crud_refund.get_refund_by_id(db, refund_id)
    if not refund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refund request not found")

    _verify_refund_manage_permission(refund, current_user, db)

    processed_refund = crud_refund.process_stripe_refund(
        db=db,
        refund_id=refund_id,
        current_user=current_user
    )

    return api_response(
        success=True,
        message=f"Refund successfully processed via Stripe ({processed_refund.stripe_refund_id})",
        data=_serialize_refund(processed_refund)
    )
