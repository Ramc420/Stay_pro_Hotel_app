from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class AmenityCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    category: str = Field(default="GENERAL")
    icon: Optional[str] = None
    description: Optional[str] = None


class AmenityUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class AmenityResponse(BaseModel):
    id: int
    name: str
    category: str
    icon: Optional[str] = None
    description: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AssociateAmenitiesRequest(BaseModel):
    amenity_ids: List[int] = Field(..., min_length=1)
