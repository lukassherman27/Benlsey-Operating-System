"""
Team Router - Staff and PM workload management

Endpoints:
    GET /api/team/staff - List all staff members
    GET /api/team/pms - List all Project Managers
    GET /api/team/pm-workload - PM workload summary (projects, tasks, overdue)
    GET /api/projects/by-pm/{pm_id} - Projects for specific PM
    PUT /api/projects/{project_code}/assign-pm - Assign PM to project
"""

import sqlite3
from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from api.dependencies import DB_PATH
from api.helpers import list_response, item_response, action_response


router = APIRouter(prefix="/api", tags=["team"])


# ============================================================================
# REQUEST MODELS
# ============================================================================

class AssignPMRequest(BaseModel):
    """Request to assign PM to project"""
    pm_staff_id: int


class CreatePMRequest(BaseModel):
    """Request to create/mark a staff member as PM"""
    first_name: str
    last_name: Optional[str] = None
    nickname: Optional[str] = None
    email: Optional[str] = None
    office: str = "Bangkok"


# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_today() -> str:
    """Get today's date as YYYY-MM-DD string"""
    return date.today().isoformat()


# ============================================================================
# STAFF ENDPOINTS
# ============================================================================

@router.get("/team/staff")
async def get_staff(
    department: Optional[str] = None,
    office: Optional[str] = None,
    is_active: Optional[bool] = True,
    limit: int = Query(100, ge=1, le=500)
):
    """Get all staff members with optional filtering"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        conditions = []
        params = []

        if is_active is not None:
            conditions.append("is_active = ?")
            params.append(1 if is_active else 0)

        if department:
            conditions.append("department = ?")
            params.append(department)

        if office:
            conditions.append("office = ?")
            params.append(office)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        cursor.execute(f"""
            SELECT
                staff_id,
                first_name,
                last_name,
                nickname,
                email,
                office,
                department,
                role,
                seniority,
                is_pm,
                is_active
            FROM staff
            WHERE {where_clause}
            ORDER BY
                CASE WHEN is_pm = 1 THEN 0 ELSE 1 END,
                department,
                first_name
            LIMIT ?
        """, params + [limit])

        staff = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return list_response(staff, len(staff))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PM ENDPOINTS
# ============================================================================

@router.get("/team/pms")
async def get_pms():
    """Get all Project Managers"""
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
                office,
                department,
                role,
                seniority
            FROM staff
            WHERE is_pm = 1 AND is_active = 1
            ORDER BY first_name
        """)

        pms = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return list_response(pms, len(pms))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/team/pms")
