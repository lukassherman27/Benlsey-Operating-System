#!/usr/bin/env python3
"""
Proposal Data Quality Analysis Script
Issue #365 - Identifies missing proposal data

Usage:
    python scripts/core/analyze_proposal_data.py
    python scripts/core/analyze_proposal_data.py --json    # Output as JSON
    python scripts/core/analyze_proposal_data.py --csv     # Output as CSV

Reports:
    1. Proposals missing project_value
    2. Proposals with 0 linked emails
    3. Lost proposals missing lost_reason
"""

import argparse
import csv
import json
import sqlite3
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "database" / "bensley_master.db"


@dataclass
class ProposalIssue:
    proposal_id: int
    project_code: str
    project_name: str
    status: str
    issue_type: str
    current_value: Optional[str] = None
    potential_matches: Optional[int] = None


def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def analyze_missing_project_value(cursor) -> list[ProposalIssue]:
    """Find proposals with missing or zero project_value."""
    cursor.execute("""
        SELECT
            proposal_id,
            project_code,
            project_name,
            status,
            project_value
        FROM proposals
        WHERE project_value IS NULL OR project_value = 0
        ORDER BY
            CASE
                WHEN status = 'Contract Signed' THEN 1
                WHEN status = 'Proposal Sent' THEN 2
                WHEN status = 'Negotiation' THEN 3
                WHEN status = 'On Hold' THEN 4
                ELSE 5
            END,
            project_code
    """)

    issues = []
    for row in cursor.fetchall():
        issues.append(ProposalIssue(
            proposal_id=row['proposal_id'],
            project_code=row['project_code'],
            project_name=row['project_name'],
            status=row['status'],
            issue_type='missing_project_value',
            current_value='NULL' if row['project_value'] is None else '0'
        ))
    return issues


def analyze_missing_emails(cursor) -> list[ProposalIssue]:
    """Find proposals with no linked emails."""
    cursor.execute("""
        SELECT
            p.proposal_id,
            p.project_code,
            p.project_name,
            p.status,
            p.contact_email,
            (SELECT COUNT(*) FROM emails e
             WHERE e.subject LIKE '%' || p.project_code || '%') as code_matches,
            (SELECT COUNT(*) FROM emails e
             WHERE e.sender_email = p.contact_email OR e.recipient_emails LIKE '%' || p.contact_email || '%') as contact_matches
        FROM proposals p
        WHERE p.proposal_id NOT IN (SELECT DISTINCT proposal_id FROM email_proposal_links)
        ORDER BY
            CASE
                WHEN p.status = 'Contract Signed' THEN 1
                WHEN p.status = 'Proposal Sent' THEN 2
                WHEN p.status = 'Negotiation' THEN 3
                ELSE 4
            END,
            p.project_code
    """)

    issues = []
    for row in cursor.fetchall():
        potential = (row['code_matches'] or 0) + (row['contact_matches'] or 0)
        issues.append(ProposalIssue(
            proposal_id=row['proposal_id'],
            project_code=row['project_code'],
            project_name=row['project_name'],
            status=row['status'],
            issue_type='no_linked_emails',
            current_value=f"contact: {row['contact_email'] or 'N/A'}",
            potential_matches=potential
        ))
    return issues


def analyze_missing_lost_reason(cursor) -> list[ProposalIssue]:
    """Find lost proposals without a lost_reason."""
    cursor.execute("""
        SELECT
            proposal_id,
            project_code,
            project_name,
            status,
            lost_date,
            lost_to_competitor
        FROM proposals
        WHERE status = 'Lost' AND (lost_reason IS NULL OR lost_reason = '')
        ORDER BY lost_date DESC, project_code
    """)

    issues = []
    for row in cursor.fetchall():
        issues.append(ProposalIssue(
            proposal_id=row['proposal_id'],
            project_code=row['project_code'],
            project_name=row['project_name'],
            status=row['status'],
            issue_type='missing_lost_reason',
            current_value=f"lost_date: {row['lost_date'] or 'N/A'}, competitor: {row['lost_to_competitor'] or 'N/A'}"
        ))
    return issues


