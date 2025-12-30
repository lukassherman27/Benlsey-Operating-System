"""
Deliverables & PM Workload Service

Manages project deliverables, PM assignments, and workload tracking.
Includes standard project lifecycle phase templates.
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from .base_service import BaseService

logger = logging.getLogger(__name__)


class DeliverablesService(BaseService):
    """Service for deliverables tracking and PM workload management"""

    # Standard Bensley project lifecycle phases with typical durations
    LIFECYCLE_PHASES = [
        {
            "phase": "mobilization",
            "phase_order": 1,
            "typical_duration_months": 2,
            "description": "Contract signed, mobilization fee paid",
            "deliverables": ["Contract execution", "Mobilization invoice"]
        },
        {
            "phase": "concept_design",
            "phase_order": 2,
            "typical_duration_months": 3,
            "description": "Initial design concepts",
            "deliverables": [
                "50% Concept Design (interim)",
                "Final Concept Design Presentation",
                "Concept Design Drawings",
                "3D Models / Renderings"
            ]
        },
        {
            "phase": "schematic_design",
            "phase_order": 3,
            "typical_duration_months": 1,
            "description": "Optional schematic refinement",
            "is_optional": True,
            "deliverables": ["Schematic Design Package"]
        },
        {
            "phase": "design_development",
            "phase_order": 4,
            "typical_duration_months": 4,
            "description": "Detailed design development",
            "deliverables": [
                "50% Design Development",
                "Final Design Development",
                "Material Boards",
                "Color Drawings",
                "Perspective Cutouts"
            ]
        },
        {
            "phase": "construction_drawings",
            "phase_order": 5,
            "typical_duration_months": 3,
            "description": "Construction documentation",
            "deliverables": [
                "50% Construction Drawings",
                "100% Construction Drawings",
                "Construction Package"
            ]
        },
        {
            "phase": "construction_observation",
            "phase_order": 6,
            "typical_duration_months": 24,  # Ongoing until contract end
            "description": "Site visits, RFI responses, design adjustments",
            "deliverables": [
                "Site Visit Reports",
                "RFI Responses",
                "Design Adjustments"
            ]
        }
    ]

    # Alert thresholds in days
    ALERT_THRESHOLDS = [14, 7, 1, 0]  # 2 weeks, 1 week, 1 day, day-of

    def get_all_deliverables(
        self,
        project_code: Optional[str] = None,
        status: Optional[str] = None,
        assigned_pm: Optional[str] = None,
        phase: Optional[str] = None,
        include_overdue: bool = True
    ) -> List[Dict]:
        """Get deliverables with optional filters"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                query = """
                    SELECT
                        d.*,
                        p.project_title,
                        p.client_id,
                        julianday(d.due_date) - julianday('now') as days_until_due,
                        CASE
                            WHEN d.status IN ('pending', 'in_progress')
                                 AND date(d.due_date) < date('now')
                            THEN 1 ELSE 0
                        END as is_overdue
                    FROM deliverables d
                    LEFT JOIN projects p ON d.project_id = p.project_id
                    WHERE 1=1
                """
                params = []

                if project_code:
                    query += " AND d.project_code = ?"
                    params.append(project_code)

                if status:
                    query += " AND d.status = ?"
                    params.append(status)

                if assigned_pm:
                    if assigned_pm.lower() == 'unassigned':
                        query += " AND d.assigned_pm IS NULL"
                    else:
                        query += " AND d.assigned_pm = ?"
                        params.append(assigned_pm)

                if phase:
                    query += " AND d.phase = ?"
                    params.append(phase)

                query += " ORDER BY d.due_date ASC"

                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                logger.warning("Deliverables table not found - returning empty list")
                return []
            raise

    def get_overdue_deliverables(self) -> List[Dict]:
        """Get all overdue deliverables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT
                        d.*,
                        p.project_title,
                        julianday('now') - julianday(d.due_date) as days_overdue
                    FROM deliverables d
                    LEFT JOIN projects p ON d.project_id = p.project_id
                    WHERE d.status IN ('pending', 'in_progress')
                    AND date(d.due_date) < date('now')
                    ORDER BY days_overdue DESC
                """)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                logger.warning("Deliverables table not found - returning empty list")
                return []
            raise

    def get_upcoming_deliverables(self, days_ahead: int = 14) -> List[Dict]:
        """Get deliverables due within specified days"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT
                        d.*,
                        p.project_title,
                        p.project_code as p_code,
                        julianday(d.due_date) - julianday('now') as days_until_due,
                        CASE
                            WHEN julianday(d.due_date) - julianday('now') <= 0 THEN 'today'
                            WHEN julianday(d.due_date) - julianday('now') <= 1 THEN 'tomorrow'
                            WHEN julianday(d.due_date) - julianday('now') <= 7 THEN 'this_week'
                            ELSE 'upcoming'
                        END as urgency_level
                    FROM deliverables d
                    LEFT JOIN projects p ON d.project_id = p.project_id
                    WHERE d.status IN ('pending', 'in_progress')
                    AND date(d.due_date) BETWEEN date('now') AND date('now', '+' || ? || ' days')
                    ORDER BY d.due_date ASC
                """, (days_ahead,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                logger.warning("Deliverables table not found - returning empty list")
                return []
            raise

    def get_pm_workload(self, pm_name: Optional[str] = None) -> List[Dict]:
        """
        Get PM workload summary showing deliverable counts by status.
        Infers PM from assigned_pm field in deliverables or team assignments.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    COALESCE(d.assigned_pm, 'Unassigned') as pm_name,
                    COUNT(*) as total_deliverables,
                    COUNT(CASE WHEN d.status = 'pending' THEN 1 END) as pending_count,
                    COUNT(CASE WHEN d.status = 'in_progress' THEN 1 END) as in_progress_count,
                    COUNT(CASE WHEN d.status = 'completed' THEN 1 END) as completed_count,
                    COUNT(CASE WHEN d.status IN ('pending', 'in_progress')
                               AND date(d.due_date) < date('now') THEN 1 END) as overdue_count,
                    COUNT(CASE WHEN date(d.due_date) BETWEEN date('now') AND date('now', '+7 days')
                               AND d.status IN ('pending', 'in_progress') THEN 1 END) as due_this_week,
                    COUNT(CASE WHEN date(d.due_date) BETWEEN date('now') AND date('now', '+14 days')
                               AND d.status IN ('pending', 'in_progress') THEN 1 END) as due_two_weeks
                FROM deliverables d
                WHERE 1=1
            """
            params = []

            if pm_name:
                query += " AND d.assigned_pm = ?"
                params.append(pm_name)

            query += " GROUP BY COALESCE(d.assigned_pm, 'Unassigned')"

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_pm_list(self) -> List[Dict]:
        """Get list of all PMs (team leads) for assignment dropdowns"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    member_id,
                    full_name,
                    discipline,
                    office,
                    is_team_lead
                FROM team_members
                WHERE is_team_lead = 1 OR discipline = 'Management'
                ORDER BY full_name
            """)
            return [dict(row) for row in cursor.fetchall()]

    def infer_pm_for_project(self, project_code: str) -> Optional[str]:
        """
        Infer the PM for a project based on:
        1. Manual assignment in projects table (team_lead)
        2. Most frequent responder to RFIs/emails
        3. Most scheduled person on the project
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Check if project has team_lead assigned
            cursor.execute("""
                SELECT team_lead FROM projects WHERE project_code = ?
            """, (project_code,))
            row = cursor.fetchone()
            if row and row['team_lead']:
                return row['team_lead']

            # 2. Find most frequent sender on project emails (who answers)
            cursor.execute("""
                SELECT e.sender_name, COUNT(*) as email_count
                FROM emails e
                JOIN email_project_links epl ON e.email_id = epl.email_id
                JOIN projects p ON epl.project_id = p.project_id
                WHERE p.project_code = ?
                AND e.sender_email LIKE '%bensley%'
                GROUP BY e.sender_name
                ORDER BY email_count DESC
                LIMIT 1
            """, (project_code,))
            row = cursor.fetchone()
            if row and row['sender_name']:
                return row['sender_name']

            # 3. Find most scheduled person on project
            cursor.execute("""
                SELECT tm.full_name, COUNT(*) as days_scheduled
                FROM schedule_entries se
                JOIN team_members tm ON se.member_id = tm.member_id
                WHERE se.project_code = ?
                GROUP BY tm.full_name
                ORDER BY days_scheduled DESC
                LIMIT 1
            """, (project_code,))
            row = cursor.fetchone()
            if row:
                return row['full_name']

            return None

    def create_deliverable(
        self,
        project_code: str,
        deliverable_name: str,
        due_date: str,
        phase: Optional[str] = None,
        deliverable_type: Optional[str] = None,
        assigned_pm: Optional[str] = None,
        description: Optional[str] = None,
        priority: str = 'normal'
    ) -> int:
        """Create a new deliverable"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get project_id
            cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
            row = cursor.fetchone()
            project_id = row['project_id'] if row else None

            # Auto-infer PM if not provided
            if not assigned_pm:
                assigned_pm = self.infer_pm_for_project(project_code)

            cursor.execute("""
                INSERT INTO deliverables (
                    project_id, project_code, deliverable_name, deliverable_type,
                    phase, due_date, assigned_pm, description, priority, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (
                project_id, project_code, deliverable_name, deliverable_type,
                phase, due_date, assigned_pm, description, priority
            ))

            conn.commit()
            deliverable_id = cursor.lastrowid

            logger.info(f"Created deliverable {deliverable_id} for {project_code}: {deliverable_name}")
            return deliverable_id

    def update_deliverable_status(
        self,
        deliverable_id: int,
        status: str,
        notes: Optional[str] = None,
        submitted_date: Optional[str] = None
    ) -> bool:
        """Update deliverable status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            updates = ["status = ?"]
            params = [status]

            if notes:
                updates.append("notes = ?")
                params.append(notes)

            if status == 'submitted' and not submitted_date:
                submitted_date = datetime.now().strftime('%Y-%m-%d')

            if submitted_date:
                updates.append("submitted_date = ?")
                params.append(submitted_date)

            if status == 'approved':
                updates.append("approved_date = datetime('now')")

            params.append(deliverable_id)

            cursor.execute(f"""
                UPDATE deliverables
                SET {', '.join(updates)}
                WHERE deliverable_id = ?
            """, params)

            conn.commit()
            return cursor.rowcount > 0

    def add_overdue_context(
        self,
        deliverable_id: int,
        context: str,
        context_by: str
    ) -> bool:
        """Add context/explanation for overdue deliverable"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get existing notes
            cursor.execute("SELECT notes FROM deliverables WHERE deliverable_id = ?", (deliverable_id,))
            row = cursor.fetchone()
            existing_notes = row['notes'] if row and row['notes'] else ''

            # Append context with timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            new_note = f"\n[{timestamp}] {context_by}: {context}"
            updated_notes = existing_notes + new_note

            cursor.execute("""
                UPDATE deliverables
                SET notes = ?
                WHERE deliverable_id = ?
            """, (updated_notes.strip(), deliverable_id))

            conn.commit()
            return cursor.rowcount > 0

    def generate_project_milestones(
        self,
        project_code: str,
        contract_start_date: str,
        disciplines: List[str] = None,
        skip_schematic: bool = True
    ) -> List[int]:
        """
        Generate standard milestone deliverables for a project based on lifecycle template.

        Args:
            project_code: Project code
            contract_start_date: When contract was signed (YYYY-MM-DD)
            disciplines: List of disciplines (default: ['Landscape', 'Architecture', 'Interior'])
            skip_schematic: Whether to skip optional schematic design phase

        Returns:
            List of created deliverable IDs
        """
        if disciplines is None:
            disciplines = ['Landscape', 'Architecture', 'Interior']

        created_ids = []
        start_date = datetime.strptime(contract_start_date, '%Y-%m-%d')
        current_date = start_date

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get project_id
            cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
            row = cursor.fetchone()
            project_id = row['project_id'] if row else None

            # Infer PM
            assigned_pm = self.infer_pm_for_project(project_code)

            for phase_info in self.LIFECYCLE_PHASES:
                # Skip optional schematic if requested
                if phase_info.get('is_optional') and skip_schematic:
                    continue

                phase = phase_info['phase']
                duration_months = phase_info['typical_duration_months']

                # Calculate phase end date
                phase_end = current_date + timedelta(days=duration_months * 30)

                # For each discipline, create deliverables
                for discipline in disciplines:
                    for deliverable_name in phase_info['deliverables']:
                        full_name = f"{discipline} - {deliverable_name}"

                        cursor.execute("""
                            INSERT INTO deliverables (
                                project_id, project_code, deliverable_name,
                                deliverable_type, phase, due_date,
                                assigned_pm, priority, status,
                                description
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'normal', 'pending', ?)
                        """, (
                            project_id,
                            project_code,
                            full_name,
                            'presentation' if 'Presentation' in deliverable_name else 'drawings',
                            phase,
                            phase_end.strftime('%Y-%m-%d'),
                            assigned_pm,
                            f"Standard {phase} deliverable"
                        ))
                        created_ids.append(cursor.lastrowid)

                # Move to next phase
                current_date = phase_end

            conn.commit()
            logger.info(f"Generated {len(created_ids)} milestone deliverables for {project_code}")

        return created_ids

    def get_project_phase_status(self, project_code: str) -> Dict:
        """
        Get current phase status for a project, flagging if behind typical schedule.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get project contract date
            cursor.execute("""
                SELECT contract_signed_date, project_title
                FROM projects
                WHERE project_code = ?
            """, (project_code,))
            project = cursor.fetchone()

            if not project or not project['contract_signed_date']:
                return {"error": "Project not found or no contract date"}

            contract_date = datetime.strptime(project['contract_signed_date'], '%Y-%m-%d')
            months_since_contract = (datetime.now() - contract_date).days / 30

            # Determine expected phase based on typical durations
            cumulative_months = 0
            expected_phase = None
            for phase_info in self.LIFECYCLE_PHASES:
                if phase_info.get('is_optional'):
                    continue
                cumulative_months += phase_info['typical_duration_months']
                if months_since_contract <= cumulative_months:
                    expected_phase = phase_info['phase']
                    break
            else:
                expected_phase = 'construction_observation'

            # Get actual deliverables status
            cursor.execute("""
                SELECT
                    phase,
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    MIN(due_date) as earliest_due,
                    MAX(CASE WHEN status = 'completed' THEN submitted_date END) as last_completed
                FROM deliverables
                WHERE project_code = ?
                GROUP BY phase
                ORDER BY MIN(due_date)
            """, (project_code,))

            phases = [dict(row) for row in cursor.fetchall()]

            # Check for flags
            flags = []

            # Flag: No deliverables at all
            if not phases:
                flags.append({
                    "type": "warning",
                    "message": f"No deliverables tracked for {project_code}",
                    "action": "Generate milestone deliverables"
                })

            # Flag: Behind typical schedule
            if months_since_contract > 3:  # After mobilization period
                concept_completed = any(
                    p['phase'] == 'concept_design' and p['completed'] > 0
                    for p in phases
                )
                if not concept_completed and months_since_contract > 5:
                    flags.append({
                        "type": "alert",
                        "message": f"{months_since_contract:.1f} months since contract, no concept design completed",
                        "typical": "Concept design typically done by month 5",
                        "action": "Add context or schedule presentation"
                    })

            return {
                "project_code": project_code,
                "project_title": project['project_title'],
                "contract_date": project['contract_signed_date'],
                "months_since_contract": round(months_since_contract, 1),
                "expected_phase": expected_phase,
                "phases": phases,
                "flags": flags
            }

    def get_alerts(self) -> List[Dict]:
        """
        Get all active alerts for deliverables (due soon + overdue)
        """
        alerts = []

        # Day-of alerts
        today = self.get_upcoming_deliverables(days_ahead=0)
        for d in today:
            alerts.append({
                "type": "day_of",
                "priority": "critical",
                "deliverable_id": d['deliverable_id'],
                "project_code": d['project_code'],
                "deliverable_name": d['deliverable_name'],
                "message": f"DUE TODAY: {d['deliverable_name']}",
                "assigned_pm": d.get('assigned_pm')
            })

        # Tomorrow alerts
        tomorrow = [d for d in self.get_upcoming_deliverables(days_ahead=1)
                   if d.get('days_until_due', 0) > 0]
        for d in tomorrow:
            alerts.append({
                "type": "tomorrow",
                "priority": "high",
                "deliverable_id": d['deliverable_id'],
                "project_code": d['project_code'],
                "deliverable_name": d['deliverable_name'],
                "message": f"DUE TOMORROW: {d['deliverable_name']}",
                "assigned_pm": d.get('assigned_pm')
            })

        # 7-day alerts
        week = [d for d in self.get_upcoming_deliverables(days_ahead=7)
               if 1 < d.get('days_until_due', 0) <= 7]
        for d in week:
            alerts.append({
                "type": "this_week",
                "priority": "medium",
                "deliverable_id": d['deliverable_id'],
                "project_code": d['project_code'],
                "deliverable_name": d['deliverable_name'],
                "message": f"Due in {int(d['days_until_due'])} days: {d['deliverable_name']}",
                "assigned_pm": d.get('assigned_pm')
            })

        # 14-day alerts
        two_weeks = [d for d in self.get_upcoming_deliverables(days_ahead=14)
                    if 7 < d.get('days_until_due', 0) <= 14]
        for d in two_weeks:
            alerts.append({
                "type": "two_weeks",
                "priority": "low",
                "deliverable_id": d['deliverable_id'],
                "project_code": d['project_code'],
                "deliverable_name": d['deliverable_name'],
                "message": f"Due in {int(d['days_until_due'])} days: {d['deliverable_name']}",
                "assigned_pm": d.get('assigned_pm')
            })

        # Overdue alerts
        overdue = self.get_overdue_deliverables()
        for d in overdue:
            alerts.append({
                "type": "overdue",
                "priority": "critical",
                "deliverable_id": d['deliverable_id'],
                "project_code": d['project_code'],
                "deliverable_name": d['deliverable_name'],
                "message": f"OVERDUE by {int(d['days_overdue'])} days: {d['deliverable_name']}",
                "days_overdue": int(d['days_overdue']),
                "assigned_pm": d.get('assigned_pm'),
                "has_context": bool(d.get('notes'))
            })

        return alerts

    def get_deliverable_by_id(self, deliverable_id: int) -> Optional[Dict]:
        """Get a single deliverable by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT d.*, p.project_title
                    FROM deliverables d
                    LEFT JOIN projects p ON d.project_id = p.project_id
                    WHERE d.deliverable_id = ?
                """, (deliverable_id,))
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    # Parse attachments JSON if present
                    if result.get('attachments'):
                        try:
                            result['attachments'] = json.loads(result['attachments'])
                        except:
                            result['attachments'] = []
                    return result
                return None
        except sqlite3.OperationalError as e:
            logger.error(f"Error getting deliverable {deliverable_id}: {e}")
            return None

    def update_deliverable(self, deliverable_id: int, updates: Dict[str, Any]) -> bool:
        """Update a deliverable with arbitrary fields"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Handle attachments JSON serialization
                if 'attachments' in updates and updates['attachments'] is not None:
                    updates['attachments'] = json.dumps(updates['attachments'])

                # Build dynamic update query
                set_clauses = []
                params = []
                for key, value in updates.items():
                    set_clauses.append(f"{key} = ?")
                    params.append(value)

                if not set_clauses:
                    return False

                set_clauses.append("updated_at = datetime('now')")
                params.append(deliverable_id)

                query = f"""
                    UPDATE deliverables
                    SET {', '.join(set_clauses)}
                    WHERE deliverable_id = ?
                """
                cursor.execute(query, params)
                conn.commit()

                logger.info(f"Updated deliverable {deliverable_id}: {list(updates.keys())}")
                return cursor.rowcount > 0
        except sqlite3.OperationalError as e:
            logger.error(f"Error updating deliverable {deliverable_id}: {e}")
            return False

    def delete_deliverable(self, deliverable_id: int) -> bool:
        """Delete a deliverable"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM deliverables WHERE deliverable_id = ?",
                    (deliverable_id,)
                )
                conn.commit()
                logger.info(f"Deleted deliverable {deliverable_id}")
                return cursor.rowcount > 0
        except sqlite3.OperationalError as e:
            logger.error(f"Error deleting deliverable {deliverable_id}: {e}")
            return False

    def seed_from_milestones(self) -> Dict:
        """
        Seed deliverables table from existing project_milestones data.
        One-time migration helper.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get existing milestones
            cursor.execute("""
                SELECT
                    m.milestone_id,
                    m.project_id,
                    m.project_code,
                    m.phase,
                    m.milestone_name,
                    m.milestone_type,
                    m.planned_date,
                    m.actual_date,
                    m.status,
                    m.notes
                FROM project_milestones m
                WHERE NOT EXISTS (
                    SELECT 1 FROM deliverables d
                    WHERE d.project_code = m.project_code
                    AND d.deliverable_name = m.milestone_name
                )
            """)

            milestones = cursor.fetchall()
            created = 0
            skipped = 0

            for m in milestones:
                # Infer PM for this project
                pm = self.infer_pm_for_project(m['project_code'])

                # Map milestone status to deliverable status
                status_map = {
                    'complete': 'completed',
                    'completed': 'completed',
                    'pending': 'pending',
                    'in_progress': 'in_progress',
                    None: 'pending'
                }
                status = status_map.get(m['status'], 'pending')

                try:
                    cursor.execute("""
                        INSERT INTO deliverables (
                            project_id, project_code, deliverable_name,
                            phase, due_date, submitted_date, status,
                            assigned_pm, notes, description
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        m['project_id'],
                        m['project_code'],
                        m['milestone_name'],
                        m['phase'],
                        m['planned_date'],
                        m['actual_date'] if status == 'completed' else None,
                        status,
                        pm,
                        m['notes'],
                        f"Seeded from milestone {m['milestone_id']}"
                    ))
                    created += 1
                except Exception as e:
                    logger.warning(f"Skipped milestone {m['milestone_id']}: {e}")
                    skipped += 1

            conn.commit()

            return {
                "milestones_found": len(milestones),
                "deliverables_created": created,
                "skipped": skipped
            }
