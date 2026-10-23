from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole, Hotel, HotelStatus, HotelVerificationDocument
from schemas import (
    HotelRegisterRequest, HotelVerificationDocResponse,
    HotelApprovalAction, HotelSuspendAction
)
from auth.dependencies import get_current_user, require_roles, verify_hotel_access
from utils.response import api_response
from utils.file_upload import save_upload_file
from config import settings

router = APIRouter(prefix="/hotels/verification", tags=["Module 3: Hotel Registration & Verification"])


@router.post("/register", summary="Register a hotel and business information")
def register_hotel(
    request: HotelRegisterRequest,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    hotel = Hotel(
        owner_id=current_user.id,
        name=request.name,
        description=request.description,
        property_type=request.property_type.upper(),
        email=request.email.lower(),
        phone=request.phone,
        website=request.website,
        address_line1=request.address_line1,
        address_line2=request.address_line2,
        city=request.city,
        state=request.state,
        country=request.country,
        postal_code=request.postal_code,
        latitude=request.latitude,
        longitude=request.longitude,
        check_in_time=request.check_in_time,
        check_out_time=request.check_out_time,
        cancellation_policy=request.cancellation_policy,
        house_rules=request.house_rules,
        status=HotelStatus.PENDING_APPROVAL,
        is_approved=False,
        is_active=True
    )
    db.add(hotel)
    db.commit()
    db.refresh(hotel)

    return api_response(
        success=True,
        message="Hotel registered successfully. Please upload business licenses and submit for admin approval.",
        data={
            "id": hotel.id,
            "owner_id": hotel.owner_id,
            "name": hotel.name,
            "property_type": hotel.property_type,
            "city": hotel.city,
            "status": hotel.status.value,
            "is_approved": hotel.is_approved
        },
        status_code=status.HTTP_201_CREATED
    )


@router.post("/{hotel_id}/documents", summary="Upload business licenses and verification documents")
def upload_verification_document(
    hotel_id: int,
    document_type: str = Form(..., description="BUSINESS_LICENSE, FIRE_SAFETY_CERTIFICATE, TAX_REGISTRATION, PROPERTY_DEED"),
    document_number: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    hotel = verify_hotel_access(hotel_id, current_user, db)

    relative_path = save_upload_file(
        upload_file=file,
        subfolder="documents",
        allowed_extensions=settings.ALLOWED_DOC_EXTENSIONS
    )

    doc = HotelVerificationDocument(
        hotel_id=hotel.id,
        document_type=document_type.upper(),
        document_url=relative_path,
        document_number=document_number,
        verification_status="PENDING"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return api_response(
        success=True,
        message="Verification document uploaded successfully",
        data={
            "id": doc.id,
            "hotel_id": doc.hotel_id,
            "document_type": doc.document_type,
            "document_url": doc.document_url,
            "verification_status": doc.verification_status,
            "uploaded_at": doc.uploaded_at.isoformat()
        },
        status_code=status.HTTP_201_CREATED
    )


@router.get("/{hotel_id}/documents", summary="Retrieve hotel verification documents")
def list_verification_documents(
    hotel_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    hotel = verify_hotel_access(hotel_id, current_user, db)
    docs = db.query(HotelVerificationDocument).filter(HotelVerificationDocument.hotel_id == hotel.id).all()

    return api_response(
        success=True,
        message="Verification documents retrieved successfully",
        data=[
            {
                "id": d.id,
                "hotel_id": d.hotel_id,
                "document_type": d.document_type,
                "document_url": d.document_url,
                "document_number": d.document_number,
                "verification_status": d.verification_status,
                "remarks": d.remarks,
                "uploaded_at": d.uploaded_at.isoformat()
            } for d in docs
        ]
    )


@router.post("/{hotel_id}/submit-approval", summary="Submit hotel application for administrator approval")
def submit_hotel_for_approval(
    hotel_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    hotel = verify_hotel_access(hotel_id, current_user, db)
    
    # Check if at least one document has been uploaded
    doc_count = db.query(HotelVerificationDocument).filter(HotelVerificationDocument.hotel_id == hotel.id).count()
    if doc_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one business verification document must be uploaded before submitting for approval"
        )

    hotel.status = HotelStatus.PENDING_APPROVAL
    db.commit()
    db.refresh(hotel)

    return api_response(
        success=True,
        message="Hotel listing application submitted for administrative review",
        data={
            "hotel_id": hotel.id,
            "name": hotel.name,
            "status": hotel.status.value
        }
    )


@router.get("/pending", summary="List pending hotel applications (Admin only)")
def list_pending_hotels(
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    pending = db.query(Hotel).filter(Hotel.status == HotelStatus.PENDING_APPROVAL).all()
    return api_response(
        success=True,
        message="Pending hotel applications retrieved successfully",
        data=[
            {
                "id": h.id,
                "name": h.name,
                "owner_id": h.owner_id,
                "city": h.city,
                "state": h.state,
                "country": h.country,
                "property_type": h.property_type,
                "status": h.status.value,
                "created_at": h.created_at.isoformat() if h.created_at else None
            } for h in pending
        ]
    )


@router.post("/{hotel_id}/moderation", summary="Approve or reject hotel application (Admin only)")
def moderate_hotel(
    hotel_id: int,
    action: HotelApprovalAction,
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Hotel {hotel_id} not found")

    if action.status not in [HotelStatus.APPROVED, HotelStatus.REJECTED]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be APPROVED or REJECTED")

    hotel.status = action.status
    hotel.is_approved = (action.status == HotelStatus.APPROVED)
    if action.status == HotelStatus.REJECTED:
        hotel.rejection_reason = action.rejection_reason
    else:
        hotel.rejection_reason = None
        # Mark all pending verification docs as VERIFIED
        db.query(HotelVerificationDocument).filter(
            HotelVerificationDocument.hotel_id == hotel_id
        ).update({"verification_status": "VERIFIED"})

    db.commit()
    db.refresh(hotel)

    return api_response(
        success=True,
        message=f"Hotel application has been {hotel.status.value.lower()}",
        data={
            "id": hotel.id,
            "name": hotel.name,
            "status": hotel.status.value,
            "is_approved": hotel.is_approved,
            "rejection_reason": hotel.rejection_reason
        }
    )


@router.post("/{hotel_id}/suspend", summary="Suspend or reactivate hotel listing (Admin only)")
def toggle_hotel_suspension(
    hotel_id: int,
    action: HotelSuspendAction,
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Hotel {hotel_id} not found")

    if action.suspend:
        hotel.status = HotelStatus.SUSPENDED
        hotel.is_active = False
        message = "Hotel listing has been suspended"
    else:
        hotel.status = HotelStatus.APPROVED
        hotel.is_active = True
        message = "Hotel listing has been reactivated"

    db.commit()
    db.refresh(hotel)

    return api_response(
        success=True,
        message=message,
        data={
            "id": hotel.id,
            "name": hotel.name,
            "status": hotel.status.value,
            "is_active": hotel.is_active
        }
    )
