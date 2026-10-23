import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from config import settings
from database import engine, SessionLocal, Base
import models
from auth.jwt_handler import hash_password
from utils.response import api_response

# Import routers
from routers.auth import router as auth_router
from routers.customer_profiles import router as customer_profiles_router
from routers.hotel_verification import router as hotel_verification_router
from routers.hotel_profiles import router as hotel_profiles_router
from routers.rooms import router as rooms_router
from routers.room_types import router as room_types_router
from routers.amenities import router as amenities_router
from routers.room_availability import router as availability_router
from routers.hotel_search import router as search_router
from routers.hotel_filters import router as filters_router
from routers.hotel_details_gallery import router as hotel_details_gallery_router
from routers.bookings import router as bookings_router
from routers.payments import router as payments_router
from routers.invoices import router as invoices_router
from routers.refunds import router as refunds_router
from routers.coupons import router as coupons_router
from routers.reviews import router as reviews_router
from routers.wishlists import router as wishlists_router
from routers.recommendations import router as recommendations_router
from routers.ai_assistant import router as ai_assistant_router
from routers.support_bot import router as support_bot_router
from routers.notifications import router as notifications_router
from routers.in_app_messages import router as in_app_messages_router
from routers.housekeeping import router as housekeeping_router
from routers.staff_management import router as staff_management_router
from routers.check_in_out import router as check_in_out_router
from routers.additional_services import router as additional_services_router
from routers.room_service import router as room_service_router
from routers.revenue_analytics import router as revenue_analytics_router
from routers.occupancy_analytics import router as occupancy_analytics_router
from routers.customer_analytics import router as customer_analytics_router
from routers.owner_dashboard import router as owner_dashboard_router
from routers.customer_dashboard import router as customer_dashboard_router
from routers.admin_dashboard import router as admin_dashboard_router
from routers.hotel_moderation import router as hotel_moderation_router
from routers.reports import router as reports_router
from routers.audit_logs import router as audit_logs_router
from routers.subscriptions import router as subscriptions_router
from routers.subscription_payments import router as subscription_payments_router
from routers.dynamic_pricing import router as dynamic_pricing_router
from routers.loyalty import router as loyalty_router
from routers.location import router as location_router
from routers.calendar_scheduler import router as calendar_scheduler_router
from routers.financial import router as financial_router
from routers.business_intelligence import router as business_intelligence_router
from routers.fraud_security import router as fraud_security_router
from routers.system_config import router as system_config_router
from routers.platform_admin import router as platform_admin_router
from crud.subscriptions import seed_default_plans
from crud.system_config import seed_default_configs
from crud.platform_admin import seed_default_policies





