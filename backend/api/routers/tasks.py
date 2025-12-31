"""
Tasks Router - Task management from AI suggestions

Endpoints:
    GET /api/tasks - List tasks with filtering
    GET /api/tasks/stats - Get task statistics
    GET /api/tasks/overdue - Get overdue tasks
    GET /api/tasks/{id} - Get single task with source details
    PUT /api/tasks/{id} - Update task (status, priority, due_date)
    PUT /api/tasks/{id}/status - Update task status only
    POST /api/tasks/{id}/complete - Mark task as completed
    POST /api/tasks/{id}/snooze - Snooze task (update due_date)
    GET /api/projects/{code}/tasks - Get tasks for a project
"""

import sqlite3
from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from api.dependencies import DB_PATH
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api", tags=["tasks"])


# ============================================================================
# REQUEST MODELS
# ============================================================================

class CreateTaskRequest(BaseModel):
    """Request to create a new task"""
    title: str
    description: Optional[str] = None
    task_type: Optional[str] = "action_item"
    priority: Optional[str] = "medium"
    due_date: Optional[str] = None
    project_code: Optional[str] = None
    proposal_id: Optional[int] = None
    assignee: Optional[str] = "us"


class UpdateTaskRequest(BaseModel):
    """Request to update a task"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    assignee: Optional[str] = None
    task_type: Optional[str] = None


class UpdateTaskStatusRequest(BaseModel):
    """Request to update task status"""
    status: str


class SnoozeTaskRequest(BaseModel):
    """Request to snooze a task"""
    due_date: str


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


# ============================================================================
# LIST ENDPOINTS
# ============================================================================

@router.get("/tasks")
async def get_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    project_code: Optional[str] = Query(None, description="Filter by project code"),
    proposal_id: Optional[int] = Query(None, description="Filter by proposal ID"),
    due_before: Optional[str] = Query(None, description="Filter tasks due before date (YYYY-MM-DD)"),
    due_after: Optional[str] = Query(None, description="Filter tasks due after date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=500, description="Max tasks to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """Get all tasks with optional filtering"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Build query dynamically
        conditions = []
        params = []

        if status:
            conditions.append("status = ?")
            params.append(status)

        if priority:
            conditions.append("priority = ?")
            params.append(priority)

        if project_code:
            conditions.append("project_code = ?")
            params.append(project_code)

        if proposal_id:
            conditions.append("proposal_id = ?")
            params.append(proposal_id)

        if due_before:
            conditions.append("due_date < ?")
            params.append(due_before)

        if due_after:
            conditions.append("due_date > ?")
            params.append(due_after)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Get total count
        count_query = f"SELECT COUNT(*) FROM tasks WHERE {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        # Get tasks
        query = f"""
            SELECT * FROM tasks
            WHERE {where_clause}
            ORDER BY
                CASE WHEN status = 'completed' THEN 1 ELSE 0 END,
                CASE WHEN due_date IS NULL THEN 1 ELSE 0 END,
                due_date ASC,
                CASE priority
                    WHEN 'critical' THEN 0
                    WHEN 'high' THEN 1
                    WHEN 'medium' THEN 2
                    ELSE 3
                END
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        cursor.execute(query, params)
        tasks = [row_to_dict(row) for row in cursor.fetchall()]

        conn.close()

        # Build response with backward compat for frontend
        response = list_response(tasks, total)
        response["success"] = True
        response["tasks"] = tasks  # Backward compat for frontend
        response["count"] = len(tasks)  # Backward compat
        response["total"] = total
        response["returned"] = len(tasks)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/tasks/stats")
async def get_task_stats():
    """Get task statistics"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        today = get_today()

        # Get counts by status
        cursor.execute("SELECT COUNT(*) FROM tasks")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
        pending = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'in_progress'")
        in_progress = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'")
        completed = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'cancelled'")
        cancelled = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM tasks
            WHERE due_date < ? AND status NOT IN ('completed', 'cancelled')
        """, [today])
        overdue = cursor.fetchone()[0]

        # Get counts by priority (for non-completed tasks)
        cursor.execute("""
            SELECT priority, COUNT(*) as count
            FROM tasks
            WHERE status NOT IN ('completed', 'cancelled')
            GROUP BY priority
        """)
        priority_rows = cursor.fetchall()
        by_priority = {row['priority']: row['count'] for row in priority_rows}

        # Get counts by task type (for non-completed tasks)
        cursor.execute("""
            SELECT task_type, COUNT(*) as count
            FROM tasks
            WHERE status NOT IN ('completed', 'cancelled')
            GROUP BY task_type
        """)
        type_rows = cursor.fetchall()
        by_type = {row['task_type']: row['count'] for row in type_rows}

        conn.close()

        return {
            "success": True,
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "cancelled": cancelled,
            "overdue": overdue,
            "active": pending + in_progress,
            "by_priority": by_priority,
            "by_type": by_type
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/tasks/overdue")
async def get_overdue_tasks():
    """Get overdue tasks"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        today = get_today()

        cursor.execute("""
            SELECT * FROM tasks
            WHERE due_date < ? AND status NOT IN ('completed', 'cancelled')
            ORDER BY due_date ASC,
                CASE priority
                    WHEN 'critical' THEN 0
                    WHEN 'high' THEN 1
                    WHEN 'medium' THEN 2
                    ELSE 3
                END
        """, [today])

        tasks = [row_to_dict(row) for row in cursor.fetchall()]
        conn.close()

        response = list_response(tasks, len(tasks))
        response["success"] = True
        response["tasks"] = tasks
        response["count"] = len(tasks)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# CREATE TASK
