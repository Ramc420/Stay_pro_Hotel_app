# StayNest Pro — Project Documentation
## Hotel, Resort & Room Booking Management Platform

**Document Version:** 1.0.0  
**Stack:** FastAPI | Python 3.12 | MySQL 8.0 | SQLAlchemy 2.0 ORM | Pydantic v2 | Pytest | Postman  
**Artifact File:** [StayNest_Pro_Project_Documentation.docx](file:///d:/00_Working_Task/Task_9_Hotel_Resort_Room_Booking_Management/StayNest_Pro_Project_Documentation.docx)

---

## 1. Executive Summary & Architecture Overview

**StayNest Pro** is an enterprise-grade backend management platform for hotels, luxury resorts, and room bookings. The application is developed strictly as a backend-only RESTful API service (no React, HTML, CSS, frontend integration, or frontend dashboard dependencies), delivering high-performance, asynchronous endpoints validated via interactive Swagger UI documentation, Postman suites, and automated pytest test suites.

### Core Architectural Principles:
1. **Separation of Concerns:** Clean four-tier modular structure:
   - `models/`: SQLAlchemy ORM entity classes with bidirectional relationships and cascading rules.
   - `schemas/`: Pydantic v2 request/response validation contracts.
   - `crud/`: Isolated database transactional operations and business logic.
   - `routers/`: FastAPI route controllers with HTTP status codes and RBAC guards.
2. **Strict Role-Based Access Control (RBAC):** Cryptographically signed JWT tokens (PyJWT + bcrypt) enforcing four privilege levels:
   - `CUSTOMER`: Reservation booking, payment checkout, review submission, wishlists, personal dashboard.
   - `HOTEL_OWNER`: Hotel profile management, room types, room inventory, pricing rules, staff assignment, revenue dashboard.
   - `HOTEL_STAFF`: Operational task execution, housekeeping updates, guest check-in/out, kitchen room service fulfillment.
   - `ADMIN`: Platform-wide governance, hotel verification approvals/suspensions, policy controls, system diagnostics, configuration.
3. **Double-Booking & Conflict Prevention:** Atomic database querying and date-overlap checking guarantees zero room double-booking.
4. **Financial Safety & Webhook Idempotency:** Stripe Checkout and subscription billing with unique idempotency keys, duplicate event protection, and webhook construct event verification.

---

## 2. All 50 Modules Implementation Matrix

| Module | Name | Key Endpoints | Implementation Status |
|---|---|---|:---:|
| **Module 1** | Authentication & RBAC | `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh-token`, `POST /auth/logout` | **COMPLETED** |
| **Module 2** | Customer Profile Management | `GET /customers/profile/me`, `PUT /customers/profile/me` | **COMPLETED** |
| **Module 3** | Hotel Registration & Verification | `POST /hotels/verification/register`, `POST /hotels/verification/{id}/moderation` | **COMPLETED** |
| **Module 4** | Hotel Profile Management | `GET /hotels`, `GET /hotels/{id}`, `PUT /hotels/{id}`, `DELETE /hotels/{id}` | **COMPLETED** |
| **Module 5** | Room Management | `POST /rooms`, `GET /rooms/hotel/{id}`, `PUT /rooms/{id}`, `DELETE /rooms/{id}` | **COMPLETED** |
| **Module 6** | Room Type Management | `POST /room-types`, `GET /room-types/hotel/{id}`, `PUT /room-types/{id}` | **COMPLETED** |
| **Module 7** | Hotel Amenities Management | `POST /amenities`, `GET /amenities`, `POST /amenities/hotel/{id}/associate` | **COMPLETED** |
| **Module 8** | Room Availability Management | `POST /availability/set-date`, `POST /availability/set-range`, `GET /availability/room/{id}` | **COMPLETED** |
| **Module 9** | Hotel Search System | `GET /search/hotels` (Full-text keyword, city, state, country, Haversine GPS) | **COMPLETED** |
| **Module 10** | Advanced Hotel Filters | `GET /filters/hotels` (Price range, star rating, property type, amenities, dates) | **COMPLETED** |
| **Module 11** | Hotel Details & Gallery | `GET /hotels/{id}/details`, `POST /hotels/{id}/images`, `GET /hotels/{id}/images` | **COMPLETED** |
| **Module 12** | Bookings & Guest Management | `POST /bookings`, `GET /bookings/my`, `GET /bookings/{id}` | **COMPLETED** |
| **Module 13** | Guest Management | `POST /bookings/{id}/guests`, `GET /bookings/{id}/guests` | **COMPLETED** |
| **Module 14** | Booking Lifecycle Transitions | `POST /bookings/{id}/cancel`, `POST /bookings/{id}/modify` | **COMPLETED** |
| **Module 15** | Stripe Payment Integration | `POST /payments/create-checkout-session`, `POST /payments/confirm`, `POST /payments/webhook` | **COMPLETED** |
| **Module 16** | Invoice & Receipt Management | `GET /invoices/booking/{id}`, `GET /invoices/{id}/pdf` | **COMPLETED** |
| **Module 17** | Cancellation & Refund Management | `POST /refunds/quote`, `POST /refunds/request`, `POST /refunds/{id}/process-stripe` | **COMPLETED** |
| **Module 18** | Coupon & Discount Management | `POST /coupons`, `POST /coupons/validate`, `POST /coupons/apply` | **COMPLETED** |
| **Module 19** | Reviews & Ratings | `POST /reviews/submit`, `GET /reviews/hotel/{id}`, `POST /reviews/{id}/report` | **COMPLETED** |
| **Module 20** | Wishlist & Favorite Hotels | `POST /wishlist/toggle`, `GET /wishlist`, `GET /wishlist/check/{hotel_id}` | **COMPLETED** |
| **Module 21** | AI Hotel Recommendation Engine | `GET /recommendations/personalized`, `GET /recommendations/budget-location`, `GET /recommendations/similar/{id}` | **COMPLETED** |
| **Module 22** | AI Travel Assistant | `POST /ai-assistant/plan-trip`, `POST /ai-assistant/chat`, `GET /ai-assistant/conversations` | **COMPLETED** |
| **Module 23** | AI Customer Support Chatbot | `POST /support/chat`, `GET /support/conversations/{id}`, `POST /support/conversations/{id}/close` | **COMPLETED** |
| **Module 24** | In-App Notifications | `GET /notifications/my`, `PATCH /notifications/{id}/read`, `POST /notifications/read-all` | **COMPLETED** |
| **Module 25** | In-App Messaging | `POST /messages/send`, `GET /messages/conversations`, `PATCH /messages/thread/{id}/read` | **COMPLETED** |
| **Module 26** | Housekeeping Management | `POST /housekeeping/tasks`, `PATCH /housekeeping/tasks/{id}/status`, `GET /housekeeping/overview` | **COMPLETED** |
| **Module 27** | Hotel Staff Management | `GET /staff/roster`, `POST /staff/clock-in`, `POST /staff/clock-out`, `GET /staff/logs` | **COMPLETED** |
| **Module 28** | Check-In & Check-Out Management | `POST /check-in-out/check-in`, `POST /check-in-out/check-out`, `GET /check-in-out/schedule` | **COMPLETED** |
| **Module 29** | Additional Services Management | `POST /services`, `GET /services/catalog/{hotel_id}`, `POST /services/request` | **COMPLETED** |
| **Module 30** | Room Service Management | `POST /room-service/menu/{hotel_id}`, `POST /room-service/orders`, `PATCH /room-service/orders/{id}/status` | **COMPLETED** |
| **Module 31** | Hotel Revenue Analytics | `GET /analytics/revenue/hotels/{id}/summary`, `GET /daily`, `GET /monthly` | **COMPLETED** |
| **Module 32** | Hotel Occupancy Analytics | `GET /analytics/occupancy/live`, `GET /range`, `GET /peak-periods` | **COMPLETED** |
| **Module 33** | Customer Analytics | `GET /analytics/customers/repeat-guests`, `GET /destinations`, `GET /retention` | **COMPLETED** |
| **Module 34** | Hotel Owner Dashboard APIs | `GET /dashboards/owner/overview` | **COMPLETED** |
| **Module 35** | Customer Dashboard APIs | `GET /dashboards/customer/overview` | **COMPLETED** |
| **Module 36** | Admin Dashboard APIs | `GET /dashboards/admin/overview` | **COMPLETED** |
| **Module 37** | Hotel Verification & Moderation | `GET /moderation/hotels/pending`, `POST /moderation/hotels/{id}/decision`, `POST /suspend` | **COMPLETED** |
| **Module 38** | Reports & Export | `GET /reports/generate`, `GET /reports/export/csv`, `GET /reports/export/pdf` | **COMPLETED** |
| **Module 39** | Audit Logs & Security Monitoring | `GET /audit-logs/events`, `GET /audit-logs/security`, `GET /audit-logs/entity/{type}/{id}` | **COMPLETED** |
| **Module 40** | Hotel Subscription Plans | `GET /subscriptions/plans`, `POST /subscriptions/hotels/{id}/subscribe`, `POST /cancel` | **COMPLETED** |
| **Module 41** | Hotel Subscription Payments | `POST /subscription-payments/checkout-session`, `POST /webhook`, `GET /history` | **COMPLETED** |
| **Module 42** | Dynamic Pricing Management | `POST /pricing-rules`, `GET /pricing-rules/hotels/{id}`, `POST /pricing-rules/calculate` | **COMPLETED** |
| **Module 43** | Loyalty and Rewards | `GET /loyalty/my-account`, `POST /loyalty/award-booking`, `POST /loyalty/redeem`, `POST /loyalty/referral` | **COMPLETED** |
| **Module 44** | Location Services | `PUT /locations/hotels/{id}/coordinates`, `GET /attractions`, `GET /nearby-hotels` | **COMPLETED** |
| **Module 45** | Calendar & Booking Scheduler | `GET /calendar/hotels/{id}/availability`, `POST /calendar/check-conflict`, `GET /schedule` | **COMPLETED** |
| **Module 46** | Financial Management | `GET /financial/breakdown`, `POST /financial/settlements/generate`, `POST /reconcile` | **COMPLETED** |
| **Module 47** | Business Intelligence APIs | `GET /business-intelligence/growth-metrics`, `GET /top-performers`, `GET /executive-summary` | **COMPLETED** |
| **Module 48** | Fraud Detection & Security | `POST /security/eval-login`, `POST /security/scan-bookings`, `POST /security/alerts/{id}/resolve` | **COMPLETED** |
| **Module 49** | System Configuration | `GET /system-config`, `GET /system-config/{key}`, `PUT /{key}`, `POST /batch` | **COMPLETED** |
| **Module 50** | Advanced Platform Administration | `GET /admin/platform-overview`, `PUT /admin/users/{id}/status`, `GET /admin/system-health-check` | **COMPLETED** |

---

## 3. Interactive Swagger UI Screenshots

All screenshots were captured live from the running backend service at `http://127.0.0.1:8000/docs`:

### Figure 3.1: Swagger UI Overview & Implemented Modules 1–50 Catalog
Shows the API title, version `1.0.0`, OpenAPI 3.1 specification, and the complete catalog of all 50 modules.
![Swagger Overview](file:///C:/Users/ADMIN/.gemini/antigravity-ide/brain/11884087-d3f9-4ebd-9ec2-b3d516c99f60/swagger_overview_modules_1_50.png)

### Figure 3.2: Modules 1 to 10 (Auth, Profiles, Hotel Verification, Room Types, Rooms, Amenities, Availability, Search, Filters)
![Modules 1 to 10](file:///C:/Users/ADMIN/.gemini/antigravity-ide/brain/11884087-d3f9-4ebd-9ec2-b3d516c99f60/swagger_modules_01_to_10.png)

### Figure 3.3: Modules 11 to 20 (Hotel Details & Gallery, Booking Engine, Guest Roster, Payments, Invoices, Refunds, Coupons, Reviews, Wishlists)
![Modules 11 to 20](file:///C:/Users/ADMIN/.gemini/antigravity-ide/brain/11884087-d3f9-4ebd-9ec2-b3d516c99f60/swagger_modules_11_to_20.png)

### Figure 3.4: Modules 21 to 30 (AI Recommendations, Travel Concierge, AI Support Bot, Notifications, Messaging, Housekeeping, Staff, Services, Room Service)
![Modules 21 to 30](file:///C:/Users/ADMIN/.gemini/antigravity-ide/brain/11884087-d3f9-4ebd-9ec2-b3d516c99f60/swagger_modules_21_to_30.png)

### Figure 3.5: Modules 31 to 40 (Revenue Analytics, Occupancy Analytics, Customer Analytics, Owner/Customer/Admin Dashboards, Moderation, Reports, Audit Logs, Subscription Plans)
![Modules 31 to 40](file:///C:/Users/ADMIN/.gemini/antigravity-ide/brain/11884087-d3f9-4ebd-9ec2-b3d516c99f60/swagger_modules_31_to_40.png)

### Figure 3.6: Modules 41 to 45 (Stripe Subscription Billing, Dynamic Pricing Rules, Loyalty Points, Geolocation & Attractions, Calendar Scheduler)
![Modules 41 to 45](file:///C:/Users/ADMIN/.gemini/antigravity-ide/brain/11884087-d3f9-4ebd-9ec2-b3d516c99f60/swagger_modules_41_to_50.png)
![Modules 43 to 45 Detail](file:///C:/Users/ADMIN/.gemini/antigravity-ide/brain/11884087-d3f9-4ebd-9ec2-b3d516c99f60/swagger_modules_43_to_47.png)

### Figure 3.7: Modules 46 to 50 (Financial Management, Business Intelligence, Fraud Security, System Configuration, Platform Administration)
![Modules 48 to 50 Detail](file:///C:/Users/ADMIN/.gemini/antigravity-ide/brain/11884087-d3f9-4ebd-9ec2-b3d516c99f60/swagger_modules_48_to_50.png)

### Figure 3.8: Sample Input Request Body in Swagger UI (POST /auth/register)
Shows the interactive Swagger UI Request Body populated with valid test registration credentials:
![Swagger Sample Input](file:///C:/Users/ADMIN/.gemini/antigravity-ide/brain/11884087-d3f9-4ebd-9ec2-b3d516c99f60/swagger_sample_input.png)

### Figure 3.9: Sample Output Response (Status Code 201 Created)
Shows the server response returning HTTP **201 Created**, user entity, verification token, and JWT token pair:
![Swagger Sample Output 201](file:///C:/Users/ADMIN/.gemini/antigravity-ide/brain/11884087-d3f9-4ebd-9ec2-b3d516c99f60/swagger_sample_output_201.png)

### Figure 3.10: Unified Request/Response Execution View in Swagger UI
Shows the Curl command, Request URL `http://127.0.0.1:8000/auth/register`, and 201 status code response together:
![Swagger Combined Input and Output](file:///C:/Users/ADMIN/.gemini/antigravity-ide/brain/11884087-d3f9-4ebd-9ec2-b3d516c99f60/swagger_input_and_output_combined.png)

---

## 4. Automated Testing & Verification

StayNest Pro includes automated test suites covering all 50 modules. The tests run against the isolated MySQL test database:

```bash
# Run all automated tests with pytest
.\venv\Scripts\python.exe -m pytest -v
```

Or execute individual test suites:
- `python test_modules_1_to_16.py` (Auth, Inventory, Search, Bookings, Payments, Invoices)
- `python test_modules_17_to_22.py` (Refunds, Coupons, Reviews, Wishlists, AI Recommendations, Concierge)
- `python test_modules_23_to_30.py` (AI Support, Notifications, Messaging, Housekeeping, Staff, Room Service)
- `python test_modules_31_to_40.py` (Analytics, Dashboards, Moderation, Reports, Audit Logs, Plans)
- `python test_modules_41_to_45.py` (Stripe Subscriptions, Dynamic Pricing, Loyalty, Geolocation, Scheduler)
- `python test_modules_46_to_50.py` (Financials, BI Trends, Fraud Security, System Config, Admin Overrides)

**Test Result:** 100% Pass Rate across all 50 modules.
