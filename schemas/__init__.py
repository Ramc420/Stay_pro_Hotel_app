from schemas.common import ApiResponse, PaginationMetadata
from schemas.user import (
    UserRegisterRequest, UserLoginRequest, TokenData, RefreshTokenRequest,
    LogoutRequest, ForgotPasswordRequest, ResetPasswordRequest, VerifyEmailRequest,
    RoleUpdateRequest, UserResponse
)
from schemas.customer import (
    CustomerProfileBase, CustomerProfileCreate, CustomerProfileUpdate, CustomerProfileResponse
)
from schemas.hotel import (
    HotelRegisterRequest, HotelUpdate, HotelVerificationDocCreate,
    HotelVerificationDocResponse, HotelApprovalAction, HotelSuspendAction,
    HotelImageCreate, HotelImageUpdate, HotelImageResponse, HotelResponse,
    HotelDetailsResponse, HotelPolicyResponse, HotelReviewSummary
)
from schemas.room import (
    RoomTypeCreate, RoomTypeUpdate, RoomTypeResponse,
    RoomCreate, RoomUpdate, RoomStatusUpdate, RoomResponse
)
from schemas.amenity import (
    AmenityCreate, AmenityUpdate, AmenityResponse, AssociateAmenitiesRequest
)
from schemas.availability import (
    RoomAvailabilitySet, RoomAvailabilityBulkSet, RoomAvailabilityResponse
)
from schemas.search import HotelSearchResult
from schemas.review import (
    ReviewCreate, ReviewUpdate, ReviewResponse, ReviewReportRequest,
    ReviewModerationRequest, HotelReviewBreakdownResponse
)
from schemas.booking import (
    GuestInput, GuestResponse, BookingCreateRequest, BookingModifyRequest,
    BookingCancelRequest, BookingStatusUpdateRequest, BookingHistoryResponse, BookingResponse
)
from schemas.payment import (
    CreatePaymentSessionRequest, ConfirmPaymentRequest,
    StripeCheckoutSessionResponse, PaymentResponse
)
from schemas.invoice import InvoiceGenerateRequest, InvoiceResponse
from schemas.refund import (
    CancellationPolicyQuoteRequest, CancellationPolicyQuoteResponse,
    RefundRequestCreate, RefundApprovalRequest, RefundRejectionRequest, RefundRequestResponse
)
from schemas.coupon import (
    CouponCreate, CouponUpdate, CouponResponse,
    CouponValidateRequest, CouponValidateResponse,
    CouponApplyRequest, CouponApplyResponse, CouponUsageResponse
)
from schemas.wishlist import WishlistCreate, WishlistResponse, WishlistCheckResponse
from schemas.recommendation import HotelRecommendationItem, HotelRecommendationResponse
from schemas.ai_assistant import (
    TripPlanRequest, DayItineraryItem, TripPlanResponse,
    AIChatRequest, AIChatResponse, AIMessageResponse, AIConversationResponse
)
from schemas.support_bot import SupportChatRequest, SupportMessageResponse, SupportConversationResponse
from schemas.notification import NotificationCreate, NotificationResponse
from schemas.in_app_message import ConversationCreate, ChatMessageCreate, ChatMessageResponse, ConversationResponse
from schemas.housekeeping import HousekeepingTaskCreate, HousekeepingStatusUpdate, HousekeepingInspectionCreate, HousekeepingTaskResponse
from schemas.staff_management import StaffCreate, StaffUpdate, StaffResponse, AttendanceClockRequest, AttendanceResponse, ActivityLogResponse
from schemas.check_in_out import VerifyBookingRequest, CheckInRequest, CheckOutRequest, CheckInOutResponse
from schemas.additional_service import ServiceCreate, ServiceUpdate, ServiceResponse, ServiceRequestCreate, ServiceRequestResponse
from schemas.room_service import MenuItemCreate, MenuItemUpdate, MenuItemResponse, OrderItemCreate, OrderItemResponse, RoomServiceOrderCreate, RoomServiceOrderResponse
from schemas.subscription_payment import (
    CheckoutSessionCreate, CheckoutSessionResponse, PlanUpgradeDowngradeRequest,
    SubscriptionPaymentResponse, WebhookEventRequest
)
from schemas.dynamic_pricing import (
    DynamicPricingRuleCreate, DynamicPricingRuleUpdate, DynamicPricingRuleResponse,
    PriceCalculationRequest, PriceCalculationResponse
)
from schemas.loyalty import (
    LoyaltyAccountResponse, LoyaltyLedgerResponse, AwardBookingPointsRequest,
    RedeemPointsRequest, RedeemPointsResponse, ApplyReferralRequest, TierBenefitInfo
)
from schemas.location import (
    CoordinatesUpdate, HotelAttractionCreate, HotelAttractionResponse,
    DistanceCalculationRequest, DistanceCalculationResponse, NearbyHotelResponse
)
from schemas.calendar_scheduler import (
    CalendarGridResponse, ScheduleSummaryResponse, RoomConflictCheckRequest,
    RoomConflictCheckResponse, ScheduledJobsRunResponse
)
from schemas.financial import (
    FinancialBreakdownResponse, SettlementGenerateRequest, SettlementResponse,
    SettlementMarkPaidRequest, ReconciliationReport, ReconciliationItem
)
from schemas.business_intelligence import (
    GrowthMetric, GrowthMetricsResponse, TopHotelPerformance, TopDestination,
    TopPerformersResponse, MonthlyTrendPoint, OccupancyTrendsResponse, ExecutiveMonthlySummary
)
from schemas.fraud_security import (
    SecurityAlertResponse, AlertResolveRequest, LoginRiskEvaluationRequest,
    LoginRiskEvaluationResponse, FraudScanResponse, SecurityMetricsResponse
)
from schemas.system_config import (
    SystemConfigItemResponse, SystemConfigUpdateRequest,
    SystemConfigBatchUpdateRequest, SystemConfigCreateRequest
)
from schemas.platform_admin import (
    UserAccountStatusUpdateRequest, HotelStatusOverrideRequest,
    BookingEmergencyOverrideRequest, PlatformPolicyResponse,
    PlatformPolicyUpdateRequest, SystemServiceStatus, SystemHealthOverview
)


