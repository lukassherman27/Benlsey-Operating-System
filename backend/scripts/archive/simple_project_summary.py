#!/usr/bin/env python3
"""
Simple Project Summary - Just the basics
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.expanduser("~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db")
OUTPUT_PATH = os.path.expanduser("~/Desktop/BENSLEY_PROJECTS_SUMMARY.txt")

def generate_summary():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write("=" * 120 + "\n")
        f.write("BENSLEY PROJECTS SUMMARY\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 120 + "\n\n")

        # Get count from both tables
        cursor.execute("SELECT COUNT(*) as count FROM proposals")
        proposals_table_count = cursor.fetchone()['count']

        cursor.execute("SELECT COUNT(*) as count FROM projects")
        projects_table_count = cursor.fetchone()['count']

        f.write(f"TOTAL IN DATABASE:\n")
        f.write(f"  Proposals Table: {proposals_table_count}\n")
        f.write(f"  Projects Table: {projects_table_count}\n\n")

        # Get all from PROPOSALS table with email counts
        cursor.execute("""
            SELECT
                p.project_code,
                p.project_title as project_name,
                NULL as client_company,
                p.status,
                0 as is_active_project,
                NULL as health_score,
                p.total_fee_usd as project_value,
                NULL as last_contact_date,
                NULL as days_since_contact,
                COUNT(DISTINCT epl.email_id) as email_count,
                COUNT(DISTINCT dpl.document_id) as document_count,
                'proposals' as source_table
            FROM proposals p
            LEFT JOIN email_proposal_links epl ON p.project_id = epl.proposal_id
            LEFT JOIN document_proposal_links dpl ON p.project_id = dpl.proposal_id
            GROUP BY p.project_code

            UNION ALL

            SELECT
                p.project_code,
                p.project_name,
                p.client_company,
                p.status,
                p.is_active_project,
                p.health_score,
                p.project_value,
                p.last_contact_date,
                p.days_since_contact,
                COUNT(DISTINCT e.email_id) as email_count,
                COUNT(DISTINCT d.document_id) as document_count,
                'projects' as source_table
            FROM projects p
            LEFT JOIN email_project_links epl ON p.project_code = epl.project_code
            LEFT JOIN emails e ON epl.email_id = e.email_id
            LEFT JOIN project_documents pd ON p.proposal_id = pd.project_id
            LEFT JOIN documents d ON pd.document_id = d.document_id
            GROUP BY p.project_code

            ORDER BY source_table DESC, is_active_project DESC, project_code
        """)

        all_records = cursor.fetchall()

        f.write(f"TOTAL RECORDS: {len(all_records)}\n\n")

        f.write("=" * 120 + "\n\n")

        # Header
        f.write(f"{'CODE':<15} {'PROJECT NAME':<40} {'SOURCE':<12} {'TYPE':<15} {'STATUS':<15} {'EMAILS':<8} {'DOCS':<6} {'HEALTH':<8} {'LAST CONTACT'}\n")
        f.write("-" * 120 + "\n")

        # List all records
        for p in all_records:
            code = (p['project_code'] or '')[:14]
            name = (p['project_name'] or 'Untitled')[:39]
            source = p['source_table'][:11]
            proj_type = 'ACTIVE' if p['is_active_project'] == 1 else 'PROPOSAL'
            status = (p['status'] or 'unknown')[:14]
            emails = p['email_count']
            docs = p['document_count']
            health = f"{p['health_score']:.0f}%" if p['health_score'] else 'N/A'
            last_contact = p['last_contact_date'] or 'Never'

            f.write(f"{code:<15} {name:<40} {source:<12} {proj_type:<15} {status:<15} {emails:<8} {docs:<6} {health:<8} {last_contact}\n")

        f.write("\n" + "=" * 120 + "\n")
        f.write("SUMMARY BY SOURCE & STATUS\n")
        f.write("=" * 120 + "\n\n")

        # Proposals table breakdown
        cursor.execute("""
            SELECT
                status,
                COUNT(*) as count,
                SUM(total_fee_usd) as total_value
            FROM proposals
            GROUP BY status
            ORDER BY count DESC
        """)

        f.write("PROPOSALS TABLE:\n")
        for row in cursor.fetchall():
            status = row['status'] or 'unknown'
            count = row['count']
            total_value = row['total_value'] or 0
            f.write(f"  {status.upper()}: {count} (Total Value: ${total_value:,.0f})\n")

        f.write("\n")

        # Projects table breakdown
        cursor.execute("""
            SELECT
                CASE WHEN is_active_project = 1 THEN 'ACTIVE PROJECT' ELSE 'PROPOSAL' END as type,
                status,
                COUNT(*) as count,
                AVG(health_score) as avg_health,
                SUM(project_value) as total_value
            FROM projects
            GROUP BY type, status
            ORDER BY type DESC, count DESC
        """)

        f.write("PROJECTS TABLE:\n")
        for row in cursor.fetchall():
            proj_type = row['type']
            status = row['status'] or 'unknown'
            count = row['count']
            avg_health = row['avg_health'] or 0
            total_value = row['total_value'] or 0
            f.write(f"  {proj_type} - {status.upper()}: {count} (Avg Health: {avg_health:.1f}%, Total Value: ${total_value:,.0f})\n")

    conn.close()
    print(f"\n✅ Summary saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    generate_summary()
