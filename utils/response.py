from typing import Any, Optional, Dict
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import status


def api_response(
    success: bool = True,
    message: str = "Operation completed successfully",
    data: Any = None,
    errors: Any = None,
    meta: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    content: Dict[str, Any] = {
        "success": success,
        "message": message,
    }
    if data is not None:
        content["data"] = data
    if errors is not None:
        content["errors"] = errors
    if meta is not None:
        content["meta"] = meta
    return JSONResponse(status_code=status_code, content=jsonable_encoder(content))



def paginated_response(
    items: list,
    total: int,
    page: int,
    limit: int,
    message: str = "Records retrieved successfully"
) -> JSONResponse:
    pages = (total + limit - 1) // limit if limit > 0 else 1
    return api_response(
        success=True,
        message=message,
        data={
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": pages,
                "has_next": page < pages,
                "has_prev": page > 1
            }
        }
    )
