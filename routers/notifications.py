"""
Module 24: In-App Notifications
APIs for receiving booking, payment, cancellation, refund, and reminder notifications.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from auth.dependencies import get_current_user
from utils.response import api_response
from schemas.notification import NotificationCreate
from crud import notification as crud_notif

router = APIRouter(prefix="/notifications", tags=["Module 24: In-App Notifications"])


@router.get("/", summary="List user's notifications")
def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notifications = crud_notif.get_user_notifications(
        db, current_user.id, unread_only=unread_only, limit=limit, offset=offset
    )
    unread_count = crud_notif.get_unread_count(db, current_user.id)

    return api_response(
        success=True,
        message="Notifications retrieved successfully",
        data=[
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "notification_type": n.notification_type.value,
                "is_read": n.is_read,
                "data": n.data,
                "created_at": n.created_at.isoformat()
            }
            for n in notifications
        ],
        meta={"unread_count": unread_count, "count": len(notifications)}
    )


@router.get("/unread-count", summary="Get unread notifications count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    count = crud_notif.get_unread_count(db, current_user.id)
    return api_response(
        success=True,
        message="Unread notification count retrieved",
        data={"unread_count": count}
    )


@router.patch("/{notification_id}/read", summary="Mark single notification as read")
def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = crud_notif.mark_notification_as_read(db, notification_id, current_user.id)
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return api_response(
        success=True,
        message="Notification marked as read",
        data={"id": notif.id, "is_read": True}
    )


@router.post("/mark-all-read", summary="Mark all notifications as read")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updated = crud_notif.mark_all_as_read(db, current_user.id)
    return api_response(
        success=True,
        message=f"{updated} notification(s) marked as read",
        data={"updated_count": updated}
    )


@router.post("/send", summary="Trigger or create in-app notification")
def create_custom_notification(
    request: NotificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = crud_notif.create_notification(
        db=db,
        user_id=request.user_id,
        title=request.title,
        message=request.message,
        data=request.data
    )
    return api_response(
        success=True,
        message="Notification sent successfully",
        data={
            "id": notif.id,
            "user_id": notif.user_id,
            "title": notif.title,
            "message": notif.message,
            "is_read": notif.is_read
        },
        status_code=status.HTTP_201_CREATED
    )
