#!/usr/bin/env python3
"""
Comprehensive Data Import from Multiple Sources
1. Proposal Overview Excel (Desktop) - shows which contracts are signed
2. Contract PDFs in OneDrive (Proposal 2025 Nung folder) - payment terms, scope
3. MASTER_CONTRACT_FEE_BREAKDOWN Excel (Desktop) - invoice/fee data
"""

import sqlite3
import pandas as pd
from pathlib import Path
import re
from datetime import datetime
import anthropic
import os
import json

# Paths
WORKING_DIR = Path("/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System")
DB_PATH = WORKING_DIR / "database" / "bensley_master.db"
PROPOSAL_OVERVIEW_EXCEL = Path("/Users/lukassherman/Desktop/bensley proposal overview November 25th.xlsx")
FEE_BREAKDOWN_EXCEL = Path("/Users/lukassherman/Desktop/MASTER_CONTRACT_FEE_BREAKDOWN.xlsx")
CONTRACTS_FOLDER = Path("/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Proposal 2025 (Nung)")

# Claude API
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def read_proposal_overview():
    """Read the proposal overview Excel file"""
    print("\n" + "="*80)
    print("STEP 1: Reading Proposal Overview Excel")
    print("="*80)

    df = pd.read_excel(PROPOSAL_OVERVIEW_EXCEL)
    print(f"\nLoaded {len(df)} proposals from overview")
    print(f"\nColumns: {list(df.columns)}")

    # Show first few rows
    print(f"\nFirst 5 rows:")
    print(df.head().to_string())

    # Find proposals marked as "contract signed"
    # Look for status column (might be 'Status', 'Contract Status', etc.)
    status_cols = [col for col in df.columns if 'status' in col.lower()]
    print(f"\nStatus columns found: {status_cols}")

    return df


def find_matching_contract(project_code, contracts_folder):
    """Find contract PDF matching project code"""
    project_code_clean = project_code.replace("-", "").replace(" ", "").upper()

    for pdf_file in contracts_folder.rglob("*.pdf"):
        filename = pdf_file.stem.replace("-", "").replace(" ", "").upper()
        if project_code_clean in filename or any(part in filename for part in project_code.split("-")):
            return pdf_file

    return None


def extract_contract_data_with_claude(contract_pdf_path):
    """Extract payment terms and scope from contract PDF using Claude"""
    print(f"\n  📄 Extracting data from: {contract_pdf_path.name}")

    try:
        # Read PDF content (simplified - you may want to use PyPDF2 or similar)
        # For now, we'll use Claude's PDF reading capability

        with open(contract_pdf_path, 'rb') as f:
            pdf_data = f.read()

        # Use Claude to extract structured data
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data.decode('latin-1') if isinstance(pdf_data, bytes) else pdf_data
                        }
                    },
                    {
                        "type": "text",
                        "text": """Extract the following from this contract:

1. Project Code (e.g., 25-BK-XXX)
2. Project Name/Title
3. Total Contract Value (USD)
4. Payment Terms (e.g., "30% deposit, 40% midpoint, 30% completion")
5. Scope of Work breakdown by discipline (Landscape/Architecture/Interior)
6. Phase breakdown (e.g., Concept, DD, CD, CA)
7. Payment schedule/milestones
8. Contract signed date
9. Any fee breakdown by phase

Return as JSON with these exact keys:
{
  "project_code": "",
  "project_name": "",
  "total_value_usd": 0,
  "payment_terms": "",
  "disciplines": {"landscape": false, "architecture": false, "interior": false},
  "phases": [],
  "contract_date": "",
  "fee_breakdown": [
    {"discipline": "", "phase": "", "fee_usd": 0, "percentage": 0}
  ]
}
"""
                    }
                ]
            }]
        )

        # Parse Claude's response
        response_text = message.content[0].text

        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            print(f"  ✅ Extracted: {data.get('project_name', 'Unknown')}")
            return data
        else:
            print(f"  ⚠️  Could not parse JSON from response")
            return None

    except Exception as e:
        print(f"  ❌ Error extracting contract data: {e}")
        return None


def read_fee_breakdown_excel():
    """Read the MASTER_CONTRACT_FEE_BREAKDOWN Excel"""
    print("\n" + "="*80)
    print("STEP 2: Reading Fee Breakdown Excel")
    print("="*80)

    try:
        # Try reading all sheets
        xls = pd.ExcelFile(FEE_BREAKDOWN_EXCEL)
        print(f"\nSheets found: {xls.sheet_names}")

        # Read first sheet
        df = pd.read_excel(FEE_BREAKDOWN_EXCEL, sheet_name=0)
        print(f"\nLoaded {len(df)} records")
        print(f"\nColumns: {list(df.columns)}")
        print(f"\nFirst 5 rows:")
        print(df.head().to_string())

        return df
    except Exception as e:
        print(f"❌ Error reading fee breakdown: {e}")
        return None


