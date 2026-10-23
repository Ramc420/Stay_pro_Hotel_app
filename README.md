# StayNest Pro – Hotel, Resort & Room Booking Management Platform

StayNest Pro is an enterprise-grade backend developed with **FastAPI**, **Python**, **MySQL**, **SQLAlchemy ORM**, **Pydantic v2**, and **JWT Authentication** implementing **Role-Based Access Control (RBAC)** across multi-tier user roles (**CUSTOMER**, **HOTEL_OWNER**, **HOTEL_STAFF**, **ADMIN**).

---

## 🚀 Key Features & Implemented Modules

| Module | Name | Endpoints & Features |
|---|---|---|
| **Module 1** | **Authentication & RBAC** | User registration, login, JWT access & refresh tokens, token blacklist invalidation, logout, forgot/reset password, email verification, admin role management, protected endpoint dependencies. |
| **Module 2** | **Customer Profile Management** | Full CRUD for customer profiles, travel preferences (smoking, dietary, floor, bed type), avatar picture upload, secure validation, and admin moderation. |
| **Module 3** | **Hotel Registration & Verification** | Hotel onboarding, business license & certificate document upload, submission for approval, admin application approval/rejection with reasons, suspension/reactivation. |
| **Module 4** | **Hotel Profile Management** | Comprehensive hotel details, addresses, contact details, policies, check-in/check-out rules, gallery image management with primary image selector, owner hotel listings. |
| **Module 5** | **Room Management** | CRUD rooms, floor numbering, status management (`AVAILABLE`, `OCCUPIED`, `MAINTENANCE`, `CLEANING`, `RESERVED`), strict duplicate room number prevention per hotel, owner/staff authorization. |
| **Module 6** | **Room Type Management** | Single, Double, Deluxe, Suite, Family categories, base pricing, occupancy capacity (adults/children), bed types, room size, amenities included, photo gallery. |
| **Module 7** | **Hotel Amenities Management** | System-wide amenities catalog, hotel-to-amenity associations, hotel amenities retrieval, and multi-amenity filtering. |
| **Module 8** | **Room Availability Management** | Daily availability tracking, date-range bulk blocking (maintenance/renovation), conflict prevention for booked dates, calendar visualization, and guest capacity search. |
| **Module 9** | **Hotel Search System** | Full-text keyword search across hotel names, cities, and countries; room type and capacity filters; **Haversine formula** GPS radius search; pagination; and sorting. |
| **Module 10** | **Advanced Hotel Filters** | Multi-criteria filtering by price range (`min_price`, `max_price`), star rating (`min_rating`), property type (`HOTEL`, `RESORT`, `VILLA`), amenities list, check-in/check-out date inventory availability. |
| **Module 11** | **Hotel Details and Gallery** | Complete hotel details retrieval (room info, amenities, reviews, policies), image metadata management (title, caption, type, display order, primary selection), and unpublished hotel privacy restrictions. |
| **Module 12** | **Room Booking System** | Reservation creation with check-in/check-out dates, guest count validation, room availability checks, pricing & tax calculations, unique references (`BK-YYYYMMDD-XXXXXX`), and booking history. |
| **Module 13** | **Guest Management** | Linked guest storage, identification validation (PASSPORT, NATIONAL_ID, DRIVING_LICENSE), capacity enforcement, and authorized hotel guest history queries. |
| **Module 14** | **Booking Management** | Booking lifecycle transitions (`CONFIRMED` -> `CHECKED_IN` -> `CHECKED_OUT` -> `COMPLETED`, `CANCELLED`), reservation modifications, date release upon cancellation, conflict prevention, and audit history logs. |
| **Module 15** | **Stripe Payment Integration** | Stripe Checkout session creation with idempotency keys preventing double-charging, payment confirmation, webhook event listeners, and payment status tracking. |
| **Module 16** | **Invoice & Receipt Management** | Automated invoice generation (`INV-YYYYMMDD-XXXX`), tax calculation, authorized printable HTML/PDF receipt downloads, customer and hotel invoice history. |
| **Module 17** | **Cancellation & Refund Management** | Hotel cancellation policies (Flexible, Moderate, Strict, Non-refundable), penalty calculation, refund submission, owner/admin approvals, and Stripe refund processing. |
| **Module 18** | **Coupon & Discount Management** | Fixed and percentage coupons, expiry dates, global & per-user usage limits, seasonal & early-booking requirements, minimum booking thresholds, duplicate prevention. |
| **Module 19** | **Reviews & Ratings** | Eligible completed-stay reviews, author edit/delete, automatic average hotel star rating recalculation, abuse reporting, and admin moderation (approve/hide/remove). |
| **Module 20** | **Wishlist & Favorite Hotels** | Add/remove favorite hotels and specific rooms, duplicate wishlist entry prevention, favorite status queries, customer wishlist catalog. |
| **Module 21** | **AI Hotel Recommendation Engine** | Collaborative & content-based personalized recommendations, budget & location suggestions, similar-hotel recommendations, with graceful offline fallback. |
| **Module 22** | **AI Travel Assistant** | Interactive AI travel concierge, structured day-by-day itineraries, suggested hotels, packing tips, conversation context memory, external LLM provider integration. |
| **Module 23** | **AI Customer Support Chatbot** | Support conversations, FAQ intelligence, authorized booking status lookup, sensitive data masking, conversation closure. |
| **Module 24** | **In-App Notifications** | Booking, payment, refund, cancellation, check-in/out alerts, unread counters, mark single/all as read. |
| **Module 25** | **In-App Messaging** | Guest-to-hotel and guest-to-support direct messaging, conversation histories, unread badges, participant access control. |
| **Module 26** | **Housekeeping Management** | Room cleaning status tracking (`CLEAN`, `DIRTY`, `CLEANING`, `INSPECTION`, `MAINTENANCE`), staff task assignments, inspection records. |
| **Module 27** | **Hotel Staff Management** | Hotel staff rosters, roles & permissions, attendance clock-in/out tracking, immutable staff audit activity logs. |
| **Module 28** | **Check-In and Check-Out Management** | Guest reservation verification, automated room status transitions, early check-in & late check-out fee calculations, arrivals schedule. |
| **Module 29** | **Additional Services Management** | Hotel services catalog (airport pickup, laundry, spa, breakfast), booking service requests, cost calculation, fulfillment tracking. |
| **Module 30** | **Room Service Management** | Food & beverage menu catalog, dietary tagging, room service ordering, kitchen status queue (`PLACED`, `PREPARING`, `DELIVERED`). |
| **Module 31** | **Hotel Revenue Analytics** | Daily and monthly revenue aggregations, Average Booking Value (ABV), refund deductions, earnings breakdown. |
| **Module 32** | **Hotel Occupancy Analytics** | Live occupancy snapshots, date-range occupancy rate formulas, available vs occupied rooms, peak booking period analysis. |
| **Module 33** | **Customer Analytics** | Booking frequency, customer lifetime spend, repeat guest identification, top destination demand aggregation. |
| **Module 34** | **Hotel Owner Dashboard APIs** | Consolidated owner command center: today's arrivals/departures, room counts, live revenue & occupancy, recent reviews. |
| **Module 35** | **Customer Dashboard APIs** | Personalized guest portal: upcoming reservations, booking history, wishlist count, total spent, recommended stays. |
| **Module 36** | **Admin Dashboard APIs** | Platform-wide KPIs: total gross volume, active properties, system-wide occupancy, pending hotel verification queue. |
| **Module 37** | **Hotel Verification and Moderation** | Admin review queue for business licenses, approved/rejected status updates with logged reasoning, hotel suspension & reactivation. |
| **Module 38** | **Reports and Export** | Dynamic report generation for bookings, revenue, and occupancy with export downloads in JSON, CSV, and printable PDF. |
| **Module 39** | **Audit Logs & Security Monitoring** | Immutable audit trail for authentication, payments, data modifications, security events, and severity filtering. |
| **Module 40** | **Hotel Subscription Plans** | SaaS subscription tiers (`FREE`, `BASIC`, `PREMIUM`, `ENTERPRISE`), billing cycles, auto-renewals, premium feature access. |
| **Module 41** | **Hotel Subscription Payments** | Stripe recurring billing integration, subscription checkout sessions, plan upgrades/downgrades, invoice webhooks. |
| **Module 42** | **Dynamic Pricing Management** | Seasonal surges, weekend pricing, holiday rates, promotional discounts, pricing rule conflict prevention. |
| **Module 43** | **Loyalty and Rewards** | Points earning per completed stay, points redemption towards booking totals, member tier benefits (Bronze/Silver/Gold/Platinum), referral rewards. |
| **Module 44** | **Location Services** | Verified GPS coordinates, Haversine nearby radius hotel search, local tourist attractions, Google Maps distance matrix calculations. |
| **Module 45** | **Calendar and Booking Scheduler** | Room availability calendar matrix, atomic double-booking conflict detection, daily arrival schedules, scheduled background jobs. |
| **Module 46** | **Financial Management** | Financial transaction ledgers, gross earnings vs platform commission splits, tax accounting, bi-weekly payout settlement generation, reconciliation. |
| **Module 47** | **Business Intelligence APIs** | Month-over-month revenue and booking growth rates, top-performing hotels and destination cities, multi-month occupancy trends, executive summaries. |
| **Module 48** | **Fraud Detection and Security** | Suspicious booking pattern detection, brute-force login anomaly detection, duplicate reservation flags, security alert resolution workflows. |
| **Module 49** | **System Configuration** | Dynamic platform settings (occupancy tax %, platform commission %, currency, notification toggles), secret masking, validation bounds. |
| **Module 50** | **Advanced Platform Administration** | Platform health diagnostics (database latency, server memory), account lockdowns, emergency booking status overrides, Terms of Service policy management. |


