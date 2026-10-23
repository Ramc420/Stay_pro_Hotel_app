from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from models.user import User, UserRole, TokenBlacklist


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email.lower()).first()


def get_user_by_verification_token(db: Session, token: str) -> Optional[User]:
    return db.query(User).filter(User.email_verification_token == token).first()


def get_user_by_reset_token(db: Session, token: str) -> Optional[User]:
    return db.query(User).filter(User.password_reset_token == token).first()


def create_user(
    db: Session,
    email: str,
    hashed_password: str,
    full_name: str,
    phone_number: Optional[str],
    role: UserRole,
    verification_token: Optional[str] = None
) -> User:
    new_user = User(
        email=email.lower(),
        hashed_password=hashed_password,
        full_name=full_name,
        phone_number=phone_number,
        role=role,
        is_active=True,
        is_verified=False,
        email_verification_token=verification_token
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def update_user_role(db: Session, user: User, new_role: UserRole) -> User:
    user.role = new_role
    db.commit()
    db.refresh(user)
    return user


def set_password_reset_token(db: Session, user: User, token: str, expires_at: datetime) -> User:
    user.password_reset_token = token
    user.password_reset_expires_at = expires_at
    db.commit()
    return user


def reset_user_password(db: Session, user: User, new_hashed_password: str) -> User:
    user.hashed_password = new_hashed_password
    user.password_reset_token = None
    user.password_reset_expires_at = None
    db.commit()
    return user


def verify_user_email(db: Session, user: User) -> User:
    user.is_verified = True
    user.email_verification_token = None
    db.commit()
    return user


def list_users(db: Session, role: Optional[UserRole] = None) -> List[User]:
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.all()


def is_token_blacklisted(db: Session, jti: str) -> bool:
    return db.query(TokenBlacklist).filter(TokenBlacklist.token_jti == jti).first() is not None


def blacklist_token(db: Session, jti: str, token_type: str, user_id: int) -> TokenBlacklist:
    entry = TokenBlacklist(token_jti=jti, token_type=token_type, user_id=user_id)
    db.add(entry)
    db.commit()
    return entry
