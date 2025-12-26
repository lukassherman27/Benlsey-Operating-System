#!/usr/bin/env python3
"""
Polished Meeting Summary Generator

Generates beautiful, structured meeting summaries like the Pearl Resorts format.
Uses Claude CLI (not API) - prepares prompts for manual processing.

WORKFLOW:
1. Run: python generate_polished_meeting_summary.py --prepare 37
2. Copy the prompt output
3. Paste into Claude CLI
4. Copy Claude's response
5. Run: python generate_polished_meeting_summary.py --save 37 < summary.txt

OR use interactive mode with Claude CLI:
1. Run: python generate_polished_meeting_summary.py --interactive 37
2. Outputs prompt, waits for you to paste summary, saves it

Created: 2025-12-26 for Issue #162
"""

import sqlite3
import os
import json
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv()

DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')


class PolishedMeetingSummaryGenerator:
    """Prepares prompts and saves polished meeting summaries."""

    MEETING_TYPE_INDICATORS = {
        'contract_negotiation': ['contract', 'terms', 'fee', 'payment', 'signing', 'mobilization'],
        'site_visit': ['site visit', 'on site', 'walked through', 'construction', 'progress'],
        'design_review': ['design review', 'feedback', 'comments', 'revisions', 'drawings'],
        'concept_presentation': ['concept', 'presentation', 'presented', 'scheme'],
        'kickoff': ['kickoff', 'kick-off', 'introduction', 'first meeting'],
        'proposal_discussion': ['proposal', 'scope', 'deliverables', 'timeline', 'budget'],
        'internal': ['internal', 'team meeting', 'coordination'],
        'client_call': ['call', 'zoom', 'teams', 'video conference'],
    }

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # =========================================================================
    # DATABASE QUERIES
    # =========================================================================

    def get_transcript(self, transcript_id: int) -> Optional[Dict]:
        """Get full transcript data."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id, audio_filename, meeting_title, meeting_date,
                    detected_project_code, proposal_id, transcript,
                    summary, key_points, action_items, participants,
                    duration_seconds, recorded_date
                FROM meeting_transcripts
                WHERE id = ?
            """, (transcript_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_proposal_context(self, project_code: str = None, proposal_id: int = None) -> Optional[Dict]:
        """Get proposal details for context."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if proposal_id:
                cursor.execute("""
                    SELECT proposal_id, project_code, project_name, client_company,
                           contact_person, contact_email, project_value, status,
                           is_landscape, is_architect, is_interior, country
                    FROM proposals WHERE proposal_id = ?
                """, (proposal_id,))
            elif project_code:
                cursor.execute("""
                    SELECT proposal_id, project_code, project_name, client_company,
                           contact_person, contact_email, project_value, status,
                           is_landscape, is_architect, is_interior, country
                    FROM proposals
                    WHERE project_code LIKE ? OR project_code LIKE ?
                    LIMIT 1
                """, (f'%{project_code}%', project_code))
            else:
                return None
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_contact_context(self, client_company: str = None) -> List[Dict]:
        """Get relevant contacts."""
        if not client_company:
            return []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, email, company, role, phone
                FROM contacts WHERE company LIKE ? LIMIT 5
            """, (f'%{client_company}%',))
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_emails(self, project_code: str = None, proposal_id: int = None) -> List[Dict]:
        """Get recent emails related to this project."""
        if not project_code and not proposal_id:
            return []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.subject, e.sender_email, e.date, substr(e.body_preview, 1, 200) as preview
                FROM emails e
                LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
                WHERE epl.proposal_id = ? OR e.subject LIKE ?
                ORDER BY e.date DESC LIMIT 5
            """, (proposal_id, f'%{project_code}%' if project_code else ''))
            return [dict(row) for row in cursor.fetchall()]

    def get_previous_meetings(self, project_code: str = None, proposal_id: int = None, exclude_id: int = None) -> List[Dict]:
        """Get previous meetings for this project."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, meeting_title, meeting_date, substr(summary, 1, 300) as summary_preview
                FROM meeting_transcripts
                WHERE (proposal_id = ? OR detected_project_code LIKE ?)
                  AND id != ?
                ORDER BY meeting_date DESC LIMIT 3
            """, (proposal_id, f'%{project_code}%' if project_code else '', exclude_id or 0))
            return [dict(row) for row in cursor.fetchall()]

    def detect_meeting_type(self, transcript: str, title: str = None) -> str:
        """Detect meeting type from content."""
        text = f"{title or ''} {transcript[:3000]}".lower()
        scores = {}
        for mtype, keywords in self.MEETING_TYPE_INDICATORS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[mtype] = score
        return max(scores, key=scores.get) if scores else 'client_call'

    # =========================================================================
    # PROMPT BUILDING
    # =========================================================================

    def build_prompt(self, transcript_id: int) -> str:
        """Build the complete prompt with all context."""
        transcript = self.get_transcript(transcript_id)
        if not transcript:
            return f"ERROR: Transcript {transcript_id} not found"

        project_code = transcript.get('detected_project_code')
        proposal_id = transcript.get('proposal_id')

        proposal = self.get_proposal_context(project_code=project_code, proposal_id=proposal_id)
        contacts = self.get_contact_context(proposal.get('client_company')) if proposal else []
        emails = self.get_recent_emails(project_code=project_code, proposal_id=proposal_id)
        previous = self.get_previous_meetings(project_code, proposal_id, transcript_id)
        meeting_type = self.detect_meeting_type(transcript.get('transcript', ''), transcript.get('meeting_title'))

        # Parse participants
        participants = transcript.get('participants')
        if isinstance(participants, str):
            try:
                participants = json.loads(participants)
            except:
                participants = []

        # Build context sections
        proposal_ctx = ""
        if proposal:
            scope_parts = []
            if proposal.get('is_landscape'): scope_parts.append("Landscape")
            if proposal.get('is_architect'): scope_parts.append("Architecture")
            if proposal.get('is_interior'): scope_parts.append("Interior Design")
            scope = ", ".join(scope_parts) or "Design Services"
            proposal_ctx = f"""
