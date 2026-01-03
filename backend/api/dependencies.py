"""
API Dependencies - Shared dependencies for all routers

Usage:
    from api.dependencies import get_db, DB_PATH, get_current_user

    @router.get("/endpoint")
    async def endpoint(db = Depends(get_db)):
        ...

    @router.get("/protected")
    async def protected(user = Depends(get_current_user)):
        ...
"""

import os
import sqlite3
from pathlib import Path
from typing import Generator, Optional
from contextlib import contextmanager

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Security scheme for JWT Bearer tokens
security = HTTPBearer(auto_error=False)

# Database path - use environment variable with fallback
DB_PATH = os.getenv(
    'DATABASE_PATH',
    os.path.join(
        Path(__file__).parent.parent.parent,
        "database",
        "bensley_master.db"
    )
)


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Database dependency for FastAPI endpoints.

    Yields a SQLite connection with Row factory enabled.
    Connection is automatically closed when the request completes.

    Usage:
        @router.get("/items")
        async def get_items(db = Depends(get_db)):
            cursor = db.cursor()
            cursor.execute("SELECT * FROM items")
            return cursor.fetchall()
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # CRITICAL: Enable FK enforcement
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_db_context():
    """
    Context manager version for non-FastAPI use (background tasks, services).

    Usage:
        with get_db_context() as db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM items")
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # CRITICAL: Enable FK enforcement
    try:
        yield conn
    finally:
        conn.close()


def get_db_connection() -> sqlite3.Connection:
    """
    Get a raw database connection (caller responsible for closing).

    Prefer get_db() with Depends() or get_db_context() instead.
    This is for backward compatibility with existing code.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # CRITICAL: Enable FK enforcement
    return conn


# ============================================================================
# AUTHENTICATION DEPENDENCIES
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: sqlite3.Connection = Depends(get_db)
) -> dict:
    """
    Dependency to get the current authenticated user from JWT token.

    Usage:
        @router.get("/protected")
        async def protected_route(user = Depends(get_current_user)):
            return {"message": f"Hello {user['first_name']}"}

    Raises:
        HTTPException 401 if token is missing, invalid, or expired
        HTTPException 401 if user not found or inactive
    """
    # Import here to avoid circular imports
    from api.security import decode_access_token

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = decode_access_token(credentials.credentials)
    if not token_data or not token_data.staff_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    cursor = db.cursor()
    cursor.execute(
        """SELECT * FROM staff WHERE staff_id = ? AND is_active = 1""",
        (token_data.staff_id,)
    )
    user = cursor.fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    return dict(user)


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: sqlite3.Connection = Depends(get_db)
) -> Optional[dict]:
    """
    Optional authentication - returns user if authenticated, None otherwise.

    Use for endpoints that work with or without auth.
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


# ============================================================================
# ROLE-BASED ACCESS CONTROL (RBAC)
# ============================================================================

RBAC_ROLES = {
    "executive": "Full access to all data and features",
    "finance": "Access to financial data and read-only projects",
    "pm": "Access to assigned projects only, no financial data",
    "admin": "Full access including admin functions",
    "staff": "Limited access - design team members",
}


def get_user_access_level(user: dict) -> str:
    """
    Compute the RBAC access level from staff attributes.

    Mapping:
    - executive: Leadership + (Owner or Principal seniority)
    - admin: Leadership + Director, or Operations role
    - finance: Finance department
    - pm: is_pm flag = 1
    - staff: Everyone else (designers)
    """
    department = user.get("department", "")
    seniority = user.get("seniority", "")
    is_pm = user.get("is_pm", 0)

    if department == "Leadership" and seniority in ("Owner", "Principal"):
        return "executive"
    if department == "Leadership" and seniority == "Director":
        return "admin"
    if department in ("Operations", "Admin"):
        return "admin"
    if department == "Finance":
        return "finance"
    if is_pm == 1:
        return "pm"
    return "staff"


def get_user_roles(user: dict) -> set:
    """Get all applicable roles for a user."""
    roles = {"staff"}
    department = user.get("department", "")
    seniority = user.get("seniority", "")
    is_pm = user.get("is_pm", 0)

    if department == "Leadership" and seniority in ("Owner", "Principal"):
        roles.update({"executive", "admin", "finance", "pm"})
        return roles

    if department in ("Leadership", "Operations", "Admin") and seniority == "Director":
        roles.update({"admin", "finance", "pm"})

    if department in ("Operations", "Admin"):
        roles.add("admin")
    if department == "Finance":
        roles.add("finance")
    if is_pm == 1:
        roles.add("pm")

    return roles


def require_role(*allowed_roles: str):
    """
    Dependency factory to require specific roles for endpoint access.

    Usage:
        @router.get("/finance/data")
        async def finance_data(user = Depends(require_role("executive", "finance"))):
            return {"data": "sensitive"}
    """
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        user_roles = get_user_roles(user)
        if not user_roles.intersection(set(allowed_roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {' or '.join(allowed_roles)}"
            )
        user["_access_level"] = get_user_access_level(user)
        user["_roles"] = user_roles
        return user
    return role_checker


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Require admin role for endpoint access."""
    checker = require_role("admin", "executive")
    return await checker(user)


async def require_finance(user: dict = Depends(get_current_user)) -> dict:
    """Require finance role for endpoint access."""
    checker = require_role("finance", "executive")
    return await checker(user)


async def require_executive(user: dict = Depends(get_current_user)) -> dict:
    """Require executive role for endpoint access."""
    checker = require_role("executive")
    return await checker(user)
