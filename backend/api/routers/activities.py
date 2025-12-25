"""
API endpoints for proposal activities, milestones, and action items.
Issue #140: Activity Tracking Database

Provides:
- GET /activities/{proposal_id} - Get all activities for a proposal
- GET /activities/{proposal_id}/timeline - Get timeline view (activities + milestones)
- GET /activities/{proposal_id}/milestones - Get milestones only
- GET /activities/{proposal_id}/action-items - Get action items
- POST /activities/{proposal_id}/action-items - Create action item manually
- PATCH /action-items/{action_id} - Update action item (complete, assign, etc.)
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
import sqlite3
import os
import json

router = APIRouter(prefix="/api/activities", tags=["activities"])

DB_PATH = os.getenv("DATABASE_PATH", "database/bensley_master.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Pydantic models
class Activity(BaseModel):
    activity_id: int
    proposal_id: Optional[int]
    activity_type: str
    activity_date: str
    source_type: Optional[str]
    source_id: Optional[str]
    actor: Optional[str]
    actor_email: Optional[str]
    title: Optional[str]
    summary: Optional[str]
    sentiment: Optional[str]
    is_significant: bool = False


class Milestone(BaseModel):
    milestone_id: int
    proposal_id: int
    milestone_type: str
    milestone_date: str
    description: Optional[str]
    proposal_value_at_milestone: Optional[float]


class ActionItem(BaseModel):
    action_id: int
    proposal_id: Optional[int]
    action_text: str
    action_category: Optional[str]
    due_date: Optional[str]
    assigned_to: Optional[str]
    status: str
    priority: str
    created_at: str


class ActionItemCreate(BaseModel):
    action_text: str
    action_category: Optional[str] = "other"
    due_date: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: str = "normal"


class ActionItemUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    completion_notes: Optional[str] = None


class TimelineEvent(BaseModel):
    event_type: str  # 'activity' or 'milestone'
    date: str
    title: str
    description: Optional[str]
    actor: Optional[str]
    activity_type: Optional[str]
    milestone_type: Optional[str]
    is_significant: bool = False


@router.get("/{proposal_id}")
async def get_proposal_activities(
    proposal_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    activity_type: Optional[str] = None
):
    """Get all activities for a proposal."""
    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT * FROM proposal_activities
        WHERE proposal_id = ?
    """
    params = [proposal_id]

    if activity_type:
        query += " AND activity_type = ?"
        params.append(activity_type)

    query += " ORDER BY activity_date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    activities = [dict(row) for row in cursor.fetchall()]

    # Get total count
    count_query = "SELECT COUNT(*) FROM proposal_activities WHERE proposal_id = ?"
    cursor.execute(count_query, [proposal_id])
    total = cursor.fetchone()[0]

    conn.close()

    return {
        "activities": activities,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/{proposal_id}/timeline")
async def get_proposal_timeline(
    proposal_id: int,
    limit: int = Query(100, ge=1, le=500)
):
    """Get combined timeline of activities and milestones."""
    conn = get_db()
    cursor = conn.cursor()

    # Get activities
    cursor.execute("""
        SELECT
            'activity' as event_type,
            activity_date as date,
            COALESCE(title, activity_type) as title,
            summary as description,
            actor,
            activity_type,
            NULL as milestone_type,
            is_significant
        FROM proposal_activities
        WHERE proposal_id = ?
        ORDER BY activity_date DESC
        LIMIT ?
    """, [proposal_id, limit])
    activities = [dict(row) for row in cursor.fetchall()]

    # Get milestones
    cursor.execute("""
        SELECT
            'milestone' as event_type,
            milestone_date as date,
            milestone_type as title,
            description,
            created_by as actor,
            NULL as activity_type,
            milestone_type,
            1 as is_significant
        FROM proposal_milestones
        WHERE proposal_id = ?
        ORDER BY milestone_date DESC
    """, [proposal_id])
    milestones = [dict(row) for row in cursor.fetchall()]

    conn.close()

    # Combine and sort by date
    timeline = activities + milestones
    timeline.sort(key=lambda x: x['date'] or '', reverse=True)

    return {
        "timeline": timeline[:limit],
        "activity_count": len(activities),
        "milestone_count": len(milestones)
    }


@router.get("/{proposal_id}/milestones")
async def get_proposal_milestones(proposal_id: int):
    """Get milestones for a proposal."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM proposal_milestones
        WHERE proposal_id = ?
        ORDER BY milestone_date ASC
    """, [proposal_id])
    milestones = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {"milestones": milestones}


