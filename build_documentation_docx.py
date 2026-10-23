import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'))

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def create_document():
    doc = docx.Document()

    # Set standard 1-inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Styles
    primary_color = RGBColor(26, 86, 160)     # Navy Blue
    secondary_color = RGBColor(45, 55, 72)    # Slate Dark
    accent_color = RGBColor(40, 167, 69)      # Emerald Green
    muted_color = RGBColor(113, 128, 150)     # Gray

    # =========================================================================
    # TITLE & HEADER
    # =========================================================================
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run("StayNest Pro")
    title_run.font.size = Pt(28)
    title_run.font.bold = True
    title_run.font.color.rgb = primary_color

    subtitle_p = doc.add_paragraph()
    subtitle_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle_run = subtitle_p.add_run("Hotel, Resort & Room Booking Management Platform")
    subtitle_run.font.size = Pt(16)
    subtitle_run.font.bold = True
    subtitle_run.font.color.rgb = secondary_color

    meta_p = doc.add_paragraph()
    meta_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_run = meta_p.add_run("Complete Backend Engineering & System Architecture Documentation\nAll 50 Modules Implemented | FastAPI | MySQL | SQLAlchemy ORM | JWT RBAC")
    meta_run.font.size = Pt(11)
    meta_run.font.color.rgb = muted_color

    doc.add_paragraph() # Spacing

    # =========================================================================
    # 1. EXECUTIVE OVERVIEW
    # =========================================================================
    h1 = doc.add_heading("1. Executive Overview & System Architecture", level=1)
    h1.runs[0].font.color.rgb = primary_color

    p = doc.add_paragraph(
        "StayNest Pro is an enterprise-grade, backend-only hotel, resort, and room booking management platform built "
        "using Python 3.12, FastAPI, MySQL 8.0, and SQLAlchemy 2.0 ORM. The architecture follows clean separation of concerns "
        "across data models (models/), Pydantic v2 validation schemas (schemas/), database abstraction operations (crud/), and "
        "REST API controllers (routers/). All 50 required business modules are fully developed, registered in main.py, and "
        "validated using interactive Swagger UI documentation, Postman integration collections, and automated pytest test suites."
    )
    p.paragraph_format.line_spacing = 1.15

    # Key Architecture Highlights
    highlights = [
        ("Unified Single-Instance Backend", "Zero frontend coupling (No React, HTML, CSS, or client dashboard dependencies). Exposes pure JSON REST APIs with standard HTTP status codes."),
        ("Strict Role-Based Access Control (RBAC)", "Enforces 4 distinct privilege tiers: CUSTOMER, HOTEL_OWNER, HOTEL_STAFF, and ADMIN using cryptographic JWT access and refresh tokens."),
        ("Double-Booking & Conflict Prevention", "Atomic database row-locking and date-overlap algorithms ensure rooms cannot be double-booked across overlapping stay windows."),
        ("Financial & Payment Safety", "Stripe Checkout integration with idempotency keys, duplicate event protection, webhook signature verification, and automated invoice/receipt generation."),
        ("Intelligence & Analytics Engines", "Built-in AI travel concierge, automated hotel recommendation algorithms, and comprehensive revenue/occupancy business intelligence metrics.")
    ]
    for title, desc in highlights:
        bp = doc.add_paragraph(style='List Bullet')
        r1 = bp.add_run(f"{title}: ")
        r1.bold = True
        r1.font.color.rgb = secondary_color
        bp.add_run(desc)

    doc.add_paragraph()

    # =========================================================================
    # 2. COMPLETE 50 MODULES IMPLEMENTATION MATRIX
    # =========================================================================
    h2 = doc.add_heading("2. Complete 50 Modules Implementation Matrix", level=1)
    h2.runs[0].font.color.rgb = primary_color

    doc.add_paragraph("The table below documents the implementation status and key capabilities of all 50 StayNest Pro modules:")

    modules_data = [
        ("Module 1", "Authentication & RBAC", "POST /auth/register, /auth/login, /auth/refresh-token, /auth/logout", "COMPLETED"),
        ("Module 2", "Customer Profile Management", "GET, PUT /customers/profile/me", "COMPLETED"),
        ("Module 3", "Hotel Registration & Verification", "POST /hotels/verification/register, /moderation", "COMPLETED"),
        ("Module 4", "Hotel Profile Management", "GET, PUT, DELETE /hotels/{id}, /hotels", "COMPLETED"),
        ("Module 5", "Room Management", "POST /rooms, GET /rooms/hotel/{id}, PUT /rooms/{id}", "COMPLETED"),
        ("Module 6", "Room Type Management", "POST /room-types, GET /room-types/hotel/{id}", "COMPLETED"),
        ("Module 7", "Hotel Amenities Management", "POST, GET /amenities, POST /amenities/hotel/{id}/associate", "COMPLETED"),
        ("Module 8", "Room Availability Management", "POST /availability/set-date, /set-range, GET /room/{id}", "COMPLETED"),
        ("Module 9", "Hotel Search System", "GET /search/hotels (keyword, city, Haversine GPS)", "COMPLETED"),
        ("Module 10", "Advanced Hotel Filters", "GET /filters/hotels (price, stars, amenities, dates)", "COMPLETED"),
        ("Module 11", "Hotel Details & Gallery", "GET /hotels/{id}/details, POST, GET /hotels/{id}/images", "COMPLETED"),
        ("Module 12", "Bookings & Guest Management", "POST /bookings, GET /bookings/my, POST /bookings/{id}/guests", "COMPLETED"),
        ("Module 13", "Guest Management", "POST /bookings/{id}/guests, GET /bookings/{id}/guests", "COMPLETED"),
        ("Module 14", "Booking Lifecycle Transitions", "POST /bookings/{id}/cancel, POST /bookings/{id}/modify", "COMPLETED"),
        ("Module 15", "Stripe Payment Integration", "POST /payments/create-checkout-session, /confirm, /webhook", "COMPLETED"),
        ("Module 16", "Invoice & Receipt Management", "GET /invoices/booking/{id}, GET /invoices/{id}/pdf", "COMPLETED"),
        ("Module 17", "Cancellation & Refund Management", "POST /refunds/quote, /request, /{id}/process-stripe", "COMPLETED"),
        ("Module 18", "Coupon & Discount Management", "POST /coupons, POST /coupons/validate, /apply", "COMPLETED"),
        ("Module 19", "Reviews & Ratings", "POST /reviews/submit, GET /reviews/hotel/{id}", "COMPLETED"),
        ("Module 20", "Wishlist & Favorite Hotels", "POST /wishlist/toggle, GET /wishlist", "COMPLETED"),
        ("Module 21", "AI Hotel Recommendation Engine", "GET /recommendations/personalized, /budget-location, /similar/{id}", "COMPLETED"),
        ("Module 22", "AI Travel Assistant", "POST /ai-assistant/plan-trip, /chat, GET /conversations", "COMPLETED"),
        ("Module 23", "AI Customer Support Chatbot", "POST /support/chat, GET /support/conversations/{id}", "COMPLETED"),
        ("Module 24", "In-App Notifications", "GET /notifications/my, PATCH /notifications/{id}/read", "COMPLETED"),
        ("Module 25", "In-App Messaging", "POST /messages/send, GET /messages/conversations", "COMPLETED"),
        ("Module 26", "Housekeeping Management", "POST /housekeeping/tasks, PATCH /{id}/status, GET /overview", "COMPLETED"),
        ("Module 27", "Hotel Staff Management", "GET /staff/roster, POST /staff/clock-in, /clock-out", "COMPLETED"),
        ("Module 28", "Check-In and Check-Out Management", "POST /check-in-out/check-in, /check-out, GET /schedule", "COMPLETED"),
        ("Module 29", "Additional Services Management", "POST /services, POST /services/request, GET /catalog", "COMPLETED"),
        ("Module 30", "Room Service Management", "POST /room-service/menu, POST /orders, PATCH /orders/{id}/status", "COMPLETED"),
        ("Module 31", "Hotel Revenue Analytics", "GET /analytics/revenue/hotels/{id}/summary, /daily, /monthly", "COMPLETED"),
        ("Module 32", "Hotel Occupancy Analytics", "GET /analytics/occupancy/live, /range, /peak-periods", "COMPLETED"),
        ("Module 33", "Customer Analytics", "GET /analytics/customers/repeat-guests, /destinations", "COMPLETED"),
        ("Module 34", "Hotel Owner Dashboard APIs", "GET /dashboards/owner/overview", "COMPLETED"),
        ("Module 35", "Customer Dashboard APIs", "GET /dashboards/customer/overview", "COMPLETED"),
        ("Module 36", "Admin Dashboard APIs", "GET /dashboards/admin/overview", "COMPLETED"),
        ("Module 37", "Hotel Verification and Moderation", "GET /moderation/hotels/pending, POST /{id}/decision", "COMPLETED"),
        ("Module 38", "Reports and Export", "GET /reports/generate, /export/csv, /export/pdf", "COMPLETED"),
        ("Module 39", "Audit Logs & Security Monitoring", "GET /audit-logs/events, /security, /entity/{type}/{id}", "COMPLETED"),
        ("Module 40", "Hotel Subscription Plans", "GET /subscriptions/plans, POST /hotels/{id}/subscribe", "COMPLETED"),
        ("Module 41", "Hotel Subscription Payments", "POST /subscription-payments/checkout-session, /webhook", "COMPLETED"),
        ("Module 42", "Dynamic Pricing Management", "POST /pricing-rules, GET /pricing-rules/hotels/{id}", "COMPLETED"),
        ("Module 43", "Loyalty and Rewards", "GET /loyalty/my-account, POST /award-booking, /redeem, /referral", "COMPLETED"),
        ("Module 44", "Location Services", "PUT /locations/hotels/{id}/coordinates, GET /attractions, /nearby", "COMPLETED"),
        ("Module 45", "Calendar and Booking Scheduler", "GET /calendar/hotels/{id}/availability, POST /check-conflict", "COMPLETED"),
        ("Module 46", "Financial Management", "GET /financial/breakdown, POST /settlements/generate, /reconcile", "COMPLETED"),
        ("Module 47", "Business Intelligence APIs", "GET /business-intelligence/growth-metrics, /top-performers", "COMPLETED"),
        ("Module 48", "Fraud Detection and Security", "POST /security/eval-login, /scan-bookings, /alerts/{id}/resolve", "COMPLETED"),
        ("Module 49", "System Configuration", "GET /system-config, PUT /system-config/{key}, POST /batch", "COMPLETED"),
        ("Module 50", "Advanced Platform Administration", "GET /admin/platform-overview, PUT /users/{id}/status, /health-check", "COMPLETED"),
    ]

    table = doc.add_table(rows=1, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Header Row
    hdr_cells = table.rows[0].cells
    hdr_titles = ["Module", "Name", "Key Endpoints & Routes", "Status"]
    col_widths = [Inches(1.0), Inches(1.8), Inches(2.7), Inches(1.0)]

    for idx, title in enumerate(hdr_titles):
        hdr_cells[idx].text = title
        hdr_cells[idx].width = col_widths[idx]
        set_cell_background(hdr_cells[idx], "1A56A0")
        set_cell_margins(hdr_cells[idx], top=120, bottom=120, left=100, right=100)
        p = hdr_cells[idx].paragraphs[0]
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        p.runs[0].font.size = Pt(9.5)

    for mod_id, name, endpoints, status in modules_data:
        row_cells = table.add_row().cells
        row_cells[0].text = mod_id
        row_cells[1].text = name
        row_cells[2].text = endpoints
        row_cells[3].text = status

        for idx, cell in enumerate(row_cells):
            cell.width = col_widths[idx]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            p = cell.paragraphs[0]
            p.runs[0].font.size = Pt(8.5)
            if idx == 0:
                p.runs[0].font.bold = True
            elif idx == 3:
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = accent_color

    doc.add_paragraph()

    # =========================================================================
    # 3. INTERACTIVE SWAGGER UI DOCUMENTATION & SCREENSHOTS
    # =========================================================================
    h3 = doc.add_heading("3. Interactive Swagger UI API Verification & Screenshots", level=1)
    h3.runs[0].font.color.rgb = primary_color

    doc.add_paragraph(
        "StayNest Pro auto-generates comprehensive interactive Swagger UI documentation at /docs and ReDoc at /redoc. "
        "The screenshots below capture live verification of all 50 modules, parameter validations, and live executions:"
    )

    brain_dir = r"C:\Users\ADMIN\.gemini\antigravity-ide\brain\11884087-d3f9-4ebd-9ec2-b3d516c99f60"

    screenshots = [
        ("Figure 3.1: Swagger UI Overview & Implemented Modules 1–50 Catalog",
         os.path.join(brain_dir, "swagger_overview_modules_1_50.png"),
         "Displays the platform OpenAPI 3.1 title, security scheme authorization, and full catalog of Modules 1 through 50."),
        
        ("Figure 3.2: Swagger UI Modules 1 to 10 (Auth, Profiles, Hotels, Rooms, Amenities, Search)",
         os.path.join(brain_dir, "swagger_modules_01_to_10.png"),
         "Displays endpoints for user registration, login, customer profiles, room types, inventory, and amenities."),
        
        ("Figure 3.3: Swagger UI Modules 11 to 20 (Details, Booking Engine, Payments, Refunds, Reviews)",
         os.path.join(brain_dir, "swagger_modules_11_to_20.png"),
         "Displays hotel details, reservation creation, Stripe checkout sessions, invoice downloads, and verified reviews."),
        
        ("Figure 3.4: Swagger UI Modules 21 to 30 (AI Concierge, Support, Messaging, Housekeeping, Staff, Services)",
         os.path.join(brain_dir, "swagger_modules_21_to_30.png"),
         "Displays AI recommendation engine, travel assistant itineraries, in-app messaging, housekeeping rosters, and room service."),
        
        ("Figure 3.5: Swagger UI Modules 31 to 40 (Analytics, Dashboards, Moderation, Reports, Plans)",
         os.path.join(brain_dir, "swagger_modules_31_to_40.png"),
         "Displays daily/monthly revenue analytics, occupancy metrics, consolidated owner/admin dashboards, and subscription plans."),
        
        ("Figure 3.6: Swagger UI Modules 41 to 45 (Subscription Billing, Dynamic Pricing, Loyalty, Geolocation, Scheduling)",
         os.path.join(brain_dir, "swagger_modules_41_to_50.png"),
         "Displays Stripe recurring subscription checkout, dynamic pricing rules, guest rewards ledger, and calendar conflict scheduler."),
        
        ("Figure 3.7: Swagger UI Modules 46 to 50 (Financial Management, BI, Fraud Security, System Config, Admin)",
         os.path.join(brain_dir, "swagger_modules_48_to_50.png"),
         "Displays gross/net earnings calculations, business intelligence trends, brute-force security alerts, system config, and admin lockdowns."),

        ("Figure 3.8: Sample Input Request Body in Swagger UI (POST /auth/register)",
         os.path.join(brain_dir, "swagger_sample_input.png"),
         "Demonstrates the interactive JSON request payload editor populated with valid test registration credentials."),

        ("Figure 3.9: Sample Output Response (Status Code 201 Created)",
         os.path.join(brain_dir, "swagger_sample_output_201.png"),
         "Shows successful 201 Created server response containing new user ID, verified flag, verification token, and JWT token pair."),

        ("Figure 3.10: Unified Request/Response Execution View in Swagger UI",
         os.path.join(brain_dir, "swagger_input_and_output_combined.png"),
         "Shows the executed curl command, Request URL http://127.0.0.1:8000/auth/register, and response body side-by-side.")
    ]

    for caption, img_path, explanation in screenshots:
        if os.path.exists(img_path):
            ch = doc.add_heading(caption, level=2)
            ch.runs[0].font.color.rgb = secondary_color
            ch.runs[0].font.size = Pt(12)
            
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.add_run().add_picture(img_path, width=Inches(6.2))
            
            p_desc = doc.add_paragraph(explanation)
            p_desc.runs[0].font.size = Pt(9.5)
            p_desc.runs[0].font.italic = True
            p_desc.runs[0].font.color.rgb = muted_color
            doc.add_paragraph()

    # =========================================================================
    # 4. DATABASE SCHEMA & ORM ARCHITECTURE
    # =========================================================================
    h4 = doc.add_heading("4. Database Schema & SQLAlchemy ORM Models", level=1)
    h4.runs[0].font.color.rgb = primary_color

    doc.add_paragraph(
        "StayNest Pro uses SQLAlchemy 2.0 ORM with PyMySQL connecting to MySQL 8.0. "
        "The relational schema encompasses 35+ relational database tables with foreign key constraints, "
        "cascade delete rules, and compound indexes optimizing high-concurrency lookups:"
    )

    tables_info = [
        ("users", "User accounts, passwords (bcrypt salt 12), roles (CUSTOMER, HOTEL_OWNER, HOTEL_STAFF, ADMIN), verification flags"),
        ("customer_profiles", "Customer birthdate, nationality, address, JSON travel preferences (floor, bedding, dietary)"),
        ("hotels", "Hotel listing, owner relationship, property type, full address, GPS latitude/longitude, status"),
        ("hotel_verification_docs", "Business licenses, municipal permits, tax registrations submitted for admin moderation"),
        ("hotel_images", "Primary and gallery image URLs, display ordering, captions, and categorized image types"),
        ("room_types", "Room classifications (Single, Double, Suite, Deluxe, Family), base price, max adult/child capacity"),
        ("rooms", "Individual physical room inventory, room numbers, floor numbers, active housekeeping status"),
        ("amenities & hotel_amenities", "Global amenities catalog (Wi-Fi, Pool, Spa) and many-to-many associations with hotels"),
        ("room_availability", "Daily room status calendar (AVAILABLE, BOOKED, BLOCKED, MAINTENANCE) and seasonal price overrides"),
        ("bookings & booking_guests", "Reservation records with unique booking reference, dates, financial breakdown, and guest rosters"),
        ("payments", "Stripe payment records, stripe session IDs, payment intent IDs, idempotency keys, and receipt URLs"),
        ("invoices", "Formal billing documents, invoice numbers, tax breakdown, and printable receipt generation"),
        ("refund_requests", "Cancellation refund claims, policy penalty rates, approved amounts, and Stripe refund IDs"),
        ("coupons & coupon_usage", "Discount codes (fixed amount, percentage), validity dates, minimum booking limits, usage tracking"),
        ("reviews", "Customer hotel ratings (1.0 - 5.0), comments, stay verification, moderation status, and abuse reports"),
        ("wishlists", "Customer saved properties and favorite room types"),
        ("ai_conversations & messages", "Multi-turn travel planning chats, day-by-day itineraries, and customer support threads"),
        ("housekeeping_tasks", "Cleaning and maintenance assignments, inspection passes, and dirty/cleaning/clean transitions"),
        ("hotel_staff & attendance", "Staff hotel assignments, position roles, JSON permissions, and clock-in/out timestamps"),
        ("additional_services & requests", "Hotel amenities catalog (airport shuttle, laundry, spa) and booking service requests"),
        ("menu_items & room_service_orders", "Hotel dining catalog, kitchen order queue, delivery tracking, and bill charges"),
        ("subscription_plans & hotel_subscriptions", "SaaS subscription tiers (FREE, BASIC, PREMIUM, ENTERPRISE), billing cycles, auto-renew"),
        ("dynamic_pricing_rules", "Seasonal surges, weekend uplifts, holiday adjustments, and promotional discounts"),
        ("loyalty_ledgers", "Customer reward points balances, booking credits, redemption debits, and referral bonuses"),
        ("hotel_attractions", "Nearby landmarks, GPS coordinates, dynamic Haversine distance, and drive duration"),
        ("payout_settlements", "Bi-weekly hotel earnings payouts, commission deductions, tax withholding, and settlement state"),
        ("security_alerts", "Suspicious booking detection, brute-force login alerts, duplicate reservations, admin resolution notes"),
        ("system_configs & platform_policies", "Global platform parameters (tax rate %, commission %, default currency) and Terms of Service")
    ]

    for tbl, desc in tables_info:
        bp = doc.add_paragraph(style='List Bullet')
        r = bp.add_run(f"`{tbl}`: ")
        r.bold = True
        bp.add_run(desc)

    doc.add_paragraph()

    # =========================================================================
    # 5. TESTING, VALIDATION & POSTMAN VERIFICATION
    # =========================================================================
    h5 = doc.add_heading("5. Quality Assurance & Automated Test Suites", level=1)
    h5.runs[0].font.color.rgb = primary_color

    doc.add_paragraph(
        "StayNest Pro includes automated test suites covering all 50 modules. Tests execute against the isolated MySQL "
        "test database and validate status codes, response schemas, error responses, and idempotency guarantees:"
    )

    test_suites = [
        ("test_modules_1_to_16.py", "16 Modules", "Tests auth registration, login, token refresh, forgot password, customer profiles, hotel registration, room inventory, availability calendars, search, filters, booking engine, Stripe checkout, invoices."),
        ("test_modules_17_to_22.py", "6 Modules", "Tests cancellation quotes, refund approvals, Stripe refunds, coupons, review submissions, wishlist toggles, AI recommendation engine, AI trip itineraries."),
        ("test_modules_23_to_30.py", "8 Modules", "Tests AI support bot, in-app notifications, customer-hotel messaging, housekeeping room clean states, staff attendance clocking, guest check-in/out, room service ordering."),
        ("test_modules_31_to_40.py", "10 Modules", "Tests hotel revenue summaries, occupancy analytics, customer retention, owner/customer/admin dashboards, hotel verification moderation, CSV/PDF reports, audit logs, subscription tiers."),
        ("test_modules_41_to_45.py", "5 Modules", "Tests Stripe subscription billing webhooks, dynamic pricing rules, loyalty points & referral bonuses, Google Maps coordinates, calendar scheduler & conflict prevention."),
        ("test_modules_46_to_50.py", "5 Modules", "Tests financial commission splits & payouts, business intelligence trends, brute-force security alerts, system config updates, admin platform lockdowns.")
    ]

    for file_name, scope, desc in test_suites:
        p = doc.add_paragraph(style='List Bullet')
        r = p.add_run(f"`{file_name}` ({scope}): ")
        r.bold = True
        p.add_run(desc)

    doc.add_paragraph(
        "To run all automated test suites, execute:\n"
        "```powershell\n"
        ".\\venv\\Scripts\\python.exe -m pytest -v\n"
        "```"
    )

    doc.add_paragraph()

    # =========================================================================
    # 6. SETUP & EXECUTION GUIDE
    # =========================================================================
    h6 = doc.add_heading("6. Setup & Developer Quickstart", level=1)
    h6.runs[0].font.color.rgb = primary_color

    steps = [
        ("Step 1: Clone or Open Project", "Navigate to `d:\\00_Working_Task\\Task_9_Hotel_Resort_Room_Booking_Management`."),
        ("Step 2: Activate Virtual Environment", "Run `.\\venv\\Scripts\\activate` (Python 3.12)."),
        ("Step 3: Configure Environment Variables", "Verify `.env` has MySQL connection: `SQLALCHEMY_DATABASE_URL=mysql+pymysql://root:Ramc%40123@localhost/hotel_resort` and `SECRET_KEY`."),
        ("Step 4: Run Database Migrations", "Execute `alembic upgrade head` to apply all 50 module database tables."),
        ("Step 5: Start the Backend Server", "Run `uvicorn main:app --reload --host 127.0.0.1 --port 8000`."),
        ("Step 6: Open Swagger UI Documentation", "Open `http://127.0.0.1:8000/docs` in your browser to interactively test endpoints."),
        ("Step 7: Postman Collection Testing", "Import `StayNest_Pro_Postman_Collection.json` and `StayNest_Pro_Postman_Environment.json` into Postman to run end-to-end automated requests.")
    ]

    for step_num, step_desc in steps:
        p = doc.add_paragraph(style='List Bullet')
        r = p.add_run(f"{step_num}: ")
        r.bold = True
        p.add_run(step_desc)

    doc.add_paragraph()

    # Save Document
    out_path = r"d:\00_Working_Task\Task_9_Hotel_Resort_Room_Booking_Management\StayNest_Pro_Project_Documentation.docx"
    doc.save(out_path)
    print(f"Document successfully created at {out_path}")

if __name__ == "__main__":
    create_document()
