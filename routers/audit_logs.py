"""
Module 39: Audit Logs and Security Monitoring
Provides append-only immutable audit logging of critical actions, authentication, and security events.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.dependencies import require_roles
from utils.response import api_response
from schemas.audit_logs import AuditLogCreate
from crud import audit_logs as crud_audit

router = APIRouter(prefix="/audit-logs", tags=["Module 39: Audit Logs and Security Monitoring"])


@router.get("/", summary="List system audit logs")
def list_audit_logs(
    event_type: Optional[str] = None,
    user_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    logs = crud_audit.get_audit_logs(db, event_type=event_type, user_id=user_id, limit=limit, offset=offset)
    return api_response(
        success=True,
        message="Audit logs retrieved",
        data=[
            {
                "id": l.id,
                "user_id": l.user_id,
                "event_type": l.event_type,
                "action": l.action,
                "ip_address": l.ip_address,
                "description": l.description,
                "details": l.details,
                "created_at": l.created_at.isoformat()
            }
            for l in logs
        ]
    )


@router.get("/security-events", summary="List security alerts and authentication incidents")
def list_security_events(
    limit: int = 50,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    events = crud_audit.get_security_events(db, limit=limit)
    return api_response(
        success=True,
        message="Security events retrieved",
        data=[
            {
                "id": e.id,
                "event_type": e.event_type,
                "action": e.action,
                "description": e.description,
                "ip_address": e.ip_address,
                "created_at": e.created_at.isoformat()
            }
            for e in events
        ]
    )


@router.post("/event", summary="Record custom audit log event")
def record_event(
    request: AuditLogCreate,
    client_req: Request,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOTEL_OWNER)),
    db: Session = Depends(get_db)
):
    client_ip = request.ip_address or (client_req.client.host if client_req.client else None)
    log = crud_audit.log_audit_event(
        db=db,
        event_type=request.event_type,
        action=request.action,
        description=request.description,
        user_id=current_user.id,
        ip_address=client_ip,
        details=request.details
    )

    return api_response(
        success=True,
        message="Audit log entry committed",
        data={"id": log.id, "event_type": log.event_type, "action": log.action},
        status_code=status.HTTP_201_CREATED
    )
