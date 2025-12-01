"""
API Response Helpers - Standard Response Envelopes

All endpoints should use these helpers to ensure consistent response formats.

Usage:
    from api.helpers import list_response, item_response, action_response

Response Format Standards:
    - Lists: {"data": [...], "meta": {"total": N, "page": 1, "per_page": 50, "has_more": bool}}
    - Single items: {"data": {...}, "meta": {"fetched_at": "..."}}
    - Actions: {"success": bool, "data": {...}, "message": "..."}
    - Errors: {"error": true, "code": "...", "message": "...", "detail": "..."}

Created: 2025-11-28
Owner: Backend Builder Agent
"""

from typing import Any, Optional, List, Union
from datetime import datetime


def list_response(
    data: List[Any],
    total: Optional[int] = None,
    page: int = 1,
    per_page: int = 50
) -> dict:
    """
    Standard response envelope for list endpoints.

    Args:
        data: List of items to return
        total: Total count of all items (for pagination). If None, uses len(data)
        page: Current page number (1-indexed)
        per_page: Items per page

    Returns:
        Standardized response dict with data and meta

    Example:
        return list_response(proposals, total=89, page=1, per_page=50)
        # Returns: {"data": [...], "meta": {"total": 89, "page": 1, "per_page": 50, "has_more": true}}
    """
    if total is None:
        total = len(data)

    return {
        "data": data,
        "meta": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "has_more": (page * per_page) < total
        }
    }


def item_response(data: Any, include_timestamp: bool = True) -> dict:
    """
    Standard response envelope for single item endpoints.

    Args:
        data: The item to return (dict, or None)
        include_timestamp: Whether to include fetched_at timestamp

    Returns:
        Standardized response dict with data and meta

    Example:
        return item_response(proposal)
        # Returns: {"data": {...}, "meta": {"fetched_at": "2025-11-28T12:00:00Z"}}
    """
    meta = {}
    if include_timestamp:
        meta["fetched_at"] = datetime.utcnow().isoformat() + "Z"

    return {
        "data": data,
        "meta": meta
    }


def action_response(
    success: bool,
    data: Any = None,
    message: Optional[str] = None
) -> dict:
    """
    Standard response envelope for action endpoints (POST/PATCH/DELETE).

    Args:
        success: Whether the action succeeded
        data: Optional data to return (created/updated item)
        message: Optional human-readable message

    Returns:
        Standardized response dict

    Example:
        return action_response(True, data=new_proposal, message="Proposal created")
        # Returns: {"success": true, "data": {...}, "message": "Proposal created"}
    """
    response = {"success": success}
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    return response


def error_response(
    code: str,
    message: str,
    detail: Optional[str] = None,
    status_code: int = 400
) -> dict:
    """
    Standard error response envelope.

    Note: This returns the response dict. To properly return HTTP errors,
    use FastAPI's HTTPException with this as the detail, or JSONResponse.

    Args:
        code: Machine-readable error code (e.g., "NOT_FOUND", "VALIDATION_ERROR")
        message: Human-readable error message
        detail: Optional additional debug information
        status_code: HTTP status code (for reference, not included in response)

    Returns:
        Standardized error response dict

    Example:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", "Project BK-999 not found"))
    """
    response = {
        "error": True,
        "code": code,
        "message": message
    }
    if detail:
        response["detail"] = detail
    return response


# Common error codes for consistency
class ErrorCodes:
    """Standard error codes for the API"""
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    DUPLICATE = "DUPLICATE"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    BAD_REQUEST = "BAD_REQUEST"
    CONFLICT = "CONFLICT"


def paginate_list(
    items: List[Any],
    page: int = 1,
    per_page: int = 50
) -> tuple[List[Any], int]:
    """
    Helper to paginate a list in memory.

    Args:
        items: Full list of items
        page: Page number (1-indexed)
        per_page: Items per page

    Returns:
        Tuple of (paginated_items, total_count)

    Example:
        items, total = paginate_list(all_proposals, page=2, per_page=20)
        return list_response(items, total=total, page=2, per_page=20)
    """
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], total
