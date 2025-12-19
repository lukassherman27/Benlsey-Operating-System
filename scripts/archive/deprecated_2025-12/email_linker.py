"""
Email Linker - Links unlinked emails to projects/proposals

DEPRECATED: This script is deprecated as of 2025-12-02.
Use the suggestion-based workflow via API: POST /api/admin/process-unlinked-emails
All links now require human approval through the suggestion review system.

Strategies:
1. Thread Linking: If any email in a thread is linked, link all emails in that thread
2. Subject Code Extraction: Extract BK project codes from subject lines
3. Sender Matching: Match sender email to contacts who have linked emails

Created: 2025-11-27
"""

import warnings
warnings.warn(
    "This script is DEPRECATED. Use API: POST /api/admin/process-unlinked-emails. "
    "All email links now require human approval through the suggestion review system.",
    DeprecationWarning,
    stacklevel=2
)

import sqlite3
import re
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Default database path
DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')


class EmailLinker:
    """Links unlinked emails to proposals using multiple strategies"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.stats = {
            'thread_linked': 0,
            'subject_linked': 0,
            'sender_linked': 0,
            'already_linked': 0,
            'no_match': 0,
            'errors': 0
        }

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def get_unlinked_emails(self) -> List[Dict]:
        """Get all emails not linked to any project or proposal"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    e.email_id,
                    e.subject,
                    e.sender_email,
                    e.thread_id,
                    e.date
                FROM emails e
                WHERE e.email_id NOT IN (SELECT email_id FROM email_project_links)
                  AND e.email_id NOT IN (SELECT email_id FROM email_proposal_links)
                ORDER BY e.date DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_project_codes(self) -> Dict[str, int]:
        """Get mapping of project_code -> proposal_id"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT proposal_id, project_code FROM proposals WHERE project_code IS NOT NULL")
            return {row[1]: row[0] for row in cursor.fetchall()}

    def clean_email(self, email_str: str) -> str:
        """Extract clean email from formats like 'Name <email@domain.com>'"""
        if not email_str:
            return ''
        match = re.search(r'<([^>]+)>', email_str)
        if match:
            return match.group(1).lower().strip()
        return email_str.lower().strip()

    # =========================================================================
    # STRATEGY 1: Thread Linking
    # =========================================================================

    def get_thread_proposal_map(self) -> Dict[str, int]:
        """Get mapping of thread_id -> proposal_id for linked threads"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT e.thread_id, epl.proposal_id
                FROM emails e
                JOIN email_proposal_links epl ON e.email_id = epl.email_id
                WHERE e.thread_id IS NOT NULL AND e.thread_id != ''
            """)
            # Return first proposal for each thread
            thread_map = {}
            for thread_id, proposal_id in cursor.fetchall():
                if thread_id not in thread_map:
                    thread_map[thread_id] = proposal_id
            return thread_map

    def link_by_thread(self, email: Dict, thread_map: Dict[str, int]) -> Optional[int]:
        """Try to link email by thread_id"""
        thread_id = email.get('thread_id')
        if thread_id and thread_id in thread_map:
            return thread_map[thread_id]
        return None

    # =========================================================================
    # STRATEGY 2: Subject Code Extraction
    # =========================================================================

    def extract_project_code(self, subject: str) -> Optional[str]:
        """Extract BK project code from subject line"""
        if not subject:
            return None

        # Patterns for BK codes:
        # "25 BK-087", "24 BK-089", "BK-123", "BK123", "#BK-001"
        patterns = [
            r'(\d{2}\s*BK[-\s]?\d{3})',  # Year prefix: 25 BK-087
            r'#?BK[-\s]?(\d{3,4})',       # No year: BK-087 or #BK-087
        ]

        for pattern in patterns:
            match = re.search(pattern, subject, re.IGNORECASE)
            if match:
                code = match.group(1) if match.group(1) else match.group(0)
                # Normalize: "25BK087" -> "25 BK-087"
                code = code.upper().replace(' ', '').replace('-', '')
                if len(code) >= 5:  # At least BK + 3 digits
                    # Format as "XX BK-YYY"
                    if code[:2].isdigit():
                        return f"{code[:2]} BK-{code[-3:]}"
                    else:
                        # Just BK code without year - try to match
                        return code
        return None

    def link_by_subject(self, email: Dict, project_codes: Dict[str, int]) -> Optional[int]:
        """Try to link email by extracting project code from subject"""
        code = self.extract_project_code(email.get('subject', ''))
        if code and code in project_codes:
            return project_codes[code]
        return None

    # =========================================================================
    # STRATEGY 3: Sender Matching
    # =========================================================================

    def get_sender_proposal_map(self) -> Dict[str, int]:
        """
        Build mapping of sender_email -> proposal_id based on:
        - Emails already linked from the same sender
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get senders who have linked emails
            cursor.execute("""
                SELECT
                    e.sender_email,
                    epl.proposal_id,
                    COUNT(*) as link_count
                FROM emails e
                JOIN email_proposal_links epl ON e.email_id = epl.email_id
                WHERE e.sender_email IS NOT NULL
                GROUP BY e.sender_email, epl.proposal_id
                ORDER BY link_count DESC
            """)

            sender_map = {}
            for sender_email, proposal_id, count in cursor.fetchall():
                clean_sender = self.clean_email(sender_email)
                if clean_sender and clean_sender not in sender_map:
                    # Use the proposal with most links for this sender
                    sender_map[clean_sender] = proposal_id

            return sender_map

    def link_by_sender(self, email: Dict, sender_map: Dict[str, int]) -> Optional[int]:
        """Try to link email by sender email address"""
        sender = self.clean_email(email.get('sender_email', ''))
        if sender and sender in sender_map:
            return sender_map[sender]
        return None

    # =========================================================================
    # MAIN LINKING LOGIC
    # =========================================================================

    def create_link(self, email_id: int, proposal_id: int, method: str, confidence: float = 0.8) -> bool:
        """Create email-proposal link"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Check if link already exists
                cursor.execute("""
                    SELECT 1 FROM email_proposal_links
                    WHERE email_id = ? AND proposal_id = ?
                """, (email_id, proposal_id))

                if cursor.fetchone():
                    return False  # Already linked

                cursor.execute("""
                    INSERT INTO email_proposal_links (
                        email_id, proposal_id, confidence_score,
                        match_reasons, auto_linked, created_at
                    ) VALUES (?, ?, ?, ?, 1, ?)
                """, (
                    email_id,
                    proposal_id,
                    confidence,
                    f"Auto-linked via {method}",
                    datetime.now().isoformat()
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error creating link: {e}")
            return False

    def run(self, dry_run: bool = False, limit: int = None) -> Dict:
        """
        Run all linking strategies on unlinked emails

        Args:
            dry_run: If True, don't actually create links, just report what would happen
            limit: Max emails to process (None for all)

        Returns:
            Statistics dict
        """
        print(f"{'[DRY RUN] ' if dry_run else ''}Starting email linking...")

        # Load mappings
        print("Loading thread map...")
        thread_map = self.get_thread_proposal_map()
        print(f"  Found {len(thread_map)} linked threads")

        print("Loading project codes...")
        project_codes = self.get_project_codes()
        print(f"  Found {len(project_codes)} project codes")

        print("Loading sender map...")
        sender_map = self.get_sender_proposal_map()
        print(f"  Found {len(sender_map)} mapped senders")

        # Get unlinked emails
        print("Loading unlinked emails...")
        unlinked = self.get_unlinked_emails()
        print(f"  Found {len(unlinked)} unlinked emails")

        if limit:
            unlinked = unlinked[:limit]
            print(f"  Processing first {limit} emails")

        # Process each email
        for i, email in enumerate(unlinked):
            if (i + 1) % 100 == 0:
                print(f"  Processed {i+1}/{len(unlinked)}...")

            proposal_id = None
            method = None
            confidence = 0.8

            # Strategy 1: Thread linking (highest confidence)
            proposal_id = self.link_by_thread(email, thread_map)
            if proposal_id:
                method = 'thread_linking'
                confidence = 0.95

            # Strategy 2: Subject code extraction
            if not proposal_id:
                proposal_id = self.link_by_subject(email, project_codes)
                if proposal_id:
                    method = 'subject_code'
                    confidence = 0.9

            # Strategy 3: Sender matching (lowest confidence)
            if not proposal_id:
                proposal_id = self.link_by_sender(email, sender_map)
                if proposal_id:
                    method = 'sender_matching'
                    confidence = 0.7

            # Create link if match found
            if proposal_id and method:
                if dry_run:
                    self.stats[f'{method.split("_")[0]}_linked'] += 1
                else:
                    if self.create_link(email['email_id'], proposal_id, method, confidence):
                        self.stats[f'{method.split("_")[0]}_linked'] += 1
                    else:
                        self.stats['already_linked'] += 1
            else:
                self.stats['no_match'] += 1

        # Print summary
        print("\n" + "="*50)
        print("LINKING SUMMARY")
        print("="*50)
        print(f"Thread linked:  {self.stats['thread_linked']}")
        print(f"Subject linked: {self.stats['subject_linked']}")
        print(f"Sender linked:  {self.stats['sender_linked']}")
        print(f"Already linked: {self.stats['already_linked']}")
        print(f"No match:       {self.stats['no_match']}")
        total_linked = self.stats['thread_linked'] + self.stats['subject_linked'] + self.stats['sender_linked']
        print(f"\nTotal newly linked: {total_linked}")

        return self.stats


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Link unlinked emails to proposals')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be linked without making changes')
    parser.add_argument('--limit', type=int, help='Max emails to process')
    parser.add_argument('--db', default=DB_PATH, help='Database path')
    args = parser.parse_args()

    linker = EmailLinker(args.db)
    stats = linker.run(dry_run=args.dry_run, limit=args.limit)

    return stats


if __name__ == '__main__':
    main()
