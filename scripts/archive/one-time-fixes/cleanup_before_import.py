#!/usr/bin/env python3
"""
CLEANUP SCRIPT - Run BEFORE importing
Deletes data from Excel sources to prevent duplicates
"""

import sqlite3
from pathlib import Path

WORKING_DIR = Path("/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System")
DB_PATH = WORKING_DIR / "database" / "bensley_master.db"


def cleanup_database():
    """Clean up imported data before re-importing"""
    print("\n" + "="*80)
    print("DATABASE CLEANUP - BEFORE IMPORT")
    print("="*80)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check current counts
    cursor.execute("SELECT COUNT(*) FROM proposals")
    proposals_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM project_fee_breakdown")
    fee_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM invoices")
    invoices_count = cursor.fetchone()[0]

    print(f"\n📊 Current Database State:")
    print(f"   Proposals: {proposals_count}")
    print(f"   Fee Breakdown: {fee_count}")
    print(f"   Invoices: {invoices_count}")

    print("\n⚠️  WARNING: This will DELETE:")
    print("   • ALL proposals")
    print("   • ALL fee breakdown records")
    print("   • ALL invoices")
    print("\nWe will re-import clean data from Excel sources.")

    response = input("\n❗ Delete ALL data and start fresh? (yes/no): ")
    if response.lower() != 'yes':
        print("\nAborted. No changes made.")
        return False

    print("\n🗑️  Deleting data...")

    # Delete in reverse order of dependencies
    cursor.execute("DELETE FROM invoices")
    deleted_invoices = cursor.rowcount
    print(f"   ✅ Deleted {deleted_invoices} invoices")

    cursor.execute("DELETE FROM project_fee_breakdown")
    deleted_fees = cursor.rowcount
    print(f"   ✅ Deleted {deleted_fees} fee breakdown records")

    cursor.execute("DELETE FROM proposals")
    deleted_proposals = cursor.rowcount
    print(f"   ✅ Deleted {deleted_proposals} proposals")

    conn.commit()
    conn.close()

    print("\n✅ Database cleaned successfully!")
    print("   Ready for fresh import.")

    return True


def main():
    print("\n" + "="*80)
    print("CLEANUP BEFORE IMPORT")
    print("="*80)
    print(f"\nDatabase: {DB_PATH}")

    success = cleanup_database()

    if success:
        print("\n" + "="*80)
        print("NEXT STEPS")
        print("="*80)
        print("\nRun import scripts in order:")
        print("  1. python3 import_step1_proposals.py")
        print("  2. python3 import_step2_fee_breakdown.py")
        print("  3. python3 import_step3_contracts.py")
        print("\nOr run all at once:")
        print("  python3 import_all_data.py")


if __name__ == "__main__":
    main()
