import re
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from models import (
    User, UserRole, Booking, Hotel, RoomType,
    SupportConversation, SupportMessage, SupportSender
)


def get_or_create_conversation(
    db: Session,
    user_id: int,
    conversation_id: Optional[int] = None,
    subject: str = "Customer Support Inquiry"
) -> SupportConversation:
    """Find existing support conversation or create a new one."""
    if conversation_id:
        conv = db.query(SupportConversation).filter(
            SupportConversation.id == conversation_id,
            SupportConversation.user_id == user_id
        ).first()
        if conv:
            return conv

    conv = SupportConversation(user_id=user_id, subject=subject, status="OPEN")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def get_user_conversations(db: Session, user_id: int) -> List[SupportConversation]:
    """Retrieve all support conversations for a user."""
    return db.query(SupportConversation).filter(
        SupportConversation.user_id == user_id
    ).order_by(SupportConversation.updated_at.desc()).all()


def get_conversation_by_id(db: Session, conversation_id: int, user_id: int) -> Optional[SupportConversation]:
    """Retrieve a specific conversation verifying ownership."""
    return db.query(SupportConversation).filter(
        SupportConversation.id == conversation_id,
        SupportConversation.user_id == user_id
    ).first()


def close_conversation(db: Session, conversation: SupportConversation) -> SupportConversation:
    """Mark a support conversation as closed."""
    conversation.status = "CLOSED"
    db.commit()
    db.refresh(conversation)
    return conversation


def _resolve_booking_context(
    db: Session,
    user: User,
    user_message: str,
    provided_ref: Optional[str] = None
) -> Tuple[Optional[Booking], Optional[str]]:
    """
    Safely retrieves booking context if referenced by the user.
    Prevents unauthorized access: only the booking owner or an admin can access booking details.
    """
    ref = provided_ref
    if not ref:
        # Search for booking reference patterns like BK-XXXXXX or STAY-XXXXXX
        match = re.search(r'\b(BK-[A-Z0-9]+|STAY-[A-Z0-9]+)\b', user_message, re.IGNORECASE)
        if match:
            ref = match.group(1).upper()

    if not ref:
        return None, None

    booking = db.query(Booking).filter(Booking.booking_reference == ref).first()
    if not booking:
        return None, f"I could not find any reservation matching reference '{ref}'. Please check the code and try again."

    # Authorization Check: avoid exposing sensitive booking info to unauthorized users
    if user.role != UserRole.ADMIN and booking.user_id != user.id:
        return None, "For privacy and security, I cannot share details about a reservation that does not belong to your account."

    return booking, None


