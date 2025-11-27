#!/usr/bin/env python3
"""
Import Existing Project Contracts

Scans your existing project folders and imports contracts into the system.
Links them to projects and classifies them properly.
"""

import os
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def find_project_folders(base_path):
    """Find all project folders"""
    project_folders = []

    # Look for folders matching project code patterns
    # BK-XXX, 24-XXX, 25-XXX, etc.
    for root, dirs, files in os.walk(base_path):
        for dir_name in dirs:
            # Check if folder name starts with project code pattern
            if any(dir_name.startswith(prefix) for prefix in ['BK-', '24-', '25-', '23-', '22-']):
                project_folders.append(os.path.join(root, dir_name))

    return project_folders


def extract_project_code(folder_name):
    """Extract project code from folder name"""
    # Examples: "BK-087 Project Name", "25-042 Project in Location"
    parts = folder_name.split()
    if parts:
        code = parts[0]
        # Clean up any trailing characters
        if code.endswith('-'):
            code = code[:-1]
        return code
    return None


def find_contracts_in_folder(folder_path):
    """Find contract files in a project folder"""
    contracts = []

    # Look for common contract file patterns
    contract_keywords = [
        'contract', 'agreement', 'sow', 'scope of work',
        'mou', 'nda', 'proposal', 'fidic', 'signed'
    ]

    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            # Check file extension
            if not filename.lower().endswith(('.pdf', '.docx', '.doc')):
                continue

            # Check if filename contains contract keywords
            filename_lower = filename.lower()
            if any(keyword in filename_lower for keyword in contract_keywords):
                contracts.append({
                    'filepath': os.path.join(root, filename),
                    'filename': filename,
                    'folder': os.path.basename(folder_path)
                })

    return contracts


def classify_contract(filename):
    """Classify contract as bensley_contract or external_contract"""
    filename_lower = filename.lower()

    # Bensley contracts typically have these patterns
    bensley_patterns = [
        'bds standard', 'bensley standard', 'scope of work',
        'sow', 'our proposal', 'bensley proposal'
    ]

    # External contracts
    external_patterns = [
        'client', 'signed by client', 'fidic', 'client contract',
        'mou', 'nda'
    ]

    if any(pattern in filename_lower for pattern in bensley_patterns):
        return 'bensley_contract'
    elif any(pattern in filename_lower for pattern in external_patterns):
        return 'external_contract'
    else:
        # Default: if it has "proposal" it's ours, otherwise external
        if 'proposal' in filename_lower:
            return 'bensley_contract'
        return 'external_contract'


