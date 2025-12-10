#!/usr/bin/env python3
"""
Smart Email Categorizer - Multi-Pass Email Processing

This script processes emails through multiple passes:
1. Direction Detection (internal/outbound/inbound)
2. Category Assignment (internal categories or project categories)
3. Project Extraction (find project codes even in internal emails)
4. Contact Mapping (link contacts to projects)

Usage:
    python scripts/core/smart_categorizer.py                    # Process uncategorized
    python scripts/core/smart_categorizer.py --all              # Reprocess all
    python scripts/core/smart_categorizer.py --email-id 12345   # Process specific email
    python scripts/core/smart_categorizer.py --dry-run          # Preview without changes

Created: 2025-12-08
"""

import sqlite3
import re
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = os.getenv('DATABASE_PATH', str(PROJECT_ROOT / 'database' / 'bensley_master.db'))

# ============================================================================
# CONFIGURATION - These rules are learned from manual categorization
# ============================================================================

# Bensley email domains
BENSLEY_DOMAINS = ['bensley.com', 'bensley.co.id', 'bensley.co.th']

# Internal category patterns (keyword → category_id)
# category_id: 1=INT-FIN, 2=INT-OPS, 3=INT-LEGAL, 4=INT-MKTG, 5=INT-BILL
INTERNAL_PATTERNS = {
    # INT-OPS (Operations/Scheduling)
    'daily work': 2,
    'schedule': 2,
    'resource allocation': 2,
    'weekly resource': 2,
    'staff schedule': 2,
    'work staff': 2,
    'bos': 2,
    'bensley brain': 2,

    # INT-FIN (Financial)
    'invoice': 1,
    'payment': 1,
    'expense': 1,
    'reimbursement': 1,
    'accounting': 1,
    'tax': 1,

    # INT-MKTG (Marketing)
    'reels': 4,
    'instagram': 4,
    'social media': 4,
    'website': 4,
    'branding': 4,
    'portfolio': 4,
    'pr ': 4,
    'press': 4,

    # INT-LEGAL (Legal)
    'dispute': 3,
    'legal': 3,
    'claim': 3,
    'lawsuit': 3,

    # INT-BILL (Bill Personal)
    'shintamani': 5,
    'bali land': 5,
    'soi 27': 5,
}

# External category patterns
EXTERNAL_PATTERNS = {
    'meeting': ['meeting', 'call', 'zoom', 'teams', 'schedule a call', 'catch up'],
    'contract': ['contract', 'agreement', 'sign', 'execute', 'terms'],
    'design': ['drawing', 'render', 'design', 'concept', 'layout', 'plan', 'elevation'],
    'financial': ['invoice', 'payment', 'fee', 'budget', 'cost', 'price'],
    'rfi': ['rfi', 'request for information', 'clarification'],
}

# Project code patterns
PROJECT_CODE_PATTERNS = [
    r'\b(\d{2}\s*BK[-\s]?\d{3})\b',  # "25 BK-070", "25BK-070", "25 BK 070"
    r'\b(BK[-\s]?\d{3})\b',           # "BK-070", "BK 070"
]

# Junk patterns (skip these)
JUNK_PATTERNS = [
    'unsubscribe',
    'click here to unsubscribe',
    'binance',
    'cryptocurrency',
    'bitcoin',
    'noreply@',
    'no-reply@',
    'mailer-daemon',
]


