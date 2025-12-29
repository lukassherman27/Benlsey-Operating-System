"""
Authentication Router - Login, logout, user info endpoints.

Endpoints:
    POST /api/auth/login - Authenticate user, return JWT
    GET /api/auth/me - Get current user info (requires auth)
    POST /api/auth/change-password - Change user password (requires auth)
"""

from datetime import datetime
from typing import Optional
import sqlite3

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from api.dependencies import get_db, get_current_user, DB_PATH
from api.security import verify_password, get_password_hash, create_access_token, Token

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """Login request body."""
    email: str
    password: str


class LoginResponse(BaseModel):
    """Login response with token and user info."""
    access_token: str
    token_type: str = "bearer"
    expires_at: str
    user: dict


class UserResponse(BaseModel):
    """Current user info response."""
    staff_id: int
    email: str
    first_name: str
    last_name: Optional[str]
    role: Optional[str]
    department: Optional[str]
    office: Optional[str]
    seniority: Optional[str]


class ChangePasswordRequest(BaseModel):
    """Change password request body."""
    current_password: str
    new_password: str


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user with email and password.

    Returns JWT token if credentials are valid.
    """
    # Create thread-local connection
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT staff_id, email, first_name, last_name, password_hash,
                   role, department, office, seniority, is_pm, is_active
            FROM staff
            WHERE LOWER(email) = LOWER(?) AND is_active = 1
        """, (request.email,))

        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not user["password_hash"]:
            raise HTTPException(
                status_code=401,
                detail="Password not set. Contact admin for initial password."
            )

        if not verify_password(request.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Update last login
        cursor.execute(
            "UPDATE staff SET last_login = ? WHERE staff_id = ?",
            (datetime.now().isoformat(), user["staff_id"])
        )
        conn.commit()

        # Create token
        name = f"{user['first_name']} {user['last_name'] or ''}".strip()
        token, expires = create_access_token({
            "email": user["email"],
            "staff_id": user["staff_id"],
            "name": name,
            "role": user["role"],
        })

        return LoginResponse(
            access_token=token,
            expires_at=expires.isoformat(),
            user={
                "staff_id": user["staff_id"],
                "email": user["email"],
                "name": name,
                "role": user["role"],
                "department": user["department"],
                "office": user["office"],
                "seniority": user["seniority"],
                "is_pm": bool(user["is_pm"]),
            }
        )
    finally:
        conn.close()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    """
    Get current authenticated user info.

    Requires valid JWT token in Authorization header.
    """
    return UserResponse(
        staff_id=current_user["staff_id"],
        email=current_user["email"],
        first_name=current_user["first_name"],
        last_name=current_user.get("last_name"),
        role=current_user.get("role"),
        department=current_user.get("department"),
        office=current_user.get("office"),
        seniority=current_user.get("seniority"),
    )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """
    Change the current user's password.

    Requires valid JWT token and current password.
    """
    # Verify current password
    if not verify_password(request.current_password, current_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # Validate new password
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    # Update password
    new_hash = get_password_hash(request.new_password)
    cursor = db.cursor()
    cursor.execute(
        "UPDATE staff SET password_hash = ?, updated_at = ? WHERE staff_id = ?",
        (new_hash, datetime.now().isoformat(), current_user["staff_id"])
    )
    db.commit()

    return {"success": True, "message": "Password updated successfully"}
