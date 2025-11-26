#!/usr/bin/env python3
"""
Email Meeting Extractor - Extract meeting requests from emails

Detects meeting-related emails and creates calendar entries:
- "Let's meet Tuesday at 3pm"
- "Can we schedule a call?"
- Calendar invites (.ics attachments)
- Meeting confirmations

Usage:
    python email_meeting_extractor.py --scan          # Scan recent emails for meetings
    python email_meeting_extractor.py --process 123  # Process specific email
    python email_meeting_extractor.py --auto         # Auto-create meetings

Created: 2025-11-26 by Agent 5 (Bensley Brain Intelligence)
"""

import sqlite3
import os
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')

# Add backend to path
import sys
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backend')
sys.path.insert(0, backend_path)

try:
    from services.calendar_service import CalendarService
    CALENDAR_SERVICE_AVAILABLE = True
except ImportError:
    CALENDAR_SERVICE_AVAILABLE = False


class EmailMeetingExtractor:
    """Extract meeting information from emails"""

    # Keywords that suggest meeting requests
    MEETING_KEYWORDS = [
        r'let\'?s\s+meet',
        r'can\s+we\s+(meet|schedule|arrange)',
        r'would\s+you\s+be\s+available',
        r'schedule\s+a\s+(call|meeting|zoom)',
        r'set\s+up\s+a\s+(meeting|call)',
        r'book\s+a\s+meeting',
        r'meeting\s+invitation',
        r'calendar\s+invite',
        r'confirm\s+(meeting|call)',
        r'reschedule\s+(the\s+)?(meeting|call)',
        r'(?:presentation|review|kickoff)\s+(?:meeting|call)',
        r'design\s+review',
        r'concept\s+presentation',
    ]

    # Date/time patterns
    TIME_PATTERNS = [
        r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)',
        r'(\d{1,2}):(\d{2})',
        r'at\s+(\d{1,2})\s*(o\'?clock)?',
    ]

    DATE_PATTERNS = [
        r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
        r'(today|tomorrow|next\s+week)',
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)(?:uary|ruary|ch|il|e|y|ust|tember|ober|ember)?\s+(\d{1,2})',
        r'(\d{1,2})[/-](\d{1,2})[/-]?(\d{2,4})?',
    ]

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self.client = None
        self._init_openai()
        self.calendar_service = CalendarService(self.db_path) if CALENDAR_SERVICE_AVAILABLE else None

    def _init_openai(self):
        """Initialize OpenAI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def has_meeting_indicators(self, subject: str, body: str) -> Tuple[bool, float]:
        """
        Quick check if email likely contains meeting info.

        Returns:
            (has_indicators, confidence_score)
        """
        text = f"{subject} {body}".lower()
        matches = 0

        for pattern in self.MEETING_KEYWORDS:
            if re.search(pattern, text, re.IGNORECASE):
                matches += 1

        # Also check for time/date patterns
        has_time = any(re.search(p, text, re.IGNORECASE) for p in self.TIME_PATTERNS)
        has_date = any(re.search(p, text, re.IGNORECASE) for p in self.DATE_PATTERNS)

        # Check for .ics attachment mention
        has_ics = '.ics' in text or 'calendar' in text or 'invite' in text

        # Calculate confidence
        if matches >= 2 or (matches >= 1 and (has_time or has_date)):
            confidence = min(0.9, 0.5 + (matches * 0.1) + (0.2 if has_time else 0) + (0.2 if has_date else 0))
            return True, confidence
        elif has_ics and (has_time or has_date):
            return True, 0.7
        elif matches >= 1:
            return True, 0.4

        return False, 0.0

    def extract_meeting_from_email(self, email_id: int) -> Dict[str, Any]:
        """
        Extract meeting details from an email using AI.

        Args:
            email_id: Email ID to analyze

        Returns:
            Dict with meeting details or empty dict if no meeting detected
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                e.email_id, e.subject, e.body_full, e.sender_email, e.date,
                ec.linked_project_code, ec.category
            FROM emails e
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE e.email_id = ?
        """, (email_id,))

        row = cursor.fetchone()
        if not row:
            return {'detected': False, 'reason': 'email_not_found'}

        email = dict(row)
        subject = email.get('subject', '')
        body = email.get('body_full', '')

        # Quick check first
        has_meeting, confidence = self.has_meeting_indicators(subject, body)
        if not has_meeting:
            return {'detected': False, 'reason': 'no_meeting_indicators', 'confidence': confidence}

        # Use AI for detailed extraction
        if self.client:
            result = self._ai_extract_meeting(email)
        else:
            result = self._regex_extract_meeting(email)

        result['email_id'] = email_id
        result['project_code'] = email.get('linked_project_code')
        result['source'] = 'email_extracted'

        conn.close()
        return result

    def _ai_extract_meeting(self, email: Dict) -> Dict:
        """Use AI to extract meeting details"""
        prompt = f"""Analyze this email for meeting/call scheduling information.

