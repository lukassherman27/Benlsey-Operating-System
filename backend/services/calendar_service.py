"""
Calendar Service - Meeting management and natural language parsing

Handles:
- Creating meetings from natural language ("Add meeting for Cheval Blanc Tuesday 3pm")
- CRUD operations for meetings
- Calendar queries (today's meetings, upcoming, etc.)
- Meeting extraction from emails

Created: 2025-11-26 by Agent 5 (Bensley Brain Intelligence)
"""

import sqlite3
import os
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from openai import OpenAI
from pathlib import Path

# Database path
DB_PATH = os.getenv("DATABASE_PATH", "database/bensley_master.db")


class CalendarService:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self.client = None
        self._init_openai()

    def _init_openai(self):
        """Initialize OpenAI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # =========================================================================
    # NATURAL LANGUAGE MEETING CREATION
    # =========================================================================

    def parse_meeting_request(self, text: str) -> Dict[str, Any]:
        """
        Parse natural language meeting request.

        Examples:
        - "Add a meeting for Cheval Blanc project Tuesday 3pm - proposal discussion"
        - "Schedule concept design presentation for Wind Marjan next Friday"
        - "Meeting with John from Accor tomorrow at 10am about the hotel project"

        Returns:
            Dict with parsed meeting details
        """
        if not self.client:
            return self._fallback_parse(text)

        # Get project context for better matching
        projects = self._get_project_list()

        prompt = f"""Parse this meeting request and extract meeting details.

REQUEST: "{text}"

AVAILABLE PROJECTS (match to one if mentioned):
{json.dumps(projects[:50], indent=2)}

Extract and return JSON with these fields:
{{
    "title": "Meeting title (infer from context)",
    "meeting_type": "one of: proposal_discussion, concept_presentation, design_review, client_call, internal, site_visit, contract_negotiation, kickoff, progress_update, final_presentation, other",
    "meeting_date": "YYYY-MM-DD format (today is {datetime.now().strftime('%Y-%m-%d')}, use relative dates)",
    "start_time": "HH:MM format (24hr) or null",
    "end_time": "HH:MM format or null",
    "project_code": "matched project code or null",
    "project_name": "matched project name or null",
    "participants": ["list of participant names mentioned"],
    "location": "location if mentioned",
    "description": "any additional details"
}}

IMPORTANT:
- "Tuesday" means next Tuesday if today is past Tuesday
- "tomorrow" means {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}
- "next week" starts {(datetime.now() + timedelta(days=7-datetime.now().weekday())).strftime('%Y-%m-%d')}
- Match project names flexibly (e.g., "Cheval Blanc" matches "Cheval Blanc, Sazan, Albania")

