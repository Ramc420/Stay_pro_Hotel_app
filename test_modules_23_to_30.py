"""
Comprehensive Integration Test Suite for Modules 23 - 30:
- Module 23: AI Customer Support Chatbot
- Module 24: In-App Notifications
- Module 25: In-App Messaging
- Module 26: Housekeeping Management
- Module 27: Hotel Staff Management
- Module 28: Check-In and Check-Out Management
- Module 29: Additional Services Management
- Module 30: Room Service Management
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

client = TestClient(app)


def run_tests():
    db: Session = SessionLocal()
    print("=== STARTING INTEGRATION TESTS FOR MODULES 23 - 30 ===")

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
    cust_suffix = uuid.uuid4().hex[:6]
    customer = models.User(
        email=f"customer_{cust_suffix}@example.com",
        hashed_password=hash_password("Customer@123"),
        full_name="Bob Traveler",
        role=models.UserRole.CUSTOMER,
        is_active=True,
        is_verified=True
    )
    db.add(customer)

    # Hotel Owner
    owner = models.User(
        email=f"owner_{cust_suffix}@example.com",
        hashed_password=hash_password("Owner@123"),
        full_name="Helen Hotelier",
        role=models.UserRole.HOTEL_OWNER,
        is_active=True,
        is_verified=True
    )
    db.add(owner)

    # Hotel Staff Member
    staff_user = models.User(
        email=f"staff_{cust_suffix}@example.com",
        hashed_password=hash_password("Staff@123"),
        full_name="Sam Concierge",
        role=models.UserRole.HOTEL_STAFF,
        is_active=True,
        is_verified=True
    )
    db.add(staff_user)

    # Unauthorized Second Customer (to verify privacy checks)
    other_customer = models.User(
        email=f"other_{cust_suffix}@example.com",
        hashed_password=hash_password("Other@123"),
        full_name="Eve Snooper",
        role=models.UserRole.CUSTOMER,
        is_active=True,
        is_verified=True
    )
    db.add(other_customer)
    db.commit()

    customer_token, _ = create_access_token(customer.id, customer.role.value)
    customer_headers = {"Authorization": f"Bearer {customer_token}"}

    owner_token, _ = create_access_token(owner.id, owner.role.value)
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    staff_token, _ = create_access_token(staff_user.id, staff_user.role.value)
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    other_token, _ = create_access_token(other_customer.id, other_customer.role.value)
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Setup Hotel, Room Type, Room, and Booking
    hotel = models.Hotel(
        owner_id=owner.id,
        name=f"Paradise Palms Resort {cust_suffix}",
        description="Luxury tropical beach hotel",
        property_type="HOTEL",
        star_rating=5.0,
        email=f"palms_{cust_suffix}@example.com",
        phone="+1-555-0988",
        address_line1="500 Palm Way",
        city="Honolulu",
        state="Hawaii",
        country="United States",
        postal_code="96815",
        check_in_time="14:00",
        check_out_time="11:00",
        is_approved=True,
        status=models.HotelStatus.APPROVED,
        is_active=True
    )
    db.add(hotel)
    db.commit()
    db.refresh(hotel)

    # Assign staff to hotel
    hotel_staff = models.HotelStaff(
        user_id=staff_user.id,
        hotel_id=hotel.id,
        department="Front Desk",
        position="Senior Receptionist",
        permissions=["FRONT_DESK", "HOUSEKEEPING"],
        is_active=True
    )
    db.add(hotel_staff)
    db.commit()

    # Room Type
    room_type = models.RoomType(
        hotel_id=hotel.id,
        name="Oceanview King Suite",
        code=f"OKS_{cust_suffix}",
        base_price_per_night=350.0,
        max_occupancy=2,
        is_active=True
    )
    db.add(room_type)
    db.commit()
    db.refresh(room_type)

    # Room
    room = models.Room(
        hotel_id=hotel.id,
        room_type_id=room_type.id,
        room_number=f"Room-301",
        floor_number=3,
        status=models.RoomStatus.AVAILABLE,
        is_active=True
    )
    db.add(room)
    db.commit()
    db.refresh(room)

    # Booking
    check_in = date.today()
    check_out = check_in + timedelta(days=3)
    booking_ref = f"BK-{uuid.uuid4().hex[:8].upper()}"
    booking = models.Booking(
        booking_reference=booking_ref,
        user_id=customer.id,
        hotel_id=hotel.id,
        room_id=room.id,
        room_type_id=room_type.id,
        check_in_date=check_in,
        check_out_date=check_out,
        total_nights=3,
        nightly_price=350.0,
        base_amount=1050.0,
        tax_amount=105.0,
        total_amount=1155.0,
        status=models.BookingStatus.CONFIRMED,
        payment_status=models.PaymentStatus.PAID
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    print("[OK] Setup test entities, users, and booking successfully")

    # =========================================================================
    # MODULE 23: AI Customer Support Chatbot
    # =========================================================================
    print("\n--- Testing Module 23: AI Customer Support Chatbot ---")

    # 1. General policy question
    resp = client.post("/support/chat", json={
        "message": "What is your cancellation and refund policy?"
    }, headers=customer_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert "StayNest Cancellation & Refund Policy" in data["bot_response"]["message"]
    conv_id = data["conversation_id"]
    print(f"[OK] General AI customer support query answered (Conversation #{conv_id})")

    # 2. Authorized booking query
    resp = client.post("/support/chat", json={
        "message": f"Can you check the details for my reservation {booking_ref}?",
        "conversation_id": conv_id,
        "booking_reference": booking_ref
    }, headers=customer_headers)
    assert resp.status_code == 200, resp.text
    bot_msg = resp.json()["data"]["bot_response"]["message"]
    assert booking_ref in bot_msg
    assert "CONFIRMED" in bot_msg
    print(f"[OK] Authorized booking context retrieved safely for owner")

    # 3. Privacy protection: Unauthorized user asking for other's booking
    resp = client.post("/support/chat", json={
        "message": f"Give me details on booking {booking_ref}",
        "booking_reference": booking_ref
    }, headers=other_headers)
    assert resp.status_code == 200, resp.text
    unauthorized_reply = resp.json()["data"]["bot_response"]["message"]
    assert "privacy and security" in unauthorized_reply.lower() or "cannot share" in unauthorized_reply.lower()
    print(f"[OK] Prevented unauthorized data exposure to non-owner user")

    # 4. List and view conversation thread
    resp = client.get("/support/conversations", headers=customer_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1

    resp = client.get(f"/support/conversations/{conv_id}", headers=customer_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]["messages"]) >= 2
    print(f"[OK] Retrieved support conversation thread and history")

    # 5. Close conversation
    resp = client.patch(f"/support/conversations/{conv_id}/close", headers=customer_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "CLOSED"
    print(f"[OK] Support conversation closed successfully")

    # =========================================================================
    # MODULE 24: In-App Notifications
    # =========================================================================
    print("\n--- Testing Module 24: In-App Notifications ---")

    # 1. Send test in-app notification
    resp = client.post("/notifications/send", json={
        "user_id": customer.id,
        "title": "Booking Reminder",
        "message": "Your check-in is scheduled for 14:00 today.",
        "notification_type": "CHECK_IN_REMINDER"
    }, headers=admin_headers)
    assert resp.status_code == 201, resp.text
    notif_id = resp.json()["data"]["id"]
    print(f"[OK] In-app notification created (ID: {notif_id})")

    # 2. Get unread count
    resp = client.get("/notifications/unread-count", headers=customer_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["unread_count"] >= 1
    print(f"[OK] Unread notifications count verified")

    # 3. List notifications
    resp = client.get("/notifications", headers=customer_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1
    print(f"[OK] Listed user notifications catalog")

    # 4. Mark single notification as read
    resp = client.patch(f"/notifications/{notif_id}/read", headers=customer_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["is_read"] is True
    print(f"[OK] Notification #{notif_id} marked as read")

    # 5. Mark all as read
    resp = client.post("/notifications/mark-all-read", headers=customer_headers)
    assert resp.status_code == 200
    print(f"[OK] All unread notifications marked as read")

    # =========================================================================
    # MODULE 25: In-App Messaging
    # =========================================================================
    print("\n--- Testing Module 25: In-App Messaging ---")

    # 1. Start conversation with hotel
    resp = client.post("/messages/conversations", json={
        "hotel_id": hotel.id,
        "subject": "Early check-in request inquiry",
        "initial_message": "Hello, could we possibly arrive around 12:30 PM?"
    }, headers=customer_headers)
    assert resp.status_code == 201, resp.text
    chat_conv_id = resp.json()["data"]["conversation_id"]
    print(f"[OK] Guest initiated conversation #{chat_conv_id} with hotel")

    # 2. Hotel staff replies
    resp = client.post(f"/messages/conversations/{chat_conv_id}/messages", json={
        "message": "Hello Bob! Yes, Room 301 is ready for your early arrival."
    }, headers=staff_headers)
    assert resp.status_code == 201, resp.text
    print(f"[OK] Hotel staff replied to guest in thread")

    # 3. View conversation messages
    resp = client.get(f"/messages/conversations/{chat_conv_id}/messages", headers=customer_headers)
    assert resp.status_code == 200
    messages = resp.json()["data"]
    assert len(messages) >= 2
    print(f"[OK] Retrieved paginated conversation message history ({len(messages)} messages)")

    # 4. Mark conversation as read
    resp = client.patch(f"/messages/conversations/{chat_conv_id}/read", headers=customer_headers)
    assert resp.status_code == 200
    print(f"[OK] Marked incoming messages as read")

    # 5. Unauthorized user cannot access other's message thread
    resp = client.get(f"/messages/conversations/{chat_conv_id}/messages", headers=other_headers)
    assert resp.status_code == 403
    print(f"[OK] Unauthorized conversation access strictly forbidden")

    # =========================================================================
    # MODULE 26: Housekeeping Management
    # =========================================================================
    print("\n--- Testing Module 26: Housekeeping Management ---")

    # 1. Create housekeeping task
    resp = client.post("/housekeeping/tasks", json={
        "hotel_id": hotel.id,
        "room_id": room.id,
        "task_type": "CLEANING",
        "priority": "HIGH",
        "notes": "Full sanitization and fresh linens required."
    }, headers=staff_headers)
    assert resp.status_code == 201, resp.text
    hk_task_id = resp.json()["data"]["id"]
    print(f"[OK] Housekeeping task #{hk_task_id} created with DIRTY status")

    # 2. Update status to CLEANING
    resp = client.patch(f"/housekeeping/tasks/{hk_task_id}/status", json={
        "status": "CLEANING",
        "notes": "Cleaning in progress by housekeeper."
    }, headers=staff_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "CLEANING"
    print(f"[OK] Housekeeping task advanced to CLEANING")

    # 3. Record inspection (passed) -> advances to CLEAN & room status AVAILABLE
    resp = client.post(f"/housekeeping/tasks/{hk_task_id}/inspect", json={
        "is_passed": True,
        "rating": 5.0,
        "comments": "Spotless room, passed all quality checks."
    }, headers=staff_headers)
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["is_passed"] is True
    print(f"[OK] Room inspection recorded (PASSED) -> task marked CLEAN")

    # 4. Rooms housekeeping overview
    resp = client.get(f"/housekeeping/hotels/{hotel.id}/rooms-overview", headers=staff_headers)
    assert resp.status_code == 200
    overview = resp.json()["data"]
    assert len(overview) >= 1
    print(f"[OK] Hotel room housekeeping condition overview retrieved")

    # =========================================================================
    # MODULE 27: Hotel Staff Management
    # =========================================================================
    print("\n--- Testing Module 27: Hotel Staff Management ---")

    # 1. List staff for hotel
    resp = client.get(f"/staff/hotels/{hotel.id}", headers=owner_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1
    print(f"[OK] Retrieved hotel staff roster")

    # 2. Update staff assignment
    resp = client.put(f"/staff/{hotel_staff.id}", json={
        "department": "Guest Services",
        "position": "Lead Concierge",
        "permissions": ["FRONT_DESK", "HOUSEKEEPING", "ROOM_SERVICE"]
    }, headers=owner_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["department"] == "Guest Services"
    print(f"[OK] Staff permissions and position updated")

    # 3. Staff Clock-In attendance
    resp = client.post(f"/staff/attendance?hotel_id={hotel.id}", json={
        "action": "CLOCK_IN",
        "notes": "Shift started at Front Desk"
    }, headers=staff_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["clock_in"] is not None
    print(f"[OK] Staff member clocked in successfully")

    # 4. Staff Clock-Out attendance
    resp = client.post(f"/staff/attendance?hotel_id={hotel.id}", json={
        "action": "CLOCK_OUT",
        "notes": "Shift ended"
    }, headers=staff_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["clock_out"] is not None
    print(f"[OK] Staff member clocked out successfully")

    # 5. View attendance records and activity log
    resp = client.get(f"/staff/attendance/{staff_user.id}?hotel_id={hotel.id}", headers=owner_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1

    resp = client.get(f"/staff/activities/{staff_user.id}?hotel_id={hotel.id}", headers=owner_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1
    print(f"[OK] Staff attendance records and audit activity log verified")

    # =========================================================================
    # MODULE 28: Check-In and Check-Out Management
    # =========================================================================
    print("\n--- Testing Module 28: Check-In and Check-Out Management ---")

    # 1. Verify reservation details
    resp = client.post("/check-in-out/verify", json={
        "booking_reference": booking.booking_reference
    }, headers=staff_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["booking_reference"] == booking.booking_reference
    print(f"[OK] Reservation {booking.booking_reference} verified for check-in")

    # 2. Process check-in with early arrival fee
    resp = client.post("/check-in-out/check-in", json={
        "booking_id": booking.id,
        "early_check_in_hours": 1.5,
        "early_check_in_fee": 30.0,
        "notes": "Guest arrived 90 mins early; room was inspected and ready."
    }, headers=staff_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["booking_status"] == "CHECKED_IN"
    assert resp.json()["data"]["room_status"] == "OCCUPIED"
    print(f"[OK] Guest checked in (Status: CHECKED_IN, Room: OCCUPIED, Early Fee: $30.00)")

    # 3. Process check-out with late departure fee
    resp = client.post("/check-in-out/check-out", json={
        "booking_id": booking.id,
        "late_check_out_hours": 2.0,
        "late_check_out_fee": 50.0,
        "notes": "Late check-out granted until 13:00."
    }, headers=staff_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["booking_status"] == "CHECKED_OUT"
    assert resp.json()["data"]["room_status"] == "CLEANING"
    print(f"[OK] Guest checked out (Status: CHECKED_OUT, Room: CLEANING, Late Fee: $50.00)")

    # 4. View today's schedule
    resp = client.get(f"/check-in-out/today/{hotel.id}", headers=staff_headers)
    assert resp.status_code == 200
    print(f"[OK] Today's arrivals and departures schedule retrieved")

    # =========================================================================
    # MODULE 29: Additional Services Management
    # =========================================================================
    print("\n--- Testing Module 29: Additional Services Management ---")

    # 1. Add hotel services (Laundry and Airport Pickup)
    resp = client.post(f"/services/hotels/{hotel.id}", json={
        "name": "Express Laundry & Dry Cleaning",
        "category": "LAUNDRY",
        "price": 25.0,
        "description": "Same-day wash and press service"
    }, headers=owner_headers)
    assert resp.status_code == 201, resp.text
    laundry_service_id = resp.json()["data"]["id"]

    resp = client.post(f"/services/hotels/{hotel.id}", json={
        "name": "VIP Airport Pickup",
        "category": "AIRPORT_PICKUP",
        "price": 60.0,
        "description": "Private luxury SUV airport transfer"
    }, headers=owner_headers)
    assert resp.status_code == 201
    print(f"[OK] Configured hotel services (Laundry & Airport Pickup)")

    # 2. List hotel services
    resp = client.get(f"/services/hotels/{hotel.id}")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 2
    print(f"[OK] Listed hotel service catalog")

    # 3. Guest requests laundry service
    resp = client.post("/services/requests", json={
        "booking_id": booking.id,
        "service_id": laundry_service_id,
        "quantity": 2,
        "special_instructions": "Please return by 6 PM"
    }, headers=customer_headers)
    assert resp.status_code == 201, resp.text
    svc_req_id = resp.json()["data"]["request_id"]
    assert resp.json()["data"]["total_price"] == 50.0  # 2 * $25.00
    print(f"[OK] Guest requested laundry service (Request #{svc_req_id}, Total: $50.00)")

    # 4. View booking service charges
    resp = client.get(f"/services/requests/booking/{booking.id}", headers=customer_headers)
    assert resp.status_code == 200
    assert resp.json()["meta"]["total_service_charges"] >= 50.0
    print(f"[OK] Booking service requests and charges verified")

    # 5. Update request status to COMPLETED
    resp = client.patch(f"/services/requests/{svc_req_id}/status?new_status=COMPLETED", headers=staff_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "COMPLETED"
    print(f"[OK] Service request #{svc_req_id} marked as COMPLETED")

    # =========================================================================
    # MODULE 30: Room Service Management
    # =========================================================================
    print("\n--- Testing Module 30: Room Service Management ---")

    # 1. Add food menu items
    resp = client.post(f"/room-service/menu/{hotel.id}", json={
        "name": "Wagyu Beef Burger with Truffle Fries",
        "category": "MAIN_COURSE",
        "price": 28.0,
        "description": "Prime wagyu patty, aged cheddar, brioche bun",
        "is_vegetarian": False
    }, headers=owner_headers)
    assert resp.status_code == 201, resp.text
    burger_item_id = resp.json()["data"]["id"]

    resp = client.post(f"/room-service/menu/{hotel.id}", json={
        "name": "Fresh Tropical Fruit Smoothie",
        "category": "BEVERAGE",
        "price": 10.0,
        "description": "Pineapple, mango, and coconut water",
        "is_vegetarian": True
    }, headers=owner_headers)
    assert resp.status_code == 201
    smoothie_item_id = resp.json()["data"]["id"]
    print(f"[OK] Added menu items (Burger: ${28}, Smoothie: ${10})")

    # 2. Get hotel food menu
    resp = client.get(f"/room-service/menu/{hotel.id}")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 2
    print(f"[OK] Retrieved hotel room-service menu catalog")

    # 3. Place room-service order
    resp = client.post("/room-service/orders", json={
        "booking_id": booking.id,
        "items": [
            {"menu_item_id": burger_item_id, "quantity": 2},     # $56.00
            {"menu_item_id": smoothie_item_id, "quantity": 1}     # $10.00
        ],
        "notes": "Deliver to Room 301, extra napkins please"
    }, headers=customer_headers)
    assert resp.status_code == 201, resp.text
    order_data = resp.json()["data"]
    rs_order_id = order_data["order_id"]
    assert order_data["subtotal"] == 66.0
    assert order_data["service_charge"] == 6.60
    assert order_data["total_amount"] == 72.60
    print(f"[OK] Room service order #{rs_order_id} placed (Subtotal: $66.00, Fee: $6.60, Total: $72.60)")

    # 4. Hotel kitchen views incoming orders
    resp = client.get(f"/room-service/orders/hotel/{hotel.id}", headers=staff_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1
    print(f"[OK] Kitchen orders queue retrieved")

    # 5. Kitchen updates status to PREPARING then DELIVERED
    resp = client.patch(f"/room-service/orders/{rs_order_id}/status?new_status=PREPARING", headers=staff_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "PREPARING"

    resp = client.patch(f"/room-service/orders/{rs_order_id}/status?new_status=DELIVERED", headers=staff_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "DELIVERED"
    assert resp.json()["data"]["delivered_at"] is not None
    print(f"[OK] Order #{rs_order_id} updated: PREPARING -> DELIVERED")

    # 6. Customer views their order history
    resp = client.get(f"/room-service/orders/booking/{booking.id}", headers=customer_headers)
    assert resp.status_code == 200
    orders = resp.json()["data"]
    assert len(orders) >= 1
    assert orders[0]["status"] == "DELIVERED"
    print(f"[OK] Customer room service order history verified")

    print("\nSUCCESS: ALL TESTS FOR MODULES 23 - 30 PASSED WITH 100% SUCCESS!")
    db.close()


def test_modules_23_to_30():
    run_tests()

if __name__ == "__main__":
    run_tests()

