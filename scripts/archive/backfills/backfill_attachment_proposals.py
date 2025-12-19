#!/usr/bin/env python3
"""
Backfill proposal_id on email_attachments based on email_proposal_links.
This links attachments to proposals via their email's existing proposal links.
"""
import sqlite3

DB_PATH = "database/bensley_master.db"

def backfill_attachment_proposals():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get attachment -> email -> proposal mappings
    # For attachments with no proposal_id, find the proposal via email_proposal_links
    cursor.execute("""
        SELECT ea.attachment_id, epl.proposal_id
        FROM email_attachments ea
        JOIN email_proposal_links epl ON ea.email_id = epl.email_id
        WHERE ea.proposal_id IS NULL
    """)

    updates = cursor.fetchall()
    print(f"Found {len(updates)} attachments to link to proposals")

    if updates:
        cursor.executemany(
            "UPDATE email_attachments SET proposal_id = ? WHERE attachment_id = ?",
            [(pid, aid) for aid, pid in updates]
        )
        conn.commit()
        print(f"Updated {len(updates)} attachments")

    # Report
    cursor.execute("""
        SELECT
          SUM(CASE WHEN proposal_id IS NOT NULL THEN 1 ELSE 0 END) as linked,
          COUNT(*) as total
        FROM email_attachments
    """)
    linked, total = cursor.fetchone()
    pct = 100 * linked // total if total > 0 else 0
    print(f"\nAttachments linked to proposals: {linked}/{total} ({pct}%)")

    # Show sample of linked attachments
    cursor.execute("""
        SELECT ea.filename, p.project_code, p.project_name
        FROM email_attachments ea
        JOIN proposals p ON ea.proposal_id = p.proposal_id
        LIMIT 5
    """)
    print("\nSample linked attachments:")
    for row in cursor.fetchall():
        print(f"  {row[0]} -> {row[1]} ({row[2][:40]}...)" if row[2] and len(row[2]) > 40 else f"  {row[0]} -> {row[1]} ({row[2]})")

    conn.close()

if __name__ == "__main__":
    backfill_attachment_proposals()
