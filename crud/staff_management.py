from typing import Optional, List, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from models import User, UserRole, HotelStaff, StaffAttendance, StaffActivityLog


def assign_hotel_staff(
    db: Session,
    user_id: int,
    hotel_id: int,
    department: str = "Front Desk",
    position: str = "Staff",
    permissions: Optional[List[str]] = None
) -> HotelStaff:
    """Assign an existing user as staff to a hotel with specific permissions."""
    # Ensure user has HOTEL_STAFF role
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.role == UserRole.CUSTOMER:
        user.role = UserRole.HOTEL_STAFF

    existing = db.query(HotelStaff).filter(
        HotelStaff.user_id == user_id,
        HotelStaff.hotel_id == hotel_id
    ).first()

    if existing:
        existing.department = department
        existing.position = position
        existing.permissions = permissions or ["FRONT_DESK"]
        existing.is_active = True
        staff_entry = existing
    else:
        staff_entry = HotelStaff(
            user_id=user_id,
            hotel_id=hotel_id,
            department=department,
            position=position,
            permissions=permissions or ["FRONT_DESK"],
            is_active=True
        )
        db.add(staff_entry)

    db.commit()
    db.refresh(staff_entry)
    log_staff_activity(db, user_id, hotel_id, "STAFF_ASSIGNED", f"Assigned to {department} as {position}")
    return staff_entry


def update_staff_assignment(
    db: Session,
    staff_entry: HotelStaff,
    department: Optional[str] = None,
    position: Optional[str] = None,
    permissions: Optional[List[str]] = None,
    is_active: Optional[bool] = None
) -> HotelStaff:
    """Update staff department, position, permissions, or active status."""
    if department is not None:
        staff_entry.department = department
    if position is not None:
        staff_entry.position = position
    if permissions is not None:
        staff_entry.permissions = permissions
    if is_active is not None:
        staff_entry.is_active = is_active

    db.commit()
    db.refresh(staff_entry)
    log_staff_activity(db, staff_entry.user_id, staff_entry.hotel_id, "STAFF_UPDATED", "Staff profile updated")
    return staff_entry


def get_hotel_staff_list(db: Session, hotel_id: int) -> List[HotelStaff]:
    """Retrieve all staff members assigned to a hotel."""
    return db.query(HotelStaff).filter(
        HotelStaff.hotel_id == hotel_id
    ).all()


def get_staff_by_id(db: Session, staff_id: int) -> Optional[HotelStaff]:
    """Retrieve a staff assignment by its primary key ID."""
    return db.query(HotelStaff).filter(HotelStaff.id == staff_id).first()


def record_attendance(
    db: Session,
    staff_user_id: int,
    hotel_id: int,
    action: str,  # CLOCK_IN, CLOCK_OUT
    notes: Optional[str] = None
) -> StaffAttendance:
    """Record clock-in or clock-out for today."""
    today = date.today()
    attendance = db.query(StaffAttendance).filter(
        StaffAttendance.staff_user_id == staff_user_id,
        StaffAttendance.hotel_id == hotel_id,
        StaffAttendance.date == today
    ).first()

    now = datetime.utcnow()

    if action.upper() == "CLOCK_IN":
        if not attendance:
            attendance = StaffAttendance(
                staff_user_id=staff_user_id,
                hotel_id=hotel_id,
                date=today,
                clock_in=now,
                status="PRESENT",
                notes=notes
            )
            db.add(attendance)
        else:
            attendance.clock_in = now
            if notes:
                attendance.notes = notes
        log_staff_activity(db, staff_user_id, hotel_id, "CLOCK_IN", f"Clocked in at {now.strftime('%H:%M:%S')}")
    elif action.upper() == "CLOCK_OUT":
        if not attendance:
            attendance = StaffAttendance(
                staff_user_id=staff_user_id,
                hotel_id=hotel_id,
                date=today,
                clock_out=now,
                status="PRESENT",
                notes=notes
            )
            db.add(attendance)
        else:
            attendance.clock_out = now
            if attendance.clock_in:
                diff_seconds = (now - attendance.clock_in).total_seconds()
                attendance.total_hours = round(diff_seconds / 3600.0, 2)
            if notes:
                attendance.notes = notes
        log_staff_activity(db, staff_user_id, hotel_id, "CLOCK_OUT", f"Clocked out at {now.strftime('%H:%M:%S')}")

    db.commit()
    db.refresh(attendance)
    return attendance


def get_staff_attendance_records(
    db: Session,
    staff_user_id: int,
    hotel_id: int
) -> List[StaffAttendance]:
    """Get attendance history for a staff member."""
    return db.query(StaffAttendance).filter(
        StaffAttendance.staff_user_id == staff_user_id,
        StaffAttendance.hotel_id == hotel_id
    ).order_by(StaffAttendance.date.desc()).all()


def log_staff_activity(
    db: Session,
    staff_user_id: int,
    hotel_id: int,
    action: str,
    description: str
) -> StaffActivityLog:
    """Persist an audit log of staff operations."""
    log = StaffActivityLog(
        staff_user_id=staff_user_id,
        hotel_id=hotel_id,
        action=action,
        description=description,
        timestamp=datetime.utcnow()
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_staff_activity_logs(
    db: Session,
    staff_user_id: int,
    hotel_id: int,
    limit: int = 50
) -> List[StaffActivityLog]:
    """Retrieve activity history for a staff member."""
    return db.query(StaffActivityLog).filter(
        StaffActivityLog.staff_user_id == staff_user_id,
        StaffActivityLog.hotel_id == hotel_id
    ).order_by(StaffActivityLog.timestamp.desc()).limit(limit).all()
