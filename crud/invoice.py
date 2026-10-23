import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.invoice import Invoice, InvoiceStatus
from models.booking import Booking


def generate_invoice_number(db: Session) -> str:
    today_str = datetime.now().strftime("%Y%m%d")
    while True:
        suffix = uuid.uuid4().hex[:6].upper()
        num = f"INV-{today_str}-{suffix}"
        exists = db.query(Invoice).filter(Invoice.invoice_number == num).first()
        if not exists:
            return num


def generate_invoice_for_booking(
    db: Session,
    booking: Booking,
    tax_rate: float = 10.0,
    payment_id: Optional[int] = None
) -> Invoice:
    # Check if invoice already exists
    existing = db.query(Invoice).filter(Invoice.booking_id == booking.id).first()
    if existing:
        if payment_id and not existing.payment_id:
            existing.payment_id = payment_id
            existing.status = InvoiceStatus.PAID
            db.commit()
            db.refresh(existing)
        return existing

    num = generate_invoice_number(db)
    user = booking.user
    customer_name = user.full_name if user else "Valued Guest"
    customer_email = user.email if user else "guest@staynest.com"

    inv_status = InvoiceStatus.PAID if booking.payment_status.value == "PAID" else InvoiceStatus.ISSUED

    invoice = Invoice(
        booking_id=booking.id,
        invoice_number=num,
        user_id=booking.user_id,
        payment_id=payment_id,
        subtotal=booking.base_amount,
        tax_rate=tax_rate,
        tax_amount=booking.tax_amount,
        total_amount=booking.total_amount,
        status=inv_status,
        billing_name=customer_name,
        billing_email=customer_email,
        pdf_receipt_url=f"/api/v1/invoices/download/{num}.pdf"
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def get_invoice_by_id(db: Session, invoice_id: int) -> Optional[Invoice]:
    return db.query(Invoice).filter(Invoice.id == invoice_id).first()


def get_invoice_by_number(db: Session, invoice_number: str) -> Optional[Invoice]:
    return db.query(Invoice).filter(Invoice.invoice_number == invoice_number).first()


def get_invoice_by_booking_id(db: Session, booking_id: int) -> Optional[Invoice]:
    return db.query(Invoice).filter(Invoice.booking_id == booking_id).first()


def list_invoices_by_user(db: Session, user_id: int) -> List[Invoice]:
    return db.query(Invoice).filter(Invoice.user_id == user_id).order_by(Invoice.created_at.desc()).all()


def list_invoices_by_hotel(db: Session, hotel_id: int) -> List[Invoice]:
    return (
        db.query(Invoice)
        .join(Booking, Booking.id == Invoice.booking_id)
        .filter(Booking.hotel_id == hotel_id)
        .order_by(Invoice.created_at.desc())
        .all()
    )


def generate_printable_invoice_html(invoice: Invoice) -> str:
    booking = invoice.booking
    hotel = booking.hotel if booking else None
    hotel_name = hotel.name if hotel else "StayNest Hotel Partner"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Invoice {invoice.invoice_number}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; color: #1e293b; }}
            .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #e2e8f0; padding-bottom: 20px; }}
            .brand {{ font-size: 24px; font-weight: bold; color: #0284c7; }}
            .meta {{ text-align: right; }}
            .status {{ display: inline-block; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: bold; background: #dcfce7; color: #15803d; }}
            .table {{ width: 100%; border-collapse: collapse; margin-top: 30px; }}
            .table th, .table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
            .table th {{ background: #f8fafc; font-weight: 600; }}
            .totals {{ margin-top: 20px; text-align: right; }}
            .total-line {{ margin: 6px 0; }}
            .grand-total {{ font-size: 18px; font-weight: bold; color: #0f172a; border-top: 2px solid #cbd5e1; padding-top: 8px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <div class="brand">StayNest Pro</div>
                <p>Property: <strong>{hotel_name}</strong></p>
            </div>
            <div class="meta">
                <h2>INVOICE</h2>
                <p>Invoice #: <strong>{invoice.invoice_number}</strong></p>
                <p>Date: {invoice.created_at.strftime('%Y-%m-%d')}</p>
                <span class="status">{invoice.status.value}</span>
            </div>
        </div>

        <div style="margin-top: 24px;">
            <p><strong>Billed To:</strong> {invoice.billing_name} ({invoice.billing_email})</p>
            <p><strong>Booking Reference:</strong> {booking.booking_reference if booking else 'N/A'}</p>
            <p><strong>Stay Dates:</strong> {booking.check_in_date if booking else ''} to {booking.check_out_date if booking else ''} ({booking.total_nights if booking else 0} nights)</p>
        </div>

        <table class="table">
            <thead>
                <tr>
                    <th>Description</th>
                    <th>Nights</th>
                    <th>Nightly Rate</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Room Accommodation ({booking.room_type.name if booking and booking.room_type else 'Room'})</td>
                    <td>{booking.total_nights if booking else 1}</td>
                    <td>${booking.nightly_price if booking else 0:.2f}</td>
                    <td>${invoice.subtotal:.2f}</td>
                </tr>
            </tbody>
        </table>

        <div class="totals">
            <div class="total-line">Subtotal: <strong>${invoice.subtotal:.2f}</strong></div>
            <div class="total-line">Taxes & Fees ({invoice.tax_rate}%): <strong>${invoice.tax_amount:.2f}</strong></div>
            <div class="total-line grand-total">Total Amount: <strong>${invoice.total_amount:.2f}</strong></div>
        </div>
    </body>
    </html>
    """
    return html
