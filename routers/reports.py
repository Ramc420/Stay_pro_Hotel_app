"""
Module 38: Reports and Export
Generates tabular business reports with CSV, Excel, and printable PDF exports.
"""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.dependencies import require_roles
from utils.response import api_response
from crud import reports as crud_rep

router = APIRouter(prefix="/reports", tags=["Module 38: Reports and Export"])


@router.get("/{report_type}", summary="Generate and export business report")
def get_report(
    report_type: str,  # bookings, payments, hotels, customers
    hotel_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    format: str = "json",  # json, csv, excel, pdf
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    dataset = crud_rep.generate_report_dataset(
        db=db,
        report_type=report_type,
        hotel_id=hotel_id,
        start_date=start_date,
        end_date=end_date
    )

    fmt = format.lower()
    if fmt == "csv":
        csv_content = crud_rep.export_as_csv(dataset)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={report_type}_report.csv"}
        )

    if fmt in ["excel", "xlsx"]:
        # Standard CSV content with excel application header
        csv_content = crud_rep.export_as_csv(dataset)
        return Response(
            content=csv_content,
            media_type="application/vnd.ms-excel",
            headers={"Content-Disposition": f"attachment; filename={report_type}_report.xls"}
        )

    if fmt == "pdf":
        html_content = crud_rep.export_as_html_report(report_type, dataset)
        return Response(content=html_content, media_type="text/html")

    # Default: json
    return api_response(
        success=True,
        message=f"{report_type.title()} report generated successfully",
        data=dataset,
        meta={"total_records": len(dataset), "report_type": report_type}
    )
