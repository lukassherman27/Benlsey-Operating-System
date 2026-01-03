#!/usr/bin/env python3
"""
Backfill Proposal Data Report Script

Identifies and reports data quality issues in proposals:
1. Missing total_fee_usd in proposals table
2. Missing project_value in proposal_tracker table
3. Proposals with no linked emails
4. Potential email matches for unlinked proposals

Issue: #365
"""

import sqlite3
import csv
import os
import re
from datetime import datetime
from pathlib import Path

# Database path
DB_PATH = os.environ.get(
    'BENSLEY_DB_PATH',
    str(Path(__file__).parent.parent.parent / 'database' / 'bensley_master.db')
)


def get_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def report_missing_fees(conn, output_dir):
    """Report proposals missing total_fee_usd."""
    cursor = conn.cursor()

    # Check proposals table
    cursor.execute("""
        SELECT project_id, project_code, project_title, status, country
        FROM proposals
        WHERE total_fee_usd IS NULL OR total_fee_usd = 0
        ORDER BY project_code
    """)
    missing_proposals = cursor.fetchall()

    # Check proposal_tracker table
    cursor.execute("""
        SELECT id, project_code, project_name, current_status
        FROM proposal_tracker
        WHERE project_value IS NULL OR project_value = 0
        ORDER BY project_code
    """)
    missing_tracker = cursor.fetchall()

    # Write CSV report
    report_path = output_dir / 'missing_fees.csv'
    with open(report_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Source', 'ID', 'Project Code', 'Project Name', 'Status', 'Country'])

        for row in missing_proposals:
            writer.writerow(['proposals', row['project_id'], row['project_code'],
                           row['project_title'], row['status'], row['country']])

        for row in missing_tracker:
            writer.writerow(['proposal_tracker', row['id'], row['project_code'],
                           row['project_name'], row['current_status'], ''])

    return {
        'proposals_missing': len(missing_proposals),
        'tracker_missing': len(missing_tracker),
        'report_path': str(report_path)
    }


def report_missing_emails(conn, output_dir):
    """Report proposals with no linked emails.

    NOTE: email_proposal_links.proposal_id references proposal_tracker.id,
    not proposals.project_id. We check proposal_tracker for email links.
    """
    cursor = conn.cursor()

    # Find proposal_tracker entries without any email links
    cursor.execute("""
        SELECT pt.id, pt.project_code, pt.project_name, pt.current_status
        FROM proposal_tracker pt
        WHERE pt.id NOT IN (
            SELECT DISTINCT proposal_id FROM email_proposal_links
        )
        ORDER BY pt.project_code
    """)
    unlinked = cursor.fetchall()

    # Write CSV report
    report_path = output_dir / 'missing_emails.csv'
    with open(report_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Tracker ID', 'Project Code', 'Project Name', 'Status'])

        for row in unlinked:
            writer.writerow([row['id'], row['project_code'],
                           row['project_name'], row['current_status']])

    return {
        'unlinked_count': len(unlinked),
        'report_path': str(report_path)
    }


def find_potential_email_matches(conn, output_dir):
    """
    Find emails that might match unlinked proposals by project code pattern.

    NOTE: Per CLAUDE.md, we do NOT auto-link. This only creates suggestions
    for human review.

    Uses proposal_tracker for linking (email_proposal_links.proposal_id = proposal_tracker.id)
    """
    cursor = conn.cursor()

    # Get unlinked proposal_tracker entries with their project codes
    cursor.execute("""
        SELECT pt.id, pt.project_code, pt.project_name
        FROM proposal_tracker pt
        WHERE pt.id NOT IN (
            SELECT DISTINCT proposal_id FROM email_proposal_links
        )
        AND pt.project_code IS NOT NULL
        ORDER BY pt.project_code
    """)
    unlinked = cursor.fetchall()

    potential_matches = []

    for proposal in unlinked:
        project_code = proposal['project_code']

        # Extract pattern: "25 BK-033" -> search for "BK-033" or "25 BK-033"
        # Also try project name keywords
        search_patterns = [project_code]

        # Add variant patterns
        if ' ' in project_code:
            parts = project_code.split(' ')
            search_patterns.extend(parts)

        # Search email subjects for matches
        for pattern in search_patterns:
            if len(pattern) < 4:
                continue

            cursor.execute("""
                SELECT email_id, subject, sender_email, date
                FROM emails
                WHERE subject LIKE ?
                AND email_id NOT IN (
                    SELECT email_id FROM email_proposal_links
                )
                LIMIT 5
            """, (f'%{pattern}%',))

            matches = cursor.fetchall()
            for match in matches:
                potential_matches.append({
                    'proposal_id': proposal['id'],
                    'project_code': project_code,
                    'project_name': proposal['project_name'],
                    'email_id': match['email_id'],
                    'email_subject': match['subject'],
                    'email_sender': match['sender_email'],
                    'email_date': match['date'],
                    'matched_pattern': pattern
                })

    # Write CSV report
    report_path = output_dir / 'potential_email_matches.csv'
    with open(report_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Proposal ID', 'Project Code', 'Project Name',
                        'Email ID', 'Email Subject', 'Email Sender',
                        'Email Date', 'Matched Pattern'])

        for match in potential_matches:
            writer.writerow([
                match['proposal_id'], match['project_code'], match['project_name'],
                match['email_id'], match['email_subject'], match['email_sender'],
                match['email_date'], match['matched_pattern']
            ])

    return {
        'potential_matches': len(potential_matches),
        'unique_proposals': len(set(m['proposal_id'] for m in potential_matches)),
        'report_path': str(report_path)
    }


def generate_summary(results, output_dir):
    """Generate summary report."""
    summary_path = output_dir / 'SUMMARY.md'

    with open(summary_path, 'w') as f:
        f.write(f"# Data Quality Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## Missing Fee/Value Data\n\n")
        f.write(f"- **proposals** table: {results['fees']['proposals_missing']} records missing `total_fee_usd`\n")
        f.write(f"- **proposal_tracker** table: {results['fees']['tracker_missing']} records missing `project_value`\n")
        f.write(f"- Report: `{results['fees']['report_path']}`\n\n")

        f.write("## Missing Email Links\n\n")
        f.write(f"- **{results['emails']['unlinked_count']}** proposals have no linked emails\n")
        f.write(f"- Report: `{results['emails']['report_path']}`\n\n")

        f.write("## Potential Email Matches\n\n")
        f.write(f"- Found **{results['matches']['potential_matches']}** potential matches\n")
        f.write(f"- Covering **{results['matches']['unique_proposals']}** unlinked proposals\n")
        f.write(f"- Report: `{results['matches']['report_path']}`\n\n")

        f.write("## Next Steps\n\n")
        f.write("1. Review `missing_fees.csv` - manually enter project values where known\n")
        f.write("2. Review `potential_email_matches.csv` - approve valid matches via UI\n")
        f.write("3. Run email sync to pick up new emails that may match\n\n")

        f.write("---\n")
        f.write("*Generated by scripts/data/backfill_proposal_data.py - Issue #365*\n")

    return str(summary_path)


def main(dry_run=False):
    """Main entry point."""
    print(f"Data Quality Report Generator")
    print(f"Database: {DB_PATH}")
    print(f"Mode: {'DRY RUN' if dry_run else 'FULL REPORT'}")
    print("-" * 50)

    # Create output directory
    output_dir = Path(__file__).parent / 'reports' / datetime.now().strftime('%Y%m%d_%H%M%S')

    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"Output: {output_dir}")

    conn = get_connection()

    try:
        # Get counts for summary
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM proposals")
        total_proposals = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM proposal_tracker")
        total_tracker = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM emails")
        total_emails = cursor.fetchone()[0]

        print(f"\nDatabase Stats:")
        print(f"  - Proposals: {total_proposals}")
        print(f"  - Proposal Tracker: {total_tracker}")
        print(f"  - Emails: {total_emails}")

        if dry_run:
            # Just show counts, don't generate files
            cursor.execute("""
                SELECT COUNT(*) FROM proposals
                WHERE total_fee_usd IS NULL OR total_fee_usd = 0
            """)
            missing_fees = cursor.fetchone()[0]

            # NOTE: email_proposal_links.proposal_id references proposal_tracker.id
            cursor.execute("""
                SELECT COUNT(*) FROM proposal_tracker pt
                WHERE pt.id NOT IN (
                    SELECT DISTINCT proposal_id FROM email_proposal_links
                )
            """)
            unlinked = cursor.fetchone()[0]

            print(f"\nData Quality Issues:")
            print(f"  - Missing fees: {missing_fees} proposals ({missing_fees*100/total_proposals:.1f}%)")
            print(f"  - Unlinked emails: {unlinked} tracker entries ({unlinked*100/total_tracker:.1f}%)")
            print(f"\nRun without --dry-run to generate full reports.")

        else:
            # Generate full reports
            print(f"\nGenerating reports...")

            results = {
                'fees': report_missing_fees(conn, output_dir),
                'emails': report_missing_emails(conn, output_dir),
                'matches': find_potential_email_matches(conn, output_dir)
            }

            summary_path = generate_summary(results, output_dir)

            print(f"\nReports generated:")
            print(f"  - {results['fees']['report_path']}")
            print(f"  - {results['emails']['report_path']}")
            print(f"  - {results['matches']['report_path']}")
            print(f"  - {summary_path}")

            print(f"\nSummary:")
            print(f"  - {results['fees']['proposals_missing']} proposals missing fees")
            print(f"  - {results['emails']['unlinked_count']} proposals missing email links")
            print(f"  - {results['matches']['potential_matches']} potential email matches found")

    finally:
        conn.close()

    print("\nDone!")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generate data quality reports for proposals')
    parser.add_argument('--dry-run', action='store_true', help='Show counts only, no file output')
    args = parser.parse_args()

    main(dry_run=args.dry_run)
