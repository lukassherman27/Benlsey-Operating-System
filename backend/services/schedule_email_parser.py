#!/usr/bin/env python3
"""
Schedule Email Parser
Processes weekly scheduling emails from team leads and populates the scheduling database

Team Leads:
- Bali: Astuti (bensley.bali@bensley.co.id)
- Bangkok Interior: Aood (aood@bensley.com)
- Bangkok Architecture: Suwit, Spot
- Bangkok Landscape: Moo (moo@bensley.com)
- Override: Bill (bill@bensley.com)
"""

import sqlite3
import sys
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

# Database path
DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

# Team lead emails
TEAM_LEADS = {
    "bensley.bali@bensley.co.id": {"name": "Astuti", "office": "Bali"},
    "aood@bensley.com": {"name": "Aood", "office": "Bangkok"},
    "moo@bensley.com": {"name": "Moo", "office": "Bangkok"},
    "bill@bensley.com": {"name": "Bill", "office": "Bangkok"},
    "bsherman@bensley.com": {"name": "Brian", "office": "Bangkok"},
}

# Project phase patterns
PHASE_PATTERNS = {
    "Concept": r"Concept|CONCEPT",
    "SD": r"\bSD\b|Schematic Design",
    "DD": r"\bDD\b|Design Development",
    "CD": r"\bCD\b|Construction Documents",
    "Past Deadline": r"Past Deadline",
}

# Discipline patterns
DISCIPLINE_PATTERNS = {
    "Architecture": r"Architectural|Architecture",
    "Interior": r"Interior",
    "Landscape": r"Landscape",
    "Artwork": r"Artwork|Art",
}


