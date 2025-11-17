"""
Service layer for project RFIs (Requests for Information)
Handles question tracking, response management, and status updates
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date
import sqlite3


class RFIService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self):
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_rfis_by_proposal(self, proposal_id: int) -> List[Dict[str, Any]]:
        """Get all RFIs for a specific proposal"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                r.*,
                e.subject as email_subject,
                e.sender_email
            FROM project_rfis r
            LEFT JOIN emails e ON r.email_id = e.email_id
            WHERE r.proposal_id = ?
            ORDER BY r.asked_date DESC
        """, (proposal_id,))

        rfis = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return rfis

    def get_rfi_by_id(self, rfi_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific RFI by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM project_rfis
            WHERE rfi_id = ?
        """, (rfi_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_rfi_by_number(self, rfi_number: str) -> Optional[Dict[str, Any]]:
        """Get an RFI by its unique RFI number"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM project_rfis
            WHERE rfi_number = ?
        """, (rfi_number,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def create_rfi(self, data: Dict[str, Any]) -> int:
        """Create a new RFI"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Auto-generate RFI number if not provided
        rfi_number = data.get('rfi_number')
        if not rfi_number:
            rfi_number = self._generate_rfi_number(data['proposal_id'], conn)

        cursor.execute("""
            INSERT INTO project_rfis (
                proposal_id,
                email_id,
                rfi_number,
                question,
                asked_by,
                asked_date,
                response,
                responded_by,
                responded_date,
                status,
                priority,
                category,
                days_waiting
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('proposal_id'),
            data.get('email_id'),
            rfi_number,
            data.get('question'),
            data.get('asked_by'),
            data.get('asked_date'),
            data.get('response'),
            data.get('responded_by'),
            data.get('responded_date'),
            data.get('status', 'unanswered'),
            data.get('priority', 'normal'),
            data.get('category'),
            data.get('days_waiting', 0)
        ))

        rfi_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return rfi_id

    def _generate_rfi_number(self, proposal_id: int, conn: sqlite3.Connection) -> str:
        """Generate RFI number like 'BK033-RFI-001'"""
        cursor = conn.cursor()

        # Get project code (from unified projects table after migration 015)
        cursor.execute("SELECT project_code FROM projects WHERE proposal_id = ?", (proposal_id,))
        row = cursor.fetchone()
        project_code = row['project_code'] if row else 'UNK'

        # Count existing RFIs for this proposal
        cursor.execute("SELECT COUNT(*) as count FROM project_rfis WHERE proposal_id = ?", (proposal_id,))
        count = cursor.fetchone()['count']

        rfi_number = f"{project_code}-RFI-{count + 1:03d}"
        return rfi_number

    def update_rfi(self, rfi_id: int, data: Dict[str, Any]) -> bool:
        """Update an existing RFI"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build dynamic update query
        update_fields = []
        values = []

        allowed_fields = [
            'email_id', 'rfi_number', 'question', 'asked_by', 'asked_date',
            'response', 'responded_by', 'responded_date', 'status',
            'priority', 'category', 'days_waiting'
        ]

        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                values.append(data[field])

        if not update_fields:
            conn.close()
            return False

        values.append(rfi_id)
        query = f"UPDATE project_rfis SET {', '.join(update_fields)} WHERE rfi_id = ?"

        cursor.execute(query, values)
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def delete_rfi(self, rfi_id: int) -> bool:
        """Delete an RFI"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM project_rfis WHERE rfi_id = ?", (rfi_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def add_response(self, rfi_id: int, response: str, responded_by: str, responded_date: Optional[str] = None) -> bool:
        """
        Add a response to an RFI
        Automatically updates status to 'answered'
        """
        if not responded_date:
            responded_date = date.today().isoformat()

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE project_rfis
            SET response = ?,
                responded_by = ?,
                responded_date = ?,
                status = 'answered'
            WHERE rfi_id = ?
        """, (response, responded_by, responded_date, rfi_id))

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def get_unanswered_rfis(self) -> List[Dict[str, Any]]:
        """Get all unanswered RFIs across all proposals"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                r.*,
                p.project_code,
                p.project_name,
                p.client_company
            FROM project_rfis r
            JOIN projects p ON r.proposal_id = p.proposal_id
            WHERE r.status = 'unanswered'
            ORDER BY r.priority DESC, r.asked_date ASC
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
                p.project_code,
                p.project_name,
                p.client_company
            FROM project_rfis r
            JOIN projects p ON r.proposal_id = p.proposal_id
            WHERE r.status = ?
            ORDER BY r.asked_date DESC
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
                p.project_code,
                p.project_name,
                p.client_company
            FROM project_rfis r
            JOIN projects p ON r.proposal_id = p.proposal_id
            WHERE r.priority = ?
            ORDER BY r.asked_date DESC
        """, (priority,))

        rfis = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return rfis

    def get_rfi_summary(self, proposal_id: int) -> Dict[str, Any]:
        """
        Generate RFI summary for a proposal
        Returns counts by status, priority, category
        """
        rfis = self.get_rfis_by_proposal(proposal_id)

        summary = {
            'proposal_id': proposal_id,
            'total_rfis': len(rfis),
            'unanswered': 0,
            'answered': 0,
            'pending_followup': 0,
            'closed': 0,
            'critical': 0,
            'high': 0,
            'normal': 0,
            'low': 0,
            'avg_days_waiting': 0,
            'by_category': {},
            'by_asked_by': {}
        }

        total_days = 0

        for rfi in rfis:
            # Status counts
            status = rfi['status']
            if status == 'unanswered':
                summary['unanswered'] += 1
            elif status == 'answered':
                summary['answered'] += 1
            elif status == 'pending_followup':
                summary['pending_followup'] += 1
            elif status == 'closed':
                summary['closed'] += 1

            # Priority counts
            priority = rfi['priority']
            if priority == 'critical':
                summary['critical'] += 1
            elif priority == 'high':
                summary['high'] += 1
            elif priority == 'normal':
                summary['normal'] += 1
            elif priority == 'low':
                summary['low'] += 1

            # Category breakdown
            category = rfi['category'] or 'uncategorized'
            summary['by_category'][category] = summary['by_category'].get(category, 0) + 1

            # Asked by breakdown
            asked_by = rfi['asked_by'] or 'unknown'
            summary['by_asked_by'][asked_by] = summary['by_asked_by'].get(asked_by, 0) + 1

            # Days waiting
            total_days += rfi['days_waiting'] or 0

        # Calculate average
        if summary['total_rfis'] > 0:
            summary['avg_days_waiting'] = total_days / summary['total_rfis']

        return summary

    def update_days_waiting(self) -> int:
        """
        Update days_waiting for all unanswered RFIs
        Returns count of RFIs updated
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        today = date.today()

        cursor.execute("""
            SELECT rfi_id, asked_date
            FROM project_rfis
            WHERE status = 'unanswered'
        """)

        rfis = cursor.fetchall()
        count = 0

        for rfi in rfis:
            asked = datetime.strptime(rfi['asked_date'], '%Y-%m-%d').date()
            days_waiting = (today - asked).days

            cursor.execute("""
                UPDATE project_rfis
                SET days_waiting = ?
                WHERE rfi_id = ?
            """, (days_waiting, rfi['rfi_id']))

            count += 1

        conn.commit()
        conn.close()

        return count
