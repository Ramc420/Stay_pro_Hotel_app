from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole, CustomerProfile
from schemas import CustomerProfileCreate, CustomerProfileUpdate
from auth.dependencies import get_current_user, require_roles
from utils.response import api_response
from utils.file_upload import save_upload_file
from config import settings

router = APIRouter(prefix="/customers/profile", tags=["Module 2: Customer Profile Management"])


@router.get("/me", summary="Get current logged-in customer's profile")
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == current_user.id).first()
    if not profile:
        # Create empty profile if not existing
        profile = CustomerProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return api_response(
        success=True,
        message="Profile retrieved successfully",
        data={
            "id": profile.id,
            "user_id": profile.user_id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "phone_number": current_user.phone_number,
            "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            "gender": profile.gender,
            "nationality": profile.nationality,
            "address": profile.address,
            "city": profile.city,
            "country": profile.country,
            "postal_code": profile.postal_code,
            "emergency_contact_name": profile.emergency_contact_name,
            "emergency_contact_phone": profile.emergency_contact_phone,
            "travel_preferences": profile.travel_preferences,
            "profile_picture_url": profile.profile_picture_url
        }
    )


@router.post("/", summary="Create or initialize customer profile")
def create_profile(
    request: CustomerProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == current_user.id).first()
    if profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists for this customer. Use PUT/PATCH to update."
        )

    profile = CustomerProfile(
        user_id=current_user.id,
        date_of_birth=request.date_of_birth,
        gender=request.gender,
        nationality=request.nationality,
        address=request.address,
        city=request.city,
        country=request.country,
        postal_code=request.postal_code,
        emergency_contact_name=request.emergency_contact_name,
        emergency_contact_phone=request.emergency_contact_phone,
        travel_preferences=request.travel_preferences,
        profile_picture_url=request.profile_picture_url
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return api_response(
        success=True,
        message="Customer profile created successfully",
        data={
            "id": profile.id,
            "user_id": profile.user_id,
            "full_name": current_user.full_name,
            "travel_preferences": profile.travel_preferences
        },
        status_code=status.HTTP_201_CREATED
    )


@router.put("/me", summary="Update current customer profile")
def update_my_profile(
    request: CustomerProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == current_user.id).first()
    if not profile:
        profile = CustomerProfile(user_id=current_user.id)
        db.add(profile)

    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return api_response(
        success=True,
        message="Profile updated successfully",
        data={
            "id": profile.id,
            "user_id": profile.user_id,
            "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            "gender": profile.gender,
            "nationality": profile.nationality,
            "address": profile.address,
            "city": profile.city,
            "country": profile.country,
            "postal_code": profile.postal_code,
            "emergency_contact_name": profile.emergency_contact_name,
            "emergency_contact_phone": profile.emergency_contact_phone,
            "travel_preferences": profile.travel_preferences,
            "profile_picture_url": profile.profile_picture_url
        }
    )


@router.get("/preferences", summary="Retrieve saved customer travel preferences")
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == current_user.id).first()
    prefs = profile.travel_preferences if profile else None
    return api_response(
        success=True,
        message="Travel preferences retrieved successfully",
        data={"travel_preferences": prefs or {}}
    )


@router.put("/preferences", summary="Update customer travel preferences")
def update_preferences(
    preferences: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == current_user.id).first()
    if not profile:
        profile = CustomerProfile(user_id=current_user.id)
        db.add(profile)

    profile.travel_preferences = preferences
    db.commit()
    db.refresh(profile)

    return api_response(
        success=True,
        message="Travel preferences updated successfully",
        data={"travel_preferences": profile.travel_preferences}
    )


@router.post("/picture", summary="Upload and validate profile picture")
def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Save file to avatars subfolder
    relative_path = save_upload_file(
        upload_file=file,
        subfolder="avatars",
        allowed_extensions=settings.ALLOWED_IMAGE_EXTENSIONS
    )

    profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == current_user.id).first()
    if not profile:
        profile = CustomerProfile(user_id=current_user.id)
        db.add(profile)

    profile.profile_picture_url = relative_path
    db.commit()
    db.refresh(profile)

    return api_response(
        success=True,
        message="Profile picture uploaded successfully",
        data={"profile_picture_url": relative_path}
    )


@router.delete("/me", summary="Delete customer profile")
def delete_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    db.delete(profile)
    db.commit()
    return api_response(success=True, message="Profile deleted successfully")


@router.get("/{user_id}", summary="Retrieve customer profile by ID (Admin only)")
def get_customer_profile_by_admin(
    user_id: int,
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found")

    profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == user_id).first()
    return api_response(
        success=True,
        message="Customer profile retrieved successfully",
        data={
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "role": user.role.value,
            "profile": {
                "date_of_birth": profile.date_of_birth.isoformat() if profile and profile.date_of_birth else None,
                "gender": profile.gender if profile else None,
                "nationality": profile.nationality if profile else None,
                "city": profile.city if profile else None,
                "country": profile.country if profile else None,
                "travel_preferences": profile.travel_preferences if profile else None,
                "profile_picture_url": profile.profile_picture_url if profile else None
            } if profile else None
        }
    )