class ScheduleEmailParser:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def parse_week_from_subject(self, subject: str) -> Optional[Tuple[str, str]]:
        """
        Extract week start and end dates from email subject
        Examples:
        - "Work Schedule 17 - 21 November 2025"
        - "Work staff schedule this week 27 Oct - 2 Nov 2025"
        - "Bensley Schedule Thailand (November 3-7)"
        """
        # Pattern: "17 - 21 November 2025" or "27 Oct - 2 Nov 2025"
        pattern1 = r'(\d{1,2})\s*-\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})'
        match = re.search(pattern1, subject)
        if match:
            start_day = int(match.group(1))
            end_day = int(match.group(2))
            month_str = match.group(3)
            year = int(match.group(4))

            # Parse month
            month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December']
            month_abbrevs = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

            month = None
            for i, name in enumerate(month_names, 1):
                if month_str.lower() in [name.lower(), month_abbrevs[i-1].lower()]:
                    month = i
                    break

            if month:
                start_date = f"{year}-{month:02d}-{start_day:02d}"
                end_date = f"{year}-{month:02d}-{end_day:02d}"
                return (start_date, end_date)

        # Pattern: "(November 3-7)" or "(September - October)"
        pattern2 = r'\(([A-Za-z]+)\s+(\d{1,2})-(\d{1,2})\)'
        match = re.search(pattern2, subject)
        if match:
            month_str = match.group(1)
            start_day = int(match.group(2))
            end_day = int(match.group(3))

            # Try to infer year from email date or use current year
            year = datetime.now().year

            month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December']
            month = None
            for i, name in enumerate(month_names, 1):
                if month_str.lower() == name.lower():
                    month = i
                    break

            if month:
                start_date = f"{year}-{month:02d}-{start_day:02d}"
                end_date = f"{year}-{month:02d}-{end_day:02d}"
                return (start_date, end_date)

        return None

    def extract_office_from_subject(self, subject: str) -> Optional[str]:
        """Determine office from subject line"""
        subject_lower = subject.lower()
        if 'bali' in subject_lower:
            return 'Bali'
        elif 'thailand' in subject_lower or 'bangkok' in subject_lower:
            return 'Bangkok'
        return None

    def parse_schedule_entry(self, line: str) -> Optional[Dict]:
        """
        Parse a single line from the schedule email
        Example: "Bang Thailand Cheval Blanc - Bodrum Architectural – SD: Hotel - Masterplan"
        """
        # Skip empty lines
        if not line.strip():
            return None

        # Pattern: Name  Office  Project  Discipline - Phase: Task
        # This is simplified - real parsing would need to be more sophisticated
        parts = line.split(None, 2)  # Split on whitespace, max 3 parts
        if len(parts) < 3:
            return None

        nickname = parts[0]
        office = parts[1] if parts[1] in ['Bali', 'Bangkok', 'Thailand'] else None
        rest = parts[2] if len(parts) > 2 else ""

        # Extract project name (everything before discipline indicator)
        project_title = None
        discipline = None
        phase = None
        task = None

        # Check for discipline and phase
        for disc_name, disc_pattern in DISCIPLINE_PATTERNS.items():
            if re.search(disc_pattern, rest):
                discipline = disc_name
                # Split on discipline to get project name
                project_match = re.split(disc_pattern, rest, maxsplit=1)
                if project_match:
                    project_title = project_match[0].strip()
                break

        # Extract phase and task
        for phase_name, phase_pattern in PHASE_PATTERNS.items():
            if re.search(phase_pattern, rest):
                phase = phase_name
                # Extract task (after colon)
                task_match = re.search(r':\s*(.+)$', rest)
                if task_match:
                    task = task_match.group(1).strip()
                break

        # Check for special statuses
        is_on_leave = 'leave' in rest.lower() or 'vacation' in rest.lower() or 'holiday' in rest.lower()
        is_unassigned = 'unassigned' in rest.lower()

        return {
            'nickname': nickname,
            'office': office,
            'project_title': project_title,
            'discipline': discipline,
            'phase': phase,
            'task': task,
            'is_on_leave': is_on_leave,
            'is_unassigned': is_unassigned,
            'raw_text': line.strip()
        }

    def process_scheduling_email(self, email_id: int, dry_run: bool = False) -> Dict:
        """
        Process a scheduling email and create schedule entries

        Returns:
            Dict with processing stats
        """
        cursor = self.conn.cursor()

        # Fetch email
        cursor.execute("""
            SELECT email_id, subject, sender_email, date, body_full, snippet
            FROM emails
            WHERE email_id = ?
        """, (email_id,))
        email = cursor.fetchone()

        if not email:
            return {"error": "Email not found"}

        subject = email['subject']
        sender_email = email['sender_email']
        body = email['body_full'] or email['snippet'] or ""

        # Extract week dates from subject
        week_dates = self.parse_week_from_subject(subject)
        if not week_dates:
            return {"error": "Could not parse week dates from subject"}

        week_start, week_end = week_dates

        # Determine office
        office = self.extract_office_from_subject(subject)
        if not office and sender_email in TEAM_LEADS:
            office = TEAM_LEADS[sender_email]["office"]

        if not office:
            return {"error": "Could not determine office"}

        print(f"Processing schedule for {office} office, week {week_start} to {week_end}")
        print(f"From: {sender_email}")

        if dry_run:
            print("DRY RUN - No database changes will be made")
            return {
                "week_start": week_start,
                "week_end": week_end,
                "office": office,
                "sender": sender_email,
                "dry_run": True
            }

        # Create or update weekly schedule
        cursor.execute("""
            INSERT INTO weekly_schedules (office, week_start_date, week_end_date, source_email_id, created_by, status)
            VALUES (?, ?, ?, ?, ?, 'published')
            ON CONFLICT(office, week_start_date) DO UPDATE SET
                week_end_date = excluded.week_end_date,
                source_email_id = excluded.source_email_id,
                created_by = excluded.created_by,
                updated_at = datetime('now')
        """, (office, week_start, week_end, email_id, sender_email))

        schedule_id = cursor.lastrowid
        if schedule_id == 0:
            # Get existing schedule_id
            cursor.execute("""
                SELECT schedule_id FROM weekly_schedules
                WHERE office = ? AND week_start_date = ?
            """, (office, week_start))
            result = cursor.fetchone()
            schedule_id = result[0] if result else None

        print(f"Created/updated schedule_id: {schedule_id}")

        # Parse body for schedule entries
        lines = body.split('\n')
        entries_created = 0

        for line in lines:
            entry = self.parse_schedule_entry(line)
            if entry:
                # TODO: Match nickname to member_id from team_members table
                # For now, we'll just log
                print(f"  - {entry['nickname']}: {entry['project_title']} ({entry['discipline']} - {entry['phase']})")
                entries_created += 1

        # Log processing
        cursor.execute("""
            INSERT INTO schedule_processing_log (email_id, office, week_start_date, status, entries_created)
            VALUES (?, ?, ?, 'success', ?)
        """, (email_id, office, week_start, entries_created))

        self.conn.commit()

        return {
            "success": True,
            "schedule_id": schedule_id,
            "week_start": week_start,
            "week_end": week_end,
            "office": office,
            "entries_created": entries_created
        }

    def find_unprocessed_schedule_emails(self, limit: int = 10) -> List[Dict]:
        """
        Find scheduling emails that haven't been processed yet
        """
        cursor = self.conn.cursor()

        # Find emails with schedule-related subjects that haven't been processed
        cursor.execute("""
            SELECT e.email_id, e.subject, e.sender_email, e.date
            FROM emails e
            LEFT JOIN schedule_processing_log spl ON e.email_id = spl.email_id
            WHERE (
                e.subject LIKE '%schedule%'
                OR e.subject LIKE '%Schedule%'
            )
            AND (
                e.sender_email LIKE '%bensley%'
                OR e.sender_email LIKE '%bdl%'
            )
            AND spl.log_id IS NULL
            ORDER BY e.date DESC
            LIMIT ?
        """, (limit,))

        emails = []
        for row in cursor.fetchall():
            emails.append({
                "email_id": row['email_id'],
                "subject": row['subject'],
                "sender": row['sender_email'],
                "date": row['date']
            })

        return emails


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 schedule_email_parser.py <email_id> [--dry-run]")
        print("   or: python3 schedule_email_parser.py --find-unprocessed")
        sys.exit(1)

    parser = ScheduleEmailParser()
    parser.connect()

    try:
        if sys.argv[1] == '--find-unprocessed':
            emails = parser.find_unprocessed_schedule_emails(20)
            print(f"Found {len(emails)} unprocessed schedule emails:\n")
            for email in emails:
                print(f"  ID {email['email_id']}: {email['subject']}")
                print(f"    From: {email['sender']} on {email['date']}\n")

        else:
            email_id = int(sys.argv[1])
            dry_run = '--dry-run' in sys.argv

            result = parser.process_scheduling_email(email_id, dry_run=dry_run)
            print(f"\nResult: {result}")

    finally:
        parser.close()


if __name__ == "__main__":
    main()
