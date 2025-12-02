"""
Health Router - System health and status endpoints

Endpoints:
    GET /health - Health check
    GET /api/health - Health check (API prefixed)
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from api.dependencies import get_db_connection

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get proposal count
        cursor.execute("SELECT COUNT(*) FROM projects")
        proposal_count = cursor.fetchone()[0]

        # Get email count
        cursor.execute("SELECT COUNT(*) FROM emails")
        email_count = cursor.fetchone()[0]

        conn.close()

        return {
            "status": "healthy",
            "database": "connected",
            "proposals_in_db": proposal_count,
            "emails_in_db": email_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
