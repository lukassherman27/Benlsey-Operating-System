"""
Meeting Briefing Service - Generate pre-meeting briefings with project context

Creates comprehensive briefings for upcoming meetings that include:
- Project overview (status, fee, location)
- Recent activity (emails, meetings)
- Key contacts
- Financial summary
- Suggested talking points

Created: 2025-11-26 by Agent 5 (Bensley Brain Intelligence)
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from openai import OpenAI

DB_PATH = os.getenv("DATABASE_PATH", "database/bensley_master.db")


class MeetingBriefingService:
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
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # =========================================================================
    # DATA GATHERING
    # =========================================================================

    def get_project_overview(self, project_code: str) -> Dict:
        """Get comprehensive project/proposal info"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Try proposals first (more detailed)
        cursor.execute("""
            SELECT
                p.proposal_id, p.project_code, p.project_name,
                p.status, p.health_score, p.days_since_contact,
                p.is_active_project, p.client_company,
                p.project_value, p.country, p.location as city,
                p.created_at, p.updated_at
            FROM proposals p
            WHERE p.project_code LIKE ?
            LIMIT 1
        """, (f"%{project_code}%",))

        row = cursor.fetchone()
        if row:
            result = dict(row)
        else:
            result = {}

        # Get additional project info if it's an active project
        cursor.execute("""
            SELECT
                project_id, project_code, project_title,
                status, total_fee_usd as contract_value, project_type as discipline
            FROM projects
            WHERE project_code LIKE ?
            LIMIT 1
        """, (f"%{project_code}%",))

        project_row = cursor.fetchone()
        if project_row:
            result.update({
                'project_id': project_row['project_id'],
                'contract_value': project_row['total_contract_value'],
                'discipline': project_row['discipline']
            })

        conn.close()
        return result

    def get_financial_summary(self, project_code: str) -> Dict:
        """Get financial summary for project"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get invoice summary
        cursor.execute("""
            SELECT
                COUNT(*) as invoice_count,
                SUM(invoice_amount) as total_invoiced,
                SUM(CASE WHEN payment_date IS NOT NULL THEN payment_amount ELSE 0 END) as total_paid,
                SUM(CASE WHEN payment_date IS NULL THEN invoice_amount ELSE 0 END) as outstanding
            FROM invoices i
            JOIN projects p ON i.project_id = p.project_id
            WHERE p.project_code LIKE ?
        """, (f"%{project_code}%",))

        row = cursor.fetchone()
        result = dict(row) if row else {}

        # Get fee breakdown by discipline
        cursor.execute("""
            SELECT discipline, phase, phase_fee_usd, total_invoiced, total_paid
            FROM project_fee_breakdown
            WHERE project_code LIKE ?
            ORDER BY discipline, phase
        """, (f"%{project_code}%",))

        result['fee_breakdown'] = [dict(r) for r in cursor.fetchall()]

        conn.close()
        return result

    def get_recent_emails(self, project_code: str, limit: int = 10) -> List[Dict]:
        """Get recent emails for project"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                e.email_id, e.subject, e.sender_email, e.date,
                e.snippet, e.body_preview
            FROM emails e
            JOIN email_project_links epl ON e.email_id = epl.email_id
            JOIN projects p ON epl.project_id = p.project_id
            WHERE p.project_code LIKE ?
            ORDER BY e.date DESC
            LIMIT ?
        """, (f"%{project_code}%", limit))

        emails = [dict(row) for row in cursor.fetchall()]

        # Also check proposal links
        if not emails:
            cursor.execute("""
                SELECT
                    e.email_id, e.subject, e.sender_email, e.date,
                    e.snippet, e.body_preview
                FROM emails e
                JOIN email_proposal_links epl ON e.email_id = epl.email_id
                JOIN proposals p ON epl.proposal_id = p.proposal_id
                WHERE p.project_code LIKE ?
                ORDER BY e.date DESC
                LIMIT ?
            """, (f"%{project_code}%", limit))
            emails = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return emails

    def get_meeting_transcripts(self, project_code: str, limit: int = 5) -> List[Dict]:
        """Get recent meeting transcripts"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id, audio_filename, summary, key_points,
                action_items, participants, meeting_type,
                sentiment, recorded_date, processed_date
            FROM meeting_transcripts
            WHERE detected_project_code LIKE ?
            ORDER BY COALESCE(recorded_date, processed_date) DESC
            LIMIT ?
        """, (f"%{project_code}%", limit))

        transcripts = []
        for row in cursor.fetchall():
            t = dict(row)
            # Parse JSON fields
            for field in ['key_points', 'action_items', 'participants']:
                if t.get(field):
                    try:
                        t[field] = json.loads(t[field])
                    except (json.JSONDecodeError, TypeError):
                        pass
            transcripts.append(t)

        conn.close()
        return transcripts

    def get_key_contacts(self, project_code: str) -> List[Dict]:
        """Get contacts associated with project"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get contacts from emails linked to project
        cursor.execute("""
            SELECT DISTINCT
                c.contact_id, c.name, c.email,
                c.role, c.phone,
                MAX(e.date) as last_seen
            FROM contacts c
            JOIN emails e ON c.email = e.sender_email
            JOIN email_project_links epl ON e.email_id = epl.email_id
            JOIN projects p ON epl.project_id = p.project_id
            WHERE p.project_code LIKE ?
            GROUP BY c.contact_id
            ORDER BY last_seen DESC
            LIMIT 10
        """, (f"%{project_code}%",))

        contacts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return contacts

    def get_open_rfis(self, project_code: str) -> List[Dict]:
        """Get open RFIs for project"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                rfi_id, rfi_number, subject, status,
                date_sent, date_due, priority
            FROM rfis
            WHERE project_code LIKE ?
            AND status = 'open'
            ORDER BY date_due ASC
        """, (f"%{project_code}%",))

        rfis = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rfis

    # =========================================================================
    # BRIEFING GENERATION
    # =========================================================================

    def generate_briefing(self, meeting_id: int = None, project_code: str = None,
                          meeting_purpose: str = None) -> Dict[str, Any]:
        """
        Generate comprehensive pre-meeting briefing.

        Args:
            meeting_id: ID of meeting to generate briefing for
            project_code: Project code (alternative to meeting_id)
            meeting_purpose: Optional context about meeting purpose

        Returns:
            Dict with briefing content and metadata
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get meeting info if ID provided
        meeting = None
        if meeting_id:
            cursor.execute("SELECT * FROM meetings WHERE meeting_id = ?", (meeting_id,))
            row = cursor.fetchone()
            if row:
                meeting = dict(row)
                project_code = meeting.get('project_code')
                meeting_purpose = meeting_purpose or meeting.get('description')

        if not project_code:
            return {'success': False, 'error': 'No project code provided'}

        # Gather all context
        context = {
            'project': self.get_project_overview(project_code),
            'financial': self.get_financial_summary(project_code),
            'emails': self.get_recent_emails(project_code),
            'transcripts': self.get_meeting_transcripts(project_code),
            'contacts': self.get_key_contacts(project_code),
            'rfis': self.get_open_rfis(project_code),
            'meeting': meeting,
            'purpose': meeting_purpose
        }

        # Generate briefing using AI or template
        if self.client:
            briefing_content = self._generate_ai_briefing(context)
        else:
            briefing_content = self._generate_template_briefing(context)

        # Cache briefing if meeting_id provided
        if meeting_id:
            cursor.execute("""
                UPDATE meetings
                SET briefing_generated = 1,
                    briefing_content = ?,
                    briefing_generated_at = datetime('now')
                WHERE meeting_id = ?
            """, (briefing_content, meeting_id))
            conn.commit()

        conn.close()

        return {
            'success': True,
            'briefing': briefing_content,
            'project_code': project_code,
            'generated_at': datetime.now().isoformat(),
            'context_summary': {
                'emails_count': len(context['emails']),
                'transcripts_count': len(context['transcripts']),
                'contacts_count': len(context['contacts']),
                'rfis_count': len(context['rfis'])
            }
        }

    def _generate_ai_briefing(self, context: Dict) -> str:
        """Generate briefing using AI"""
        project = context.get('project', {})
        financial = context.get('financial', {})
        emails = context.get('emails', [])
        transcripts = context.get('transcripts', [])
        contacts = context.get('contacts', [])
        rfis = context.get('rfis', [])
        meeting = context.get('meeting', {})
        purpose = context.get('purpose', '')

        prompt = f"""Generate a professional pre-meeting briefing for a design studio meeting.

