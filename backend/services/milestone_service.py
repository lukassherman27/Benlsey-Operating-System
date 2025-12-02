"""
Service layer for project milestones management
Handles CRUD operations, timeline generation, and delay tracking
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
import sqlite3


class MilestoneService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self):
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_milestones_by_proposal(self, proposal_id: int) -> List[Dict[str, Any]]:
        """Get all milestones for a specific proposal"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                milestone_id,
                project_id as proposal_id,
                milestone_type,
                milestone_name,
                notes as description,
                planned_date as expected_date,
                actual_date,
                status,
                '' as delay_reason,
                0 as delay_days,
                '' as responsible_party,
                notes,
                created_at,
                created_at as updated_at
            FROM project_milestones
            WHERE project_id = ?
            ORDER BY planned_date ASC
        """, (proposal_id,))

        milestones = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return milestones

    def get_milestone_by_id(self, milestone_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific milestone by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM project_milestones
            WHERE milestone_id = ?
        """, (milestone_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def create_milestone(self, data: Dict[str, Any]) -> int:
        """Create a new milestone"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO project_milestones (
                project_id,
                project_code,
                phase,
                milestone_name,
                milestone_type,
                planned_date,
                actual_date,
                status,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('proposal_id') or data.get('project_id'),
            data.get('project_code', ''),
            data.get('phase', ''),
            data.get('milestone_name'),
            data.get('milestone_type'),
            data.get('expected_date') or data.get('planned_date'),
            data.get('actual_date'),
            data.get('status', 'pending'),
            data.get('notes') or data.get('description')
        ))

        milestone_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return milestone_id

    def update_milestone(self, milestone_id: int, data: Dict[str, Any]) -> bool:
        """Update an existing milestone"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build dynamic update query based on provided fields
        update_fields = []
        values = []

        allowed_fields = [
            'milestone_type', 'milestone_name', 'description',
            'planned_date', 'actual_date', 'status', 'delay_reason',
            'delay_days', 'responsible_party', 'notes'
        ]

        # Allow both expected_date and planned_date for compatibility
        if 'expected_date' in data and 'planned_date' not in data:
            data['planned_date'] = data['expected_date']

        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                values.append(data[field])

        if not update_fields:
            conn.close()
            return False

        values.append(milestone_id)
        query = f"UPDATE project_milestones SET {', '.join(update_fields)} WHERE milestone_id = ?"

        cursor.execute(query, values)
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def delete_milestone(self, milestone_id: int) -> bool:
        """Delete a milestone"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM project_milestones WHERE milestone_id = ?", (milestone_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def get_timeline_data(self, proposal_id: int) -> Dict[str, Any]:
        """
        Generate timeline view data for a proposal
        Returns milestones with expected vs actual comparison
        """
        milestones = self.get_milestones_by_proposal(proposal_id)

        timeline = {
            'proposal_id': proposal_id,
            'total_milestones': len(milestones),
            'completed': 0,
            'on_track': 0,
            'delayed': 0,
            'pending': 0,
            'milestones': []
        }

        today = date.today()

        for milestone in milestones:
            # Calculate delay if applicable
            if milestone['status'] == 'delayed':
                timeline['delayed'] += 1
            elif milestone['status'] == 'completed':
                timeline['completed'] += 1
            elif milestone['status'] == 'on_track':
                timeline['on_track'] += 1
            elif milestone['status'] == 'pending':
                timeline['pending'] += 1

            # Parse dates
            expected = datetime.strptime(milestone['expected_date'], '%Y-%m-%d').date() if milestone['expected_date'] else None
            actual = datetime.strptime(milestone['actual_date'], '%Y-%m-%d').date() if milestone['actual_date'] else None

            # Calculate days until/since expected
            days_until_expected = (expected - today).days if expected else None

            timeline['milestones'].append({
                'milestone_id': milestone['milestone_id'],
                'milestone_name': milestone['milestone_name'],
                'milestone_type': milestone['milestone_type'],
                'expected_date': milestone['expected_date'],
                'actual_date': milestone['actual_date'],
                'status': milestone['status'],
                'delay_days': milestone['delay_days'],
                'delay_reason': milestone['delay_reason'],
                'responsible_party': milestone['responsible_party'],
                'days_until_expected': days_until_expected,
                'is_overdue': expected < today if expected and milestone['status'] != 'completed' else False
            })

        return timeline

    def get_overdue_milestones(self) -> List[Dict[str, Any]]:
        """Get all overdue milestones across all proposals"""
        conn = self._get_connection()
        cursor = conn.cursor()

        today = date.today().isoformat()

        cursor.execute("""
            SELECT
                m.*,
                p.project_code,
                p.project_title,
                COALESCE(pr.client_company, 'Unknown') as client_company
            FROM project_milestones m
            JOIN projects p ON m.project_id = p.project_id
            LEFT JOIN proposals pr ON p.project_code = pr.project_code
            WHERE m.planned_date < ?
              AND m.status != 'completed'
              AND m.status != 'cancelled'
            ORDER BY m.planned_date ASC
        """, (today,))

        milestones = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return milestones

    def get_upcoming_milestones(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get milestones coming up in the next N days"""
        conn = self._get_connection()
        cursor = conn.cursor()

        today = date.today()
        future_date = (today + timedelta(days=days_ahead)).isoformat()
        today_str = today.isoformat()

        cursor.execute("""
            SELECT
                m.*,
                p.project_code,
                p.project_title,
                COALESCE(pr.client_company, 'Unknown') as client_company
            FROM project_milestones m
            JOIN projects p ON m.project_id = p.project_id
            LEFT JOIN proposals pr ON p.project_code = pr.project_code
            WHERE m.planned_date BETWEEN ? AND ?
              AND m.status != 'completed'
              AND m.status != 'cancelled'
            ORDER BY m.planned_date ASC
        """, (today_str, future_date))

        milestones = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return milestones

    def update_milestone_status(self, milestone_id: int, status: str, actual_date: Optional[str] = None) -> bool:
        """
        Update milestone status and optionally set actual completion date
        Automatically calculates delay_days if completed late
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get current milestone data
        cursor.execute("SELECT planned_date, actual_date FROM project_milestones WHERE milestone_id = ?", (milestone_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False

        planned_date = row['planned_date']
        delay_days = 0

        # Calculate delay if completing milestone
        if status == 'completed' and actual_date:
            planned = datetime.strptime(planned_date, '%Y-%m-%d').date()
            actual = datetime.strptime(actual_date, '%Y-%m-%d').date()
            delay_days = (actual - planned).days if actual > planned else 0

        cursor.execute("""
            UPDATE project_milestones
            SET status = ?,
                actual_date = ?,
                delay_days = ?
            WHERE milestone_id = ?
        """, (status, actual_date, delay_days, milestone_id))

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success