@router.get("/{proposal_id}/action-items")
async def get_proposal_action_items(
    proposal_id: int,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None
):
    """Get action items for a proposal."""
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM proposal_action_items WHERE proposal_id = ?"
    params = [proposal_id]

    if status:
        query += " AND status = ?"
        params.append(status)

    if assigned_to:
        query += " AND assigned_to = ?"
        params.append(assigned_to)

    query += " ORDER BY CASE WHEN status = 'pending' THEN 0 ELSE 1 END, due_date ASC"

    cursor.execute(query, params)
    action_items = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {"action_items": action_items}


@router.post("/{proposal_id}/action-items")
async def create_action_item(proposal_id: int, item: ActionItemCreate):
    """Create a new action item manually."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO proposal_action_items (
            proposal_id, action_text, action_category,
            due_date, assigned_to, priority, status,
            source_type, due_date_source
        ) VALUES (?, ?, ?, ?, ?, ?, 'pending', 'manual', 'manual')
    """, [
        proposal_id,
        item.action_text,
        item.action_category,
        item.due_date,
        item.assigned_to,
        item.priority
    ])

    action_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {"action_id": action_id, "message": "Action item created"}


@router.patch("/action-items/{action_id}")
async def update_action_item(action_id: int, update: ActionItemUpdate):
    """Update an action item (complete, reassign, etc.)."""
    conn = get_db()
    cursor = conn.cursor()

    # Build update query dynamically
    updates = []
    params = []

    if update.status:
        updates.append("status = ?")
        params.append(update.status)
        if update.status == 'completed':
            updates.append("completed_at = datetime('now')")

    if update.assigned_to:
        updates.append("assigned_to = ?")
        params.append(update.assigned_to)

    if update.due_date:
        updates.append("due_date = ?")
        params.append(update.due_date)

    if update.priority:
        updates.append("priority = ?")
        params.append(update.priority)

    if update.completion_notes:
        updates.append("completion_notes = ?")
        params.append(update.completion_notes)

    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    updates.append("updated_at = datetime('now')")
    params.append(action_id)

    cursor.execute(f"""
        UPDATE proposal_action_items
        SET {', '.join(updates)}
        WHERE action_id = ?
    """, params)

    conn.commit()
    conn.close()

    return {"message": "Action item updated"}


# Summary endpoints for dashboards
@router.get("/summary/pending-actions")
async def get_pending_actions(
    assigned_to: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100)
):
    """Get pending action items across all proposals."""
    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT
            ai.*,
            p.project_code,
            p.project_name
        FROM proposal_action_items ai
        JOIN proposals p ON ai.proposal_id = p.proposal_id
        WHERE ai.status = 'pending'
    """
    params = []

    if assigned_to:
        query += " AND ai.assigned_to = ?"
        params.append(assigned_to)

    query += " ORDER BY ai.due_date ASC NULLS LAST LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    items = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {"pending_actions": items}


@router.get("/summary/recent")
async def get_recent_activity(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(50, ge=1, le=200)
):
    """Get recent activity across all proposals."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            pa.*,
            p.project_code,
            p.project_name
        FROM proposal_activities pa
        JOIN proposals p ON pa.proposal_id = p.proposal_id
        WHERE pa.activity_date >= date('now', ?)
        ORDER BY pa.activity_date DESC
        LIMIT ?
    """, [f'-{days} days', limit])

    activities = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {"recent_activities": activities, "days": days}
