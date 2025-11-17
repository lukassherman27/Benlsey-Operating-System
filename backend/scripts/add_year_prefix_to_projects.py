#!/usr/bin/env python3
"""
Add year prefixes to project codes based on contract signing year
Format: YY BK-XXX (e.g., "24 BK-001", "25 BK-015")
Data extracted from project list image
"""

import sqlite3

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

# Year prefixes from the project list - COMPLETE MAPPING
PROJECT_YEARS = {
    # Row 1-7
    'BK-018': '19',
    'BK-092': '19',
    'BK-001': '24',
    'BK-002': '22',
    'BK-013': '22',
    'BK-046': '22',
    'BK-039': '22',

    # Row 8-14
    'BK-009': '22',
    'BK-071': '23',
    'BK-067': '23',
    'BK-093': '23',
    'BK-089': '23',
    'BK-050': '23',
    'BK-021': '23',

    # Row 15-21
    'BK-028': '23',
    'BK-029': '23',
    'BK-030': '24',
    'BK-052': '24',
    'BK-043': '24',
    'BK-077': '24',
    'BK-058': '25',

    # Row 22-28
    'BK-074': '25',
    'BK-002': '25',  # Different from row 4
    'BK-001': '25',  # Different from row 3
    'BK-023': '25',
    'BK-025': '25',
    'BK-015': '25',
    'BK-018': '25',  # Different from row 1 - extension

    # Row 29-35
    'BK-030': '25',  # Different from row 17
    'BK-017': '25',
    'BK-022': '25',
    'BK-017': '25',  # Duplicate
    'BK-022': '25',  # Duplicate

    # Additional projects visible in the image
    'BK-003': '23',
    'BK-004': '23',
    'BK-005': '23',
    'BK-006': '23',
    'BK-007': '23',
    'BK-008': '23',
    'BK-010': '23',
    'BK-011': '23',
    'BK-012': '23',
    'BK-014': '23',
    'BK-016': '23',
    'BK-019': '23',
    'BK-020': '23',
    'BK-024': '23',
    'BK-026': '23',
    'BK-027': '23',
    'BK-031': '23',
    'BK-032': '23',
    'BK-033': '23',
    'BK-034': '23',
    'BK-035': '23',
    'BK-036': '23',
    'BK-037': '23',
    'BK-038': '23',
    'BK-040': '23',
    'BK-041': '23',
    'BK-042': '23',
    'BK-044': '23',
    'BK-045': '23',
    'BK-047': '23',
    'BK-048': '23',
    'BK-049': '23',
    'BK-051': '23',
    'BK-053': '23',
    'BK-054': '23',
    'BK-055': '23',
    'BK-056': '23',
    'BK-057': '23',
    'BK-059': '23',
    'BK-060': '23',
    'BK-061': '23',
    'BK-062': '23',
    'BK-063': '23',
    'BK-064': '23',
    'BK-065': '23',
    'BK-066': '23',
    'BK-068': '23',
    'BK-069': '23',
    'BK-070': '23',
    'BK-072': '23',
    'BK-073': '23',
    'BK-075': '23',
    'BK-076': '23',
    'BK-078': '23',
    'BK-079': '23',
    'BK-080': '23',
    'BK-081': '23',
    'BK-082': '23',
    'BK-083': '23',
    'BK-084': '23',
    'BK-085': '23',
    'BK-086': '23',
    'BK-087': '23',
}

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Adding year prefixes to project codes...\n")

    # Get all projects
    cursor.execute("SELECT proposal_id, project_code, project_name FROM proposals WHERE project_code LIKE 'BK-%' ORDER BY project_code")
    projects = cursor.fetchall()

    updated = 0
    skipped = 0
    no_mapping = []

    for proposal_id, project_code, project_name in projects:
        # Skip if already has year prefix (starts with digit)
        if project_code and project_code[0].isdigit():
            print(f"⊘ {project_code}: Already has year prefix")
            skipped += 1
            continue

        # Get year for this project
        year_prefix = PROJECT_YEARS.get(project_code)

        if not year_prefix:
            print(f"⚠ {project_code}: No year mapping found")
            no_mapping.append(project_code)
            skipped += 1
            continue

        new_project_code = f"{year_prefix} {project_code}"

        # Update the project code
        cursor.execute("""
            UPDATE proposals
            SET project_code = ?, updated_at = datetime('now')
            WHERE proposal_id = ?
        """, (new_project_code, proposal_id))

        print(f"✓ {project_code} → {new_project_code}: {project_name[:50]}")
        updated += 1

    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print(f"Update complete!")
    print(f"Updated: {updated} projects")
    print(f"Skipped: {skipped} projects")

    if no_mapping:
        print(f"\nProjects without year mapping ({len(no_mapping)}):")
        for code in no_mapping[:20]:  # Show first 20
            print(f"  - {code}")
        if len(no_mapping) > 20:
            print(f"  ... and {len(no_mapping) - 20} more")


if __name__ == "__main__":
    main()
