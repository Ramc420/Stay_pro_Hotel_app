from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from models import (
    Room, RoomStatus, HousekeepingTask, HousekeepingInspection, HousekeepingStatus
)


def create_task(
    db: Session,
    hotel_id: int,
    room_id: int,
    assigned_staff_id: Optional[int] = None,
    task_type: str = "CLEANING",
    priority: str = "MEDIUM",
    notes: Optional[str] = None
) -> HousekeepingTask:
    """Create a new housekeeping task for a room."""
    # Default status based on type
    initial_status = HousekeepingStatus.MAINTENANCE if task_type.upper() == "MAINTENANCE" else HousekeepingStatus.DIRTY

    task = HousekeepingTask(
        hotel_id=hotel_id,
        room_id=room_id,
        assigned_staff_id=assigned_staff_id,
        task_type=task_type.upper(),
        status=initial_status,
        priority=priority.upper(),
        notes=notes
    )
    db.add(task)

    # Sync room status
    room = db.query(Room).filter(Room.id == room_id).first()
    if room:
        if task.status == HousekeepingStatus.MAINTENANCE:
            room.status = RoomStatus.MAINTENANCE
        elif task.status in [HousekeepingStatus.DIRTY, HousekeepingStatus.CLEANING]:
            room.status = RoomStatus.CLEANING

    db.commit()
    db.refresh(task)
    return task


def get_tasks(
    db: Session,
    hotel_id: int,
    status: Optional[str] = None,
    assigned_staff_id: Optional[int] = None,
    room_id: Optional[int] = None
) -> List[HousekeepingTask]:
    """Filter housekeeping tasks for a hotel."""
    query = db.query(HousekeepingTask).filter(HousekeepingTask.hotel_id == hotel_id)

    if status:
        query = query.filter(HousekeepingTask.status == status.upper())
    if assigned_staff_id:
        query = query.filter(HousekeepingTask.assigned_staff_id == assigned_staff_id)
    if room_id:
        query = query.filter(HousekeepingTask.room_id == room_id)

    return query.order_by(HousekeepingTask.created_at.desc()).all()


def get_task_by_id(db: Session, task_id: int) -> Optional[HousekeepingTask]:
    """Retrieve single task by ID."""
    return db.query(HousekeepingTask).filter(HousekeepingTask.id == task_id).first()


def update_task_status(
    db: Session,
    task: HousekeepingTask,
    new_status: str,
    notes: Optional[str] = None
) -> HousekeepingTask:
    """
    Update task status across the 5 states:
    DIRTY -> CLEANING -> INSPECTION -> CLEAN (or MAINTENANCE).
    Synchronizes room status.
    """
    valid_status = HousekeepingStatus(new_status.upper())
    task.status = valid_status
    if notes:
        task.notes = f"{task.notes or ''} | {notes}".strip(" | ")

    room = db.query(Room).filter(Room.id == task.room_id).first()

    if valid_status == HousekeepingStatus.CLEAN:
        task.completed_at = datetime.utcnow()
        if room and room.status != RoomStatus.OCCUPIED:
            room.status = RoomStatus.AVAILABLE
    elif valid_status == HousekeepingStatus.CLEANING:
        if room and room.status != RoomStatus.OCCUPIED:
            room.status = RoomStatus.CLEANING
    elif valid_status == HousekeepingStatus.MAINTENANCE:
        if room:
            room.status = RoomStatus.MAINTENANCE

    db.commit()
    db.refresh(task)
    return task


def record_inspection(
    db: Session,
    task: HousekeepingTask,
    inspector_id: int,
    is_passed: bool,
    rating: float = 5.0,
    checklist: Optional[Dict[str, Any]] = None,
    comments: Optional[str] = None
) -> HousekeepingInspection:
    """Record an inspection for a cleaned room."""
    inspection = HousekeepingInspection(
        task_id=task.id,
        room_id=task.room_id,
        inspector_id=inspector_id,
        is_passed=is_passed,
        rating=rating,
        checklist=checklist or {},
        comments=comments
    )
    db.add(inspection)

    # If passed, advance task to CLEAN
    if is_passed:
        task.status = HousekeepingStatus.CLEAN
        task.completed_at = datetime.utcnow()
        room = db.query(Room).filter(Room.id == task.room_id).first()
        if room and room.status != RoomStatus.OCCUPIED:
            room.status = RoomStatus.AVAILABLE
    else:
        # Failed inspection -> back to DIRTY / CLEANING
        task.status = HousekeepingStatus.DIRTY

    db.commit()
    db.refresh(inspection)
    return inspection


def get_hotel_rooms_housekeeping_overview(db: Session, hotel_id: int) -> List[Dict[str, Any]]:
    """Return an overview of all rooms and their current housekeeping condition."""
    rooms = db.query(Room).filter(Room.hotel_id == hotel_id, Room.is_active == True).all()
    overview = []
    for r in rooms:
        latest_task = db.query(HousekeepingTask).filter(
            HousekeepingTask.room_id == r.id
        ).order_by(HousekeepingTask.created_at.desc()).first()

        overview.append({
            "room_id": r.id,
            "room_number": r.room_number,
            "room_status": r.status.value,
            "housekeeping_status": latest_task.status.value if latest_task else "CLEAN",
            "active_task_id": latest_task.id if latest_task else None,
            "assigned_staff_id": latest_task.assigned_staff_id if latest_task else None
        })
    return overview