---

## 🛠️ Technology Stack

- **Backend Framework:** FastAPI
- **Language:** Python 3.12+
- **Database:** MySQL 8.0
- **Database Driver:** PyMySQL
- **ORM:** SQLAlchemy 2.0
- **Data Validation:** Pydantic v2
- **Authentication:** JWT (PyJWT) with Access & Refresh tokens, Token Blacklist
- **Password Security:** bcrypt hashing (salt rounds: 12)
- **Database Migrations:** Alembic
- **Documentation:** Interactive Swagger UI (`/docs`) & ReDoc (`/redoc`)
- **API Testing:** Postman Collection (`StayNest_Pro_Postman_Collection.json`) & Environment included

---

## 📦 Project Directory Structure

```text
Task_9_Hotel_Resort_Room_Booking_Management/
├── database.py                        # SQLAlchemy database connection & session generator
├── config.py                          # App settings loaded from .env
├── main.py                            # FastAPI entry point, Swagger, CORS, error handling
├── alembic.ini                        # Alembic migration configuration
├── alembic/                           # Alembic migration environment and versions
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 83fbb3f5df9d_initial_schema_modules_1_to_10.py
├── auth/                              # Authentication & RBAC security layer
│   ├── __init__.py
│   ├── jwt_handler.py                 # Token generation, decoding, bcrypt password hashing
│   └── dependencies.py                # get_current_user, require_roles (RBAC), verify_hotel_access
├── models/                            # Modular SQLAlchemy ORM models with two-way relationships
│   ├── __init__.py
│   ├── user.py                        # Users, roles, hotel staff, token blacklist
│   ├── customer.py                    # Customer profiles & travel preferences
│   ├── hotel.py                       # Hotels, verification docs, hotel images & gallery
│   ├── room.py                        # Rooms, room types, bed types
│   ├── amenity.py                     # Amenities catalog & hotel associations
│   ├── availability.py                # Daily room availability calendars
│   ├── review.py                      # Module 11: Hotel reviews and star ratings
│   ├── booking.py                     # Modules 12, 13, 14: Bookings, guests, audit history
│   ├── payment.py                     # Module 15: Stripe payments & idempotency keys
│   ├── invoice.py                     # Module 16: Invoices & billing records
│   ├── refund.py                      # Module 17: Refund requests & cancellation policies
│   ├── coupon.py                      # Module 18: Coupons & coupon usages
│   ├── wishlist.py                    # Module 20: Wishlist & favorite hotels
│   └── ai_assistant.py                # Module 22: AI conversations & messages
├── schemas/                           # Pydantic v2 validation models
│   ├── __init__.py
│   ├── common.py                      # ApiResponse wrapper & pagination metadata
│   ├── user.py                        # Auth & user schemas
│   ├── customer.py                    # Customer profile schemas
│   ├── hotel.py                       # Hotel profile & gallery schemas
│   ├── room.py                        # Room & room type schemas
│   ├── amenity.py                     # Amenity schemas
│   ├── availability.py                # Availability schemas
│   ├── search.py                      # Search results schemas
│   ├── review.py                      # Module 19: Review submission, breakdown & moderation
│   ├── booking.py                     # Modules 12, 13, 14: Booking & guest schemas
│   ├── payment.py                     # Module 15: Stripe checkout & payment schemas
│   ├── invoice.py                     # Module 16: Invoicing schemas
│   ├── refund.py                      # Module 17: Cancellation quotes & refund requests
│   ├── coupon.py                      # Module 18: Coupon creation, validation & redemption
│   ├── wishlist.py                    # Module 20: Wishlist schemas
│   ├── recommendation.py              # Module 21: Hotel recommendation schemas
│   └── ai_assistant.py                # Module 22: AI trip planner & chat concierge
├── crud/                              # Modular database service layer
│   ├── __init__.py
│   ├── user.py
│   ├── customer.py
│   ├── hotel.py
│   ├── room.py
│   ├── amenity.py
│   ├── availability.py
│   ├── search.py
│   ├── review.py                      # Module 19 reviews, rating recalculation & moderation
│   ├── booking.py                     # Modules 12, 13, 14 booking engine & lifecycle
│   ├── payment.py                     # Module 15 Stripe integration & idempotency
│   ├── invoice.py                     # Module 16 tax calculations & HTML receipts
│   ├── refund.py                      # Module 17 cancellation policy engine & refunds
│   ├── coupon.py                      # Module 18 coupon validation & discount calculation
│   ├── wishlist.py                    # Module 20 wishlist management
│   ├── recommendation.py              # Module 21 AI personalized & heuristic recommendations
│   └── ai_assistant.py                # Module 22 AI trip planner & contextual chat assistant
├── routers/                           # FastAPI API route controllers
│   ├── __init__.py
│   ├── auth.py                        # Module 1 endpoints
│   ├── customer_profiles.py           # Module 2 endpoints
│   ├── hotel_verification.py          # Module 3 endpoints
│   ├── hotel_profiles.py              # Module 4 endpoints
│   ├── rooms.py                       # Module 5 endpoints
│   ├── room_types.py                  # Module 6 endpoints
│   ├── amenities.py                   # Module 7 endpoints
│   ├── room_availability.py           # Module 8 endpoints
│   ├── hotel_search.py                # Module 9 endpoints
│   ├── hotel_filters.py               # Module 10 endpoints
│   ├── hotel_details_gallery.py       # Module 11 endpoints
│   ├── bookings.py                    # Modules 12, 13, 14 endpoints
│   ├── payments.py                    # Module 15 endpoints
│   ├── invoices.py                    # Module 16 endpoints
│   ├── refunds.py                     # Module 17 endpoints
│   ├── coupons.py                     # Module 18 endpoints
│   ├── reviews.py                     # Module 19 endpoints
│   ├── wishlists.py                   # Module 20 endpoints
│   ├── recommendations.py             # Module 21 endpoints
│   └── ai_assistant.py                # Module 22 endpoints
├── utils/                             # Core utilities
│   ├── __init__.py
│   ├── response.py                    # Standard JSON response wrappers & pagination
│   ├── geo.py                         # Haversine distance calculator
│   └── file_upload.py                 # Secure file uploads for avatars, docs, images
├── uploads/                           # Static file upload repository
│   ├── avatars/
│   ├── documents/
│   └── hotels/
├── StayNest_Pro_Postman_Collection.json   # Exported Postman test suite (Modules 1-22)
├── StayNest_Pro_Postman_Environment.json  # Postman environment variables
├── .env                               # Environment configuration
├── .env.example                       # Sample environment configuration
└── requirements.txt                   # Project dependencies
```



