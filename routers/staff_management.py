"""
Module 27: Hotel Staff Management
Manage hotel staff assignments, roles, permissions, attendance, and activity audit trails.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole, HotelStaff
from auth.dependencies import get_current_user, verify_hotel_access, require_roles
from utils.response import api_response
from schemas.staff_management import StaffCreate, StaffUpdate, AttendanceClockRequest
from crud import staff_management as crud_staff

router = APIRouter(prefix="/staff", tags=["Module 27: Hotel Staff Management"])


@router.post("/hotels/{hotel_id}/assign", summary="Assign user as hotel staff")
def assign_staff(
    hotel_id: int,
    request: StaffCreate,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)

    staff_entry = crud_staff.assign_hotel_staff(
        db=db,
        user_id=request.user_id,
        hotel_id=hotel_id,
        department=request.department or "Front Desk",
        position=request.position or "Staff",
        permissions=request.permissions
    )

    return api_response(
        success=True,
        message="Staff member assigned successfully",
        data={
            "id": staff_entry.id,
            "user_id": staff_entry.user_id,
            "hotel_id": staff_entry.hotel_id,
            "department": staff_entry.department,
            "position": staff_entry.position,
            "permissions": staff_entry.permissions,
            "is_active": staff_entry.is_active
        },
        status_code=status.HTTP_201_CREATED
    )


@router.get("/hotels/{hotel_id}", summary="List hotel staff members")
def list_hotel_staff(
    hotel_id: int,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    staff_list = crud_staff.get_hotel_staff_list(db, hotel_id)

    return api_response(
        success=True,
        message="Hotel staff list retrieved",
        data=[
            {
                "id": s.id,
                "user_id": s.user_id,
                "full_name": s.user.full_name if s.user else None,
                "email": s.user.email if s.user else None,
                "department": s.department,
                "position": s.position,
                "permissions": s.permissions,
                "is_active": s.is_active,
                "created_at": s.created_at.isoformat()
            }
            for s in staff_list
        ]
    )


@router.put("/{staff_id}", summary="Update staff assignment")
def update_staff(
    staff_id: int,
    request: StaffUpdate,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    staff_entry = crud_staff.get_staff_by_id(db, staff_id)
    if not staff_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff record not found")

    verify_hotel_access(staff_entry.hotel_id, current_user, db)

    updated = crud_staff.update_staff_assignment(
        db=db,
        staff_entry=staff_entry,
        department=request.department,
        position=request.position,
        permissions=request.permissions,
        is_active=request.is_active
    )

    return api_response(
        success=True,
        message="Staff assignment updated successfully",
        data={
            "id": updated.id,
            "department": updated.department,
            "position": updated.position,
            "permissions": updated.permissions,
            "is_active": updated.is_active
        }
    )


@router.post("/attendance", summary="Record staff clock-in / clock-out")
def clock_attendance(
    hotel_id: int,
    request: AttendanceClockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = crud_staff.record_attendance(
        db=db,
        staff_user_id=current_user.id,
        hotel_id=hotel_id,
        action=request.action,
        notes=request.notes
    )

    return api_response(
        success=True,
        message=f"Attendance {request.action.upper()} recorded successfully",
        data={
            "id": record.id,
            "staff_user_id": record.staff_user_id,
            "hotel_id": record.hotel_id,
            "date": record.date.isoformat(),
            "clock_in": record.clock_in.isoformat() if record.clock_in else None,
            "clock_out": record.clock_out.isoformat() if record.clock_out else None,
            "total_hours": record.total_hours,
            "status": record.status
        }
    )


@router.get("/attendance/{staff_user_id}", summary="View staff attendance records")
def get_attendance(
    staff_user_id: int,
    hotel_id: int,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    records = crud_staff.get_staff_attendance_records(db, staff_user_id, hotel_id)

    return api_response(
        success=True,
        message="Staff attendance records retrieved",
        data=[
            {
                "id": r.id,
                "date": r.date.isoformat(),
                "clock_in": r.clock_in.isoformat() if r.clock_in else None,
                "clock_out": r.clock_out.isoformat() if r.clock_out else None,
                "total_hours": r.total_hours,
                "status": r.status,
                "notes": r.notes
            }
            for r in records
        ]
    )


@router.get("/activities/{staff_user_id}", summary="View staff activity logs")
def get_activities(
    staff_user_id: int,
    hotel_id: int,
    limit: int = 50,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.HOTEL_STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    logs = crud_staff.get_staff_activity_logs(db, staff_user_id, hotel_id, limit=limit)

    return api_response(
        success=True,
        message="Staff activity logs retrieved",
        data=[
            {
                "id": l.id,
                "action": l.action,
                "description": l.description,
                "timestamp": l.timestamp.isoformat()
            }
            for l in logs
        ]
    )
