import sys
import uuid
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
    print("=== STARTING INTEGRATION TESTS FOR MODULES 1 - 16 ===")

    # 1. Setup Admin Token
    admin = db.query(models.User).filter(models.User.email == "admin@staynest.com").first()
    if not admin:
        admin = models.User(
            email="admin@staynest.com",
            hashed_password=hash_password("Admin@123456"),
            full_name="StayNest System Administrator",
            role=models.UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    admin_token, _ = create_access_token(admin.id, admin.role.value)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    uid = uuid.uuid4().hex[:6]
    customer_email = f"cust_{uid}@testnest.com"
    owner_email = f"owner_{uid}@testnest.com"

    # =========================================================================
    # MODULE 1: User Registration and Authentication
    # =========================================================================
    print("\n--- Testing Module 1: User Registration & Authentication ---")
    
    # 1. Register Customer
    reg_resp = client.post("/auth/register", json={
        "email": customer_email,
        "password": "SecurePassword@123",
        "full_name": "Test Customer",
        "phone_number": "+1234567890",
        "role": "CUSTOMER"
    })
    assert reg_resp.status_code == 201, reg_resp.text
    reg_data = reg_resp.json()["data"]
    customer_id = reg_data["user"]["id"]
    customer_token = reg_data["tokens"]["access_token"]
    refresh_token = reg_data["tokens"]["refresh_token"]
    v_token = reg_data["user"]["verification_token"]
    customer_headers = {"Authorization": f"Bearer {customer_token}"}
    print(f"[OK] Customer registered successfully (ID: {customer_id})")

    # 2. Duplicate registration rejected
    dup_resp = client.post("/auth/register", json={
        "email": customer_email,
        "password": "Password123!",
        "full_name": "Duplicate User",
        "role": "CUSTOMER"
    })
    assert dup_resp.status_code == 400
    print("[OK] Duplicate email registration correctly prevented")

    # 3. Login
    login_resp = client.post("/auth/login", json={
        "email": customer_email,
        "password": "SecurePassword@123"
    })
    assert login_resp.status_code == 200
    print("[OK] User login successful")

    # 4. Refresh token
    refresh_resp = client.post("/auth/refresh-token", json={
        "refresh_token": refresh_token
    })
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()["data"]
    print("[OK] Access token refreshed successfully")

    # 5. Get current user profile
    me_resp = client.get("/auth/me", headers=customer_headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["email"] == customer_email
    print("[OK] Current authenticated user retrieved")

    # =========================================================================
    # MODULE 2: Password Reset & Email Verification
    # =========================================================================
    print("\n--- Testing Module 2: Password Reset & Email Verification ---")

    # 1. Verify Email
    ver_resp = client.post("/auth/verify-email", json={
        "token": v_token
    })
    assert ver_resp.status_code == 200
    print("[OK] Email verification verified")

    # 2. Forgot Password Request
    forgot_resp = client.post("/auth/forgot-password", json={
        "email": customer_email
    })
    assert forgot_resp.status_code == 200
    reset_token = forgot_resp.json()["data"]["reset_token"]
    print("[OK] Forgot password token generated")

    # 3. Reset Password
    reset_resp = client.post("/auth/reset-password", json={
        "token": reset_token,
        "new_password": "NewSecurePassword@123"
    })
    assert reset_resp.status_code == 200
    print("[OK] Password reset completed successfully")

    # 4. Login with new password
    login_resp2 = client.post("/auth/login", json={
        "email": customer_email,
        "password": "NewSecurePassword@123"
    })
    assert login_resp2.status_code == 200
    customer_token = login_resp2.json()["data"]["tokens"]["access_token"]
    customer_headers = {"Authorization": f"Bearer {customer_token}"}
    print("[OK] Login with new password confirmed")

    # =========================================================================
    # MODULE 3: Customer Profile Management
    # =========================================================================
    print("\n--- Testing Module 3: Customer Profile Management ---")

    profile_resp = client.get("/customers/profile/me", headers=customer_headers)
    assert profile_resp.status_code == 200
    print("[OK] Retrieved customer profile")

    update_prof = client.put("/customers/profile/me", json={
        "city": "San Francisco",
        "country": "USA",
        "emergency_contact_name": "Bob Friend",
        "travel_preferences": {"room_floor": "high", "bed": "king"}
    }, headers=customer_headers)
    assert update_prof.status_code == 200
    assert update_prof.json()["data"]["city"] == "San Francisco"
    print("[OK] Updated customer profile preferences")

    # =========================================================================
    # Register Hotel Owner for hotel tests
    # =========================================================================
    owner_reg = client.post("/auth/register", json={
        "email": owner_email,
        "password": "OwnerPassword@123",
        "full_name": "Hotelier Alice",
        "phone_number": "+1987654321",
        "role": "HOTEL_OWNER"
    })
    assert owner_reg.status_code == 201
    owner_data = owner_reg.json()["data"]
    owner_id = owner_data["user"]["id"]
    owner_token = owner_data["tokens"]["access_token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    print(f"[OK] Hotel Owner registered (ID: {owner_id})")

    # =========================================================================
    # MODULE 4: Hotel Registration and Verification
    # =========================================================================
    print("\n--- Testing Module 4: Hotel Registration & Verification ---")

    hotel_reg = client.post("/hotels/verification/register", json={
        "name": f"StayNest Palm Oasis {uid}",
        "description": "Luxury 5-star beachfront boutique resort",
        "property_type": "RESORT",
        "email": f"oasis_{uid}@palmoasis.com",
        "phone": "+1-808-555-0100",
        "address_line1": "777 Beach Boulevard",
        "city": "Honolulu",
        "state": "Hawaii",
        "country": "USA",
        "postal_code": "96815",
        "latitude": 21.2780,
        "longitude": -157.8280,
        "check_in_time": "15:00",
        "check_out_time": "11:00",
        "cancellation_policy": "MODERATE"
    }, headers=owner_headers)
    assert hotel_reg.status_code in [200, 201], hotel_reg.text
    hotel_id = hotel_reg.json()["data"]["id"]
    print(f"[OK] Hotel registered (ID: {hotel_id}, Status: PENDING_APPROVAL)")

    # Admin approves hotel
    appr_resp = client.post(f"/hotels/verification/{hotel_id}/moderation", json={
        "status": "APPROVED",
        "comments": "All business licenses verified"
    }, headers=admin_headers)
    assert appr_resp.status_code == 200
    assert appr_resp.json()["data"]["is_approved"] is True
    print(f"[OK] Admin approved Hotel #{hotel_id}")

    # =========================================================================
    # MODULE 5: Hotel Profile Management
    # =========================================================================
    print("\n--- Testing Module 5: Hotel Profile Management ---")

    hotel_get = client.get(f"/hotels/{hotel_id}")
    assert hotel_get.status_code == 200
    assert hotel_get.json()["data"]["name"] == f"StayNest Palm Oasis {uid}"
    print(f"[OK] Retrieved Hotel #{hotel_id} public profile")

    hotel_upd = client.put(f"/hotels/{hotel_id}", json={
        "house_rules": "No smoking, pets allowed upon request"
    }, headers=owner_headers)
    assert hotel_upd.status_code == 200
    print(f"[OK] Hotel owner updated house rules")

    # =========================================================================
    # MODULE 6: Room Type Management
    # =========================================================================
    print("\n--- Testing Module 6: Room Type Management ---")

    rt_resp = client.post("/room-types", json={
        "hotel_id": hotel_id,
        "name": "Deluxe Ocean View",
        "code": f"DOV_{uid}",
        "description": "Spacious oceanfront king bedroom with private balcony",
        "base_price_per_night": 250.0,
        "max_occupancy": 3,
        "max_adults": 2,
        "max_children": 1,
        "bed_type": "KING",
        "number_of_beds": 1,
        "room_size_sqm": 45.0
    }, headers=owner_headers)
    assert rt_resp.status_code == 201, rt_resp.text
    room_type_id = rt_resp.json()["data"]["id"]
    print(f"[OK] Created Room Type 'Deluxe Ocean View' (ID: {room_type_id})")

    rt_list = client.get(f"/room-types/hotel/{hotel_id}")
    assert rt_list.status_code == 200
    assert len(rt_list.json()["data"]) >= 1
    print(f"[OK] Listed room types for Hotel #{hotel_id}")

    # =========================================================================
    # MODULE 7: Room Inventory Management
    # =========================================================================
    print("\n--- Testing Module 7: Room Inventory Management ---")

    room_resp = client.post("/rooms", json={
        "hotel_id": hotel_id,
        "room_type_id": room_type_id,
        "room_number": f"101-{uid}",
        "floor_number": 1,
        "is_active": True
    }, headers=owner_headers)
    assert room_resp.status_code == 201, room_resp.text
    room_id = room_resp.json()["data"]["id"]
    print(f"[OK] Room #{room_id} (Number 101-{uid}) created")

    # Create second room for availability test
    room_resp2 = client.post("/rooms", json={
        "hotel_id": hotel_id,
        "room_type_id": room_type_id,
        "room_number": f"102-{uid}",
        "floor_number": 1,
        "is_active": True
    }, headers=owner_headers)
    assert room_resp2.status_code == 201
    room_id2 = room_resp2.json()["data"]["id"]
    print(f"[OK] Second Room #{room_id2} created")

    # =========================================================================
    # MODULE 8: Hotel Amenities Management
    # =========================================================================
    print("\n--- Testing Module 8: Hotel Amenities Management ---")

    amenities_all = client.get("/amenities")
    assert amenities_all.status_code == 200
    amenity_items = amenities_all.json()["data"]
    assert len(amenity_items) >= 1
    first_amenity_id = amenity_items[0]["id"]
    print(f"[OK] Retrieved {len(amenity_items)} platform amenities")

    # Attach amenity to hotel
    attach_resp = client.post(f"/amenities/hotel/{hotel_id}/associate", json={
        "amenity_ids": [first_amenity_id]
    }, headers=owner_headers)
    assert attach_resp.status_code == 200
    print(f"[OK] Attached amenity #{first_amenity_id} to Hotel #{hotel_id}")

    # =========================================================================
    # MODULE 9: Room Availability Management
    # =========================================================================
    print("\n--- Testing Module 9: Room Availability Management ---")

    today = date.today()
    check_in = today + timedelta(days=5)
    check_out = today + timedelta(days=8)

    avail_resp = client.get(
        f"/availability/room/{room_id}?start_date={check_in.isoformat()}&end_date={check_out.isoformat()}"
    )
    assert avail_resp.status_code == 200
    print(f"[OK] Checked daily availability calendar for Room #{room_id}")

    # =========================================================================
    # MODULE 10: Hotel Search System
    # =========================================================================
    print("\n--- Testing Module 10: Hotel Search System ---")

    search_resp = client.get(f"/search/hotels?q=Honolulu")
    assert search_resp.status_code == 200
    search_data = search_resp.json()["data"]
    assert any(h["id"] == hotel_id for h in search_data)
    print(f"[OK] Search query 'Honolulu' matched Hotel #{hotel_id}")

    # =========================================================================
    # MODULE 11: Advanced Hotel Filters
    # =========================================================================
    print("\n--- Testing Module 11: Advanced Hotel Filters ---")

    filter_resp = client.get(f"/filters/hotels?city=Honolulu&property_type=RESORT")
    assert filter_resp.status_code == 200
    filter_data = filter_resp.json()["data"]
    assert any(h["id"] == hotel_id for h in filter_data)
    print(f"[OK] Multi-criteria filter (city=Honolulu, property_type=RESORT) verified")

    # =========================================================================
    # MODULE 12: Hotel Details & Gallery
    # =========================================================================
    print("\n--- Testing Module 12: Hotel Details & Gallery ---")

    details_resp = client.get(f"/hotels/{hotel_id}/details")
    assert details_resp.status_code == 200
    details_data = details_resp.json()["data"]
    assert details_data["hotel"]["id"] == hotel_id
    assert len(details_data["room_types"]) >= 1
    print(f"[OK] Comprehensive hotel details and gallery retrieved")

    # =========================================================================
    # MODULE 13: Booking Reservation Engine & Conflict Prevention
    # =========================================================================
    print("\n--- Testing Module 13: Booking Engine & Conflict Prevention ---")

    # 1. Create reservation
    booking_resp = client.post("/bookings", json={
        "hotel_id": hotel_id,
        "room_id": room_id,
        "room_type_id": room_type_id,
        "check_in_date": check_in.isoformat(),
        "check_out_date": check_out.isoformat(),
        "special_requests": "Quiet room facing the ocean",
        "guests": [
            {
                "full_name": "Test Customer",
                "email": customer_email,
                "phone": "+1234567890",
                "is_primary": True
            }
        ]
    }, headers=customer_headers)
    assert booking_resp.status_code == 201, booking_resp.text
    booking_data = booking_resp.json()["data"]
    booking_id = booking_data["id"]
    booking_ref = booking_data["booking_reference"]
    total_amount = booking_data["total_amount"]
    print(f"[OK] Reservation created successfully: Ref {booking_ref}, Amount ${total_amount}")

    # 2. Conflict prevention: Attempt double-booking exact same dates & room
    dup_booking = client.post("/bookings", json={
        "hotel_id": hotel_id,
        "room_id": room_id,
        "room_type_id": room_type_id,
        "check_in_date": check_in.isoformat(),
        "check_out_date": check_out.isoformat(),
        "guests": [
            {"full_name": "Conflict Person", "email": "other@test.com", "is_primary": True}
        ]
    }, headers=customer_headers)
    assert dup_booking.status_code == 400
    print("[OK] Conflicting reservation strictly prevented (400 Bad Request)")

    # 3. Customer views their bookings
    my_bookings = client.get("/bookings/my", headers=customer_headers)
    assert my_bookings.status_code == 200
    assert any(b["id"] == booking_id for b in my_bookings.json()["data"])
    print(f"[OK] Customer retrieved their active bookings list")

    # =========================================================================
    # MODULE 14: Booking Guest Management
    # =========================================================================
    print("\n--- Testing Module 14: Booking Guest Management ---")

    guest_add = client.post(f"/bookings/{booking_id}/guests", json={
        "full_name": "Second Guest",
        "email": "guest2@test.com",
        "phone": "+1999888777",
        "is_primary": False
    }, headers=customer_headers)
    assert guest_add.status_code == 201
    print(f"[OK] Added secondary guest to reservation #{booking_id}")

    guests_list = client.get(f"/bookings/{booking_id}/guests", headers=customer_headers)
    assert guests_list.status_code == 200
    assert len(guests_list.json()["data"]) >= 2
    print(f"[OK] Retrieved guest roster ({len(guests_list.json()['data'])} guests)")

    # =========================================================================
    # MODULE 15: Stripe Payment Integration & Idempotency
    # =========================================================================
    print("\n--- Testing Module 15: Stripe Payment Integration & Idempotency ---")

    idemp_key = f"idemp_{booking_id}_{uid}"
    pay_sess = client.post("/payments/create-checkout-session", json={
        "booking_id": booking_id,
        "idempotency_key": idemp_key
    }, headers=customer_headers)
    assert pay_sess.status_code in [200, 201], pay_sess.text
    session_data = pay_sess.json()["data"]
    stripe_session_id = session_data["session_id"]
    print(f"[OK] Initialized Stripe Checkout Session: {stripe_session_id}")

    # Idempotent retry: Re-sending exact same idempotency_key returns cached session
    pay_sess_retry = client.post("/payments/create-checkout-session", json={
        "booking_id": booking_id,
        "idempotency_key": idemp_key
    }, headers=customer_headers)
    assert pay_sess_retry.status_code == 200
    assert pay_sess_retry.json()["data"]["session_id"] == stripe_session_id
    print("[OK] Payment idempotency verified: Duplicate session creation prevented")

    # Confirm payment
    pay_confirm = client.post("/payments/confirm", json={
        "booking_id": booking_id,
        "payment_intent_id": f"pi_test_{uid}",
        "idempotency_key": f"confirm_{uid}"
    }, headers=customer_headers)
    assert pay_confirm.status_code == 200
    assert pay_confirm.json()["data"]["status"] == "SUCCEEDED"
    print(f"[OK] Payment confirmed successfully: Status SUCCEEDED")

    # Webhook handler test
    webhook_resp = client.post("/payments/webhook", json={
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "client_reference_id": str(booking_id),
                "id": f"pi_test_{uid}"
            }
        }
    })
    assert webhook_resp.status_code == 200
    print("[OK] Stripe webhook event processed safely")

    # =========================================================================
    # MODULE 16: Invoice & Receipt Management
    # =========================================================================
    print("\n--- Testing Module 16: Invoice & Receipt Management ---")

    inv_resp = client.get(f"/invoices/booking/{booking_id}", headers=customer_headers)
    assert inv_resp.status_code == 200
    inv_data = inv_resp.json()["data"]
    inv_id = inv_data["id"]
    inv_num = inv_data["invoice_number"]
    print(f"[OK] Invoice #{inv_num} (ID: {inv_id}) retrieved for booking #{booking_id}")

    # View printable receipt HTML
    receipt_resp = client.get(f"/invoices/{inv_id}/pdf", headers=customer_headers)
    assert receipt_resp.status_code == 200
    assert "StayNest Pro" in receipt_resp.text
    print(f"[OK] Printable receipt rendered successfully")

    print("\nSUCCESS: ALL TESTS FOR MODULES 1 - 16 PASSED WITH 100% SUCCESS!")
    db.close()

def test_modules_1_to_16():
    run_tests()

if __name__ == "__main__":
    run_tests()