def generate_support_bot_response(
    db: Session,
    user: User,
    user_message: str,
    booking_reference: Optional[str] = None
) -> Tuple[str, Optional[int]]:
    """
    Knowledge-based AI Support Engine for Hotel, Booking, Payment, and Cancellation questions.
    Returns (bot_response_text, booking_id).
    """
    booking, auth_error = _resolve_booking_context(db, user, user_message, booking_reference)
    if auth_error:
        return auth_error, None

    msg_lower = user_message.lower()
    booking_id = booking.id if booking else None

    # 1. Booking specific inquiry
    if booking:
        hotel_name = booking.hotel.name if booking.hotel else "StayNest Hotel"
        room_name = booking.room_type.name if booking.room_type else "Reserved Room"

        if any(w in msg_lower for w in ["status", "details", "check", "reservation"]):
            return (
                f"Here are the details for reservation **{booking.booking_reference}**:\n"
                f"- **Hotel**: {hotel_name}\n"
                f"- **Room**: {room_name}\n"
                f"- **Dates**: {booking.check_in_date} to {booking.check_out_date} ({booking.total_nights} nights)\n"
                f"- **Booking Status**: {booking.status.value}\n"
                f"- **Payment Status**: {booking.payment_status.value} (Total: ${booking.total_amount:.2f})",
                booking_id
            )

        if any(w in msg_lower for w in ["cancel", "cancellation", "refund"]):
            return (
                f"Regarding cancellation for **{booking.booking_reference}** at {hotel_name}:\n"
                f"- **Current Status**: {booking.status.value}\n"
                f"- **Cancellation Policy**: Standard reservations cancelled at least 48 hours prior to check-in ({booking.check_in_date}) qualify for a full or partial refund.\n"
                f"- To submit an official cancellation or refund request, please use the Cancellation & Refund menu under your booking.",
                booking_id
            )

        if any(w in msg_lower for w in ["pay", "payment", "invoice", "receipt", "charge"]):
            return (
                f"Payment overview for **{booking.booking_reference}**:\n"
                f"- **Total Amount**: ${booking.total_amount:.2f}\n"
                f"- **Payment Status**: {booking.payment_status.value}\n"
                f"- Invoices and printable receipts are accessible in your Account under Bookings & Receipts.",
                booking_id
            )

    # 2. General Cancellation & Refund inquiries
    if any(w in msg_lower for w in ["cancel", "cancellation", "refund", "refund policy"]):
        return (
            "**StayNest Cancellation & Refund Policy:**\n"
            "- **Flexible Policy**: Free cancellation up to 24 hours prior to check-in.\n"
            "- **Moderate Policy**: 50% refund up to 48 hours before check-in.\n"
            "- **Non-Refundable**: No refund once booked.\n"
            "- Refunds are processed back to your original payment method via Stripe within 5 to 10 business days.\n"
            "If you have a specific booking reference (e.g. BK-123456), please share it and I can look up its exact cancellation window!",
            None
        )

    # 3. General Payment inquiries
    if any(w in msg_lower for w in ["payment", "pay", "credit card", "stripe", "methods", "currency"]):
        return (
            "**Payment Information:**\n"
            "- We accept Visa, MasterCard, American Express, and Discover through secure Stripe checkout.\n"
            "- Payments are encrypted with 256-bit SSL.\n"
            "- Your card is only charged upon booking confirmation. Invoices are automatically generated and emailed to your registered address.",
            None
        )

    # 4. Check-in & Check-out inquiries
    if any(w in msg_lower for w in ["check in", "check out", "check-in", "check-out", "hours", "arrival", "departure"]):
        return (
            "**Check-In & Check-Out Times:**\n"
            "- Standard **Check-in time** is **14:00 (2:00 PM)**.\n"
            "- Standard **Check-out time** is **11:00 (11:00 AM)**.\n"
            "- Early check-in or late check-out is subject to room availability and may incur a nominal fee. You can request this during check-in or directly with hotel reception.",
            None
        )

    # 5. Amenities & Services
    if any(w in msg_lower for w in ["amenity", "amenities", "wifi", "wi-fi", "pool", "gym", "breakfast", "parking", "pets"]):
        return (
            "**Amenities & Hotel Services:**\n"
            "- All StayNest properties offer complimentary high-speed Wi-Fi.\n"
            "- Wellness amenities including swimming pools and fitness centers are available at select locations.\n"
            "- Additional services such as laundry, spa, airport shuttle, and 24/7 room service can be requested directly through your booking portal.",
            None
        )

    # 6. Default AI Assistant response
    return (
        f"Hello {user.full_name}! I am your StayNest AI Support Assistant. "
        "I can help you with:\n"
        "1. Checking your reservation status and details (share your booking code, e.g., BK-XXXXXX)\n"
        "2. Understanding cancellation and refund rules\n"
        "3. Payment methods and receipt lookups\n"
        "4. Hotel policies, check-in/out hours, and available amenities.\n\n"
        "How may I assist you today?",
        None
    )


def process_support_chat(
    db: Session,
    user: User,
    user_message: str,
    conversation_id: Optional[int] = None,
    booking_reference: Optional[str] = None
) -> Tuple[SupportConversation, SupportMessage, SupportMessage]:
    """
    Main entry point for support chat:
    1. Saves user's message
    2. Runs AI support chatbot
    3. Saves bot's response
    4. Returns (conversation, user_msg, bot_msg)
    """
    conv = get_or_create_conversation(db, user.id, conversation_id)

    # 1. Save user message
    user_msg = SupportMessage(
        conversation_id=conv.id,
        sender=SupportSender.USER,
        message=user_message
    )
    db.add(user_msg)
    db.commit()

    # 2. Generate bot response
    bot_reply_text, ref_booking_id = generate_support_bot_response(
        db, user, user_message, booking_reference
    )

    # 3. Save bot response
    bot_msg = SupportMessage(
        conversation_id=conv.id,
        sender=SupportSender.BOT,
        message=bot_reply_text,
        booking_id=ref_booking_id
    )
    db.add(bot_msg)
    db.commit()
    db.refresh(bot_msg)
    db.refresh(conv)

    return conv, user_msg, bot_msg
