"""
Module 49: System Configuration
Platform settings, financial rates, currencies, email, and secure masked configuration management.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.dependencies import require_roles
from utils.response import api_response
from schemas.system_config import (
    SystemConfigUpdateRequest, SystemConfigBatchUpdateRequest, SystemConfigCreateRequest
)
from crud import system_config as crud_cfg

router = APIRouter(prefix="/system-config", tags=["Module 49: System Configuration"])


@router.get("", summary="Retrieve platform system configurations (Admin only)")
def list_configs(
    category: Optional[str] = None,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    configs = crud_cfg.get_all_configs(db, category=category)
    return api_response(
        success=True,
        message="System configurations retrieved",
        data=configs
    )


@router.get("/{key}", summary="Retrieve specific configuration setting by key (Admin only)")
def get_config(
    key: str,
    reveal_secret: bool = False,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    cfg = crud_cfg.get_config_by_key(db, key, reveal_secret=reveal_secret)
    if not cfg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Configuration key '{key}' not found")
    return api_response(
        success=True,
        message="System configuration retrieved",
        data=cfg
    )


@router.put("/{key}", summary="Update platform configuration setting with validation (Admin only)")
def update_config(
    key: str,
    request: SystemConfigUpdateRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    try:
        updated = crud_cfg.set_config_value(
            db=db,
            key=key,
            value=request.value,
            admin_id=current_user.id,
            description=request.description
        )
        return api_response(
            success=True,
            message=f"Configuration '{key}' updated successfully",
            data=updated
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/batch", summary="Batch update multiple platform settings (Admin only)")
def batch_update(
    request: SystemConfigBatchUpdateRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    try:
        results = crud_cfg.batch_update_configs(
            db=db,
            settings=request.settings,
            admin_id=current_user.id
        )
        return api_response(
            success=True,
            message=f"Batch updated {len(results)} system setting(s)",
            data=results
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reset-defaults", summary="Seed standard platform defaults if missing (Admin only)")
def reset_defaults(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    crud_cfg.seed_default_configs(db)
    configs = crud_cfg.get_all_configs(db)
    return api_response(
        success=True,
        message="Platform default configurations ensured",
        data=configs
    )