EMAIL:
From: {email.get('sender_email', 'unknown')}
Subject: {email.get('subject', '')}
Date: {email.get('date', '')}
Body:
{email.get('body_full', '')[:2000]}

TODAY'S DATE: {datetime.now().strftime('%Y-%m-%d')}

If this email is scheduling, confirming, or discussing a meeting/call, extract:
{{
    "detected": true,
    "meeting_title": "Inferred meeting title",
    "meeting_type": "proposal_discussion|concept_presentation|design_review|client_call|internal|site_visit|contract_negotiation|kickoff|progress_update|other",
    "meeting_date": "YYYY-MM-DD or null if not determinable",
    "start_time": "HH:MM (24hr) or null",
    "end_time": "HH:MM or null",
    "location": "Location or 'Zoom'/'Teams' for video calls",
    "participants": ["list of people mentioned"],
    "purpose": "Brief description of meeting purpose",
    "is_confirmation": true/false (is this confirming an existing meeting?),
    "is_rescheduling": true/false,
    "confidence": 0.0-1.0
}}

If NOT a meeting-related email:
{{
    "detected": false,
    "reason": "why not a meeting email"
}}

IMPORTANT:
- Convert relative dates (Tuesday, next week) to actual dates based on today
- If meeting is in past, still extract but note it
- For video calls, set location to the platform (Zoom, Teams, etc.)

