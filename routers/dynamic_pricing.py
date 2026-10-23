"""
Module 42: Dynamic Pricing Management
Configures seasonal, weekend, holiday, and promotional prices, applies date-specific pricing, and prevents conflicts.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole
from auth.dependencies import verify_hotel_access, require_roles, get_current_user
from utils.response import api_response
from schemas.dynamic_pricing import (
    DynamicPricingRuleCreate, DynamicPricingRuleUpdate, PriceCalculationRequest
)
from crud import dynamic_pricing as crud_pricing

router = APIRouter(prefix="/pricing-rules", tags=["Module 42: Dynamic Pricing Management"])


@router.post("", summary="Configure dynamic pricing rule (Seasonal, Weekend, Holiday, Promo)")
def create_rule(
    request: DynamicPricingRuleCreate,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(request.hotel_id, current_user, db)
    try:
        rule = crud_pricing.create_pricing_rule(
            db=db,
            hotel_id=request.hotel_id,
            rule_name=request.rule_name,
            rule_type=request.rule_type,
            adjustment_type=request.adjustment_type,
            adjustment_value=request.adjustment_value,
            room_type_id=request.room_type_id,
            start_date=request.start_date,
            end_date=request.end_date,
            days_of_week=request.days_of_week,
            priority=request.priority,
            is_active=request.is_active
        )
        return api_response(
            success=True,
            message="Dynamic pricing rule created successfully",
            data={
                "id": rule.id,
                "hotel_id": rule.hotel_id,
                "room_type_id": rule.room_type_id,
                "rule_name": rule.rule_name,
                "rule_type": rule.rule_type.value,
                "adjustment_type": rule.adjustment_type.value,
                "adjustment_value": rule.adjustment_value,
                "start_date": rule.start_date.isoformat() if rule.start_date else None,
                "end_date": rule.end_date.isoformat() if rule.end_date else None,
                "days_of_week": rule.days_of_week,
                "priority": rule.priority,
                "is_active": rule.is_active,
                "created_at": rule.created_at.isoformat()
            },
            status_code=status.HTTP_201_CREATED
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/hotels/{hotel_id}", summary="Retrieve dynamic pricing rules for hotel")
def list_rules(
    hotel_id: int,
    active_only: bool = False,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    verify_hotel_access(hotel_id, current_user, db)
    rules = crud_pricing.get_pricing_rules(db, hotel_id, active_only=active_only)
    return api_response(
        success=True,
        message="Dynamic pricing rules retrieved",
        data=[
            {
                "id": r.id,
                "hotel_id": r.hotel_id,
                "room_type_id": r.room_type_id,
                "rule_name": r.rule_name,
                "rule_type": r.rule_type.value,
                "adjustment_type": r.adjustment_type.value,
                "adjustment_value": r.adjustment_value,
                "start_date": r.start_date.isoformat() if r.start_date else None,
                "end_date": r.end_date.isoformat() if r.end_date else None,
                "days_of_week": r.days_of_week,
                "priority": r.priority,
                "is_active": r.is_active,
                "created_at": r.created_at.isoformat()
            }
            for r in rules
        ]
    )


@router.put("/{rule_id}", summary="Update dynamic pricing rule")
def update_rule(
    rule_id: int,
    request: DynamicPricingRuleUpdate,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    rule = crud_pricing.get_pricing_rule_by_id(db, rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pricing rule not found")
    verify_hotel_access(rule.hotel_id, current_user, db)

    updated = crud_pricing.update_pricing_rule(db, rule_id, **request.model_dump(exclude_unset=True))
    return api_response(
        success=True,
        message="Dynamic pricing rule updated",
        data={
            "id": updated.id,
            "rule_name": updated.rule_name,
            "adjustment_value": updated.adjustment_value,
            "is_active": updated.is_active
        }
    )


@router.delete("/{rule_id}", summary="Delete dynamic pricing rule")
def delete_rule(
    rule_id: int,
    current_user: User = Depends(require_roles(UserRole.HOTEL_OWNER, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    rule = crud_pricing.get_pricing_rule_by_id(db, rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pricing rule not found")
    verify_hotel_access(rule.hotel_id, current_user, db)

    crud_pricing.delete_pricing_rule(db, rule_id)
    return api_response(success=True, message="Pricing rule deleted successfully")


@router.post("/calculate", summary="Calculate final booking prices with dynamic adjustments")
def calculate_price(
    request: PriceCalculationRequest,
    db: Session = Depends(get_db)
):
    try:
        quote = crud_pricing.calculate_booking_price(
            db=db,
            hotel_id=request.hotel_id,
            room_type_id=request.room_type_id,
            check_in=request.check_in_date,
            check_out=request.check_out_date
        )
        return api_response(
            success=True,
            message="Dynamic room price calculated successfully",
            data=quote
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
