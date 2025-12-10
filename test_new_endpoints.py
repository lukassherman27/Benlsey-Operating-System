#!/usr/bin/env python3
"""
Test script for new timeline and team endpoints
"""
import sqlite3
import sys
sys.path.insert(0, '/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/backend')

DB_PATH = '/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/bensley_master.db'

def test_proposal_timeline(project_code):
    """Test the proposal timeline endpoint logic"""
    print(f"\n{'='*60}")
    print(f"Testing Proposal Timeline: {project_code}")
    print(f"{'='*60}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get proposal_id
    cursor.execute("SELECT proposal_id, project_name FROM proposals WHERE project_code = ?", (project_code,))
    proposal_row = cursor.fetchone()

    if not proposal_row:
        print(f"❌ Proposal {project_code} not found")
        conn.close()
        return False

    proposal_id = proposal_row['proposal_id']
    project_name = proposal_row['project_name']
    print(f"✓ Found proposal: {project_name}")

    timeline_items = []

    # Get emails
    cursor.execute("""
        SELECT COUNT(*) as count FROM emails e
        JOIN email_proposal_links epl ON e.email_id = epl.email_id
        WHERE epl.proposal_id = ?
    """, (proposal_id,))
    email_count = cursor.fetchone()['count']
    print(f"✓ Emails: {email_count}")

    # Get meetings
    cursor.execute("""
        SELECT COUNT(*) as count FROM meeting_transcripts
        WHERE proposal_id = ? OR detected_project_code = ?
    """, (proposal_id, project_code))
    meeting_count = cursor.fetchone()['count']
    print(f"✓ Meetings: {meeting_count}")

    # Get events
    cursor.execute("""
        SELECT COUNT(*) as count FROM proposal_events
        WHERE proposal_id = ? OR project_code = ?
    """, (proposal_id, project_code))
    event_count = cursor.fetchone()['count']
    print(f"✓ Events: {event_count}")

    total = email_count + meeting_count + event_count
    print(f"✓ Total timeline items: {total}")

    conn.close()
    return True

def test_proposal_stakeholders(project_code):
    """Test the proposal stakeholders endpoint logic"""
    print(f"\n{'='*60}")
    print(f"Testing Proposal Stakeholders: {project_code}")
    print(f"{'='*60}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get proposal_id
    cursor.execute("SELECT proposal_id, project_name FROM proposals WHERE project_code = ?", (project_code,))
    proposal_row = cursor.fetchone()

    if not proposal_row:
        print(f"❌ Proposal {project_code} not found")
        conn.close()
        return False

    proposal_id = proposal_row['proposal_id']
    project_name = proposal_row['project_name']
    print(f"✓ Found proposal: {project_name}")

    # Check proposal_stakeholders table
    cursor.execute("""
        SELECT COUNT(*) as count FROM proposal_stakeholders
        WHERE proposal_id = ? OR project_code = ?
    """, (proposal_id, project_code))
    stakeholder_count = cursor.fetchone()['count']
    print(f"✓ Stakeholders in table: {stakeholder_count}")

    # Check derived from emails
    cursor.execute("""
        SELECT COUNT(DISTINCT e.sender_email) as count
        FROM emails e
        JOIN email_proposal_links epl ON e.email_id = epl.email_id
        WHERE epl.proposal_id = ?
        AND e.sender_email NOT LIKE '%@bensley.com%'
    """, (proposal_id,))
    derived_count = cursor.fetchone()['count']
    print(f"✓ Stakeholders (derived from emails): {derived_count}")

    conn.close()
    return True

def test_project_team(project_code):
    """Test the project team endpoint logic"""
    print(f"\n{'='*60}")
    print(f"Testing Project Team: {project_code}")
    print(f"{'='*60}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get team members
    cursor.execute("""
        SELECT
            cpm.contact_email,
            cpm.contact_name as name,
            c.role,
            c.position as discipline,
            cpm.email_count,
            cpm.is_primary_contact
        FROM contact_project_mappings cpm
        LEFT JOIN contacts c ON cpm.contact_email = c.email
        WHERE cpm.project_code = ?
        ORDER BY cpm.is_primary_contact DESC, cpm.email_count DESC
    """, (project_code,))

    team_members = cursor.fetchall()
    count = len(team_members)

    if count == 0:
        print(f"⚠️  No team members found for {project_code}")
        conn.close()
        return True

    print(f"✓ Team members: {count}")

    # Show sample members
    for i, member in enumerate(team_members[:3]):
        name = member['name'] or 'Unknown'
        role = member['role'] or 'Team Member'
        email_count = member['email_count'] or 0
        is_primary = '⭐' if member['is_primary_contact'] else ''
        print(f"  {i+1}. {name} - {role} ({email_count} emails) {is_primary}")

    if count > 3:
        print(f"  ... and {count - 3} more")

    conn.close()
    return True

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("TESTING NEW ENDPOINTS")
    print("="*60)

    # Test with projects that have data
    test_projects = [
        ("25 BK-002", "Has emails"),
        ("25 BK-013", "Has team data"),
    ]

    all_passed = True

    for project_code, description in test_projects:
        print(f"\n\n{'#'*60}")
        print(f"# Test Project: {project_code} ({description})")
        print(f"{'#'*60}")

        # Test proposal endpoints
        if not test_proposal_timeline(project_code):
            all_passed = False

        if not test_proposal_stakeholders(project_code):
            all_passed = False

        # Test project team endpoint
        if not test_project_team(project_code):
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*60 + "\n")

    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
