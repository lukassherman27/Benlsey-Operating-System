#!/usr/bin/env python3
"""
Proposal Data Backfill Script
Issue #365 - Fills missing proposal data where possible

Usage:
    python scripts/core/backfill_proposal_data.py --dry-run    # Preview changes (default)
    python scripts/core/backfill_proposal_data.py --execute    # Create suggestions
    python scripts/core/backfill_proposal_data.py --execute --link-emails  # Also link high-confidence emails

What this script does:
    1. Matches emails to proposals by project name/contact email
    2. Creates AI suggestions for email links (for human review)
    3. Does NOT auto-fill lost_reason (that's manual via UI #360)
    4. Does NOT auto-fill project_value (needs manual review of proposals/contracts)

Why suggestions instead of auto-linking:
    - CLAUDE.md rule: "Never auto-link emails - Create suggestions for human review"
    - Prevents incorrect links that could confuse proposal history
"""

import argparse
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "database" / "bensley_master.db"


@dataclass
class EmailMatch:
    email_id: int
    proposal_id: int
    project_code: str
    match_method: str
    match_reason: str
    confidence: float
    subject: str


def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def normalize_name(name: str) -> str:
    """Normalize project name for matching."""
    if not name:
        return ""
    # Remove common suffixes and clean up
    name = re.sub(r'\s*\([^)]*\)\s*', ' ', name)  # Remove parentheticals
    name = re.sub(r'\s+', ' ', name)  # Normalize whitespace
    name = name.strip().lower()
    return name


def find_email_matches_by_name(cursor) -> list[EmailMatch]:
    """Find emails that match unlinked proposals by project name in subject."""
    matches = []

    # Get proposals without linked emails
    cursor.execute("""
        SELECT proposal_id, project_code, project_name
        FROM proposals
        WHERE proposal_id NOT IN (SELECT DISTINCT proposal_id FROM email_proposal_links)
    """)
    unlinked_proposals = cursor.fetchall()

    for proposal in unlinked_proposals:
        project_name = proposal['project_name']
        if not project_name or len(project_name) < 10:
            continue

        # Try exact match on project name
        cursor.execute("""
            SELECT email_id, subject
            FROM emails
            WHERE subject LIKE ?
              AND email_id NOT IN (SELECT email_id FROM email_proposal_links WHERE proposal_id = ?)
            LIMIT 50
        """, (f"%{project_name}%", proposal['proposal_id']))

        for email in cursor.fetchall():
            matches.append(EmailMatch(
                email_id=email['email_id'],
                proposal_id=proposal['proposal_id'],
                project_code=proposal['project_code'],
                match_method='project_name_exact',
                match_reason=f"Subject contains '{project_name[:40]}...'",
                confidence=0.9,
                subject=email['subject'][:80] if email['subject'] else ''
            ))

        # Try partial match on key words (first 3 significant words)
        words = [w for w in normalize_name(project_name).split() if len(w) > 3][:3]
        if len(words) >= 2:
            pattern = '%' + '%'.join(words) + '%'
            cursor.execute("""
                SELECT email_id, subject
                FROM emails
                WHERE LOWER(subject) LIKE ?
                  AND email_id NOT IN (SELECT email_id FROM email_proposal_links WHERE proposal_id = ?)
                  AND email_id NOT IN (SELECT email_id FROM email_proposal_links)
                LIMIT 20
            """, (pattern, proposal['proposal_id']))

            for email in cursor.fetchall():
                # Skip if already matched with higher confidence
                if any(m.email_id == email['email_id'] for m in matches):
                    continue
                matches.append(EmailMatch(
                    email_id=email['email_id'],
                    proposal_id=proposal['proposal_id'],
                    project_code=proposal['project_code'],
                    match_method='project_name_partial',
                    match_reason=f"Subject matches keywords: {', '.join(words)}",
                    confidence=0.7,
                    subject=email['subject'][:80] if email['subject'] else ''
                ))

    return matches


