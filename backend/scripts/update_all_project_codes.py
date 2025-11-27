#!/usr/bin/env python3
"""
Update ALL project codes with correct year prefixes based on official project list
This is the authoritative mapping from the screenshots
"""

import sqlite3

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

# Complete mapping from screenshots - authoritative source
PROJECT_YEAR_MAPPING = {
    'BK-001': '25',
    'BK-002': '25',
    'BK-003': '25',
    'BK-004': '25',
    'BK-005': '25',
    'BK-006': '25',
    'BK-007': '25',
    'BK-008': '25',
    'BK-009': '25',
    'BK-010': '25',
    'BK-011': '25',
    'BK-012': '25',
    'BK-013': '25',
    'BK-014': '25',
    'BK-015': '24',
    'BK-016': '24',
    'BK-017': '24',
    'BK-018': '24',
    'BK-019': '24',
    'BK-020': '24',
    'BK-021': '24',
    'BK-022': '24',
    'BK-023': '25',
    'BK-024': '25',
    'BK-025': '25',
    'BK-026': '25',
    'BK-027': '25',
    'BK-028': '25',
    'BK-029': '25',
    'BK-030': '25',
    'BK-031': '25',
    'BK-032': '25',
    'BK-033': '25',
    'BK-034': '25',
    'BK-035': '25',
    'BK-036': '25',
    'BK-037': '25',
    'BK-038': '25',
    'BK-039': '25',
    'BK-040': '25',
    'BK-041': '25',
    'BK-042': '25',
    'BK-043': '25',
    'BK-044': '25',
    'BK-045': '25',
    'BK-046': '25',
    'BK-047': '25',
    'BK-048': '25',
    'BK-049': '25',
    'BK-050': '25',
    'BK-051': '25',
    'BK-052': '25',
    'BK-053': '25',
    'BK-054': '25',
    'BK-055': '25',
    'BK-056': '25',
    'BK-057': '25',
    'BK-058': '25',
    'BK-059': '25',
    'BK-060': '25',
    'BK-061': '25',
    'BK-062': '25',
    'BK-063': '25',
    'BK-064': '25',
    'BK-065': '25',
    'BK-066': '25',
    'BK-067': '25',
    'BK-068': '25',
    'BK-069': '25',
    'BK-070': '25',
    'BK-071': '25',
    'BK-072': '25',
    'BK-073': '25',
    'BK-074': '25',
    'BK-075': '25',
    'BK-076': '25',
    'BK-077': '25',
    'BK-078': '25',
    'BK-079': '25',
    'BK-080': '25',
    'BK-081': '25',
    'BK-082': '25',
    'BK-083': '25',
    'BK-084': '25',
}

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Updating ALL project codes with correct year prefixes...\n")

    # Get all BK projects
    cursor.execute("SELECT proposal_id, project_code, project_name FROM proposals WHERE project_code LIKE '%BK-%' ORDER BY project_code")
    projects = cursor.fetchall()

    updated = 0
    already_correct = 0
    not_in_mapping = []

    for proposal_id, project_code, project_name in projects:
        # Extract the BK-XXX part
        if ' ' in project_code:
            # Already has year prefix like "25 BK-001"
            parts = project_code.split(' ', 1)
            if len(parts) == 2:
                current_year = parts[0]
                bk_code = parts[1]
            else:
                bk_code = project_code
                current_year = None
        else:
            # No year prefix yet
            bk_code = project_code
            current_year = None

        # Get correct year
        correct_year = PROJECT_YEAR_MAPPING.get(bk_code)

        if not correct_year:
            print(f"⚠ {project_code}: Not in mapping")
            not_in_mapping.append(project_code)
            continue

        correct_code = f"{correct_year} {bk_code}"

        # Check if already correct
        if project_code == correct_code:
            print(f"✓ {project_code}: Already correct")
            already_correct += 1
            continue

        # Update to correct year prefix
        cursor.execute("""
            UPDATE proposals
            SET project_code = ?, updated_at = datetime('now')
            WHERE proposal_id = ?
        """, (correct_code, proposal_id))

        print(f"↻ {project_code} → {correct_code}")
        updated += 1

    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print(f"Update complete!")
    print(f"Updated: {updated} projects")
    print(f"Already correct: {already_correct} projects")

    if not_in_mapping:
        print(f"Not in mapping: {len(not_in_mapping)} projects")
        for code in not_in_mapping:
            print(f"  - {code}")


if __name__ == "__main__":
    main()