def get_summary_stats(cursor) -> dict:
    """Get overall proposal statistics."""
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN project_value IS NULL OR project_value = 0 THEN 1 ELSE 0 END) as missing_value,
            SUM(CASE WHEN status = 'Lost' AND (lost_reason IS NULL OR lost_reason = '') THEN 1 ELSE 0 END) as missing_lost_reason
        FROM proposals
    """)
    row = cursor.fetchone()

    cursor.execute("""
        SELECT COUNT(DISTINCT p.proposal_id) as with_emails
        FROM proposals p
        INNER JOIN email_proposal_links epl ON p.proposal_id = epl.proposal_id
    """)
    with_emails = cursor.fetchone()['with_emails']

    return {
        'total_proposals': row['total'],
        'missing_project_value': row['missing_value'],
        'missing_project_value_pct': round(row['missing_value'] / row['total'] * 100, 1),
        'with_linked_emails': with_emails,
        'without_linked_emails': row['total'] - with_emails,
        'without_linked_emails_pct': round((row['total'] - with_emails) / row['total'] * 100, 1),
        'missing_lost_reason': row['missing_lost_reason']
    }


def print_table_report(issues: list[ProposalIssue], title: str):
    """Print issues in a formatted table."""
    if not issues:
        print(f"\n{title}: 0 issues found")
        return

    print(f"\n{title}: {len(issues)} issues")
    print("-" * 100)
    print(f"{'ID':<6} {'Code':<12} {'Status':<16} {'Name':<40} {'Extra Info':<24}")
    print("-" * 100)

    for issue in issues[:50]:  # Limit to 50 for readability
        name = issue.project_name[:38] + '..' if len(issue.project_name) > 40 else issue.project_name
        extra = str(issue.current_value or issue.potential_matches or '')[:22]
        print(f"{issue.proposal_id:<6} {issue.project_code:<12} {issue.status:<16} {name:<40} {extra:<24}")

    if len(issues) > 50:
        print(f"... and {len(issues) - 50} more")


def output_json(all_issues: dict, stats: dict):
    """Output results as JSON."""
    result = {
        'generated_at': datetime.now().isoformat(),
        'summary': stats,
        'issues': {
            'missing_project_value': [asdict(i) for i in all_issues['missing_value']],
            'no_linked_emails': [asdict(i) for i in all_issues['missing_emails']],
            'missing_lost_reason': [asdict(i) for i in all_issues['missing_lost_reason']]
        }
    }
    print(json.dumps(result, indent=2))


def output_csv(all_issues: dict):
    """Output results as CSV."""
    writer = csv.writer(sys.stdout)
    writer.writerow(['proposal_id', 'project_code', 'project_name', 'status', 'issue_type', 'current_value', 'potential_matches'])

    for category in all_issues.values():
        for issue in category:
            writer.writerow([
                issue.proposal_id,
                issue.project_code,
                issue.project_name,
                issue.status,
                issue.issue_type,
                issue.current_value,
                issue.potential_matches
            ])


def main():
    parser = argparse.ArgumentParser(description="Analyze proposal data quality issues")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--csv", action="store_true", help="Output as CSV")
    args = parser.parse_args()

    conn = get_connection()
    cursor = conn.cursor()

    # Run all analyses
    missing_value = analyze_missing_project_value(cursor)
    missing_emails = analyze_missing_emails(cursor)
    missing_lost_reason = analyze_missing_lost_reason(cursor)
    stats = get_summary_stats(cursor)

    all_issues = {
        'missing_value': missing_value,
        'missing_emails': missing_emails,
        'missing_lost_reason': missing_lost_reason
    }

    # Output based on format
    if args.json:
        output_json(all_issues, stats)
    elif args.csv:
        output_csv(all_issues)
    else:
        # Default: formatted text report
        print("=" * 60)
        print("PROPOSAL DATA QUALITY ANALYSIS")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Database: {DB_PATH}")
        print("=" * 60)

        print("\n--- SUMMARY ---")
        print(f"Total proposals:           {stats['total_proposals']}")
        print(f"Missing project_value:     {stats['missing_project_value']} ({stats['missing_project_value_pct']}%)")
        print(f"Without linked emails:     {stats['without_linked_emails']} ({stats['without_linked_emails_pct']}%)")
        print(f"Lost without reason:       {stats['missing_lost_reason']}")

        print_table_report(missing_value, "MISSING PROJECT_VALUE")
        print_table_report(missing_emails, "NO LINKED EMAILS")
        print_table_report(missing_lost_reason, "LOST WITHOUT REASON")

        print("\n" + "=" * 60)
        print("ACTION REQUIRED:")
        print("-" * 60)
        if missing_value:
            print(f"  - Review {len(missing_value)} proposals for project_value")
        if missing_emails:
            print(f"  - Match {len(missing_emails)} proposals to their emails")
        if missing_lost_reason:
            print(f"  - Add lost_reason for {len(missing_lost_reason)} lost proposals (via UI)")
        print()

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
