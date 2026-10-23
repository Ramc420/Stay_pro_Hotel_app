import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole, TokenBlacklist, CustomerProfile
from schemas import (
    UserRegisterRequest, UserLoginRequest, RefreshTokenRequest, LogoutRequest,
    ForgotPasswordRequest, ResetPasswordRequest, VerifyEmailRequest,
    RoleUpdateRequest, UserResponse
)
from auth.jwt_handler import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token
)
from auth.dependencies import get_current_user, require_roles
from utils.response import api_response

router = APIRouter(prefix="/auth", tags=["Module 1: Authentication & RBAC"])


@router.post("/register", summary="Register a new user")
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists"
        )

    # Generate email verification token
    verification_token = uuid.uuid4().hex

    new_user = User(
        email=request.email.lower(),
        hashed_password=hash_password(request.password),
        full_name=request.full_name,
        phone_number=request.phone_number,
        role=request.role,
        is_active=True,
        is_verified=False,
        email_verification_token=verification_token
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # If role is CUSTOMER, automatically create initial CustomerProfile record
    if new_user.role == UserRole.CUSTOMER:
        profile = CustomerProfile(user_id=new_user.id)
        db.add(profile)
        db.commit()

    # Generate JWT tokens
    access_token, _ = create_access_token(user_id=new_user.id, role=new_user.role.value)
    refresh_token, _ = create_refresh_token(user_id=new_user.id, role=new_user.role.value)

    return api_response(
        success=True,
        message="User registered successfully. Please verify your email using the verification token.",
        data={
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "full_name": new_user.full_name,
                "role": new_user.role.value,
                "is_verified": new_user.is_verified,
                "verification_token": verification_token  # Provided for seamless test environments
            },
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer"
            }
        },
        status_code=status.HTTP_201_CREATED
    )


@router.post("/login", summary="Login with email and password")
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email.lower()).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Please contact platform administration."
        )

    access_token, _ = create_access_token(user_id=user.id, role=user.role.value)
    refresh_token, _ = create_refresh_token(user_id=user.id, role=user.role.value)

    return api_response(
        success=True,
        message="Login successful",
        data={
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_verified": user.is_verified
            },
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer"
            }
        }
    )


@router.post("/refresh-token", summary="Obtain a new access token using a refresh token")
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(request.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired refresh token: {str(e)}"
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type: refresh token expected"
        )

    jti = payload.get("jti")
    if jti:
        blacklisted = db.query(TokenBlacklist).filter(TokenBlacklist.token_jti == jti).first()
        if blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been invalidated"
            )

    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer active or found"
        )

    new_access_token, _ = create_access_token(user_id=user.id, role=user.role.value)
    return api_response(
        success=True,
        message="Access token refreshed successfully",
        data={
            "access_token": new_access_token,
            "token_type": "Bearer"
        }
    )


@router.post("/logout", summary="Logout and invalidate current tokens")
def logout(
    request: LogoutRequest = None,
    authorization: str = Header(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Invalidate current access token
    if authorization and authorization.startswith("Bearer "):
        access_token_raw = authorization.split(" ")[1]
        try:
            payload = decode_token(access_token_raw)
            jti = payload.get("jti")
            if jti:
                blacklist_entry = TokenBlacklist(
                    token_jti=jti,
                    token_type="access",
                    user_id=current_user.id
                )
                db.add(blacklist_entry)
        except Exception:
            pass

    # Invalidate refresh token if passed
    if request and request.refresh_token:
        try:
            r_payload = decode_token(request.refresh_token)
            r_jti = r_payload.get("jti")
            if r_jti:
                r_entry = TokenBlacklist(
                    token_jti=r_jti,
                    token_type="refresh",
                    user_id=current_user.id
                )
                db.add(r_entry)
        except Exception:
            pass

    db.commit()
    return api_response(success=True, message="Logged out successfully and token invalidated")


@router.post("/forgot-password", summary="Initiate password reset")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email.lower()).first()
    if not user:
        # Don't reveal user existence for security
        return api_response(
            success=True,
            message="If your email is registered with us, a password reset link has been dispatched."
        )

    reset_token = uuid.uuid4().hex
    user.password_reset_token = reset_token
    user.password_reset_expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    db.commit()

    return api_response(
        success=True,
        message="Password reset token generated successfully",
        data={"reset_token": reset_token}
    )


@router.post("/reset-password", summary="Reset password using reset token")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.password_reset_token == request.token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    now = datetime.datetime.now(datetime.timezone.utc)
    # Check expiry if timezone-aware comparison
    if user.password_reset_expires_at:
        exp = user.password_reset_expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=datetime.timezone.utc)
        if exp < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token has expired"
            )

    user.hashed_password = hash_password(request.new_password)
    user.password_reset_token = None
    user.password_reset_expires_at = None
    db.commit()

    return api_response(success=True, message="Password has been reset successfully. You may now log in.")


@router.post("/verify-email", summary="Verify email address using token")
def verify_email(request: VerifyEmailRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email_verification_token == request.token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email verification token"
        )

    user.is_verified = True
    user.email_verification_token = None
    db.commit()

    return api_response(success=True, message="Email verified successfully")


@router.get("/me", summary="Retrieve currently authenticated user profile & role")
def get_me(current_user: User = Depends(get_current_user)):
    return api_response(
        success=True,
        message="User profile retrieved successfully",
        data={
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "phone_number": current_user.phone_number,
            "role": current_user.role.value,
            "is_active": current_user.is_active,
            "is_verified": current_user.is_verified,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        }
    )


@router.put("/users/{user_id}/role", summary="Update user role (Admin only)")
def update_user_role(
    user_id: int,
    request: RoleUpdateRequest,
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    user.role = request.role
    db.commit()
    db.refresh(user)

    return api_response(
        success=True,
        message=f"User {user.email} role updated to {user.role.value}",
        data={
            "id": user.id,
            "email": user.email,
            "role": user.role.value
        }
    )


@router.get("/users", summary="List users with role filtering (Admin only)")
def list_users(
    role: UserRole = None,
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    users = query.all()

    return api_response(
        success=True,
        message="Users list retrieved successfully",
        data=[
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role.value,
                "is_active": u.is_active,
                "is_verified": u.is_verified,
                "created_at": u.created_at.isoformat() if u.created_at else None
            } for u in users
        ]
    )
