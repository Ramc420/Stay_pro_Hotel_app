import math
from typing import Optional, List, Dict, Any, Set
from sqlalchemy.orm import Session
from sqlalchemy import func

from config import settings
from models.hotel import Hotel, HotelStatus
from models.room import RoomType
from models.booking import Booking, BookingStatus
from models.customer import CustomerProfile
from models.amenity import HotelAmenity, Amenity
from models.review import Review


def _get_hotel_starting_price(db: Session, hotel_id: int) -> float:
    min_price = db.query(func.min(RoomType.base_price_per_night)).filter(
        RoomType.hotel_id == hotel_id,
        RoomType.is_active == True
    ).scalar()
    return float(min_price) if min_price is not None else 100.0


def _get_hotel_amenity_names(db: Session, hotel_id: int) -> List[str]:
    amenities = (
        db.query(Amenity.name)
        .join(HotelAmenity, HotelAmenity.amenity_id == Amenity.id)
        .filter(HotelAmenity.hotel_id == hotel_id)
        .all()
    )
    return [a[0] for a in amenities]


def _get_hotel_primary_image(hotel: Hotel) -> Optional[str]:
    if hotel.images:
        primary = next((img.image_url for img in hotel.images if img.is_primary), None)
        return primary or hotel.images[0].image_url
    return None


def get_similar_hotels(
    db: Session,
    hotel_id: int,
    limit: int = 6
) -> Dict[str, Any]:
    """
    Module 21: Provide similar-hotel recommendations based on property type,
    city, price tier, star rating, and shared amenities.
    """
    target = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not target:
        return {"recommendations": [], "total": 0, "algorithm_applied": "content_similarity", "ai_enhanced": False}

    target_price = _get_hotel_starting_price(db, target.id)
    target_amenities = set(_get_hotel_amenity_names(db, target.id))

    candidates = (
        db.query(Hotel)
        .filter(
            Hotel.id != target.id,
            Hotel.is_approved == True,
            Hotel.is_active == True,
            Hotel.status == HotelStatus.APPROVED
        )
        .all()
    )

    scored_items = []
    for cand in candidates:
        score = 0.0
        reasons = []

        # 1. Location match
        if cand.city.lower() == target.city.lower():
            score += 35.0
            reasons.append(f"Located in same city ({target.city})")
        elif cand.country.lower() == target.country.lower():
            score += 15.0

        # 2. Property type match
        if cand.property_type.lower() == target.property_type.lower():
            score += 25.0
            reasons.append(f"Same property style ({cand.property_type.title()})")

        # 3. Price proximity
        cand_price = _get_hotel_starting_price(db, cand.id)
        price_diff = abs(cand_price - target_price)
        max_price = max(target_price, cand_price, 1.0)
        price_sim = max(0.0, 1.0 - (price_diff / max_price))
        score += price_sim * 20.0
        if price_sim > 0.8:
            reasons.append(f"Comparable pricing (~${cand_price:.0f}/night vs ~${target_price:.0f})")

        # 4. Amenities overlap
        cand_amenities = set(_get_hotel_amenity_names(db, cand.id))
        shared = target_amenities.intersection(cand_amenities)
        if target_amenities:
            jaccard = len(shared) / max(1, len(target_amenities.union(cand_amenities)))
            score += jaccard * 20.0
            if len(shared) >= 2:
                reasons.append(f"Shares key amenities ({', '.join(list(shared)[:3])})")

        # Normalized similarity
        sim_normalized = min(100.0, score)
        match_pct = int(round(sim_normalized))

        scored_items.append({
            "hotel_id": cand.id,
            "name": cand.name,
            "property_type": cand.property_type,
            "star_rating": cand.star_rating,
            "city": cand.city,
            "country": cand.country,
            "starting_price": cand_price,
            "primary_image_url": _get_hotel_primary_image(cand),
            "similarity_score": round(sim_normalized / 100.0, 3),
            "match_percentage": match_pct,
            "recommendation_reasons": reasons or ["Great alternative match"],
            "amenities": list(cand_amenities)[:6]
        })

    # Sort descending
    scored_items.sort(key=lambda x: x["similarity_score"], reverse=True)
    results = scored_items[:limit]

    return {
        "recommendations": results,
        "total": len(results),
        "algorithm_applied": "multi_factor_content_similarity",
        "ai_enhanced": False,
        "context_notes": f"Similar hotel suggestions relative to {target.name}"
    }


