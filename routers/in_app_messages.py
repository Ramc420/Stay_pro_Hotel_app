"""
Module 25: In-App Messaging
Enables customer-to-hotel and customer-to-support messaging with conversation history and unread tracking.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, Conversation
from auth.dependencies import get_current_user
from utils.response import api_response, paginated_response
from schemas.in_app_message import ConversationCreate, ChatMessageCreate
from crud import in_app_message as crud_msg

router = APIRouter(prefix="/messages", tags=["Module 25: In-App Messaging"])


@router.post("/conversations", summary="Start a new message conversation")
def start_conversation(
    request: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv, first_msg = crud_msg.create_conversation(
        db=db,
        customer_id=current_user.id,
        subject=request.subject,
        hotel_id=request.hotel_id,
        conversation_type=request.conversation_type or "HOTEL",
        initial_message=request.initial_message
    )

    return api_response(
        success=True,
        message="Conversation started successfully",
        data={
            "conversation_id": conv.id,
            "subject": conv.subject,
            "hotel_id": conv.hotel_id,
            "conversation_type": conv.conversation_type,
            "initial_message": first_msg.message if first_msg else None,
            "created_at": conv.created_at.isoformat()
        },
        status_code=status.HTTP_201_CREATED
    )


@router.get("/conversations", summary="List user's message conversations")
def list_conversations(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    convs_with_unread = crud_msg.get_user_conversations(db, current_user, limit=limit, offset=offset)

    return api_response(
        success=True,
        message="Conversations retrieved successfully",
        data=[
            {
                "id": c.id,
                "customer_id": c.customer_id,
                "hotel_id": c.hotel_id,
                "hotel_name": c.hotel.name if c.hotel else None,
                "subject": c.subject,
                "conversation_type": c.conversation_type,
                "unread_count": unread,
                "last_message_at": c.last_message_at.isoformat(),
                "created_at": c.created_at.isoformat()
            }
            for c, unread in convs_with_unread
        ]
    )


@router.get("/conversations/{conversation_id}/messages", summary="Get messages in conversation")
def get_messages(
    conversation_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    if not crud_msg.can_access_conversation(db, current_user, conv):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this conversation")

    messages, total = crud_msg.get_conversation_messages(db, conversation_id, limit=limit, offset=offset)

    return api_response(
        success=True,
        message="Messages retrieved successfully",
        data=[
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "sender_name": m.sender.full_name if m.sender else "User",
                "message": m.message,
                "status": m.status,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ],
        meta={"total": total, "limit": limit, "offset": offset}
    )


@router.post("/conversations/{conversation_id}/messages", summary="Send message in conversation")
def send_message(
    conversation_id: int,
    request: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    if not crud_msg.can_access_conversation(db, current_user, conv):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this conversation")

    msg = crud_msg.send_chat_message(db, conv, current_user.id, request.message)

    return api_response(
        success=True,
        message="Message sent successfully",
        data={
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "sender_id": msg.sender_id,
            "message": msg.message,
            "status": msg.status,
            "created_at": msg.created_at.isoformat()
        },
        status_code=status.HTTP_201_CREATED
    )


@router.patch("/conversations/{conversation_id}/read", summary="Mark conversation as read")
def mark_read(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    if not crud_msg.can_access_conversation(db, current_user, conv):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    count = crud_msg.mark_conversation_as_read(db, conversation_id, current_user.id)
    return api_response(
        success=True,
        message=f"{count} message(s) marked as read",
        data={"updated_count": count}
    )
