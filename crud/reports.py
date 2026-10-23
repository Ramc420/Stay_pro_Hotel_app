import io
import csv
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from sqlalchemy.orm import Session
from models import Booking, Payment, Hotel, User, UserRole


def generate_report_dataset(
    db: Session,
    report_type: str,
    hotel_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """Generate tabular data for a specified report type."""
    rep = report_type.lower()

    if rep == "bookings":
        query = db.query(Booking)
        if hotel_id:
            query = query.filter(Booking.hotel_id == hotel_id)
        if start_date:
            query = query.filter(Booking.check_in_date >= start_date)
        if end_date:
            query = query.filter(Booking.check_out_date <= end_date)
        bookings = query.order_by(Booking.created_at.desc()).all()

        return [
            {
                "Booking Reference": b.booking_reference,
                "Hotel": b.hotel.name if b.hotel else "",
                "Guest Name": b.user.full_name if b.user else "",
                "Guest Email": b.user.email if b.user else "",
                "Check-In": b.check_in_date.isoformat(),
                "Check-Out": b.check_out_date.isoformat(),
                "Nights": b.total_nights,
                "Total Amount": f"${b.total_amount:.2f}",
                "Status": b.status.value,
                "Payment": b.payment_status.value
            }
            for b in bookings
        ]

    elif rep == "payments":
        query = db.query(Payment)
        if start_date:
            query = query.filter(Payment.created_at >= start_date)
        if end_date:
            query = query.filter(Payment.created_at <= end_date)
        payments = query.order_by(Payment.created_at.desc()).all()

        return [
            {
                "Payment ID": p.id,
                "Booking ID": p.booking_id,
                "Customer": p.booking.user.full_name if p.booking and p.booking.user else "",
                "Amount": f"${p.amount:.2f}",
                "Currency": p.currency,
                "Method": p.payment_method,
                "Status": p.status.value,
                "Transaction Ref": p.stripe_payment_intent_id or "N/A",
                "Date": p.created_at.strftime("%Y-%m-%d %H:%M")
            }
            for p in payments
        ]

    elif rep == "hotels":
        hotels = db.query(Hotel).order_by(Hotel.name).all()
        return [
            {
                "Hotel ID": h.id,
                "Hotel Name": h.name,
                "Property Type": h.property_type,
                "City": h.city,
                "Country": h.country,
                "Rating": f"{h.star_rating}*",
                "Status": h.status.value,
                "Approved": "Yes" if h.is_approved else "No",
                "Total Rooms": len(h.rooms)
            }
            for h in hotels
        ]

    elif rep == "customers":
        customers = db.query(User).filter(User.role == UserRole.CUSTOMER).all()
        return [
            {
                "Customer ID": c.id,
                "Full Name": c.full_name,
                "Email": c.email,
                "Phone": c.phone_number or "N/A",
                "Active": "Yes" if c.is_active else "No",
                "Registered At": c.created_at.strftime("%Y-%m-%d")
            }
            for c in customers
        ]

    # Default fallback
    return []


def export_as_csv(dataset: List[Dict[str, Any]]) -> str:
    """Convert dataset rows to CSV format string."""
    if not dataset:
        return "No data available"

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=dataset[0].keys())
    writer.writeheader()
    writer.writerows(dataset)
    return output.getvalue()


def export_as_html_report(report_title: str, dataset: List[Dict[str, Any]]) -> str:
    """Generate printable HTML report with print-to-PDF styles."""
    if not dataset:
        return "<html><body><h2>No records found</h2></body></html>"

    headers = list(dataset[0].keys())
    header_html = "".join(f"<th style='padding:10px; border:1px solid #ddd; background:#f4f6f8;'>{h}</th>" for h in headers)

    rows_html = ""
    for row in dataset:
        cols = "".join(f"<td style='padding:8px; border:1px solid #ddd;'>{row.get(h, '')}</td>" for h in headers)
        rows_html += f"<tr>{cols}</tr>"

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{report_title}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 30px; }}
    h1 {{ color: #2c3e50; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    @media print {{
      body {{ margin: 0; }}
      button {{ display: none; }}
    }}
  </style>
</head>
<body>
  <h1>StayNest Pro - {report_title.title()} Report</h1>
  <p>Generated on {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")} | Total Records: {len(dataset)}</p>
  <button onclick="window.print()" style="padding:8px 16px; background:#007bff; color:white; border:none; border-radius:4px; cursor:pointer;">Print to PDF</button>
  <table>
    <thead><tr>{header_html}</tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</body>
</html>"""
