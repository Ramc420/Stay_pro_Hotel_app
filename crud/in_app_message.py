from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models import User, UserRole, Hotel, HotelStaff, Conversation, ChatMessage


def can_access_conversation(db: Session, user: User, conversation: Conversation) -> bool:
    """Check if the user is authorized to participate in this conversation."""
    if user.role == UserRole.ADMIN:
        return True

    # Customer owner of the conversation
    if conversation.customer_id == user.id:
        return True

    # Hotel Owner or assigned Staff
    if conversation.hotel_id:
        hotel = db.query(Hotel).filter(Hotel.id == conversation.hotel_id).first()
        if hotel and hotel.owner_id == user.id:
            return True

        if user.role == UserRole.HOTEL_STAFF:
            is_staff = db.query(HotelStaff).filter(
                HotelStaff.hotel_id == conversation.hotel_id,
                HotelStaff.user_id == user.id,
                HotelStaff.is_active == True
            ).first()
            if is_staff:
                return True

    return False


def create_conversation(
    db: Session,
    customer_id: int,
    subject: str,
    hotel_id: Optional[int] = None,
    conversation_type: str = "HOTEL",
    initial_message: Optional[str] = None
) -> Tuple[Conversation, Optional[ChatMessage]]:
    """Start a new message conversation and optionally post the first message."""
    conv = Conversation(
        customer_id=customer_id,
        hotel_id=hotel_id,
        subject=subject,
        conversation_type=conversation_type,
        last_message_at=datetime.utcnow()
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    first_msg = None
    if initial_message:
        first_msg = ChatMessage(
            conversation_id=conv.id,
            sender_id=customer_id,
            message=initial_message,
            status="SENT"
        )
        db.add(first_msg)
        db.commit()
        db.refresh(first_msg)

    return conv, first_msg


def get_user_conversations(
    db: Session,
    user: User,
    limit: int = 50,
    offset: int = 0
) -> List[Tuple[Conversation, int]]:
    """
    List conversations accessible to the user with unread message counts.
    Returns list of (Conversation, unread_count).
    """
    query = db.query(Conversation)

    if user.role == UserRole.CUSTOMER:
        query = query.filter(Conversation.customer_id == user.id)
    elif user.role == UserRole.HOTEL_OWNER:
        # Owns the hotel or initiated as customer
        hotel_ids = [h.id for h in db.query(Hotel.id).filter(Hotel.owner_id == user.id).all()]
        query = query.filter(
            or_(Conversation.customer_id == user.id, Conversation.hotel_id.in_(hotel_ids))
        )
    elif user.role == UserRole.HOTEL_STAFF:
        staff_hotel_ids = [s.hotel_id for s in db.query(HotelStaff.hotel_id).filter(
            HotelStaff.user_id == user.id, HotelStaff.is_active == True
        ).all()]
        query = query.filter(
            or_(Conversation.customer_id == user.id, Conversation.hotel_id.in_(staff_hotel_ids))
        )
    # Admin sees all

    conversations = query.order_by(Conversation.last_message_at.desc()).offset(offset).limit(limit).all()

    result = []
    for conv in conversations:
        # Count unread messages not sent by the current user
        unread = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conv.id,
            ChatMessage.sender_id != user.id,
            ChatMessage.status != "READ"
        ).count()
        result.append((conv, unread))

    return result


def get_conversation_messages(
    db: Session,
    conversation_id: int,
    limit: int = 50,
    offset: int = 0
) -> Tuple[List[ChatMessage], int]:
    """Get paginated message history and total message count."""
    total = db.query(ChatMessage).filter(ChatMessage.conversation_id == conversation_id).count()
    messages = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation_id
    ).order_by(ChatMessage.created_at.asc()).offset(offset).limit(limit).all()
    return messages, total


def send_chat_message(
    db: Session,
    conversation: Conversation,
    sender_id: int,
    message_text: str
) -> ChatMessage:
    """Send a new message in a conversation and update last_message_at timestamp."""
    msg = ChatMessage(
        conversation_id=conversation.id,
        sender_id=sender_id,
        message=message_text,
        status="SENT"
    )
    db.add(msg)
    conversation.last_message_at = datetime.utcnow()
    db.commit()
    db.refresh(msg)
    return msg


def mark_conversation_as_read(db: Session, conversation_id: int, reader_user_id: int) -> int:
    """Mark all incoming messages in the conversation as READ."""
    updated = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation_id,
        ChatMessage.sender_id != reader_user_id,
        ChatMessage.status != "READ"
    ).update({"status": "READ"}, synchronize_session=False)
    db.commit()
    return updated
