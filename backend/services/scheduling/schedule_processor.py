"""
Schedule Processor Service

Processes scheduling emails from team leads and populates the schedule database.
Handles both PDF attachments (Bali) and text emails (Bangkok).

Team Leads:
- Bali: Astuti (bensley.bali@bensley.co.id) - sends PDFs
- Bangkok Interior: Aood (aood@bensley.com) - sends text
- Bangkok Landscape: Moo (moo@bensley.com)
- Override: Bill (bill@bensley.com), Brian (bsherman@bensley.com)
"""

import sqlite3
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent.parent.parent.parent / "database" / "bensley_master.db"

# Team lead config
TEAM_LEADS = {
    "bensley.bali@bensley.co.id": {"name": "Astuti", "office": "Bali", "sends_pdf": True},
    "aood@bensley.com": {"name": "Aood", "office": "Bangkok", "sends_pdf": False},
    "moo@bensley.com": {"name": "Moo", "office": "Bangkok", "sends_pdf": False},
    "bill@bensley.com": {"name": "Bill", "office": "Bangkok", "sends_pdf": False, "is_override": True},
    "bsherman@bensley.com": {"name": "Brian", "office": "Bangkok", "sends_pdf": False, "is_override": True},
}

# Phase patterns
PHASES = ["Mobilization", "Concept", "SD", "DD", "CD", "CA"]
PHASE_PATTERNS = {
    "Mobilization": r"\bMOB\b|Mobilization",
    "Concept": r"\bConcept\b|CONCEPT",
    "SD": r"\bSD\b|Schematic Design|Schematic",
    "DD": r"\bDD\b|Design Development",
    "CD": r"\bCD\b|Construction Doc|CDs\b",
    "CA": r"\bCA\b|Contract Admin",
}