PROPOSAL CONTEXT:
- Project Code: {proposal.get('project_code', 'Unknown')}
- Project Name: {proposal.get('project_name', 'Unknown')}
- Client: {proposal.get('client_company', 'Unknown')}
- Country: {proposal.get('country', 'Unknown')}
- Scope: {scope}
- Value: ${proposal.get('project_value', 0):,.0f}
- Status: {proposal.get('status', 'Unknown')}
- Contact: {proposal.get('contact_person', 'Unknown')} ({proposal.get('contact_email', '')})
"""

        contacts_ctx = ""
        if contacts:
            contacts_ctx = "\nKNOWN CONTACTS:\n" + "\n".join([
                f"  - {c.get('name', 'Unknown')} ({c.get('role', '')}) - {c.get('company', '')} - {c.get('email', '')}"
                for c in contacts
            ]) + "\n"

        emails_ctx = ""
        if emails:
            emails_ctx = "\nRECENT EMAILS:\n" + "\n".join([
                f"  - {e.get('date', '')}: {e.get('subject', '')} (from {e.get('sender_email', '')})"
                for e in emails
            ]) + "\n"

        previous_ctx = ""
        if previous:
            previous_ctx = "\nPREVIOUS MEETINGS:\n" + "\n".join([
                f"  - {m.get('meeting_date', '')}: {m.get('meeting_title', '')} - {m.get('summary_preview', '')}"
                for m in previous
            ]) + "\n"

        participants_str = ""
        if participants:
            if isinstance(participants, list) and participants:
                if isinstance(participants[0], dict):
                    participants_str = ", ".join([
                        f"{p.get('name', 'Unknown')} ({p.get('role', p.get('type', ''))})"
                        for p in participants
                    ])
                else:
                    participants_str = ", ".join(str(p) for p in participants)

        full_transcript = transcript.get('transcript', '')
        if len(full_transcript) > 50000:
            full_transcript = full_transcript[:50000] + "\n\n[TRANSCRIPT TRUNCATED]"

        return f"""Generate a polished meeting summary for BENSLEY Design Studios.