Return ONLY valid JSON, no explanation."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You parse meeting requests into structured JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )

            content = response.choices[0].message.content.strip()
            # Clean JSON if wrapped in markdown
            if content.startswith("```"):
                content = re.sub(r'^```json?\s*', '', content)
                content = re.sub(r'\s*```$', '', content)

            return json.loads(content)

        except Exception as e:
            print(f"AI parsing failed: {e}")
            return self._fallback_parse(text)

    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Fallback regex-based parsing when AI unavailable"""
        result = {
            "title": text[:100],
            "meeting_type": "other",
            "meeting_date": None,
            "start_time": None,
            "participants": [],
            "project_code": None,
            "description": text
        }

        # Extract project code (BK-XXX)
        code_match = re.search(r'\b(\d{2}\s*BK-?\d{3})\b', text, re.IGNORECASE)
        if code_match:
            result["project_code"] = code_match.group(1).upper()

        # Extract time (3pm, 15:00, etc.)
        time_match = re.search(r'\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b', text, re.IGNORECASE)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            ampm = (time_match.group(3) or '').lower()

            if ampm == 'pm' and hour < 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0

            result["start_time"] = f"{hour:02d}:{minute:02d}"

        # Extract relative dates
        text_lower = text.lower()
        today = datetime.now()

        if 'today' in text_lower:
            result["meeting_date"] = today.strftime('%Y-%m-%d')
        elif 'tomorrow' in text_lower:
            result["meeting_date"] = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            # Check for day names
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for i, day in enumerate(days):
                if day in text_lower:
                    days_ahead = i - today.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    result["meeting_date"] = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
                    break

        # Detect meeting type from keywords
        type_keywords = {
            'proposal': 'proposal_discussion',
            'concept': 'concept_presentation',
            'design review': 'design_review',
            'call': 'client_call',
            'internal': 'internal',
            'site': 'site_visit',
            'contract': 'contract_negotiation',
            'kickoff': 'kickoff',
            'progress': 'progress_update',
            'presentation': 'concept_presentation'
        }

        for keyword, mtype in type_keywords.items():
            if keyword in text_lower:
                result["meeting_type"] = mtype
                break

        return result

    def _get_project_list(self) -> List[Dict]:
        """Get list of projects for matching"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT project_code, project_name, status
            FROM proposals
            WHERE status NOT IN ('lost', 'cancelled', 'rejected')
            ORDER BY created_at DESC
            LIMIT 100
        """)

        projects = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return projects

    # =========================================================================
    # MEETING CRUD OPERATIONS
    # =========================================================================

    def create_meeting(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new meeting from parsed data.

        Args:
            meeting_data: Dict with meeting details from parse_meeting_request()

        Returns:
            Dict with created meeting info
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Look up project if code provided
            project_id = None
            proposal_id = None

            if meeting_data.get('project_code'):
                cursor.execute("""
                    SELECT proposal_id, project_code, project_name
                    FROM proposals
                    WHERE project_code LIKE ?
                    LIMIT 1
                """, (f"%{meeting_data['project_code']}%",))
                row = cursor.fetchone()
                if row:
                    proposal_id = row['proposal_id']
                    meeting_data['project_code'] = row['project_code']
                    if not meeting_data.get('project_name'):
                        meeting_data['project_name'] = row['project_name']

            # Build title if not provided
            title = meeting_data.get('title')
            if not title and meeting_data.get('project_name'):
                title = f"{meeting_data['meeting_type'].replace('_', ' ').title()} - {meeting_data['project_name']}"
            elif not title:
                title = "New Meeting"

            # Insert meeting
            cursor.execute("""
                INSERT INTO meetings (
                    title, description, meeting_type,
                    meeting_date, start_time, end_time,
                    location, project_id, project_code, proposal_id,
                    participants, status, source, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', ?, 'chat')
            """, (
                title,
                meeting_data.get('description'),
                meeting_data.get('meeting_type', 'other'),
                meeting_data.get('meeting_date'),
                meeting_data.get('start_time'),
                meeting_data.get('end_time'),
                meeting_data.get('location'),
                project_id,
                meeting_data.get('project_code'),
                proposal_id,
                json.dumps(meeting_data.get('participants', [])),
                meeting_data.get('source', 'chat_input')
            ))

            meeting_id = cursor.lastrowid
            conn.commit()

            return {
                'success': True,
                'meeting_id': meeting_id,
                'title': title,
                'date': meeting_data.get('meeting_date'),
                'time': meeting_data.get('start_time'),
                'project_code': meeting_data.get('project_code'),
                'message': f"Meeting scheduled: {title} on {meeting_data.get('meeting_date')} at {meeting_data.get('start_time') or 'TBD'}"
            }

        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to create meeting: {e}"
            }
        finally:
            conn.close()

    def add_meeting_from_chat(self, user_input: str) -> Dict[str, Any]:
        """
        Main entry point: Parse natural language and create meeting.

        Args:
            user_input: Natural language meeting request

        Returns:
            Dict with result
        """
        # Parse the request
        parsed = self.parse_meeting_request(user_input)

        if not parsed.get('meeting_date'):
            return {
                'success': False,
                'parsed': parsed,
                'message': "Could not determine meeting date. Please specify when (e.g., 'Tuesday', 'tomorrow', 'Dec 5')"
            }

        # Create the meeting
        parsed['source'] = 'chat_input'
        result = self.create_meeting(parsed)
        result['parsed'] = parsed

        return result

    # =========================================================================
    # CALENDAR QUERIES
    # =========================================================================

    def get_meetings_for_date(self, date: str) -> List[Dict]:
        """Get all meetings for a specific date"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                m.*,
                p.project_name as linked_project_name
            FROM meetings m
            LEFT JOIN proposals p ON m.proposal_id = p.proposal_id
            WHERE m.meeting_date = ?
            AND m.status NOT IN ('cancelled')
            ORDER BY m.start_time
        """, (date,))

        meetings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return meetings

    def get_today_meetings(self) -> List[Dict]:
        """Get today's meetings"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.get_meetings_for_date(today)

    def get_upcoming_meetings(self, days: int = 7) -> List[Dict]:
        """Get meetings in the next N days"""
        conn = self._get_connection()
        cursor = conn.cursor()

        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

        cursor.execute("""
            SELECT
                m.*,
                p.project_name as linked_project_name
            FROM meetings m
            LEFT JOIN proposals p ON m.proposal_id = p.proposal_id
            WHERE m.meeting_date BETWEEN ? AND ?
            AND m.status NOT IN ('cancelled')
            ORDER BY m.meeting_date, m.start_time
        """, (start_date, end_date))

        meetings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return meetings

    def get_meetings_for_project(self, project_code: str) -> List[Dict]:
        """Get all meetings for a project, including linked transcript data"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get meetings with LEFT JOIN to transcripts
        # Join by transcript_id OR by matching project_code
        cursor.execute("""
            SELECT
                m.*,
                COALESCE(t.id, t2.id) as transcript_id,
                COALESCE(t.summary, t2.summary) as transcript_summary,
                COALESCE(t.polished_summary, t2.polished_summary) as transcript_polished_summary,
                COALESCE(t.key_points, t2.key_points) as transcript_key_points,
                COALESCE(t.action_items, t2.action_items) as transcript_action_items,
                COALESCE(t.duration_seconds, t2.duration_seconds) as transcript_duration
            FROM meetings m
            LEFT JOIN meeting_transcripts t ON m.transcript_id = t.id
            LEFT JOIN meeting_transcripts t2 ON (
                t2.detected_project_code LIKE '%' || ? || '%'
                AND DATE(t2.meeting_date) = DATE(m.meeting_date)
                AND m.transcript_id IS NULL
            )
            WHERE m.project_code LIKE ?
            ORDER BY m.meeting_date DESC, m.start_time
        """, (project_code, f"%{project_code}%",))

        meetings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return meetings

    def update_meeting(self, meeting_id: int, updates: Dict) -> Dict:
        """Update a meeting"""
        conn = self._get_connection()
        cursor = conn.cursor()

        allowed_fields = [
            'title', 'description', 'meeting_type', 'meeting_date',
            'start_time', 'end_time', 'location', 'status', 'notes', 'outcome'
        ]

        set_clauses = []
        params = []

        for field, value in updates.items():
            if field in allowed_fields:
                set_clauses.append(f"{field} = ?")
                params.append(value)

        if not set_clauses:
            return {'success': False, 'message': 'No valid fields to update'}

        set_clauses.append("updated_at = datetime('now')")
        params.append(meeting_id)

        try:
            cursor.execute(f"""
                UPDATE meetings
                SET {', '.join(set_clauses)}
                WHERE meeting_id = ?
            """, params)

            conn.commit()
            return {'success': True, 'message': 'Meeting updated'}

        except Exception as e:
            return {'success': False, 'message': str(e)}
        finally:
            conn.close()

    def delete_meeting(self, meeting_id: int) -> Dict:
        """Delete (cancel) a meeting"""
        return self.update_meeting(meeting_id, {'status': 'cancelled'})


# CLI for testing
if __name__ == '__main__':
    import sys

    service = CalendarService()

    if len(sys.argv) > 1:
        # Parse command line input
        user_input = ' '.join(sys.argv[1:])
        print(f"\n📅 Processing: {user_input}\n")

        result = service.add_meeting_from_chat(user_input)

        if result['success']:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")

        print(f"\nParsed data: {json.dumps(result.get('parsed', {}), indent=2)}")

    else:
        # Interactive mode
        print("=" * 60)
        print("📅 CALENDAR SERVICE - Add Meetings via Chat")
        print("=" * 60)
        print("\nExamples:")
        print("  Add meeting for Cheval Blanc Tuesday 3pm - proposal discussion")
        print("  Schedule concept presentation for Wind Marjan next Friday")
        print("  Meeting with client tomorrow at 10am about Bodrum project")
        print("\nType 'exit' to quit\n")

        while True:
            try:
                user_input = input("📅 Add meeting: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['exit', 'quit', 'q']:
                    break

                result = service.add_meeting_from_chat(user_input)

                if result['success']:
                    print(f"\n✅ {result['message']}\n")
                else:
                    print(f"\n❌ {result['message']}\n")

            except KeyboardInterrupt:
                break

        print("\n👋 Goodbye!")