class ScheduleProcessor:
    """Main processor for schedule emails"""

    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.conn = None

    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close connection"""
        if self.conn:
            self.conn.close()

    def find_unprocessed_schedule_emails(self, limit: int = 20) -> List[Dict]:
        """Find scheduling emails that haven't been processed yet"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.date,
                e.body_full,
                e.snippet,
                (SELECT filepath FROM email_attachments
                 WHERE email_id = e.email_id
                 AND (filename LIKE '%.pdf' OR mime_type LIKE '%pdf%')
                 LIMIT 1) as pdf_path
            FROM emails e
            LEFT JOIN schedule_processing_log spl ON e.email_id = spl.email_id
            WHERE (
                e.subject LIKE '%schedule%'
                OR e.subject LIKE '%Schedule%'
                OR e.subject LIKE '%SCHEDULE%'
            )
            AND e.sender_email IN (
                'bensley.bali@bensley.co.id',
                'aood@bensley.com',
                'moo@bensley.com',
                'bill@bensley.com',
                'bsherman@bensley.com',
                'ouant@bensley.com'
            )
            AND spl.log_id IS NULL
            ORDER BY e.date DESC
            LIMIT ?
        """, (limit,))

        emails = []
        for row in cursor.fetchall():
            emails.append({
                "email_id": row["email_id"],
                "subject": row["subject"],
                "sender_email": row["sender_email"],
                "date": row["date"],
                "body": row["body_full"] or row["snippet"] or "",
                "pdf_path": row["pdf_path"],
            })
        return emails

    def parse_week_from_subject(self, subject: str) -> Optional[Tuple[str, str]]:
        """
        Extract week dates from email subject

        Examples:
        - "Work staff schedule 8-14 Dec 2025"
        - "Updated ID team schedule (10 - 12 December 2025)"
        - "Work Schedule 17 - 21 November 2025"
        """
        # Pattern 1: "8-14 Dec 2025" or "17 - 21 November 2025"
        pattern1 = r'(\d{1,2})\s*[-–]\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})'
        match = re.search(pattern1, subject)
        if match:
            start_day = int(match.group(1))
            end_day = int(match.group(2))
            month_str = match.group(3)
            year = int(match.group(4))

            month = self._parse_month(month_str)
            if month:
                start_date = f"{year}-{month:02d}-{start_day:02d}"
                end_date = f"{year}-{month:02d}-{end_day:02d}"
                return (start_date, end_date)

        # Pattern 2: "(December 2025)" with date range before
        pattern2 = r'(\d{1,2})\s*[-–]\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})'
        match = re.search(pattern2, subject)
        if match:
            return self._parse_date_match(match)

        return None

    def _parse_month(self, month_str: str) -> Optional[int]:
        """Parse month string to number"""
        months = {
            'jan': 1, 'january': 1, 'feb': 2, 'february': 2,
            'mar': 3, 'march': 3, 'apr': 4, 'april': 4,
            'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
            'aug': 8, 'august': 8, 'sep': 9, 'september': 9,
            'oct': 10, 'october': 10, 'nov': 11, 'november': 11,
            'dec': 12, 'december': 12
        }
        return months.get(month_str.lower())

    def _parse_date_match(self, match) -> Optional[Tuple[str, str]]:
        """Parse regex match to date tuple"""
        start_day = int(match.group(1))
        end_day = int(match.group(2))
        month_str = match.group(3)
        year = int(match.group(4))

        month = self._parse_month(month_str)
        if month:
            start_date = f"{year}-{month:02d}-{start_day:02d}"
            end_date = f"{year}-{month:02d}-{end_day:02d}"
            return (start_date, end_date)
        return None

    def detect_office(self, sender_email: str, subject: str) -> str:
        """Determine office from sender or subject"""
        # Check sender first
        sender_lower = sender_email.lower()
        for email, info in TEAM_LEADS.items():
            if email in sender_lower:
                return info["office"]

        # Check subject
        subject_lower = subject.lower()
        if 'bali' in subject_lower:
            return 'Bali'
        elif 'thailand' in subject_lower or 'bangkok' in subject_lower:
            return 'Bangkok'
        elif 'id team' in subject_lower:  # Interior Design
            return 'Bangkok'

        return 'Bangkok'  # Default

    def get_or_create_member(self, nickname: str, office: str) -> Optional[int]:
        """Find or create team member by nickname"""
        cursor = self.conn.cursor()

        # Try exact nickname match
        cursor.execute("""
            SELECT member_id FROM team_members
            WHERE LOWER(nickname) = LOWER(?)
        """, (nickname,))
        result = cursor.fetchone()
        if result:
            return result[0]

        # Try full name contains
        cursor.execute("""
            SELECT member_id FROM team_members
            WHERE LOWER(full_name) LIKE LOWER(?)
        """, (f"%{nickname}%",))
        result = cursor.fetchone()
        if result:
            return result[0]

        # Create placeholder if not found
        cursor.execute("""
            INSERT INTO team_members
            (email, full_name, nickname, office, discipline, is_active)
            VALUES (?, ?, ?, ?, 'Interior', 1)
        """, (f"{nickname.lower().replace(' ', '.')}@bensley.com", nickname, nickname, office))

        self.conn.commit()
        return cursor.lastrowid

    def match_project(self, project_text: str) -> Optional[Dict]:
        """Match project text to database project"""
        cursor = self.conn.cursor()

        # Clean up the text
        clean_text = project_text.strip().upper()

        # Common project name mappings
        mappings = {
            'TEL AVIV': '24 BK-082',
            'RITZ CARLTON RESERVE': '25 BK-033',
            'RITZ CARLTON': '25 BK-033',
            '25 DOWNTOWN': '23 BK-093',
            'DOWNTOWN MUMBAI': '23 BK-093',
            'MANDARIN ORIENTAL': '24 BK-070',
            'WYNN': '23 BK-059',
            'DANG THAI MAI': '23 BK-085',
            'DTM': '23 BK-085',
        }

        for pattern, project_code in mappings.items():
            if pattern in clean_text:
                cursor.execute("""
                    SELECT project_code, project_name FROM projects
                    WHERE project_code = ?
                """, (project_code,))
                result = cursor.fetchone()
                if result:
                    return {"project_code": result[0], "project_name": result[1]}

        # Try fuzzy match on project_name
        cursor.execute("""
            SELECT project_code, project_name FROM projects
            WHERE UPPER(project_name) LIKE ?
            LIMIT 1
        """, (f"%{clean_text[:20]}%",))
        result = cursor.fetchone()
        if result:
            return {"project_code": result[0], "project_name": result[1]}

        return None

    def parse_phase(self, text: str) -> Optional[str]:
        """Extract phase from text"""
        for phase, pattern in PHASE_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return phase
        return None

    def process_email(self, email: Dict, dry_run: bool = False) -> Dict:
        """Process a single scheduling email"""
        email_id = email["email_id"]
        subject = email["subject"]
        sender = email["sender_email"]
        body = email["body"]
        pdf_path = email.get("pdf_path")

        logger.info(f"Processing email {email_id}: {subject[:50]}...")

        # Parse week dates
        week_dates = self.parse_week_from_subject(subject)
        if not week_dates:
            return {"error": "Could not parse week dates from subject", "email_id": email_id}

        week_start, week_end = week_dates
        office = self.detect_office(sender, subject)

        logger.info(f"  Week: {week_start} to {week_end}, Office: {office}")

        if dry_run:
            return {
                "email_id": email_id,
                "week_start": week_start,
                "week_end": week_end,
                "office": office,
                "has_pdf": bool(pdf_path),
                "dry_run": True
            }

        # Create or update weekly schedule
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO weekly_schedules
            (office, week_start_date, week_end_date, source_email_id, created_by, status)
            VALUES (?, ?, ?, ?, ?, 'published')
            ON CONFLICT(office, week_start_date) DO UPDATE SET
                week_end_date = excluded.week_end_date,
                source_email_id = excluded.source_email_id,
                updated_at = datetime('now')
        """, (office, week_start, week_end, email_id, sender))

        # Get schedule_id
        cursor.execute("""
            SELECT schedule_id FROM weekly_schedules
            WHERE office = ? AND week_start_date = ?
        """, (office, week_start))
        result = cursor.fetchone()
        schedule_id = result[0] if result else None

        if not schedule_id:
            return {"error": "Failed to create schedule", "email_id": email_id}

        # Process based on type
        entries_created = 0
        if pdf_path and Path(pdf_path).exists():
            # Process PDF
            entries_created = self._process_pdf_schedule(schedule_id, pdf_path, week_start, week_end, office)
        else:
            # Process text body
            entries_created = self._process_text_schedule(schedule_id, body, week_start, week_end, office)

        # Log processing
        cursor.execute("""
            INSERT INTO schedule_processing_log (email_id, office, week_start_date, status, entries_created)
            VALUES (?, ?, ?, 'success', ?)
        """, (email_id, office, week_start, entries_created))

        self.conn.commit()

        return {
            "success": True,
            "email_id": email_id,
            "schedule_id": schedule_id,
            "week_start": week_start,
            "week_end": week_end,
            "office": office,
            "entries_created": entries_created,
            "source": "pdf" if pdf_path else "text"
        }

    def _process_pdf_schedule(self, schedule_id: int, pdf_path: str,
                              week_start: str, week_end: str, office: str) -> int:
        """Process PDF schedule attachment"""
        try:
            import pdfplumber
        except ImportError:
            logger.error("pdfplumber not installed. Run: pip install pdfplumber")
            return 0

        entries_created = 0
        cursor = self.conn.cursor()

        try:
            with pdfplumber.open(pdf_path) as pdf:
                page = pdf.pages[0]
                tables = page.extract_tables()

                if not tables:
                    logger.warning(f"No tables found in PDF: {pdf_path}")
                    return 0

                table = tables[0]

                # Skip header rows (first 2 rows are usually dates)
                for row_idx in range(2, len(table)):
                    row = table[row_idx]
                    if not row or len(row) < 2:
                        continue

                    # First column is name
                    nickname = row[0].strip() if row[0] else ""
                    if not nickname or nickname.upper() in ['NAME', 'SICK', 'PERMIT', '']:
                        continue

                    # Get member_id
                    member_id = self.get_or_create_member(nickname, office)
                    if not member_id:
                        continue

                    # Find assignment (first non-empty cell after name)
                    assignment = None
                    for col in row[1:10]:
                        if col and col.strip() and 'HOLIDAY' not in col.upper():
                            assignment = col.strip()
                            break

                    if not assignment:
                        continue

                    # Parse assignment
                    project = self.match_project(assignment)
                    phase = self.parse_phase(assignment)

                    project_code = project["project_code"] if project else None
                    project_name = project["project_name"] if project else assignment[:50]

                    # Create entries for each weekday
                    start_dt = datetime.strptime(week_start, "%Y-%m-%d")
                    end_dt = datetime.strptime(week_end, "%Y-%m-%d")
                    current = start_dt

                    while current <= end_dt:
                        if current.weekday() < 5:  # Mon-Fri
                            work_date = current.strftime("%Y-%m-%d")
                            try:
                                cursor.execute("""
                                    INSERT OR REPLACE INTO schedule_entries
                                    (schedule_id, member_id, work_date, project_code, project_name,
                                     phase, task_description, raw_text)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (schedule_id, member_id, work_date, project_code,
                                      project_name, phase, None, assignment))
                                entries_created += 1
                            except Exception as e:
                                logger.error(f"Error inserting entry: {e}")
                        current += timedelta(days=1)

        except Exception as e:
            logger.error(f"Error processing PDF: {e}")

        return entries_created

    def _process_text_schedule(self, schedule_id: int, body: str,
                               week_start: str, week_end: str, office: str) -> int:
        """Process text-based schedule email"""
        # Text schedules are less structured
        # For now, just log that we processed it
        logger.info(f"  Text schedule detected (not fully implemented)")

        # Create a single entry to mark as processed
        cursor = self.conn.cursor()

        # Just mark as processed for now
        return 0


def process_pending_schedules(dry_run: bool = False, limit: int = 10) -> Dict:
    """Main entry point: process all pending schedule emails"""
    processor = ScheduleProcessor()
    processor.connect()

    try:
        emails = processor.find_unprocessed_schedule_emails(limit=limit)
        logger.info(f"Found {len(emails)} unprocessed schedule emails")

        results = {
            "processed": 0,
            "errors": 0,
            "total_entries": 0,
            "details": []
        }

        for email in emails:
            result = processor.process_email(email, dry_run=dry_run)
            results["details"].append(result)

            if result.get("success"):
                results["processed"] += 1
                results["total_entries"] += result.get("entries_created", 0)
            elif result.get("error"):
                results["errors"] += 1
                logger.warning(f"  Error: {result['error']}")

        return results

    finally:
        processor.close()


if __name__ == "__main__":
    import sys

    dry_run = "--dry-run" in sys.argv

    print("=" * 60)
    print("Schedule Processor")
    print("=" * 60)

    if dry_run:
        print("DRY RUN - No database changes will be made\n")

    results = process_pending_schedules(dry_run=dry_run)

    print(f"\nSummary:")
    print(f"  - Processed: {results['processed']}")
    print(f"  - Errors: {results['errors']}")
    print(f"  - Entries created: {results['total_entries']}")

    if results["details"]:
        print(f"\nDetails:")
        for r in results["details"]:
            if r.get("success"):
                print(f"  ✓ {r['week_start']} to {r['week_end']} ({r['office']}): {r['entries_created']} entries")
            elif r.get("error"):
                print(f"  ✗ Email {r.get('email_id')}: {r['error']}")
