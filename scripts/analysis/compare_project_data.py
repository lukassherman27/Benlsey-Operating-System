#!/usr/bin/env python3
"""
Compare project data between Desktop and OneDrive databases
"""
import sqlite3
import sys
from datetime import datetime

DESKTOP_DB = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
ONEDRIVE_DB = "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/bensley_master.db"

def format_currency(value):
    if value is None:
        return "N/A"
    return f"${value:,.2f}"

def compare_project(project_search):
    """Compare a specific project across both databases"""

    print("="*100)
    print(f"COMPARING PROJECT: {project_search}")
    print("="*100)

    for db_name, db_path in [("DESKTOP", DESKTOP_DB), ("ONEDRIVE", ONEDRIVE_DB)]:
        print(f"\n{'='*100}")
        print(f"{db_name} DATABASE")
        print("="*100)

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Find the project - handle different schemas
            # First check what columns exist
            cursor.execute("PRAGMA table_info(proposals)")
            columns = {col[1] for col in cursor.fetchall()}

            # Build query based on available columns
            search_conditions = []
            search_params = []

            if 'project_name' in columns:
                search_conditions.append("project_name LIKE ?")
                search_params.append(f"%{project_search}%")
            if 'project_code' in columns:
                search_conditions.append("project_code LIKE ?")
                search_params.append(f"%{project_search}%")
            if 'client_company' in columns:
                search_conditions.append("client_company LIKE ?")
                search_params.append(f"%{project_search}%")
            if 'name' in columns:
                search_conditions.append("name LIKE ?")
                search_params.append(f"%{project_search}%")
            if 'code' in columns:
                search_conditions.append("code LIKE ?")
                search_params.append(f"%{project_search}%")

            if not search_conditions:
                print(f"❌ Can't search - no searchable columns in proposals table")
                conn.close()
                continue

            query = f"SELECT * FROM proposals WHERE {' OR '.join(search_conditions)} ORDER BY proposal_id"
            cursor.execute(query, tuple(search_params))

            projects = cursor.fetchall()

            if not projects:
                print(f"❌ No project found matching '{project_search}'")
                conn.close()
                continue

            for project in projects:
                # Convert to dict to handle different schemas
                project_dict = dict(project)

                print(f"\n📋 PROJECT DETAILS")
                print(f"   Code: {project_dict.get('project_code') or project_dict.get('code', 'N/A')}")
                print(f"   Name: {project_dict.get('project_name') or project_dict.get('name', 'N/A')}")
                print(f"   Client: {project_dict.get('client_company') or project_dict.get('client', 'N/A')}")
                print(f"   Contact: {project_dict.get('contact_person') or project_dict.get('contact', 'N/A')}")
                print(f"   Status: {project_dict.get('status', 'N/A')}")

                project_id = project_dict.get('proposal_id') or project_dict.get('id')
                project_code = project_dict.get('project_code') or project_dict.get('code')

                # Get invoices
                print(f"\n💰 INVOICES")
                cursor.execute("""
                    SELECT invoice_number, invoice_date, amount, currency, status, payment_received_date
                    FROM invoices
                    WHERE project_code = ?
                    ORDER BY invoice_date
                """, (project_code,))

                invoices = cursor.fetchall()
                if invoices:
                    print(f"   Found {len(invoices)} invoices:")
                    for inv in invoices:
                        amt = format_currency(inv['amount']) if inv['currency'] == 'USD' else f"{inv['amount']} {inv['currency']}"
                        print(f"   • {inv['invoice_number']}: {amt} | Date: {inv['invoice_date']} | Paid: {inv['payment_received_date'] or 'Not paid'} | Status: {inv['status']}")
                else:
                    print(f"   ⚠️  No invoices found")

                # Get fee breakdown (if table exists)
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_fee_breakdown'")
                if cursor.fetchone():
                    cursor.execute("""
                        SELECT phase_name, fee_amount, currency, payment_terms
                        FROM project_fee_breakdown
                        WHERE project_code = ?
                        ORDER BY phase_name
                    """, (project_code,))

                    fees = cursor.fetchall()
                    if fees:
                        print(f"\n💵 PHASE FEE BREAKDOWN")
                        print(f"   Found {len(fees)} phases:")
                        total = 0
                        for fee in fees:
                            amt = fee['fee_amount'] or 0
                            total += amt
                            print(f"   • {fee['phase_name']}: {format_currency(amt)} | Terms: {fee['payment_terms'] or 'N/A'}")
                        print(f"   TOTAL: {format_currency(total)}")
                    else:
                        print(f"\n💵 PHASE FEE BREAKDOWN")
                        print(f"   ⚠️  No fee breakdown found")
                else:
                    print(f"\n💵 PHASE FEE BREAKDOWN")
                    print(f"   ⚠️  Table doesn't exist in this database")

                # Get contract info
                cursor.execute("""
                    SELECT contract_signed_date, contract_value, contract_currency
                    FROM proposals
                    WHERE proposal_id = ?
                """, (project_id,))

                contract = cursor.fetchone()
                if contract:
                    print(f"\n📝 CONTRACT")
                    print(f"   Signed: {contract['contract_signed_date'] or 'Not signed'}")
                    if contract['contract_value']:
                        print(f"   Value: {format_currency(contract['contract_value'])}")

                # Get payment terms (if table exists)
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contract_payment_terms'")
                if cursor.fetchone():
                    cursor.execute("""
                        SELECT payment_stage, percentage, due_date, amount_due, payment_received
                        FROM contract_payment_terms
                        WHERE project_code = ?
                        ORDER BY payment_stage
                    """, (project_code,))

                    terms = cursor.fetchall()
                    if terms:
                        print(f"\n📅 PAYMENT SCHEDULE")
                        print(f"   Found {len(terms)} payment stages:")
                        for term in terms:
                            status = "✅ Paid" if term['payment_received'] else "⏳ Pending"
                            print(f"   • {term['payment_stage']}: {term['percentage']}% ({format_currency(term['amount_due'])}) | Due: {term['due_date']} | {status}")
                    else:
                        print(f"\n📅 PAYMENT SCHEDULE")
                        print(f"   ⚠️  No payment schedule found")
                else:
                    print(f"\n📅 PAYMENT SCHEDULE")
                    print(f"   ⚠️  Table doesn't exist in this database")

                # Get related emails count
                cursor.execute("""
                    SELECT COUNT(*) as email_count
                    FROM email_proposal_links
                    WHERE proposal_id = ?
                """, (project_id,))

                email_count = cursor.fetchone()['email_count']
                print(f"\n📧 LINKED EMAILS: {email_count}")

            conn.close()

        except Exception as e:
            print(f"❌ Error accessing {db_name} database: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        search = ' '.join(sys.argv[1:])
    else:
        search = input("Enter project name/code to search: ").strip()

    if not search:
        print("❌ No search term provided")
        sys.exit(1)

    compare_project(search)
