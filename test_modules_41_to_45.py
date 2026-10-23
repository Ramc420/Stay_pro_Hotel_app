"""
Comprehensive Integration Test Suite for Modules 41 - 45:
- Module 41: Hotel Subscription Payments
- Module 42: Dynamic Pricing Management
- Module 43: Loyalty and Rewards
- Module 44: Location Services
- Module 45: Calendar and Booking Scheduler
"""
import sys
import uuid
from datetime import datetime, date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from database import SessionLocal
import models
from auth.jwt_handler import create_access_token, hash_password
import crud

client = TestClient(app)


def run_tests():
    db: Session = SessionLocal()
    print("=== STARTING INTEGRATION TESTS FOR MODULES 41 - 45 ===")

    # 0. Seed subscription plans
    crud.subscriptions.seed_default_plans(db)

    # 1. Setup Test Users
    # Admin
    admin = db.query(models.User).filter(models.User.email == "admin@staynest.com").first()
    if not admin:
        admin = models.User(
            email="admin@staynest.com",
            hashed_password=hash_password("Admin@123456"),
            full_name="System Admin",
            role=models.UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    admin_token, _ = create_access_token(admin.id, admin.role.value)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Customer 1 (Referrer)
    suffix = uuid.uuid4().hex[:6]
    customer1 = models.User(
        email=f"cust1_m41_{suffix}@example.com",
        hashed_password=hash_password("Cust1@123"),
        full_name="Alice Traveler",
        role=models.UserRole.CUSTOMER,
        is_active=True,
        is_verified=True
    )
    # Customer 2 (Referee)
    customer2 = models.User(
        email=f"cust2_m41_{suffix}@example.com",
        hashed_password=hash_password("Cust2@123"),
        full_name="Bob Newcomer",
        role=models.UserRole.CUSTOMER,
        is_active=True,
        is_verified=True
    )
    # Hotel Owner
    owner = models.User(
        email=f"owner_m41_{suffix}@example.com",
        hashed_password=hash_password("Owner@123"),
        full_name="Gregory Host",
        role=models.UserRole.HOTEL_OWNER,
        is_active=True,
        is_verified=True
    )
    db.add_all([customer1, customer2, owner])
    db.commit()

    cust1_token, _ = create_access_token(customer1.id, customer1.role.value)
    cust1_headers = {"Authorization": f"Bearer {cust1_token}"}

    cust2_token, _ = create_access_token(customer2.id, customer2.role.value)
    cust2_headers = {"Authorization": f"Bearer {cust2_token}"}

    owner_token, _ = create_access_token(owner.id, owner.role.value)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    # Setup Hotel
    hotel = models.Hotel(
        owner_id=owner.id,
        name=f"Azure Haven Luxury Resort {suffix}",
        description="Exclusive oceanfront resort with panoramic coral views",
        property_type="RESORT",
        star_rating=5.0,
        email=f"azure_{suffix}@example.com",
        phone="+1-555-7733",
        address_line1="100 Azure Bay Blvd",
        city="Honolulu",
        state="Hawaii",
        country="United States",
        postal_code="96815",
        latitude=21.2768,
        longitude=-157.8272,
        is_approved=True,
        status=models.HotelStatus.APPROVED,
        is_active=True
    )
    db.add(hotel)
    db.commit()

    # Room Type & Rooms
    room_type = models.RoomType(
        hotel_id=hotel.id,
        name="Ocean King Suite",
        code=f"OKS-{suffix[:4]}",
        description="King bed with ocean balcony",
        base_price_per_night=250.0,
        max_occupancy=3,
        max_adults=2,
        max_children=1,
        bed_type="King"
    )
    db.add(room_type)
    db.commit()

    room1 = models.Room(
        hotel_id=hotel.id,
        room_type_id=room_type.id,
        room_number=f"OK-{suffix[:3]}-1",
        floor_number=2,
        status=models.RoomStatus.AVAILABLE
    )
    room2 = models.Room(
        hotel_id=hotel.id,
        room_type_id=room_type.id,
        room_number=f"OK-{suffix[:3]}-2",
        floor_number=2,
        status=models.RoomStatus.AVAILABLE
    )
    db.add_all([room1, room2])
    db.commit()

    # Create an active booking on room1
    today = date.today()
    check_in = today + timedelta(days=2)
    check_out = today + timedelta(days=5)

    booking = models.Booking(
        booking_reference=f"BK-{uuid.uuid4().hex[:8].upper()}",
        user_id=customer1.id,
        hotel_id=hotel.id,
        room_type_id=room_type.id,
        room_id=room1.id,
        check_in_date=check_in,
        check_out_date=check_out,
        total_nights=3,
        nightly_price=250.0,
        base_amount=750.0,
        tax_amount=75.0,
        total_amount=825.0,
        status=models.BookingStatus.CONFIRMED,
        payment_status=models.PaymentStatus.PAID
    )
    db.add(booking)
    db.commit()

    print("[OK] Test environment and sample entities initialized successfully")

    # =========================================================================
    # MODULE 41: Hotel Subscription Payments
    # =========================================================================
    print("\n--- Testing Module 41: Hotel Subscription Payments ---")

    plans = crud.subscriptions.get_all_plans(db, active_only=True)
    basic_plan = next((p for p in plans if p.tier == models.SubscriptionTier.BASIC), plans[0])
    premium_plan = next((p for p in plans if p.tier == models.SubscriptionTier.PREMIUM), plans[-1])

    # 1. Initiate Stripe subscription checkout session
    resp = client.post("/subscription-payments/checkout-session", json={
        "hotel_id": hotel.id,
        "plan_id": basic_plan.id,
        "success_url": "https://example.com/success",
        "cancel_url": "https://example.com/cancel"
    }, headers=owner_headers)
    assert resp.status_code == 201, resp.text
    session_data = resp.json()["data"]
    assert "cs_sub_" in session_data["session_id"]
    assert session_data["amount"] == basic_plan.price
    print(f"[OK] Created Stripe checkout session: {session_data['session_id']}")

    # 2. Process Stripe Webhook (invoice.payment_succeeded)
    resp = client.post("/subscription-payments/webhook", json={
        "event_type": "invoice.payment_succeeded",
        "session_id": session_data["session_id"],
        "amount_paid": basic_plan.price
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "success"
    print("[OK] Processed invoice.payment_succeeded webhook -> activated subscription")

    # 3. Upgrade subscription tier to PREMIUM
    resp = client.post(f"/subscription-payments/hotels/{hotel.id}/upgrade-downgrade", json={
        "new_plan_id": premium_plan.id,
        "immediate": True
    }, headers=owner_headers)
    assert resp.status_code == 200
    upgrade_res = resp.json()["data"]
    assert upgrade_res["action"] == "UPGRADE"
    assert upgrade_res["new_plan"] == premium_plan.name
    print(f"[OK] Upgraded subscription plan to {premium_plan.name}")

    # 4. View subscription payment history
    resp = client.get(f"/subscription-payments/hotels/{hotel.id}/history", headers=owner_headers)
    assert resp.status_code == 200
    history = resp.json()["data"]
    assert len(history) >= 2
    print(f"[OK] Subscription payment history verified ({len(history)} entries)")

    # =========================================================================
    # MODULE 42: Dynamic Pricing Management
    # =========================================================================
    print("\n--- Testing Module 42: Dynamic Pricing Management ---")

    # 1. Configure Seasonal rule (+20% for upcoming summer)
    resp = client.post("/pricing-rules", json={
        "hotel_id": hotel.id,
        "room_type_id": room_type.id,
        "rule_name": "Peak Summer Season",
        "rule_type": "SEASONAL",
        "adjustment_type": "PERCENTAGE_INCREASE",
        "adjustment_value": 20.0,
        "start_date": (today + timedelta(days=1)).isoformat(),
        "end_date": (today + timedelta(days=30)).isoformat(),
        "priority": 10
    }, headers=owner_headers)
    assert resp.status_code == 201, resp.text
    rule1_id = resp.json()["data"]["id"]
    print(f"[OK] Created Seasonal pricing rule (ID: {rule1_id}, +20%)")

    # 2. Configure Weekend surge rule (+$40 on Fri, Sat: 4, 5)
    resp = client.post("/pricing-rules", json={
        "hotel_id": hotel.id,
        "room_type_id": room_type.id,
        "rule_name": "Weekend Surge",
        "rule_type": "WEEKEND",
        "adjustment_type": "FIXED_ADJUSTMENT",
        "adjustment_value": 40.0,
        "days_of_week": "4,5",
        "priority": 5
    }, headers=owner_headers)
    assert resp.status_code == 201, resp.text
    print("[OK] Created Weekend surge rule (+ $40 on Fri/Sat)")

    # 3. Test Conflict Prevention: Creating overlapping rule with same type & priority
    resp = client.post("/pricing-rules", json={
        "hotel_id": hotel.id,
        "room_type_id": room_type.id,
        "rule_name": "Conflicting Summer",
        "rule_type": "SEASONAL",
        "adjustment_type": "PERCENTAGE_INCREASE",
        "adjustment_value": 25.0,
        "start_date": (today + timedelta(days=5)).isoformat(),
        "end_date": (today + timedelta(days=15)).isoformat(),
        "priority": 10  # same priority conflict!
    }, headers=owner_headers)
    assert resp.status_code == 400
    err_msg = resp.json().get("detail") or resp.json().get("message", "")
    assert "Conflicting pricing rule" in err_msg
    print("[OK] Conflict prevention verified: Blocked conflicting rule with identical priority & date range")

    # 4. Calculate dynamic room pricing consistently
    calc_in = today + timedelta(days=2)
    calc_out = today + timedelta(days=6)  # 4 nights
    resp = client.post("/pricing-rules/calculate", json={
        "hotel_id": hotel.id,
        "room_type_id": room_type.id,
        "check_in_date": calc_in.isoformat(),
        "check_out_date": calc_out.isoformat()
    })
    assert resp.status_code == 200, resp.text
    calc_data = resp.json()["data"]
    assert calc_data["nights"] == 4
    assert calc_data["final_total"] > calc_data["base_total"]  # Season surge applied!
    assert len(calc_data["daily_breakdown"]) == 4
    print(f"[OK] Calculated dynamic pricing for {calc_data['nights']} nights: Base ${calc_data['base_total']} -> Adjusted ${calc_data['final_total']}")

    # 5. List pricing rules
    resp = client.get(f"/pricing-rules/hotels/{hotel.id}", headers=owner_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 2
    print(f"[OK] Retrieved {len(resp.json()['data'])} configured pricing rules")

    # =========================================================================
    # MODULE 43: Loyalty and Rewards
    # =========================================================================
    print("\n--- Testing Module 43: Loyalty and Rewards ---")

    # 1. Retrieve member loyalty account
    resp = client.get("/loyalty/my-account", headers=cust1_headers)
    assert resp.status_code == 200
    cust1_acc = resp.json()["data"]
    assert cust1_acc["points_balance"] == 0
    assert cust1_acc["tier"] == "BRONZE"
    cust1_ref_code = cust1_acc["referral_code"]
    print(f"[OK] Alice's loyalty account initialized (Tier: BRONZE, Ref Code: {cust1_ref_code})")

    # 2. Member 2 joins using Member 1's referral code
    resp = client.post("/loyalty/referral", json={
        "referral_code": cust1_ref_code
    }, headers=cust2_headers)
    assert resp.status_code == 200
    ref_data = resp.json()["data"]
    assert ref_data["welcome_bonus_points"] == 250
    print("[OK] Bob claimed referral code -> received 250 welcome bonus points")

    # Check Alice received 500 referral reward points
    resp = client.get("/loyalty/my-account", headers=cust1_headers)
    assert resp.json()["data"]["points_balance"] == 500
    print("[OK] Alice's account credited 500 referral reward points")

    # Prevent duplicate referral claim
    resp = client.post("/loyalty/referral", json={"referral_code": cust1_ref_code}, headers=cust2_headers)
    assert resp.status_code == 400
    print("[OK] Duplicate referral claim rejected")

    # 3. Award points for eligible completed booking
    resp = client.post("/loyalty/award-booking", json={
        "booking_id": booking.id
    }, headers=cust1_headers)
    assert resp.status_code == 201
    award_data = resp.json()["data"]
    assert award_data["points_awarded"] == int(booking.total_amount)  # $750 * 1.0 = 750 pts
    print(f"[OK] Awarded {award_data['points_awarded']} points for booking {booking.booking_reference}")

    # 4. Prevent duplicate point credit on same booking
    resp = client.post("/loyalty/award-booking", json={
        "booking_id": booking.id
    }, headers=cust1_headers)
    assert resp.status_code == 400
    err_msg = resp.json().get("detail") or resp.json().get("message", "")
    assert "already been awarded" in err_msg
    print("[OK] Prevented duplicate point credit on booking")

    # 5. Redeem points for booking discount
    # Alice has 500 + 750 = 1250 points. Let's redeem 500 points for $5.00 discount
    resp = client.post("/loyalty/redeem", json={
        "points": 500,
        "booking_id": booking.id
    }, headers=cust1_headers)
    assert resp.status_code == 200
    redeem_data = resp.json()["data"]
    assert redeem_data["discount_amount"] == 5.0
    assert redeem_data["new_balance"] == award_data["points_awarded"]
    print(f"[OK] Successfully redeemed 500 points for ${redeem_data['discount_amount']} discount")

    # Prevent unauthorized / overdraft redemption
    resp = client.post("/loyalty/redeem", json={"points": 99999}, headers=cust1_headers)
    assert resp.status_code == 400
    err_msg = resp.json().get("detail") or resp.json().get("message", "")
    assert "Insufficient points" in err_msg
    print("[OK] Prevented unauthorized points overdraft")

    # 6. Retrieve points ledger
    resp = client.get("/loyalty/ledger", headers=cust1_headers)
    assert resp.status_code == 200
    ledger = resp.json()["data"]
    assert len(ledger) >= 3  # Referral bonus, Booking earned, Points redeemed
    print(f"[OK] Verified points ledger audit trail ({len(ledger)} entries)")

    # 7. List membership tiers catalog
    resp = client.get("/loyalty/tiers")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 4  # BRONZE, SILVER, GOLD, PLATINUM
    print("[OK] Retrieved membership tiers & benefit rules (Bronze, Silver, Gold, Platinum)")

    # =========================================================================
    # MODULE 44: Location Services
    # =========================================================================
    print("\n--- Testing Module 44: Location Services ---")

    # 1. Update verified hotel coordinates
    resp = client.put(f"/locations/hotels/{hotel.id}/coordinates", json={
        "latitude": 21.2768,
        "longitude": -157.8272,
        "formatted_address": "100 Azure Bay Blvd, Waikiki Beach, Honolulu, HI"
    }, headers=owner_headers)
    assert resp.status_code == 200
    coord_data = resp.json()["data"]
    assert coord_data["latitude"] == 21.2768
    print(f"[OK] Verified and updated hotel coordinates: {coord_data['latitude']}, {coord_data['longitude']}")

    # Coordinate validation boundary test (invalid lat 150)
    resp = client.put(f"/locations/hotels/{hotel.id}/coordinates", json={
        "latitude": 150.0,
        "longitude": -157.8272
    }, headers=owner_headers)
    assert resp.status_code in [400, 422]
    print("[OK] Invalid coordinate rejection verified (lat > 90)")

    # 2. Add nearby attractions
    resp = client.post(f"/locations/hotels/{hotel.id}/attractions", json={
        "name": "Waikiki Beach",
        "category": "BEACH",
        "latitude": 21.2760,
        "longitude": -157.8260,
        "description": "World-famous golden sand beach and surfing",
        "icon": "umbrella-beach"
    }, headers=owner_headers)
    assert resp.status_code == 201
    print("[OK] Added Waikiki Beach attraction")

    resp = client.post(f"/locations/hotels/{hotel.id}/attractions", json={
        "name": "Diamond Head State Monument",
        "category": "LANDMARK",
        "latitude": 21.2631,
        "longitude": -157.8058,
        "description": "Iconic volcanic crater with panoramic views",
        "icon": "mountain"
    }, headers=owner_headers)
    assert resp.status_code == 201
    print("[OK] Added Diamond Head attraction")

    # 3. Retrieve attractions with accurate haversine distances
    resp = client.get(f"/locations/hotels/{hotel.id}/attractions")
    assert resp.status_code == 200
    attractions = resp.json()["data"]
    assert len(attractions) >= 2
    waikiki = next(a for a in attractions if "Waikiki" in a["name"])
    assert waikiki["distance_km"] is not None
    print(f"[OK] Retrieved attractions with dynamic distance: Waikiki is {waikiki['distance_km']} km away")

    # 4. Search nearby hotels within 50 km radius
    resp = client.get(f"/locations/nearby-hotels?latitude=21.2768&longitude=-157.8272&radius_km=30")
    assert resp.status_code == 200
    nearby = resp.json()["data"]
    assert any(h["hotel_id"] == hotel.id for h in nearby)
    print(f"[OK] Geographic radius search successful (Found {len(nearby)} hotels within 30 km)")

    # 5. Distance Matrix & Driving Duration calculation
    resp = client.post("/locations/distance-matrix", json={
        "origin_lat": 21.2768,
        "origin_lon": -157.8272,
        "destination_lat": 21.3245,
        "destination_lon": -157.9251  # Honolulu Airport (HNL)
    })
    assert resp.status_code == 200
    matrix_res = resp.json()["data"]
    assert matrix_res["distance_km"] > 0
    assert matrix_res["estimated_drive_minutes"] > 0
    print(f"[OK] Distance Matrix computed: {matrix_res['distance_km']} km, ~{matrix_res['estimated_drive_minutes']} mins drive")

    # =========================================================================
    # MODULE 45: Calendar and Booking Scheduler
    # =========================================================================
    print("\n--- Testing Module 45: Calendar and Booking Scheduler ---")

    # 1. Retrieve room availability calendar matrix
    cal_start = today
    cal_end = today + timedelta(days=7)
    resp = client.get(
        f"/calendar/hotels/{hotel.id}/availability?start_date={cal_start.isoformat()}&end_date={cal_end.isoformat()}",
        headers=owner_headers
    )
    assert resp.status_code == 200
    cal_data = resp.json()["data"]
    assert cal_data["total_rooms"] == 2
    room1_row = next(r for r in cal_data["rooms"] if r["room_id"] == room1.id)
    # Check that room1 has booked days corresponding to booking
    has_booked_day = any(d["status"] == "BOOKED" and d["booking_id"] == booking.id for d in room1_row["days"])
    assert has_booked_day
    print(f"[OK] Room availability calendar matrix generated ({len(cal_data['rooms'])} rooms across 8 days)")

    # 2. Check room conflict on already booked room & dates
    resp = client.post("/calendar/check-conflict", json={
        "room_id": room1.id,
        "check_in_date": (check_in + timedelta(days=1)).isoformat(),
        "check_out_date": (check_out + timedelta(days=1)).isoformat()
    })
    assert resp.status_code == 200
    conflict_res = resp.json()["data"]
    assert conflict_res["has_conflict"] is True
    assert conflict_res["is_available"] is False
    assert len(conflict_res["conflicting_bookings"]) >= 1
    print("[OK] Room conflict correctly detected: Double-booking prevented!")

    # Open date conflict check on room2 (should be available)
    resp = client.post("/calendar/check-conflict", json={
        "room_id": room2.id,
        "check_in_date": check_in.isoformat(),
        "check_out_date": check_out.isoformat()
    })
    assert resp.status_code == 200
    no_conflict_res = resp.json()["data"]
    assert no_conflict_res["has_conflict"] is False
    assert no_conflict_res["is_available"] is True
    print("[OK] Open room availability verified: No conflict found")

    # 3. Retrieve daily arrival/departure timetable
    resp = client.get(f"/calendar/hotels/{hotel.id}/schedule?target_date={check_in.isoformat()}", headers=owner_headers)
    assert resp.status_code == 200
    sched = resp.json()["data"]
    assert sched["total_arrivals"] >= 1
    assert any(a["booking_id"] == booking.id for a in sched["arrivals"])
    print(f"[OK] Daily timetable retrieved: Found {sched['total_arrivals']} expected arrival(s) on {check_in.isoformat()}")

    # 4. Run automated background reminders and scheduler jobs
    resp = client.post("/calendar/run-scheduled-jobs", headers=admin_headers)
    assert resp.status_code == 200
    jobs_summary = resp.json()["data"]
    print(f"[OK] Executed {jobs_summary['jobs_executed']} scheduled background reminder/cleanup job(s)")

    print("\nSUCCESS: ALL TESTS FOR MODULES 41 - 45 PASSED WITH 100% SUCCESS!")


def test_modules_41_to_45():
    run_tests()

if __name__ == "__main__":
    run_tests()

