from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SystemConfigItemResponse(BaseModel):
    id: int
    key: str
    value: str
    category: str
    is_secret: bool
    description: Optional[str] = None
    updated_by_id: Optional[int] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class SystemConfigUpdateRequest(BaseModel):
    value: str
    description: Optional[str] = None


class SystemConfigBatchUpdateRequest(BaseModel):
    settings: Dict[str, str]  # key: new_value


class SystemConfigCreateRequest(BaseModel):
    key: str
    value: str
    category: str = "GENERAL"
    is_secret: bool = False
    description: Optional[str] = None
