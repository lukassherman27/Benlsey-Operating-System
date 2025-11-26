"""
Service layer for project outreach tracking
Handles contact history, follow-ups, and communication logging
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
import sqlite3


class OutreachService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self):
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_outreach_by_proposal(self, proposal_id: int) -> List[Dict[str, Any]]:
        """Get all outreach records for a specific proposal"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                o.*,
                e.subject as email_subject,
                m.meeting_title
            FROM project_outreach o
            LEFT JOIN emails e ON o.related_email_id = e.email_id
            LEFT JOIN project_meetings m ON o.related_meeting_id = m.meeting_id
            WHERE o.proposal_id = ?
            ORDER BY o.contact_date DESC
        """, (proposal_id,))

        outreach = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return outreach

    def get_outreach_by_id(self, outreach_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific outreach record by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM project_outreach
            WHERE outreach_id = ?
        """, (outreach_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def create_outreach(self, data: Dict[str, Any]) -> int:
        """Create a new outreach record"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO project_outreach (
                proposal_id,
                contact_date,
                contact_type,
                contact_person,
                contact_person_role,
                contact_method,
                subject,
                summary,
                outcome,
                next_action,
                next_action_date,
                related_email_id,
                related_meeting_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('proposal_id'),
            data.get('contact_date') or date.today().isoformat(),
            data.get('contact_type'),
            data.get('contact_person'),
            data.get('contact_person_role'),
            data.get('contact_method'),
            data.get('subject'),
            data.get('summary'),
            data.get('outcome'),
            data.get('next_action'),
            data.get('next_action_date'),
            data.get('related_email_id'),
            data.get('related_meeting_id')
        ))

        outreach_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return outreach_id

    def update_outreach(self, outreach_id: int, data: Dict[str, Any]) -> bool:
        """Update an existing outreach record"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build dynamic update query
        update_fields = []
        values = []

        allowed_fields = [
            'contact_date', 'contact_type', 'contact_person',
            'contact_person_role', 'contact_method', 'subject',
            'summary', 'outcome', 'next_action', 'next_action_date',
            'related_email_id', 'related_meeting_id'
        ]

        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                values.append(data[field])

        if not update_fields:
            conn.close()
            return False

        values.append(outreach_id)
        query = f"UPDATE project_outreach SET {', '.join(update_fields)} WHERE outreach_id = ?"

        cursor.execute(query, values)
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def delete_outreach(self, outreach_id: int) -> bool:
        """Delete an outreach record"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM project_outreach WHERE outreach_id = ?", (outreach_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def get_outreach_by_contact_type(self, proposal_id: int, contact_type: str) -> List[Dict[str, Any]]:
        """Get outreach records filtered by contact type"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM project_outreach
            WHERE proposal_id = ? AND contact_type = ?
            ORDER BY contact_date DESC
        """, (proposal_id, contact_type))

        outreach = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return outreach

    def get_outreach_needing_followup(self) -> List[Dict[str, Any]]:
        """
        Get all outreach records that need follow-up action
        Returns records with next_action_date in the past or today
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        today = date.today().isoformat()

        cursor.execute("""
            SELECT
                o.*,
                p.project_code,
                p.project_title,
                COALESCE(pr.client_company, 'Unknown')
            FROM project_outreach o
            JOIN proposals p ON o.proposal_id = p.project_id
            WHERE o.next_action_date <= ?
              AND o.next_action IS NOT NULL
            ORDER BY o.next_action_date ASC
        """, (today,))

        outreach = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return outreach

    def get_upcoming_followups(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get follow-ups scheduled in the next N days"""
        conn = self._get_connection()
        cursor = conn.cursor()

        today = date.today()
        future_date = (today + timedelta(days=days_ahead)).isoformat()
        today_str = today.isoformat()

        cursor.execute("""
            SELECT
                o.*,
                p.project_code,
                p.project_title,
                COALESCE(pr.client_company, 'Unknown')
            FROM project_outreach o
            JOIN proposals p ON o.proposal_id = p.project_id
            WHERE o.next_action_date BETWEEN ? AND ?
              AND o.next_action IS NOT NULL
            ORDER BY o.next_action_date ASC
        """, (today_str, future_date))

        outreach = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return outreach

    def get_last_contact(self, proposal_id: int) -> Optional[Dict[str, Any]]:
        """Get the most recent contact/outreach for a proposal"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM project_outreach
            WHERE proposal_id = ?
            ORDER BY contact_date DESC
            LIMIT 1
        """, (proposal_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_outreach_summary(self, proposal_id: int) -> Dict[str, Any]:
        """
        Generate outreach summary for a proposal
        Returns counts by type, outcome, and contact frequency
        """
        outreach = self.get_outreach_by_proposal(proposal_id)

        summary = {
            'proposal_id': proposal_id,
            'total_contacts': len(outreach),
            'by_type': {},
            'by_outcome': {},
            'by_contact_person': {},
            'needs_followup': 0,
            'last_contact_date': None,
            'days_since_contact': None
        }

        today = date.today()

        for contact in outreach:
            # Type breakdown
            contact_type = contact['contact_type']
            summary['by_type'][contact_type] = summary['by_type'].get(contact_type, 0) + 1

            # Outcome breakdown
            outcome = contact['outcome'] or 'unknown'
            summary['by_outcome'][outcome] = summary['by_outcome'].get(outcome, 0) + 1

            # Contact person breakdown
            person = contact['contact_person'] or 'unknown'
            summary['by_contact_person'][person] = summary['by_contact_person'].get(person, 0) + 1

            # Follow-up needed
            if contact['next_action_date']:
                next_date = datetime.strptime(contact['next_action_date'], '%Y-%m-%d').date()
                if next_date <= today:
                    summary['needs_followup'] += 1

        # Calculate last contact
        if outreach:
            last_contact = outreach[0]  # Already sorted by date DESC
            summary['last_contact_date'] = last_contact['contact_date']

            contact_date = datetime.strptime(last_contact['contact_date'], '%Y-%m-%d').date()
            summary['days_since_contact'] = (today - contact_date).days

        return summary

    def get_contact_history_timeline(self, proposal_id: int) -> List[Dict[str, Any]]:
        """
        Get chronological contact history for timeline visualization
        Includes outreach records and related emails/meetings
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                o.*,
                e.subject as email_subject,
                e.sender_email,
                m.meeting_title,
                m.scheduled_date as meeting_date
            FROM project_outreach o
            LEFT JOIN emails e ON o.related_email_id = e.email_id
            LEFT JOIN project_meetings m ON o.related_meeting_id = m.meeting_id
            WHERE o.proposal_id = ?
            ORDER BY o.contact_date ASC
        """, (proposal_id,))

        timeline = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return timeline

    def bulk_create_from_emails(self, proposal_id: int, email_ids: List[int]) -> int:
        """
        Bulk create outreach records from email communications
        Useful for importing historical email data into outreach tracking
        Returns count of records created
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        count = 0

        for email_id in email_ids:
            # Get email details
            cursor.execute("""
                SELECT subject, sender_email, date
                FROM emails
                WHERE email_id = ?
            """, (email_id,))

            email = cursor.fetchone()
            if not email:
                continue

            # Create outreach record
            cursor.execute("""
                INSERT INTO project_outreach (
                    proposal_id,
                    contact_date,
                    contact_type,
                    contact_method,
                    subject,
                    related_email_id
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                proposal_id,
                email['date'][:10],  # Extract date from datetime
                'email',
                'received_email',
                email['subject'],
                email_id
            ))

            count += 1

        conn.commit()
        conn.close()

        return count

    def search_outreach(self, search_term: str, proposal_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search outreach records by subject, summary, or contact person
        Optionally filter by proposal_id
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        search_pattern = f"%{search_term}%"

        query = """
            SELECT
                o.*,
                p.project_code,
                p.project_title
            FROM project_outreach o
            JOIN proposals p ON o.proposal_id = p.project_id
            WHERE (
                o.subject LIKE ?
                OR o.summary LIKE ?
                OR o.contact_person LIKE ?
            )
        """
        params = [search_pattern, search_pattern, search_pattern]

        if proposal_id:
            query += " AND o.proposal_id = ?"
            params.append(proposal_id)

        query += " ORDER BY o.contact_date DESC"

        cursor.execute(query, params)

        outreach = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return outreach
