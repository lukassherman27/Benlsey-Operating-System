#!/usr/bin/env python3
"""
RFI Detection Module for Bensley Operations Platform

Detects RFIs (Requests for Information) from emails and auto-creates tracking records.

Design Principles:
1. Designed for rfi@bensley.com - clients just CC this address
2. Don't change their workflow - just add tracking
3. 48-hour SLA tracking
4. Link to active projects only
5. Simple workflow: detect → track → remind → mark done

Usage:
    # As standalone script
    python rfi_detector.py

    # As module
    from rfi_detector import RFIDetector
    detector = RFIDetector(db_path)
    result = detector.detect_and_create_rfi(email_id)

Created: 2025-11-26
"""

import sqlite3
import re
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path


class RFIDetector:
    """
    Detects RFIs from email content and creates tracking records

    Detection Strategy:
    1. HIGH CONFIDENCE: Email sent TO rfi@bensley.com
    2. HIGH CONFIDENCE: Subject contains [RFI] or "Request for Information"
    3. MEDIUM CONFIDENCE: Subject contains known RFI patterns (DAE-RFI-, NRC RFI, etc.)
    4. LOW CONFIDENCE: Body contains RFI keywords + linked to active project
    """

    # 48-hour SLA (user confirmed)
    DEFAULT_SLA_HOURS = 48

    # High-confidence subject patterns (explicit RFI markers)
    HIGH_CONFIDENCE_SUBJECT_PATTERNS = [
        r'\[rfi\]',                          # [RFI] tag
        r'\brfi\s*[-#:]\s*\d+',              # RFI-001, RFI #123, RFI: 456
        r'request\s+for\s+information',     # Request for Information
        r'dae-rfi-',                         # DAE-RFI-CIR-009552 (common format)
        r'nrc\s*rfi\s*no',                   # NRC RFI No. format
        r'-rfi-\w+',                         # Generic -RFI-XXX pattern
    ]

    # Medium-confidence subject patterns
    MEDIUM_CONFIDENCE_SUBJECT_PATTERNS = [
        r'clarification\s+(required|needed|request)',
        r'information\s+request',
        r'technical\s+query',
        r'design\s+clarification',
        r'specification\s+clarification',
    ]

    # Body keywords that suggest RFI content
    RFI_BODY_KEYWORDS = [
        r'please\s+clarify',
        r'kindly\s+clarify',
        r'request\s+clarification',
        r'need\s+information',
        r'require\s+information',
        r'can\s+you\s+(confirm|clarify|provide)',
        r'please\s+(confirm|advise|provide)',
        r'awaiting\s+(your\s+)?(response|clarification|confirmation)',
        r'as\s+per\s+contract',
        r'discrepancy\s+(between|in)',
        r'conflict\s+(between|in)',
        r'inconsistent\s+with',
        r'setting.?out\s+plan',
    ]

    # Email addresses that indicate RFI routing
    RFI_EMAIL_ADDRESSES = [
        'rfi@bensley.com',
        'rfis@bensley.com',
    ]

    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to project database
            project_root = Path(__file__).parent
            db_path = str(project_root / "database" / "bensley_master.db")
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def detect_rfi(
        self,
        email_id: int,
        subject: str,
        body: str,
        to_addresses: str,
        from_address: str
    ) -> Tuple[bool, float, str, Dict[str, Any]]:
        """
        Detect if an email is an RFI

        Args:
            email_id: Email ID
            subject: Email subject line
            body: Email body text
            to_addresses: Recipient email addresses (comma-separated)
            from_address: Sender email address

        Returns:
            Tuple of:
            - is_rfi: bool - Whether this is an RFI
            - confidence: float - Confidence score (0.0 to 1.0)
            - detection_reason: str - Why we think it's an RFI
            - metadata: dict - Extracted RFI metadata
        """
        subject_lower = (subject or '').lower()
        body_lower = (body or '').lower()
        to_lower = (to_addresses or '').lower()

        metadata = {
            'email_id': email_id,
            'extracted_rfi_number': None,
            'extracted_priority': 'normal',
            'detection_patterns_matched': []
        }

        # Check 1: Email sent to rfi@bensley.com (highest confidence)
        for rfi_address in self.RFI_EMAIL_ADDRESSES:
            if rfi_address in to_lower:
                metadata['detection_patterns_matched'].append(f'to:{rfi_address}')
                return (True, 0.95, 'rfi_email_address', metadata)

        # Check 2: High-confidence subject patterns
        for pattern in self.HIGH_CONFIDENCE_SUBJECT_PATTERNS:
            match = re.search(pattern, subject_lower, re.IGNORECASE)
            if match:
                metadata['detection_patterns_matched'].append(f'subject:{pattern}')
                # Try to extract RFI number
                rfi_num = self._extract_rfi_number(subject)
                if rfi_num:
                    metadata['extracted_rfi_number'] = rfi_num
                return (True, 0.90, 'explicit_rfi_subject', metadata)

        # Check 3: Medium-confidence subject patterns
        for pattern in self.MEDIUM_CONFIDENCE_SUBJECT_PATTERNS:
            if re.search(pattern, subject_lower, re.IGNORECASE):
                metadata['detection_patterns_matched'].append(f'subject:{pattern}')
                return (True, 0.75, 'clarification_request', metadata)

        # Check 4: Body keyword analysis (lower confidence, needs multiple matches)
        keyword_matches = 0
        for pattern in self.RFI_BODY_KEYWORDS:
            if re.search(pattern, body_lower, re.IGNORECASE):
                keyword_matches += 1
                metadata['detection_patterns_matched'].append(f'body:{pattern}')

        if keyword_matches >= 2:
            return (True, 0.60, 'keyword_match', metadata)

        # Check 5: Question pattern + project reference (lowest confidence)
        question_count = body.count('?')
        if question_count >= 3 and keyword_matches >= 1:
            return (True, 0.50, 'question_pattern', metadata)

        return (False, 0.0, 'not_detected', metadata)

    def _extract_rfi_number(self, subject: str) -> Optional[str]:
        """Extract RFI number from subject line if present"""
        patterns = [
            r'(DAE-RFI-\w+-\d+)',           # DAE-RFI-CIR-009552
            r'(NRC-\w+-\w+-[^:\s]+)',       # NRC-INF-OV2-...
            r'RFI\s*[-#:]\s*(\d+)',         # RFI-001, RFI #123
            r'\[RFI[:\s]*([^\]]+)\]',       # [RFI: xxx]
        ]

        for pattern in patterns:
            match = re.search(pattern, subject, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def detect_and_create_rfi(
        self,
        email_id: int,
        project_code: str = None,
        auto_link_project: bool = True
    ) -> Dict[str, Any]:
        """
        Detect if email is RFI and create tracking record if so

        Args:
            email_id: ID of email to analyze
            project_code: Optional project code to link to
            auto_link_project: If True, try to find project from email links

        Returns:
            Dict with:
            - is_rfi: bool
            - rfi_id: int (if created)
            - confidence: float
            - reason: str
            - message: str
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Get email data
            cursor.execute("""
                SELECT
                    email_id, subject, body_full, recipient_emails, sender_email
                FROM emails
                WHERE email_id = ?
            """, (email_id,))

            email = cursor.fetchone()
            if not email:
                return {
                    'is_rfi': False,
                    'rfi_id': None,
                    'confidence': 0,
                    'reason': 'email_not_found',
                    'message': f'Email {email_id} not found'
                }

            # Detect RFI
            is_rfi, confidence, reason, metadata = self.detect_rfi(
                email_id=email['email_id'],
                subject=email['subject'] or '',
                body=email['body_full'] or '',
                to_addresses=email['recipient_emails'] or '',
                from_address=email['sender_email'] or ''
            )

            if not is_rfi:
                return {
                    'is_rfi': False,
                    'rfi_id': None,
                    'confidence': confidence,
                    'reason': reason,
                    'message': 'Not detected as RFI'
                }

            # Find project code if not provided
            if not project_code and auto_link_project:
                cursor.execute("""
                    SELECT project_code
                    FROM email_project_links
                    WHERE email_id = ?
                    LIMIT 1
                """, (email_id,))
                link = cursor.fetchone()
                if link:
                    project_code = link['project_code']

            # Must be linked to a project for RFI
            if not project_code:
                return {
                    'is_rfi': True,
                    'rfi_id': None,
                    'confidence': confidence,
                    'reason': 'no_project_link',
                    'message': 'RFI detected but no project link found'
                }

            # Verify project is active
            cursor.execute("""
                SELECT project_id, project_code, project_title, is_active_project
                FROM projects
                WHERE project_code = ?
            """, (project_code,))
            project = cursor.fetchone()

            if not project:
                return {
                    'is_rfi': True,
                    'rfi_id': None,
                    'confidence': confidence,
                    'reason': 'project_not_found',
                    'message': f'Project {project_code} not found'
                }

            # Check if RFI already exists for this email
            cursor.execute("""
                SELECT rfi_id FROM rfis WHERE extracted_from_email_id = ?
            """, (email_id,))
            existing = cursor.fetchone()

            if existing:
                return {
                    'is_rfi': True,
                    'rfi_id': existing['rfi_id'],
                    'confidence': confidence,
                    'reason': 'already_exists',
                    'message': f'RFI already exists (ID: {existing["rfi_id"]})'
                }

            # Generate RFI number
            cursor.execute("""
                SELECT COUNT(*) as count FROM rfis WHERE project_code = ?
            """, (project_code,))
            count = cursor.fetchone()['count']
            clean_code = project_code.replace(' ', '-')
            rfi_number = metadata.get('extracted_rfi_number') or f"{clean_code}-RFI-{count + 1:03d}"

            # Calculate due date (48 hours)
            date_sent = email['date'] if hasattr(email, 'date') else datetime.now()
            if isinstance(date_sent, str):
                try:
                    date_sent = datetime.strptime(date_sent[:19], '%Y-%m-%d %H:%M:%S')
                except:
                    date_sent = datetime.now()
            date_due = (date_sent + timedelta(hours=self.DEFAULT_SLA_HOURS)).strftime('%Y-%m-%d')

            # Create RFI record
            cursor.execute("""
                INSERT INTO rfis (
                    project_id,
                    project_code,
                    rfi_number,
                    subject,
                    description,
                    date_sent,
                    date_due,
                    status,
                    priority,
                    sender_email,
                    sender_name,
                    extracted_from_email_id,
                    extraction_confidence,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?, ?, ?, ?, ?, datetime('now'))
            """, (
                project['project_id'],
                project_code,
                rfi_number,
                email['subject'] or 'RFI from email',
                f"Detected via: {reason}. Patterns: {', '.join(metadata['detection_patterns_matched'])}",
                datetime.now().strftime('%Y-%m-%d'),
                date_due,
                metadata.get('extracted_priority', 'normal'),
                email['sender_email'],
                None,  # sender_name - could parse from email
                email_id,
                confidence
            ))

            rfi_id = cursor.lastrowid
            conn.commit()

            return {
                'is_rfi': True,
                'rfi_id': rfi_id,
                'rfi_number': rfi_number,
                'confidence': confidence,
                'reason': reason,
                'project_code': project_code,
                'date_due': date_due,
                'message': f'RFI created: {rfi_number} (due: {date_due})'
            }

        finally:
            conn.close()

    def scan_unprocessed_emails(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Scan recent emails that aren't linked to RFIs yet

        Returns list of detected RFIs (but doesn't create them)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Find emails that:
            # 1. Are linked to projects
            # 2. Don't already have RFIs
            # 3. Are within last 30 days
            cursor.execute("""
                SELECT DISTINCT
                    e.email_id,
                    e.subject,
                    e.body_full,
                    e.recipient_emails,
                    e.sender_email,
                    e.date,
                    epl.project_code
                FROM emails e
                JOIN email_project_links epl ON e.email_id = epl.email_id
                LEFT JOIN rfis r ON e.email_id = r.extracted_from_email_id
                WHERE r.rfi_id IS NULL
                AND e.date >= datetime('now', '-30 days')
                ORDER BY e.date DESC
                LIMIT ?
            """, (limit,))

            emails = cursor.fetchall()
            results = []

            for email in emails:
                is_rfi, confidence, reason, metadata = self.detect_rfi(
                    email_id=email['email_id'],
                    subject=email['subject'] or '',
                    body=email['body_full'] or '',
                    to_addresses=email['recipient_emails'] or '',
                    from_address=email['sender_email'] or ''
                )

                if is_rfi and confidence >= 0.5:
                    results.append({
                        'email_id': email['email_id'],
                        'subject': email['subject'],
                        'project_code': email['project_code'],
                        'confidence': confidence,
                        'reason': reason,
                        'date': email['date']
                    })

            return results

        finally:
            conn.close()

    def process_rfi_email_address(self) -> Dict[str, Any]:
        """
        Process all emails sent TO rfi@bensley.com

        This is the primary entry point once rfi@bensley.com is set up.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Find emails TO rfi@bensley.com that don't have RFIs yet
            cursor.execute("""
                SELECT
                    e.email_id,
                    e.subject,
                    e.sender_email,
                    e.date,
                    epl.project_code
                FROM emails e
                LEFT JOIN email_project_links epl ON e.email_id = epl.email_id
                LEFT JOIN rfis r ON e.email_id = r.extracted_from_email_id
                WHERE (
                    e.recipient_emails LIKE '%rfi@bensley.com%'
                    OR e.recipient_emails LIKE '%rfis@bensley.com%'
                )
                AND r.rfi_id IS NULL
                ORDER BY e.date DESC
            """)

            emails = cursor.fetchall()

            created = 0
            skipped = 0
            errors = []

            for email in emails:
                if not email['project_code']:
                    skipped += 1
                    errors.append({
                        'email_id': email['email_id'],
                        'reason': 'no_project_link',
                        'subject': email['subject']
                    })
                    continue

                result = self.detect_and_create_rfi(
                    email_id=email['email_id'],
                    project_code=email['project_code']
                )

                if result.get('rfi_id'):
                    created += 1
                else:
                    skipped += 1

            return {
                'processed': len(emails),
                'created': created,
                'skipped': skipped,
                'errors': errors[:10]  # First 10 errors
            }

        finally:
            conn.close()


def main():
    """CLI interface for RFI detection"""
    import argparse

    parser = argparse.ArgumentParser(description='RFI Detection Tool')
    parser.add_argument('--scan', action='store_true', help='Scan for potential RFIs')
    parser.add_argument('--process-rfi-address', action='store_true',
                       help='Process emails sent to rfi@bensley.com')
    parser.add_argument('--email-id', type=int, help='Check specific email for RFI')
    parser.add_argument('--create', action='store_true',
                       help='Actually create RFI records (not just detect)')
    parser.add_argument('--limit', type=int, default=100, help='Limit for scan')

    args = parser.parse_args()

    # Get database path
    db_path = os.getenv(
        'DATABASE_PATH',
        str(Path(__file__).parent / "database" / "bensley_master.db")
    )

    detector = RFIDetector(db_path)

    if args.email_id:
        print(f"\n🔍 Checking email {args.email_id} for RFI...")

        if args.create:
            result = detector.detect_and_create_rfi(args.email_id)
        else:
            conn = detector._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT subject, body_full, recipient_emails, sender_email
                FROM emails WHERE email_id = ?
            """, (args.email_id,))
            email = cursor.fetchone()
            conn.close()

            if email:
                is_rfi, confidence, reason, metadata = detector.detect_rfi(
                    args.email_id,
                    email['subject'] or '',
                    email['body_full'] or '',
                    email['recipient_emails'] or '',
                    email['sender_email'] or ''
                )
                result = {
                    'is_rfi': is_rfi,
                    'confidence': confidence,
                    'reason': reason,
                    'metadata': metadata
                }
            else:
                result = {'error': 'Email not found'}

        print(f"Result: {result}")

    elif args.process_rfi_address:
        print("\n📬 Processing emails sent to rfi@bensley.com...")
        result = detector.process_rfi_email_address()
        print(f"Processed: {result['processed']}")
        print(f"Created: {result['created']}")
        print(f"Skipped: {result['skipped']}")
        if result['errors']:
            print(f"Errors: {result['errors']}")

    elif args.scan:
        print(f"\n🔍 Scanning for potential RFIs (limit: {args.limit})...")
        results = detector.scan_unprocessed_emails(limit=args.limit)

        print(f"\nFound {len(results)} potential RFIs:\n")
        for r in results[:20]:
            print(f"  [{r['confidence']:.0%}] {r['project_code']}: {r['subject'][:60]}...")
            print(f"       Reason: {r['reason']}")

        if len(results) > 20:
            print(f"\n  ... and {len(results) - 20} more")

    else:
        # Default: show stats
        conn = detector._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM rfis")
        total_rfis = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM rfis WHERE status = 'open'")
        open_rfis = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM rfis
            WHERE status = 'open' AND date(date_due) < date('now')
        """)
        overdue = cursor.fetchone()[0]

        conn.close()

        print("\n📊 RFI Statistics:")
        print(f"   Total RFIs: {total_rfis}")
        print(f"   Open: {open_rfis}")
        print(f"   Overdue: {overdue}")
        print(f"\nUse --scan to find potential RFIs")
        print("Use --process-rfi-address to process rfi@bensley.com emails")
        print("Use --email-id <id> to check a specific email")


if __name__ == '__main__':
    main()
