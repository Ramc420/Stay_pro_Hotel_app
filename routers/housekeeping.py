"""
Module 26: Housekeeping Management
Tracks CLEAN, DIRTY, CLEANING, INSPECTION, and MAINTENANCE task workflows for rooms.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.dependencies import get_current_user, verify_hotel_access, require_roles
from utils.response import api_response
from schemas.housekeeping import (
    HousekeepingTaskCreate, HousekeepingStatusUpdate, HousekeepingInspectionCreate
)
from crud import housekeeping as crud_house

router = APIRouter(prefix="/housekeeping", tags=["Module 26: Housekeeping Management"])


@router.post("/tasks", summary="Create housekeeping task")
def create_housekeeping_task(
    request: HousekeepingTaskCreate,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(request.hotel_id, current_user, db)

    task = crud_house.create_task(
        db=db,
        hotel_id=request.hotel_id,
        room_id=request.room_id,
        assigned_staff_id=request.assigned_staff_id,
        task_type=request.task_type or "CLEANING",
        priority=request.priority or "MEDIUM",
        notes=request.notes
    )

    return api_response(
        success=True,
        message="Housekeeping task created successfully",
        data={
            "id": task.id,
            "hotel_id": task.hotel_id,
            "room_id": task.room_id,
            "task_type": task.task_type,
            "status": task.status.value,
            "priority": task.priority,
            "assigned_staff_id": task.assigned_staff_id,
            "created_at": task.created_at.isoformat()
        },
        status_code=status.HTTP_201_CREATED
    )


@router.get("/tasks", summary="List housekeeping tasks")
def list_tasks(
    hotel_id: int,
    status: Optional[str] = None,
    assigned_staff_id: Optional[int] = None,
    room_id: Optional[int] = None,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    tasks = crud_house.get_tasks(db, hotel_id, status=status, assigned_staff_id=assigned_staff_id, room_id=room_id)

    return api_response(
        success=True,
        message="Housekeeping tasks retrieved",
        data=[
            {
                "id": t.id,
                "room_id": t.room_id,
                "room_number": t.room.room_number if t.room else None,
                "task_type": t.task_type,
                "status": t.status.value,
                "priority": t.priority,
                "assigned_staff_id": t.assigned_staff_id,
                "notes": t.notes,
                "created_at": t.created_at.isoformat(),
                "completed_at": t.completed_at.isoformat() if t.completed_at else None
            }
            for t in tasks
        ]
    )


@router.patch("/tasks/{task_id}/status", summary="Update task status (DIRTY, CLEANING, INSPECTION, CLEAN, MAINTENANCE)")
def update_task_status(
    task_id: int,
    request: HousekeepingStatusUpdate,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    task = crud_house.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Housekeeping task not found")

    verify_hotel_access(task.hotel_id, current_user, db)

    updated_task = crud_house.update_task_status(db, task, request.status, request.notes)
    return api_response(
        success=True,
        message=f"Housekeeping task status updated to {updated_task.status.value}",
        data={
            "id": updated_task.id,
            "status": updated_task.status.value,
            "completed_at": updated_task.completed_at.isoformat() if updated_task.completed_at else None
        }
    )


@router.post("/tasks/{task_id}/inspect", summary="Record room cleaning inspection")
def inspect_task(
    task_id: int,
    request: HousekeepingInspectionCreate,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    task = crud_house.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Housekeeping task not found")

    verify_hotel_access(task.hotel_id, current_user, db)

    inspection = crud_house.record_inspection(
        db=db,
        task=task,
        inspector_id=current_user.id,
        is_passed=request.is_passed,
        rating=request.rating or 5.0,
        checklist=request.checklist,
        comments=request.comments
    )

    return api_response(
        success=True,
        message=f"Inspection recorded. Result: {'PASSED' if inspection.is_passed else 'FAILED'}",
        data={
            "inspection_id": inspection.id,
            "task_id": inspection.task_id,
            "room_id": inspection.room_id,
            "is_passed": inspection.is_passed,
            "rating": inspection.rating,
            "comments": inspection.comments,
            "current_task_status": task.status.value
        },
        status_code=status.HTTP_201_CREATED
    )


@router.get("/hotels/{hotel_id}/rooms-overview", summary="Overview of room housekeeping statuses")
def rooms_overview(
    hotel_id: int,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    overview = crud_house.get_hotel_rooms_housekeeping_overview(db, hotel_id)
    return api_response(
        success=True,
        message="Room housekeeping overview retrieved",
        data=overview
    )