## Meeting Context
{f"Purpose: {purpose}" if purpose else "General project discussion"}
{f"Date: {meeting.get('meeting_date')}" if meeting else ""}
{f"Type: {meeting.get('meeting_type')}" if meeting else ""}

## Project Information
- Name: {project.get('project_name', 'Unknown')}
- Code: {project.get('project_code', 'Unknown')}
- Status: {project.get('status', 'Unknown')}
- Location: {project.get('city', '')}, {project.get('country', '')}
- Value: ${project.get('project_value', 0):,.0f}
- Days since contact: {project.get('days_since_contact', 'Unknown')}

## Financial Summary
- Total Invoiced: ${financial.get('total_invoiced', 0) or 0:,.0f}
- Total Paid: ${financial.get('total_paid', 0) or 0:,.0f}
- Outstanding: ${financial.get('outstanding', 0) or 0:,.0f}

## Recent Emails (last {len(emails)}):
{chr(10).join([f"- {e.get('date', 'N/A')}: {e.get('subject', 'No subject')} (from {e.get('sender_email', 'unknown')})" for e in emails[:5]])}

## Previous Meetings ({len(transcripts)} transcripts):
{chr(10).join([f"- {t.get('recorded_date', 'N/A')}: {t.get('summary', 'No summary')[:200]}..." for t in transcripts[:3]]) if transcripts else "No previous meeting transcripts"}