def find_email_matches_by_contact(cursor) -> list[EmailMatch]:
    """Find emails that match unlinked proposals by contact email."""
    matches = []

    cursor.execute("""
        SELECT
            p.proposal_id,
            p.project_code,
            p.project_name,
            p.contact_email,
            e.email_id,
            e.subject
        FROM proposals p
        CROSS JOIN emails e
        WHERE p.proposal_id NOT IN (SELECT DISTINCT proposal_id FROM email_proposal_links)
          AND p.contact_email IS NOT NULL
          AND p.contact_email != ''
          AND (e.sender_email = p.contact_email OR e.recipient_emails LIKE '%' || p.contact_email || '%')
          AND e.email_id NOT IN (SELECT email_id FROM email_proposal_links)
        LIMIT 200
    """)

    for row in cursor.fetchall():
        matches.append(EmailMatch(
            email_id=row['email_id'],
            proposal_id=row['proposal_id'],
            project_code=row['project_code'],
            match_method='contact_email',
            match_reason=f"Contact email: {row['contact_email']}",
            confidence=0.6,  # Lower confidence - contact might have multiple projects
            subject=row['subject'][:80] if row['subject'] else ''
        ))

    return matches


def create_suggestions(cursor, matches: list[EmailMatch], execute: bool) -> int:
    """Create AI suggestions for email-proposal links."""
    if not execute:
        return len(matches)

    created = 0
    for match in matches:
        # Check if suggestion already exists
        cursor.execute("""
            SELECT suggestion_id FROM ai_suggestions
            WHERE entity_type = 'email_proposal_link'
              AND entity_id = ?
              AND suggested_field = 'proposal_id'
              AND suggested_value = ?
              AND status = 'pending'
        """, (str(match.email_id), str(match.proposal_id)))

        if cursor.fetchone():
            continue  # Skip duplicate

        cursor.execute("""
            INSERT INTO ai_suggestions (
                entity_type, entity_id, suggested_field, suggested_value,
                confidence_score, reasoning, suggestion_type, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'email_proposal_link',
            str(match.email_id),
            'proposal_id',
            str(match.proposal_id),
            match.confidence,
            f"[{match.match_method}] {match.match_reason}. Subject: {match.subject}",
            'link_review',
            'pending',
            datetime.now().isoformat()
        ))
        created += 1

    return created


def create_direct_links(cursor, matches: list[EmailMatch], min_confidence: float = 0.85) -> int:
    """Create direct email-proposal links for high-confidence matches."""
    linked = 0

    for match in matches:
        if match.confidence < min_confidence:
            continue

        # Check if link already exists
        cursor.execute("""
            SELECT link_id FROM email_proposal_links
            WHERE email_id = ? AND proposal_id = ?
        """, (match.email_id, match.proposal_id))

        if cursor.fetchone():
            continue

        cursor.execute("""
            INSERT INTO email_proposal_links (
                email_id, proposal_id, confidence_score, match_method, match_reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            match.email_id,
            match.proposal_id,
            match.confidence,
            f"backfill_{match.match_method}",
            match.match_reason,
            datetime.now().isoformat()
        ))
        linked += 1

    return linked


