import json
import httpx
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from config import settings
from models.ai_assistant import AIConversation, AIMessage
from models.hotel import Hotel, HotelStatus
from models.room import RoomType
from crud.recommendation import _get_hotel_starting_price, _get_hotel_primary_image, _get_hotel_amenity_names


async def _call_external_ai_provider(prompt: str, system_prompt: str = "") -> Optional[str]:
    """
    Attempts to invoke configured external AI provider (Gemini or OpenAI).
    Returns None if neither is configured or if the external call fails, allowing
    seamless fallback to the built-in intelligent travel engine.
    """
    # 1. Gemini Provider
    if settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("dummy"):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{prompt}"}]}
                ]
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text")
                        if text:
                            return text
        except Exception:
            pass

    # 2. OpenAI Provider
    if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("dummy"):
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            payload = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.7
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content")
                        if content:
                            return content
        except Exception:
            pass

    return None


def _find_candidate_hotels_for_destination(
    db: Session,
    destination: str,
    max_budget: Optional[float] = None,
    limit: int = 4
) -> List[Dict[str, Any]]:
    query = db.query(Hotel).filter(
        Hotel.is_approved == True,
        Hotel.is_active == True,
        Hotel.status == HotelStatus.APPROVED
    )

    clean_dest = destination.strip().lower()
    matching_hotels = query.filter(
        (Hotel.city.ilike(f"%{clean_dest}%")) |
        (Hotel.country.ilike(f"%{clean_dest}%")) |
        (Hotel.state.ilike(f"%{clean_dest}%")) |
        (Hotel.name.ilike(f"%{clean_dest}%"))
    ).all()

    # Fallback to top approved hotels if destination has no exact match in DB
    if not matching_hotels:
        matching_hotels = query.order_by(Hotel.star_rating.desc()).limit(limit).all()

    results = []
    for h in matching_hotels:
        price = _get_hotel_starting_price(db, h.id)
        if max_budget is not None and price > max_budget:
            continue
        results.append({
            "hotel_id": h.id,
            "name": h.name,
            "city": h.city,
            "country": h.country,
            "property_type": h.property_type,
            "star_rating": h.star_rating,
            "nightly_rate": price,
            "primary_image": _get_hotel_primary_image(h),
            "amenities": _get_hotel_amenity_names(db, h.id)[:4]
        })

    return results[:limit]


async def generate_trip_itinerary(
    db: Session,
    destination: str,
    budget: Optional[float] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    travel_style: str = "balanced",
    preferred_amenities: Optional[List[str]] = None,
    guests_count: int = 1,
    special_preferences: Optional[str] = None
) -> Dict[str, Any]:
    """
    Module 22: Generates complete trip plan with daily itinerary, hotel matches, and travel tips.
    """
    days = 3
    if start_date and end_date:
        delta = (end_date - start_date).days
        if delta > 0:
            days = min(7, max(1, delta))

    matched_hotels = _find_candidate_hotels_for_destination(db, destination, max_budget=budget)

    # 1. Try external AI provider
    system_prompt = (
        "You are an expert, world-class travel planner for StayNest Pro. "
        "Create an inspiring, practical, day-by-day travel plan. Be engaging, clear, and culturally insightful."
    )
    user_prompt = (
        f"Plan a {days}-day trip to {destination}. Style: {travel_style}. "
        f"Budget: ${budget if budget else 'flexible'}. Travelers: {guests_count}. "
        f"Special requests: {special_preferences or 'None'}."
    )

    ai_provider = "StayNest Intelligent Travel Engine (Built-in)"
    external_text = await _call_external_ai_provider(user_prompt, system_prompt)
    if external_text:
        ai_provider = "External LLM Provider (Connected)"

    # Construct rich, structured daily itinerary
    daily_items = []
    itinerary_themes = [
        {"title": f"Arrival & Discovery of {destination}", "morning": "Arrive, transfer to your hotel, settle in, and unwind.", "afternoon": f"Take a relaxed stroll around central {destination} and explore historical landmarks.", "evening": "Welcome dinner featuring authentic regional cuisine and lively evening atmosphere."},
        {"title": "Cultural Icons & Hidden Gems", "morning": "Visit premier architectural marvels, heritage museums, and local artisan markets.", "afternoon": "Scenic waterfront or viewpoint tour, followed by afternoon tea or coffee tasting.", "evening": "Rooftop dining or live music venue overlooking the illuminated city skyline."},
        {"title": "Nature, Adventure & Coastal Escapes", "morning": "Early morning nature excursion, botanical garden stroll, or hiking trail.", "afternoon": "Leisurely lunch at a waterfront terrace, followed by boutique shopping.", "evening": "Sunset cruise or panoramic dinner reservation."},
        {"title": "Local Flavors & Culinary Exploration", "morning": "Interactive morning cooking masterclass or food market walking tour.", "afternoon": "Art gallery district exploration and souvenir discovery.", "evening": "Celebratory gourmet dinner at a top-reviewed local restaurant."},
        {"title": "Relaxation & Wellness Retreat", "morning": "Morning spa therapy, yoga session, or tranquil beach walk.", "afternoon": "Scenic vineyard or tea estate countryside excursion.", "evening": "Candlelight al-fresco dining experience."},
        {"title": "High Energy & Urban Vibrance", "morning": "Modern architecture tour and bustling shopping avenues.", "afternoon": "Interactive science center, theme pavilion, or cultural quarter.", "evening": "Theater performance, night bazaar, and craft cocktails."},
        {"title": "Farewell Memories & Departure", "morning": "Morning breakfast at hotel, final photography walk, and souvenir shopping.", "afternoon": "Packing and hotel check-out assistance.", "evening": "Airport transfer and pleasant return journey."}
    ]

    for d in range(1, days + 1):
        theme = itinerary_themes[(d - 1) % len(itinerary_themes)]
        daily_items.append({
            "day": d,
            "title": f"Day {d}: {theme['title']}",
            "morning": theme["morning"],
            "afternoon": theme["afternoon"],
            "evening": theme["evening"],
            "recommended_dining": [f"Bistro {destination}", f"{destination} Royal Kitchen", "The Artisan Café"],
            "local_tip": f"Book top attractions online in advance to skip ticket queues in {destination}."
        })

    summary = (
        f"A customized {days}-day {travel_style} adventure in {destination}. "
        f"Designed for {guests_count} traveler(s) with tailored accommodations and authentic experiences."
    )
    if external_text:
        summary = f"{summary}\n\nAI Insights: {external_text[:280]}..."

    packing_tips = [
        f"Check local seasonal weather in {destination} before packing layers.",
        "Comfortable walking shoes are essential for cobblestone streets and heritage walks.",
        "Keep digital and printed copies of hotel reservation vouchers and IDs.",
        "Carry a universal travel plug adapter and portable power bank."
    ]

    return {
        "destination": destination,
        "duration_days": days,
        "travel_style": travel_style,
        "estimated_budget": budget,
        "trip_summary": summary,
        "daily_itinerary": daily_items,
        "suggested_hotels": matched_hotels,
        "packing_and_travel_tips": packing_tips,
        "ai_provider_used": ai_provider
    }


