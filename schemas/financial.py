from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field


class FinancialBreakdownResponse(BaseModel):
    hotel_id: int
    hotel_name: str
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    gross_booking_volume: float
    total_tax_collected: float
    total_refunds: float
    commission_rate_percentage: float
    platform_commission_amount: float
    net_hotel_earnings: float
    pending_payout_balance: float
    currency: str = "USD"


class SettlementGenerateRequest(BaseModel):
    hotel_id: int
    period_start: date
    period_end: date
    notes: Optional[str] = None


class SettlementResponse(BaseModel):
    id: int
    hotel_id: int
    hotel_name: Optional[str] = None
    period_start: date
    period_end: date
    gross_revenue: float
    commission_rate: float
    platform_commission: float
    tax_collected: float
    refunds_deducted: float
    net_payout_amount: float
    status: str
    payout_reference: Optional[str] = None
    notes: Optional[str] = None
    settled_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SettlementMarkPaidRequest(BaseModel):
    payout_reference: Optional[str] = None
    notes: Optional[str] = None


class ReconciliationItem(BaseModel):
    booking_id: int
    booking_reference: str
    system_amount: float
    system_status: str
    payment_provider_id: Optional[str] = None
    provider_status: str
    is_reconciled: bool
    discrepancy_amount: float


class ReconciliationReport(BaseModel):
    reconciliation_date: datetime
    total_transactions_checked: int
    total_matched: int
    total_discrepancies: int
    reconciled_volume: float
    discrepancy_volume: float
    items: List[ReconciliationItem]