# ============================================================================

@router.post("/tasks")
async def create_task(request: CreateTaskRequest):
    """Create a new task"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Get proposal_id from project_code if not provided
        proposal_id = request.proposal_id
        if not proposal_id and request.project_code:
            cursor.execute(
                "SELECT proposal_id FROM proposals WHERE project_code = ?",
                [request.project_code]
            )
            row = cursor.fetchone()
            if row:
                proposal_id = row[0]

        cursor.execute("""
            INSERT INTO tasks (
                title, description, task_type, priority, status,
                due_date, project_code, proposal_id, assignee, created_at
            ) VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?, datetime('now'))
        """, [
            request.title,
            request.description,
            request.task_type or 'action_item',
            request.priority or 'medium',
            request.due_date,
            request.project_code,
            proposal_id,
            request.assignee or 'us'
        ])

        task_id = cursor.lastrowid
        conn.commit()

        # Get the created task
        cursor.execute("SELECT * FROM tasks WHERE task_id = ?", [task_id])
        task = row_to_dict(cursor.fetchone())
        conn.close()

        return action_response(True, data={"task": task, "task_id": task_id}, message="Task created")

    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# STAFF ENDPOINT (for assignee dropdown)
# ============================================================================

@router.get("/staff")
async def get_staff():
    """Get list of active staff members for task assignment"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                staff_id,
                first_name,
                last_name,
                nickname,
                email,
                department,
                role
            FROM staff
            WHERE is_active = 1
            ORDER BY first_name, last_name
        """)

        staff = [row_to_dict(row) for row in cursor.fetchall()]
        conn.close()

        # Add special entries
        assignees = [
            {"id": "us", "name": "Us (Bensley)", "type": "team"},
            {"id": "them", "name": "Client/Them", "type": "external"},
        ]

        for s in staff:
            name = s.get('nickname') or s.get('first_name') or 'Unknown'
            assignees.append({
                "id": str(s['staff_id']),
                "name": name,
                "full_name": f"{s.get('first_name', '')} {s.get('last_name', '')}".strip(),
                "email": s.get('email'),
                "department": s.get('department'),
                "role": s.get('role'),
                "type": "staff"
            })

        return {
            "success": True,
            "assignees": assignees,
            "count": len(assignees)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# SINGLE TASK ENDPOINTS
# ============================================================================

@router.get("/tasks/{task_id}")
async def get_task(task_id: int):
    """Get a single task with source suggestion/email details"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Get task
        cursor.execute("SELECT * FROM tasks WHERE task_id = ?", [task_id])
        task = row_to_dict(cursor.fetchone())

        if not task:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Get source suggestion if exists
        if task.get('source_suggestion_id'):
            cursor.execute("""
                SELECT suggestion_id, suggestion_type, summary, status, confidence, created_at
                FROM ai_suggestions
                WHERE suggestion_id = ?
            """, [task['source_suggestion_id']])
            suggestion = row_to_dict(cursor.fetchone())
            task['source_suggestion'] = suggestion

        # Get source email if exists
        if task.get('source_email_id'):
            cursor.execute("""
                SELECT email_id, subject, sender_email, received_date
                FROM emails
                WHERE email_id = ?
            """, [task['source_email_id']])
            email = row_to_dict(cursor.fetchone())
            task['source_email'] = email

        # Get proposal if linked
        if task.get('proposal_id'):
            cursor.execute("""
                SELECT proposal_id, client_name, project_name, status
                FROM proposals
                WHERE proposal_id = ?
            """, [task['proposal_id']])
            proposal = row_to_dict(cursor.fetchone())
            task['proposal'] = proposal

        conn.close()

        response = item_response(task)
        response["success"] = True
        response["task"] = task

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.put("/tasks/{task_id}")
async def update_task(task_id: int, request: UpdateTaskRequest):
    """Update a task (all fields)"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Check task exists
        cursor.execute("SELECT * FROM tasks WHERE task_id = ?", [task_id])
        task = row_to_dict(cursor.fetchone())
        if not task:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Build update
        updates = []
        params = []
        completing = False

        if request.title is not None:
            updates.append("title = ?")
            params.append(request.title)

        if request.description is not None:
            updates.append("description = ?")
            params.append(request.description)

        if request.status is not None:
            if request.status not in ('pending', 'in_progress', 'completed', 'cancelled'):
                raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")
            updates.append("status = ?")
            params.append(request.status)
            # Set completed_at if completing
            if request.status == 'completed':
                updates.append("completed_at = ?")
                params.append(datetime.utcnow().isoformat())
                completing = True
            elif task.get('status') == 'completed':
                # Uncompleting - clear completed_at
                updates.append("completed_at = NULL")

        if request.priority is not None:
            if request.priority not in ('low', 'medium', 'high', 'critical'):
                raise HTTPException(status_code=400, detail=f"Invalid priority: {request.priority}")
            updates.append("priority = ?")
            params.append(request.priority)

        if request.due_date is not None:
            updates.append("due_date = ?")
            params.append(request.due_date if request.due_date else None)

        if request.assignee is not None:
            updates.append("assignee = ?")
            params.append(request.assignee)

        if request.task_type is not None:
            updates.append("task_type = ?")
            params.append(request.task_type)

        if not updates:
            conn.close()
            raise HTTPException(status_code=400, detail="No updates provided")

        # Execute update
        params.append(task_id)
        cursor.execute(f"""
            UPDATE tasks SET {', '.join(updates)} WHERE task_id = ?
        """, params)

        # Update ball_in_court if completing a task linked to a proposal
        ball_updated = False
        if completing:
            proposal_id = task.get('proposal_id')
            project_code = task.get('project_code')

            if proposal_id:
                cursor.execute("""
                    SELECT COUNT(*) FROM tasks
                    WHERE proposal_id = ?
                    AND status NOT IN ('completed', 'cancelled')
                    AND COALESCE(assignee, 'us') = 'us'
                """, [proposal_id])
                remaining = cursor.fetchone()[0]
                if remaining == 0:
                    cursor.execute("""
                        UPDATE proposals
                        SET ball_in_court = 'them',
                            waiting_for = 'Completed all action items - awaiting client response'
                        WHERE proposal_id = ?
                    """, [proposal_id])
                    ball_updated = True
            elif project_code:
                cursor.execute("SELECT proposal_id FROM proposals WHERE project_code = ?", [project_code])
                row = cursor.fetchone()
                if row:
                    prop_id = row[0]
                    cursor.execute("""
                        SELECT COUNT(*) FROM tasks
                        WHERE (proposal_id = ? OR project_code = ?)
                        AND status NOT IN ('completed', 'cancelled')
                        AND COALESCE(assignee, 'us') = 'us'
                    """, [prop_id, project_code])
                    remaining = cursor.fetchone()[0]
                    if remaining == 0:
                        cursor.execute("""
                            UPDATE proposals
                            SET ball_in_court = 'them',
                                waiting_for = 'Completed all action items - awaiting client response'
                            WHERE proposal_id = ?
                        """, [prop_id])
                        ball_updated = True

        conn.commit()

        # Get updated task
        cursor.execute("SELECT * FROM tasks WHERE task_id = ?", [task_id])
        updated_task = row_to_dict(cursor.fetchone())
        conn.close()

        return action_response(True, data={"task": updated_task, "ball_updated": ball_updated}, message="Task updated")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.put("/tasks/{task_id}/status")
async def update_task_status(task_id: int, request: UpdateTaskStatusRequest):
    """Update task status only (for frontend compat)"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Check task exists
        cursor.execute("SELECT * FROM tasks WHERE task_id = ?", [task_id])
        task = cursor.fetchone()
        if not task:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Validate status
        if request.status not in ('pending', 'in_progress', 'completed', 'cancelled'):
            raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")

        # Update
        if request.status == 'completed':
            cursor.execute("""
                UPDATE tasks SET status = ?, completed_at = ? WHERE task_id = ?
            """, [request.status, datetime.utcnow().isoformat(), task_id])
        else:
            cursor.execute("""
                UPDATE tasks SET status = ?, completed_at = NULL WHERE task_id = ?
            """, [request.status, task_id])

        conn.commit()
        conn.close()

        return {"success": True, "message": f"Task {task_id} status updated to {request.status}"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("/tasks/{task_id}/complete")
async def complete_task(task_id: int):
    """Mark a task as completed and update ball_in_court if linked to proposal"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Check task exists and get proposal_id
        cursor.execute("SELECT * FROM tasks WHERE task_id = ?", [task_id])
        task = row_to_dict(cursor.fetchone())
        if not task:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Update task to completed
        cursor.execute("""
            UPDATE tasks SET status = 'completed', completed_at = ? WHERE task_id = ?
        """, [datetime.utcnow().isoformat(), task_id])

        ball_updated = False
        proposal_id = task.get('proposal_id')
        project_code = task.get('project_code')

        # Update ball_in_court if task linked to a proposal
        if proposal_id:
            # Count remaining open tasks assigned to "us" for this proposal
            cursor.execute("""
                SELECT COUNT(*) FROM tasks
                WHERE proposal_id = ?
                AND status NOT IN ('completed', 'cancelled')
                AND COALESCE(assignee, 'us') = 'us'
            """, [proposal_id])
            remaining_our_tasks = cursor.fetchone()[0]

            if remaining_our_tasks == 0:
                # All our tasks done - ball goes to them
                cursor.execute("""
                    UPDATE proposals
                    SET ball_in_court = 'them',
                        waiting_for = 'Completed all action items - awaiting client response'
                    WHERE proposal_id = ?
                """, [proposal_id])
                ball_updated = True
        elif project_code:
            # Check by project_code if no proposal_id
            # Get proposal_id from project_code
            cursor.execute("""
                SELECT proposal_id FROM proposals WHERE project_code = ?
            """, [project_code])
            proposal_row = cursor.fetchone()
            if proposal_row:
                prop_id = proposal_row[0]
                cursor.execute("""
                    SELECT COUNT(*) FROM tasks
                    WHERE (proposal_id = ? OR project_code = ?)
                    AND status NOT IN ('completed', 'cancelled')
                    AND COALESCE(assignee, 'us') = 'us'
                """, [prop_id, project_code])
                remaining_our_tasks = cursor.fetchone()[0]

                if remaining_our_tasks == 0:
                    cursor.execute("""
                        UPDATE proposals
                        SET ball_in_court = 'them',
                            waiting_for = 'Completed all action items - awaiting client response'
                        WHERE proposal_id = ?
                    """, [prop_id])
                    ball_updated = True

        conn.commit()
        conn.close()

        message = f"Task {task_id} marked as completed"
        if ball_updated:
            message += " - ball moved to client (all action items done)"

        return action_response(True, message=message, data={"ball_updated": ball_updated})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("/tasks/{task_id}/snooze")
async def snooze_task(task_id: int, request: SnoozeTaskRequest):
    """Snooze a task by updating its due date"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Check task exists
        cursor.execute("SELECT * FROM tasks WHERE task_id = ?", [task_id])
        task = cursor.fetchone()
        if not task:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Update due_date
        cursor.execute("""
            UPDATE tasks SET due_date = ? WHERE task_id = ?
        """, [request.due_date, task_id])
        conn.commit()
        conn.close()

        return {"success": True, "message": f"Task {task_id} snoozed to {request.due_date}"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# PROJECT TASKS
# ============================================================================

@router.get("/projects/{project_code}/tasks")
async def get_project_tasks(
    project_code: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    include_completed: bool = Query(False, description="Include completed tasks")
):
    """Get all tasks for a specific project"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Build query
        conditions = ["project_code = ?"]
        params = [project_code]

        if status:
            conditions.append("status = ?")
            params.append(status)
        elif not include_completed:
            conditions.append("status NOT IN ('completed', 'cancelled')")

        where_clause = " AND ".join(conditions)

        cursor.execute(f"""
            SELECT * FROM tasks
            WHERE {where_clause}
            ORDER BY
                CASE WHEN due_date IS NULL THEN 1 ELSE 0 END,
                due_date ASC,
                CASE priority
                    WHEN 'critical' THEN 0
                    WHEN 'high' THEN 1
                    WHEN 'medium' THEN 2
                    ELSE 3
                END
        """, params)

        tasks = [row_to_dict(row) for row in cursor.fetchall()]
        conn.close()

        response = list_response(tasks, len(tasks))
        response["success"] = True
        response["project_code"] = project_code
        response["tasks"] = tasks
        response["count"] = len(tasks)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")
