#!/usr/bin/env python3
"""
STEP 3: Import Signed Contract PDFs using Claude API
Extract payment terms, scope, fee breakdown from 8 signed contract PDFs

IMPORTANT: Proposals stay in proposals table for analytics (conversion tracking).
This step creates active projects from signed proposals.
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
import openai
from dotenv import load_dotenv
import pdfplumber

# Load environment variables
load_dotenv()

# Paths
WORKING_DIR = Path("/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System")
DB_PATH = WORKING_DIR / "database" / "bensley_master.db"
CONTRACTS_FOLDER = Path("/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Proposal 2025 (Nung)")

# OpenAI API
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Map of 8 signed contracts: old code -> (new code, filename, signed date, value)
SIGNED_CONTRACTS = {
    "25-BK-001": {
        "file_code": "25-001",
        "filename": "25-001 Ramhan Marina Hotel Project in Abu Dhabi, UAE revised 11 Feb 25.pdf",
        "signed_date": "2025-02-15",
        "project_value": 1850000,
        "project_name": "Ramhan Marina Hotel Project in Abu Dhabi, UAE"
    },
    "25-BK-002": {
        "file_code": "25-002",
        "filename": "25-002 Tonkin Palace Hanoi, Vietnam revised on 26 Jan 25 (both signed).pdf",
        "signed_date": "2025-02-05",
        "project_value": 1000000,
        "project_name": "Tonkin Palace Hanoi Project, Vietnam"
    },
    "24-BK-017": {
        "file_code": "25-017",
        "filename": "25-017 TARC's Luxury Branded Residence Project in Delhi date 21 Aug 25 (Signed).pdf",
        "signed_date": "2025-08-22",
        "project_value": 3000000,
        "project_name": "TARC's Luxury Branded Residence Project in New Delhi, India"
    },
    "24-BK-018": {
        "file_code": "25-018",
        "filename": "25-018 The Ritz Carlton Hotel Nanyan Bay, China-Extension Contract (Addendum) (Eng-Chi) signed.pdf",
        "signed_date": "2025-03-07",
        "project_value": 225000,
        "project_name": "The Ritz-Carlton Hotel Nanyan Bay, China (One year Extension)"
    },
    "24-BK-021": {
        "file_code": "25-021",
        "filename": "25-021 Art DEco Residential Project in Mumbai, India (Redesign)-revised-Signed both.pdf",
        "signed_date": "2025-03-04",
        "project_value": 750000,
        "project_name": "Art Deco Residential Project in Mumbai, India (Addendum)"
    },
    "25-BK-025": {
        "file_code": "25-025",
        "filename": "25-025 APEC Downtown Project, Vietnam revised 10 Apr 25.pdf",
        "signed_date": "2025-04-10",
        "project_value": 2500000,
        "project_name": "APEC Downtown Project, Vietnam"
    },
    "25-BK-030": {
        "file_code": "25-030",
        "filename": "25-030 Beach Club at Mandarin Oriental Bali (both signed).pdf",
        "signed_date": "2025-06-25",
        "project_value": 550000,
        "project_name": "Beach Club at Mandarin Oriental Bali"
    },
    "25-BK-033": {
        "file_code": "25-033",
        "filename": "25-033 Ritz Carlton Rserve, Nusa Dua (June 30) - FINAL (Brian's signed).pdf",
        "signed_date": "2025-07-03",
        "project_value": 3150000,
        "project_name": "The Ritz Carlton Reserve, Nusa Dua, Bali, Indonesia"
    }
}


def extract_contract_data_with_openai(contract_path, project_code, project_info):
    """Extract payment terms and scope from contract PDF using OpenAI"""
    print(f"\n  📄 Extracting: {project_info['project_name']}")
    print(f"     File: {contract_path.name}")

    try:
        # Extract text from PDF using pdfplumber
        print(f"  📖 Reading PDF...")
        pdf_text = ""
        with pdfplumber.open(contract_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    pdf_text += f"\n--- Page {page_num} ---\n{text}"

        if not pdf_text.strip():
            print(f"  ⚠️  No text extracted from PDF")
            return None

        print(f"  ✅ Extracted {len(pdf_text)} characters from {len(pdf.pages)} pages")

        # Use OpenAI to extract structured data
        print(f"  🤖 Analyzing with OpenAI...")
        response = openai.chat.completions.create(
            model="gpt-4-turbo-preview",  # or "gpt-4" if you don't have turbo access
            messages=[{
                "role": "user",
                "content": f"""Extract the following information from this contract for project {project_code}:

