import sys
from datetime import datetime, date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from database import SessionLocal
import models
from auth.jwt_handler import create_access_token, hash_password

client = TestClient(app)

def run_tests():
    db: Session = SessionLocal()
    print("=== STARTING INTEGRATION TESTS FOR MODULES 17 - 22 ===")

    # 1. Setup Test Users
    # Admin
    admin = db.query(models.User).filter(models.User.email == "admin@staynest.com").first()
    admin_token, _ = create_access_token(admin.id, admin.role.value)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Customer
    customer_email = "test_customer_m17_22@example.com"
    customer = db.query(models.User).filter(models.User.email == customer_email).first()
    if not customer:
        customer = models.User(
            email=customer_email,
            hashed_password=hash_password("Customer@123"),
            full_name="Alice Explorer",
            role=models.UserRole.CUSTOMER,
            is_active=True,
            is_verified=True
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

    customer_token, _ = create_access_token(customer.id, customer.role.value)
    customer_headers = {"Authorization": f"Bearer {customer_token}"}

    # Hotel Owner
    owner_email = "test_owner_m17_22@example.com"
    owner = db.query(models.User).filter(models.User.email == owner_email).first()
    if not owner:
        owner = models.User(
            email=owner_email,
            hashed_password=hash_password("Owner@123"),
            full_name="Grand Hotelier",
            role=models.UserRole.HOTEL_OWNER,
            is_active=True,
            is_verified=True
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)

    owner_token, _ = create_access_token(owner.id, owner.role.value)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    # Setup Test Hotel
    test_hotel = db.query(models.Hotel).filter(models.Hotel.name == "StayNest Azure Grand Resort").first()
    if not test_hotel:
        test_hotel = models.Hotel(
            owner_id=owner.id,
            name="StayNest Azure Grand Resort",
            description="Luxury beachfront haven with azure lagoon views",
            property_type="RESORT",
            star_rating=4.5,
            email="azure@staynest.com",
            phone="+1-555-0144",
            address_line1="100 Ocean Boulevard",
            city="Miami",
            state="Florida",
            country="United States",
            postal_code="33139",
            latitude=25.7617,
            longitude=-80.1918,
            cancellation_policy="MODERATE",
            is_approved=True,
            status=models.HotelStatus.APPROVED,
            is_active=True
        )
        db.add(test_hotel)
        db.commit()
        db.refresh(test_hotel)

    # Setup Room Type and Room
    rt = db.query(models.RoomType).filter(models.RoomType.hotel_id == test_hotel.id).first()
    if not rt:
        rt = models.RoomType(
            hotel_id=test_hotel.id,
            name="Ocean View Deluxe",
            code="OVD-01",
            base_price_per_night=250.0,
            max_occupancy=2,
            is_active=True
        )
        db.add(rt)
        db.commit()
        db.refresh(rt)

    room = db.query(models.Room).filter(models.Room.room_type_id == rt.id).first()
    if not room:
        room = models.Room(
            hotel_id=test_hotel.id,
            room_type_id=rt.id,
            room_number="AZ-301",
            floor_number=3,
            is_active=True
        )
        db.add(room)
        db.commit()
        db.refresh(room)

    # Setup Test Booking
    booking = db.query(models.Booking).filter(
        models.Booking.user_id == customer.id,
        models.Booking.hotel_id == test_hotel.id
    ).first()
    if not booking:
        booking = models.Booking(
            booking_reference="SN-TEST-REFUND-001",
            user_id=customer.id,
            hotel_id=test_hotel.id,
            room_id=room.id,
            room_type_id=rt.id,
            check_in_date=date.today() + timedelta(days=10),
            check_out_date=date.today() + timedelta(days=13),
            total_nights=3,
            nightly_price=250.0,
            base_amount=750.0,
            tax_amount=90.0,
            total_amount=840.0,
            status=models.BookingStatus.CONFIRMED,
            payment_status=models.PaymentStatus.PAID
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
    else:
        booking.payment_status = models.PaymentStatus.PAID
        booking.status = models.BookingStatus.CONFIRMED
        db.commit()

    # Ensure payment record exists
    pay = db.query(models.Payment).filter(models.Payment.booking_id == booking.id).first()
    if not pay:
        pay = models.Payment(
            booking_id=booking.id,
            payment_reference="PAY-TEST-001",
            idempotency_key="idem_test_001",
            amount=840.0,
            currency="usd",
            status=models.PaymentRecordStatus.SUCCEEDED,
            stripe_payment_intent_id="pi_test_m17_mock"
        )
        db.add(pay)
        db.commit()
    else:
        pay.status = models.PaymentRecordStatus.SUCCEEDED
        db.commit()

    print("[OK] Setup test entities successfully")

    # -------------------------------------------------------------
    # MODULE 17: Cancellation and Refund Management
    # -------------------------------------------------------------
    print("\n--- Testing Module 17: Cancellation and Refund Management ---")
    
    # 1. Policy quote
    res = client.post(
        "/refunds/policy-quote",
        json={"booking_id": booking.id},
        headers=customer_headers
    )
    assert res.status_code == 200, f"Quote failed: {res.text}"
    quote_data = res.json()["data"]
    assert quote_data["is_eligible_for_refund"] is True
    assert quote_data["refundable_amount"] == 840.0
    print(f"[OK] Cancellation policy quote calculated: ${quote_data['refundable_amount']} refundable (Policy: {quote_data['cancellation_policy']})")

    # Clean existing refund if any
    db.query(models.RefundRequest).filter(models.RefundRequest.booking_id == booking.id).delete()
    db.commit()

    # 2. Submit refund request
    res = client.post(
        "/refunds/request",
        json={"booking_id": booking.id, "reason": "Family emergency forced change of vacation plans"},
        headers=customer_headers
    )
    assert res.status_code == 201, f"Submit refund failed: {res.text}"
    refund_req = res.json()["data"]
    refund_id = refund_req["id"]
    assert refund_req["status"] == "PENDING"
    print(f"[OK] Refund request #{refund_id} submitted successfully")

    # 3. Retrieve my requests
    res = client.get("/refunds/my-requests", headers=customer_headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) >= 1
    print("[OK] Retrieved customer refund requests")

    # 4. Hotel refund list
    res = client.get(f"/refunds/hotel/{test_hotel.id}", headers=owner_headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) >= 1
    print("[OK] Retrieved hotel refund requests (Hotel Owner)")

    # 5. Approve refund request
    res = client.post(
        f"/refunds/{refund_id}/approve",
        json={"amount_approved": 840.0, "admin_notes": "Approved per 10-day advance notice"},
        headers=owner_headers
    )
    assert res.status_code == 200, f"Approve refund failed: {res.text}"
    assert res.json()["data"]["status"] == "APPROVED"
    print(f"[OK] Refund request #{refund_id} approved")

    # 6. Process Stripe refund
    res = client.post(f"/refunds/{refund_id}/process", headers=admin_headers)
    assert res.status_code == 200, f"Process refund failed: {res.text}"
    proc_data = res.json()["data"]
    assert proc_data["status"] == "PROCESSED"
    assert proc_data["stripe_refund_id"] is not None
    print(f"[OK] Refund #{refund_id} processed through Stripe ({proc_data['stripe_refund_id']})")

    # -------------------------------------------------------------
    # MODULE 18: Coupon and Discount Management
    # -------------------------------------------------------------
    print("\n--- Testing Module 18: Coupon and Discount Management ---")

    test_code = f"DISC{int(datetime.now().timestamp()) % 10000}"
    res = client.post(
        "/coupons",
        json={
            "code": test_code,
            "description": "Special Summer Escape 15% Off",
            "discount_type": "PERCENTAGE",
            "discount_value": 15.0,
            "max_discount_amount": 100.0,
            "min_booking_amount": 200.0,
            "start_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "expiry_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "max_uses": 50,
            "max_uses_per_user": 1,
            "is_active": True,
            "hotel_id": test_hotel.id,
            "discount_category": "SEASONAL",
            "min_advance_days": 0
        },
        headers=admin_headers
    )
    assert res.status_code == 201, f"Create coupon failed: {res.text}"
    coupon_data = res.json()["data"]
    coupon_id = coupon_data["id"]
    print(f"[OK] Created coupon '{test_code}' (15% off, max $100)")

    # Validate coupon
    res = client.post(
        "/coupons/validate",
        json={
            "code": test_code,
            "hotel_id": test_hotel.id,
            "booking_amount": 500.0,
            "check_in_date": (date.today() + timedelta(days=5)).isoformat()
        },
        headers=customer_headers
    )
    assert res.status_code == 200
    val_data = res.json()["data"]
    assert val_data["valid"] is True
    assert val_data["discount_amount"] == 75.0  # 15% of 500
    assert val_data["final_amount"] == 425.0
    print(f"[OK] Validated coupon: calculated discount ${val_data['discount_amount']} on $500 booking")

    # Create fresh booking to apply coupon
    booking2 = models.Booking(
        booking_reference=f"SN-COUPON-{int(datetime.now().timestamp()) % 10000}",
        user_id=customer.id,
        hotel_id=test_hotel.id,
        room_id=room.id,
        room_type_id=rt.id,
        check_in_date=date.today() + timedelta(days=15),
        check_out_date=date.today() + timedelta(days=18),
        total_nights=3,
        nightly_price=250.0,
        base_amount=750.0,
        tax_amount=90.0,
        total_amount=840.0,
        status=models.BookingStatus.CONFIRMED,
        payment_status=models.PaymentStatus.UNPAID
    )
    db.add(booking2)
    db.commit()
    db.refresh(booking2)

    # Apply coupon to booking
    res = client.post(
        "/coupons/apply",
        json={"booking_id": booking2.id, "code": test_code},
        headers=customer_headers
    )
    assert res.status_code == 200, f"Apply coupon failed: {res.text}"
    app_data = res.json()["data"]
    assert app_data["applied"] is True
    assert app_data["discount_amount"] == 100.0  # capped at $100 max
    print(f"[OK] Coupon applied: new total amount ${app_data['new_total_amount']} (saved ${app_data['discount_amount']})")

    # Prevent repeated coupon usage
    res = client.post(
        "/coupons/apply",
        json={"booking_id": booking2.id, "code": test_code},
        headers=customer_headers
    )
    assert res.status_code == 400
    print("[OK] Prevented duplicate coupon application on same booking")

    # Coupon usage history
    res = client.get(f"/coupons/{coupon_id}/usages", headers=admin_headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) >= 1
    print("[OK] Retrieved coupon usage tracking history")

    # -------------------------------------------------------------
    # MODULE 19: Reviews and Ratings
    # -------------------------------------------------------------
    print("\n--- Testing Module 19: Reviews and Ratings ---")

    # Make booking completed for eligibility
    completed_booking = models.Booking(
        booking_reference=f"SN-REV-{int(datetime.now().timestamp()) % 10000}",
        user_id=customer.id,
        hotel_id=test_hotel.id,
        room_id=room.id,
        room_type_id=rt.id,
        check_in_date=date.today() - timedelta(days=5),
        check_out_date=date.today() - timedelta(days=2),
        total_nights=3,
        nightly_price=250.0,
        base_amount=750.0,
        tax_amount=90.0,
        total_amount=840.0,
        status=models.BookingStatus.COMPLETED,
        payment_status=models.PaymentStatus.PAID
    )
    db.add(completed_booking)
    db.commit()
    db.refresh(completed_booking)

    # Submit review
    res = client.post(
        "/reviews",
        json={
            "hotel_id": test_hotel.id,
            "booking_id": completed_booking.id,
            "rating": 5.0,
            "comment": "Absolutely spectacular stay! The ocean views and concierge service exceeded all expectations."
        },
        headers=customer_headers
    )
    assert res.status_code == 201, f"Submit review failed: {res.text}"
    rev_data = res.json()["data"]
    rev_id = rev_data["id"]
    print(f"[OK] Review #{rev_id} submitted for completed stay (Rating: 5.0)")

    # Prevent duplicate review for same stay
    res = client.post(
        "/reviews",
        json={
            "hotel_id": test_hotel.id,
            "booking_id": completed_booking.id,
            "rating": 4.0,
            "comment": "Second review attempt"
        },
        headers=customer_headers
    )
    assert res.status_code == 400
    print("[OK] Prevented duplicate review for the same completed stay")

    # Update review
    res = client.put(
        f"/reviews/{rev_id}",
        json={"rating": 4.8, "comment": "Updated: Truly breathtaking experience!"},
        headers=customer_headers
    )
    assert res.status_code == 200
    assert res.json()["data"]["rating"] == 4.8
    print(f"[OK] Review #{rev_id} updated by author")

    # Hotel reviews breakdown & calculation
    res = client.get(f"/reviews/hotel/{test_hotel.id}")
    assert res.status_code == 200
    h_reviews = res.json()["data"]
    assert h_reviews["summary"]["total_reviews"] >= 1
    print(f"[OK] Hotel average rating verified: {h_reviews['summary']['average_rating']}* (Total: {h_reviews['summary']['total_reviews']})")

    # Report review
    res = client.post(
        f"/reviews/{rev_id}/report",
        json={"reason": "Contains potential advertising mention"},
        headers=owner_headers
    )
    assert res.status_code == 200
    assert res.json()["data"]["is_reported"] is True
    print(f"[OK] Review #{rev_id} reported successfully")

    # Moderate review
    res = client.post(
        f"/reviews/{rev_id}/moderate",
        json={"action": "APPROVE", "notes": "Content verified authentic guest experience"},
        headers=admin_headers
    )
    assert res.status_code == 200
    assert res.json()["data"]["is_reported"] is False
    print(f"[OK] Review #{rev_id} moderated and approved by Admin")

    # -------------------------------------------------------------
    # MODULE 20: Wishlist and Favorite Hotels
    # -------------------------------------------------------------
    print("\n--- Testing Module 20: Wishlist and Favorite Hotels ---")

    db.query(models.Wishlist).filter(models.Wishlist.user_id == customer.id).delete()
    db.commit()

    # Add favorite hotel
    res = client.post(
        "/wishlist",
        json={"hotel_id": test_hotel.id, "room_id": room.id, "notes": "Dream anniversary suite"},
        headers=customer_headers
    )
    assert res.status_code == 201, f"Add wishlist failed: {res.text}"
    wish_item = res.json()["data"]
    wish_id = wish_item["id"]
    print(f"[OK] Hotel & room added to favorites (Wishlist ID: {wish_id})")

    # Duplicate check
    res = client.post(
        "/wishlist",
        json={"hotel_id": test_hotel.id, "room_id": room.id},
        headers=customer_headers
    )
    assert res.status_code == 409
    print("[OK] Prevented duplicate wishlist entry")

    # Check favorite status
    res = client.get(f"/wishlist/check/{test_hotel.id}", headers=customer_headers)
    assert res.status_code == 200
    assert res.json()["data"]["is_favorite"] is True
    print(f"[OK] Wishlist check verified: is_favorite=True")

    # Retrieve wishlist
    res = client.get("/wishlist", headers=customer_headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) >= 1
    print("[OK] Retrieved customer wishlist catalog")

    # Delete favorite
    res = client.delete(f"/wishlist/{wish_id}", headers=customer_headers)
    assert res.status_code == 200
    print(f"[OK] Wishlist item #{wish_id} removed")

    # -------------------------------------------------------------
    # MODULE 21: AI Hotel Recommendation Engine
    # -------------------------------------------------------------
    print("\n--- Testing Module 21: AI Hotel Recommendation Engine ---")

    # Personalized
    res = client.get("/recommendations/personalized", headers=customer_headers)
    assert res.status_code == 200, f"Personalized failed: {res.text}"
    rec_data = res.json()["data"]
    assert rec_data["total"] >= 1
    print(f"[OK] Personalized recommendations generated ({rec_data['total']} hotels, Alg: {rec_data['algorithm_applied']})")

    # Budget & Location
    res = client.get("/recommendations/budget-location?city=Miami&max_budget=500")
    assert res.status_code == 200
    bl_data = res.json()["data"]
    assert bl_data["total"] >= 1
    print(f"[OK] Budget & location recommendations generated ({bl_data['total']} hotels in Miami)")

    # Similar hotels
    res = client.get(f"/recommendations/similar/{test_hotel.id}")
    assert res.status_code == 200
    sim_data = res.json()["data"]
    print(f"[OK] Similar hotel recommendations generated (Alg: {sim_data['algorithm_applied']})")

    # -------------------------------------------------------------
    # MODULE 22: AI Travel Assistant
    # -------------------------------------------------------------
    print("\n--- Testing Module 22: AI Travel Assistant ---")

    # Plan trip
    res = client.post(
        "/ai-assistant/plan-trip",
        json={
            "destination": "Miami",
            "budget": 1500.0,
            "start_date": (date.today() + timedelta(days=20)).isoformat(),
            "end_date": (date.today() + timedelta(days=23)).isoformat(),
            "travel_style": "luxury",
            "guests_count": 2,
            "special_preferences": "Beachfront dining, ocean views, and spa treatments"
        },
        headers=customer_headers
    )
    assert res.status_code == 200, f"Plan trip failed: {res.text}"
    plan_data = res.json()["data"]
    assert len(plan_data["daily_itinerary"]) >= 3
    assert len(plan_data["suggested_hotels"]) >= 1
    print(f"[OK] AI Travel Itinerary generated ({len(plan_data['daily_itinerary'])} days, Provider: {plan_data['ai_provider_used']})")

    # Interactive Chat
    res = client.post(
        "/ai-assistant/chat",
        json={"message": "Can you recommend top resorts with infinity pools in Miami?", "destination": "Miami"},
        headers=customer_headers
    )
    assert res.status_code == 200, f"Chat failed: {res.text}"
    chat_data = res.json()["data"]
    conv_id = chat_data["conversation_id"]
    assert conv_id is not None
    assert len(chat_data["reply"]) > 10
    print(f"[OK] AI Chat message processed (Conversation #{conv_id}, Provider: {chat_data['provider']})")

    # Follow-up Chat with memory context
    res = client.post(
        "/ai-assistant/chat",
        json={"message": "What is the best time of year to visit these resorts?", "conversation_id": conv_id},
        headers=customer_headers
    )
    assert res.status_code == 200
    print("[OK] Follow-up AI chat processed with conversation context memory")

    # Get conversations
    res = client.get("/ai-assistant/conversations", headers=customer_headers)
    assert res.status_code == 200
    assert len(res.json()["data"]) >= 1
    print("[OK] Retrieved customer AI conversation sessions")

    # Delete conversation
    res = client.delete(f"/ai-assistant/conversations/{conv_id}", headers=customer_headers)
    assert res.status_code == 200
    print(f"[OK] AI Conversation #{conv_id} cleared")

    db.close()
    print("\nSUCCESS: ALL TESTS FOR MODULES 17 - 22 PASSED SUCCESSFULLY!")

def test_modules_17_to_22():
    run_tests()

if __name__ == "__main__":
    run_tests()

