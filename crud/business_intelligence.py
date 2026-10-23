from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import (
    Hotel, Booking, BookingStatus, PaymentStatus, User, UserRole, Review, Room
)


def get_platform_growth_metrics(db: Session, days: int = 30) -> Dict[str, Any]:
    """Calculate platform growth metrics (Revenue, Bookings, Customers) with previous period comparison."""
    now = datetime.utcnow()
    current_start = now - timedelta(days=days)
    previous_start = current_start - timedelta(days=days)

    # 1. Revenue
    curr_rev = db.query(func.coalesce(func.sum(Booking.total_amount), 0.0)).filter(
        Booking.payment_status.in_([PaymentStatus.PAID, PaymentStatus.REFUNDED]),
        Booking.created_at >= current_start
    ).scalar() or 0.0

    prev_rev = db.query(func.coalesce(func.sum(Booking.total_amount), 0.0)).filter(
        Booking.payment_status.in_([PaymentStatus.PAID, PaymentStatus.REFUNDED]),
        Booking.created_at >= previous_start,
        Booking.created_at < current_start
    ).scalar() or 0.0

    rev_growth = round(((curr_rev - prev_rev) / prev_rev * 100.0) if prev_rev > 0 else (100.0 if curr_rev > 0 else 0.0), 2)
    rev_trend = "UP" if rev_growth > 0 else ("DOWN" if rev_growth < 0 else "FLAT")

    # 2. Bookings
    curr_b = db.query(Booking).filter(Booking.created_at >= current_start).count()
    prev_b = db.query(Booking).filter(
        Booking.created_at >= previous_start,
        Booking.created_at < current_start
    ).count()

    b_growth = round(((curr_b - prev_b) / prev_b * 100.0) if prev_b > 0 else (100.0 if curr_b > 0 else 0.0), 2)
    b_trend = "UP" if b_growth > 0 else ("DOWN" if b_growth < 0 else "FLAT")

    # 3. Customer growth
    curr_c = db.query(User).filter(
        User.role == UserRole.CUSTOMER,
        User.created_at >= current_start
    ).count()

    prev_c = db.query(User).filter(
        User.role == UserRole.CUSTOMER,
        User.created_at >= previous_start,
        User.created_at < current_start
    ).count()

    c_growth = round(((curr_c - prev_c) / prev_c * 100.0) if prev_c > 0 else (100.0 if curr_c > 0 else 0.0), 2)
    c_trend = "UP" if c_growth > 0 else ("DOWN" if c_growth < 0 else "FLAT")

    return {
        "period": f"Last {days} days vs prior {days} days",
        "revenue_growth": {
            "metric_name": "Gross Revenue",
            "current_period_value": round(curr_rev, 2),
            "previous_period_value": round(prev_rev, 2),
            "growth_percentage": rev_growth,
            "trend": rev_trend
        },
        "bookings_growth": {
            "metric_name": "Total Bookings",
            "current_period_value": float(curr_b),
            "previous_period_value": float(prev_b),
            "growth_percentage": b_growth,
            "trend": b_trend
        },
        "customer_growth": {
            "metric_name": "New Customers",
            "current_period_value": float(curr_c),
            "previous_period_value": float(prev_c),
            "growth_percentage": c_growth,
            "trend": c_trend
        }
    }


def get_top_performers(db: Session, limit: int = 5) -> Dict[str, Any]:
    """Identify top-performing revenue-generating hotels and popular destinations."""
    hotels = db.query(Hotel).filter(Hotel.is_approved == True).all()

    hotel_stats = []
    dest_map = {}

    for h in hotels:
        bks = db.query(Booking).filter(
            Booking.hotel_id == h.id,
            Booking.payment_status.in_([PaymentStatus.PAID, PaymentStatus.REFUNDED])
        ).all()

        h_rev = sum(b.total_amount for b in bks)
        h_cnt = len(bks)

        hotel_stats.append({
            "hotel_id": h.id,
            "hotel_name": h.name,
            "city": h.city,
            "total_bookings": h_cnt,
            "gross_revenue": round(h_rev, 2),
            "average_rating": round(h.star_rating, 1)
        })

        # Destination aggregation
        dest_key = (h.city, h.state, h.country)
        if dest_key not in dest_map:
            dest_map[dest_key] = {"bookings": 0, "revenue": 0.0}
        dest_map[dest_key]["bookings"] += h_cnt
        dest_map[dest_key]["revenue"] += h_rev

    # Sort hotels by gross revenue
    hotel_stats.sort(key=lambda x: x["gross_revenue"], reverse=True)

    # Sort destinations
    dest_list = [
        {
            "city": k[0],
            "state": k[1],
            "country": k[2],
            "total_bookings": v["bookings"],
            "total_revenue": round(v["revenue"], 2)
        }
        for k, v in dest_map.items()
    ]
    dest_list.sort(key=lambda x: x["total_revenue"], reverse=True)

    return {
        "top_hotels": hotel_stats[:limit],
        "top_destinations": dest_list[:limit]
    }


