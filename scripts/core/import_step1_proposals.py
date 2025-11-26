#!/usr/bin/env python3
"""
STEP 1: Import Proposal Overview to proposals table
This preserves ALL proposals for analytics (win rates, pipeline stats, etc.)
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

# Paths
WORKING_DIR = Path("/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System")
DB_PATH = WORKING_DIR / "database" / "bensley_master.db"
PROPOSAL_EXCEL = Path("/Users/lukassherman/Desktop/bensley proposal overview November 25th.xlsx")


def import_proposal_overview():
    """Import proposal dashboard sheet to proposals table"""
    print("\n" + "="*80)
    print("STEP 1: IMPORT PROPOSAL OVERVIEW TO PROPOSALS TABLE")
    print("="*80)

    # Read the Proposal dashboard sheet (header at row 6)
    print(f"\n📖 Reading: {PROPOSAL_EXCEL}")
    df = pd.read_excel(PROPOSAL_EXCEL, sheet_name="Proposal dashboard ", header=5)  # Note: sheet name has trailing space

    print(f"Loaded {len(df)} proposals")
    print(f"\nColumns: {list(df.columns)}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    imported = 0
    updated = 0
    skipped = 0
    errors = 0

    for idx, row in df.iterrows():
        try:
            # Get project code (required)
            project_code = row.get('Project #')
            if pd.isna(project_code):
                skipped += 1
                continue

            project_code = str(project_code).strip()

            # Parse signed date
            signed_date = row.get('Date of contract signed ')
            if pd.notna(signed_date) and signed_date != '':
                try:
                    if isinstance(signed_date, str):
                        signed_date = pd.to_datetime(signed_date).strftime('%Y-%m-%d')
                    else:
                        signed_date = signed_date.strftime('%Y-%m-%d')
                except:
                    signed_date = None
            else:
                signed_date = None

            # Determine status
            current_status = str(row.get('Current status ', '')).lower()
            if 'signed' in current_status or 'contract' in current_status:
                status = 'won'
            elif 'lost' in current_status or 'cancelled' in current_status:
                status = 'lost'
            else:
                status = 'proposal'

            # Parse disciplines (L, A, I columns)
            landscape = 1 if str(row.get('L', '')).strip().upper() == 'L' else 0
            architecture = 1 if str(row.get('A', '')).strip().upper() == 'A' else 0
            interior = 1 if str(row.get('I', '')).strip().upper() == 'I' else 0

            # Project value
            project_value = row.get('Project Value')
            if pd.isna(project_value):
                project_value = None
            else:
                try:
                    project_value = float(project_value)
                except:
                    project_value = None

            # Check if exists
            cursor.execute("SELECT proposal_id FROM proposals WHERE project_code = ?", (project_code,))
            existing = cursor.fetchone()

            if existing:
                # Update existing
                cursor.execute("""
                    UPDATE proposals
                    SET project_name = ?,
                        project_value = ?,
                        status = ?,
                        contract_signed_date = ?,
                        is_landscape = ?,
                        is_architect = ?,
                        is_interior = ?,
                        location = ?,
                        updated_at = datetime('now')
                    WHERE project_code = ?
                """, (
                    row.get('Project Name '),
                    project_value,
                    status,
                    signed_date,
                    landscape,
                    architecture,
                    interior,
                    row.get('Country'),
                    project_code
                ))
                updated += 1
                print(f"  ✅ Updated: {project_code} - {row.get('Project Name ')}")
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO proposals (
                        project_code,
                        project_name,
                        project_value,
                        status,
                        contract_signed_date,
                        is_landscape,
                        is_architect,
                        is_interior,
                        location,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    project_code,
                    row.get('Project Name '),
                    project_value,
                    status,
                    signed_date,
                    landscape,
                    architecture,
                    interior,
                    row.get('Country')
                ))
                imported += 1
                print(f"  ✅ Imported: {project_code} - {row.get('Project Name ')}")

        except Exception as e:
            errors += 1
            print(f"  ❌ Error at row {idx}: {e}")
            continue

    conn.commit()
    conn.close()

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"  ✅ Imported: {imported}")
    print(f"  🔄 Updated: {updated}")
    print(f"  ⏭️  Skipped: {skipped}")
    print(f"  ❌ Errors: {errors}")
    print(f"  📊 Total processed: {imported + updated}")


def main():
    print("\n" + "="*80)
    print("IMPORT PROPOSALS TO DATABASE")
    print("="*80)
    print(f"\nSource: {PROPOSAL_EXCEL}")
    print(f"Database: {DB_PATH}")
    print("\nThis imports ALL proposals for analytics tracking.")
    print("Signed proposals stay in this table for conversion metrics.")

    response = input("\nProceed with import? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return

    import_proposal_overview()

    print("\n✅ STEP 1 COMPLETE - Proposals imported")
    print("Next: Run import_step2_fee_breakdown.py")


if __name__ == "__main__":
    main()
