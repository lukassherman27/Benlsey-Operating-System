#!/usr/bin/env python3
"""
Stale Proposals Weekly Report Generator

Replaces individual follow_up_needed suggestions with a single weekly report.
Groups stale proposals by urgency tier:
- 90+ days: Critical
- 30-90 days: High
- 14-30 days: Medium
- 7-14 days: Watch

Run weekly (or on-demand) instead of creating 150+ individual suggestions.
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')


def get_stale_proposals() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all stale proposals grouped by urgency tier.

    Returns dict with keys: critical, high, medium, watch
    Each contains list of proposal dicts with days_since_contact, last_email info
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get proposals with their email activity
    cursor.execute("""
        WITH email_activity AS (
            SELECT
                epl.proposal_id,
                MAX(e.date) as last_email_date,
                MAX(CASE WHEN e.sender_email LIKE '%@bensley.com%' THEN e.date END) as our_last_email,
                MAX(CASE WHEN e.sender_email NOT LIKE '%@bensley.com%' THEN e.date END) as client_last_email,
                COUNT(*) as email_count,
                -- Get last sender
                (SELECT sender_email FROM emails e2
                 JOIN email_proposal_links epl2 ON e2.email_id = epl2.email_id
                 WHERE epl2.proposal_id = epl.proposal_id
                 ORDER BY e2.date DESC LIMIT 1) as last_sender
            FROM email_proposal_links epl
            JOIN emails e ON epl.email_id = e.email_id
            GROUP BY epl.proposal_id
        )
        SELECT
            p.proposal_id,
            p.project_code,
            p.project_name,
            p.status,
            p.client_company,
            p.contact_person,
            p.contact_email,
            ea.last_email_date,
            ea.our_last_email,
            ea.client_last_email,
            ea.email_count,
            ea.last_sender,
            CAST(julianday('now') - julianday(ea.last_email_date) AS INTEGER) as days_since_contact,
            CAST(julianday('now') - julianday(ea.client_last_email) AS INTEGER) as days_since_client,
            CASE
                WHEN ea.last_sender LIKE '%@bensley.com%' THEN 'We sent last'
                ELSE 'Client sent last'
            END as who_sent_last
        FROM proposals p
        JOIN email_activity ea ON p.proposal_id = ea.proposal_id
        WHERE p.status NOT IN ('won', 'lost', 'cancelled', 'declined', 'dormant', 'on_hold', 'Contract Signed')
        AND ea.last_email_date IS NOT NULL
        ORDER BY days_since_contact DESC
    """)

    proposals = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Group by urgency
    result = {
        'critical': [],  # 90+ days
        'high': [],      # 30-90 days
        'medium': [],    # 14-30 days
        'watch': []      # 7-14 days
    }

    for p in proposals:
        days = p['days_since_contact']
        if days is None:
            continue

        # Only include if WE sent the last email (waiting for response)
        if p['who_sent_last'] == 'We sent last':
            if days >= 90:
                result['critical'].append(p)
            elif days >= 30:
                result['high'].append(p)
            elif days >= 14:
                result['medium'].append(p)
            elif days >= 7:
                result['watch'].append(p)

    return result


def generate_text_report(stale: Dict[str, List]) -> str:
    """Generate plain text report"""
    lines = []
    today = datetime.now().strftime('%Y-%m-%d')

    lines.append("=" * 70)
    lines.append(f"STALE PROPOSALS REPORT - {today}")
    lines.append("Proposals where WE sent the last email and haven't heard back")
    lines.append("=" * 70)
    lines.append("")

    # Summary
    total = sum(len(v) for v in stale.values())
    lines.append(f"Total stale proposals: {total}")
    lines.append(f"  Critical (90+ days):  {len(stale['critical'])}")
    lines.append(f"  High (30-90 days):    {len(stale['high'])}")
    lines.append(f"  Medium (14-30 days):  {len(stale['medium'])}")
    lines.append(f"  Watch (7-14 days):    {len(stale['watch'])}")
    lines.append("")

    # Critical section
    if stale['critical']:
        lines.append("-" * 70)
        lines.append("CRITICAL - No response in 90+ days")
        lines.append("-" * 70)
        for p in stale['critical']:
            lines.append(f"  {p['project_code']} ({p['project_name']})")
            lines.append(f"    Days silent: {p['days_since_contact']}")
            lines.append(f"    Last email:  {p['last_email_date'][:10] if p['last_email_date'] else 'N/A'}")
            lines.append(f"    Contact:     {p['contact_person'] or 'N/A'} ({p['contact_email'] or 'N/A'})")
            lines.append(f"    Status:      {p['status']}")
            lines.append("")

    # High section
    if stale['high']:
        lines.append("-" * 70)
        lines.append("HIGH PRIORITY - No response in 30-90 days")
        lines.append("-" * 70)
        for p in stale['high']:
            lines.append(f"  {p['project_code']} ({p['project_name']})")
            lines.append(f"    Days silent: {p['days_since_contact']}, Last: {p['last_email_date'][:10] if p['last_email_date'] else 'N/A'}")
            lines.append(f"    Contact: {p['contact_person'] or 'N/A'}")
            lines.append("")

    # Medium section
    if stale['medium']:
        lines.append("-" * 70)
        lines.append("MEDIUM - No response in 14-30 days")
        lines.append("-" * 70)
        for p in stale['medium']:
            lines.append(f"  {p['project_code']} ({p['project_name']}) - {p['days_since_contact']} days")

    lines.append("")

    # Watch section
    if stale['watch']:
        lines.append("-" * 70)
        lines.append("WATCH - No response in 7-14 days")
        lines.append("-" * 70)
        for p in stale['watch']:
            lines.append(f"  {p['project_code']} ({p['project_name']}) - {p['days_since_contact']} days")

    lines.append("")
    lines.append("=" * 70)
    lines.append(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("Run: python scripts/core/generate_stale_proposals_report.py")
    lines.append("=" * 70)

    return "\n".join(lines)


def save_report(report_text: str) -> Path:
    """Save report to reports directory"""
    reports_dir = Path('reports/weekly')
    reports_dir.mkdir(parents=True, exist_ok=True)

    filename = f"stale_proposals_{datetime.now().strftime('%Y-%m-%d')}.txt"
    filepath = reports_dir / filename

    with open(filepath, 'w') as f:
        f.write(report_text)

    return filepath


def create_single_suggestion(stale: Dict[str, List]) -> int:
    """
    Create a single summary suggestion instead of 150 individual ones.
    Returns suggestion_id.
    """
    total = sum(len(v) for v in stale.values())

    if total == 0:
        print("No stale proposals found - skipping suggestion creation")
        return 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Build summary description
    critical_codes = [f"{p['project_code']} ({p['project_name'][:30]})" for p in stale['critical'][:5]]
    high_codes = [f"{p['project_code']} ({p['project_name'][:30]})" for p in stale['high'][:5]]

    description_parts = [
        f"Weekly stale proposals summary: {total} proposals need follow-up.",
        "",
        f"CRITICAL ({len(stale['critical'])} proposals, 90+ days):",
    ]
    if critical_codes:
        description_parts.extend([f"  - {c}" for c in critical_codes])
        if len(stale['critical']) > 5:
            description_parts.append(f"  ... and {len(stale['critical']) - 5} more")
    else:
        description_parts.append("  None")

    description_parts.extend([
        "",
        f"HIGH ({len(stale['high'])} proposals, 30-90 days):",
    ])
    if high_codes:
        description_parts.extend([f"  - {c}" for c in high_codes])
        if len(stale['high']) > 5:
            description_parts.append(f"  ... and {len(stale['high']) - 5} more")
    else:
        description_parts.append("  None")

    description = "\n".join(description_parts)

    # Create single suggestion
    cursor.execute("""
        INSERT INTO ai_suggestions (
            suggestion_type, priority, confidence_score,
            source_type, source_reference,
            title, description, suggested_action,
            status, created_at
        ) VALUES (
            'weekly_stale_report', 'high', 0.95,
            'system', 'weekly_stale_report',
            ?, ?, 'Review weekly stale proposals report',
            'pending', datetime('now')
        )
    """, (
        f"Weekly Stale Proposals: {total} need follow-up",
        description
    ))

    suggestion_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return suggestion_id


def cleanup_old_followup_suggestions() -> int:
    """Delete old individual follow_up_needed suggestions"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM ai_suggestions
        WHERE suggestion_type = 'follow_up_needed'
        AND status = 'pending'
    """)

    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    return deleted


def main():
    print("Generating Stale Proposals Report...")
    print()

    # Get stale proposals
    stale = get_stale_proposals()

    # Generate and save report
    report_text = generate_text_report(stale)
    filepath = save_report(report_text)

    print(report_text)
    print()
    print(f"Report saved to: {filepath}")
    print()

    # Optional: Create single summary suggestion
    # Uncomment to enable:
    # suggestion_id = create_single_suggestion(stale)
    # print(f"Created summary suggestion #{suggestion_id}")

    return filepath


if __name__ == "__main__":
    main()