__all__ = [
    "ApiResponse",
    "PaginationMetadata",
    "UserRegisterRequest",
    "UserLoginRequest",
    "TokenData",
    "RefreshTokenRequest",
    "LogoutRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "VerifyEmailRequest",
    "RoleUpdateRequest",
    "UserResponse",
    "CustomerProfileBase",
    "CustomerProfileCreate",
    "CustomerProfileUpdate",
    "CustomerProfileResponse",
    "HotelRegisterRequest",
    "HotelUpdate",
    "HotelVerificationDocCreate",
    "HotelVerificationDocResponse",
    "HotelApprovalAction",
    "HotelSuspendAction",
    "HotelImageCreate",
    "HotelImageUpdate",
    "HotelImageResponse",
    "HotelResponse",
    "RoomTypeCreate",
    "RoomTypeUpdate",
    "RoomTypeResponse",
    "RoomCreate",
    "RoomUpdate",
    "RoomStatusUpdate",
    "RoomResponse",
    "AmenityCreate",
    "AmenityUpdate",
    "AmenityResponse",
    "AssociateAmenitiesRequest",
    "RoomAvailabilitySet",
    "RoomAvailabilityBulkSet",
    "RoomAvailabilityResponse",
    "HotelSearchResult",
    "ReviewCreate",
    "ReviewUpdate",
    "ReviewResponse",
    "ReviewReportRequest",
    "ReviewModerationRequest",
    "HotelReviewBreakdownResponse",
    "GuestInput",
    "GuestResponse",
    "BookingCreateRequest",
    "BookingModifyRequest",
    "BookingCancelRequest",
    "BookingStatusUpdateRequest",
    "BookingHistoryResponse",
    "BookingResponse",
    "CreatePaymentSessionRequest",
    "ConfirmPaymentRequest",
    "StripeCheckoutSessionResponse",
    "PaymentResponse",
    "InvoiceGenerateRequest",
    "InvoiceResponse",
    "CancellationPolicyQuoteRequest",
    "CancellationPolicyQuoteResponse",
    "RefundRequestCreate",
    "RefundApprovalRequest",
    "RefundRejectionRequest",
    "RefundRequestResponse",
    "CouponCreate",
    "CouponUpdate",
    "CouponResponse",
    "CouponValidateRequest",
    "CouponValidateResponse",
    "CouponApplyRequest",
    "CouponApplyResponse",
    "CouponUsageResponse",
    "WishlistCreate",
    "WishlistResponse",
    "WishlistCheckResponse",
    "HotelRecommendationItem",
    "HotelRecommendationResponse",
    "TripPlanRequest",
    "DayItineraryItem",
    "TripPlanResponse",
    "AIChatRequest",
    "AIChatResponse",
    "AIMessageResponse",
    "AIConversationResponse",
    "SupportChatRequest",
    "SupportMessageResponse",
    "SupportConversationResponse",
    "NotificationCreate",
    "NotificationResponse",
    "ConversationCreate",
    "ChatMessageCreate",
    "ChatMessageResponse",
    "ConversationResponse",
    "HousekeepingTaskCreate",
    "HousekeepingStatusUpdate",
    "HousekeepingInspectionCreate",
    "HousekeepingTaskResponse",
    "StaffCreate",
    "StaffUpdate",
    "StaffResponse",
    "AttendanceClockRequest",
    "AttendanceResponse",
    "ActivityLogResponse",
    "VerifyBookingRequest",
    "CheckInRequest",
    "CheckOutRequest",
    "CheckInOutResponse",
    "ServiceCreate",
    "ServiceUpdate",
    "ServiceResponse",
    "ServiceRequestCreate",
    "ServiceRequestResponse",
    "MenuItemCreate",
    "MenuItemUpdate",
    "MenuItemResponse",
    "OrderItemCreate",
    "OrderItemResponse",
    "RoomServiceOrderCreate",
    "RoomServiceOrderResponse",
    # Module 41
    "CheckoutSessionCreate",
    "CheckoutSessionResponse",
    "PlanUpgradeDowngradeRequest",
    "SubscriptionPaymentResponse",
    "WebhookEventRequest",
    # Module 42
    "DynamicPricingRuleCreate",
    "DynamicPricingRuleUpdate",
    "DynamicPricingRuleResponse",
    "PriceCalculationRequest",
    "PriceCalculationResponse",
    # Module 43
    "LoyaltyAccountResponse",
    "LoyaltyLedgerResponse",
    "AwardBookingPointsRequest",
    "RedeemPointsRequest",
    "RedeemPointsResponse",
    "ApplyReferralRequest",
    "TierBenefitInfo",
    # Module 44
    "CoordinatesUpdate",
    "HotelAttractionCreate",
    "HotelAttractionResponse",
    "DistanceCalculationRequest",
    "DistanceCalculationResponse",
    "NearbyHotelResponse",
    # Module 45
    "CalendarGridResponse",
    "ScheduleSummaryResponse",
    "RoomConflictCheckRequest",
    "RoomConflictCheckResponse",
    "ScheduledJobsRunResponse",
    # Module 46
    "FinancialBreakdownResponse",
    "SettlementGenerateRequest",
    "SettlementResponse",
    "SettlementMarkPaidRequest",
    "ReconciliationReport",
    # Module 47
    "GrowthMetricsResponse",
    "TopPerformersResponse",
    "OccupancyTrendsResponse",
    "ExecutiveMonthlySummary",
    # Module 48
    "SecurityAlertResponse",
    "AlertResolveRequest",
    "LoginRiskEvaluationRequest",
    "LoginRiskEvaluationResponse",
    "FraudScanResponse",
    "SecurityMetricsResponse",
    # Module 49
    "SystemConfigItemResponse",
    "SystemConfigUpdateRequest",
    "SystemConfigBatchUpdateRequest",
    "SystemConfigCreateRequest",
    # Module 50
    "UserAccountStatusUpdateRequest",
    "HotelStatusOverrideRequest",
    "BookingEmergencyOverrideRequest",
    "PlatformPolicyResponse",
    "PlatformPolicyUpdateRequest",
    "SystemHealthOverview",
]

