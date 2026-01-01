#!/usr/bin/env python3
"""
Simple project data comparison - just show everything
"""
import sqlite3
import sys
import json

DESKTOP_DB = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
ONEDRIVE_DB = "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/bensley_master.db"

def show_project_data(project_search):
    """Show all data for a project from both databases"""

    print("="*100)
    print(f"PROJECT DATA COMPARISON: {project_search}")
    print("="*100)

    for db_name, db_path in [("DESKTOP", DESKTOP_DB), ("ONEDRIVE", ONEDRIVE_DB)]:
        print(f"\n{'='*100}")
        print(f"{db_name} DATABASE")
        print("="*100)

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get all proposals matching search
            cursor.execute("SELECT * FROM proposals")
            all_proposals = cursor.fetchall()

            matching_projects = []
            for p in all_proposals:
                p_dict = dict(p)
                # Search in any text field
                match = False
                for key, value in p_dict.items():
                    if value and isinstance(value, str) and project_search.lower() in value.lower():
                        match = True
                        break
                if match:
                    matching_projects.append(p_dict)

            if not matching_projects:
                print(f"❌ No project found matching '{project_search}'")
                conn.close()
                continue

            for proj in matching_projects:
                print(f"\n{'─'*100}")
                print("📋 PROPOSAL/PROJECT DATA:")
                print(f"{'─'*100}")
                for key, value in proj.items():
                    if value is not None:
                        print(f"   {key}: {value}")

                # Try to find project code
                project_code = proj.get('project_code') or proj.get('code')

                if not project_code:
                    print("\n⚠️  No project code found, skipping invoice/payment lookup")
                    continue

                # Get invoices
                print(f"\n{'─'*100}")
                print(f"💰 INVOICES for {project_code}:")
                print(f"{'─'*100}")
                cursor.execute(f"SELECT * FROM invoices WHERE project_code = ?", (project_code,))
                invoices = cursor.fetchall()

                if invoices:
                    for idx, inv in enumerate(invoices, 1):
                        print(f"\n   Invoice #{idx}:")
                        inv_dict = dict(inv)
                        for key, value in inv_dict.items():
                            if value is not None:
                                print(f"      {key}: {value}")
                else:
                    print("   No invoices found")

                # Check for payment terms table
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contract_payment_terms'")
                if cursor.fetchone():
                    print(f"\n{'─'*100}")
                    print(f"📅 PAYMENT TERMS for {project_code}:")
                    print(f"{'─'*100}")
                    cursor.execute(f"SELECT * FROM contract_payment_terms WHERE project_code = ?", (project_code,))
                    terms = cursor.fetchall()

                    if terms:
                        for idx, term in enumerate(terms, 1):
                            print(f"\n   Payment #{idx}:")
                            term_dict = dict(term)
                            for key, value in term_dict.items():
                                if value is not None:
                                    print(f"      {key}: {value}")
                    else:
                        print("   No payment terms found")

                # Check for fee breakdown table
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_fee_breakdown'")
                if cursor.fetchone():
                    print(f"\n{'─'*100}")
                    print(f"💵 FEE BREAKDOWN for {project_code}:")
                    print(f"{'─'*100}")
                    cursor.execute(f"SELECT * FROM project_fee_breakdown WHERE project_code = ?", (project_code,))
                    fees = cursor.fetchall()

                    if fees:
                        for idx, fee in enumerate(fees, 1):
                            print(f"\n   Phase #{idx}:")
                            fee_dict = dict(fee)
                            for key, value in fee_dict.items():
                                if value is not None:
                                    print(f"      {key}: {value}")
                    else:
                        print("   No fee breakdown found")

                # Get linked emails count
                cursor.execute(f"""
                    SELECT COUNT(*) as count
                    FROM email_proposal_links
                    WHERE proposal_id = ?
                """, (proj.get('proposal_id') or proj.get('id'),))
                email_count = cursor.fetchone()
                if email_count:
                    print(f"\n{'─'*100}")
                    print(f"📧 LINKED EMAILS: {email_count['count']}")

            conn.close()

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        search = ' '.join(sys.argv[1:])
    else:
        search = input("Enter project name/code to search: ").strip()

    if not search:
        print("❌ No search term provided")
        sys.exit(1)

    show_project_data(search)
