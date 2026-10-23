from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import (
    User, UserRole, Hotel, Room, RoomStatus, Booking, BookingStatus,
    Payment, PaymentStatus, Review, Wishlist, Notification,
    RefundRequest, RefundStatus, HousekeepingTask, HousekeepingStatus
)


def get_owner_dashboard(db: Session, hotel_id: int) -> Dict[str, Any]:
    """Consolidated single-call dashboard for Hotel Owners."""
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    hotel_name = hotel.name if hotel else f"Hotel #{hotel_id}"

    today = date.today()
    month_start = datetime(today.year, today.month, 1)

    # 1. Rooms & Live Occupancy
    rooms = db.query(Room).filter(Room.hotel_id == hotel_id, Room.is_active == True).all()
    total_rooms = len(rooms)
    occupied_rooms = sum(1 for r in rooms if r.status == RoomStatus.OCCUPIED)
    occupancy_rate = round((occupied_rooms / total_rooms * 100.0), 2) if total_rooms > 0 else 0.0

    # 2. Today's Arrivals and Departures
    today_arrivals = db.query(Booking).filter(
        Booking.hotel_id == hotel_id,
        Booking.check_in_date == today,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING])
    ).all()

    today_departures = db.query(Booking).filter(
        Booking.hotel_id == hotel_id,
        Booking.check_out_date == today,
        Booking.status == BookingStatus.CHECKED_IN
    ).all()

    # 3. Revenue
    today_start = datetime.combine(today, datetime.min.time())
    today_rev = db.query(func.coalesce(func.sum(Booking.total_amount), 0.0)).filter(
        Booking.hotel_id == hotel_id,
        Booking.payment_status == PaymentStatus.PAID,
        Booking.created_at >= today_start
    ).scalar()

    month_rev = db.query(func.coalesce(func.sum(Booking.total_amount), 0.0)).filter(
        Booking.hotel_id == hotel_id,
        Booking.payment_status == PaymentStatus.PAID,
        Booking.created_at >= month_start
    ).scalar()

    total_rev = db.query(func.coalesce(func.sum(Booking.total_amount), 0.0)).filter(
        Booking.hotel_id == hotel_id,
        Booking.payment_status == PaymentStatus.PAID
    ).scalar()

    # 4. Reviews & Rating
    reviews = db.query(Review).filter(Review.hotel_id == hotel_id, Review.is_hidden == False).all()
    total_reviews = len(reviews)
    avg_rating = round(sum(r.rating for r in reviews) / total_reviews, 1) if total_reviews > 0 else 0.0


    # 5. Pending Housekeeping Tasks
    pending_hk = db.query(HousekeepingTask).filter(
        HousekeepingTask.hotel_id == hotel_id,
        HousekeepingTask.status.in_([HousekeepingStatus.DIRTY, HousekeepingStatus.CLEANING])
    ).count()

    return {
        "hotel_id": hotel_id,
        "hotel_name": hotel_name,
        "today_arrivals_count": len(today_arrivals),
        "today_departures_count": len(today_departures),
        "current_guest_count": occupied_rooms * 2,  # approx occupancy estimation
        "total_rooms": total_rooms,
        "occupied_rooms": occupied_rooms,
        "occupancy_rate": occupancy_rate,
        "today_revenue": round(float(today_rev), 2),
        "month_revenue": round(float(month_rev), 2),
        "total_revenue": round(float(total_rev), 2),
        "average_rating": avg_rating,
        "total_reviews": total_reviews,
        "pending_check_ins": [
            {
                "booking_id": b.id,
                "booking_reference": b.booking_reference,
                "guest_name": b.user.full_name if b.user else "Guest",
                "room_id": b.room_id
            }
            for b in today_arrivals[:5]
        ],
        "recent_reviews": [
            {
                "rating": r.rating,
                "comment": r.comment,
                "created_at": r.created_at.isoformat()
            }
            for r in reviews[-3:]
        ],

        "action_items": {
            "rooms_requiring_cleaning": pending_hk,
            "pending_arrivals": len(today_arrivals)
        }
    }