def get_budget_and_location_recommendations(
    db: Session,
    city: Optional[str] = None,
    country: Optional[str] = None,
    min_budget: Optional[float] = None,
    max_budget: Optional[float] = None,
    guests_count: int = 1,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Module 21: Generate budget-based and location-based suggestions.
    """
    query = db.query(Hotel).filter(
        Hotel.is_approved == True,
        Hotel.is_active == True,
        Hotel.status == HotelStatus.APPROVED
    )

    if city:
        query = query.filter(Hotel.city.ilike(f"%{city.strip()}%"))
    if country:
        query = query.filter(Hotel.country.ilike(f"%{country.strip()}%"))

    candidates = query.all()
    results = []

    for hotel in candidates:
        starting_price = _get_hotel_starting_price(db, hotel.id)
        amenities = _get_hotel_amenity_names(db, hotel.id)

        # Budget filtering & scoring
        if min_budget is not None and starting_price < min_budget:
            continue
        if max_budget is not None and starting_price > max_budget:
            continue

        reasons = []
        score = 60.0  # Base eligibility score

        if max_budget is not None and starting_price <= max_budget:
            savings = max_budget - starting_price
            reasons.append(f"Fits within your budget (${starting_price:.0f} vs max ${max_budget:.0f})")
            score += min(20.0, (savings / max_budget) * 20.0)

        if hotel.star_rating >= 4.0:
            score += 15.0
            reasons.append(f"High guest satisfaction ({hotel.star_rating}★)")

        if city and hotel.city.lower() == city.lower():
            score += 10.0
            reasons.append(f"Prime location in {hotel.city}")

        results.append({
            "hotel_id": hotel.id,
            "name": hotel.name,
            "property_type": hotel.property_type,
            "star_rating": hotel.star_rating,
            "city": hotel.city,
            "country": hotel.country,
            "starting_price": starting_price,
            "primary_image_url": _get_hotel_primary_image(hotel),
            "similarity_score": round(min(1.0, score / 100.0), 3),
            "match_percentage": int(round(min(100.0, score))),
            "recommendation_reasons": reasons or ["Excellent property match"],
            "amenities": amenities[:6]
        })

    results.sort(key=lambda x: (x["similarity_score"], x["star_rating"]), reverse=True)
    top_items = results[:limit]

    return {
        "recommendations": top_items,
        "total": len(top_items),
        "algorithm_applied": "budget_location_heuristic",
        "ai_enhanced": False,
        "context_notes": f"Suggestions matched for city={city or 'Any'}, budget range={min_budget}-{max_budget}"
    }


def get_personalized_recommendations(
    db: Session,
    user_id: int,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Module 21: Build APIs for personalized hotel recommendations based on:
    - User's previous booking history (cities, property types, average pricing, amenities)
    - Customer profile travel preferences
    - Graceful fallback algorithm when external AI service is unavailable
    """
    # 1. Fetch user past bookings
    user_bookings = (
        db.query(Booking)
        .filter(Booking.user_id == user_id, Booking.status != BookingStatus.CANCELLED)
        .all()
    )

    # 2. Fetch customer profile preferences
    profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == user_id).first()
    prefs = profile.travel_preferences if profile and profile.travel_preferences else {}

    # Extract historical vectors
    visited_cities = [b.hotel.city for b in user_bookings if b.hotel]
    spent_amounts = [b.nightly_price for b in user_bookings if b.nightly_price > 0]
    avg_spent = sum(spent_amounts) / len(spent_amounts) if spent_amounts else None
    preferred_types = [b.hotel.property_type for b in user_bookings if b.hotel]

    # Preference overrides
    fav_destinations = prefs.get("favorite_destinations", [])
    pref_style = prefs.get("travel_style")
    pref_budget = prefs.get("budget_per_night")

    all_hotels = (
        db.query(Hotel)
        .filter(
            Hotel.is_approved == True,
            Hotel.is_active == True,
            Hotel.status == HotelStatus.APPROVED
        )
        .all()
    )

    scored_hotels = []
    for hotel in all_hotels:
        starting_price = _get_hotel_starting_price(db, hotel.id)
        amenities = _get_hotel_amenity_names(db, hotel.id)

        score = 50.0  # Base
        reasons = []

        # City match
        if visited_cities and hotel.city in visited_cities:
            score += 20.0
            reasons.append(f"Based on your previous stays in {hotel.city}")
        elif fav_destinations and any(d.lower() in hotel.city.lower() for d in fav_destinations):
            score += 25.0
            reasons.append(f"Matches your saved preferred destination ({hotel.city})")

        # Price proximity
        ref_price = pref_budget or avg_spent
        if ref_price:
            price_diff = abs(starting_price - ref_price)
            ratio = price_diff / ref_price
            if ratio <= 0.3:
                score += 20.0
                reasons.append(f"Fits your typical nightly preference (~${ref_price:.0f})")
            elif ratio <= 0.6:
                score += 10.0

        # Property type match
        if preferred_types and hotel.property_type in preferred_types:
            score += 15.0
            reasons.append(f"You frequently book {hotel.property_type.title()} properties")

        # Star rating bonus
        if hotel.star_rating >= 4.5:
            score += 15.0
            reasons.append("Top rated customer choice (4.5+ ★)")
        elif hotel.star_rating >= 4.0:
            score += 10.0

        # High amenity count
        if len(amenities) >= 5:
            score += 10.0
            reasons.append("Feature-rich resort with abundant amenities")

        normalized = min(100.0, score)
        scored_hotels.append({
            "hotel_id": hotel.id,
            "name": hotel.name,
            "property_type": hotel.property_type,
            "star_rating": hotel.star_rating,
            "city": hotel.city,
            "country": hotel.country,
            "starting_price": starting_price,
            "primary_image_url": _get_hotel_primary_image(hotel),
            "similarity_score": round(normalized / 100.0, 3),
            "match_percentage": int(round(normalized)),
            "recommendation_reasons": reasons or ["Recommended based on trending popular stays"],
            "amenities": amenities[:6]
        })

    scored_hotels.sort(key=lambda x: (x["similarity_score"], x["star_rating"]), reverse=True)
    top_items = scored_hotels[:limit]

    return {
        "recommendations": top_items,
        "total": len(top_items),
        "algorithm_applied": "personalized_collaborative_and_content_filtering",
        "ai_enhanced": False,
        "context_notes": f"Personalized suggestions generated using {len(user_bookings)} booking records and customer travel profile"
    }
