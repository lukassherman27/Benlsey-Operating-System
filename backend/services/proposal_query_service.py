#!/usr/bin/env python3
"""
Backend service for proposal query system
Can be integrated into FastAPI backend
"""
import sqlite3
import re
from typing import List, Dict, Optional, Any

DB_PATH = "database/bensley_master.db"

class ProposalQueryService:
    """Service for querying proposals, projects, documents, and emails"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def search_projects_and_proposals(self, query_text: str) -> List[Dict[str, Any]]:
        """
        Search across both projects and proposals tables
        Returns unified results
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return dict-like rows
        cursor = conn.cursor()

        # Extract project code if present
        code_match = re.search(r'\d{2}\s*BK-\d+|BK-\d+', query_text, re.IGNORECASE)

        results = []

        # Search proposals first
        # Issue #111: Fixed column names to match proposals table schema
        if code_match:
            code = code_match.group().replace(' ', '')
            cursor.execute("""
                SELECT
                    'proposal' as source,
                    p.proposal_id as id,
                    p.project_code,
                    p.project_name as project_title,
                    COALESCE(p.client_company, 'Unknown') as client_company,
                    p.contact_person,
                    p.contact_email,
                    p.project_value,
                    p.status,
                    p.created_at,
                    p.last_contact_date,
                    p.on_hold,
                    p.on_hold_reason,
                    p.internal_notes,
                    p.win_probability,
                    p.health_score
                FROM proposals p
                WHERE p.project_code LIKE ?
            """, (f'%{code}%',))
            results.extend([dict(row) for row in cursor.fetchall()])

        # Also search by name/client
        # Issue #111: Fixed column names to match proposals table schema
        if not results or not code_match:
            search_term = f'%{query_text}%'
            cursor.execute("""
                SELECT
                    'proposal' as source,
                    p.proposal_id as id,
                    p.project_code,
                    p.project_name as project_title,
                    COALESCE(p.client_company, 'Unknown') as client_company,
                    p.contact_person,
                    p.contact_email,
                    p.project_value,
                    p.status,
                    p.created_at,
                    p.last_contact_date,
                    p.on_hold,
                    p.on_hold_reason,
                    p.internal_notes,
                    p.win_probability,
                    p.health_score
                FROM proposals p
                WHERE p.project_name LIKE ?
                   OR COALESCE(p.client_company, 'Unknown') LIKE ?
                   OR p.project_code LIKE ?
                LIMIT 10
            """, (search_term, search_term, search_term))
            results.extend([dict(row) for row in cursor.fetchall()])

        # Also search active projects table
        # Issue #110: Fixed typo project_coder -> project_code
        # Issue #111: Fixed query to properly use projects table columns
        if code_match:
            code = code_match.group().replace(' ', '')
            cursor.execute("""
                SELECT
                    'project' as source,
                    p.project_id as id,
                    p.project_code,
                    p.project_title as project_title,
                    c.company_name as client_company,
                    NULL as contact_person,
                    NULL as contact_email,
                    p.total_fee_usd as project_value,
                    p.status,
                    p.date_created as created_at,
                    NULL as last_contact_date,
                    0 as on_hold,
                    NULL as on_hold_reason,
                    p.notes as internal_notes,
                    NULL as win_probability,
                    NULL as health_score
                FROM projects p
                LEFT JOIN clients c ON p.client_id = c.client_id
                WHERE p.project_code LIKE ?
            """, (f'%{code}%',))
            results.extend([dict(row) for row in cursor.fetchall()])

        conn.close()
        return results

    def get_project_documents(self, project_code: str, doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all documents or specific type of documents for a project"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if doc_type == 'scope':
            # Get scope/proposal documents
            cursor.execute("""
                SELECT
                    file_name,
                    document_type,
                    file_path,
                    file_size,
                    created_date,
                    modified_date,
                    page_count
                FROM documents
                WHERE project_code = ?
                  AND (file_name LIKE '%scope%'
                       OR file_name LIKE '%proposal%'
                       OR file_name LIKE '%contract%'
                       OR document_type IN ('proposal', 'contract'))
                ORDER BY modified_date DESC
            """, (project_code,))
        else:
            # Get all documents
            cursor.execute("""
                SELECT
                    file_name,
                    document_type,
                    file_path,
                    file_size,
                    created_date,
                    modified_date,
                    page_count
                FROM documents
                WHERE project_code = ?
                ORDER BY modified_date DESC
            """, (project_code,))

        docs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return docs

    def get_project_emails(self, project_code: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent emails about a project"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Try proposals table first
        cursor.execute("""
            SELECT
                e.email_id,
                e.subject,
                e.sender_name,
                e.sender_email,
                e.date,
                e.snippet,
                e.has_attachments
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            JOIN proposals p ON epl.proposal_id = p.project_id
            WHERE p.project_code = ?
            ORDER BY e.date DESC
            LIMIT ?
        """, (project_code, limit))

        emails = [dict(row) for row in cursor.fetchall()]

        # If no results, try project table
        if not emails:
            cursor.execute("""
                SELECT
                    e.email_id,
                    e.subject,
                    e.sender_name,
                    e.sender_email,
                    e.date,
                    e.snippet,
                    e.has_attachments
                FROM emails e
                JOIN email_project_links epl ON e.email_id = epl.email_id
                JOIN projects pr ON epl.project_id = pr.project_id
                WHERE pr.project_code = ?
                ORDER BY e.date DESC
                LIMIT ?
            """, (project_code, limit))

            emails = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return emails

    def get_project_fee(self, project_code: str) -> Optional[float]:
        """Get the contract fee for a project"""
        results = self.search_projects_and_proposals(project_code)
        if results:
            return results[0].get('project_value')
        return None

    def find_scope_of_work(self, project_code: str) -> List[Dict[str, Any]]:
        """Find scope of work documents for a project"""
        return self.get_project_documents(project_code, doc_type='scope')

    def get_proposal_status(self, project_code: str) -> Optional[Dict[str, Any]]:
        """Get full status of a proposal"""
        results = self.search_projects_and_proposals(project_code)
        if not results:
            return None

        project = results[0]
        project['documents'] = self.get_project_documents(project['project_code'])
        project['recent_emails'] = self.get_project_emails(project['project_code'], limit=5)

        return project


# Example usage
if __name__ == "__main__":
    service = ProposalQueryService()

    # Test queries
    print("Testing: BK-070")
    result = service.get_proposal_status("BK-070")
    if result:
        print(f"Found: {result['project_title']}")
        print(f"Status: {result['status']}")
        print(f"Value: ${result['project_value']:,.0f}" if result['project_value'] else "Value: N/A")
        print(f"Documents: {len(result['documents'])}")
        print(f"Emails: {len(result['recent_emails'])}")

    print("\n" + "=" * 80 + "\n")

    print("Testing: Tel Aviv")
    results = service.search_projects_and_proposals("Tel Aviv")
    print(f"Found {len(results)} results:")
    for r in results:
        print(f"  - {r['project_code']}: {r['project_title']} ({r['status']})")
