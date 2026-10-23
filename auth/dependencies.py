from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole, TokenBlacklist, Hotel, HotelStaff
from auth.jwt_handler import decode_token

# HTTPBearer allows standard Bearer token authorization in Swagger UI
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: access token expected",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    jti = payload.get("jti")
    if jti:
        # Check if token is blacklisted
        blacklisted = db.query(TokenBlacklist).filter(TokenBlacklist.token_jti == jti).first()
        if blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked/logged out",
                headers={"WWW-Authenticate": "Bearer"},
            )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: subject must be integer id",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive or disabled",
        )
        
    return user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Returns the authenticated User if valid token is provided, or None for guest/unauthenticated requests."""
    if not credentials or not credentials.credentials:
        return None
    token = credentials.credentials
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        jti = payload.get("jti")
        if jti:
            blacklisted = db.query(TokenBlacklist).filter(TokenBlacklist.token_jti == jti).first()
            if blacklisted:
                return None
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
        user_id = int(user_id_str)
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            return None
        return user
    except Exception:
        return None



def require_roles(*allowed_roles: UserRole):
    """
    Dependency factory to enforce Role-Based Access Control (RBAC).
    Returns 403 Forbidden if user's role is not within allowed_roles.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            role_names = [r.value for r in allowed_roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of the following roles: {', '.join(role_names)}. Current role: {current_user.role.value}"
            )
        return current_user
    return role_checker


def verify_hotel_access(hotel_id: int, current_user: User, db: Session) -> Hotel:
    """
    Verifies that the current user has administrative or ownership permissions
    to manage the given hotel.
    """
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hotel with ID {hotel_id} not found"
        )

    # ADMIN can manage any hotel
    if current_user.role == UserRole.ADMIN:
        return hotel

    # HOTEL_OWNER must own the hotel
    if current_user.role == UserRole.HOTEL_OWNER and hotel.owner_id == current_user.id:
        return hotel

    # HOTEL_STAFF must be assigned to the hotel
    if current_user.role == UserRole.HOTEL_STAFF:
        staff_entry = db.query(HotelStaff).filter(
            HotelStaff.hotel_id == hotel_id,
            HotelStaff.user_id == current_user.id,
            HotelStaff.is_active == True
        ).first()
        if staff_entry:
            return hotel

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not authorized to manage this hotel property"
    )