Return ONLY valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You extract meeting scheduling information from emails."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )

            content = response.choices[0].message.content.strip()

            # Clean JSON
            if content.startswith("```"):
                content = re.sub(r'^```json?\s*', '', content)
                content = re.sub(r'\s*```$', '', content)

            return json.loads(content)

        except Exception as e:
            print(f"AI extraction failed: {e}")
            return self._regex_extract_meeting(email)

    def _regex_extract_meeting(self, email: Dict) -> Dict:
        """Fallback regex-based extraction"""
        subject = email.get('subject', '')
        body = email.get('body_full', '')
        text = f"{subject} {body}".lower()

        result = {
            'detected': True,
            'meeting_title': subject[:100] if subject else 'Meeting from email',
            'meeting_type': 'other',
            'meeting_date': None,
            'start_time': None,
            'participants': [],
            'confidence': 0.5
        }

        # Extract time
        for pattern in self.TIME_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                hour = int(groups[0])
                minute = int(groups[1]) if len(groups) > 1 and groups[1] else 0
                ampm = groups[2].lower() if len(groups) > 2 and groups[2] else None

                if ampm == 'pm' and hour < 12:
                    hour += 12
                elif ampm == 'am' and hour == 12:
                    hour = 0

                result['start_time'] = f"{hour:02d}:{minute:02d}"
                break

        # Extract date
        today = datetime.now()
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

        for i, day in enumerate(days):
            if day in text:
                days_ahead = i - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                result['meeting_date'] = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
                break

        if not result['meeting_date']:
            if 'today' in text:
                result['meeting_date'] = today.strftime('%Y-%m-%d')
            elif 'tomorrow' in text:
                result['meeting_date'] = (today + timedelta(days=1)).strftime('%Y-%m-%d')

        # Detect meeting type
        if any(x in text for x in ['concept', 'presentation', 'present']):
            result['meeting_type'] = 'concept_presentation'
        elif any(x in text for x in ['design review', 'review session']):
            result['meeting_type'] = 'design_review'
        elif any(x in text for x in ['kickoff', 'kick-off', 'kick off']):
            result['meeting_type'] = 'kickoff'
        elif any(x in text for x in ['proposal', 'fee', 'contract']):
            result['meeting_type'] = 'proposal_discussion'
        elif any(x in text for x in ['call', 'phone', 'zoom', 'teams']):
            result['meeting_type'] = 'client_call'

        return result

    def scan_recent_emails(self, days: int = 7, limit: int = 100) -> List[Dict]:
        """
        Scan recent emails for meeting requests.

        Returns:
            List of emails with detected meetings
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                e.email_id, e.subject, e.body_full, e.sender_email, e.date,
                ec.linked_project_code, ec.category
            FROM emails e
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            LEFT JOIN meetings m ON e.email_id = m.source_email_id
            WHERE e.date > datetime('now', '-' || ? || ' days')
            AND m.meeting_id IS NULL  -- Not already extracted
            AND (ec.category = 'meeting' OR e.subject LIKE '%meeting%' OR e.subject LIKE '%call%')
            ORDER BY e.date DESC
            LIMIT ?
        """, (days, limit))

        emails = [dict(row) for row in cursor.fetchall()]
        conn.close()

        results = []
        for email in emails:
            has_meeting, confidence = self.has_meeting_indicators(
                email.get('subject', ''),
                email.get('body_full', '')
            )

            if has_meeting and confidence >= 0.4:
                results.append({
                    'email_id': email['email_id'],
                    'subject': email['subject'],
                    'date': email['date'],
                    'sender': email['sender_email'],
                    'project_code': email.get('linked_project_code'),
                    'confidence': confidence
                })

        return results

    def create_meeting_from_email(self, email_id: int, auto_create: bool = False) -> Dict:
        """
        Extract meeting from email and optionally create calendar entry.

        Args:
            email_id: Email to process
            auto_create: If True, automatically create meeting in database

        Returns:
            Dict with extraction results and meeting_id if created
        """
        extraction = self.extract_meeting_from_email(email_id)

        if not extraction.get('detected'):
            return extraction

        if not extraction.get('meeting_date'):
            extraction['message'] = 'Meeting detected but date could not be determined'
            return extraction

        if auto_create and self.calendar_service:
            # Create meeting via calendar service
            meeting_data = {
                'title': extraction.get('meeting_title', 'Meeting from email'),
                'meeting_type': extraction.get('meeting_type', 'other'),
                'meeting_date': extraction.get('meeting_date'),
                'start_time': extraction.get('start_time'),
                'end_time': extraction.get('end_time'),
                'location': extraction.get('location'),
                'project_code': extraction.get('project_code'),
                'participants': extraction.get('participants', []),
                'description': extraction.get('purpose'),
                'source': 'email_extracted',
                'source_email_id': email_id,
                'extraction_confidence': extraction.get('confidence', 0.5)
            }

            result = self.calendar_service.create_meeting(meeting_data)
            extraction['meeting_created'] = result.get('success', False)
            extraction['meeting_id'] = result.get('meeting_id')
            extraction['message'] = result.get('message')
        else:
            extraction['meeting_created'] = False
            extraction['message'] = 'Meeting detected - use --auto to create automatically'

        return extraction


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Extract meetings from emails')
    parser.add_argument('--scan', action='store_true', help='Scan recent emails for meetings')
    parser.add_argument('--process', type=int, help='Process specific email ID')
    parser.add_argument('--auto', action='store_true', help='Auto-create meetings from detected emails')
    parser.add_argument('--days', type=int, default=7, help='Days to scan (default: 7)')
    parser.add_argument('--limit', type=int, default=50, help='Max emails to scan')

    args = parser.parse_args()

    extractor = EmailMeetingExtractor()

    if args.process:
        print(f"\n📧 Processing email {args.process}...")
        result = extractor.create_meeting_from_email(args.process, auto_create=args.auto)
        print(json.dumps(result, indent=2, default=str))

    elif args.scan:
        print(f"\n🔍 Scanning last {args.days} days for meeting emails...")
        candidates = extractor.scan_recent_emails(days=args.days, limit=args.limit)

        print(f"\nFound {len(candidates)} potential meetings:\n")
        for c in candidates:
            print(f"  [{c['confidence']:.0%}] ID:{c['email_id']} - {c['subject'][:50]}...")
            if c.get('project_code'):
                print(f"        Project: {c['project_code']}")

        if args.auto and candidates:
            print(f"\n⚡ Auto-creating meetings...")
            created = 0
            for c in candidates:
                if c['confidence'] >= 0.6:
                    result = extractor.create_meeting_from_email(c['email_id'], auto_create=True)
                    if result.get('meeting_created'):
                        created += 1
                        print(f"  ✅ Created: {result.get('message')}")
            print(f"\n✅ Created {created} meetings")

    else:
        print("Usage:")
        print("  python email_meeting_extractor.py --scan           # Find meeting emails")
        print("  python email_meeting_extractor.py --scan --auto    # Find and create meetings")
        print("  python email_meeting_extractor.py --process 123    # Check specific email")


if __name__ == '__main__':
    main()
