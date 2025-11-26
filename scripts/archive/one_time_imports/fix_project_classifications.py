#!/usr/bin/env python3
"""
Fix project classifications based on user feedback
"""

import sqlite3
import uuid
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def remove_from_active_projects(project_code: str):
    """Mark a project as not active"""
    conn = get_connection()
    cursor = conn.cursor()

    # First check if it exists
    cursor.execute("SELECT * FROM projects WHERE project_code = ?", (project_code,))
    project = cursor.fetchone()

    if not project:
        print(f"❌ Project {project_code} not found in database")
        conn.close()
        return False

    print(f"\n📋 Found project: {project['project_name']}")
    print(f"   Current status: {project['status']}")
    print(f"   Is active: {project['is_active_project']}")

    # Update to mark as not active
    cursor.execute("""
        UPDATE projects
        SET is_active_project = 0,
            status = 'inactive',
            updated_at = ?
        WHERE project_code = ?
    """, (datetime.now().isoformat(), project_code))

    conn.commit()
    conn.close()

    print(f"✅ Removed {project_code} from active projects")
    return True


def move_to_proposals(project_code: str):
    """Move a project from active projects to proposals"""
    conn = get_connection()
    cursor = conn.cursor()

    # Get project data
    cursor.execute("SELECT * FROM projects WHERE project_code = ?", (project_code,))
    project = cursor.fetchone()

    if not project:
        print(f"❌ Project {project_code} not found in database")
        conn.close()
        return False

    print(f"\n📋 Found project: {project['project_name']}")
    print(f"   Total fee: ${project['total_fee_usd']:,.0f}" if project['total_fee_usd'] else "   Total fee: Unknown")

    # Check if already in proposals
    cursor.execute("SELECT * FROM proposals WHERE project_code = ?", (project_code,))
    existing_proposal = cursor.fetchone()

    if existing_proposal:
        print(f"⚠️  Already exists in proposals table")
    else:
        # Create proposal entry
        proposal_id = f"PROP-{project_code}-{uuid.uuid4().hex[:8]}"

        cursor.execute("""
            INSERT INTO proposals (
                proposal_id,
                project_code,
                project_name,
                client_company,
                total_fee_usd,
                status,
                proposal_date,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            proposal_id,
            project_code,
            project['project_name'],
            project['client_company'],
            project['total_fee_usd'],
            'pending',  # Default proposal status
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

        print(f"✅ Created proposal entry: {proposal_id}")

    # Remove from active projects
    cursor.execute("""
        UPDATE projects
        SET is_active_project = 0,
            status = 'proposal',
            updated_at = ?
        WHERE project_code = ?
    """, (datetime.now().isoformat(), project_code))

    conn.commit()
    conn.close()

    print(f"✅ Moved {project_code} to proposals")
    return True


def main():
    print("\n" + "="*80)
    print(" FIX PROJECT CLASSIFICATIONS ".center(80, "="))
    print("="*80)

    # 1. Remove 25 BK-008 (TARC $2.75M) from active
    print("\n1. Removing 25 BK-008 from active projects...")
    remove_from_active_projects("25 BK-008")

    # 2. Move 25 BK-037 (India Wellness) to proposals
    print("\n2. Moving 25 BK-037 to proposals...")
    move_to_proposals("25 BK-037")

    print("\n" + "="*80)
    print("✅ COMPLETED")
    print("="*80)
    print("\nChanges made:")
    print("  • 25 BK-008 (TARC $2.75M) - Removed from active projects")
    print("  • 25 BK-037 (India Wellness) - Moved to proposals table")
    print("\nNote: You can add proposal details (first contact, etc.) using the proposals")
    print("      management interface or by updating the proposals table directly.")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
