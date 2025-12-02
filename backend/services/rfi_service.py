"""
Service layer for project RFIs (Requests for Information)
Handles RFI tracking, response management, and status updates

Updated 2025-11-26: Aligned with actual rfis table schema
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
import sqlite3


class RFIService:
    """
    Service for managing RFIs (Requests for Information)

    RFI Workflow:
    1. Client sends RFI (CC: rfi@bensley.com)
    2. System auto-detects and creates RFI record
    3. PM assigned based on project/specialty
    4. 48-hour SLA tracked
    5. PM marks as responded when done
    """

    # Default SLA in hours
    DEFAULT_SLA_HOURS = 48

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self):
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_rfis_by_project(self, project_code: str) -> List[Dict[str, Any]]:
        """Get all RFIs for a specific project"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                r.*,
                e.subject as email_subject,
                e.sender_email as email_sender,
                e.date as email_date,
                CAST(JULIANDAY('now') - JULIANDAY(r.date_sent) AS INTEGER) as days_open,
                CASE
                    WHEN r.status = 'open' AND date(r.date_due) < date('now') THEN 1
                    ELSE 0
                END as is_overdue
            FROM rfis r
            LEFT JOIN emails e ON r.extracted_from_email_id = e.email_id
            WHERE r.project_code = ?
            ORDER BY r.date_sent DESC
        """, (project_code,))

        rfis = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return rfis

    def get_rfis_by_project_id(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all RFIs for a specific project by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                r.*,
                e.subject as email_subject,
                e.sender_email as email_sender,
                CAST(JULIANDAY('now') - JULIANDAY(r.date_sent) AS INTEGER) as days_open,
                CASE
                    WHEN r.status = 'open' AND date(r.date_due) < date('now') THEN 1
                    ELSE 0
                END as is_overdue
            FROM rfis r
            LEFT JOIN emails e ON r.extracted_from_email_id = e.email_id
            WHERE r.project_id = ?
            ORDER BY r.date_sent DESC
        """, (project_id,))

        rfis = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return rfis

    # Alias for backward compatibility with old API
    def get_rfis_by_proposal(self, proposal_id: int) -> List[Dict[str, Any]]:
        """Alias for get_rfis_by_project_id (backward compatibility)"""
        return self.get_rfis_by_project_id(proposal_id)

    def get_rfi_by_id(self, rfi_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific RFI by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                r.*,
                e.subject as email_subject,
                e.sender_email as email_sender,
                e.body_full as email_body,
                CAST(JULIANDAY('now') - JULIANDAY(r.date_sent) AS INTEGER) as days_open,
                CASE
                    WHEN r.status = 'open' AND date(r.date_due) < date('now') THEN 1
                    ELSE 0
                END as is_overdue
            FROM rfis r
            LEFT JOIN emails e ON r.extracted_from_email_id = e.email_id
            WHERE r.rfi_id = ?
        """, (rfi_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_rfi_by_number(self, rfi_number: str) -> Optional[Dict[str, Any]]:
        """Get an RFI by its unique RFI number"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM rfis WHERE rfi_number = ?
        """, (rfi_number,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def create_rfi(self, data: Dict[str, Any]) -> int:
        """
        Create a new RFI

        Required fields:
        - project_code OR project_id
        - subject

        Optional fields:
        - rfi_number (auto-generated if not provided)
        - description
        - date_sent (defaults to now)
        - date_due (defaults to date_sent + 48 hours)
        - priority (defaults to 'normal')
        - sender_email, sender_name
        - extracted_from_email_id (link to source email)
        - assigned_pm_id (who's responsible)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get project info if only project_code provided
        project_id = data.get('project_id')
        project_code = data.get('project_code')

        if project_code and not project_id:
            cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
            row = cursor.fetchone()
            if row:
                project_id = row['project_id']
        elif project_id and not project_code:
            cursor.execute("SELECT project_code FROM projects WHERE project_id = ?", (project_id,))
            row = cursor.fetchone()
            if row:
                project_code = row['project_code']

        # Auto-generate RFI number if not provided
        rfi_number = data.get('rfi_number')
        if not rfi_number and project_code:
            rfi_number = self._generate_rfi_number(project_code, conn)

        # Set dates
        date_sent = data.get('date_sent') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Calculate due date (48 hours from sent)
        if data.get('date_due'):
            date_due = data['date_due']
        else:
            sent_dt = datetime.strptime(date_sent[:10], '%Y-%m-%d')
            due_dt = sent_dt + timedelta(hours=self.DEFAULT_SLA_HOURS)
            date_due = due_dt.strftime('%Y-%m-%d')

        cursor.execute("""
            INSERT INTO rfis (
                project_id,
                project_code,
                rfi_number,
                subject,
                description,
                date_sent,
                date_due,
                status,
                priority,
                sender_email,
                sender_name,
                extracted_from_email_id,
                extraction_confidence,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            project_id,
            project_code,
            rfi_number,
            data.get('subject', 'Untitled RFI'),
            data.get('description', ''),
            date_sent,
            date_due,
            data.get('status', 'open'),
            data.get('priority', 'normal'),
            data.get('sender_email'),
            data.get('sender_name'),
            data.get('extracted_from_email_id'),
            data.get('extraction_confidence', 0.5)
        ))

        rfi_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return rfi_id

    def _generate_rfi_number(self, project_code: str, conn: sqlite3.Connection) -> str:
        """Generate RFI number like 'BK-033-RFI-001'"""
        cursor = conn.cursor()

        # Count existing RFIs for this project
        cursor.execute("SELECT COUNT(*) as count FROM rfis WHERE project_code = ?", (project_code,))
        count = cursor.fetchone()['count']

        # Clean project code for RFI number
        clean_code = project_code.replace(' ', '-')
        rfi_number = f"{clean_code}-RFI-{count + 1:03d}"
        return rfi_number

    def update_rfi(self, rfi_id: int, data: Dict[str, Any]) -> bool:
        """Update an existing RFI"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build dynamic update query
        update_fields = []
        values = []

        allowed_fields = [
            'rfi_number', 'subject', 'description',
            'date_sent', 'date_due', 'date_responded',
            'status', 'priority',
            'sender_email', 'sender_name',
            'response_email_id', 'extraction_confidence',
            'assigned_pm_id', 'assigned_to'  # PM assignment fields
        ]

        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                values.append(data[field])

        if not update_fields:
            conn.close()
            return False

        values.append(rfi_id)
        query = f"UPDATE rfis SET {', '.join(update_fields)} WHERE rfi_id = ?"

        cursor.execute(query, values)
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def mark_responded(self, rfi_id: int, response_email_id: Optional[int] = None) -> bool:
        """
        Mark an RFI as responded

        Args:
            rfi_id: The RFI to mark as responded
            response_email_id: Optional email ID of the response

        Returns:
            True if successful
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE rfis
            SET status = 'responded',
                date_responded = datetime('now'),
                response_email_id = ?
            WHERE rfi_id = ?
        """, (response_email_id, rfi_id))

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def close_rfi(self, rfi_id: int) -> bool:
        """Mark an RFI as closed"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE rfis
            SET status = 'closed'
            WHERE rfi_id = ?
        """, (rfi_id,))

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def delete_rfi(self, rfi_id: int) -> bool:
        """Delete an RFI"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM rfis WHERE rfi_id = ?", (rfi_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def get_open_rfis(self) -> List[Dict[str, Any]]:
        """Get all open RFIs across all projects"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                r.*,
                p.project_title,
                e.subject as email_subject,
                CAST(JULIANDAY('now') - JULIANDAY(r.date_sent) AS INTEGER) as days_open,
                CASE
                    WHEN date(r.date_due) < date('now') THEN 1
                    ELSE 0
                END as is_overdue
            FROM rfis r
            LEFT JOIN projects p ON r.project_id = p.project_id
            LEFT JOIN emails e ON r.extracted_from_email_id = e.email_id
            WHERE r.status = 'open'
            ORDER BY r.date_due ASC
        """)

        rfis = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return rfis

    # Alias for backward compatibility
    def get_unanswered_rfis(self) -> List[Dict[str, Any]]:
        """Alias for get_open_rfis (backward compatibility)"""
        return self.get_open_rfis()

    def get_overdue_rfis(self) -> List[Dict[str, Any]]:
        """Get all RFIs that are past their due date"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                r.*,
                p.project_title,
                p.project_code,
                e.subject as email_subject,
                CAST(JULIANDAY('now') - JULIANDAY(r.date_sent) AS INTEGER) as days_open,
                CAST(JULIANDAY('now') - JULIANDAY(r.date_due) AS INTEGER) as days_overdue
            FROM rfis r
            LEFT JOIN projects p ON r.project_id = p.project_id
            LEFT JOIN emails e ON r.extracted_from_email_id = e.email_id
            WHERE r.status = 'open'
            AND date(r.date_due) < date('now')
            ORDER BY r.date_due ASC
        """)

        rfis = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return rfis

    def get_rfis_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get RFIs filtered by status"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                r.*,
                p.project_title,
                p.project_code,
                CAST(JULIANDAY('now') - JULIANDAY(r.date_sent) AS INTEGER) as days_open
            FROM rfis r
            LEFT JOIN projects p ON r.project_id = p.project_id
            WHERE r.status = ?
            ORDER BY r.date_sent DESC
        """, (status,))

        rfis = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return rfis

    def get_rfis_by_priority(self, priority: str) -> List[Dict[str, Any]]:
        """Get RFIs filtered by priority"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                r.*,
                p.project_title,
                p.project_code,
                CAST(JULIANDAY('now') - JULIANDAY(r.date_sent) AS INTEGER) as days_open
            FROM rfis r
            LEFT JOIN projects p ON r.project_id = p.project_id
            WHERE r.priority = ?
            ORDER BY r.date_sent DESC
        """, (priority,))

        rfis = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return rfis

    def get_rfi_summary(self, project_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate RFI summary statistics

        Args:
            project_code: Optional - if provided, stats for that project only

        Returns:
            Summary with counts by status, priority, overdue stats
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Base query
        where_clause = "WHERE 1=1"
        params = []

        if project_code:
            where_clause += " AND project_code = ?"
            params.append(project_code)

        # Get totals by status
        cursor.execute(f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_count,
                SUM(CASE WHEN status = 'responded' THEN 1 ELSE 0 END) as responded_count,
                SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed_count,
                SUM(CASE WHEN status = 'open' AND date(date_due) < date('now') THEN 1 ELSE 0 END) as overdue_count,
                SUM(CASE WHEN priority = 'high' AND status = 'open' THEN 1 ELSE 0 END) as high_priority_open,
                AVG(CASE WHEN status = 'open'
                    THEN JULIANDAY('now') - JULIANDAY(date_sent)
                    ELSE NULL END) as avg_days_open
            FROM rfis
            {where_clause}
        """, params)

        row = cursor.fetchone()

        summary = {
            'total_rfis': row['total'] or 0,
            'open': row['open_count'] or 0,
            'responded': row['responded_count'] or 0,
            'closed': row['closed_count'] or 0,
            'overdue': row['overdue_count'] or 0,
            'high_priority_open': row['high_priority_open'] or 0,
            'avg_days_open': round(row['avg_days_open'] or 0, 1),
            'sla_hours': self.DEFAULT_SLA_HOURS
        }

        conn.close()
        return summary

    def get_rfi_stats_for_dashboard(self) -> Dict[str, Any]:
        """Get RFI statistics formatted for dashboard display"""
        summary = self.get_rfi_summary()
        overdue = self.get_overdue_rfis()

        return {
            'summary': summary,
            'overdue_rfis': overdue[:5],  # Top 5 overdue
            'needs_attention': summary['overdue'] > 0 or summary['high_priority_open'] > 0,
            'alert_message': self._generate_alert_message(summary)
        }

    def _generate_alert_message(self, summary: Dict[str, Any]) -> Optional[str]:
        """Generate alert message if RFIs need attention"""
        messages = []

        if summary['overdue'] > 0:
            messages.append(f"{summary['overdue']} RFI(s) overdue!")

        if summary['high_priority_open'] > 0:
            messages.append(f"{summary['high_priority_open']} high-priority RFI(s) open")

        return " | ".join(messages) if messages else None
