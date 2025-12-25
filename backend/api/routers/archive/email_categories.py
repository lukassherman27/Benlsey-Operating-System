"""
Email Categories Router - Expose EmailCategoryService as API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sqlite3

from api.dependencies import DB_PATH
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api/email-categories", tags=["email-categories"])


@router.get("")
async def get_categories():
    """Get all email categories"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT c.*,
                   COUNT(DISTINCT r.rule_id) as rule_count,
                   COUNT(DISTINCT e.email_id) as email_count
            FROM email_categories c
            LEFT JOIN email_category_rules r ON c.category_id = r.category_id
            LEFT JOIN email_content e ON e.category = c.name
            GROUP BY c.category_id
            ORDER BY c.name
        """)

        categories = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return list_response(categories, total=len(categories))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_category_stats():
    """Get category statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get counts by category
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM email_content
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
        """)
        by_category = {row['category']: row['count'] for row in cursor.fetchall()}

        # Get uncategorized count
        cursor.execute("SELECT COUNT(*) FROM uncategorized_emails WHERE reviewed = 0")
        uncategorized = cursor.fetchone()[0]

        # Get total rules
        cursor.execute("SELECT COUNT(*) FROM email_category_rules")
        total_rules = cursor.fetchone()[0]

        conn.close()

        return {
            "success": True,
            "by_category": by_category,
            "uncategorized_pending": uncategorized,
            "total_rules": total_rules,
            "total_categories": len(by_category)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/uncategorized")
async def get_uncategorized(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Get uncategorized emails for review"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.*, e.subject, e.sender_email, e.date
            FROM uncategorized_emails u
            JOIN emails e ON u.email_id = e.email_id
            WHERE u.reviewed = 0
            ORDER BY u.created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        emails = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT COUNT(*) FROM uncategorized_emails WHERE reviewed = 0")
        total = cursor.fetchone()[0]

        conn.close()

        return list_response(emails, total=total)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{category_id}/assign/{email_id}")
async def assign_category(category_id: int, email_id: int):
    """Assign a category to an email"""
    try:
        from backend.services.email_category_service import EmailCategoryService
        svc = EmailCategoryService()

        # Get category name
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM email_categories WHERE category_id = ?", (category_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Category not found")

        category_name = row[0]

        # Update email
        cursor.execute("""
            UPDATE email_content SET category = ? WHERE email_id = ?
        """, (category_name, email_id))

        # Mark as reviewed in uncategorized
        cursor.execute("""
            UPDATE uncategorized_emails
            SET reviewed = 1, reviewed_at = datetime('now')
            WHERE email_id = ?
        """, (email_id,))

        conn.commit()
        conn.close()

        return action_response(True, message=f"Email assigned to {category_name}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules")
async def get_rules(category_id: Optional[int] = None):
    """Get categorization rules"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if category_id:
            cursor.execute("""
                SELECT r.*, c.name as category_name
                FROM email_category_rules r
                JOIN email_categories c ON r.category_id = c.category_id
                WHERE r.category_id = ?
                ORDER BY r.confidence DESC
            """, (category_id,))
        else:
            cursor.execute("""
                SELECT r.*, c.name as category_name
                FROM email_category_rules r
                JOIN email_categories c ON r.category_id = c.category_id
                ORDER BY c.name, r.confidence DESC
            """)

        rules = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return list_response(rules, total=len(rules))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