def import_proposal_data_to_db(proposal_df):
    """Import proposal overview data to database"""
    print("\n" + "="*80)
    print("STEP 3: Importing Proposal Overview to Database")
    print("="*80)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    imported = 0
    updated = 0
    errors = 0

    for idx, row in proposal_df.iterrows():
        try:
            # Extract project code (adjust column name as needed)
            project_code = row.get('Project Code') or row.get('Code') or row.get('project_code')
            if pd.isna(project_code):
                continue

            project_code = str(project_code).strip()

            # Check if already exists
            cursor.execute("SELECT id FROM proposal_tracker WHERE project_code = ?", (project_code,))
            existing = cursor.fetchone()

            # Extract all available fields
            updates = {
                'project_name': row.get('Project Name') or row.get('Name'),
                'project_value': row.get('Value (USD)') or row.get('Project Value'),
                'current_status': row.get('Status') or row.get('Current Status'),
                'country': row.get('Country'),
                'current_remark': row.get('Remarks') or row.get('Notes'),
                'proposal_sent_date': row.get('Proposal Sent') or row.get('Date Sent'),
                'first_contact_date': row.get('First Contact'),
                'waiting_on': row.get('Waiting On'),
                'next_steps': row.get('Next Steps'),
                'updated_by': 'excel_import',
                'source_type': 'proposal_overview_excel'
            }

            # Remove None values
            updates = {k: v for k, v in updates.items() if not pd.isna(v)}

            if existing:
                # Update existing
                set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
                values = list(updates.values()) + [project_code]
                cursor.execute(f"""
                    UPDATE proposal_tracker
                    SET {set_clause}, updated_at = datetime('now')
                    WHERE project_code = ?
                """, values)
                updated += 1
                print(f"  ✅ Updated: {project_code}")
            else:
                # Insert new
                updates['project_code'] = project_code
                columns = ', '.join(updates.keys())
                placeholders = ', '.join(['?' for _ in updates])
                cursor.execute(f"""
                    INSERT INTO proposal_tracker ({columns}, created_at)
                    VALUES ({placeholders}, datetime('now'))
                """, list(updates.values()))
                imported += 1
                print(f"  ✅ Imported: {project_code}")

        except Exception as e:
            errors += 1
            print(f"  ❌ Error processing row {idx}: {e}")
            continue

    conn.commit()
    conn.close()

    print(f"\n📊 Summary:")
    print(f"   Imported: {imported}")
    print(f"   Updated: {updated}")
    print(f"   Errors: {errors}")


def import_fee_breakdown_to_db(fee_df):
    """Import fee breakdown data to database"""
    print("\n" + "="*80)
    print("STEP 4: Importing Fee Breakdown to Database")
    print("="*80)

    if fee_df is None:
        print("⚠️  No fee breakdown data to import")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    imported = 0
    errors = 0

    for idx, row in fee_df.iterrows():
        try:
            project_code = row.get('Project Code') or row.get('Code') or row.get('project_code')
            if pd.isna(project_code):
                continue

            project_code = str(project_code).strip()

            # Insert/update fee breakdown
            cursor.execute("""
                INSERT OR REPLACE INTO project_fee_breakdown (
                    project_code,
                    discipline,
                    phase,
                    phase_fee_usd,
                    percentage_of_total,
                    total_invoiced,
                    total_paid,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                project_code,
                row.get('Discipline'),
                row.get('Phase'),
                row.get('Fee (USD)') or row.get('Amount'),
                row.get('Percentage') or row.get('%'),
                row.get('Invoiced') or 0,
                row.get('Paid') or 0
            ))

            imported += 1
            if imported % 10 == 0:
                print(f"  Imported {imported} fee records...")

        except Exception as e:
            errors += 1
            print(f"  ❌ Error at row {idx}: {e}")
            continue

    conn.commit()
    conn.close()

    print(f"\n📊 Summary:")
    print(f"   Imported: {imported}")
    print(f"   Errors: {errors}")


def process_contracts_for_signed_proposals(proposal_df):
    """Find and process contracts for proposals marked as signed"""
    print("\n" + "="*80)
    print("STEP 5: Processing Contract PDFs for Signed Proposals")
    print("="*80)

    # Find signed contracts (adjust column name as needed)
    status_col = None
    for col in proposal_df.columns:
        if 'status' in col.lower():
            status_col = col
            break

    if status_col is None:
        print("⚠️  Could not find status column")
        return

    signed_proposals = proposal_df[
        proposal_df[status_col].str.contains('signed|contract', case=False, na=False)
    ]

    print(f"\nFound {len(signed_proposals)} proposals marked as signed")

    processed = 0
    for idx, row in signed_proposals.iterrows():
        project_code = row.get('Project Code') or row.get('Code')
        if pd.isna(project_code):
            continue

        project_code = str(project_code).strip()
        print(f"\n🔍 Looking for contract: {project_code}")

        # Find matching contract PDF
        contract_path = find_matching_contract(project_code, CONTRACTS_FOLDER)

        if contract_path:
            print(f"  ✅ Found contract: {contract_path.name}")

            # Extract data using Claude
            contract_data = extract_contract_data_with_claude(contract_path)

            if contract_data:
                # Import to database
                # (You would add database insert logic here)
                processed += 1
        else:
            print(f"  ⚠️  No contract PDF found for {project_code}")

    print(f"\n📊 Processed {processed} contracts")


def main():
    """Main import process"""
    print("\n" + "="*80)
    print("COMPREHENSIVE DATA IMPORT")
    print("="*80)
    print(f"\nSources:")
    print(f"  1. {PROPOSAL_OVERVIEW_EXCEL}")
    print(f"  2. {FEE_BREAKDOWN_EXCEL}")
    print(f"  3. {CONTRACTS_FOLDER}")
    print(f"\nDatabase: {DB_PATH}")

    # Step 1: Read proposal overview
    proposal_df = read_proposal_overview()

    # Step 2: Read fee breakdown
    fee_df = read_fee_breakdown_excel()

    # Step 3: Import proposal data
    if proposal_df is not None:
        import_proposal_data_to_db(proposal_df)

    # Step 4: Import fee breakdown
    if fee_df is not None:
        import_fee_breakdown_to_db(fee_df)

    # Step 5: Process contracts (optional - can be slow)
    print("\n" + "="*80)
    print("CONTRACT PDF PROCESSING")
    print("="*80)
    response = input("\nProcess contract PDFs? This will use Claude API and may take time (y/n): ")
    if response.lower() == 'y':
        process_contracts_for_signed_proposals(proposal_df)

    print("\n" + "="*80)
    print("✅ IMPORT COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