def get_customer_dashboard(db: Session, user_id: int) -> Dict[str, Any]:
    """Personalized overview for a customer."""
    user = db.query(User).filter(User.id == user_id).first()
    today = date.today()

    # 1. Upcoming bookings
    upcoming = db.query(Booking).filter(
        Booking.user_id == user_id,
        Booking.check_out_date >= today,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN])
    ).order_by(Booking.check_in_date.asc()).all()

    # 2. Past bookings count
    past_count = db.query(Booking).filter(
        Booking.user_id == user_id,
        Booking.check_out_date < today
    ).count()

    # 3. Total spent
    total_spent = db.query(func.coalesce(func.sum(Booking.total_amount), 0.0)).filter(
        Booking.user_id == user_id,
        Booking.payment_status == PaymentStatus.PAID
    ).scalar()

    # 4. Wishlist count
    wishlist_count = db.query(Wishlist).filter(Wishlist.user_id == user_id).count()

    # 5. Unread notifications
    unread_notifs = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).count()

    # 6. Recent Payments
    payments = db.query(Payment).join(Booking, Payment.booking_id == Booking.id).filter(
        Booking.user_id == user_id
    ).order_by(Payment.created_at.desc()).limit(3).all()


    # 7. Recommended hotels (top approved hotels)
    top_hotels = db.query(Hotel).filter(
        Hotel.is_approved == True, Hotel.is_active == True
    ).order_by(Hotel.star_rating.desc()).limit(3).all()

    return {
        "user_id": user_id,
        "full_name": user.full_name if user else "Customer",
        "upcoming_bookings": [
            {
                "booking_id": b.id,
                "booking_reference": b.booking_reference,
                "hotel_name": b.hotel.name if b.hotel else "Hotel",
                "city": b.hotel.city if b.hotel else "",
                "check_in_date": b.check_in_date.isoformat(),
                "check_out_date": b.check_out_date.isoformat(),
                "status": b.status.value,
                "total_amount": b.total_amount
            }
            for b in upcoming
        ],
        "past_bookings_count": past_count,
        "total_spent": round(float(total_spent), 2),
        "wishlist_count": wishlist_count,
        "unread_notifications_count": unread_notifs,
        "recent_payments": [
            {
                "payment_id": p.id,
                "amount": p.amount,
                "status": p.status.value,
                "created_at": p.created_at.isoformat()
            }
            for p in payments
        ],
        "recommended_hotels": [
            {
                "hotel_id": h.id,
                "name": h.name,
                "city": h.city,
                "star_rating": h.star_rating
            }
            for h in top_hotels
        ]
    }


def get_admin_dashboard(db: Session) -> Dict[str, Any]:
    """Platform-wide summary metrics for Platform Administrators."""
    total_cust = db.query(User).filter(User.role == UserRole.CUSTOMER).count()
    total_owners = db.query(User).filter(User.role == UserRole.HOTEL_OWNER).count()
    total_hotels = db.query(Hotel).count()
    approved_hotels = db.query(Hotel).filter(Hotel.is_approved == True).count()
    pending_hotels = db.query(Hotel).filter(Hotel.is_approved == False).count()
    total_rooms = db.query(Room).filter(Room.is_active == True).count()
    total_bookings = db.query(Booking).count()

    active_reservations = db.query(Booking).filter(
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN])
    ).count()

    gross_rev = db.query(func.coalesce(func.sum(Booking.total_amount), 0.0)).filter(
        Booking.payment_status == PaymentStatus.PAID
    ).scalar()

    total_refunds = db.query(func.coalesce(func.sum(RefundRequest.amount_approved), 0.0)).filter(
        RefundRequest.status.in_([RefundStatus.APPROVED, RefundStatus.PROCESSED])
    ).scalar()


    net_vol = max(0.0, float(gross_rev) - float(total_refunds))

    recent_users = db.query(User).order_by(User.created_at.desc()).limit(5).all()

    return {
        "total_customers": total_cust,
        "total_hotel_owners": total_owners,
        "total_hotels": total_hotels,
        "approved_hotels": approved_hotels,
        "pending_hotels_count": pending_hotels,
        "total_rooms": total_rooms,
        "total_bookings": total_bookings,
        "active_reservations": active_reservations,
        "total_platform_revenue": round(float(gross_rev), 2),
        "total_refunds_processed": round(float(total_refunds), 2),
        "net_platform_volume": round(net_vol, 2),
        "pending_moderation_items": pending_hotels,
        "recent_registrations": [
            {
                "user_id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "role": u.role.value,
                "created_at": u.created_at.isoformat()
            }
            for u in recent_users
        ]
    }