async def create_pm(request: CreatePMRequest):
    """Create a new staff member marked as PM"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO staff (
                first_name, last_name, nickname, email, office,
                department, role, is_pm, is_active
            ) VALUES (?, ?, ?, ?, ?, 'Operations', 'Management', 1, 1)
        """, (
            request.first_name,
            request.last_name,
            request.nickname or request.first_name,
            request.email,
            request.office
        ))

        staff_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return action_response(
            True,
            data={"staff_id": staff_id},
            message=f"PM {request.first_name} created"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team/pm-workload")
async def get_pm_workload():
    """
    Get PM workload summary showing projects per PM, open tasks, and overdue items.

    Returns:
        List of PMs with their workload metrics:
        - pm_id, pm_name: PM identification
        - project_count: Number of active projects assigned
        - open_task_count: Number of open tasks across their projects
        - overdue_count: Number of overdue tasks
        - projects: List of project summaries
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        today = get_today()

        # Get all PMs
        cursor.execute("""
            SELECT
                staff_id,
                first_name,
                COALESCE(nickname, first_name) as display_name,
                email,
                office
            FROM staff
            WHERE is_pm = 1 AND is_active = 1
            ORDER BY first_name
        """)
        pms = [dict(row) for row in cursor.fetchall()]

        # For each PM, get their workload
        pm_workloads = []
        for pm in pms:
            pm_id = pm['staff_id']

            # Get projects assigned to this PM
            cursor.execute("""
                SELECT
                    p.project_id,
                    p.project_code,
                    p.project_title,
                    p.status,
                    p.health_score,
                    COALESCE(pr.client_company, p.project_title) as client_name
                FROM projects p
                LEFT JOIN proposals pr ON p.project_code = pr.project_code
                WHERE p.pm_staff_id = ?
                  AND (p.is_active_project = 1 OR p.status IN ('Active', 'active'))
                ORDER BY p.project_code DESC
            """, (pm_id,))
            projects = [dict(row) for row in cursor.fetchall()]
            project_count = len(projects)

            # Get project codes for task queries
            project_codes = [p['project_code'] for p in projects]

            open_task_count = 0
            overdue_count = 0

            if project_codes:
                placeholders = ','.join(['?' for _ in project_codes])

                # Count open tasks for PM's projects
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM tasks
                    WHERE project_code IN ({placeholders})
                      AND status IN ('pending', 'in_progress')
                """, project_codes)
                open_task_count = cursor.fetchone()[0]

                # Count overdue tasks
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM tasks
                    WHERE project_code IN ({placeholders})
                      AND status IN ('pending', 'in_progress')
                      AND due_date < ?
                      AND due_date IS NOT NULL
                """, project_codes + [today])
                overdue_count = cursor.fetchone()[0]

            pm_workloads.append({
                "pm_id": pm_id,
                "pm_name": pm['display_name'],
                "pm_email": pm.get('email'),
                "office": pm.get('office'),
                "project_count": project_count,
                "open_task_count": open_task_count,
                "overdue_count": overdue_count,
                "health_status": "at_risk" if overdue_count > 3 else ("warning" if overdue_count > 0 else "on_track"),
                "projects": projects
            })

        conn.close()

        # Calculate totals
        total_projects = sum(pm['project_count'] for pm in pm_workloads)
        total_open_tasks = sum(pm['open_task_count'] for pm in pm_workloads)
        total_overdue = sum(pm['overdue_count'] for pm in pm_workloads)

        return {
            "success": True,
            "data": pm_workloads,
            "summary": {
                "total_pms": len(pm_workloads),
                "total_projects_assigned": total_projects,
                "total_open_tasks": total_open_tasks,
                "total_overdue": total_overdue,
                "unassigned_projects": 0  # Will be calculated below
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team/unassigned-projects")
async def get_unassigned_projects():
    """Get active projects without a PM assigned"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                p.project_id,
                p.project_code,
                p.project_title,
                p.status,
                p.health_score,
                COALESCE(pr.client_company, p.project_title) as client_name,
                p.contract_signed_date
            FROM projects p
            LEFT JOIN proposals pr ON p.project_code = pr.project_code
            WHERE (p.is_active_project = 1 OR p.status IN ('Active', 'active'))
              AND (p.pm_staff_id IS NULL OR p.pm_staff_id = 0)
            ORDER BY p.project_code DESC
        """)

        projects = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return list_response(projects, len(projects))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROJECT-PM ASSIGNMENT
# ============================================================================

@router.get("/projects/by-pm/{pm_id}")
async def get_projects_by_pm(pm_id: int):
    """
    Get all projects assigned to a specific PM.

    Returns project details with task counts and health indicators.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        today = get_today()

        # Verify PM exists
        cursor.execute("""
            SELECT staff_id, first_name, COALESCE(nickname, first_name) as display_name
            FROM staff WHERE staff_id = ?
        """, (pm_id,))
        pm = cursor.fetchone()
        if not pm:
            raise HTTPException(status_code=404, detail=f"PM with id {pm_id} not found")
        pm_dict = dict(pm)

        # Get all projects for this PM
        cursor.execute("""
            SELECT
                p.project_id,
                p.project_code,
                p.project_title,
                p.status,
                p.current_phase,
                p.health_score,
                p.total_fee_usd as contract_value,
                p.contract_signed_date,
                p.target_completion,
                COALESCE(pr.client_company, p.project_title) as client_name
            FROM projects p
            LEFT JOIN proposals pr ON p.project_code = pr.project_code
            WHERE p.pm_staff_id = ?
            ORDER BY
                CASE WHEN p.is_active_project = 1 THEN 0 ELSE 1 END,
                p.project_code DESC
        """, (pm_id,))
        projects = []

        for row in cursor.fetchall():
            project = dict(row)
            project_code = project['project_code']

            # Get task counts for this project
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status IN ('pending', 'in_progress') THEN 1 ELSE 0 END) as open_tasks,
                    SUM(CASE WHEN status IN ('pending', 'in_progress')
                             AND due_date < ? AND due_date IS NOT NULL THEN 1 ELSE 0 END) as overdue
                FROM tasks
                WHERE project_code = ?
            """, (today, project_code))
            task_row = cursor.fetchone()
            project['total_tasks'] = task_row['total'] or 0
            project['open_tasks'] = task_row['open_tasks'] or 0
            project['overdue_tasks'] = task_row['overdue'] or 0

            # Get team count (architects on project)
            cursor.execute("""
                SELECT COUNT(DISTINCT member_id) as architect_count
                FROM schedule_entries
                WHERE project_code = ?
            """, (project_code,))
            arch_row = cursor.fetchone()
            project['architect_count'] = arch_row['architect_count'] or 0

            # Determine project health status
            overdue = project['overdue_tasks']
            if overdue > 3:
                project['health_status'] = 'at_risk'
            elif overdue > 0:
                project['health_status'] = 'warning'
            else:
                project['health_status'] = 'on_track'

            projects.append(project)

        conn.close()

        return {
            "success": True,
            "pm": pm_dict,
            "data": projects,
            "count": len(projects),
            "summary": {
                "total_projects": len(projects),
                "active_projects": len([p for p in projects if p.get('status') in ('Active', 'active')]),
                "total_open_tasks": sum(p['open_tasks'] for p in projects),
                "total_overdue": sum(p['overdue_tasks'] for p in projects)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/projects/{project_code}/assign-pm")
async def assign_pm_to_project(project_code: str, request: AssignPMRequest):
    """Assign a PM to a project"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Verify PM exists and is a PM
        cursor.execute("""
            SELECT staff_id, first_name, is_pm FROM staff WHERE staff_id = ?
        """, (request.pm_staff_id,))
        pm = cursor.fetchone()
        if not pm:
            raise HTTPException(status_code=404, detail=f"Staff {request.pm_staff_id} not found")
        if not pm['is_pm']:
            raise HTTPException(status_code=400, detail=f"Staff {pm['first_name']} is not a PM")

        # Verify project exists
        cursor.execute("""
            SELECT project_code FROM projects WHERE project_code = ?
        """, (project_code,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        # Assign PM
        cursor.execute("""
            UPDATE projects SET pm_staff_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE project_code = ?
        """, (request.pm_staff_id, project_code))

        conn.commit()
        conn.close()

        return action_response(
            True,
            message=f"PM {pm['first_name']} assigned to project {project_code}"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project_code}/assign-pm")
async def unassign_pm_from_project(project_code: str):
    """Remove PM assignment from a project"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE projects SET pm_staff_id = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE project_code = ?
        """, (project_code,))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        conn.commit()
        conn.close()

        return action_response(True, message=f"PM unassigned from project {project_code}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
