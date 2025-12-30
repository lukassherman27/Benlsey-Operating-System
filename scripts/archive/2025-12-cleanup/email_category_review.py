#!/usr/bin/env python3
"""
Email Category Review Script

Outputs emails for Claude-in-the-loop review. Instead of keyboard shortcuts,
this script outputs full context that you review with Claude, provide corrections
in natural language, and the system learns from your feedback.

Usage:
    # Get a batch of emails for review
    python scripts/core/email_category_review.py --batch 20

    # Review specific emails
    python scripts/core/email_category_review.py --email-ids 123,456,789

    # Apply corrections from a JSON file
    python scripts/core/email_category_review.py --apply corrections.json

    # Show statistics
    python scripts/core/email_category_review.py --stats

Part of Phase 2.0: Multi-Tag Categorization System
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# Set database path
os.environ.setdefault('DATABASE_PATH', 'database/bensley_master.db')

from backend.services.email_tagger_service import EmailTaggerService


# Category reference for the review output
CATEGORY_REFERENCE = """
## BILL'S UNIVERSE - CATEGORY REFERENCE

| Code | Name | Description |
|------|------|-------------|
| **BDS** | Design Business | Bensley design projects - link to XX BK-XXX codes |
| **INT** | Internal Operations | Bensley internal (not project-specific) |
| INT-FIN | Finance | Taxes, accounting, invoices, payments |
| INT-OPS | IT/Systems | Email, software, BOS, NaviWorld, D365 |
| INT-HR | Human Resources | Hiring, policies, team |
| INT-LEGAL | Legal | Contracts for Bensley, IP, compliance |
| INT-SCHED | Scheduling | PM scheduling, site visits |
| INT-DAILY | Daily Work | Team updates, progress reports |
| **SM** | Shinta Mani Hotels | Bill's hotels (NOT design projects) |
| SM-WILD | Shinta Mani Wild | Wild hotel operations, P&L |
| SM-MUSTANG | Shinta Mani Mustang | Mustang operations |
| SM-ANGKOR | Shinta Mani Angkor | Angkor operations |
| SM-FOUNDATION | SM Foundation | Charity, monthly reports |
| **PERS** | Personal | Bill's personal matters |
| PERS-ART | Gallery/Art | Bill's art, exhibitions |
| PERS-INVEST | Investments | Land, property deals |
| PERS-FAMILY | Family | Personal family |
| PERS-PRESS | Press/Speaking | Interviews, lectures |
| **MKT** | Marketing/Brand | Marketing activities |
| MKT-SOCIAL | Social Media | Instagram, content |
| MKT-PRESS | Press Coverage | Articles, awards |
| MKT-WEB | Website | Web analytics, updates |
| **SKIP** | Skip/Ignore | Don't process |
| SKIP-SPAM | Spam | Marketing spam, newsletters |
| SKIP-AUTO | Automated | System notifications |
| SKIP-DUP | Duplicate | Already processed |
"""


def format_email_for_review(item: dict, index: int) -> str:
    """Format a single email for Claude review"""
    lines = []
    lines.append(f"\n{'='*80}")
    lines.append(f"## EMAIL #{index + 1} (ID: {item['email_id']})")
    lines.append(f"{'='*80}")

    # Basic info
    lines.append(f"**Date:** {item.get('date', 'Unknown')}")
    lines.append(f"**From:** {item.get('sender_name', '')} <{item.get('sender', 'Unknown')}>")
    lines.append(f"**To:** {item.get('recipients', 'Unknown')[:100]}")
    lines.append(f"**Subject:** {item.get('subject', 'No subject')}")
    lines.append(f"**Folder:** {item.get('folder', 'INBOX')}")

    # Thread context
    if item.get('thread_email_count', 1) > 1:
        lines.append(f"\n**Thread:** {item['thread_email_count']} emails in thread")
        if item.get('thread_has_project_link'):
            links = item.get('thread_project', [])
            if links:
                link_str = ', '.join([f"{l['project_code']} ({l['project_name']})" for l in links])
                lines.append(f"**Thread Project:** {link_str} ← Thread already linked to this project!")

    # Existing links
    if item.get('existing_project_links'):
        links = item['existing_project_links']
        link_str = ', '.join([f"{l['project_code']} ({l['project_name']})" for l in links])
        lines.append(f"**Existing Links:** {link_str}")

    # Pattern match
    if item.get('pattern_match'):
        pm = item['pattern_match']
        lines.append(f"\n**Pattern Match:** {pm.get('primary_category')} / {pm.get('subcategory')}")
        lines.append(f"  - Matched: {pm.get('pattern_type')} = '{pm.get('matched_pattern')}'")
        lines.append(f"  - Confidence: {pm.get('confidence', 0):.0%}")

    # Current classification (if any)
    if item.get('current_category'):
        lines.append(f"\n**Current Category:** {item['current_category']}")
    if item.get('current_type'):
        lines.append(f"**Current Type:** {item['current_type']}")

    # Body preview
    body = item.get('body_preview', '')[:600]
    if body:
        lines.append(f"\n**Body Preview:**")
        lines.append(f"```")
        lines.append(body)
        lines.append(f"```")

    # Suggestion placeholder
    lines.append(f"\n**Suggested Category:** [To be determined]")
    lines.append(f"**Suggested Subcategory:** [To be determined]")
    lines.append(f"**Project Link:** [None / XX BK-XXX]")
    lines.append(f"**Action Type:** [None / invoice / scheduling / etc.]")

    return '\n'.join(lines)


def get_review_batch(batch_size: int = 20, email_ids: list = None) -> str:
    """Get a batch of emails formatted for Claude review"""
    tagger = EmailTaggerService()

    if email_ids:
        # Get specific emails
        emails = tagger._get_emails_by_ids(email_ids)
        review_items = []
        category_patterns = tagger._load_category_patterns()

        for email in emails:
            pattern_result = tagger._match_patterns(email, category_patterns)
            thread_context = tagger._get_thread_context(email)
            project_links = tagger._get_existing_links(email['email_id'])

            item = {
                'email_id': email['email_id'],
                'date': email.get('date', ''),
                'sender': email.get('sender_email', ''),
                'sender_name': email.get('sender_name', ''),
                'recipients': email.get('recipient_emails', ''),
                'subject': email.get('subject', ''),
                'body_preview': (email.get('body_full') or email.get('body_preview') or '')[:600],
                'folder': email.get('folder', 'INBOX'),
                'pattern_match': pattern_result,
                'thread_email_count': thread_context.get('email_count', 1),
                'thread_has_project_link': bool(thread_context.get('existing_project_links')),
                'thread_project': thread_context.get('existing_project_links', []),
                'existing_project_links': project_links,
                'current_category': email.get('primary_category'),
                'current_type': email.get('email_type'),
            }
            review_items.append(item)
    else:
        review_items = tagger.get_review_batch(batch_size)

    if not review_items:
        return "No uncategorized emails found!"

    # Build output
    output = []
    output.append(f"# EMAIL CATEGORIZATION REVIEW")
    output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    output.append(f"Emails to review: {len(review_items)}")

    output.append(CATEGORY_REFERENCE)

    output.append("\n# EMAILS FOR REVIEW\n")
    output.append("Review each email and provide corrections. For each email, specify:")
    output.append("- primary_category: BDS, INT, SM, PERS, MKT, or SKIP")
    output.append("- subcategory: e.g., INT-FIN, SM-WILD (or null)")
    output.append("- project_code: e.g., 25 BK-033 (only for BDS, or null)")
    output.append("- action_type: invoice, scheduling, status_update, report, inquiry (or null)")

    for i, item in enumerate(review_items):
        output.append(format_email_for_review(item, i))

    output.append("\n" + "="*80)
    output.append("# CORRECTIONS")
    output.append("="*80)
    output.append("""
