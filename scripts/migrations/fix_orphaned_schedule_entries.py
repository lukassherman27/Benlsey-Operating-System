"""
Migration: Fix orphaned schedule_entries

Problem:
- schedule_entries references schedule_id 1 and 2
- weekly_schedules table is empty (foreign key orphans)
- schedule_entries references member_ids 66-103 that don't exist

Solution:
1. Create weekly_schedules records for schedule_id 1 and 2
2. Create placeholder team_members for missing member_ids
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent / "database" / "bensley_master.db"

def run_migration():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print("=" * 60)
    print("Migration: Fix Orphaned Schedule Entries")
    print("=" * 60)

    # Step 1: Check current state
    print("\n1. Current State:")
    cur.execute("SELECT COUNT(*) FROM weekly_schedules")
    ws_count = cur.fetchone()[0]
    print(f"   - weekly_schedules: {ws_count} records")

    cur.execute("SELECT COUNT(*) FROM schedule_entries")
    se_count = cur.fetchone()[0]
    print(f"   - schedule_entries: {se_count} records")

    cur.execute("SELECT COUNT(*) FROM team_members")
    tm_count = cur.fetchone()[0]
    print(f"   - team_members: {tm_count} records")

    # Step 2: Get schedule_id info from entries
    print("\n2. Analyzing schedule_entries...")
    cur.execute("""
        SELECT
            schedule_id,
            MIN(work_date) as week_start,
            MAX(work_date) as week_end,
            COUNT(*) as entries
        FROM schedule_entries
        GROUP BY schedule_id
    """)
    schedules = cur.fetchall()

    for s in schedules:
        print(f"   - Schedule {s['schedule_id']}: {s['week_start']} to {s['week_end']} ({s['entries']} entries)")

    # Step 3: Create weekly_schedules records
    print("\n3. Creating weekly_schedules records...")

    schedules_to_create = [
        {
            "schedule_id": 1,
            "office": "Bali",  # Assuming Bali based on team structure
            "week_start_date": "2025-11-10",
            "week_end_date": "2025-11-14",
            "status": "published",
            "created_by": "migration"
        },
        {
            "schedule_id": 2,
            "office": "Bali",
            "week_start_date": "2025-11-03",
            "week_end_date": "2025-12-12",  # Extended schedule
            "status": "published",
            "created_by": "migration"
        }
    ]

    for s in schedules_to_create:
        # Check if already exists
        cur.execute("SELECT COUNT(*) FROM weekly_schedules WHERE schedule_id = ?", (s["schedule_id"],))
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO weekly_schedules
                (schedule_id, office, week_start_date, week_end_date, status, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (s["schedule_id"], s["office"], s["week_start_date"], s["week_end_date"], s["status"], s["created_by"]))
            print(f"   ✓ Created schedule_id {s['schedule_id']}: {s['week_start_date']} to {s['week_end_date']}")
        else:
            print(f"   - Schedule {s['schedule_id']} already exists, skipping")

    # Step 4: Find missing team members
    print("\n4. Finding missing team member IDs...")
    cur.execute("""
        SELECT DISTINCT e.member_id
        FROM schedule_entries e
        LEFT JOIN team_members t ON e.member_id = t.member_id
        WHERE t.member_id IS NULL
        ORDER BY e.member_id
    """)
    missing_ids = [row[0] for row in cur.fetchall()]
    print(f"   - Missing member_ids: {missing_ids}")

    # Step 5: Create placeholder team members
    print("\n5. Creating placeholder team members...")
    for mid in missing_ids:
        cur.execute("SELECT COUNT(*) FROM team_members WHERE member_id = ?", (mid,))
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO team_members
                (member_id, email, full_name, nickname, office, discipline, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, datetime('now'), datetime('now'))
            """, (
                mid,
                f"team{mid}@bensley.com",  # Placeholder email
                f"Team Member {mid}",  # Placeholder name
                f"TM{mid}",  # Placeholder nickname
                "Bali",  # Default office
                "Interior"  # Valid discipline (Architecture, Interior, Landscape, Artwork, Management)
            ))
            print(f"   ✓ Created placeholder for member_id {mid}")

    # Step 6: Verify fixes
    print("\n6. Verification:")
    cur.execute("SELECT COUNT(*) FROM weekly_schedules")
    print(f"   - weekly_schedules: {cur.fetchone()[0]} records")

    cur.execute("""
        SELECT COUNT(*) FROM schedule_entries e
        LEFT JOIN weekly_schedules w ON e.schedule_id = w.schedule_id
        WHERE w.schedule_id IS NULL
    """)
    orphaned_schedules = cur.fetchone()[0]
    print(f"   - Orphaned schedule entries: {orphaned_schedules}")

    cur.execute("""
        SELECT COUNT(*) FROM schedule_entries e
        LEFT JOIN team_members t ON e.member_id = t.member_id
        WHERE t.member_id IS NULL
    """)
    orphaned_members = cur.fetchone()[0]
    print(f"   - Entries with missing members: {orphaned_members}")

    # Commit
    conn.commit()
    print("\n✓ Migration complete!")
    print("\nNote: Placeholder team members created with names like 'Team Member 66'")
    print("Update these with real names when schedule PDFs are processed.")

    conn.close()

if __name__ == "__main__":
    run_migration()
