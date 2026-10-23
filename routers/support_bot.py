"""
Module 23: AI Customer Support Chatbot
Provides intelligent AI customer support for hotel, booking, payment, and cancellation inquiries.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from auth.dependencies import get_current_user
from utils.response import api_response
from schemas.support_bot import SupportChatRequest
from crud import support_bot as crud_support

router = APIRouter(prefix="/support", tags=["Module 23: AI Customer Support Chatbot"])


@router.post("/chat", summary="Chat with AI Customer Support")
def chat_with_support_bot(
    request: SupportChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ask a question regarding hotels, bookings, payments, or cancellations.
    Automatically retrieves authorized booking context and protects sensitive data.
    """
    conv, user_msg, bot_msg = crud_support.process_support_chat(
        db=db,
        user=current_user,
        user_message=request.message,
        conversation_id=request.conversation_id,
        booking_reference=request.booking_reference
    )

    return api_response(
        success=True,
        message="AI Support response generated successfully",
        data={
            "conversation_id": conv.id,
            "subject": conv.subject,
            "status": conv.status,
            "user_message": {
                "id": user_msg.id,
                "message": user_msg.message,
                "created_at": user_msg.created_at.isoformat()
            },
            "bot_response": {
                "id": bot_msg.id,
                "sender": bot_msg.sender.value,
                "message": bot_msg.message,
                "booking_id": bot_msg.booking_id,
                "created_at": bot_msg.created_at.isoformat()
            }
        }
    )


@router.get("/conversations", summary="List user's support conversations")
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversations = crud_support.get_user_conversations(db, current_user.id)
    return api_response(
        success=True,
        message="Conversations retrieved successfully",
        data=[
            {
                "id": c.id,
                "subject": c.subject,
                "status": c.status,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat()
            }
            for c in conversations
        ]
    )


@router.get("/conversations/{conversation_id}", summary="Get support conversation thread")
def get_conversation_thread(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = crud_support.get_conversation_by_id(db, conversation_id, current_user.id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support conversation not found"
        )

    return api_response(
        success=True,
        message="Conversation thread retrieved",
        data={
            "id": conv.id,
            "subject": conv.subject,
            "status": conv.status,
            "created_at": conv.created_at.isoformat(),
            "messages": [
                {
                    "id": m.id,
                    "sender": m.sender.value,
                    "message": m.message,
                    "booking_id": m.booking_id,
                    "created_at": m.created_at.isoformat()
                }
                for m in conv.messages
            ]
        }
    )


@router.patch("/conversations/{conversation_id}/close", summary="Close support conversation")
def close_support_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = crud_support.get_conversation_by_id(db, conversation_id, current_user.id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support conversation not found"
        )

    closed_conv = crud_support.close_conversation(db, conv)
    return api_response(
        success=True,
        message="Conversation marked as closed",
        data={"id": closed_conv.id, "status": closed_conv.status}
    )