def main():
    parser = argparse.ArgumentParser(description="Backfill missing proposal data")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", default=True,
                       help="Preview changes without modifying database (default)")
    group.add_argument("--execute", action="store_true",
                       help="Actually create suggestions/links")
    parser.add_argument("--link-emails", action="store_true",
                       help="Directly link high-confidence emails (>=0.85)")
    args = parser.parse_args()

    execute = args.execute
    mode = "EXECUTE" if execute else "DRY RUN"

    print(f"\n{'='*60}")
    print(f"Proposal Data Backfill - {mode}")
    print(f"Database: {DB_PATH}")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"{'='*60}\n")

    conn = get_connection()
    cursor = conn.cursor()

    # Get current state
    cursor.execute("SELECT COUNT(*) FROM proposals WHERE project_value IS NULL OR project_value = 0")
    missing_value_before = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM proposals
        WHERE proposal_id NOT IN (SELECT DISTINCT proposal_id FROM email_proposal_links)
    """)
    unlinked_before = cursor.fetchone()[0]

    print(f"Before backfill:")
    print(f"  - Proposals missing project_value: {missing_value_before}")
    print(f"  - Proposals without linked emails: {unlinked_before}")
    print()

    # Find email matches
    print("Finding email matches...")
    name_matches = find_email_matches_by_name(cursor)
    contact_matches = find_email_matches_by_contact(cursor)

    # Deduplicate (prefer higher confidence)
    all_matches_dict = {}
    for match in contact_matches + name_matches:
        key = (match.email_id, match.proposal_id)
        if key not in all_matches_dict or match.confidence > all_matches_dict[key].confidence:
            all_matches_dict[key] = match
    all_matches = list(all_matches_dict.values())

    print(f"  - By project name: {len(name_matches)} matches")
    print(f"  - By contact email: {len(contact_matches)} matches")
    print(f"  - Total unique: {len(all_matches)} matches")
    print()

    # Categorize by confidence
    high_conf = [m for m in all_matches if m.confidence >= 0.85]
    medium_conf = [m for m in all_matches if 0.6 <= m.confidence < 0.85]
    low_conf = [m for m in all_matches if m.confidence < 0.6]

    print("By confidence level:")
    print(f"  - High (>=0.85): {len(high_conf)} - can auto-link")
    print(f"  - Medium (0.6-0.85): {len(medium_conf)} - needs review")
    print(f"  - Low (<0.6): {len(low_conf)} - needs review")
    print()

    # Show sample matches
    if all_matches:
        print("Sample matches (top 10 by confidence):")
        print("-" * 100)
        sorted_matches = sorted(all_matches, key=lambda m: m.confidence, reverse=True)[:10]
        for m in sorted_matches:
            print(f"  [{m.confidence:.2f}] {m.project_code}: {m.match_method}")
            print(f"         Subject: {m.subject[:60]}...")
        print()

    # Execute actions
    if execute:
        # Create suggestions for review
        suggestions_created = create_suggestions(cursor, all_matches, execute)
        print(f"Created {suggestions_created} AI suggestions for review")

        # Optionally create direct links for high-confidence matches
        if args.link_emails:
            links_created = create_direct_links(cursor, all_matches)
            print(f"Created {links_created} direct email-proposal links (confidence >= 0.85)")

        conn.commit()
    else:
        print(f"Would create {len(all_matches)} AI suggestions for review")
        if args.link_emails:
            print(f"Would create {len(high_conf)} direct links (confidence >= 0.85)")

    # Summary about project_value
    print()
    print("=" * 60)
    print("NOTES ON PROJECT_VALUE")
    print("-" * 60)
    print(f"  {missing_value_before} proposals are missing project_value.")
    print("  This cannot be auto-filled - values must come from:")
    print("    1. Proposal documents/PDFs")
    print("    2. Contract documents")
    print("    3. Manual entry based on negotiations")
    print()
    print("  To fix: Review each proposal in the UI and enter values manually.")
    print()

    # Summary about lost_reason
    cursor.execute("""
        SELECT COUNT(*) FROM proposals
        WHERE status = 'Lost' AND (lost_reason IS NULL OR lost_reason = '')
    """)
    missing_lost_reason = cursor.fetchone()[0]

    if missing_lost_reason > 0:
        print("=" * 60)
        print("NOTES ON LOST_REASON")
        print("-" * 60)
        print(f"  {missing_lost_reason} lost proposals are missing lost_reason.")
        print("  This should be filled via the UI (#360) with one of:")
        print("    - Lost to competitor")
        print("    - Budget constraints")
        print("    - Project cancelled")
        print("    - Scope mismatch")
        print("    - No response / went cold")
        print()

    if not execute:
        print("To execute, run:")
        print("  python scripts/core/backfill_proposal_data.py --execute")
        print("  python scripts/core/backfill_proposal_data.py --execute --link-emails")

    conn.close()
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