{proposal_ctx}
{contacts_ctx}
{emails_ctx}
{previous_ctx}

MEETING DETAILS:
- Title: {transcript.get('meeting_title', 'Meeting')}
- Date: {transcript.get('meeting_date') or transcript.get('recorded_date', 'Unknown')}
- Type: {meeting_type.replace('_', ' ').title()}
- Participants: {participants_str or 'See transcript'}
- Duration: {int((transcript.get('duration_seconds') or 0) / 60)} minutes

FULL TRANSCRIPT:
{full_transcript}

---

Generate meeting notes in this EXACT format:

[CLIENT NAME IN CAPS]
[Meeting Type Description]
[PROJECT CODE] | [Project Name]

Date & Time
[Date] | [Time]

Platform
[Zoom/Teams/In-Person]

Attendees
[Name (Affiliation)] for each person

Meeting Summary:
[2-3 paragraph summary focusing on outcomes and decisions]

📋 Projects Under Discussion
1. [Project Name] - [Location]
   Type: [type]
   Status: [status]
   Notes: [key points]

📝 Key Terms/Decisions Discussed
| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | [Topic] | [Agreed/Pending] | [Notes] |

🔧 Technical Notes
[Any technical/regulatory points - omit if none]

✅ Action Items

**BENSLEY**
| Action | Owner | Deadline |
|--------|-------|----------|
| [Action] | [Person] | [Date/TBD] |

**[CLIENT]**
| Action | Deadline |
|--------|----------|
| [Action] | [Date/TBD] |

Key Decisions Made
- [Decision 1]
- [Decision 2]

Next Steps
- Immediate: [next action]
- [Timeline]: [future action]

---
Minutes prepared from meeting recording | [Date]
Projects: [Codes] | Client: [Name]
BENSLEY Design Studios | Bangkok, Thailand

