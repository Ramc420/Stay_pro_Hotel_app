from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import (
    Booking, BookingStatus, PaymentStatus, Hotel,
    RefundRequest, RefundStatus, ServiceRequest, RoomServiceOrder
)


def get_hotel_revenue_summary(
    db: Session,
    hotel_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Aggregate total hotel revenue:
    - Paid bookings only (excludes failed/unpaid/cancelled without payment)
    - Completed additional services
    - Delivered room service orders
    - Subtracts approved/processed refunds
    - Calculates Average Booking Value (ABV)
    """
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    hotel_name = hotel.name if hotel else f"Hotel #{hotel_id}"

    # 1. Booking Revenue
    booking_q = db.query(Booking).filter(
        Booking.hotel_id == hotel_id,
        Booking.payment_status.in_([PaymentStatus.PAID, PaymentStatus.REFUNDED])
    )
    if start_date:
        booking_q = booking_q.filter(Booking.created_at >= start_date)
    if end_date:
        booking_q = booking_q.filter(Booking.created_at <= end_date)

    paid_bookings = booking_q.all()
    booking_revenue = sum(b.total_amount for b in paid_bookings)
    completed_bookings_count = len(paid_bookings)

    # 2. Additional Services Revenue
    svc_q = db.query(ServiceRequest).filter(
        ServiceRequest.hotel_id == hotel_id,
        ServiceRequest.status == "COMPLETED"
    )
    if start_date:
        svc_q = svc_q.filter(ServiceRequest.requested_at >= start_date)
    if end_date:
        svc_q = svc_q.filter(ServiceRequest.requested_at <= end_date)

    service_revenue = sum(s.total_price for s in svc_q.all())

    # 3. Room Service Revenue
    rs_q = db.query(RoomServiceOrder).filter(
        RoomServiceOrder.hotel_id == hotel_id,
        RoomServiceOrder.status == "DELIVERED"
    )
    if start_date:
        rs_q = rs_q.filter(RoomServiceOrder.created_at >= start_date)
    if end_date:
        rs_q = rs_q.filter(RoomServiceOrder.created_at <= end_date)

    room_service_revenue = sum(r.total_amount for r in rs_q.all())

    # 4. Refunds accounted for
    ref_q = db.query(RefundRequest).filter(
        RefundRequest.hotel_id == hotel_id,
        RefundRequest.status.in_([RefundStatus.APPROVED, RefundStatus.PROCESSED])
    )
    if start_date:
        ref_q = ref_q.filter(RefundRequest.processed_at >= start_date)
    if end_date:
        ref_q = ref_q.filter(RefundRequest.processed_at <= end_date)

    refund_amount = sum(
        (r.amount_approved if r.amount_approved is not None else r.amount_requested)
        for r in ref_q.all()
    )

    gross_revenue = booking_revenue + service_revenue + room_service_revenue
    net_revenue = max(0.0, gross_revenue - refund_amount)
    abv = (booking_revenue / completed_bookings_count) if completed_bookings_count > 0 else 0.0

    return {
        "hotel_id": hotel_id,
        "hotel_name": hotel_name,
        "total_gross_revenue": round(gross_revenue, 2),
        "total_booking_revenue": round(booking_revenue, 2),
        "total_service_revenue": round(service_revenue, 2),
        "total_room_service_revenue": round(room_service_revenue, 2),
        "total_refunded": round(refund_amount, 2),
        "net_revenue": round(net_revenue, 2),
        "total_completed_bookings": completed_bookings_count,
        "average_booking_value": round(abv, 2)
    }


def get_daily_revenue_breakdown(
    db: Session,
    hotel_id: int,
    days: int = 14
) -> List[Dict[str, Any]]:
    """Generate daily day-by-day revenue breakdown for recent days."""
    today = date.today()
    results = []

    for i in range(days - 1, -1, -1):
        target_day = today - timedelta(days=i)
        day_start = datetime.combine(target_day, datetime.min.time())
        day_end = datetime.combine(target_day, datetime.max.time())

        # Bookings on target day
        bookings = db.query(Booking).filter(
            Booking.hotel_id == hotel_id,
            Booking.payment_status.in_([PaymentStatus.PAID, PaymentStatus.REFUNDED]),
            Booking.created_at >= day_start,
            Booking.created_at <= day_end
        ).all()
        b_rev = sum(b.total_amount for b in bookings)

        # Services on target day
        services = db.query(ServiceRequest).filter(
            ServiceRequest.hotel_id == hotel_id,
            ServiceRequest.status == "COMPLETED",
            ServiceRequest.requested_at >= day_start,
            ServiceRequest.requested_at <= day_end
        ).all()
        s_rev = sum(s.total_price for s in services)

        # Room service on target day
        rs = db.query(RoomServiceOrder).filter(
            RoomServiceOrder.hotel_id == hotel_id,
            RoomServiceOrder.status == "DELIVERED",
            RoomServiceOrder.created_at >= day_start,
            RoomServiceOrder.created_at <= day_end
        ).all()
        rs_rev = sum(r.total_amount for r in rs)

        # Refunds on target day
        refunds = db.query(RefundRequest).filter(
            RefundRequest.hotel_id == hotel_id,
            RefundRequest.status.in_([RefundStatus.APPROVED, RefundStatus.PROCESSED]),
            RefundRequest.processed_at >= day_start,
            RefundRequest.processed_at <= day_end
        ).all()
        ref_rev = sum(
            (r.amount_approved if r.amount_approved is not None else r.amount_requested)
            for r in refunds
        )

        net = max(0.0, (b_rev + s_rev + rs_rev) - ref_rev)
        results.append({
            "date": target_day.isoformat(),
            "booking_revenue": round(b_rev, 2),
            "service_revenue": round(s_rev, 2),
            "room_service_revenue": round(rs_rev, 2),
            "refund_amount": round(ref_rev, 2),
            "net_revenue": round(net, 2),
            "bookings_count": len(bookings)
        })

    return results


def get_monthly_revenue_breakdown(
    db: Session,
    hotel_id: int,
    months_count: int = 6
) -> List[Dict[str, Any]]:
    """Generate monthly breakdown of revenue."""
    today = date.today()
    results = []

    for i in range(months_count - 1, -1, -1):
        # Calculate year and month
        y = today.year
        m = today.month - i
        while m <= 0:
            m += 12
            y -= 1

        month_label = f"{y}-{m:02d}"
        start_date = datetime(y, m, 1)
        next_m = m + 1 if m < 12 else 1
        next_y = y if m < 12 else y + 1
        end_date = datetime(next_y, next_m, 1) - timedelta(microseconds=1)

        bookings = db.query(Booking).filter(
            Booking.hotel_id == hotel_id,
            Booking.payment_status.in_([PaymentStatus.PAID, PaymentStatus.REFUNDED]),
            Booking.created_at >= start_date,
            Booking.created_at <= end_date
        ).all()
        b_rev = sum(b.total_amount for b in bookings)

        refunds = db.query(RefundRequest).filter(
            RefundRequest.hotel_id == hotel_id,
            RefundRequest.status.in_([RefundStatus.APPROVED, RefundStatus.PROCESSED]),
            RefundRequest.processed_at >= start_date,
            RefundRequest.processed_at <= end_date
        ).all()
        ref_rev = sum(
            (r.amount_approved if r.amount_approved is not None else r.amount_requested)
            for r in refunds
        )

        net = max(0.0, b_rev - ref_rev)
        results.append({
            "month": month_label,
            "booking_revenue": round(b_rev, 2),
            "service_revenue": 0.0,
            "room_service_revenue": 0.0,
            "refund_amount": round(ref_rev, 2),
            "net_revenue": round(net, 2),
            "bookings_count": len(bookings)
        })

    return results
