"""
Meeting Summary Email Parser

Parses meeting summary emails (sent from Claude CLI) to extract:
- Action items with owner, deadline, and ball tracking
- Creates tasks in the tasks table
- Links tasks to proposals/projects

Format expected:
✅ Action Items
BENSLEY Action | Owner | Deadline
...
CLIENT (Company Name) Action | Deadline
...
"""

import re
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "database" / "bensley_master.db"


class MeetingSummaryParser:
    """Parse meeting summary emails and create tasks."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)

    def is_meeting_summary_email(self, subject: str, sender: str) -> bool:
        """Check if email is a meeting summary."""
        subject_lower = subject.lower() if subject else ""
        return (
            "meeting summary" in subject_lower or
            "call summary" in subject_lower or
            "action items" in subject_lower
        ) and "bensley" in (sender or "").lower()

    def extract_project_code(self, subject: str, body: str) -> Optional[str]:
        """Extract project code from subject or body."""
        # Pattern: 25 BK-087, 24 BK-058, etc.
        pattern = r'\b(\d{2}\s*BK-\d{3})\b'

        # Check subject first
        if subject:
            match = re.search(pattern, subject)
            if match:
                return match.group(1).replace(" ", " ")  # Normalize spaces

        # Check body
        if body:
            match = re.search(pattern, body)
            if match:
                return match.group(1).replace(" ", " ")

        return None

    def parse_deadline(self, deadline_text: str) -> Tuple[Optional[str], str]:
        """
        Parse deadline text into a date and urgency level.

        Returns: (date_string or None, urgency: 'urgent'|'soon'|'flexible'|'tbd')
        """
        if not deadline_text:
            return None, "tbd"

        text = deadline_text.lower().strip()
        today = datetime.now()

        # Immediate/urgent
        if text in ("today", "asap", "immediately", "urgent", "now"):
            return today.strftime("%Y-%m-%d"), "urgent"

        if text in ("tomorrow", "tmrw"):
            return (today + timedelta(days=1)).strftime("%Y-%m-%d"), "urgent"

        if text in ("eod", "end of day", "by eod"):
            return today.strftime("%Y-%m-%d"), "urgent"

        if text in ("eow", "end of week", "this week"):
            # Friday of this week
            days_until_friday = (4 - today.weekday()) % 7
            if days_until_friday == 0 and today.weekday() > 4:
                days_until_friday = 7
            return (today + timedelta(days=days_until_friday)).strftime("%Y-%m-%d"), "soon"

        # Next week
        if "next week" in text:
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            return (today + timedelta(days=days_until_monday)).strftime("%Y-%m-%d"), "soon"

        # Specific day
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for i, day in enumerate(days):
            if day in text:
                days_ahead = i - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d"), "soon"

        # Holidays, TBD, etc.
        if text in ("holidays", "holiday", "vacation"):
            # After new year
            return "2026-01-06", "flexible"

        if text in ("tbd", "to be determined", "upon receipt", "post-signing", "before site visit"):
            return None, "flexible"

        # Try to parse as date
        try:
            # Try common formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%B %d", "%b %d"]:
                try:
                    parsed = datetime.strptime(text, fmt)
                    if parsed.year == 1900:  # No year specified
                        parsed = parsed.replace(year=today.year)
                        if parsed < today:
                            parsed = parsed.replace(year=today.year + 1)
                    return parsed.strftime("%Y-%m-%d"), "soon"
                except ValueError:
                    continue
        except:
            pass

        return None, "tbd"

    def determine_ball_owner(self, owner_text: str, is_bensley_section: bool) -> Tuple[str, str]:
        """
        Determine who has the ball and normalized assignee.

        Returns: (assignee: 'us'|'them'|person_name, ball_with: 'us'|'them')
        """
        if not owner_text:
            return ("us" if is_bensley_section else "them", "us" if is_bensley_section else "them")

        owner_lower = owner_text.lower().strip()

        # BENSLEY team members
        bensley_people = {
            "lukas": "Lukas",
            "bill": "Bill",
            "brian": "Brian",
            "team": "Team",
            "design team": "Design Team",
            "bensley": "us",
        }

        for key, value in bensley_people.items():
            if key in owner_lower:
                return (value, "us")

        # If in BENSLEY section, default to us
        if is_bensley_section:
            return (owner_text.strip(), "us")

        # Client/them
        return (owner_text.strip(), "them")

    def parse_action_items(self, body: str) -> List[Dict]:
        """
        Parse action items from meeting summary email body.

        Returns list of action item dicts with:
        - task: str
        - owner: str
        - assignee: 'us'|'them'|person_name
        - ball_with: 'us'|'them'
        - due_date: str or None
        - urgency: str
        - priority: str
        """
        if not body:
            return []

        action_items = []

        # Find action items section - may be on single line or multiline
        # Look for "Action Items" or "✅ Action Items" header
        action_section_match = re.search(
            r'(?:✅\s*)?Action Items?\s*(.*?)(?=Key Decisions|Next Steps|Minutes prepared|$)',
            body,
            re.IGNORECASE | re.DOTALL
        )

        if not action_section_match:
            return []

        action_section = action_section_match.group(1)

        # Parse BENSLEY section - look for pattern: "BENSLEY Action Owner Deadline [items...] PEARL/CLIENT"
        # Format: "Task Owner Deadline Task Owner Deadline..."
        bensley_match = re.search(
            r'BENSLEY\s+Action\s+Owner\s+Deadline\s+(.*?)(?=PEARL|CLIENT|[A-Z][A-Z\s]+\([^)]+\)\s+Action)',
            action_section,
            re.IGNORECASE | re.DOTALL
        )

        if bensley_match:
            bensley_text = bensley_match.group(1).strip()
            bensley_items = self._parse_action_text(bensley_text, is_bensley=True)
            action_items.extend(bensley_items)

        # Parse CLIENT/PEARL RESORTS section
        # Format: "PEARL RESORTS (Name) Action Deadline [items...]"
        client_match = re.search(
            r'(?:PEARL RESORTS|CLIENT|[A-Z][A-Z\s]+)\s*\([^)]+\)\s+Action\s+Deadline\s+(.*?)(?=Key Decisions|Next Steps|Minutes|$)',
            action_section,
            re.IGNORECASE | re.DOTALL
        )

        if client_match:
            client_text = client_match.group(1).strip()
            client_items = self._parse_action_text(client_text, is_bensley=False)
            action_items.extend(client_items)

        return action_items

    def _parse_action_text(self, text: str, is_bensley: bool) -> List[Dict]:
        """
        Parse action items from text where format is:
        "Task1 Owner1 Deadline1 Task2 Owner2 Deadline2..."

        For BENSLEY: triplets of (task, owner, deadline)
        For Client: pairs of (task, deadline)
        """
        items = []

        # Known owners (helps split the text)
        owners = ['Lukas', 'Bill', 'Brian', 'Team', 'Design Team']
        deadlines = ['Tomorrow', 'Today', 'Holidays', 'TBD', 'Post-signing', 'Upon Receipt',
                     'Before Site Visit', 'Before Permit Stage', 'ASAP', 'EOD', 'EOW',
                     'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

        if is_bensley:
            # BENSLEY format: Task Owner Deadline Task Owner Deadline...
            # Split by known owners
            pattern = r'(.+?)\s+(' + '|'.join(owners) + r')\s+(' + '|'.join(deadlines) + r')'
            matches = re.findall(pattern, text, re.IGNORECASE)

            for match in matches:
                task, owner, deadline = match
                task = task.strip()
                if not task or len(task) < 5:
                    continue

                assignee, ball_with = self.determine_ball_owner(owner, True)
                due_date, urgency = self.parse_deadline(deadline)
                priority_map = {"urgent": "high", "soon": "medium", "flexible": "low", "tbd": "low"}

                items.append({
                    "task": task,
                    "owner": owner,
                    "assignee": assignee,
                    "ball_with": ball_with,
                    "due_date": due_date,
                    "urgency": urgency,
                    "priority": priority_map.get(urgency, "medium"),
                    "is_bensley": True
                })
        else:
            # Client format: Task Deadline Task Deadline...
            pattern = r'(.+?)\s+(' + '|'.join(deadlines) + r')(?=\s|$)'
            matches = re.findall(pattern, text, re.IGNORECASE)

            for match in matches:
                task, deadline = match
                task = task.strip()
                if not task or len(task) < 5:
                    continue

                due_date, urgency = self.parse_deadline(deadline)
                priority_map = {"urgent": "high", "soon": "medium", "flexible": "low", "tbd": "low"}

                items.append({
                    "task": task,
                    "owner": "Client",
                    "assignee": "them",
                    "ball_with": "them",
                    "due_date": due_date,
                    "urgency": urgency,
                    "priority": priority_map.get(urgency, "medium"),
                    "is_bensley": False
                })

        return items

    def _parse_action_lines(self, text: str, is_bensley: bool) -> List[Dict]:
        """Parse individual action item lines."""
        items = []

        # Split into lines and process
        lines = text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('-'):
                continue

            # Try to parse as "Task | Owner | Deadline" or "Task | Deadline"
            parts = [p.strip() for p in line.split('|')]

            if len(parts) >= 1 and parts[0]:
                task = parts[0]
                owner = parts[1] if len(parts) > 1 else None
                deadline = parts[2] if len(parts) > 2 else (parts[1] if len(parts) == 2 and not is_bensley else None)

                # Skip header rows
                if task.lower() in ('action', 'owner', 'deadline', 'action owner deadline'):
                    continue

                assignee, ball_with = self.determine_ball_owner(owner, is_bensley)
                due_date, urgency = self.parse_deadline(deadline)

                # Determine priority based on urgency
                priority_map = {"urgent": "high", "soon": "medium", "flexible": "low", "tbd": "low"}

                items.append({
                    "task": task,
                    "owner": owner or ("BENSLEY" if is_bensley else "Client"),
                    "assignee": assignee,
                    "ball_with": ball_with,
                    "due_date": due_date,
                    "urgency": urgency,
                    "priority": priority_map.get(urgency, "medium"),
                    "is_bensley": is_bensley
                })

        return items

    def create_tasks_from_email(self, email_id: int) -> Dict:
        """
        Process a meeting summary email and create tasks.

        Returns summary of what was created.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Get email
            cursor.execute("""
                SELECT email_id, subject, sender_email, body_full, date
                FROM emails WHERE email_id = ?
            """, (email_id,))
            email = cursor.fetchone()

            if not email:
                return {"success": False, "error": "Email not found"}

            email = dict(email)

            # Check if it's a meeting summary
            if not self.is_meeting_summary_email(email['subject'], email['sender_email']):
                return {"success": False, "error": "Not a meeting summary email"}

            # Extract project code
            project_code = self.extract_project_code(email['subject'], email['body_full'])

            # Get proposal_id if project_code found
            proposal_id = None
            if project_code:
                cursor.execute(
                    "SELECT proposal_id FROM proposals WHERE project_code = ?",
                    (project_code,)
                )
                row = cursor.fetchone()
                if row:
                    proposal_id = row['proposal_id']

            # Parse action items
            action_items = self.parse_action_items(email['body_full'])

            if not action_items:
                return {
                    "success": True,
                    "email_id": email_id,
                    "project_code": project_code,
                    "tasks_created": 0,
                    "message": "No action items found in email"
                }

            # Create tasks
            created_tasks = []
            for item in action_items:
                # Check for duplicate task
                cursor.execute("""
                    SELECT task_id FROM tasks
                    WHERE title = ? AND source_email_id = ?
                """, (item['task'], email_id))

                if cursor.fetchone():
                    continue  # Skip duplicate

                cursor.execute("""
                    INSERT INTO tasks (
                        title, description, task_type, priority, status,
                        due_date, project_code, proposal_id, assignee,
                        source_email_id, category, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    item['task'],
                    f"From meeting: {email['subject']}\nOwner: {item['owner']}\nBall with: {item['ball_with']}",
                    'action_item',
                    item['priority'],
                    'pending',
                    item['due_date'],
                    project_code,
                    proposal_id,
                    item['assignee'],
                    email_id,
                    'Meeting' if item['is_bensley'] else 'Client Action'
                ))

                created_tasks.append({
                    "task_id": cursor.lastrowid,
                    "title": item['task'],
                    "assignee": item['assignee'],
                    "ball_with": item['ball_with'],
                    "due_date": item['due_date']
                })

            conn.commit()

            return {
                "success": True,
                "email_id": email_id,
                "project_code": project_code,
                "proposal_id": proposal_id,
                "tasks_created": len(created_tasks),
                "tasks": created_tasks,
                "action_items_found": len(action_items)
            }

        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def process_unprocessed_summaries(self, limit: int = 50) -> Dict:
        """
        Find and process meeting summary emails that haven't been processed.

        Returns summary of processing.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Find meeting summary emails not yet processed (no tasks from them)
            cursor.execute("""
                SELECT e.email_id, e.subject, e.date
                FROM emails e
                WHERE (e.subject LIKE '%Meeting Summary%' OR e.subject LIKE '%meeting summary%')
                AND e.sender_email LIKE '%bensley%'
                AND NOT EXISTS (
                    SELECT 1 FROM tasks t WHERE t.source_email_id = e.email_id
                )
                ORDER BY e.date DESC
                LIMIT ?
            """, (limit,))

            emails = cursor.fetchall()
            conn.close()

            results = {
                "emails_found": len(emails),
                "emails_processed": 0,
                "tasks_created": 0,
                "errors": []
            }

            for email in emails:
                result = self.create_tasks_from_email(email['email_id'])
                if result.get('success'):
                    results['emails_processed'] += 1
                    results['tasks_created'] += result.get('tasks_created', 0)
                else:
                    results['errors'].append({
                        "email_id": email['email_id'],
                        "subject": email['subject'],
                        "error": result.get('error')
                    })

            return results

        except Exception as e:
            return {"success": False, "error": str(e)}


# CLI usage
if __name__ == "__main__":
    import sys

    parser = MeetingSummaryParser()

    if len(sys.argv) > 1:
        email_id = int(sys.argv[1])
        result = parser.create_tasks_from_email(email_id)
        print(json.dumps(result, indent=2))
    else:
        # Process all unprocessed
        result = parser.process_unprocessed_summaries()
        print(json.dumps(result, indent=2))
