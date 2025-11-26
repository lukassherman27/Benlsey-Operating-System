"""
Service layer for project context, tasks, and notes
Handles context management, task tracking, and agent action logging
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
import sqlite3
import json


class ContextService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self):
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_context_by_proposal(self, proposal_id: int, context_type: Optional[str] = None,
                                 status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all context items for a specific proposal with optional filters"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                c.*,
                e.subject as email_subject,
                m.milestone_name
            FROM project_context c
            LEFT JOIN emails e ON c.related_email_id = e.email_id
            LEFT JOIN project_milestones m ON c.related_milestone_id = m.milestone_id
            WHERE c.proposal_id = ?
        """
        params = [proposal_id]

        if context_type:
            query += " AND c.context_type = ?"
            params.append(context_type)

        if status:
            query += " AND c.status = ?"
            params.append(status)

        query += " ORDER BY c.created_at DESC"

        cursor.execute(query, params)

        contexts = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return contexts

    def get_context_by_id(self, context_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific context item by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM project_context
            WHERE context_id = ?
        """, (context_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def create_context(self, data: Dict[str, Any]) -> int:
        """Create a new context item (note, task, reminder, etc.)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO project_context (
                proposal_id,
                context_type,
                context_text,
                priority,
                status,
                due_date,
                assigned_to,
                created_by,
                related_email_id,
                related_milestone_id,
                agent_action_taken,
                agent_action_result,
                agent_action_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('proposal_id'),
            data.get('context_type'),
            data.get('context_text'),
            data.get('priority', 'normal'),
            data.get('status', 'active'),
            data.get('due_date'),
            data.get('assigned_to'),
            data.get('created_by', 'lukas'),
            data.get('related_email_id'),
            data.get('related_milestone_id'),
            data.get('agent_action_taken'),
            data.get('agent_action_result'),
            data.get('agent_action_timestamp')
        ))

        context_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return context_id

    def update_context(self, context_id: int, data: Dict[str, Any]) -> bool:
        """Update an existing context item"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build dynamic update query
        update_fields = []
        values = []

        allowed_fields = [
            'context_type', 'context_text', 'priority', 'status',
            'due_date', 'assigned_to', 'related_email_id',
            'related_milestone_id', 'agent_action_taken',
            'agent_action_result', 'agent_action_timestamp'
        ]

        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                values.append(data[field])

        # Handle completed_at timestamp
        if data.get('status') == 'completed' and 'completed_at' not in update_fields:
            update_fields.append("completed_at = ?")
            values.append(datetime.now().isoformat())

        if not update_fields:
            conn.close()
            return False

        values.append(context_id)
        query = f"UPDATE project_context SET {', '.join(update_fields)} WHERE context_id = ?"

        cursor.execute(query, values)
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def delete_context(self, context_id: int) -> bool:
        """Delete a context item"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM project_context WHERE context_id = ?", (context_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def complete_task(self, context_id: int) -> bool:
        """Mark a task as completed"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE project_context
            SET status = 'completed',
                completed_at = ?
            WHERE context_id = ?
        """, (datetime.now().isoformat(), context_id))

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def get_tasks_by_assigned(self, assigned_to: str, status: str = 'active') -> List[Dict[str, Any]]:
        """Get tasks assigned to a specific person"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                c.*,
                p.project_code,
                p.project_title,
                COALESCE(pr.client_company, 'Unknown')
            FROM project_context c
            JOIN proposals p ON c.proposal_id = p.project_id
            WHERE c.assigned_to = ?
              AND c.status = ?
              AND c.context_type = 'task'
            ORDER BY c.due_date ASC NULLS LAST, c.priority DESC
        """, (assigned_to, status))

        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return tasks

    def get_overdue_tasks(self) -> List[Dict[str, Any]]:
        """Get all overdue tasks across all proposals"""
        conn = self._get_connection()
        cursor = conn.cursor()

        today = date.today().isoformat()

        cursor.execute("""
            SELECT
                c.*,
                p.project_code,
                p.project_title,
                COALESCE(pr.client_company, 'Unknown')
            FROM project_context c
            JOIN proposals p ON c.proposal_id = p.project_id
            WHERE c.context_type = 'task'
              AND c.status = 'active'
              AND c.due_date < ?
            ORDER BY c.due_date ASC
        """, (today,))

        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return tasks

    def get_upcoming_tasks(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get tasks due in the next N days"""
        conn = self._get_connection()
        cursor = conn.cursor()

        today = date.today()
        future_date = (today + timedelta(days=days_ahead)).isoformat()
        today_str = today.isoformat()

        cursor.execute("""
            SELECT
                c.*,
                p.project_code,
                p.project_title,
                COALESCE(pr.client_company, 'Unknown')
            FROM project_context c
            JOIN proposals p ON c.proposal_id = p.project_id
            WHERE c.context_type = 'task'
              AND c.status = 'active'
              AND c.due_date BETWEEN ? AND ?
            ORDER BY c.due_date ASC
        """, (today_str, future_date))

        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return tasks

    def log_agent_action(self, context_id: int, action_taken: str,
                         action_result: Dict[str, Any]) -> bool:
        """
        Log an agent action on a context item
        action_result should be a dict that will be stored as JSON
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE project_context
            SET agent_action_taken = ?,
                agent_action_result = ?,
                agent_action_timestamp = ?
            WHERE context_id = ?
        """, (
            action_taken,
            json.dumps(action_result),
            datetime.now().isoformat(),
            context_id
        ))

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def get_context_summary(self, proposal_id: int) -> Dict[str, Any]:
        """
        Generate context summary for a proposal
        Returns counts by type, status, priority
        """
        contexts = self.get_context_by_proposal(proposal_id)

        summary = {
            'proposal_id': proposal_id,
            'total_items': len(contexts),
            'by_type': {},
            'by_status': {},
            'by_priority': {},
            'active_tasks': 0,
            'overdue_tasks': 0,
            'agent_actions': 0
        }

        today = date.today()

        for context in contexts:
            # Type breakdown
            context_type = context['context_type']
            summary['by_type'][context_type] = summary['by_type'].get(context_type, 0) + 1

            # Status breakdown
            status = context['status']
            summary['by_status'][status] = summary['by_status'].get(status, 0) + 1

            # Priority breakdown
            priority = context['priority']
            summary['by_priority'][priority] = summary['by_priority'].get(priority, 0) + 1

            # Task-specific counts
            if context_type == 'task':
                if status == 'active':
                    summary['active_tasks'] += 1

                    # Check if overdue
                    if context['due_date']:
                        due = datetime.strptime(context['due_date'], '%Y-%m-%d').date()
                        if due < today:
                            summary['overdue_tasks'] += 1

            # Agent action count
            if context['agent_action_taken']:
                summary['agent_actions'] += 1

        return summary

    def get_notes_by_proposal(self, proposal_id: int) -> List[Dict[str, Any]]:
        """Get all notes for a proposal (convenience method)"""
        return self.get_context_by_proposal(proposal_id, context_type='note')

    def get_tasks_by_proposal(self, proposal_id: int) -> List[Dict[str, Any]]:
        """Get all tasks for a proposal (convenience method)"""
        return self.get_context_by_proposal(proposal_id, context_type='task')

    def get_reminders_by_proposal(self, proposal_id: int) -> List[Dict[str, Any]]:
        """Get all reminders for a proposal (convenience method)"""
        return self.get_context_by_proposal(proposal_id, context_type='reminder')

    def get_decisions_by_proposal(self, proposal_id: int) -> List[Dict[str, Any]]:
        """Get all decisions for a proposal (convenience method)"""
        return self.get_context_by_proposal(proposal_id, context_type='decision')

    def search_context(self, search_term: str, proposal_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search context items by text content
        Optionally filter by proposal_id
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        search_pattern = f"%{search_term}%"

        query = """
            SELECT
                c.*,
                p.project_code,
                p.project_title
            FROM project_context c
            JOIN proposals p ON c.proposal_id = p.project_id
            WHERE c.context_text LIKE ?
        """
        params = [search_pattern]

        if proposal_id:
            query += " AND c.proposal_id = ?"
            params.append(proposal_id)

        query += " ORDER BY c.created_at DESC"

        cursor.execute(query, params)

        contexts = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return contexts
