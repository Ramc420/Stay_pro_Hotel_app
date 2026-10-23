from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from models.invoice import InvoiceStatus


class InvoiceGenerateRequest(BaseModel):
    booking_id: Optional[int] = None
    tax_rate: Optional[float] = Field(default=10.0, ge=0.0, le=100.0)



class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    booking_id: int
    user_id: int
    payment_id: Optional[int] = None
    subtotal: float
    tax_rate: float
    tax_amount: float
    total_amount: float
    status: InvoiceStatus
    billing_name: str
    billing_email: str
    billing_address: Optional[str] = None
    pdf_receipt_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
