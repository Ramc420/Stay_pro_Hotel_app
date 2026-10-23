from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field


class RoomDayAvailability(BaseModel):
    date: date
    status: str  # AVAILABLE, BOOKED, BLOCKED, MAINTENANCE
    booking_id: Optional[int] = None
    booking_ref: Optional[str] = None
    guest_name: Optional[str] = None
    nightly_price: Optional[float] = None


class RoomCalendarRow(BaseModel):
    room_id: int
    room_number: str
    room_type_id: int
    room_type_name: str
    days: List[RoomDayAvailability]


class CalendarGridResponse(BaseModel):
    hotel_id: int
    start_date: date
    end_date: date
    total_rooms: int
    rooms: List[RoomCalendarRow]


class ScheduleEntry(BaseModel):
    booking_id: int
    booking_reference: str
    guest_name: str
    guest_phone: Optional[str] = None
    room_number: Optional[str] = None
    room_type: str
    scheduled_type: str  # ARRIVAL, DEPARTURE
    date: date
    expected_time: str
    status: str


class ScheduleSummaryResponse(BaseModel):
    hotel_id: int
    target_date: date
    total_arrivals: int
    total_departures: int
    arrivals: List[ScheduleEntry]
    departures: List[ScheduleEntry]


class RoomConflictCheckRequest(BaseModel):
    room_id: int
    check_in_date: date
    check_out_date: date
    exclude_booking_id: Optional[int] = None


class RoomConflictCheckResponse(BaseModel):
    room_id: int
    has_conflict: bool
    is_available: bool
    conflicting_bookings: List[Dict[str, Any]] = []
    message: str


class ScheduledJobsRunResponse(BaseModel):
    jobs_executed: int
    jobs_succeeded: int
    jobs_failed: int
    executed_jobs: List[Dict[str, Any]]