async def process_ai_chat_message(
    db: Session,
    user_id: int,
    message_content: str,
    conversation_id: Optional[int] = None,
    destination: Optional[str] = None
) -> Dict[str, Any]:
    """
    Module 22: Interactive conversational travel assistant with context memory.
    """
    conversation = None
    if conversation_id:
        conversation = db.query(AIConversation).filter(
            AIConversation.id == conversation_id,
            AIConversation.user_id == user_id
        ).first()

    if not conversation:
        title = message_content[:40] + ("..." if len(message_content) > 40 else "")
        conversation = AIConversation(
            user_id=user_id,
            title=title,
            destination=destination
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Save user message
    user_msg = AIMessage(
        conversation_id=conversation.id,
        role="user",
        content=message_content
    )
    db.add(user_msg)
    db.commit()

    # Load prior conversation context
    past_messages = (
        db.query(AIMessage)
        .filter(AIMessage.conversation_id == conversation.id)
        .order_by(AIMessage.created_at.asc())
        .limit(10)
        .all()
    )

    # Match hotels if destination mentioned or stored
    dest = destination or conversation.destination or "Paris"
    for word in message_content.split():
        clean_word = word.strip(",.!?")
        if len(clean_word) > 3:
            h_match = db.query(Hotel).filter(Hotel.city.ilike(f"%{clean_word}%")).first()
            if h_match:
                dest = h_match.city
                conversation.destination = dest
                db.commit()
                break

    matched_hotels = _find_candidate_hotels_for_destination(db, dest, limit=3)

    # Build prompt
    system_prompt = (
        "You are the StayNest Pro AI Travel Concierge. You give friendly, expert recommendations, "
        "highlight hotel options, and propose exciting itineraries."
    )
    history_context = "\n".join([f"{m.role}: {m.content}" for m in past_messages[-4:]])
    prompt = f"Context:\n{history_context}\n\nUser Question: {message_content}"

    external_reply = await _call_external_ai_provider(prompt, system_prompt)

    provider_name = "StayNest Intelligent Concierge"
    if external_reply:
        reply_text = external_reply
        provider_name = "External LLM Provider"
    else:
        # High quality built-in assistant response
        reply_text = (
            f"Hello! I'd be delighted to assist with your travel inquiries regarding {dest}. "
            f"I have reviewed our hand-picked collection of hotels and properties in this area. "
            f"Here are top-tier recommendations that guarantee outstanding comfort, verified reviews, and prime access to local highlights. "
            f"Feel free to ask me for custom day-by-day itineraries, packing checklists, or budget optimization tips!"
        )

    # Save assistant message
    itinerary_preview = {
        "focus_destination": dest,
        "recommended_activities": ["Historic center walking tour", "Gourmet dining experience", "Sunset viewpoint"]
    }
    assistant_msg = AIMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=reply_text,
        suggested_hotels=matched_hotels,
        itinerary_data=itinerary_preview
    )
    db.add(assistant_msg)
    conversation.updated_at = datetime.now()
    db.commit()
    db.refresh(assistant_msg)

    return {
        "conversation_id": conversation.id,
        "conversation_title": conversation.title,
        "reply": reply_text,
        "suggested_hotels": matched_hotels,
        "itinerary_data": itinerary_preview,
        "provider": provider_name
    }


def list_user_conversations(db: Session, user_id: int) -> List[AIConversation]:
    return (
        db.query(AIConversation)
        .filter(AIConversation.user_id == user_id)
        .order_by(AIConversation.updated_at.desc())
        .all()
    )


def get_conversation_with_messages(db: Session, conversation_id: int, user_id: int) -> AIConversation:
    conv = (
        db.query(AIConversation)
        .filter(AIConversation.id == conversation_id, AIConversation.user_id == user_id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv


def delete_conversation(db: Session, conversation_id: int, user_id: int) -> bool:
    conv = (
        db.query(AIConversation)
        .filter(AIConversation.id == conversation_id, AIConversation.user_id == user_id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    db.delete(conv)
    db.commit()
    return True
