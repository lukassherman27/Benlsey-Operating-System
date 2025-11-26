#!/usr/bin/env python3
"""
CONTRACT SCANNER - RUN ON PC

Scans your project folders and creates a manifest of all contracts.
Save the output JSON file and transfer to Mac for import.
"""

import os
import json
from datetime import datetime
from pathlib import Path


def extract_project_code(folder_name):
    """Extract project code from folder name"""
    parts = folder_name.split()
    if parts:
        code = parts[0]
        if code.endswith('-'):
            code = code[:-1]
        return code
    return None


def find_contracts_in_folder(folder_path):
    """Find contract files in a project folder"""
    contracts = []

    contract_keywords = [
        'contract', 'agreement', 'sow', 'scope of work',
        'mou', 'nda', 'proposal', 'fidic', 'signed'
    ]

    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if not filename.lower().endswith(('.pdf', '.docx', '.doc')):
                continue

            filename_lower = filename.lower()
            if any(keyword in filename_lower for keyword in contract_keywords):
                full_path = os.path.join(root, filename)

                # Get file info
                stat = os.stat(full_path)

                contracts.append({
                    'filename': filename,
                    'filepath': full_path,
                    'filesize': stat.st_size,
                    'modified_date': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'relative_path': os.path.relpath(full_path, folder_path)
                })

    return contracts


def main():
    print("=" * 80)
    print("CONTRACT SCANNER FOR PC")
    print("=" * 80)
    print("\nThis will scan your project folders and create a manifest.")
    print("Transfer the manifest to your Mac for import.\n")

    # Ask for projects folder
    print("Where are your project folders?")
    print("Example: C:\\Users\\YourName\\Documents\\Bensley Projects")

    base_path = input("\nEnter path: ").strip()

    if not os.path.exists(base_path):
        print(f"❌ Path not found: {base_path}")
        return

    print(f"\n🔍 Scanning: {base_path}")

    manifest = {
        'scan_date': datetime.now().isoformat(),
        'base_path': base_path,
        'projects': []
    }

    total_contracts = 0

    # Find all project folders
    for item in os.listdir(base_path):
        folder_path = os.path.join(base_path, item)

        if not os.path.isdir(folder_path):
            continue

        # Check if it's a project folder
        if any(item.startswith(prefix) for prefix in ['BK-', '24-', '25-', '23-', '22-']):
            project_code = extract_project_code(item)

            if not project_code:
                continue

            print(f"\n📁 {item}")

            contracts = find_contracts_in_folder(folder_path)

            if contracts:
                print(f"   Found {len(contracts)} contract(s)")
                for contract in contracts:
                    print(f"   - {contract['filename']}")
                    total_contracts += 1

                manifest['projects'].append({
                    'project_code': project_code,
                    'folder_name': item,
                    'folder_path': folder_path,
                    'contracts': contracts
                })

    # Save manifest
    output_file = 'contract_manifest.json'
    with open(output_file, 'w') as f:
        json.dump(manifest, f, indent=2)

    print("\n" + "=" * 80)
    print("✅ SCAN COMPLETE")
    print("=" * 80)
    print(f"Total projects scanned: {len(manifest['projects'])}")
    print(f"Total contracts found: {total_contracts}")
    print(f"\nManifest saved to: {os.path.abspath(output_file)}")
    print("\n📤 NEXT STEP:")
    print(f"   1. Copy {output_file} to your Mac")
    print(f"   2. Also copy all contract files to Mac (or set up file sharing)")
    print(f"   3. Run the import script on Mac")
    print("\n")


if __name__ == '__main__':
    main()
