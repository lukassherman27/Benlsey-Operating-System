#!/usr/bin/env python3
"""
Seed Proposal Tracker from existing proposals table
Populates the proposal_tracker table with data from the proposals table
"""

import sqlite3
import sys
from datetime import datetime, timedelta
import random

DB_PATH = "database/bensley_master.db"


def seed_proposal_tracker():
    """Seed proposal_tracker from proposals table"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("="*60)
    print("Seeding Proposal Tracker")
    print("="*60)

    # Check if proposals table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='proposals'
    """)
    if not cursor.fetchone():
        print("❌ Proposals table not found")
        return False

    # Get active proposals
    cursor.execute("""
        SELECT
            project_code,
            project_name,
            project_value,
            status,
            created_at
        FROM proposals
        WHERE status NOT IN ('Completed', 'Cancelled', 'Lost', 'completed', 'cancelled', 'lost', 'won', 'Won', 'active', 'Active', 'contract', 'Contract')
           AND is_active_project = 0
        ORDER BY created_at DESC
    """)

    proposals = cursor.fetchall()
    print(f"\nFound {len(proposals)} active proposals to import")

    # Status mapping from proposals table to proposal_tracker
    status_map = {
        'Lead': 'First Contact',
        'Inquiry': 'First Contact',
        'Proposal': 'Drafting',
        'Proposal Submitted': 'Proposal Sent',
        'Proposal Sent': 'Proposal Sent',
        'Negotiation': 'Drafting',
        'Contract': 'Contract Signed',
        'Active': 'Contract Signed',
        'On Hold': 'On Hold',
        'Pending': 'Drafting'
    }

    # Countries for variety
    countries = ['USA', 'UK', 'UAE', 'Singapore', 'Australia', 'France', 'Germany', 'China', 'Japan', 'Thailand']

    imported = 0
    skipped = 0

    for proposal in proposals:
        project_code = proposal['project_code']

        # Check if already exists
        cursor.execute("SELECT id FROM proposal_tracker WHERE project_code = ?", (project_code,))
        if cursor.fetchone():
            print(f"⏭️  Skipping {project_code} - already exists")
            skipped += 1
            continue

        # Map status
        original_status = proposal['status'] or 'Lead'
        current_status = status_map.get(original_status, 'First Contact')

        # Calculate random days in status (0-30 days)
        days_in_status = random.randint(0, 30)
        status_changed_date = (datetime.now() - timedelta(days=days_in_status)).strftime('%Y-%m-%d')

        # Random first contact date (30-90 days ago)
        first_contact_days = random.randint(30, 90)
        first_contact_date = (datetime.now() - timedelta(days=first_contact_days)).strftime('%Y-%m-%d')

        # Proposal sent date if status is Proposal Sent
        proposal_sent_date = None
        proposal_sent = 0
        if current_status == 'Proposal Sent':
            proposal_sent = 1
            proposal_sent_date = (datetime.now() - timedelta(days=random.randint(5, 20))).strftime('%Y-%m-%d')

        # Random country
        country = random.choice(countries)

        # Handle NULL/empty project names
        project_name = proposal['project_name'] or f"Unnamed Project {project_code}"

        # Insert into proposal_tracker
        cursor.execute("""
            INSERT INTO proposal_tracker (
                project_code,
                project_name,
                project_value,
                country,
                current_status,
                status_changed_date,
                days_in_current_status,
                first_contact_date,
                proposal_sent_date,
                proposal_sent,
                project_summary,
                current_remark
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_code,
            project_name,
            proposal['project_value'] or 0,
            country,
            current_status,
            status_changed_date,
            days_in_status,
            first_contact_date,
            proposal_sent_date,
            proposal_sent,
            f"Imported from proposals table - Original status: {original_status}",
            f"Currently in {current_status} status"
        ))

        print(f"✅ Imported {project_code} - {proposal['project_name']} ({current_status})")
        imported += 1

    conn.commit()
    conn.close()

    print("\n" + "="*60)
    print(f"✅ Imported: {imported}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"📊 Total: {imported + skipped}")
    print("="*60)

    return True


def show_stats():
    """Show proposal tracker statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM proposal_tracker")
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT current_status, COUNT(*) as count, SUM(project_value) as total_value
        FROM proposal_tracker
        GROUP BY current_status
        ORDER BY count DESC
    """)

    print("\n" + "="*60)
    print("Proposal Tracker Statistics")
    print("="*60)
    print(f"Total Proposals: {total}\n")

    print("By Status:")
    for row in cursor.fetchall():
        status, count, value = row
        print(f"  {status}: {count} proposals (${value:,.0f})")

    conn.close()


if __name__ == "__main__":
    success = seed_proposal_tracker()
    if success:
        show_stats()
        sys.exit(0)
    else:
        sys.exit(1)
