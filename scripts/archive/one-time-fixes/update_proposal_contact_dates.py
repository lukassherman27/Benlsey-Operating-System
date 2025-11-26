#!/usr/bin/env python3
"""
Auto-Update Proposal Contact Dates

This script automatically updates last_contact_date and days_since_contact
in the proposals table based on the most recent email linked to each proposal.

Logic:
- Find the most recent email (sent OR received) for each proposal
- Update last_contact_date to that email's date
- Recalculate days_since_contact

This ensures the follow-up tracker is accurate based on actual email activity.
"""

import sqlite3
import os
from datetime import datetime
from email.utils import parsedate_to_datetime
from dotenv import load_dotenv

load_dotenv()

def update_contact_dates(db_path, dry_run=False):
    """
    Update last_contact_date for all proposals based on linked emails.

    Args:
        db_path: Path to database
        dry_run: If True, only show what would be updated without making changes
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 100)
    print("📧 UPDATING PROPOSAL CONTACT DATES FROM EMAILS")
    print("=" * 100)
    print()

    # Get all proposals with their most recent linked email
    cursor.execute("""
        SELECT
            p.proposal_id,
            p.project_code,
            p.project_name,
            p.last_contact_date as old_contact_date,
            p.days_since_contact as old_days_since,
            MAX(e.date) as most_recent_email_date,
            COUNT(e.email_id) as email_count
        FROM proposals p
        LEFT JOIN email_proposal_links epl ON p.proposal_id = epl.proposal_id
        LEFT JOIN emails e ON epl.email_id = e.email_id
        WHERE p.status IN ('proposal', 'negotiating', 'pending')
        GROUP BY p.proposal_id
        HAVING email_count > 0
        ORDER BY p.project_code
    """)

    proposals = cursor.fetchall()

    if not proposals:
        print("✅ No proposals with linked emails found")
        conn.close()
        return

    updates = []
    no_change = []

    for proposal in proposals:
        project_code = proposal['project_code']
        project_name = proposal['project_name']
        old_date = proposal['old_contact_date']
        new_date = proposal['most_recent_email_date']
        email_count = proposal['email_count']

        if not new_date:
            continue

        # Parse dates (handle both ISO and RFC 2822 formats)
        try:
            # Try ISO format first
            try:
                new_date_obj = datetime.fromisoformat(new_date.replace('Z', '+00:00'))
            except:
                # Try RFC 2822 format (email date format)
                new_date_obj = parsedate_to_datetime(new_date)

            new_date_str = new_date_obj.strftime('%Y-%m-%d')

            # Calculate days since contact
            days_since = (datetime.now(new_date_obj.tzinfo) - new_date_obj).days

            # Check if this is different from current value
            if old_date != new_date_str:
                updates.append({
                    'proposal_id': proposal['proposal_id'],
                    'project_code': project_code,
                    'project_name': project_name,
                    'old_date': old_date or 'Never',
                    'new_date': new_date_str,
                    'days_since': days_since,
                    'email_count': email_count
                })
            else:
                no_change.append(project_code)

        except Exception as e:
            print(f"⚠️  Error processing {project_code}: {e}")
            continue

    # Display updates
    if updates:
        print(f"📝 Found {len(updates)} proposals to update:\n")

        for update in updates:
            print(f"📌 {update['project_code']}: {update['project_name']}")
            print(f"   Old Contact Date: {update['old_date']}")
            print(f"   New Contact Date: {update['new_date']} ({update['days_since']} days ago)")
            print(f"   Based on {update['email_count']} linked emails")
            print()

        if not dry_run:
            # Apply updates
            print("💾 Applying updates...")
            for update in updates:
                cursor.execute("""
                    UPDATE proposals
                    SET
                        last_contact_date = ?,
                        days_since_contact = ?,
                        updated_at = datetime('now'),
                        updated_by = 'email_sync'
                    WHERE proposal_id = ?
                """, (update['new_date'], update['days_since'], update['proposal_id']))

            conn.commit()
            print(f"✅ Updated {len(updates)} proposals")
        else:
            print("🔍 DRY RUN - No changes made")
    else:
        print("✅ All proposals already have up-to-date contact dates")

    if no_change:
        print(f"\n📊 {len(no_change)} proposals already up-to-date")

    conn.close()

    print("\n" + "=" * 100)
    print("✅ CONTACT DATE UPDATE COMPLETE")
    print("=" * 100)

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Update proposal contact dates from linked emails')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')
    args = parser.parse_args()

    db_path = os.getenv('DATABASE_PATH', 'database/bensley_master.db')

    update_contact_dates(db_path, dry_run=args.dry_run)

if __name__ == '__main__':
    main()
