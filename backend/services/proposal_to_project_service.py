"""
Service to handle proposal → active project transition.
Triggered when proposal status changes to 'Contract Signed'.

Issue #423: Implements the lifecycle fix for proposals becoming active projects.

CRITICAL: project_id in projects table is NOT the same as proposal_id in proposals table!
- proposals.proposal_id = auto-increment PK for proposals (e.g., 3554, 115072)
- projects.project_id = auto-increment PK for projects (e.g., 31, 38)
- They are linked by project_code (e.g., '25 BK-033')
"""

from datetime import datetime
from typing import Optional, Dict, Any
import sqlite3
import logging

logger = logging.getLogger(__name__)


def on_contract_signed(
    conn: sqlite3.Connection,
    proposal_id: int,
    contract_signed_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Handle transition when contract is signed.

    This function:
    1. Updates proposals table: set contract_signed_date, is_archived=1
    2. Updates projects table: set status='active', link proposal_id
    3. Copies email links from email_proposal_links to email_project_links

    Args:
        conn: Database connection (passed in to use existing transaction)
        proposal_id: The proposal being transitioned
        contract_signed_date: Optional date string (YYYY-MM-DD), defaults to today

    Returns:
        Dict with transition results

    Raises:
        ValueError: If proposal or project not found
    """
    cursor = conn.cursor()

    # Get proposal details
    cursor.execute(
        "SELECT proposal_id, project_code, project_name FROM proposals WHERE proposal_id = ?",
        (proposal_id,)
    )
    proposal = cursor.fetchone()

    if not proposal:
        raise ValueError(f"Proposal {proposal_id} not found")

    project_code = proposal['project_code']
    project_name = proposal['project_name']
    signed_date = contract_signed_date or datetime.now().strftime('%Y-%m-%d')

    # Get the ACTUAL project_id from projects table
    # CRITICAL: This is different from proposal_id!
    cursor.execute(
        "SELECT project_id FROM projects WHERE project_code = ?",
        (project_code,)
    )
    project_row = cursor.fetchone()

    if not project_row:
        # Project doesn't exist in projects table - create it
        logger.warning(f"Project {project_code} not found in projects table, creating...")
        cursor.execute("""
            INSERT INTO projects (project_code, project_title, status, proposal_id, created_at, updated_at)
            VALUES (?, ?, 'active', ?, datetime('now'), datetime('now'))
        """, (project_code, project_name, proposal_id))
        actual_project_id = cursor.lastrowid
        logger.info(f"Created project {project_code} with project_id={actual_project_id}")
    else:
        actual_project_id = project_row['project_id']

    # 1. Update proposal - mark as archived with signed date
    cursor.execute("""
        UPDATE proposals
        SET contract_signed_date = ?,
            is_archived = 1,
            updated_at = datetime('now')
        WHERE proposal_id = ?
    """, (signed_date, proposal_id))

    logger.info(f"Updated proposal {proposal_id} ({project_code}): is_archived=1, contract_signed_date={signed_date}")

    # 2. Update projects table - set to active, link proposal
    cursor.execute("""
        UPDATE projects
        SET status = 'active',
            proposal_id = ?,
            contract_signed_date = ?,
            updated_at = datetime('now')
        WHERE project_id = ?
    """, (proposal_id, signed_date, actual_project_id))

    logger.info(f"Updated project {actual_project_id} ({project_code}): status='active', proposal_id={proposal_id}")

    # 3. Copy email links from email_proposal_links to email_project_links
    # CRITICAL: Use actual_project_id (from projects table), NOT proposal_id!
    cursor.execute("""
        INSERT OR IGNORE INTO email_project_links
            (email_id, project_id, project_code, confidence, link_method, created_at)
        SELECT
            epl.email_id,
            :project_id,
            :project_code,
            epl.confidence_score,
            'proposal_transition',
            datetime('now')
        FROM email_proposal_links epl
        WHERE epl.proposal_id = :proposal_id
    """, {
        'proposal_id': proposal_id,
        'project_id': actual_project_id,  # Use actual project_id, NOT proposal_id!
        'project_code': project_code
    })

    # Get count of copied links
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM email_project_links
        WHERE project_id = ? AND project_code = ?
    """, (actual_project_id, project_code))
    copied_count = cursor.fetchone()['cnt']

    # Get count of source links for comparison
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM email_proposal_links
        WHERE proposal_id = ?
    """, (proposal_id,))
    source_count = cursor.fetchone()['cnt']

    logger.info(f"Copied {copied_count} email links for {project_code} (source had {source_count})")

    # Note: We don't commit here - let the caller manage the transaction

    return {
        'success': True,
        'proposal_id': proposal_id,
        'project_id': actual_project_id,
        'project_code': project_code,
        'project_name': project_name,
        'emails_in_proposal_links': source_count,
        'emails_in_project_links': copied_count,
        'contract_signed_date': signed_date
    }


def run_transition_for_signed_proposals(db_path: str) -> list:
    """
    Run transitions for all proposals that are 'Contract Signed' but not yet archived.

    This is a one-time fix for existing data.

    Args:
        db_path: Path to the SQLite database

    Returns:
        List of transition results
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find proposals that are Contract Signed but not archived
    cursor.execute("""
        SELECT proposal_id, project_code, project_name, contract_signed_date
        FROM proposals
        WHERE status = 'Contract Signed'
        AND (is_archived IS NULL OR is_archived = 0)
    """)

    proposals = cursor.fetchall()
    results = []

    for proposal in proposals:
        try:
            result = on_contract_signed(
                conn=conn,
                proposal_id=proposal['proposal_id'],
                contract_signed_date=proposal['contract_signed_date']
            )
            results.append(result)
            print(f"✅ Transitioned {proposal['project_code']}: {proposal['project_name']}")
        except Exception as e:
            error_result = {
                'success': False,
                'proposal_id': proposal['proposal_id'],
                'project_code': proposal['project_code'],
                'error': str(e)
            }
            results.append(error_result)
            print(f"❌ Failed {proposal['project_code']}: {e}")

    conn.commit()
    conn.close()

    return results


if __name__ == "__main__":
    # For testing/one-time fix
    import os
    from pathlib import Path

    # Find database
    db_path = Path(__file__).parent.parent.parent / "database" / "bensley_master.db"

    if not db_path.exists():
        print(f"Database not found: {db_path}")
        exit(1)

    print(f"Running transitions on: {db_path}")
    print("=" * 60)

    results = run_transition_for_signed_proposals(str(db_path))

    print("=" * 60)
    print(f"Completed: {len([r for r in results if r.get('success')])} succeeded")
    print(f"Failed: {len([r for r in results if not r.get('success')])}")