## Key Contacts:
{chr(10).join([f"- {c.get('name', 'Unknown')} ({c.get('role', 'N/A')}) - {c.get('email', 'N/A')}" for c in contacts[:5]]) if contacts else "No contacts linked"}

## Open RFIs: {len(rfis)}
{chr(10).join([f"- RFI {r.get('rfi_number', 'N/A')}: {r.get('subject', 'No subject')} (due: {r.get('date_due', 'N/A')})" for r in rfis[:3]]) if rfis else "No open RFIs"}

---
Generate a professional briefing document with these sections:
1. **Meeting Briefing Header** (project name, date, purpose)
2. **Project Overview** (status, location, value - 2-3 sentences)
3. **Recent Activity** (bullet points of key recent events from emails/meetings)
4. **Key Contacts** (who to expect, their roles)
5. **Financial Status** (brief summary)
6. **Open Items** (RFIs, pending decisions)
7. **Suggested Talking Points** (3-5 points based on recent activity)
8. **Preparation Notes** (anything they should review before meeting)

Format in clean Markdown. Be concise but comprehensive."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use better model for briefings
                messages=[
                    {"role": "system", "content": "You are an executive assistant preparing meeting briefings for a luxury design studio. Be professional, concise, and actionable."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"AI briefing failed: {e}")
            return self._generate_template_briefing(context)

    def _generate_template_briefing(self, context: Dict) -> str:
        """Generate briefing using template (no AI)"""
        project = context.get('project', {})
        financial = context.get('financial', {})
        emails = context.get('emails', [])
        transcripts = context.get('transcripts', [])
        contacts = context.get('contacts', [])
        rfis = context.get('rfis', [])
        meeting = context.get('meeting', {})

        briefing = f"""# Meeting Briefing: {project.get('project_name', 'Unknown Project')}

**Project Code:** {project.get('project_code', 'N/A')}
**Date:** {meeting.get('meeting_date', datetime.now().strftime('%Y-%m-%d'))}
**Type:** {meeting.get('meeting_type', 'General Discussion')}

---

## Project Overview
- **Status:** {project.get('status', 'Unknown')}
- **Location:** {project.get('city', 'N/A')}, {project.get('country', 'N/A')}
- **Value:** ${project.get('project_value', 0):,.0f}
- **Days Since Contact:** {project.get('days_since_contact', 'N/A')}

---

## Financial Summary
| Metric | Amount |
|--------|--------|
| Total Invoiced | ${financial.get('total_invoiced', 0) or 0:,.0f} |
| Total Paid | ${financial.get('total_paid', 0) or 0:,.0f} |
| Outstanding | ${financial.get('outstanding', 0) or 0:,.0f} |

---

## Recent Activity
"""
        for email in emails[:5]:
            briefing += f"- **{email.get('date', 'N/A')}**: {email.get('subject', 'No subject')}\n"

        briefing += "\n---\n\n## Key Contacts\n"
        for contact in contacts[:5]:
            briefing += f"- **{contact.get('name', 'Unknown')}** ({contact.get('role', 'N/A')}) - {contact.get('email', 'N/A')}\n"

        if rfis:
            briefing += "\n---\n\n## Open RFIs\n"
            for rfi in rfis:
                briefing += f"- **{rfi.get('rfi_number', 'N/A')}**: {rfi.get('subject', 'No subject')} (Due: {rfi.get('date_due', 'N/A')})\n"

        briefing += "\n---\n\n*Briefing generated automatically. Please review project files for full context.*"

        return briefing

    # =========================================================================
    # BRIEFING RETRIEVAL
    # =========================================================================

    def get_upcoming_briefings_needed(self, days: int = 7) -> List[Dict]:
        """Get meetings in next N days that need briefings"""
        conn = self._get_connection()
        cursor = conn.cursor()

        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

        cursor.execute("""
            SELECT
                meeting_id, title, meeting_date, start_time,
                project_code, meeting_type, briefing_generated
            FROM meetings
            WHERE meeting_date BETWEEN ? AND ?
            AND status NOT IN ('cancelled')
            AND (briefing_generated = 0 OR briefing_generated IS NULL)
            ORDER BY meeting_date, start_time
        """, (start_date, end_date))

        meetings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return meetings


# CLI for testing
if __name__ == '__main__':
    import sys

    service = MeetingBriefingService()

    if len(sys.argv) > 1:
        project_code = sys.argv[1]
        purpose = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else None

        print(f"\n📋 Generating briefing for {project_code}...\n")

        result = service.generate_briefing(project_code=project_code, meeting_purpose=purpose)

        if result['success']:
            print(result['briefing'])
        else:
            print(f"❌ Error: {result.get('error')}")

    else:
        print("Usage: python meeting_briefing_service.py <project_code> [meeting purpose]")
        print("\nExample:")
        print("  python meeting_briefing_service.py '25 BK-076' 'proposal discussion'")