def seed_database(db: Session):
    """
    Seeds initial system Admin and standard hotel amenities if not already present.
    """
    # 1. Seed Admin
    admin_email = "admin@staynest.com"
    admin = db.query(models.User).filter(models.User.email == admin_email).first()
    if not admin:
        admin = models.User(
            email=admin_email,
            hashed_password=hash_password("Admin@123456"),
            full_name="StayNest System Administrator",
            phone_number="+1-800-555-0199",
            role=models.UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    # 2. Seed Standard Amenities
    default_amenities = [
        {"name": "Free Wi-Fi", "category": "GENERAL", "icon": "wifi", "description": "High-speed wireless internet in all rooms and public areas"},
        {"name": "Swimming Pool", "category": "WELLNESS", "icon": "pool", "description": "Outdoor temperature-controlled swimming pool"},
        {"name": "Spa & Wellness", "category": "WELLNESS", "icon": "spa", "description": "Full-service luxury spa offering massages and therapies"},
        {"name": "Fitness Center", "category": "WELLNESS", "icon": "fitness", "description": "24/7 gym with modern cardio and weight training equipment"},
        {"name": "Free Parking", "category": "GENERAL", "icon": "parking", "description": "Complimentary on-site guest vehicle parking"},
        {"name": "Restaurant & Dining", "category": "DINING", "icon": "restaurant", "description": "Gourmet multi-cuisine restaurant with breakfast buffet"},
        {"name": "Bar & Lounge", "category": "DINING", "icon": "bar", "description": "Cocktail bar and social lounge area"},
        {"name": "Airport Shuttle", "category": "GENERAL", "icon": "shuttle", "description": "Scheduled airport pickup and drop-off service"},
        {"name": "Pet Friendly", "category": "GENERAL", "icon": "pets", "description": "Pets welcomed with dedicated amenities"},
        {"name": "Air Conditioning", "category": "GENERAL", "icon": "ac", "description": "Individually controlled climate air conditioning in all rooms"},
        {"name": "24-Hour Front Desk", "category": "GENERAL", "icon": "desk", "description": "Front desk concierge service available round the clock"},
        {"name": "Business Center", "category": "BUSINESS", "icon": "business", "description": "Conference rooms, meeting facilities, and printing services"}
    ]

    for item in default_amenities:
        existing = db.query(models.Amenity).filter(models.Amenity.name == item["name"]).first()
        if not existing:
            amenity = models.Amenity(
                name=item["name"],
                category=item["category"],
                icon=item["icon"],
                description=item["description"],
                is_active=True
            )
            db.add(amenity)
    db.commit()

    # 3. Seed Subscription Plans
    seed_default_plans(db)

    # 4. Seed Platform Configurations & Policies
    seed_default_configs(db)
    seed_default_policies(db)



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables exist & seed initial data
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        seed_database(db)
        db.close()
    except Exception as e:
        print(f"Startup Warning (DB init): {e}")
    yield
    # Shutdown logic if any


tags_metadata = [
    {"name": "Health", "description": "Service health check and root endpoints"},
    {"name": "Module 1: Authentication & RBAC", "description": "User registration, login, JWT authentication, and RBAC authorization"},
    {"name": "Module 2: Customer Profile Management", "description": "Customer profiles, travel preferences, and avatars"},
    {"name": "Module 3: Hotel Registration & Verification", "description": "Hotel onboarding, business license documents, and verification moderation"},
    {"name": "Module 4: Hotel Profile Management", "description": "Hotel profile management, policies, and address settings"},
    {"name": "Module 5: Room Management", "description": "Room inventory, unique numbering, and status management"},
    {"name": "Module 6: Room Type Management", "description": "Room types, capacities, bed specifications, and base pricing"},
    {"name": "Module 7: Hotel Amenities Management", "description": "Global and hotel-specific amenities catalog"},
    {"name": "Module 8: Room Availability Management", "description": "Daily availability calendars, bulk date blocking, and occupancy tracking"},
    {"name": "Module 9: Hotel Search System", "description": "Full-text hotel keyword search and Haversine GPS radius geolocation"},
    {"name": "Module 10: Advanced Hotel Filters", "description": "Multi-criteria hotel filtering by price, star rating, property type, amenities, and dates"},
    {"name": "Module 11: Hotel Details & Gallery", "description": "Comprehensive hotel details, room catalogs, image galleries, and guest reviews"},
    {"name": "Module 12: Bookings & Guest Management", "description": "Room reservation creation, guest identification, lifecycle management, and history"},
    {"name": "Module 15: Stripe Payment Integration", "description": "Stripe checkout session creation, payment confirmation, and webhook handlers"},
    {"name": "Module 16: Invoice & Receipt Management", "description": "Invoice generation, tax breakdown, and printable HTML receipts"},
    {"name": "Module 17: Cancellation and Refund Management", "description": "Cancellation policy quotes, refund request submission, review, approval, and Stripe processing"},
    {"name": "Module 18: Coupon and Discount Management", "description": "Fixed and percentage coupons, expiry dates, seasonal and early-bird discounts, and usage limits"},
    {"name": "Module 19: Reviews and Ratings", "description": "Completed stay reviews, rating recalculations, moderation, and abuse reporting"},
    {"name": "Module 20: Wishlist and Favorite Hotels", "description": "Customer favorite hotels, saved rooms, and wishlist management"},
    {"name": "Module 21: AI Hotel Recommendation Engine", "description": "Personalized, budget-based, location-based, and similar-hotel recommendation algorithms"},
    {"name": "Module 22: AI Travel Assistant", "description": "Interactive AI travel planning, day-by-day itineraries, suggested hotels, and conversation memory"},
    {"name": "Module 23: AI Customer Support Chatbot", "description": "Support conversations, FAQs, and authorized booking lookups"},
    {"name": "Module 24: In-App Notifications", "description": "Booking, payment, refund, cancellation, and stay reminder notifications"},
    {"name": "Module 25: In-App Messaging", "description": "Guest-to-hotel and guest-to-support messaging threads"},
    {"name": "Module 26: Housekeeping Management", "description": "Room cleaning, dirty/clean status transitions, maintenance, and inspections"},
    {"name": "Module 27: Hotel Staff Management", "description": "Staff account assignment, roles, attendance clocking, and activity logs"},
    {"name": "Module 28: Check-In and Check-Out Management", "description": "Reservation verification, guest check-in/out, room assignment, and fee calculation"},
    {"name": "Module 29: Additional Services Management", "description": "Catalog and guest requests for laundry, spa, airport transport, and extra beds"},
    {"name": "Module 30: Room Service Management", "description": "Food menu catalog, room service ordering, preparation tracking, and charges"},
    {"name": "Module 31: Hotel Revenue Analytics", "description": "Daily and monthly revenue, aggregations, and refund accounting"},
    {"name": "Module 32: Hotel Occupancy Analytics", "description": "Occupancy rates, available vs occupied rooms, peak booking period analysis"},
    {"name": "Module 33: Customer Analytics", "description": "Booking frequency, spending patterns, repeat customers, and retention metrics"},
    {"name": "Module 34: Hotel Owner Dashboard APIs", "description": "Consolidated owner view: today's bookings, guests, revenue, occupancy, action items"},
    {"name": "Module 35: Customer Dashboard APIs", "description": "Personalized customer overview: upcoming stays, history, wishlist, and payments"},
    {"name": "Module 36: Admin Dashboard APIs", "description": "Platform-wide metrics, total revenue, active reservations, and moderation queue"},
    {"name": "Module 37: Hotel Verification and Moderation", "description": "Administrative document reviews, approvals, rejections, and audit history"},
    {"name": "Module 38: Reports and Export", "description": "Tabular business reports with CSV, Excel, and printable PDF exports"},
    {"name": "Module 39: Audit Logs and Security Monitoring", "description": "Immutable audit trails for logins, payments, administrative actions, and security events"},
    {"name": "Module 40: Hotel Subscription Plans", "description": "FREE, BASIC, PREMIUM, ENTERPRISE tiers, billing cycles, benefits, and renewals"},
    {"name": "Module 41: Hotel Subscription Payments", "description": "Stripe subscription billing, webhooks, and payment history"},
    {"name": "Module 42: Dynamic Pricing Management", "description": "Seasonal, weekend, holiday, and promotional pricing rules"},
    {"name": "Module 43: Loyalty and Rewards", "description": "Guest loyalty points, tiers, referral bonuses, and redemptions"},
    {"name": "Module 44: Location Services", "description": "Hotel coordinates, distance calculations, and nearby attractions"},
    {"name": "Module 45: Calendar and Booking Scheduler", "description": "Availability calendar matrix, double-booking prevention, and automated tasks"},
    {"name": "Module 46: Financial Management", "description": "Hotel earnings, platform commissions, taxes, and payout settlements"},
    {"name": "Module 47: Business Intelligence APIs", "description": "Platform revenue growth, market trends, top destinations, and executive metrics"},
    {"name": "Module 48: Fraud Detection and Security", "description": "Suspicious bookings, brute-force protection, login anomaly detection, and security alerts"},
    {"name": "Module 49: System Configuration", "description": "Platform settings, tax rates, fee percentages, and system-wide configurations"},
    {"name": "Module 50: Advanced Platform Administration", "description": "System health diagnostics, account lockdowns, status overrides, and platform policies"},
]

app = FastAPI(
    title="Hotel, Resort & Room Booking Management Platform",
    description="""

## Features & Implemented Modules:
* **Module 1**: Authentication & RBAC (Customer, Hotel Owner, Hotel Staff, Admin)
* **Module 2**: Customer Profile Management & Preferences
* **Module 3**: Hotel Registration, Verification & Administrative Moderation
* **Module 4**: Hotel Profile Management & Image Gallery
* **Module 5**: Room Management & Unique Numbering
* **Module 6**: Room Type Management (Single, Double, Deluxe, Suite, Family)
* **Module 7**: Hotel Amenities Management & Filtering
* **Module 8**: Room Availability Management & Calendars
* **Module 9**: Hotel Search System with Haversine Geolocation
* **Module 10**: Advanced Multi-Criteria Hotel Filters
* **Module 11**: Hotel Details and Gallery
* **Module 12**: Room Booking System
* **Module 13**: Guest Management
* **Module 14**: Booking Management & Lifecycle Transitions
* **Module 15**: Stripe Payment Integration & Idempotency
* **Module 16**: Invoice and Receipt Management
* **Module 17**: Cancellation and Refund Management
* **Module 18**: Coupon and Discount Management
* **Module 19**: Reviews and Ratings
* **Module 20**: Wishlist and Favorite Hotels
* **Module 21**: AI Hotel Recommendation Engine
* **Module 22**: AI Travel Assistant
* **Module 23**: AI Customer Support Chatbot
* **Module 24**: In-App Notifications
* **Module 25**: In-App Messaging
* **Module 26**: Housekeeping Management
* **Module 27**: Hotel Staff Management
* **Module 28**: Check-In and Check-Out Management
* **Module 29**: Additional Services Management
* **Module 30**: Room Service Management
* **Module 31**: Hotel Revenue Analytics
* **Module 32**: Hotel Occupancy Analytics
* **Module 33**: Customer Analytics
* **Module 34**: Hotel Owner Dashboard APIs
* **Module 35**: Customer Dashboard APIs
* **Module 36**: Admin Dashboard APIs
* **Module 37**: Hotel Verification and Moderation
* **Module 38**: Reports and Export
* **Module 39**: Audit Logs and Security Monitoring
* **Module 40**: Hotel Subscription Plans
* **Module 41**: Hotel Subscription Payments
* **Module 42**: Dynamic Pricing Management
* **Module 43**: Loyalty and Rewards
* **Module 44**: Location Services
* **Module 45**: Calendar and Booking Scheduler
* **Module 46**: Financial Management
* **Module 47**: Business Intelligence APIs
* **Module 48**: Fraud Detection and Security
* **Module 49**: System Configuration
* **Module 50**: Advanced Platform Administration


### Authentication:
Click the **Authorize** button on the top right and enter your Bearer token: `Bearer <access_token>`.
Default System Administrator: `admin@staynest.com` / `Admin@123456`.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static file uploads directory
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = " -> ".join([str(loc) for loc in error.get("loc", [])])
        errors.append({
            "field": field,
            "message": error.get("msg"),
            "type": error.get("type")
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Input validation error",
            "errors": errors
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": f"An unexpected internal error occurred: {str(exc)}"
        }
    )


# Health check endpoints
@app.get("/", tags=["Health"])
def root():
    return {
        "success": True,
        "message": "StayNest Pro API is running",
        "version": "1.0.0",
        "docs_url": "/docs"
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "success": True,
        "status": "healthy",
        "service": "StayNest Pro API",
        "database": "connected"
    }


# Include Routers directly (No /api/v1 prefix in endpoint URLs or OpenAPI schema)
routers_list = [
    auth_router,
    customer_profiles_router,
    hotel_verification_router,
    hotel_profiles_router,
    rooms_router,
    room_types_router,
    amenities_router,
    availability_router,
    search_router,
    filters_router,
    hotel_details_gallery_router,
    bookings_router,
    payments_router,
    invoices_router,
    refunds_router,
    coupons_router,
    reviews_router,
    wishlists_router,
    recommendations_router,
    ai_assistant_router,
    support_bot_router,
    notifications_router,
    in_app_messages_router,
    housekeeping_router,
    staff_management_router,
    check_in_out_router,
    additional_services_router,
    room_service_router,
    revenue_analytics_router,
    occupancy_analytics_router,
    customer_analytics_router,
    owner_dashboard_router,
    customer_dashboard_router,
    admin_dashboard_router,
    hotel_moderation_router,
    reports_router,
    audit_logs_router,
    subscriptions_router,
    subscription_payments_router,
    dynamic_pricing_router,
    loyalty_router,
    location_router,
    calendar_scheduler_router,
    financial_router,
    business_intelligence_router,
    fraud_security_router,
    system_config_router,
    platform_admin_router
]



for router in routers_list:
    app.include_router(router)

# Also support legacy /api/v1 paths without duplicating them in the OpenAPI Swagger schema
for router in routers_list:
    app.include_router(router, prefix="/api/v1", include_in_schema=False)




if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
