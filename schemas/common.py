from typing import Optional, Any, Dict
from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Any] = None
    errors: Optional[Any] = None
    meta: Optional[Dict[str, Any]] = None


class PaginationMetadata(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
