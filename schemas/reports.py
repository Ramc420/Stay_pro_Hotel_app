from typing import Optional, List, Dict, Any
from datetime import date
from pydantic import BaseModel


class ReportFilterRequest(BaseModel):
    report_type: str  # bookings, revenue, occupancy, customers, hotels, payments
    hotel_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    format: Optional[str] = "json"  # json, csv, excel, pdf
