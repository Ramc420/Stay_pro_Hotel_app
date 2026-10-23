from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import User, UserRole, Booking, PaymentStatus, Hotel


def get_customer_analytics_summary(db: Session, hotel_id: Optional[int] = None) -> Dict[str, Any]:
    """Calculate customer retention, average lifetime spend, and repeat metrics."""
    # Find customers who booked
    booking_q = db.query(Booking).filter(
        Booking.payment_status.in_([PaymentStatus.PAID, PaymentStatus.REFUNDED])
    )
    if hotel_id:
        booking_q = booking_q.filter(Booking.hotel_id == hotel_id)

    bookings = booking_q.all()
    user_booking_counts: Dict[int, int] = {}
    user_spends: Dict[int, float] = {}

    for b in bookings:
        user_booking_counts[b.user_id] = user_booking_counts.get(b.user_id, 0) + 1
        user_spends[b.user_id] = user_spends.get(b.user_id, 0.0) + b.total_amount

    total_customers_with_bookings = len(user_booking_counts)
    repeat_customers = sum(1 for count in user_booking_counts.values() if count >= 2)
    retention_rate = round((repeat_customers / total_customers_with_bookings * 100.0), 2) if total_customers_with_bookings > 0 else 0.0

    total_bookings = len(bookings)
    avg_bookings_per_user = round(total_bookings / total_customers_with_bookings, 2) if total_customers_with_bookings > 0 else 0.0

    total_spend_all = sum(user_spends.values())
    avg_lifetime_value = round(total_spend_all / total_customers_with_bookings, 2) if total_customers_with_bookings > 0 else 0.0

    total_registered = db.query(User).filter(User.role == UserRole.CUSTOMER).count()

    return {
        "total_registered_customers": total_registered,
        "active_booking_customers": total_customers_with_bookings,
        "repeat_customers_count": repeat_customers,
        "retention_rate": retention_rate,
        "average_bookings_per_customer": avg_bookings_per_user,
        "average_customer_lifetime_value": avg_lifetime_value
    }


def get_repeat_customers(
    db: Session,
    hotel_id: Optional[int] = None,
    min_bookings: int = 2,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Identify and list top repeat customers with their total spend."""
    booking_q = db.query(Booking).filter(
        Booking.payment_status.in_([PaymentStatus.PAID, PaymentStatus.REFUNDED])
    )
    if hotel_id:
        booking_q = booking_q.filter(Booking.hotel_id == hotel_id)

    bookings = booking_q.all()
    user_stats: Dict[int, Dict[str, Any]] = {}

    for b in bookings:
        uid = b.user_id
        if uid not in user_stats:
            user_stats[uid] = {
                "user_id": uid,
                "full_name": b.user.full_name if b.user else f"Guest #{uid}",
                "email": b.user.email if b.user else "",
                "bookings_count": 0,
                "total_spend": 0.0
            }
        user_stats[uid]["bookings_count"] += 1
        user_stats[uid]["total_spend"] += b.total_amount

    # Filter for repeat customers
    repeat = [s for s in user_stats.values() if s["bookings_count"] >= min_bookings]
    for r in repeat:
        r["total_spend"] = round(r["total_spend"], 2)
        r["average_spend"] = round(r["total_spend"] / r["bookings_count"], 2)

    repeat.sort(key=lambda x: x["bookings_count"], reverse=True)
    return repeat[:limit]


def get_popular_destinations(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """Aggregate top cities and destination demand by completed bookings."""
    results = db.query(
        Hotel.city,
        Hotel.country,
        func.count(Hotel.id).label("hotels_count"),
        func.count(Booking.id).label("total_bookings"),
        func.coalesce(func.sum(Booking.total_amount), 0.0).label("total_revenue")
    ).outerjoin(Booking, Booking.hotel_id == Hotel.id).group_by(
        Hotel.city, Hotel.country
    ).order_by(func.count(Booking.id).desc()).limit(limit).all()

    return [
        {
            "city": r.city,
            "country": r.country,
            "hotels_count": r.hotels_count,
            "total_bookings": r.total_bookings,
            "total_revenue": round(float(r.total_revenue), 2)
        }
        for r in results
    ]