def get_occupancy_trends(
    db: Session,
    hotel_id: Optional[int] = None,
    months_count: int = 6
) -> Dict[str, Any]:
    """Track occupancy rates and nights sold across recent months."""
    today = date.today()
    trend_points = []

    for i in range(months_count - 1, -1, -1):
        # Month computation
        y = today.year
        m = today.month - i
        while m <= 0:
            m += 12
            y -= 1

        month_label = f"{y}-{m:02d}"
        m_start = date(y, m, 1)
        next_m = m + 1 if m < 12 else 1
        next_y = y if m < 12 else y + 1
        m_end = date(next_y, next_m, 1) - timedelta(days=1)
        days_in_month = (m_end - m_start).days + 1

        # Rooms count
        r_q = db.query(Room)
        if hotel_id:
            r_q = r_q.filter(Room.hotel_id == hotel_id)
        rooms_count = max(1, r_q.count())

        # Bookings in month
        b_q = db.query(Booking).filter(
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT, BookingStatus.COMPLETED]),
            Booking.check_in_date <= m_end,
            Booking.check_out_date >= m_start
        )
        if hotel_id:
            b_q = b_q.filter(Booking.hotel_id == hotel_id)

        bks = b_q.all()
        nights_sold = sum(b.total_nights for b in bks)
        rev = sum(b.total_amount for b in bks)

        total_capacity_room_nights = rooms_count * days_in_month
        occ_rate = round(min(100.0, (nights_sold / total_capacity_room_nights) * 100.0), 2)

        trend_points.append({
            "month": month_label,
            "occupancy_rate_percentage": occ_rate,
            "total_nights_sold": nights_sold,
            "total_bookings": len(bks),
            "revenue": round(rev, 2)
        })

    return {
        "hotel_id": hotel_id,
        "period_months": months_count,
        "trends": trend_points
    }


def get_executive_monthly_summary(
    db: Session,
    year: int,
    month: int
) -> Dict[str, Any]:
    """Generate high-level executive business summary for given year and month."""
    start_dt = datetime(year, month, 1)
    next_m = month + 1 if month < 12 else 1
    next_y = year if month < 12 else year + 1
    end_dt = datetime(next_y, next_m, 1) - timedelta(microseconds=1)

    bookings = db.query(Booking).filter(
        Booking.payment_status.in_([PaymentStatus.PAID, PaymentStatus.REFUNDED]),
        Booking.created_at >= start_dt,
        Booking.created_at <= end_dt
    ).all()

    total_rev = sum(b.total_amount for b in bookings)
    b_count = len(bookings)
    abv = (total_rev / b_count) if b_count > 0 else 0.0

    active_hotels = db.query(Hotel).filter(Hotel.is_approved == True, Hotel.is_active == True).count()
    new_cust = db.query(User).filter(
        User.role == UserRole.CUSTOMER,
        User.created_at >= start_dt,
        User.created_at <= end_dt
    ).count()

    # Commission estimate (10%)
    commission_earned = round(total_rev * 0.10, 2)

    # Top city
    top_city_row = db.query(Hotel.city, func.count(Booking.id)).join(Booking, Booking.hotel_id == Hotel.id).filter(
        Booking.created_at >= start_dt,
        Booking.created_at <= end_dt
    ).group_by(Hotel.city).order_by(func.count(Booking.id).desc()).first()

    return {
        "year": year,
        "month": month,
        "month_name": start_dt.strftime("%B %Y"),
        "total_revenue": round(total_rev, 2),
        "total_bookings": float(b_count),
        "total_active_hotels": active_hotels,
        "total_new_customers": new_cust,
        "average_booking_value": round(abv, 2),
        "platform_commission_earned": commission_earned,
        "top_city": top_city_row[0] if top_city_row else "Honolulu"
    }