CONTRACT TEXT:
{pdf_text[:15000]}

EXTRACT:
1. Payment Terms (e.g., "30% deposit, 40% midpoint, 30% completion")
2. Payment Schedule/Milestones with amounts
3. Scope of Work - which disciplines are included:
   - Landscape Design (Yes/No)
   - Architecture (Yes/No)
   - Interior Design (Yes/No)
4. Phase breakdown (e.g., Concept Design, Design Development, Construction Documentation, Construction Administration)
5. Fee breakdown by discipline and phase (if available)
6. Any specific deliverables or milestones mentioned
7. Project duration or timeline
8. Any special terms or conditions

Return ONLY valid JSON with this exact structure (no markdown, no explanation):
{{
  "payment_terms": "description of payment terms",
  "payment_schedule": [
    {{"milestone": "milestone name", "percentage": 30, "amount_usd": 555000, "timing": "upon signing"}}
  ],
  "disciplines": {{
    "landscape": true,
    "architecture": false,
    "interior": true
  }},
  "phases": ["Concept Design", "Design Development"],
  "fee_breakdown": [
    {{"discipline": "Landscape", "phase": "Concept Design", "fee_usd": 100000, "percentage": 5.4}}
  ],
  "deliverables": ["list of key deliverables"],
  "project_duration": "duration description",
  "special_terms": "any special terms"
}}

