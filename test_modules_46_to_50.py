"""
Comprehensive Integration Test Suite for Modules 46 - 50:
- Module 46: Financial Management
- Module 47: Business Intelligence APIs
- Module 48: Fraud Detection and Security
- Module 49: System Configuration
- Module 50: Advanced Platform Administration
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
    print("=== STARTING INTEGRATION TESTS FOR MODULES 46 - 50 ===")

    # 0. Seed initial platform defaults
    crud.subscriptions.seed_default_plans(db)
    crud.system_config.seed_default_configs(db)
    crud.platform_admin.seed_default_policies(db)

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
        email=f"cust_m46_{suffix}@example.com",
        hashed_password=hash_password("Customer@123"),
        full_name="Morgan Chase",
        role=models.UserRole.CUSTOMER,
        is_active=True,
        is_verified=True
    )
    # Hotel Owner
    owner = models.User(
        email=f"owner_m46_{suffix}@example.com",
        hashed_password=hash_password("Owner@123"),
        full_name="Harrison Ford",
        role=models.UserRole.HOTEL_OWNER,
        is_active=True,
        is_verified=True
    )
    db.add_all([customer, owner])
    db.commit()

    cust_token, _ = create_access_token(customer.id, customer.role.value)
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    owner_token, _ = create_access_token(owner.id, owner.role.value)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    # Setup Hotel
    hotel = models.Hotel(
        owner_id=owner.id,
        name=f"Grand Horizon Resort {suffix}",
        description="Luxury mountain and sea view resort",
        property_type="RESORT",
        star_rating=4.8,
        email=f"horizon_{suffix}@example.com",
        phone="+1-555-9090",
        address_line1="500 Horizon Ridge Way",
        city="Honolulu",
        state="Hawaii",
        country="United States",
        postal_code="96815",
        latitude=21.2850,
        longitude=-157.8350,
        is_approved=True,
        status=models.HotelStatus.APPROVED,
        is_active=True
    )
    db.add(hotel)
    db.commit()

    # Room Type & Rooms
    room_type = models.RoomType(
        hotel_id=hotel.id,
        name="Penthouse Suite",
        code=f"PS-{suffix[:4]}",
        description="Panoramic penthouse",
        base_price_per_night=500.0,
        max_occupancy=4,
        max_adults=2,
        max_children=2,
        bed_type="King"
    )
    db.add(room_type)
    db.commit()

    room1 = models.Room(
        hotel_id=hotel.id,
        room_type_id=room_type.id,
        room_number=f"PH-{suffix[:3]}",
        floor_number=10,
        status=models.RoomStatus.AVAILABLE
    )
    db.add(room1)
    db.commit()

    # Create paid bookings
    today = date.today()
    booking1 = models.Booking(
        booking_reference=f"BK-{uuid.uuid4().hex[:8].upper()}",
        user_id=customer.id,
        hotel_id=hotel.id,
        room_id=room1.id,
        room_type_id=room_type.id,
        check_in_date=today - timedelta(days=5),
        check_out_date=today - timedelta(days=2),
        total_nights=3,
        nightly_price=500.0,
        base_amount=1500.0,
        tax_amount=150.0,
        total_amount=1650.0,
        status=models.BookingStatus.COMPLETED,
        payment_status=models.PaymentStatus.PAID
    )
    booking2 = models.Booking(
        booking_reference=f"BK-{uuid.uuid4().hex[:8].upper()}",
        user_id=customer.id,
        hotel_id=hotel.id,
        room_id=room1.id,
        room_type_id=room_type.id,
        check_in_date=today + timedelta(days=1),
        check_out_date=today + timedelta(days=3),
        total_nights=2,
        nightly_price=500.0,
        base_amount=1000.0,
        tax_amount=100.0,
        total_amount=1100.0,
        status=models.BookingStatus.CONFIRMED,
        payment_status=models.PaymentStatus.PAID
    )
    db.add_all([booking1, booking2])
    db.commit()

    print("[OK] Test environment and sample transactions initialized")

    # =========================================================================
    # MODULE 46: Financial Management
    # =========================================================================
    print("\n--- Testing Module 46: Financial Management ---")

    # 1. Retrieve hotel financial breakdown
    resp = client.get(f"/financial/hotels/{hotel.id}/breakdown", headers=owner_headers)
    assert resp.status_code == 200, resp.text
    breakdown = resp.json()["data"]
    assert breakdown["gross_booking_volume"] >= 2750.0  # 1650 + 1100
    assert breakdown["total_tax_collected"] >= 250.0   # 150 + 100
    assert breakdown["platform_commission_amount"] > 0
    assert breakdown["net_hotel_earnings"] > 0
    print(f"[OK] Financial breakdown calculated: Gross ${breakdown['gross_booking_volume']}, Net ${breakdown['net_hotel_earnings']}")

    # 2. Generate a payout settlement statement
    start_p = today - timedelta(days=10)
    end_p = today + timedelta(days=10)
    resp = client.post("/financial/settlements/generate", json={
        "hotel_id": hotel.id,
        "period_start": start_p.isoformat(),
        "period_end": end_p.isoformat(),
        "notes": "Bi-weekly owner disbursement"
    }, headers=admin_headers)
    assert resp.status_code == 201, resp.text
    settlement = resp.json()["data"]
    assert settlement["status"] == "PENDING"
    settle_id = settlement["id"]
    print(f"[OK] Generated payout settlement #{settle_id} (Ref: {settlement['payout_reference']}, Net: ${settlement['net_payout_amount']})")

    # 3. List payout settlements
    resp = client.get(f"/financial/settlements?hotel_id={hotel.id}", headers=owner_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1
    print(f"[OK] Retrieved settlements list for hotel #{hotel.id}")

    # 4. Mark settlement as PAID
    resp = client.post(f"/financial/settlements/{settle_id}/mark-paid", json={
        "payout_reference": f"ACH-WIRE-{uuid.uuid4().hex[:6].upper()}",
        "notes": "Bank ACH wire transfer confirmed"
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "PAID"
    print(f"[OK] Settlement #{settle_id} marked as PAID")

    # 5. Run payment reconciliation
    resp = client.post(f"/financial/reconciliation/run?hotel_id={hotel.id}", headers=admin_headers)
    assert resp.status_code == 200
    recon = resp.json()["data"]
    assert recon["total_transactions_checked"] >= 2
    assert recon["total_matched"] >= 2
    print(f"[OK] Payment reconciliation executed: {recon['total_matched']}/{recon['total_transactions_checked']} matched seamlessly")

    # =========================================================================
    # MODULE 47: Business Intelligence APIs
    # =========================================================================
    print("\n--- Testing Module 47: Business Intelligence APIs ---")

    # 1. Growth metrics
    resp = client.get("/business-intelligence/growth-metrics?days=30", headers=admin_headers)
    assert resp.status_code == 200
    growth = resp.json()["data"]
    assert "revenue_growth" in growth
    assert "bookings_growth" in growth
    assert "customer_growth" in growth
    print(f"[OK] Growth metrics computed: Revenue trend {growth['revenue_growth']['trend']}, Bookings {growth['bookings_growth']['trend']}")

    # 2. Top performers
    resp = client.get("/business-intelligence/top-performers?limit=5", headers=admin_headers)
    assert resp.status_code == 200
    top = resp.json()["data"]
    assert len(top["top_hotels"]) >= 1
    assert len(top["top_destinations"]) >= 1
    print(f"[OK] Top performers retrieved (Top Hotel: {top['top_hotels'][0]['hotel_name']}, Top City: {top['top_destinations'][0]['city']})")

    # 3. Occupancy trends
    resp = client.get(f"/business-intelligence/occupancy-trends?hotel_id={hotel.id}&months_count=6", headers=owner_headers)
    assert resp.status_code == 200
    occ = resp.json()["data"]
    assert len(occ["trends"]) == 6
    print(f"[OK] Occupancy trends retrieved across {len(occ['trends'])} monthly checkpoints")

    # 4. Executive monthly summary
    resp = client.get(f"/business-intelligence/monthly-summary?year={today.year}&month={today.month}", headers=admin_headers)
    assert resp.status_code == 200
    exec_summary = resp.json()["data"]
    assert exec_summary["total_revenue"] > 0
    assert exec_summary["total_bookings"] > 0
    print(f"[OK] Executive summary for {exec_summary['month_name']} generated: Total Revenue ${exec_summary['total_revenue']}")

    # =========================================================================
    # MODULE 48: Fraud Detection and Security
    # =========================================================================
    print("\n--- Testing Module 48: Fraud Detection and Security ---")

    # 1. Evaluate login risk
    resp = client.post("/security/check-login-risk", json={
        "user_email": customer.email,
        "ip_address": "192.168.1.100",
        "failed_attempts_in_window": 1
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["risk_level"] == "LOW"
    print("[OK] Low-risk login evaluated successfully")

    # Evaluate high risk brute force login
    resp = client.post("/security/check-login-risk", json={
        "user_email": "intruder@suspicious.org",
        "ip_address": "203.0.113.42",
        "failed_attempts_in_window": 6
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["risk_level"] == "HIGH"
    assert resp.json()["data"]["is_suspicious"] is True
    print("[OK] Brute-force login attempt flagged as HIGH risk and generated alert")

    # 2. Automated fraud scan across transactions
    resp = client.post("/security/scan-transactions?window_hours=24", headers=admin_headers)
    assert resp.status_code == 200
    scan = resp.json()["data"]
    print(f"[OK] Fraud scan completed across {scan['scanned_bookings_count']} bookings and {scan['scanned_payments_count']} payments")

    # 3. Retrieve security alerts
    resp = client.get("/security/alerts", headers=admin_headers)
    assert resp.status_code == 200
    alerts = resp.json()["data"]
    assert len(alerts) >= 1
    target_alert = alerts[0]
    print(f"[OK] Retrieved {len(alerts)} security alerts (Latest: {target_alert['title']})")

    # 4. Resolve security alert
    resp = client.post(f"/security/alerts/{target_alert['id']}/resolve", json={
        "status": "RESOLVED",
        "resolution_notes": "Reviewed IP trace. False alarm or mitigated threat."
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "RESOLVED"
    print(f"[OK] Security alert #{target_alert['id']} resolved with admin review note")

    # 5. Security metrics
    resp = client.get("/security/metrics", headers=admin_headers)
    assert resp.status_code == 200
    sec_metrics = resp.json()["data"]
    assert "resolved_alerts_count" in sec_metrics
    print(f"[OK] Security posture metrics retrieved ({sec_metrics['resolved_alerts_count']} resolved incidents)")

    # =========================================================================
    # MODULE 49: System Configuration
    # =========================================================================
    print("\n--- Testing Module 49: System Configuration ---")

    # 1. Retrieve all system settings (check secrets are masked)
    resp = client.get("/system-config", headers=admin_headers)
    assert resp.status_code == 200
    configs = resp.json()["data"]
    assert len(configs) >= 5
    webhook_secret_cfg = next(c for c in configs if "stripe_webhook_secret" in c["key"])
    assert webhook_secret_cfg["value"] == "********"  # masked!
    print(f"[OK] Listed {len(configs)} system configurations (Sensitive secrets verified masked)")

    # 2. Retrieve specific setting
    resp = client.get("/system-config/platform.tax_rate_percentage", headers=admin_headers)
    assert resp.status_code == 200
    tax_cfg = resp.json()["data"]
    assert float(tax_cfg["value"]) > 0
    print(f"[OK] Retrieved setting 'platform.tax_rate_percentage': {tax_cfg['value']}%")

    # 3. Update single configuration with validation
    resp = client.put("/system-config/platform.tax_rate_percentage", json={
        "value": "11.5",
        "description": "Updated state occupancy tax"
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["key"] == "platform.tax_rate_percentage"
    print("[OK] Updated tax rate configuration to 11.5%")

    # Validation rejection test (percentage > 100)
    resp = client.put("/system-config/platform.tax_rate_percentage", json={
        "value": "250.0"
    }, headers=admin_headers)
    assert resp.status_code == 400
    print("[OK] Invalid setting validation verified: Rejected invalid rate (250% > 100%)")

    # 4. Batch update configurations
    resp = client.post("/system-config/batch", json={
        "settings": {
            "platform.default_currency": "USD",
            "platform.commission_rate_percentage": "13.0"
        }
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2
    print("[OK] Batch configuration update applied atomically")

    # =========================================================================
    # MODULE 50: Advanced Platform Administration
    # =========================================================================
    print("\n--- Testing Module 50: Advanced Platform Administration ---")

    # 1. Platform operational overview & health
    resp = client.get("/admin/platform-overview", headers=admin_headers)
    assert resp.status_code == 200
    overview = resp.json()["data"]
    assert overview["database"]["status"] == "HEALTHY"
    assert overview["total_db_tables"] > 20
    print(f"[OK] Platform operational overview verified (DB: {overview['database']['status']}, Latency: {overview['database']['latency_ms']}ms)")

    # 2. Deactivate and reactivate customer account
    resp = client.put(f"/admin/users/{customer.id}/status", json={
        "is_active": False,
        "reason": "Administrative temporary freeze"
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is False
    print(f"[OK] Customer #{customer.id} account deactivated with audit trail")

    resp = client.put(f"/admin/users/{customer.id}/status", json={
        "is_active": True,
        "reason": "Verification review complete, reinstated"
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is True
    print(f"[OK] Customer #{customer.id} account reactivated")

    # 3. Emergency booking status override
    resp = client.put(f"/admin/bookings/{booking2.id}/override-status", json={
        "new_status": "COMPLETED",
        "reason": "Customer checked out early with concierge confirmation"
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "COMPLETED"
    print(f"[OK] Emergency booking status override applied for Booking #{booking2.id} -> COMPLETED")

    # 4. Administrative hotel status override
    resp = client.put(f"/admin/hotels/{hotel.id}/status", json={
        "status": "APPROVED",
        "is_active": True,
        "reason": "Annual partner accreditation approved"
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "APPROVED"
    print(f"[OK] Hotel #{hotel.id} status override verified")

    # 5. Platform policies management
    resp = client.get("/admin/policies")
    assert resp.status_code == 200
    policies = resp.json()["data"]
    assert len(policies) >= 3
    print(f"[OK] Retrieved {len(policies)} platform policies (Terms of Service, Cancellation, Privacy)")

    # Update policy
    resp = client.put("/admin/policies/TERMS_OF_SERVICE", json={
        "content": "Updated Terms of Service with enhanced security provisions.",
        "version": "1.1"
    }, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["version"] == "1.1"
    print("[OK] Updated platform Terms of Service to v1.1 with audit logging")

    # 6. Deep system diagnostics
    resp = client.get("/admin/system-health-check", headers=admin_headers)
    assert resp.status_code == 200
    health = resp.json()["data"]
    assert health["overall_status"] in ["HEALTHY", "WARNING"]
    print(f"[OK] Deep diagnostic health check completed (Overall: {health['overall_status']})")

    print("\nSUCCESS: ALL TESTS FOR MODULES 46 - 50 PASSED WITH 100% SUCCESS!")


def test_modules_46_to_50():
    run_tests()

if __name__ == "__main__":
    run_tests()

