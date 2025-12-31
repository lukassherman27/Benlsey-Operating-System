"""
My Day Router - Personal daily workflow dashboard for Bill and Brian

Endpoints:
    GET /api/my-day - Get personalized daily overview
    GET /api/my-day/{user_id} - Get daily overview for specific user
"""

import sqlite3
from datetime import datetime, date, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from api.dependencies import DB_PATH
from api.helpers import action_response

router = APIRouter(prefix="/api", tags=["my-day"])


# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row) -> dict:
    """Convert sqlite Row to dict"""
    if row is None:
        return None
    return dict(row)


def get_today() -> str:
    """Get today's date as YYYY-MM-DD string"""
    return date.today().isoformat()


def get_greeting(hour: int) -> str:
    """Get time-appropriate greeting"""
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


# ============================================================================
# MY DAY ENDPOINT
# ============================================================================

@router.get("/my-day")
async def get_my_day(
    user_id: Optional[str] = Query("bill", description="User ID (default: bill)"),
    user_name: Optional[str] = Query(None, description="User display name")
):
    """
    Get personalized daily overview for a user.

    Returns everything needed for the "My Day" dashboard:
    - Greeting with date info
    - Today's tasks and overdue items
    - Today's meetings
    - Proposals needing follow-up
    - AI suggestions to review
    - Week ahead preview
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        today = get_today()
        now = datetime.now()

        # Determine display name
        display_name = user_name or user_id.capitalize()

        # ============================================================
        # 1. GREETING
        # ============================================================
        greeting = {
            "text": get_greeting(now.hour),
            "name": display_name,
            "date": today,
            "day_of_week": now.strftime("%A"),
            "formatted_date": now.strftime("%B %d, %Y"),
        }

        # ============================================================
        # 2. TODAY'S TASKS
        # ============================================================

        # Get tasks due today (assignee='us' or Bill)
        cursor.execute("""
            SELECT * FROM tasks
            WHERE status NOT IN ('completed', 'cancelled')
            AND due_date = ?
            AND (COALESCE(assignee, 'us') = 'us' OR assignee = ?)
            ORDER BY
                CASE priority
                    WHEN 'critical' THEN 0
                    WHEN 'high' THEN 1
                    WHEN 'medium' THEN 2
                    ELSE 3
                END
            LIMIT 20
        """, [today, user_id])
        tasks_today = [row_to_dict(row) for row in cursor.fetchall()]

        # Get overdue tasks
        cursor.execute("""
            SELECT * FROM tasks
            WHERE status NOT IN ('completed', 'cancelled')
            AND due_date < ?
            AND (COALESCE(assignee, 'us') = 'us' OR assignee = ?)
            ORDER BY due_date ASC,
                CASE priority
                    WHEN 'critical' THEN 0
                    WHEN 'high' THEN 1
                    WHEN 'medium' THEN 2
                    ELSE 3
                END
            LIMIT 10
        """, [today, user_id])
        tasks_overdue = [row_to_dict(row) for row in cursor.fetchall()]

        # Total active tasks count
        cursor.execute("""
            SELECT COUNT(*) FROM tasks
            WHERE status NOT IN ('completed', 'cancelled')
            AND (COALESCE(assignee, 'us') = 'us' OR assignee = ?)
        """, [user_id])
        total_active_tasks = cursor.fetchone()[0]

        tasks = {
            "today": tasks_today,
            "overdue": tasks_overdue,
            "today_count": len(tasks_today),
            "overdue_count": len(tasks_overdue),
            "total_active": total_active_tasks,
        }

        # ============================================================
        # 3. TODAY'S MEETINGS
        # ============================================================

        cursor.execute("""
            SELECT * FROM meetings
            WHERE meeting_date = ?
            AND status NOT IN ('cancelled')
            ORDER BY start_time ASC
        """, [today])
        meetings_today = [row_to_dict(row) for row in cursor.fetchall()]

        # Check if any meetings have video links
        has_virtual = any(
            m.get('location') and
            ('zoom' in m['location'].lower() or 'teams' in m['location'].lower() or 'meet' in m['location'].lower())
            for m in meetings_today
        )

        meetings = {
            "today": meetings_today,
            "count": len(meetings_today),
            "has_virtual": has_virtual,
        }

        # ============================================================
        # 4. PROPOSALS NEEDING FOLLOW-UP
        # ============================================================

        # Get proposals where ball_in_court='us' (we need to act)
        cursor.execute("""
            SELECT
                p.proposal_id, p.project_code, p.project_name, p.client_company as client_name,
                p.status, p.ball_in_court, p.waiting_for, p.last_contact_date,
                p.next_action_date as next_followup_date, p.win_probability as probability,
                CASE
                    WHEN p.next_action_date < ? THEN 'overdue'
                    WHEN p.next_action_date = ? THEN 'today'
                    ELSE 'upcoming'
                END as urgency,
                (julianday(?) - julianday(p.last_contact_date)) as days_since_contact
            FROM proposals p
            WHERE p.ball_in_court = 'us'
            AND p.status NOT IN ('won', 'lost', 'cancelled', 'on_hold', 'inactive')
            ORDER BY
                CASE WHEN p.next_action_date IS NULL THEN 1 ELSE 0 END,
                p.next_action_date ASC
            LIMIT 10
        """, [today, today, today])
        proposals_needing_action = [row_to_dict(row) for row in cursor.fetchall()]

        # Get count of all "our ball" proposals
        cursor.execute("""
            SELECT COUNT(*) FROM proposals
            WHERE ball_in_court = 'us'
            AND status NOT IN ('won', 'lost', 'cancelled', 'on_hold', 'inactive')
        """)
        total_our_ball = cursor.fetchone()[0]

        proposals = {
            "needing_followup": proposals_needing_action,
            "count": len(proposals_needing_action),
            "total_our_ball": total_our_ball,
        }

        # ============================================================
        # 5. AI SUGGESTIONS QUEUE
        # ============================================================

        # Get top pending suggestions by priority
        cursor.execute("""
            SELECT
                suggestion_id, suggestion_type, title, description,
                priority, confidence_score, project_code, created_at
            FROM ai_suggestions
            WHERE status = 'pending'
            ORDER BY
                CASE priority
                    WHEN 'high' THEN 0
                    WHEN 'medium' THEN 1
                    ELSE 2
                END,
                confidence_score DESC,
                created_at DESC
            LIMIT 5
        """)
        top_suggestions = [row_to_dict(row) for row in cursor.fetchall()]

        # Total pending count
        cursor.execute("SELECT COUNT(*) FROM ai_suggestions WHERE status = 'pending'")
        total_pending = cursor.fetchone()[0]

        # Count by type
        cursor.execute("""
            SELECT suggestion_type, COUNT(*) as count
            FROM ai_suggestions
            WHERE status = 'pending'
            GROUP BY suggestion_type
        """)
        suggestions_by_type = {row['suggestion_type']: row['count'] for row in cursor.fetchall()}

        suggestions_queue = {
            "top_suggestions": top_suggestions,
            "total_pending": total_pending,
            "by_type": suggestions_by_type,
        }

        # ============================================================
        # 6. WEEK AHEAD PREVIEW
        # ============================================================

        week_end = (date.today() + timedelta(days=7)).isoformat()

        # Upcoming deadlines this week
        cursor.execute("""
            SELECT * FROM tasks
            WHERE status NOT IN ('completed', 'cancelled')
            AND due_date > ? AND due_date <= ?
            ORDER BY due_date ASC
            LIMIT 10
        """, [today, week_end])
        upcoming_deadlines = [row_to_dict(row) for row in cursor.fetchall()]

        # Meetings this week
        cursor.execute("""
            SELECT COUNT(*) FROM meetings
            WHERE meeting_date > ? AND meeting_date <= ?
            AND status NOT IN ('cancelled')
        """, [today, week_end])
        meetings_this_week = cursor.fetchone()[0]

        # Proposal action dates this week (next_action_date)
        cursor.execute("""
            SELECT project_code, project_name, client_company as client_name, next_action_date as decision_date
            FROM proposals
            WHERE next_action_date > ? AND next_action_date <= ?
            AND status NOT IN ('won', 'lost', 'cancelled', 'on_hold', 'inactive')
        """, [today, week_end])
        decision_dates = [row_to_dict(row) for row in cursor.fetchall()]

        # Deliverables due this week
        cursor.execute("""
            SELECT deliverable_id, name, project_code, due_date, status
            FROM deliverables
            WHERE status NOT IN ('approved', 'cancelled')
            AND due_date > ? AND due_date <= ?
            ORDER BY due_date ASC
            LIMIT 5
        """, [today, week_end])
        deliverables_due = [row_to_dict(row) for row in cursor.fetchall()]

        week_ahead = {
            "upcoming_deadlines": upcoming_deadlines,
            "meetings_this_week": meetings_this_week,
            "decision_dates": decision_dates,
            "deliverables_due": deliverables_due,
        }

        # ============================================================
        # 7. COMMITMENTS (NEW)
        # ============================================================

        # Our overdue commitments
        cursor.execute("""
            SELECT * FROM commitments
            WHERE commitment_type = 'our_commitment'
            AND fulfillment_status = 'pending'
            AND due_date < ?
            ORDER BY due_date ASC
            LIMIT 5
        """, [today])
        our_overdue = [row_to_dict(row) for row in cursor.fetchall()]

        # Their overdue commitments (for follow-up)
        cursor.execute("""
            SELECT * FROM commitments
            WHERE commitment_type = 'their_commitment'
            AND fulfillment_status = 'pending'
            AND due_date < ?
            ORDER BY due_date ASC
            LIMIT 5
        """, [today])
        their_overdue = [row_to_dict(row) for row in cursor.fetchall()]

        commitments = {
            "our_overdue": our_overdue,
            "their_overdue": their_overdue,
            "our_overdue_count": len(our_overdue),
            "their_overdue_count": len(their_overdue),
        }

        conn.close()

        # ============================================================
        # BUILD RESPONSE
        # ============================================================

        return {
            "success": True,
            "greeting": greeting,
            "tasks": tasks,
            "meetings": meetings,
            "proposals": proposals,
            "suggestions_queue": suggestions_queue,
            "week_ahead": week_ahead,
            "commitments": commitments,
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/my-day/{user_id}")
async def get_my_day_for_user(user_id: str):
    """Get My Day data for a specific user"""
    return await get_my_day(user_id=user_id)
