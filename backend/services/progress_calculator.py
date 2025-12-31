"""
Progress Calculator Service

Calculates project and phase progress based on tasks, deliverables, and milestones.
Provides behind/ahead indicators based on timeline comparison.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from .base_service import BaseService

logger = logging.getLogger(__name__)


class ProgressCalculatorService(BaseService):
    """Service for calculating project progress metrics"""

    # Standard phase order for Bensley projects
    PHASE_ORDER = {
        "Concept": 1, "concept_design": 1, "Concept Design": 1,
        "SD": 2, "schematic_design": 2, "Schematic Design": 2,
        "DD": 3, "design_development": 3, "Design Development": 3,
        "CD": 4, "construction_drawings": 4, "Construction Documents": 4,
        "CA": 5, "construction_observation": 5, "Construction Administration": 5,
    }

    def get_project_progress(self, project_code: str) -> Dict[str, Any]:
        """
        Get comprehensive project progress including per-phase breakdown.

        Returns:
            {
                "project_code": "25 BK-001",
                "overall_progress": 45.5,
                "phases": [
                    {
                        "phase": "Concept",
                        "progress_percent": 100,
                        "tasks_total": 10,
                        "tasks_completed": 10,
                        "deliverables_total": 5,
                        "deliverables_completed": 5,
                        "status": "completed",
                        "timeline_status": "on_track"  # or "behind", "ahead"
                    },
                    ...
                ],
                "current_phase": "DD",
                "timeline_status": "behind",
                "days_behind": 5
            }
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Get project info
                cursor.execute("""
                    SELECT project_id, project_title, contract_signed_date, status
                    FROM projects WHERE project_code = ?
                """, (project_code,))
                project = cursor.fetchone()

                if not project:
                    return {"error": f"Project {project_code} not found"}

                project_id = project['project_id']

                # Get phase progress from contract_phases
                cursor.execute("""
                    SELECT
                        phase_id, phase_name, phase_code, phase_order,
                        start_date, end_date, target_end_date,
                        progress_percent, status,
                        fee_percent
                    FROM contract_phases
                    WHERE project_id = ?
                    ORDER BY phase_order
                """, (project_id,))
                contract_phases = [dict(row) for row in cursor.fetchall()]

                # Get task counts by phase
                cursor.execute("""
                    SELECT
                        phase,
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
                    FROM tasks
                    WHERE project_code = ?
                    GROUP BY phase
                """, (project_code,))
                task_stats = {row['phase']: dict(row) for row in cursor.fetchall()}

                # Get deliverable counts by phase
                cursor.execute("""
                    SELECT
                        phase,
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as completed
                    FROM deliverables
                    WHERE project_code = ?
                    GROUP BY phase
                """, (project_code,))
                deliverable_stats = {row['phase']: dict(row) for row in cursor.fetchall()}

                # Get daily_work hours by phase (if table exists)
                work_stats = {}
                try:
                    cursor.execute("""
                        SELECT
                            phase,
                            SUM(hours_spent) as total_hours,
                            COUNT(*) as submission_count
                        FROM daily_work
                        WHERE project_code = ?
                        GROUP BY phase
                    """, (project_code,))
                    work_stats = {row['phase']: dict(row) for row in cursor.fetchall()}
                except sqlite3.OperationalError:
                    pass  # Table doesn't exist

                # Build phase progress list
                phases = []
                total_weight = 0
                weighted_progress = 0

                for cp in contract_phases:
                    phase_name = cp['phase_name'] or cp['phase_code']
                    phase_code = cp['phase_code']

                    # Get task stats for this phase
                    ts = task_stats.get(phase_code, {'total': 0, 'completed': 0})
                    ds = deliverable_stats.get(phase_code, {'total': 0, 'completed': 0})
                    ws = work_stats.get(phase_code, {'total_hours': 0, 'submission_count': 0})

                    # Calculate phase progress
                    # Priority: 1) stored progress_percent, 2) task completion, 3) deliverable completion
                    if cp['progress_percent'] is not None:
                        progress = cp['progress_percent']
                    elif ts['total'] > 0:
                        progress = (ts['completed'] / ts['total']) * 100
                    elif ds['total'] > 0:
                        progress = (ds['completed'] / ds['total']) * 100
                    else:
                        progress = 0

                    # Determine timeline status
                    timeline_status = "on_track"
                    days_variance = 0

                    if cp['target_end_date'] and cp['end_date']:
                        target = datetime.strptime(cp['target_end_date'], '%Y-%m-%d')
                        actual_or_planned = datetime.strptime(cp['end_date'], '%Y-%m-%d')
                        days_variance = (actual_or_planned - target).days

                        if days_variance > 7:
                            timeline_status = "behind"
                        elif days_variance < -7:
                            timeline_status = "ahead"
                    elif cp['end_date'] and cp['status'] not in ('completed', 'approved'):
                        # Check if past end date but not complete
                        end = datetime.strptime(cp['end_date'], '%Y-%m-%d')
                        if end < datetime.now() and progress < 100:
                            timeline_status = "behind"
                            days_variance = (datetime.now() - end).days

                    phases.append({
                        "phase_id": cp['phase_id'],
                        "phase": phase_code,
                        "phase_name": phase_name,
                        "phase_order": cp['phase_order'],
                        "progress_percent": round(progress, 1),
                        "tasks_total": ts['total'],
                        "tasks_completed": ts['completed'],
                        "deliverables_total": ds['total'],
                        "deliverables_completed": ds['completed'],
                        "hours_logged": ws.get('total_hours', 0) or 0,
                        "start_date": cp['start_date'],
                        "end_date": cp['end_date'],
                        "target_end_date": cp['target_end_date'],
                        "status": cp['status'],
                        "timeline_status": timeline_status,
                        "days_variance": days_variance,
                        "fee_percent": cp['fee_percent'] or 0
                    })

                    # Accumulate weighted progress
                    weight = cp['fee_percent'] or (100 / max(len(contract_phases), 1))
                    total_weight += weight
                    weighted_progress += progress * weight

                # Calculate overall progress
                overall_progress = (weighted_progress / total_weight) if total_weight > 0 else 0

                # Determine current phase (first non-completed phase)
                current_phase = None
                for p in phases:
                    if p['status'] not in ('completed', 'approved') and p['progress_percent'] < 100:
                        current_phase = p['phase']
                        break

                # Overall timeline status
                behind_phases = [p for p in phases if p['timeline_status'] == 'behind']
                overall_timeline = "on_track"
                total_days_behind = 0
                if behind_phases:
                    overall_timeline = "behind"
                    total_days_behind = max(p['days_variance'] for p in behind_phases)

                return {
                    "success": True,
                    "project_code": project_code,
                    "project_title": project['project_title'],
                    "overall_progress": round(overall_progress, 1),
                    "phases": phases,
                    "current_phase": current_phase,
                    "timeline_status": overall_timeline,
                    "days_behind": total_days_behind if overall_timeline == "behind" else 0,
                    "total_phases": len(phases)
                }

        except sqlite3.OperationalError as e:
            logger.error(f"Database error getting progress: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error calculating progress: {e}")
            return {"error": str(e)}

    def update_phase_progress(
        self,
        phase_id: int,
        progress_percent: float,
        status: Optional[str] = None
    ) -> bool:
        """Update progress for a specific phase"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                updates = ["progress_percent = ?", "updated_at = datetime('now')"]
                params = [progress_percent]

                if status:
                    updates.append("status = ?")
                    params.append(status)

                # Auto-set status based on progress
                if progress_percent >= 100 and not status:
                    updates.append("status = 'completed'")
                elif progress_percent > 0 and progress_percent < 100 and not status:
                    updates.append("status = 'in_progress'")

                params.append(phase_id)

                cursor.execute(f"""
                    UPDATE contract_phases
                    SET {', '.join(updates)}
                    WHERE phase_id = ?
                """, params)

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error updating phase progress: {e}")
            return False

    def get_progress_summary(self, project_codes: List[str] = None) -> List[Dict]:
        """
        Get progress summary for multiple projects.

        Useful for dashboard views showing overall portfolio progress.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                query = """
                    SELECT
                        p.project_code,
                        p.project_title,
                        p.status as project_status,
                        COUNT(cp.phase_id) as total_phases,
                        SUM(CASE WHEN cp.status = 'completed' THEN 1 ELSE 0 END) as completed_phases,
                        AVG(cp.progress_percent) as avg_progress,
                        MAX(CASE
                            WHEN cp.end_date < date('now') AND cp.status NOT IN ('completed', 'approved')
                            THEN julianday('now') - julianday(cp.end_date)
                            ELSE 0
                        END) as max_days_behind
                    FROM projects p
                    LEFT JOIN contract_phases cp ON p.project_id = cp.project_id
                    WHERE p.status IN ('active', 'in_progress')
                """
                params = []

                if project_codes:
                    placeholders = ','.join('?' * len(project_codes))
                    query += f" AND p.project_code IN ({placeholders})"
                    params.extend(project_codes)

                query += " GROUP BY p.project_id ORDER BY max_days_behind DESC, avg_progress ASC"

                cursor.execute(query, params)

                results = []
                for row in cursor.fetchall():
                    results.append({
                        "project_code": row['project_code'],
                        "project_title": row['project_title'],
                        "status": row['project_status'],
                        "total_phases": row['total_phases'] or 0,
                        "completed_phases": row['completed_phases'] or 0,
                        "progress_percent": round(row['avg_progress'] or 0, 1),
                        "days_behind": int(row['max_days_behind'] or 0),
                        "timeline_status": "behind" if (row['max_days_behind'] or 0) > 7 else "on_track"
                    })

                return results

        except Exception as e:
            logger.error(f"Error getting progress summary: {e}")
            return []


# Singleton instance
_progress_calculator = None


def get_progress_calculator(db_path: str = None) -> ProgressCalculatorService:
    """Get or create the progress calculator service instance."""
    global _progress_calculator
    if _progress_calculator is None:
        _progress_calculator = ProgressCalculatorService(db_path)
    return _progress_calculator