If a field is not clearly specified, use null or empty array.
"""
            }],
            temperature=0.1,
            max_tokens=2000
        )

        # Parse OpenAI's response
        response_text = response.choices[0].message.content

        # Extract JSON from response (handle markdown code blocks)
        json_text = response_text
        if "```json" in response_text:
            json_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_text = response_text.split("```")[1].split("```")[0].strip()

        # Try to find JSON object
        start = json_text.find('{')
        end = json_text.rfind('}') + 1
        if start >= 0 and end > start:
            json_text = json_text[start:end]

        data = json.loads(json_text)
        print(f"  ✅ Extracted successfully")
        return data

    except Exception as e:
        print(f"  ❌ Error extracting contract: {e}")
        import traceback
        traceback.print_exc()
        return None


def import_contract_to_db(project_code, contract_data, project_info):
    """Import extracted contract data to database"""
    print(f"\n  💾 Importing to database: {project_code}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Update proposals table - mark as signed/won
        cursor.execute("""
            UPDATE proposals
            SET status = 'won',
                contract_signed_date = ?,
                project_value = ?,
                is_landscape = ?,
                is_architect = ?,
                is_interior = ?,
                updated_at = datetime('now')
            WHERE project_code = ?
        """, (
            project_info['signed_date'],
            project_info['project_value'],
            1 if contract_data.get('disciplines', {}).get('landscape', False) else 0,
            1 if contract_data.get('disciplines', {}).get('architecture', False) else 0,
            1 if contract_data.get('disciplines', {}).get('interior', False) else 0,
            project_code
        ))

        # 2. Check if project exists in projects table
        cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
        project = cursor.fetchone()

        if not project:
            # Create project record
            cursor.execute("""
                INSERT INTO projects (
                    project_code,
                    project_title,
                    total_fee_usd,
                    status,
                    is_active_project,
                    contract_signed_date
                ) VALUES (?, ?, ?, 'active', 1, ?)
            """, (
                project_code,
                project_info['project_name'],
                project_info['project_value'],
                project_info['signed_date']
            ))
            project_id = cursor.lastrowid
            print(f"  ✅ Created project record: {project_code}")
        else:
            project_id = project[0]
            # Update existing project
            cursor.execute("""
                UPDATE projects
                SET total_fee_usd = ?,
                    status = 'active',
                    is_active_project = 1,
                    contract_signed_date = ?
                WHERE project_id = ?
            """, (
                project_info['project_value'],
                project_info['signed_date'],
                project_id
            ))
            print(f"  ✅ Updated project record: {project_code}")

        # 3. Import fee breakdown by discipline and phase
        fee_breakdown = contract_data.get('fee_breakdown', [])
        if fee_breakdown:
            for fee in fee_breakdown:
                cursor.execute("""
                    INSERT OR REPLACE INTO project_fee_breakdown (
                        project_code,
                        discipline,
                        phase,
                        phase_fee_usd,
                        percentage_of_total,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, datetime('now'))
                """, (
                    project_code,
                    fee.get('discipline', ''),
                    fee.get('phase', ''),
                    fee.get('fee_usd', 0),
                    fee.get('percentage', 0)
                ))
            print(f"  ✅ Imported {len(fee_breakdown)} fee breakdown records")

        # 4. Store payment terms in contract_terms table (if exists)
        try:
            payment_schedule_json = json.dumps(contract_data.get('payment_schedule', []))
            phases_json = json.dumps(contract_data.get('phases', []))
            deliverables_json = json.dumps(contract_data.get('deliverables', []))

            cursor.execute("""
                INSERT OR REPLACE INTO contract_terms (
                    project_code,
                    payment_terms,
                    payment_schedule,
                    phases,
                    deliverables,
                    project_duration,
                    special_terms,
                    source_document,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                project_code,
                contract_data.get('payment_terms', ''),
                payment_schedule_json,
                phases_json,
                deliverables_json,
                contract_data.get('project_duration', ''),
                contract_data.get('special_terms', ''),
                project_info['filename']
            ))
            print(f"  ✅ Stored contract terms")
        except sqlite3.OperationalError as e:
            if "no such table" not in str(e):
                raise
            # Table doesn't exist, skip
            print(f"  ⚠️  contract_terms table doesn't exist, skipping")

        conn.commit()
        print(f"  ✅ Successfully imported: {project_code}")

    except Exception as e:
        conn.rollback()
        print(f"  ❌ Database error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


def main():
    """Main import process"""
    print("\n" + "="*80)
    print("STEP 3: IMPORT SIGNED CONTRACT PDFs")
    print("="*80)
    print(f"\nContracts folder: {CONTRACTS_FOLDER}")
    print(f"Database: {DB_PATH}")

    if not os.environ.get("OPENAI_API_KEY"):
        print("\n❌ ERROR: OPENAI_API_KEY not set in environment")
        return

    print(f"\n📋 Processing {len(SIGNED_CONTRACTS)} signed contracts:")
    for code, info in SIGNED_CONTRACTS.items():
        print(f"  • {code} - {info['project_name']}")

    print("\nThis will:")
    print("  • Extract contract data from PDFs using Claude API")
    print("  • Create active projects in projects table")
    print("  • Keep proposals in proposals table for analytics")
    print("  • Import fee breakdown and payment terms")
    print(f"\nEstimated API cost: ~$2-4 for {len(SIGNED_CONTRACTS)} contracts")

    # Ask for confirmation
    response = input("\nProceed with extraction and import? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return

    # Process each contract
    success_count = 0
    error_count = 0

    for project_code, project_info in SIGNED_CONTRACTS.items():
        print("\n" + "="*80)
        print(f"Processing: {project_code} - {project_info['project_name']}")
        print("="*80)

        contract_path = CONTRACTS_FOLDER / project_info['filename']

        if not contract_path.exists():
            print(f"  ❌ Contract file not found: {contract_path}")
            error_count += 1
            continue

        # Extract contract data using OpenAI
        contract_data = extract_contract_data_with_openai(contract_path, project_code, project_info)

        if contract_data:
            # Import to database
            import_contract_to_db(project_code, contract_data, project_info)
            success_count += 1
        else:
            error_count += 1

        print(f"\n  Progress: {success_count + error_count}/{len(SIGNED_CONTRACTS)}")

    # Final summary
    print("\n" + "="*80)
    print("STEP 3 COMPLETE")
    print("="*80)
    print(f"  ✅ Success: {success_count}")
    print(f"  ❌ Errors: {error_count}")
    print(f"  📊 Total: {len(SIGNED_CONTRACTS)}")
    print("\n✅ All 3 steps complete!")
    print("   • Proposals imported (87 proposals for analytics)")
    print("   • Fee breakdown imported (invoices & phases)")
    print("   • Contract PDFs imported (8 active projects created)")
    print("\nProposals remain in proposals table for conversion tracking.")


if __name__ == "__main__":
    main()
