"""
Comprehensive Integration Test Suite for Modules 31 - 40:
- Module 31: Hotel Revenue Analytics
- Module 32: Hotel Occupancy Analytics
- Module 33: Customer Analytics
- Module 34: Hotel Owner Dashboard APIs
- Module 35: Customer Dashboard APIs
- Module 36: Admin Dashboard APIs
- Module 37: Hotel Verification and Moderation
- Module 38: Reports and Export
- Module 39: Audit Logs and Security Monitoring
- Module 40: Hotel Subscription Plans
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
    print("=== STARTING INTEGRATION TESTS FOR MODULES 31 - 40 ===")
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

    # Customer
    suffix = uuid.uuid4().hex[:6]
    customer = models.User(
        email=f"customer_m31_{suffix}@example.com",
        hashed_password=hash_password("Customer@123"),
        full_name="Samantha Traveler",
        role=models.UserRole.CUSTOMER,
        is_active=True,
        is_verified=True
    )
    db.add(customer)

    # Hotel Owner
    owner = models.User(
        email=f"owner_m31_{suffix}@example.com",
        hashed_password=hash_password("Owner@123"),
        full_name="Oliver Owner",
        role=models.UserRole.HOTEL_OWNER,
        is_active=True,
        is_verified=True
    )
    db.add(owner)
    db.commit()

    customer_token, _ = create_access_token(customer.id, customer.role.value)
    customer_headers = {"Authorization": f"Bearer {customer_token}"}

    owner_token, _ = create_access_token(owner.id, owner.role.value)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    # Setup Hotel, Room Type, and Rooms
    hotel = models.Hotel(
        owner_id=owner.id,
        name=f"Emerald Cove Resort {suffix}",
        description="Luxury coastal resort",
        property_type="RESORT",
        star_rating=4.9,
        email=f"emerald_{suffix}@example.com",
        phone="+1-555-8822",
        address_line1="77 Emerald Beach Rd",
        city="Honolulu",
        state="Hawaii",
        country="United States",
        postal_code="96815",
        is_approved=True,
        status=models.HotelStatus.APPROVED,
        is_active=True
    )
    db.add(hotel)
    db.commit()
    db.refresh(hotel)

    room_type = models.RoomType(
        hotel_id=hotel.id,
        name="Ocean Breeze Villa",
        code=f"OBV_{suffix}",
        base_price_per_night=400.0,
        max_occupancy=4,
        is_active=True
    )
    db.add(room_type)
    db.commit()
    db.refresh(room_type)

    room1 = models.Room(
        hotel_id=hotel.id,
        room_type_id=room_type.id,
        room_number=f"Villa-1",
        status=models.RoomStatus.OCCUPIED,
        is_active=True
    )
    room2 = models.Room(
        hotel_id=hotel.id,
        room_type_id=room_type.id,
        room_number=f"Villa-2",
        status=models.RoomStatus.AVAILABLE,
        is_active=True
    )
    room3 = models.Room(
        hotel_id=hotel.id,
        room_type_id=room_type.id,
        room_number=f"Villa-3",
        status=models.RoomStatus.CLEANING,
        is_active=True
    )
    db.add_all([room1, room2, room3])
    db.commit()

    # Create paid bookings
    booking1 = models.Booking(
        booking_reference=f"BK-{uuid.uuid4().hex[:8].upper()}",
        user_id=customer.id,
        hotel_id=hotel.id,
        room_id=room1.id,
        room_type_id=room_type.id,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=2),
        total_nights=2,
        nightly_price=400.0,
        base_amount=800.0,
        tax_amount=80.0,
        total_amount=880.0,
        status=models.BookingStatus.CHECKED_IN,
        payment_status=models.PaymentStatus.PAID
    )
    booking2 = models.Booking(
        booking_reference=f"BK-{uuid.uuid4().hex[:8].upper()}",
        user_id=customer.id,
        hotel_id=hotel.id,
        room_id=room2.id,
        room_type_id=room_type.id,
        check_in_date=date.today() - timedelta(days=10),
        check_out_date=date.today() - timedelta(days=7),
        total_nights=3,
        nightly_price=400.0,
        base_amount=1200.0,
        tax_amount=120.0,
        total_amount=1320.0,
        status=models.BookingStatus.COMPLETED,
        payment_status=models.PaymentStatus.PAID
    )
    db.add_all([booking1, booking2])
    db.commit()

    print("[OK] Test environment and sample transactions set up successfully")

    # =========================================================================
    # MODULE 31: Hotel Revenue Analytics
    # =========================================================================
    print("\n--- Testing Module 31: Hotel Revenue Analytics ---")

    resp = client.get(f"/analytics/revenue/hotels/{hotel.id}/summary", headers=owner_headers)
    assert resp.status_code == 200, resp.text
    rev_data = resp.json()["data"]
    assert rev_data["total_gross_revenue"] >= 2200.0
    assert rev_data["total_completed_bookings"] >= 2
    assert rev_data["average_booking_value"] >= 1000.0
    print(f"[OK] Hotel revenue summary: Gross ${rev_data['total_gross_revenue']}, ABV ${rev_data['average_booking_value']}")

    resp = client.get(f"/analytics/revenue/hotels/{hotel.id}/daily?days=7", headers=owner_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 7
    print(f"[OK] Daily revenue breakdown (7 days) calculated")

    resp = client.get(f"/analytics/revenue/hotels/{hotel.id}/monthly?months=3", headers=owner_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 3
    print(f"[OK] Monthly revenue breakdown calculated")

    # =========================================================================
    # MODULE 32: Hotel Occupancy Analytics
    # =========================================================================
    print("\n--- Testing Module 32: Hotel Occupancy Analytics ---")

    resp = client.get(f"/analytics/occupancy/hotels/{hotel.id}/live", headers=owner_headers)
    assert resp.status_code == 200, resp.text
    occ_data = resp.json()["data"]
    assert occ_data["total_rooms"] == 3
    assert occ_data["occupied_rooms"] == 1
    assert occ_data["available_rooms"] == 1
    assert occ_data["cleaning_rooms"] == 1
    assert occ_data["occupancy_rate"] == 33.33
    print(f"[OK] Live occupancy snapshot verified: 33.33% (1 occupied, 1 available, 1 cleaning)")

    resp = client.get(f"/analytics/occupancy/hotels/{hotel.id}/summary", headers=owner_headers)
    assert resp.status_code == 200
    print(f"[OK] Occupancy rate for date range calculated successfully")

    resp = client.get(f"/analytics/occupancy/hotels/{hotel.id}/peak-periods?limit=5", headers=owner_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1
    print(f"[OK] Peak booking periods identified")

    # =========================================================================
    # MODULE 33: Customer Analytics
    # =========================================================================
    print("\n--- Testing Module 33: Customer Analytics ---")

    resp = client.get(f"/analytics/customers/summary?hotel_id={hotel.id}", headers=owner_headers)
    assert resp.status_code == 200, resp.text
    cust_summary = resp.json()["data"]
    assert cust_summary["repeat_customers_count"] >= 1
    assert cust_summary["retention_rate"] >= 50.0
    print(f"[OK] Customer retention metrics: Retention {cust_summary['retention_rate']}%, Avg Spend ${cust_summary['average_customer_lifetime_value']}")

    resp = client.get(f"/analytics/customers/repeat?hotel_id={hotel.id}&min_bookings=2", headers=owner_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1
    print(f"[OK] Identified repeat customers with booking frequency and spend")

    resp = client.get("/analytics/customers/destinations?limit=5", headers=owner_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1
    print(f"[OK] Top destination demand cities aggregated")

    # =========================================================================
    # MODULE 34: Hotel Owner Dashboard APIs
    # =========================================================================
    print("\n--- Testing Module 34: Hotel Owner Dashboard APIs ---")

    resp = client.get(f"/dashboards/owner/{hotel.id}", headers=owner_headers)
    assert resp.status_code == 200, resp.text
    owner_dash = resp.json()["data"]
    assert owner_dash["hotel_name"] == hotel.name
    assert owner_dash["total_rooms"] == 3
    assert owner_dash["occupancy_rate"] == 33.33
    assert owner_dash["total_revenue"] >= 2200.0
    print(f"[OK] Consolidated Hotel Owner Dashboard loaded (Revenue: ${owner_dash['total_revenue']}, Occupancy: {owner_dash['occupancy_rate']}%)")

    # =========================================================================
    # MODULE 35: Customer Dashboard APIs
    # =========================================================================
    print("\n--- Testing Module 35: Customer Dashboard APIs ---")

    resp = client.get("/dashboards/customer", headers=customer_headers)
    assert resp.status_code == 200, resp.text
    cust_dash = resp.json()["data"]
    assert cust_dash["full_name"] == customer.full_name
    assert len(cust_dash["upcoming_bookings"]) >= 1
    assert cust_dash["total_spent"] >= 2200.0
    print(f"[OK] Personalized Customer Dashboard loaded ({len(cust_dash['upcoming_bookings'])} upcoming stays, Spent: ${cust_dash['total_spent']})")

    # =========================================================================
    # MODULE 36: Admin Dashboard APIs
    # =========================================================================
    print("\n--- Testing Module 36: Admin Dashboard APIs ---")

    resp = client.get("/dashboards/admin", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    admin_dash = resp.json()["data"]
    assert admin_dash["total_hotels"] >= 1
    assert admin_dash["total_bookings"] >= 2
    assert admin_dash["total_platform_revenue"] >= 2200.0
    print(f"[OK] Admin platform dashboard loaded (Platform Volume: ${admin_dash['total_platform_revenue']}, Total Bookings: {admin_dash['total_bookings']})")

    # =========================================================================
    # MODULE 37: Hotel Verification and Moderation
    # =========================================================================
    print("\n--- Testing Module 37: Hotel Verification and Moderation ---")

    # Create a pending hotel
    pending_hotel = models.Hotel(
        owner_id=owner.id,
        name=f"Awaiting Verification Hotel {suffix}",
        email=f"pending_{suffix}@example.com",
        phone="+1-555-9000",
        address_line1="123 Test St",
        city="Maui",
        state="Hawaii",
        country="United States",
        postal_code="96761",
        is_approved=False,
        status=models.HotelStatus.PENDING_APPROVAL,
        is_active=True
    )
    db.add(pending_hotel)
    db.commit()
    db.refresh(pending_hotel)

    # 1. List pending hotels
    resp = client.get("/moderation/hotels/pending", headers=admin_headers)
    assert resp.status_code == 200
    assert any(h["id"] == pending_hotel.id for h in resp.json()["data"])
    print(f"[OK] Listed pending hotel applications (Found Hotel #{pending_hotel.id})")

    # 2. Approve hotel
    resp = client.post(f"/moderation/hotels/{pending_hotel.id}/approve", json={
        "reason": "Business license verified",
        "notes": "All health inspection certificates submitted."
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["is_approved"] is True
    assert resp.json()["data"]["status"] == "APPROVED"
    print(f"[OK] Hotel #{pending_hotel.id} approved successfully")

    # 3. Suspend hotel
    resp = client.post(f"/moderation/hotels/{pending_hotel.id}/suspend", json={
        "reason": "Customer complaint investigation",
        "notes": "Temporary freeze"
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "SUSPENDED"
    print(f"[OK] Hotel #{pending_hotel.id} suspended with recorded reason")

    # 4. Reactivate hotel
    resp = client.post(f"/moderation/hotels/{pending_hotel.id}/reactivate", json={
        "reason": "Investigation concluded, issue resolved"
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "APPROVED"
    print(f"[OK] Hotel #{pending_hotel.id} reactivated")

    # 5. Audit history
    resp = client.get(f"/moderation/hotels/{pending_hotel.id}/history", headers=admin_headers)
    assert resp.status_code == 200
    history = resp.json()["data"]
    assert len(history) >= 3  # APPROVED, SUSPENDED, REACTIVATED
    print(f"[OK] Moderation decision history verified ({len(history)} decision records)")

    # =========================================================================
    # MODULE 38: Reports and Export
    # =========================================================================
    print("\n--- Testing Module 38: Reports and Export ---")

    # JSON report
    resp = client.get("/reports/bookings?format=json", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 2
    print(f"[OK] Generated Bookings report (JSON format, {len(resp.json()['data'])} records)")

    # CSV report download
    resp = client.get("/reports/bookings?format=csv", headers=admin_headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "Booking Reference" in resp.text
    print(f"[OK] Exported Bookings report as CSV download")

    # PDF / HTML report
    resp = client.get("/reports/bookings?format=pdf", headers=admin_headers)
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Print to PDF" in resp.text
    print(f"[OK] Exported Bookings report as printable PDF/HTML document")

    # =========================================================================
    # MODULE 39: Audit Logs and Security Monitoring
    # =========================================================================
    print("\n--- Testing Module 39: Audit Logs and Security Monitoring ---")

    # Log security event
    resp = client.post("/audit-logs/event", json={
        "event_type": "SECURITY",
        "action": "ADMIN_PASSWORD_RESET_ATTEMPT",
        "description": "Admin requested a manual password audit",
        "details": {"source": "admin_console"}
    }, headers=admin_headers)
    assert resp.status_code == 201
    print(f"[OK] Immutable audit log entry committed")

    # List audit logs
    resp = client.get("/audit-logs", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1
    print(f"[OK] Retrieved system audit logs")

    # Query security events
    resp = client.get("/audit-logs/security-events", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1
    print(f"[OK] Filtered security and critical incidents audit stream")

    # =========================================================================
    # MODULE 40: Hotel Subscription Plans
    # =========================================================================
    print("\n--- Testing Module 40: Hotel Subscription Plans ---")

    # 1. List available plans
    resp = client.get("/subscriptions/plans")
    assert resp.status_code == 200
    plans = resp.json()["data"]
    assert len(plans) >= 4  # FREE, BASIC, PREMIUM, ENTERPRISE
    premium_plan = next((p for p in plans if p["tier"] == "PREMIUM"), plans[0])
    print(f"[OK] Retrieved {len(plans)} subscription tiers (Free, Basic, Premium, Enterprise)")

    # 2. Subscribe hotel to plan
    resp = client.post(f"/subscriptions/hotels/{hotel.id}/subscribe", json={
        "plan_id": premium_plan["id"],
        "auto_renew": True
    }, headers=owner_headers)
    assert resp.status_code == 201, resp.text
    sub_data = resp.json()["data"]
    assert sub_data["status"] == "ACTIVE"
    assert sub_data["plan_id"] == premium_plan["id"]
    print(f"[OK] Subscribed hotel to {premium_plan['name']} (Status: ACTIVE)")

    # 3. View active subscription & listing benefits
    resp = client.get(f"/subscriptions/hotels/{hotel.id}/current", headers=owner_headers)
    assert resp.status_code == 200
    cur_sub = resp.json()["data"]
    assert cur_sub["status"] == "ACTIVE"
    assert cur_sub["benefits"]["has_analytics"] is True
    print(f"[OK] Active subscription verified with analytics benefits")

    # 4. Cancel auto-renewal
    resp = client.post(f"/subscriptions/hotels/{hotel.id}/cancel", headers=owner_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["auto_renew"] is False
    print(f"[OK] Subscription auto-renewal cancelled successfully")

    print("\nSUCCESS: ALL TESTS FOR MODULES 31 - 40 PASSED WITH 100% SUCCESS!")
    db.close()


def test_modules_31_to_40():
    run_tests()

if __name__ == "__main__":
    run_tests()