class SmartCategorizer:
    def __init__(self, db_path: str = DB_PATH, dry_run: bool = False):
        self.db_path = db_path
        self.dry_run = dry_run
        self.stats = {
            'processed': 0,
            'categorized': 0,
            'linked_to_project': 0,
            'internal_tagged': 0,
            'contacts_mapped': 0,
            'skipped_junk': 0,
            'errors': 0,
        }

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ========================================================================
    # PASS 1: Direction Detection
    # ========================================================================

    def detect_direction(self, sender: str, recipients: str) -> str:
        """Determine if email is internal, outbound, or inbound"""
        sender_lower = (sender or '').lower()
        recipients_lower = (recipients or '').lower()

        sender_is_bensley = any(domain in sender_lower for domain in BENSLEY_DOMAINS)
        recipient_is_bensley = any(domain in recipients_lower for domain in BENSLEY_DOMAINS)

        if sender_is_bensley and recipient_is_bensley:
            # Check if ALL recipients are Bensley (truly internal)
            # vs some external recipients (outbound with CC)
            non_bensley = False
            for part in recipients_lower.split(','):
                part = part.strip()
                if part and not any(domain in part for domain in BENSLEY_DOMAINS):
                    non_bensley = True
                    break
            return 'internal' if not non_bensley else 'outbound'
        elif sender_is_bensley:
            return 'outbound'
        elif recipient_is_bensley:
            return 'inbound'
        else:
            return 'external'  # Neither party is Bensley (rare)

    # ========================================================================
    # PASS 2: Category Assignment
    # ========================================================================

    def is_junk(self, subject: str, sender: str, body: str) -> bool:
        """Check if email is junk/spam"""
        text = f"{subject} {sender} {body}".lower()
        return any(pattern in text for pattern in JUNK_PATTERNS)

    def categorize_internal(self, subject: str, body: str) -> Optional[int]:
        """Categorize internal email, returns category_id or None"""
        text = f"{subject} {body}".lower()

        for pattern, category_id in INTERNAL_PATTERNS.items():
            if pattern in text:
                return category_id

        return 2  # Default to INT-OPS for uncategorized internal

    def categorize_external(self, subject: str, body: str) -> str:
        """Categorize external email, returns category name"""
        text = f"{subject} {body}".lower()

        for category, keywords in EXTERNAL_PATTERNS.items():
            if any(kw in text for kw in keywords):
                return category

        return 'general'

    # ========================================================================
    # PASS 3: Project Extraction
    # ========================================================================

    def extract_project_codes(self, subject: str, body: str) -> List[str]:
        """Extract all project codes mentioned in email"""
        text = f"{subject} {body}"
        codes = set()

        for pattern in PROJECT_CODE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Normalize to "XX BK-XXX" format
                normalized = self.normalize_project_code(match)
                if normalized:
                    codes.add(normalized)

        return list(codes)

    def normalize_project_code(self, code: str) -> Optional[str]:
        """Normalize project code to standard format: 'XX BK-XXX'"""
        code = code.upper().strip()

        # Handle "25BK070" or "25 BK 070" or "25 BK-070"
        match = re.match(r'(\d{2})\s*BK[-\s]?(\d{3})', code)
        if match:
            return f"{match.group(1)} BK-{match.group(2)}"

        # Handle "BK-070" (no year prefix)
        match = re.match(r'BK[-\s]?(\d{3})', code)
        if match:
            return f"BK-{match.group(1)}"

        return None

    def get_project_id(self, conn, project_code: str) -> Optional[int]:
        """Look up project_id from project_code"""
        cursor = conn.cursor()

        # Try proposals first
        cursor.execute(
            "SELECT proposal_id FROM proposals WHERE project_code = ?",
            (project_code,)
        )
        row = cursor.fetchone()
        if row:
            return ('proposal', row[0])

        # Try projects
        cursor.execute(
            "SELECT project_id FROM projects WHERE project_code = ?",
            (project_code,)
        )
        row = cursor.fetchone()
        if row:
            return ('project', row[0])

        return None

    # ========================================================================
    # PASS 4: Contact Mapping
    # ========================================================================

    def extract_email_addresses(self, sender: str, recipients: str) -> List[str]:
        """Extract all email addresses from sender and recipients"""
        text = f"{sender} {recipients}"
        # Simple email regex
        pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        emails = re.findall(pattern, text.lower())
        # Filter out Bensley addresses for external contact mapping
        return [e for e in emails if not any(d in e for d in BENSLEY_DOMAINS)]

    # ========================================================================
    # MAIN PROCESSING
    # ========================================================================

    def process_email(self, conn, email: Dict) -> Dict:
        """Process a single email through all passes"""
        email_id = email['email_id']
        subject = email['subject'] or ''
        body = email['body_full'] or email['snippet'] or ''
        sender = email['sender_email'] or ''
        recipients = email['recipient_emails'] or ''

        result = {
            'email_id': email_id,
            'direction': None,
            'category': None,
            'internal_category_id': None,
            'project_codes': [],
            'external_contacts': [],
            'is_junk': False,
        }

        # Check for junk
        if self.is_junk(subject, sender, body):
            result['is_junk'] = True
            result['category'] = 'junk'
            return result

        # Pass 1: Direction
        result['direction'] = self.detect_direction(sender, recipients)

        # Pass 2: Category
        if result['direction'] == 'internal':
            result['internal_category_id'] = self.categorize_internal(subject, body)
            result['category'] = 'internal'
        else:
            result['category'] = self.categorize_external(subject, body)

        # Pass 3: Project extraction (even for internal emails!)
        result['project_codes'] = self.extract_project_codes(subject, body)

        # Pass 4: Contact extraction (for external emails)
        if result['direction'] != 'internal':
            result['external_contacts'] = self.extract_email_addresses(sender, recipients)

        return result

    def apply_result(self, conn, result: Dict):
        """Apply categorization result to database"""
        if self.dry_run:
            return

        cursor = conn.cursor()
        email_id = result['email_id']

        # Update email category
        cursor.execute(
            "UPDATE emails SET category = ? WHERE email_id = ?",
            (result['category'], email_id)
        )
        self.stats['categorized'] += 1

        # Add internal category link if internal
        if result['internal_category_id']:
            cursor.execute("""
                INSERT OR IGNORE INTO email_internal_links
                (email_id, category_id, confidence_score, match_method)
                VALUES (?, ?, 0.9, 'smart_categorizer')
            """, (email_id, result['internal_category_id']))
            self.stats['internal_tagged'] += 1

        # Create project links
        for code in result['project_codes']:
            project_info = self.get_project_id(conn, code)
            if project_info:
                table_type, proj_id = project_info
                if table_type == 'proposal':
                    cursor.execute("""
                        INSERT OR IGNORE INTO email_proposal_links
                        (email_id, proposal_id, confidence_score, link_source)
                        VALUES (?, ?, 0.85, 'smart_categorizer_code_match')
                    """, (email_id, proj_id))
                else:
                    cursor.execute("""
                        INSERT OR IGNORE INTO email_project_links
                        (email_id, project_id, confidence_score, link_source)
                        VALUES (?, ?, 0.85, 'smart_categorizer_code_match')
                    """, (email_id, proj_id))
                self.stats['linked_to_project'] += 1

        conn.commit()

    def run(self, email_ids: List[int] = None, process_all: bool = False, limit: int = 500):
        """Run categorization on emails"""
        conn = self.get_connection()
        cursor = conn.cursor()

        print("=" * 60)
        print("SMART EMAIL CATEGORIZER")
        print("=" * 60)

        if self.dry_run:
            print("DRY RUN - No changes will be made\n")

        # Build query
        if email_ids:
            placeholders = ','.join('?' * len(email_ids))
            cursor.execute(f"""
                SELECT email_id, subject, snippet, body_full, sender_email, recipient_emails
                FROM emails WHERE email_id IN ({placeholders})
            """, email_ids)
        elif process_all:
            cursor.execute("""
                SELECT email_id, subject, snippet, body_full, sender_email, recipient_emails
                FROM emails ORDER BY date DESC LIMIT ?
            """, (limit,))
        else:
            # Only uncategorized
            cursor.execute("""
                SELECT email_id, subject, snippet, body_full, sender_email, recipient_emails
                FROM emails WHERE category IS NULL
                ORDER BY date DESC LIMIT ?
            """, (limit,))

        emails = cursor.fetchall()
        total = len(emails)
        print(f"Processing {total} emails...\n")

        for i, email in enumerate(emails, 1):
            try:
                result = self.process_email(conn, dict(email))
                self.apply_result(conn, result)
                self.stats['processed'] += 1

                # Progress output
                if i % 50 == 0 or i == total:
                    print(f"Progress: {i}/{total} ({self.stats['categorized']} categorized, "
                          f"{self.stats['linked_to_project']} linked)")

            except Exception as e:
                print(f"Error processing email {email['email_id']}: {e}")
                self.stats['errors'] += 1

        conn.close()

        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        for key, value in self.stats.items():
            print(f"  {key}: {value}")

        return self.stats


def main():
    parser = argparse.ArgumentParser(description='Smart multi-pass email categorizer')
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    parser.add_argument('--all', action='store_true', help='Reprocess all emails (not just uncategorized)')
    parser.add_argument('--email-id', type=int, nargs='+', help='Process specific email IDs')
    parser.add_argument('--limit', type=int, default=500, help='Max emails to process')

    args = parser.parse_args()

    categorizer = SmartCategorizer(dry_run=args.dry_run)
    categorizer.run(
        email_ids=args.email_id,
        process_all=args.all,
        limit=args.limit
    )


if __name__ == '__main__':
    main()
