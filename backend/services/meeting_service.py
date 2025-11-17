"""
Service layer for project meetings
Handles meeting scheduling, notes, and calendar integration
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
import sqlite3
import json


class MeetingService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self):
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_meetings_by_proposal(self, proposal_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all meetings for a specific proposal"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT * FROM project_meetings
            WHERE proposal_id = ?
        """
        params = [proposal_id]

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY scheduled_date DESC"

        cursor.execute(query, params)

        meetings = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return meetings

    def get_meeting_by_id(self, meeting_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific meeting by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM project_meetings
            WHERE meeting_id = ?
        """, (meeting_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def create_meeting(self, data: Dict[str, Any]) -> int:
        """Create a new meeting"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Convert attendees and action_items to JSON if they're dicts/lists
        attendees = data.get('attendees')
        if isinstance(attendees, (list, dict)):
            attendees = json.dumps(attendees)

        action_items = data.get('action_items')
        if isinstance(action_items, (list, dict)):
            action_items = json.dumps(action_items)

        cursor.execute("""
            INSERT INTO project_meetings (
                proposal_id,
                meeting_type,
                meeting_title,
                scheduled_date,
                duration_minutes,
                location,
                meeting_url,
                attendees,
                agenda,
                meeting_notes,
                action_items,
                status,
                calendar_event_id,
                reminder_sent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('proposal_id'),
            data.get('meeting_type'),
            data.get('meeting_title'),
            data.get('scheduled_date'),
            data.get('duration_minutes', 60),
            data.get('location'),
            data.get('meeting_url'),
            attendees,
            data.get('agenda'),
            data.get('meeting_notes'),
            action_items,
            data.get('status', 'scheduled'),
            data.get('calendar_event_id'),
            data.get('reminder_sent', 0)
        ))

        meeting_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return meeting_id

    def update_meeting(self, meeting_id: int, data: Dict[str, Any]) -> bool:
        """Update an existing meeting"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build dynamic update query
        update_fields = []
        values = []

        allowed_fields = [
            'meeting_type', 'meeting_title', 'scheduled_date',
            'duration_minutes', 'location', 'meeting_url',
            'attendees', 'agenda', 'meeting_notes', 'action_items',
            'status', 'calendar_event_id', 'reminder_sent'
        ]

        for field in allowed_fields:
            if field in data:
                value = data[field]

                # Convert to JSON if needed
                if field in ['attendees', 'action_items'] and isinstance(value, (list, dict)):
                    value = json.dumps(value)

                update_fields.append(f"{field} = ?")
                values.append(value)

        if not update_fields:
            conn.close()
            return False

        values.append(meeting_id)
        query = f"UPDATE project_meetings SET {', '.join(update_fields)} WHERE meeting_id = ?"

        cursor.execute(query, values)
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def delete_meeting(self, meeting_id: int) -> bool:
        """Delete a meeting"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM project_meetings WHERE meeting_id = ?", (meeting_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def add_meeting_notes(self, meeting_id: int, notes: str) -> bool:
        """Add or update meeting notes"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE project_meetings
            SET meeting_notes = ?
            WHERE meeting_id = ?
        """, (notes, meeting_id))

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def add_action_items(self, meeting_id: int, action_items: List[Dict[str, Any]]) -> bool:
        """Add or update action items for a meeting"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE project_meetings
            SET action_items = ?
            WHERE meeting_id = ?
        """, (json.dumps(action_items), meeting_id))

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def mark_meeting_completed(self, meeting_id: int) -> bool:
        """Mark a meeting as completed"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE project_meetings
            SET status = 'completed'
            WHERE meeting_id = ?
        """, (meeting_id,))

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def get_upcoming_meetings(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get meetings scheduled in the next N days"""
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now()
        future_date = (now + timedelta(days=days_ahead)).isoformat()
        now_str = now.isoformat()

        cursor.execute("""
            SELECT
                m.*,
                p.project_code,
                p.project_name,
                p.client_company
            FROM project_meetings m
            JOIN proposals p ON m.proposal_id = p.proposal_id
            WHERE m.scheduled_date BETWEEN ? AND ?
              AND m.status = 'scheduled'
            ORDER BY m.scheduled_date ASC
        """, (now_str, future_date))

        meetings = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return meetings

    def get_todays_meetings(self) -> List[Dict[str, Any]]:
        """Get meetings scheduled for today"""
        conn = self._get_connection()
        cursor = conn.cursor()

        today = date.today()
        start_of_day = datetime.combine(today, datetime.min.time()).isoformat()
        end_of_day = datetime.combine(today, datetime.max.time()).isoformat()

        cursor.execute("""
            SELECT
                m.*,
                p.project_code,
                p.project_name,
                p.client_company
            FROM project_meetings m
            JOIN proposals p ON m.proposal_id = p.proposal_id
            WHERE m.scheduled_date BETWEEN ? AND ?
              AND m.status = 'scheduled'
            ORDER BY m.scheduled_date ASC
        """, (start_of_day, end_of_day))

        meetings = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return meetings

    def get_past_meetings(self, proposal_id: int) -> List[Dict[str, Any]]:
        """Get all past/completed meetings for a proposal"""
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute("""
            SELECT * FROM project_meetings
            WHERE proposal_id = ?
              AND (
                  scheduled_date < ?
                  OR status = 'completed'
              )
            ORDER BY scheduled_date DESC
        """, (proposal_id, now))

        meetings = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return meetings

    def get_meetings_needing_reminders(self, hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """
        Get meetings that need reminders sent
        Returns meetings scheduled within next N hours that haven't had reminders sent
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now()
        future_time = (now + timedelta(hours=hours_ahead)).isoformat()
        now_str = now.isoformat()

        cursor.execute("""
            SELECT
                m.*,
                p.project_code,
                p.project_name,
                p.client_company
            FROM project_meetings m
            JOIN proposals p ON m.proposal_id = p.proposal_id
            WHERE m.scheduled_date BETWEEN ? AND ?
              AND m.status = 'scheduled'
              AND m.reminder_sent = 0
            ORDER BY m.scheduled_date ASC
        """, (now_str, future_time))

        meetings = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return meetings

    def mark_reminder_sent(self, meeting_id: int) -> bool:
        """Mark that a reminder has been sent for a meeting"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE project_meetings
            SET reminder_sent = 1
            WHERE meeting_id = ?
        """, (meeting_id,))

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def get_meeting_summary(self, proposal_id: int) -> Dict[str, Any]:
        """
        Generate meeting summary for a proposal
        Returns counts by status, type, and upcoming meetings
        """
        meetings = self.get_meetings_by_proposal(proposal_id)

        summary = {
            'proposal_id': proposal_id,
            'total_meetings': len(meetings),
            'scheduled': 0,
            'completed': 0,
            'cancelled': 0,
            'by_type': {},
            'next_meeting': None,
            'last_meeting': None
        }

        now = datetime.now()
        next_meeting_date = None
        last_meeting_date = None

        for meeting in meetings:
            # Status counts
            status = meeting['status']
            if status == 'scheduled':
                summary['scheduled'] += 1
            elif status == 'completed':
                summary['completed'] += 1
            elif status == 'cancelled':
                summary['cancelled'] += 1

            # Type breakdown
            meeting_type = meeting['meeting_type']
            summary['by_type'][meeting_type] = summary['by_type'].get(meeting_type, 0) + 1

            # Track next and last meetings
            meeting_date = datetime.fromisoformat(meeting['scheduled_date'])

            if meeting_date > now and status == 'scheduled':
                if not next_meeting_date or meeting_date < next_meeting_date:
                    next_meeting_date = meeting_date
                    summary['next_meeting'] = {
                        'meeting_id': meeting['meeting_id'],
                        'meeting_title': meeting['meeting_title'],
                        'scheduled_date': meeting['scheduled_date'],
                        'meeting_type': meeting['meeting_type']
                    }

            if meeting_date <= now or status == 'completed':
                if not last_meeting_date or meeting_date > last_meeting_date:
                    last_meeting_date = meeting_date
                    summary['last_meeting'] = {
                        'meeting_id': meeting['meeting_id'],
                        'meeting_title': meeting['meeting_title'],
                        'scheduled_date': meeting['scheduled_date'],
                        'meeting_type': meeting['meeting_type']
                    }

        return summary
