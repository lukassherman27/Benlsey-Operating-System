#!/usr/bin/env python3
"""
View what emails are currently linked to proposals
"""
import sqlite3
from pathlib import Path
import sys

def view_links(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 80)
    print("📧 LINKED EMAILS OVERVIEW")
    print("=" * 80)
    print(f"Database: {db_path}\n")

    # Get summary stats
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN auto_linked = 1 THEN 1 ELSE 0 END) as auto_linked,
            SUM(CASE WHEN auto_linked = 0 THEN 1 ELSE 0 END) as manual_review
        FROM email_proposal_links
    """)

    stats = cursor.fetchone()
    print(f"📊 SUMMARY:")
    print(f"  Total email-proposal links: {stats['total']}")
    print(f"  ✅ Auto-linked (≥70%):       {stats['auto_linked']}")
    print(f"  ⚠️  Needs manual review:     {stats['manual_review']}")

    # Get breakdown by project
    print(f"\n\n📋 EMAILS BY PROJECT:")
    print("=" * 80)

    cursor.execute("""
        SELECT
            p.project_code,
            p.project_name,
            p.client_company,
            COUNT(*) as total_emails,
            SUM(CASE WHEN l.auto_linked = 1 THEN 1 ELSE 0 END) as auto,
            SUM(CASE WHEN l.auto_linked = 0 THEN 1 ELSE 0 END) as review,
            AVG(l.confidence_score) as avg_confidence
        FROM email_proposal_links l
        JOIN proposals p ON l.proposal_id = p.proposal_id
        GROUP BY p.project_code, p.project_name, p.client_company
        ORDER BY total_emails DESC
    """)

    projects = cursor.fetchall()

    for i, proj in enumerate(projects, 1):
        print(f"\n{i}. {proj['project_code']}: {proj['project_name'][:50]}")
        print(f"   Client: {proj['client_company'] or 'N/A'}")
        print(f"   Emails: {proj['total_emails']} total (✅ {proj['auto']} auto, ⚠️ {proj['review']} review)")
        print(f"   Avg confidence: {proj['avg_confidence']*100:.0f}%")

    # Show sample auto-linked emails
    print(f"\n\n✅ SAMPLE AUTO-LINKED EMAILS (Top 10):")
    print("=" * 80)

    cursor.execute("""
        SELECT
            e.subject,
            e.sender_email,
            e.date,
            p.project_code,
            p.project_name,
            l.confidence_score,
            l.match_reasons
        FROM email_proposal_links l
        JOIN emails e ON l.email_id = e.email_id
        JOIN proposals p ON l.proposal_id = p.proposal_id
        WHERE l.auto_linked = 1
        ORDER BY l.confidence_score DESC, e.date DESC
        LIMIT 10
    """)

    for i, email in enumerate(cursor.fetchall(), 1):
        print(f"\n{i}. [{email['confidence_score']*100:.0f}%] {email['project_code']}")
        print(f"   Subject: {email['subject'][:70]}")
        print(f"   From: {email['sender_email']}")
        print(f"   Date: {email['date']}")
        print(f"   Why: {email['match_reasons']}")

    # Show sample needing review
    print(f"\n\n⚠️  SAMPLE NEEDING REVIEW (Top 10):")
    print("=" * 80)

    cursor.execute("""
        SELECT
            e.subject,
            e.sender_email,
            p.project_code,
            p.project_name,
            l.confidence_score,
            l.match_reasons
        FROM email_proposal_links l
        JOIN emails e ON l.email_id = e.email_id
        JOIN proposals p ON l.proposal_id = p.proposal_id
        WHERE l.auto_linked = 0
        ORDER BY l.confidence_score DESC
        LIMIT 10
    """)

    for i, email in enumerate(cursor.fetchall(), 1):
        print(f"\n{i}. [{email['confidence_score']*100:.0f}%] {email['project_code']}: {email['project_name'][:40]}")
        print(f"   Subject: {email['subject'][:70]}")
        print(f"   From: {email['sender_email']}")
        print(f"   Why: {email['match_reasons']}")

    print("\n" + "=" * 80)

    conn.close()

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "database/bensley_master.db"

    if not Path(db_path).exists():
        print(f"✗ Database not found: {db_path}")
        sys.exit(1)

    view_links(db_path)