After reviewing, provide corrections in this JSON format:

```json
[
  {
    "email_id": 123,
    "primary_category": "INT",
    "subcategory": "INT-FIN",
    "project_code": null,
    "action_type": "invoice",
    "notes": "Tax-related email from accountant"
  },
  {
    "email_id": 456,
    "primary_category": "BDS",
    "subcategory": null,
    "project_code": "25 BK-033",
    "action_type": "scheduling",
    "notes": "Site visit scheduling for Ritz Carlton"
  },
  {
    "email_id": 789,
    "primary_category": "SKIP",
    "subcategory": "SKIP-SPAM",
    "project_code": null,
    "action_type": null,
    "notes": "Unanet marketing"
  }
]
```

Then run: python scripts/core/email_category_review.py --apply corrections.json
""")

    return '\n'.join(output)


def apply_corrections(corrections_file: str) -> str:
    """Apply corrections from a JSON file"""
    # Handle inline JSON (starting with [)
    if corrections_file.strip().startswith('['):
        corrections = json.loads(corrections_file)
    else:
        with open(corrections_file, 'r') as f:
            corrections = json.load(f)

    tagger = EmailTaggerService()
    results = tagger.apply_batch_tags(corrections)

    output = []
    output.append(f"# CORRECTION RESULTS")
    output.append(f"Total: {results['total']}")
    output.append(f"Success: {results['success']}")
    output.append(f"Failed: {results['failed']}")

    if results['errors']:
        output.append("\n## Errors:")
        for err in results['errors']:
            output.append(f"  - Email {err.get('email_id')}: {err.get('error')}")

    # Show updated stats
    stats = tagger.get_category_stats()
    output.append(f"\n## Updated Statistics:")
    output.append(f"  - Total emails: {stats['total_emails']}")
    output.append(f"  - Categorized: {stats['categorized_emails']}")
    output.append(f"  - Active patterns: {stats['active_patterns']}")

    if stats.get('by_category'):
        output.append(f"\n## By Category:")
        for cat, count in stats['by_category'].items():
            output.append(f"  - {cat}: {count}")

    return '\n'.join(output)


def get_stats() -> str:
    """Get categorization statistics"""
    tagger = EmailTaggerService()
    stats = tagger.get_category_stats()

    output = []
    output.append("# CATEGORIZATION STATISTICS")
    output.append(f"\nTotal emails: {stats['total_emails']}")
    output.append(f"Categorized: {stats['categorized_emails']}")
    pct = (stats['categorized_emails'] / stats['total_emails'] * 100) if stats['total_emails'] > 0 else 0
    output.append(f"Progress: {pct:.1f}%")
    output.append(f"Active patterns: {stats['active_patterns']}")

    if stats.get('by_category'):
        output.append(f"\n## By Category:")
        for cat, count in sorted(stats['by_category'].items(), key=lambda x: -x[1]):
            output.append(f"  - {cat}: {count}")

    return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(
        description='Email Category Review - Claude-in-the-loop categorization'
    )
    parser.add_argument(
        '--batch', type=int, default=20,
        help='Number of emails to review (default: 20)'
    )
    parser.add_argument(
        '--email-ids', type=str,
        help='Specific email IDs to review (comma-separated)'
    )
    parser.add_argument(
        '--apply', type=str,
        help='Apply corrections from JSON file or inline JSON'
    )
    parser.add_argument(
        '--stats', action='store_true',
        help='Show categorization statistics'
    )
    parser.add_argument(
        '--output', type=str,
        help='Output file (default: stdout)'
    )

    args = parser.parse_args()

    if args.stats:
        result = get_stats()
    elif args.apply:
        result = apply_corrections(args.apply)
    else:
        email_ids = None
        if args.email_ids:
            email_ids = [int(x.strip()) for x in args.email_ids.split(',')]
        result = get_review_batch(args.batch, email_ids)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(result)
        print(f"Output written to {args.output}")
    else:
        print(result)


if __name__ == '__main__':
    main()
