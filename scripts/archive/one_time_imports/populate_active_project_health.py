#!/usr/bin/env python3
"""
Populate health metrics for active projects
Handles RFC 2822 date parsing that SQLite cannot handle
"""
import sqlite3
from datetime import datetime
from email.utils import parsedate_to_datetime

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get all active projects with email links
cursor.execute("""
    SELECT DISTINCT p.proposal_id, p.project_code, p.project_name
    FROM proposals p
    JOIN email_proposal_links epl ON p.proposal_id = epl.proposal_id
    WHERE p.is_active_project = 1
    ORDER BY p.project_code
""")

projects = cursor.fetchall()
print(f"Found {len(projects)} active projects with email links\n")

for proposal_id, project_code, project_name in projects:
    # Get most recent email date for this project
    cursor.execute("""
        SELECT MAX(e.date) as last_email_date
        FROM emails e
        JOIN email_proposal_links epl ON e.email_id = epl.email_id
        WHERE epl.proposal_id = ?
    """, (proposal_id,))

    result = cursor.fetchone()
    if result and result[0]:
        try:
            # Parse RFC 2822 date
            last_date = parsedate_to_datetime(result[0])
            days_since = (datetime.now(last_date.tzinfo) - last_date).days

            # Calculate health score
            if days_since <= 7:
                health_score = 100
            elif days_since <= 14:
                health_score = 85
            elif days_since <= 30:
                health_score = 70
            elif days_since <= 60:
                health_score = 50
            else:
                health_score = 25

            # Update proposal
            cursor.execute("""
                UPDATE proposals
                SET days_since_contact = ?,
                    last_contact_date = ?,
                    health_score = ?
                WHERE proposal_id = ?
            """, (days_since, last_date.date().isoformat(), health_score, proposal_id))

            status = "🟢" if health_score >= 85 else "🟡" if health_score >= 70 else "🟠" if health_score >= 50 else "🔴"
            print(f"{status} {project_code}: {days_since} days ago, score {health_score}")

        except Exception as e:
            print(f"❌ {project_code}: Error parsing date - {e}")

conn.commit()

# Show final summary
cursor.execute("""
    SELECT
        CASE
            WHEN health_score >= 85 THEN '🟢 Healthy'
            WHEN health_score >= 70 THEN '🟡 Good'
            WHEN health_score >= 50 THEN '🟠 At Risk'
            ELSE '🔴 Critical'
        END as status,
        COUNT(*) as count
    FROM proposals
    WHERE is_active_project = 1
    GROUP BY status
    ORDER BY MIN(health_score) DESC
""")

print("\n" + "="*60)
print("FINAL HEALTH DISTRIBUTION:")
print("="*60)
for status, count in cursor.fetchall():
    print(f"  {status}: {count} projects")

cursor.execute("""
    SELECT COUNT(*) FROM proposals
    WHERE is_active_project = 1 AND days_since_contact IS NOT NULL
""")
with_data = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*) FROM proposals WHERE is_active_project = 1
""")
total = cursor.fetchone()[0]

print(f"\n  Total: {total} projects")
print(f"  With email data: {with_data}")
print(f"  Without email data: {total - with_data}")
print("="*60)

conn.close()
print("\n✓ Health metrics updated for active projects")