---

## ⚙️ Setup and Installation

### 1. Configure the Environment
Ensure your MySQL server is running and the database exists:
```sql
CREATE DATABASE IF NOT EXISTS hotel_resort CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Edit your `.env` file or use the pre-configured parameters:
```ini
PROJECT_NAME="StayNest Pro – Hotel, Resort & Room Booking Management"
SQLALCHEMY_DATABASE_URL="mysql+pymysql://root:Ramc%40123@localhost/hotel_resort"
SECRET_KEY="staynest-pro-secure-jwt-secret-key-32charslong!"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
UPLOAD_DIR="uploads"
MAX_FILE_SIZE_MB=10
```

### 2. Apply Database Migrations (Alembic)
```bash
alembic upgrade head
```

### 3. Launch the API Server
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
The server will automatically start at: **http://127.0.0.1:8000**
- Interactive Swagger UI: **http://127.0.0.1:8000/docs**
- ReDoc Documentation: **http://127.0.0.1:8000/redoc**
- Health Check: **http://127.0.0.1:8000/health**

---

## 🛡️ Default System Credentials & RBAC Roles

Upon the first startup, the database is automatically seeded with:
1. **System Administrator Account**:
   - **Email:** `admin@staynest.com`
   - **Password:** `Admin@123456`
   - **Role:** `ADMIN`
2. **12 Standard Hotel Amenities**:
   - Free Wi-Fi, Swimming Pool, Spa & Wellness, Fitness Center, Free Parking, Restaurant & Dining, Bar & Lounge, Airport Shuttle, Pet Friendly, Air Conditioning, 24-Hour Front Desk, Business Center.

### Role Permissions:
- **`CUSTOMER`**: Can manage own profile, travel preferences, search & filter hotels, view rooms and availability.
- **`HOTEL_OWNER`**: Can register hotels, submit verification documents, manage room types, rooms, hotel galleries, and availability for approved owned hotels.
- **`HOTEL_STAFF`**: Can access assigned hotel operational functions (room status updates, availability calendars).
- **`ADMIN`**: Platform-wide access. Can approve/reject hotel registrations, suspend/reactivate listings, update user roles, and manage global amenities.

---

## 📡 API Verification, Automated Testing & Documentation

All 50 modules are organized into decoupled layers (`models`, `schemas`, `crud`, and `routers`) with automated test suites, Postman collections, and interactive Swagger documentation:

1. **Interactive Swagger UI:**
   - Run the application (`uvicorn main:app --reload`) and navigate to `http://localhost:8000/docs`
   - Use the **Authorize** button with `Bearer <token>` to authenticate as `CUSTOMER`, `HOTEL_OWNER`, `HOTEL_STAFF`, or `ADMIN`.
