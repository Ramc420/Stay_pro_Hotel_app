from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from models.customer import CustomerProfile


def get_profile_by_user_id(db: Session, user_id: int) -> Optional[CustomerProfile]:
    return db.query(CustomerProfile).filter(CustomerProfile.user_id == user_id).first()


def get_or_create_profile(db: Session, user_id: int) -> CustomerProfile:
    profile = get_profile_by_user_id(db, user_id)
    if not profile:
        profile = CustomerProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def create_customer_profile(db: Session, user_id: int, profile_data: dict) -> CustomerProfile:
    profile = CustomerProfile(user_id=user_id, **profile_data)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update_customer_profile(db: Session, profile: CustomerProfile, update_data: dict) -> CustomerProfile:
    for field, value in update_data.items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


def update_travel_preferences(db: Session, profile: CustomerProfile, preferences: dict) -> CustomerProfile:
    profile.travel_preferences = preferences
    db.commit()
    db.refresh(profile)
    return profile


def update_profile_picture(db: Session, profile: CustomerProfile, picture_url: str) -> CustomerProfile:
    profile.profile_picture_url = picture_url
    db.commit()
    db.refresh(profile)
    return profile


def delete_customer_profile(db: Session, profile: CustomerProfile) -> None:
    db.delete(profile)
    db.commit()