RULES:
1. Extract REAL info from transcript - don't invent
2. If unknown, omit rather than guess
3. Use format "XX BK-XXX" for project codes
4. Include emojis for headers as shown"""

    # =========================================================================
    # LISTING & SAVING
    # =========================================================================

    def list_transcripts(self, unprocessed_only: bool = False) -> List[Dict]:
        """List transcripts available for processing."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if polished_summary column exists
            cursor.execute("PRAGMA table_info(meeting_transcripts)")
            columns = [row[1] for row in cursor.fetchall()]
            has_polished = 'polished_summary' in columns

            if unprocessed_only and has_polished:
                cursor.execute("""
                    SELECT id, meeting_title, meeting_date, detected_project_code,
                           length(transcript) as transcript_len
                    FROM meeting_transcripts
                    WHERE transcript IS NOT NULL AND transcript != ''
                      AND (polished_summary IS NULL OR polished_summary = '')
                    ORDER BY created_at DESC
                """)
            else:
                cursor.execute("""
                    SELECT id, meeting_title, meeting_date, detected_project_code,
                           length(transcript) as transcript_len
                    FROM meeting_transcripts
                    WHERE transcript IS NOT NULL AND transcript != ''
                    ORDER BY created_at DESC
                """)

            return [dict(row) for row in cursor.fetchall()]

    def save_summary(self, transcript_id: int, polished_summary: str):
        """Save polished summary to database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Add column if missing
            try:
                cursor.execute("ALTER TABLE meeting_transcripts ADD COLUMN polished_summary TEXT")
            except sqlite3.OperationalError:
                pass

            cursor.execute("""
                UPDATE meeting_transcripts
                SET polished_summary = ?, processed_date = ?
                WHERE id = ?
            """, (polished_summary, datetime.now().isoformat(), transcript_id))

            conn.commit()
            print(f"✓ Saved polished summary for transcript {transcript_id}")

    def interactive_mode(self, transcript_id: int):
        """Interactive mode: show prompt, wait for summary, save."""
        print("\n" + "="*70)
        print(f"POLISHED SUMMARY GENERATOR - Transcript #{transcript_id}")
        print("="*70)

        prompt = self.build_prompt(transcript_id)
        print("\n📋 PROMPT (copy this to Claude CLI):\n")
        print("-"*70)
        print(prompt)
        print("-"*70)

        print("\n\n⏳ After getting Claude's response, paste it below.")
        print("   (Enter a blank line, then type END on its own line when done)\n")

        lines = []
        blank_count = 0
        while True:
            try:
                line = input()
                if line.strip() == "END":
                    break
                if line == "":
                    blank_count += 1
                    if blank_count >= 2:
                        print("   (Type END to finish)")
                else:
                    blank_count = 0
                lines.append(line)
            except EOFError:
                break

        summary = "\n".join(lines).strip()
        if summary:
            self.save_summary(transcript_id, summary)
            print(f"\n✅ Saved {len(summary)} characters to transcript {transcript_id}")
        else:
            print("\n⚠️ No summary provided, nothing saved.")


def main():
    parser = argparse.ArgumentParser(description='Polished Meeting Summary Generator')
    parser.add_argument('--list', action='store_true', help='List transcripts')
    parser.add_argument('--unprocessed', action='store_true', help='Show only unprocessed')
    parser.add_argument('--prepare', type=int, metavar='ID', help='Prepare prompt for transcript')
    parser.add_argument('--save', type=int, metavar='ID', help='Save summary (reads from stdin)')
    parser.add_argument('--interactive', type=int, metavar='ID', help='Interactive: show prompt, paste summary')
    parser.add_argument('--db', default=DB_PATH, help='Database path')

    args = parser.parse_args()
    gen = PolishedMeetingSummaryGenerator(args.db)

    if args.list or args.unprocessed:
        transcripts = gen.list_transcripts(unprocessed_only=args.unprocessed)
        print(f"\n{'Unprocessed t' if args.unprocessed else 'T'}ranscripts ({len(transcripts)}):\n")
        print(f"{'ID':>4} | {'Date':<12} | {'Project':<12} | {'Title':<40} | {'Len':>6}")
        print("-"*85)
        for t in transcripts:
            print(f"{t['id']:>4} | {(t.get('meeting_date') or 'Unknown'):<12} | "
                  f"{(t.get('detected_project_code') or '-'):<12} | "
                  f"{(t.get('meeting_title') or 'Untitled')[:40]:<40} | "
                  f"{t.get('transcript_len', 0):>6}")

    elif args.prepare:
        prompt = gen.build_prompt(args.prepare)
        print(prompt)

    elif args.save:
        summary = sys.stdin.read().strip()
        if summary:
            gen.save_summary(args.save, summary)
        else:
            print("No input received.")

    elif args.interactive:
        gen.interactive_mode(args.interactive)

    else:
        print("""
Polished Meeting Summary Generator

USAGE:
  # List all transcripts
  python generate_polished_meeting_summary.py --list

  # List unprocessed transcripts
  python generate_polished_meeting_summary.py --list --unprocessed

  # Get prompt for a transcript (copy to Claude CLI)
  python generate_polished_meeting_summary.py --prepare 37

  # Save summary from file
  python generate_polished_meeting_summary.py --save 37 < summary.txt

  # Interactive mode (shows prompt, you paste response)
  python generate_polished_meeting_summary.py --interactive 37

WORKFLOW:
  1. Run --list to see transcripts
  2. Run --prepare ID to get the prompt
  3. Paste prompt into Claude CLI
  4. Copy Claude's response
  5. Run --save ID and paste, OR use --interactive
""")


if __name__ == '__main__':
    main()