2. **ReDoc Interactive Documentation:**
   - Available at `http://localhost:8000/redoc`.
3. **Automated Pytest Test Suites (100% Passing):**
   - Execute all test suites across all 50 modules against the isolated MySQL test database:
   ```bash
   .\venv\Scripts\python.exe -m pytest -v
   ```
   Or run individual module test suites:
   - `python test_modules_1_to_16.py` (Auth, Inventory, Search, Bookings, Payments, Invoices)
   - `python test_modules_17_to_22.py` (Refunds, Coupons, Reviews, Wishlists, AI Recommendations, Concierge)
   - `python test_modules_23_to_30.py` (AI Support, Notifications, Messaging, Housekeeping, Staff, Room Service)
   - `python test_modules_31_to_40.py` (Analytics, Dashboards, Moderation, Reports, Audit Logs, Plans)
   - `python test_modules_41_to_45.py` (Stripe Subscriptions, Dynamic Pricing, Loyalty, Geolocation, Scheduler)
   - `python test_modules_46_to_50.py` (Financials, BI Trends, Fraud Security, System Config, Admin Overrides)
4. **Complete Project Documentation (.docx):**
   - Full Word document with architecture, 50 modules matrix, and live Swagger UI screenshots: `StayNest_Pro_Project_Documentation.docx`.

---

## 📮 Postman Collection Import

1. Open Postman.
2. Click **Import** -> Select `StayNest_Pro_Postman_Collection.json`.
3. Click **Import** -> Select `StayNest_Pro_Postman_Environment.json`.
4. Set the active environment to **StayNest Pro Environment**.
5. Run the **Authentication and RBAC** -> **1. Admin Login** request. The test script will automatically save your `access_token` into the environment, authenticating all subsequent requests.

