from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Response, Body, status
from sqlalchemy.orm import Session


from database import get_db
from models import Invoice, InvoiceStatus, Booking, User, UserRole, HotelStaff
from schemas.invoice import InvoiceGenerateRequest, InvoiceResponse
from auth.dependencies import get_current_user, get_optional_current_user, require_roles, verify_hotel_access
from crud import invoice as crud_invoice, booking as crud_booking
from utils.response import api_response

router = APIRouter(prefix="/invoices", tags=["Module 16: Invoice & Receipt Management"])


def _serialize_invoice(inv: Invoice) -> dict:
    return {
        "id": inv.id,
        "invoice_number": inv.invoice_number,
        "booking_id": inv.booking_id,
        "booking_reference": inv.booking.booking_reference if inv.booking else None,
        "user_id": inv.user_id,
        "payment_id": inv.payment_id,
        "subtotal": inv.subtotal,
        "tax_rate": inv.tax_rate,
        "tax_amount": inv.tax_amount,
        "total_amount": inv.total_amount,
        "status": inv.status.value,
        "billing_name": inv.billing_name,
        "billing_email": inv.billing_email,
        "billing_address": inv.billing_address,
        "pdf_receipt_url": inv.pdf_receipt_url,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "updated_at": inv.updated_at.isoformat() if inv.updated_at else None
    }


def _verify_invoice_access(inv: Invoice, user: User, db: Session):
    if user.role == UserRole.ADMIN:
        return

    # Booking customer
    if inv.user_id == user.id:
        return

    # Hotel owner
    booking = inv.booking
    if booking and user.role == UserRole.HOTEL_OWNER and booking.hotel.owner_id == user.id:
        return

    # Hotel staff
    if booking and user.role == UserRole.HOTEL_STAFF:
        staff_entry = db.query(HotelStaff).filter(
            HotelStaff.hotel_id == booking.hotel_id,
            HotelStaff.user_id == user.id,
            HotelStaff.is_active == True
        ).first()
        if staff_entry:
            return

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to view or download this invoice")


# ---------------------------------------------------------
# Module 16: Invoice and Receipt Management
# ---------------------------------------------------------

@router.post("/generate/{booking_id}", summary="Generate an invoice and receipt for a booking")
def generate_invoice(
    booking_id: int,
    payload: Optional[InvoiceGenerateRequest] = Body(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    booking = crud_booking.get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    # Authorize: booking owner, hotel staff, hotel owner, or admin
    tax_rate = payload.tax_rate if payload and payload.tax_rate is not None else 10.0
    invoice = crud_invoice.generate_invoice_for_booking(db, booking, tax_rate=tax_rate)


    return api_response(
        success=True,
        message="Invoice generated successfully",
        data=_serialize_invoice(invoice),
        status_code=status.HTTP_201_CREATED
    )


@router.get("/my-invoices", summary="Retrieve all invoices for current logged-in customer")
def get_my_invoices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    invoices = crud_invoice.list_invoices_by_user(db, current_user.id)
    return api_response(
        success=True,
        message="Invoices retrieved successfully",
        data=[_serialize_invoice(i) for i in invoices]
    )


@router.get("/hotel/{hotel_id}", summary="Retrieve all invoices for a hotel (authorized)")
def get_hotel_invoices(
    hotel_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)

    invoices = crud_invoice.list_invoices_by_hotel(db, hotel_id)
    return api_response(
        success=True,
        message="Hotel invoices retrieved successfully",
        data=[_serialize_invoice(i) for i in invoices]
    )


@router.get("/booking/{booking_id}", summary="Retrieve invoice for a specific booking")
def get_invoice_by_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    inv = crud_invoice.get_invoice_by_booking_id(db, booking_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No invoice found for booking ID {booking_id}")

    _verify_invoice_access(inv, current_user, db)
    return api_response(
        success=True,
        message="Invoice retrieved successfully",
        data=_serialize_invoice(inv)
    )


@router.get("/{invoice_id}/download", summary="Download printable receipt and invoice (HTML/PDF)")
def download_invoice_by_id(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    inv = crud_invoice.get_invoice_by_id(db, invoice_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invoice with ID {invoice_id} not found")

    _verify_invoice_access(inv, current_user, db)

    html = crud_invoice.generate_printable_invoice_html(inv)
    return Response(
        content=html,
        media_type="text/html",
        headers={
            "Content-Disposition": f'inline; filename="invoice_{inv.invoice_number}.html"'
        }
    )


@router.get("/download/{invoice_number}", summary="Download printable receipt by invoice number")
def download_invoice_by_number(
    invoice_number: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    inv = crud_invoice.get_invoice_by_number(db, invoice_number)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invoice with number {invoice_number} not found")

    if current_user:
        _verify_invoice_access(inv, current_user, db)

    html = crud_invoice.generate_printable_invoice_html(inv)
    return Response(
        content=html,
        media_type="text/html",
        headers={
            "Content-Disposition": f'inline; filename="invoice_{inv.invoice_number}.html"'
        }
    )


@router.get("/{invoice_id}", summary="Retrieve invoice details by ID")
def get_invoice_by_id(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    inv = crud_invoice.get_invoice_by_id(db, invoice_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invoice with ID {invoice_id} not found")

    _verify_invoice_access(inv, current_user, db)
    return api_response(
        success=True,
        message="Invoice retrieved successfully",
        data=_serialize_invoice(inv)
    )