def import_contract_to_system(conn, contract, project_code, db_path):
    """Import a contract file into the system"""
    cursor = conn.cursor()

    # Get proposal_id for this project
    cursor.execute("""
        SELECT proposal_id FROM proposals WHERE project_code = ?
    """, (project_code,))
    result = cursor.fetchone()

    if not result:
        print(f"   ⚠️  Project {project_code} not found in database, skipping...")
        return False

    proposal_id = result[0]

    # Copy file to BY_DATE structure
    file_date = datetime.fromtimestamp(os.path.getmtime(contract['filepath']))
    date_folder = file_date.strftime('%Y-%m')
    dest_dir = f"/Users/lukassherman/Desktop/BDS_SYSTEM/05_FILES/BY_DATE/{date_folder}"
    os.makedirs(dest_dir, exist_ok=True)

    # Handle duplicate filenames
    dest_path = os.path.join(dest_dir, contract['filename'])
    counter = 1
    base_name, ext = os.path.splitext(contract['filename'])
    while os.path.exists(dest_path):
        dest_path = os.path.join(dest_dir, f"{base_name}_{counter}{ext}")
        counter += 1

    # Copy file
    shutil.copy2(contract['filepath'], dest_path)

    # Get file info
    filesize = os.path.getsize(dest_path)
    mime_type = 'application/pdf' if dest_path.endswith('.pdf') else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

    # Classify
    doc_type = classify_contract(contract['filename'])

    # Check if signed
    is_signed = 1 if 'signed' in contract['filename'].lower() else 0

    # Create fake email_id (we'll use proposal_id as reference)
    # First, create a placeholder email entry
    cursor.execute("""
        INSERT INTO emails (
            message_id, sender_email, subject, date, processed, has_attachments
        ) VALUES (?, ?, ?, ?, 1, 1)
    """, (
        f"imported-contract-{project_code}-{counter}",
        "imported@bensley.com",
        f"Imported Contract: {contract['filename']}",
        file_date.isoformat()
    ))
    email_id = cursor.lastrowid

    # Link email to proposal
    cursor.execute("""
        INSERT INTO email_proposal_links (email_id, proposal_id, confidence_score)
        VALUES (?, ?, 1.0)
    """, (email_id, proposal_id))

    # Insert into email_attachments
    cursor.execute("""
        INSERT INTO email_attachments (
            email_id,
            filename,
            filepath,
            filesize,
            mime_type,
            document_type,
            is_signed,
            proposal_id,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        email_id,
        os.path.basename(dest_path),
        dest_path,
        filesize,
        mime_type,
        doc_type,
        is_signed,
        proposal_id,
        file_date.isoformat()
    ))

    conn.commit()
    return True


def main():
    print("=" * 80)
    print("IMPORT EXISTING PROJECT CONTRACTS")
    print("=" * 80)

    # Ask user for projects folder location
    print("\nWhere are your existing project folders located?")
    print("Examples:")
    print("  - /Users/lukassherman/Desktop/Projects")
    print("  - /Volumes/ServerName/Projects  (mounted network drive)")
    print("  - /Users/lukassherman/OneDrive/Bensley Projects")
    print("\nTip: If on local server, mount the drive first in Finder:")
    print("  Finder > Go > Connect to Server (Cmd+K)")
    print("  Then enter: smb://server-address or afp://server-address")

    base_path = input("\nEnter path: ").strip()

    if not os.path.exists(base_path):
        print(f"❌ Path not found: {base_path}")
        return

    print(f"\n🔍 Scanning for project folders in: {base_path}")
    project_folders = find_project_folders(base_path)

    print(f"   Found {len(project_folders)} project folders")

    if not project_folders:
        print("❌ No project folders found!")
        return

    # Show sample
    print("\n📁 Sample project folders found:")
    for folder in project_folders[:10]:
        print(f"   - {os.path.basename(folder)}")
    if len(project_folders) > 10:
        print(f"   ... and {len(project_folders) - 10} more")

    confirm = input("\nProceed with contract import? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return

    # Connect to database
    db_path = os.getenv('DATABASE_PATH')
    conn = sqlite3.connect(db_path)

    total_contracts = 0
    imported_contracts = 0
    skipped = 0

    for folder_path in project_folders:
        folder_name = os.path.basename(folder_path)
        project_code = extract_project_code(folder_name)

        if not project_code:
            continue

        # Find contracts in this folder
        contracts = find_contracts_in_folder(folder_path)

        if contracts:
            print(f"\n📁 {folder_name} ({project_code})")
            print(f"   Found {len(contracts)} contract(s)")

            for contract in contracts:
                total_contracts += 1
                print(f"   📄 {contract['filename']}")

                if import_contract_to_system(conn, contract, project_code, db_path):
                    print(f"      ✅ Imported")
                    imported_contracts += 1
                else:
                    print(f"      ⚠️  Skipped")
                    skipped += 1

    conn.close()

    print("\n" + "=" * 80)
    print("📊 IMPORT COMPLETE")
    print("=" * 80)
    print(f"Total contracts found: {total_contracts}")
    print(f"Successfully imported: {imported_contracts}")
    print(f"Skipped: {skipped}")
    print("\n✅ All contracts are now in the system!")
    print(f"   Files copied to: /Users/lukassherman/Desktop/BDS_SYSTEM/05_FILES/BY_DATE/")
    print(f"   Database updated: {db_path}")
    print("\n")


if __name__ == '__main__':
    main()
