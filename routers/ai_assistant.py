from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas.ai_assistant import (
    TripPlanRequest, TripPlanResponse,
    AIChatRequest, AIChatResponse,
    AIConversationResponse, AIMessageResponse
)
from auth.dependencies import get_current_user
from crud import ai_assistant as crud_ai
from utils.response import api_response

router = APIRouter(prefix="/ai-assistant", tags=["Module 22: AI Travel Assistant"])


def _serialize_conversation(c) -> dict:
    return {
        "id": c.id,
        "user_id": c.user_id,
        "title": c.title,
        "destination": c.destination,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        "message_count": len(c.messages) if c.messages else 0
    }


def _serialize_message(m) -> dict:
    return {
        "id": m.id,
        "conversation_id": m.conversation_id,
        "role": m.role,
        "content": m.content,
        "suggested_hotels": m.suggested_hotels,
        "itinerary_data": m.itinerary_data,
        "created_at": m.created_at.isoformat() if m.created_at else None
    }


# ---------------------------------------------------------
# Trip Planning & Itinerary Generator
# ---------------------------------------------------------

@router.post("/plan-trip", summary="Generate structured day-by-day travel itinerary with hotel suggestions")
async def plan_trip(
    request: TripPlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = await crud_ai.generate_trip_itinerary(
        db=db,
        destination=request.destination,
        budget=request.budget,
        start_date=request.start_date,
        end_date=request.end_date,
        travel_style=request.travel_style or "balanced",
        preferred_amenities=request.preferred_amenities,
        guests_count=request.guests_count,
        special_preferences=request.special_preferences
    )

    return api_response(
        success=True,
        message="Travel itinerary and hotel suggestions generated successfully",
        data=plan
    )


# ---------------------------------------------------------
# Interactive Conversational Concierge
# ---------------------------------------------------------

@router.post("/chat", summary="Send message to AI Travel Assistant with conversation memory context")
async def chat_with_assistant(
    request: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chat_result = await crud_ai.process_ai_chat_message(
        db=db,
        user_id=current_user.id,
        message_content=request.message,
        conversation_id=request.conversation_id,
        destination=request.destination
    )

    return api_response(
        success=True,
        message="AI assistant response generated",
        data=chat_result
    )


# ---------------------------------------------------------
# Conversation Context History Management
# ---------------------------------------------------------

@router.get("/conversations", summary="Retrieve all past travel assistant conversations for customer")
def get_user_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversations = crud_ai.list_user_conversations(db, current_user.id)
    return api_response(
        success=True,
        message="AI travel conversations retrieved successfully",
        data=[_serialize_conversation(c) for c in conversations]
    )


@router.get("/conversations/{conversation_id}", summary="Retrieve conversation history and messages")
def get_conversation_history(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = crud_ai.get_conversation_with_messages(db, conversation_id, current_user.id)
    return api_response(
        success=True,
        message="Conversation history retrieved successfully",
        data={
            "conversation": _serialize_conversation(conv),
            "messages": [_serialize_message(m) for m in conv.messages]
        }
    )


@router.delete("/conversations/{conversation_id}", summary="Delete conversation and clear context memory")
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    crud_ai.delete_conversation(db, conversation_id, current_user.id)
    return api_response(
        success=True,
        message="Conversation deleted successfully"
    )
