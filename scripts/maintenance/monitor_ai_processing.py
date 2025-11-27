#!/usr/bin/env python3
"""
Real-time monitor for AI processing decisions

Shows what the AI is doing and lets you verify linkages are correct
"""

import sqlite3
import time
from datetime import datetime

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


def watch_recent_updates():
    """Watch recent AI updates in real-time"""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 100)
    print("🔍 AI PROCESSING MONITOR - Real-time Updates")
    print("=" * 100)
    print("\nPress Ctrl+C to stop\n")

    last_email_id = 0
    last_doc_id = 0

    while True:
        # Check for new email categorizations
        cursor.execute("""
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.category,
                e.date as email_date,
                GROUP_CONCAT(epl.project_code) as linked_projects
            FROM emails e
            LEFT JOIN email_project_links epl ON e.email_id = epl.email_id
            WHERE e.email_id > ?
            AND e.category IS NOT NULL
            GROUP BY e.email_id
            ORDER BY e.email_id
            LIMIT 10
        """, (last_email_id,))

        emails = cursor.fetchall()

        for email in emails:
            print(f"\n📧 Email #{email['email_id']}: {email['subject'][:60]}")
            print(f"   From: {email['sender_email']}")
            print(f"   Category: {email['category']}")
            print(f"   Date: {email['email_date']}")

            if email['linked_projects']:
                projects = email['linked_projects'].split(',')
                print(f"   ✅ Linked to: {', '.join(projects)}")

                # Show which project this updates "last contact" for
                for project_code in projects:
                    cursor.execute("""
                        SELECT
                            p.project_code,
                            p.project_name,
                            p.days_since_contact,
                            (SELECT COUNT(*) FROM email_project_links epl2
                             WHERE epl2.project_code = p.project_code) as total_emails
                        FROM projects p
                        WHERE p.project_code = ?
                    """, (project_code.strip(),))

                    project = cursor.fetchone()
                    if project:
                        print(f"      → {project['project_code']}: {project['project_name']}")
                        print(f"         Last contact: {project['days_since_contact']} days ago")
                        print(f"         Total emails: {project['total_emails']}")
            else:
                print(f"   ⚠️  Not linked to any project (general categorization only)")

            last_email_id = email['email_id']

        # Check for new document intelligence
        cursor.execute("""
            SELECT
                d.document_id,
                d.file_name,
                d.document_type,
                d.project_code,
                di.fee_amount,
                di.fee_currency,
                di.confidence_score,
                di.extracted_at
            FROM documents d
            LEFT JOIN document_intelligence di ON d.document_id = di.document_id
            WHERE d.document_id > ?
            AND d.document_type IS NOT NULL
            ORDER BY d.document_id
            LIMIT 10
        """, (last_doc_id,))

        docs = cursor.fetchall()

        for doc in docs:
            print(f"\n📄 Document #{doc['document_id']}: {doc['file_name'][:60]}")
            print(f"   Type: {doc['document_type']}")

            if doc['project_code']:
                print(f"   ✅ Linked to: {doc['project_code']}")

                # Show project details
                cursor.execute("""
                    SELECT project_name, project_value
                    FROM projects
                    WHERE project_code = ?
                """, (doc['project_code'],))

                project = cursor.fetchone()
                if project:
                    print(f"      → {project['project_name']}")
                    print(f"         Current DB value: ${project['project_value'] or 0:,.0f}")
            else:
                print(f"   ⚠️  Not linked to any project yet")

            if doc['fee_amount'] and doc['fee_amount'] != '':
                confidence = doc['confidence_score'] or 0
                print(f"   💰 Extracted value: ${float(doc['fee_amount'] or 0):,.0f} {doc['fee_currency']}")
                print(f"   📊 AI Confidence: {confidence*100:.0f}%")

            last_doc_id = doc['document_id']

        # Check for new AI suggestions
        cursor.execute("""
            SELECT
                id,
                project_code,
                suggestion_type,
                impact_summary,
                confidence,
                created_at
            FROM ai_suggestions_queue
            WHERE status = 'pending'
            ORDER BY created_at DESC
            LIMIT 5
        """)

        suggestions = cursor.fetchall()

        if suggestions:
            print(f"\n💡 {len(suggestions)} AI Suggestions Pending Review:")
            for sug in suggestions[:3]:
                print(f"   • [{sug['project_code']}] {sug['impact_summary'][:70]}")
                print(f"     Confidence: {sug['confidence']*100:.0f}%")

        # Show summary stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_emails,
                COUNT(CASE WHEN category IS NOT NULL THEN 1 END) as categorized,
                COUNT(CASE WHEN category IS NULL THEN 1 END) as uncategorized
            FROM emails
        """)
        stats = cursor.fetchone()

        cursor.execute("""
            SELECT
                COUNT(*) as total_docs,
                COUNT(CASE WHEN document_type IS NOT NULL THEN 1 END) as classified
            FROM documents
        """)
        doc_stats = cursor.fetchone()

        print(f"\n{'─' * 100}")
        print(f"📊 Progress: Emails {stats['categorized']}/{stats['total_emails']} ({stats['categorized']*100/stats['total_emails']:.1f}%) | "
              f"Documents {doc_stats['classified']}/{doc_stats['total_docs']} ({doc_stats['classified']*100/doc_stats['total_docs']:.1f}%)")
        print(f"{'─' * 100}")

        time.sleep(5)  # Check every 5 seconds

    conn.close()


def show_recent_linkages():
    """Show most recent email-project linkages for verification"""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 100)
    print("🔗 RECENT EMAIL-PROJECT LINKAGES")
    print("=" * 100)

    cursor.execute("""
        SELECT
            e.subject,
            e.sender_email,
            e.date,
            epl.project_code,
            p.project_name,
            epl.link_method,
            epl.confidence,
            epl.created_at
        FROM email_project_links epl
        JOIN emails e ON epl.email_id = e.email_id
        JOIN projects p ON epl.project_code = p.project_code
        ORDER BY epl.created_at DESC
        LIMIT 20
    """)

    links = cursor.fetchall()

    for i, link in enumerate(links, 1):
        print(f"\n[{i}] {link['subject'][:60]}")
        print(f"    From: {link['sender_email']}")
        print(f"    Date: {link['date']}")
        print(f"    → Linked to: {link['project_code']} - {link['project_name']}")
        print(f"    Method: {link['link_method']} | Confidence: {link['confidence']*100:.0f}%")
        print(f"    Created: {link['created_at']}")

    conn.close()


def show_projects_with_last_contact():
    """Show projects with their last contact dates"""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 100)
    print("📅 PROJECTS WITH LAST CONTACT DATES")
    print("=" * 100)

    cursor.execute("""
        SELECT
            p.project_code,
            p.project_name,
            p.days_since_contact,
            p.last_contact_date,
            COUNT(epl.email_id) as email_count,
            MAX(e.date) as most_recent_email
        FROM projects p
        LEFT JOIN email_project_links epl ON p.project_code = epl.project_code
        LEFT JOIN emails e ON epl.email_id = e.email_id
        WHERE p.is_active_project = 1
        GROUP BY p.project_code
        ORDER BY p.days_since_contact ASC
        LIMIT 30
    """)

    projects = cursor.fetchall()

    print(f"\n{'Code':<12} {'Project':<40} {'Emails':<8} {'Last Contact':<20} {'Most Recent Email'}")
    print(f"{'-'*12} {'-'*40} {'-'*8} {'-'*20} {'-'*20}")

    for proj in projects:
        days = proj['days_since_contact'] if proj['days_since_contact'] else 999
        last = proj['last_contact_date'] or 'Never'
        recent = proj['most_recent_email'] or 'None'

        print(f"{proj['project_code']:<12} {proj['project_name'][:40]:<40} "
              f"{proj['email_count']:<8} {str(days) + ' days':<20} {recent}")

    conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "watch":
            watch_recent_updates()
        elif sys.argv[1] == "links":
            show_recent_linkages()
        elif sys.argv[1] == "contacts":
            show_projects_with_last_contact()
        else:
            print("Usage: python monitor_ai_processing.py [watch|links|contacts]")
    else:
        print("🔍 AI Processing Monitor\n")
        print("Options:")
        print("  python monitor_ai_processing.py watch     - Watch real-time updates")
        print("  python monitor_ai_processing.py links     - Show recent email-project linkages")
        print("  python monitor_ai_processing.py contacts  - Show projects with last contact dates")
