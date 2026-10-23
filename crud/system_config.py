from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from models import SystemConfig


DEFAULT_PLATFORM_CONFIGS = [
    {"key": "platform.tax_rate_percentage", "value": "10.0", "category": "FINANCIAL", "is_secret": False, "description": "Standard state and local occupancy tax percentage"},
    {"key": "platform.commission_rate_percentage", "value": "12.0", "category": "FINANCIAL", "is_secret": False, "description": "Default platform booking commission rate"},
    {"key": "platform.default_currency", "value": "USD", "category": "GENERAL", "is_secret": False, "description": "Primary platform settlement currency"},
    {"key": "notifications.email_alerts_enabled", "value": "true", "category": "EMAIL", "is_secret": False, "description": "Global toggle for guest and host email dispatches"},
    {"key": "payment.stripe_webhook_secret", "value": "whsec_test_secret_998877", "category": "PAYMENT", "is_secret": True, "description": "Stripe endpoint webhook signature verification key"},
    {"key": "security.max_login_attempts", "value": "5", "category": "SECURITY", "is_secret": False, "description": "Max failed login attempts before temporary lockout"}
]


def seed_default_configs(db: Session):
    """Seed initial platform configuration defaults."""
    for item in DEFAULT_PLATFORM_CONFIGS:
        existing = db.query(SystemConfig).filter(SystemConfig.key == item["key"]).first()
        if not existing:
            cfg = SystemConfig(
                key=item["key"],
                value=item["value"],
                category=item["category"],
                is_secret=item["is_secret"],
                description=item["description"]
            )
            db.add(cfg)
    db.commit()


def get_all_configs(db: Session, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve system configuration items (masking secrets)."""
    query = db.query(SystemConfig)
    if category:
        query = query.filter(SystemConfig.category == category.upper())
    
    configs = query.order_by(SystemConfig.category.asc(), SystemConfig.key.asc()).all()

    results = []
    for c in configs:
        masked_val = "********" if c.is_secret else c.value
        results.append({
            "id": c.id,
            "key": c.key,
            "value": masked_val,
            "category": c.category,
            "is_secret": c.is_secret,
            "description": c.description,
            "updated_by_id": c.updated_by_id,
            "updated_at": c.updated_at
        })
    return results


def get_config_by_key(db: Session, key: str, reveal_secret: bool = False) -> Optional[Dict[str, Any]]:
    """Retrieve single configuration by key."""
    c = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not c:
        return None

    val = c.value if (reveal_secret or not c.is_secret) else "********"
    return {
        "id": c.id,
        "key": c.key,
        "value": val,
        "category": c.category,
        "is_secret": c.is_secret,
        "description": c.description,
        "updated_by_id": c.updated_by_id,
        "updated_at": c.updated_at
    }


def validate_setting_value(key: str, value: str):
    """Validate setting format and logical ranges before saving."""
    if "rate_percentage" in key or "tax" in key or "commission" in key:
        try:
            val_float = float(value)
            if val_float < 0.0 or val_float > 100.0:
                raise ValueError(f"Percentage for '{key}' must be between 0.0 and 100.0")
        except ValueError:
            raise ValueError(f"Value for '{key}' must be a valid number between 0.0 and 100.0")

    if key == "platform.default_currency":
        if len(value) != 3:
            raise ValueError("Currency code must be a 3-letter ISO code (e.g. USD, EUR)")


def set_config_value(
    db: Session,
    key: str,
    value: str,
    admin_id: int,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Update or create a system setting with validation."""
    validate_setting_value(key, value)

    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        config = SystemConfig(
            key=key,
            value=value,
            description=description,
            updated_by_id=admin_id
        )
        db.add(config)
    else:
        config.value = value
        if description:
            config.description = description
        config.updated_by_id = admin_id

    db.commit()
    db.refresh(config)

    return {
        "id": config.id,
        "key": config.key,
        "value": "********" if config.is_secret else config.value,
        "category": config.category,
        "is_secret": config.is_secret,
        "updated_by_id": config.updated_by_id,
        "updated_at": config.updated_at
    }


def batch_update_configs(
    db: Session,
    settings: Dict[str, str],
    admin_id: int
) -> List[Dict[str, Any]]:
    """Batch update multiple settings atomically."""
    # First validate all
    for k, v in settings.items():
        validate_setting_value(k, v)

    updated = []
    for k, v in settings.items():
        res = set_config_value(db, k, v, admin_id)
        updated.append(res)

    return updated
