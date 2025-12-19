#!/usr/bin/env python3
"""
Schedule PDF Parser
Extracts schedule data from PDF files sent by team leads
"""

import sqlite3
import PyPDF2
import pdfplumber
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import os

DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')


class SchedulePDFParser:
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

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract all text from PDF using pdfplumber"""
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            # Fallback to PyPDF2
            try:
                text = ""
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                return text
            except Exception as e2:
                print(f"PyPDF2 also failed: {e2}")
                return ""

    def parse_schedule_table(self, pdf_path: str) -> Dict:
        """
        Parse schedule PDF and extract structured data
        Returns dict with schedule entries
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page = pdf.pages[0]

                # Extract tables
                tables = page.extract_tables()
                if not tables:
                    print("No tables found in PDF")
                    return {"entries": []}

                table = tables[0]

                # First row should be dates
                date_row = table[0] if table else []
                # Second row should be specific dates (10, 11, 12, etc.)
                date_nums = table[1] if len(table) > 1 else []

                # Parse dates
                dates = []
                month_year = None

                # Look for month/year in the PDF
                text = page.extract_text()
                month_match = re.search(r'(NOVEMBER|DECEMBER|JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER)\s*(\d{4})?', text, re.IGNORECASE)
                if month_match:
                    month_str = month_match.group(1).capitalize()
                    year_str = month_match.group(2) or str(datetime.now().year)
                    month_year = f"{month_str} {year_str}"

                # Parse date numbers
                for cell in date_nums:
                    if cell and cell.strip() and cell.strip().isdigit():
                        dates.append(int(cell.strip()))

                # Parse schedule entries (rows after date rows)
                entries = []
                for row_idx in range(2, len(table)):
                    row = table[row_idx]
                    if not row or len(row) < 2:
                        continue

                    # First column is the name
                    name = row[0].strip() if row[0] else ""
                    if not name or name in ['NAME', 'SICK', 'PERMIT']:
                        continue

                    # Find this person in database (flexible matching)
                    cursor = self.conn.cursor()

                    # Try exact nickname match first
                    cursor.execute("""
                        SELECT member_id, office FROM team_members
                        WHERE nickname = ?
                    """, (name,))
                    member = cursor.fetchone()

                    # Try full name contains
                    if not member:
                        cursor.execute("""
                            SELECT member_id, office FROM team_members
                            WHERE full_name LIKE ?
                        """, (f"%{name}%",))
                        member = cursor.fetchone()

                    # Try reverse - name contains nickname (for "Putu Mahendra" matching "Putu")
                    if not member and ' ' in name:
                        first_name = name.split()[0]
                        cursor.execute("""
                            SELECT member_id, office FROM team_members
                            WHERE nickname = ? OR full_name LIKE ?
                        """, (first_name, f"{first_name}%"))
                        member = cursor.fetchone()

                    if not member:
                        print(f"Warning: Could not find team member '{name}' in database")
                        continue

                    member_id = member['member_id']
                    office = member['office']

                    # Find first non-empty cell (person's weekly assignment)
                    # This cell represents their work for the entire week
                    weekly_assignment = None
                    for col_idx in range(1, min(len(row), 10)):  # Check first 10 columns
                        cell_value = row[col_idx]
                        if cell_value and cell_value.strip() and 'HOLIDAY' not in cell_value.upper():
                            weekly_assignment = cell_value.strip()
                            break

                    if not weekly_assignment:
                        continue

                    # Parse project and task from weekly assignment
                    project_title, task, phase = self.parse_cell_value(weekly_assignment)

                    if project_title:
                        # Create entry for this person's weekly assignment
                        # We'll expand to daily entries when saving to database
                        entries.append({
                            'member_id': member_id,
                            'nickname': name,
                            'office': office,
                            'project_title': project_title,
                            'task': task,
                            'phase': phase,
                            'raw_text': weekly_assignment,
                            'is_weekly': True  # Flag to indicate this spans the whole week
                        })

                return {
                    'month_year': month_year,
                    'entries': entries
                }

        except Exception as e:
            print(f"Error parsing PDF table: {e}")
            import traceback
            traceback.print_exc()
            return {"entries": []}

    def parse_cell_value(self, cell_text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Parse a schedule cell to extract project name, task, and phase
        Examples:
        - "TEL AVIV 100% CD ID (42nd Floor)" -> ("Tel Aviv", "42nd Floor", "CD")
        - "RITZ CARLTON RESERVE - NUSA DUA BALI (PRESENTATION)" -> ("Ritz Carlton Reserve Nusa Dua", "Presentation", None)
        """
        if not cell_text:
            return None, None, None

        text = cell_text.strip()

        # Extract phase (SD, DD, CD, Concept)
        phase = None
        if re.search(r'\b(100%\s*)?CD\b', text, re.IGNORECASE):
            phase = 'CD'
        elif re.search(r'\b(100%\s*)?DD\b', text, re.IGNORECASE):
            phase = 'DD'
        elif re.search(r'\b(100%\s*)?SD\b', text, re.IGNORECASE):
            phase = 'SD'
        elif 'CONCEPT' in text.upper():
            phase = 'Concept'

        # Extract task from parentheses
        task = None
        task_match = re.search(r'\(([^)]+)\)', text)
        if task_match:
            task = task_match.group(1).strip()

        # Extract project name (remove phase markers and task)
        project_title = text
        project_title = re.sub(r'\([^)]+\)', '', project_title)  # Remove parentheses
        project_title = re.sub(r'\b(100%\s*)?(CD|DD|SD|ID|AR|LA)\b', '', project_title, flags=re.IGNORECASE)  # Remove phases
        project_title = re.sub(r'\s+', ' ', project_title).strip()  # Clean whitespace

        # Clean up common project names
        project_title = self.normalize_project_title(project_title)

        return project_title, task, phase

    def normalize_project_title(self, name: str) -> str:
        """Normalize project names to match database"""
        if not name:
            return name

        # Common project name mappings
        mappings = {
            'TEL AVIV': 'Tel Aviv High Rise Project in Israel',
            'RITZ CARLTON RESERVE - NUSA DUA': 'Ritz Carlton Reserve Nusa Dua',
            'RITZ CARLTON RESERVE': 'Ritz Carlton Reserve Nusa Dua',
            '25 DOWNTOWN - MUMBAI': '25 Downtown Mumbai',
            '25 DOWNTOWN': '25 Downtown Mumbai',
            'MANDARIN ORIENTAL': 'Mandarin Oriental Bali, Indonesia',
            'WYNN AL MARJAN': "Wynn Al Marjan Island Project",
            'DTM HANOI': 'Dang Thai Mai project',
            'DANG THAI MAI': 'Dang Thai Mai project',
            'RITZ CARLTON - HAINAN': 'Ritz Carlton Hotel Nanyan bay',
        }

        name_upper = name.upper().strip()
        for key, value in mappings.items():
            if key in name_upper:
                return value

        # Title case if not matched
        return name.title()

    def save_schedule_to_database(self, email_id: int, schedule_data: Dict, week_start: str, week_end: str) -> int:
        """
        Save parsed schedule data to database
        Returns schedule_id
        """
        cursor = self.conn.cursor()

        if not schedule_data.get('entries'):
            print("No schedule entries to save")
            return None

        # Determine office from first entry
        office = schedule_data['entries'][0]['office'] if schedule_data['entries'] else 'Bali'

        # Get sender email from email table
        cursor.execute("SELECT sender_email FROM emails WHERE email_id = ?", (email_id,))
        result = cursor.fetchone()
        created_by = result['sender_email'] if result else None

        # Create weekly schedule entry
        cursor.execute("""
            INSERT INTO weekly_schedules (office, week_start_date, week_end_date, source_email_id, created_by, status)
            VALUES (?, ?, ?, ?, ?, 'published')
            ON CONFLICT(office, week_start_date) DO UPDATE SET
                week_end_date = excluded.week_end_date,
                source_email_id = excluded.source_email_id,
                updated_at = datetime('now')
        """, (office, week_start, week_end, email_id, created_by))

        # Get schedule_id
        cursor.execute("""
            SELECT schedule_id FROM weekly_schedules
            WHERE office = ? AND week_start_date = ?
        """, (office, week_start))
        result = cursor.fetchone()
        schedule_id = result['schedule_id'] if result else None

        if not schedule_id:
            print("Failed to create schedule")
            return None

        # Parse month and year from schedule data
        month_year = schedule_data.get('month_year', '')
        if month_year:
            # Parse "November 2025" into month number
            try:
                dt = datetime.strptime(month_year, "%B %Y")
                year = dt.year
                month = dt.month
            except ValueError:
                # Fallback to week_start date
                dt = datetime.strptime(week_start, "%Y-%m-%d")
                year = dt.year
                month = dt.month
        else:
            dt = datetime.strptime(week_start, "%Y-%m-%d")
            year = dt.year
            month = dt.month

        # Save schedule entries
        # Expand weekly assignments to individual weekdays
        entries_created = 0

        # Parse week dates
        week_start_dt = datetime.strptime(week_start, "%Y-%m-%d")
        week_end_dt = datetime.strptime(week_end, "%Y-%m-%d")

        for entry in schedule_data['entries']:
            # For weekly assignments, create entries for each weekday (Mon-Fri)
            current_date = week_start_dt
            while current_date <= week_end_dt:
                # Skip weekends (Saturday=5, Sunday=6)
                if current_date.weekday() < 5:  # Monday=0 through Friday=4
                    work_date = current_date.strftime("%Y-%m-%d")

                    # Insert entry
                    try:
                        cursor.execute("""
                            INSERT INTO schedule_entries
                            (schedule_id, member_id, work_date, project_title, task_description, phase, raw_text)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(schedule_id, member_id, work_date) DO UPDATE SET
                                project_title = excluded.project_title,
                                task_description = excluded.task_description,
                                phase = excluded.phase,
                                raw_text = excluded.raw_text,
                                updated_at = datetime('now')
                        """, (
                            schedule_id,
                            entry['member_id'],
                            work_date,
                            entry['project_title'],
                            entry['task'],
                            entry['phase'],
                            entry['raw_text']
                        ))
                        entries_created += 1
                    except Exception as e:
                        print(f"Error inserting entry for {work_date}: {e}")

                current_date += timedelta(days=1)

        # Log processing
        cursor.execute("""
            INSERT INTO schedule_processing_log (email_id, office, week_start_date, status, entries_created)
            VALUES (?, ?, ?, 'success', ?)
        """, (email_id, office, week_start, entries_created))

        self.conn.commit()

        print(f"Saved {entries_created} schedule entries for {office} office")
        return schedule_id

    def process_schedule_pdf(self, email_id: int, week_start: str, week_end: str) -> Dict:
        """
        Process schedule PDF from email attachments
        """
        cursor = self.conn.cursor()

        # Find PDF attachments for this email
        cursor.execute("""
            SELECT attachment_id, filepath, filename
            FROM email_attachments
            WHERE email_id = ? AND (filename LIKE '%.pdf' OR mime_type LIKE '%pdf%')
            ORDER BY attachment_id DESC
            LIMIT 1
        """, (email_id,))

        attachment = cursor.fetchone()
        if not attachment:
            return {"error": "No PDF attachment found"}

        pdf_path = attachment['filepath']
        if not Path(pdf_path).exists():
            return {"error": f"PDF file not found: {pdf_path}"}

        print(f"Processing PDF: {pdf_path}")

        # Parse the PDF
        schedule_data = self.parse_schedule_table(pdf_path)

        if not schedule_data.get('entries'):
            return {"error": "No schedule entries found in PDF"}

        # Save to database
        schedule_id = self.save_schedule_to_database(email_id, schedule_data, week_start, week_end)

        return {
            "success": True,
            "schedule_id": schedule_id,
            "entries_created": len(schedule_data['entries']),
            "pdf_path": pdf_path
        }


def main():
    import sys

    if len(sys.argv) < 4:
        print("Usage: python3 schedule_pdf_parser.py <email_id> <week_start> <week_end>")
        print("Example: python3 schedule_pdf_parser.py 2024914 2025-11-10 2025-11-14")
        sys.exit(1)

    email_id = int(sys.argv[1])
    week_start = sys.argv[2]
    week_end = sys.argv[3]

    parser = SchedulePDFParser()
    parser.connect()

    try:
        result = parser.process_schedule_pdf(email_id, week_start, week_end)
        print(f"\nResult: {result}")
    finally:
        parser.close()


if __name__ == "__main__":
    main()
