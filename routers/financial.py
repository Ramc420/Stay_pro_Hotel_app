"""
Module 46: Financial Management
Calculates hotel earnings, platform commissions, collected taxes, settlements, and payment reconciliation.
"""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.dependencies import verify_hotel_access, require_roles
from utils.response import api_response
from schemas.financial import (
    SettlementGenerateRequest, SettlementMarkPaidRequest
)
from crud import financial as crud_fin

router = APIRouter(prefix="/financial", tags=["Module 46: Financial Management"])


@router.get("/hotels/{hotel_id}/breakdown", summary="Retrieve hotel earnings, commissions, taxes, and pending payouts")
def get_breakdown(
    hotel_id: int,
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    commission_rate: float = 10.0,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    try:
        data = crud_fin.get_hotel_financial_breakdown(
            db=db,
            hotel_id=hotel_id,
            period_start=period_start,
            period_end=period_end,
            commission_rate=commission_rate
        )
        return api_response(
            success=True,
            message="Financial breakdown calculated",
            data=data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/settlements", summary="List payout settlements (Owner or Admin)")
def list_settlements(
    hotel_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    if current_user.role == UserRole.HOTEL_OWNER:
        if not hotel_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hotel ID required for owner")
        verify_hotel_access(hotel_id, current_user, db)

    settlements = crud_fin.get_settlements(db, hotel_id=hotel_id, status_filter=status)
    return api_response(
        success=True,
        message="Payout settlements retrieved",
        data=[
            {
                "id": s.id,
                "hotel_id": s.hotel_id,
                "hotel_name": s.hotel.name if s.hotel else None,
                "period_start": s.period_start.isoformat(),
                "period_end": s.period_end.isoformat(),
                "gross_revenue": s.gross_revenue,
                "commission_rate": s.commission_rate,
                "platform_commission": s.platform_commission,
                "tax_collected": s.tax_collected,
                "refunds_deducted": s.refunds_deducted,
                "net_payout_amount": s.net_payout_amount,
                "status": s.status.value,
                "payout_reference": s.payout_reference,
                "notes": s.notes,
                "settled_at": s.settled_at.isoformat() if s.settled_at else None,
                "created_at": s.created_at.isoformat()
            }
            for s in settlements
        ]
    )


@router.post("/settlements/generate", summary="Generate a payout settlement statement (Admin only)")
def generate_settlement(
    request: SettlementGenerateRequest,
    commission_rate: float = 10.0,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    try:
        settlement = crud_fin.generate_payout_settlement(
            db=db,
            hotel_id=request.hotel_id,
            period_start=request.period_start,
            period_end=request.period_end,
            commission_rate=commission_rate,
            notes=request.notes
        )
        return api_response(
            success=True,
            message=f"Settlement statement {settlement.payout_reference} generated successfully",
            data={
                "id": settlement.id,
                "hotel_id": settlement.hotel_id,
                "period_start": settlement.period_start.isoformat(),
                "period_end": settlement.period_end.isoformat(),
                "gross_revenue": settlement.gross_revenue,
                "net_payout_amount": settlement.net_payout_amount,
                "status": settlement.status.value,
                "payout_reference": settlement.payout_reference
            },
            status_code=status.HTTP_201_CREATED
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/settlements/{settlement_id}/mark-paid", summary="Mark payout settlement as settled/disbursed (Admin only)")
def mark_settlement_paid_endpoint(
    settlement_id: int,
    request: SettlementMarkPaidRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    try:
        settlement = crud_fin.mark_settlement_paid(
            db=db,
            settlement_id=settlement_id,
            payout_reference=request.payout_reference,
            notes=request.notes
        )
        return api_response(
            success=True,
            message=f"Settlement #{settlement_id} marked as PAID",
            data={
                "id": settlement.id,
                "status": settlement.status.value,
                "settled_at": settlement.settled_at.isoformat() if settlement.settled_at else None,
                "payout_reference": settlement.payout_reference
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reconciliation/run", summary="Reconcile platform booking payments against payment-gateway transactions (Admin only)")
def run_reconciliation(
    hotel_id: Optional[int] = None,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    report = crud_fin.reconcile_financial_transactions(db, hotel_id=hotel_id)
    return api_response(
        success=True,
        message="Payment reconciliation completed successfully",
        data=report
    )
