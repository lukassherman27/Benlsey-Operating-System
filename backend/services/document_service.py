"""
Document Service

Handles all document-related operations:
- Document retrieval and search
- Document-proposal linking
- Document statistics
"""

from typing import Optional, List, Dict, Any
from .base_service import BaseService


class DocumentService(BaseService):
    """Service for document operations"""

    def get_all_documents(
        self,
        search_query: Optional[str] = None,
        document_type: Optional[str] = None,
        proposal_id: Optional[int] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Get all documents with search and filtering

        Args:
            search_query: Search in filename field
            document_type: Filter by document type
            proposal_id: Filter by linked proposal
            page: Page number
            per_page: Results per page

        Returns:
            Paginated document results
        """
        sql = """
            SELECT
                d.document_id,
                d.file_name,
                d.file_path,
                d.document_type,
                d.file_size,
                d.modified_date,
                d.project_code
            FROM documents d
            WHERE 1=1
        """
        params = []

        if search_query:
            sql += " AND d.file_name LIKE ?"
            search_term = f"%{search_query}%"
            params.append(search_term)

        if document_type:
            sql += " AND d.document_type = ?"
            params.append(document_type)

        if proposal_id:
            sql += """ AND d.document_id IN (
                SELECT document_id FROM document_proposal_links WHERE proposal_id = ?
            )"""
            params.append(proposal_id)

        sql += " ORDER BY d.modified_date DESC"

        return self.paginate(sql, tuple(params), page, per_page)

    def get_document_by_id(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        sql = """
            SELECT
                d.*,
                p.project_code,
                p.project_title
            FROM documents d
            LEFT JOIN document_proposal_links dpl ON d.document_id = dpl.document_id
            LEFT JOIN proposals p ON dpl.proposal_id = p.proposal_id
            WHERE d.document_id = ?
        """
        return self.execute_query(sql, (document_id,), fetch_one=True)

    def get_documents_for_proposal(self, project_code: str) -> List[Dict[str, Any]]:
        """Get all documents for a proposal"""
        sql = """
            SELECT
                d.document_id,
                d.file_name,
                d.file_path,
                d.document_type,
                d.file_size,
                d.modified_date,
                dpl.link_type
            FROM documents d
            JOIN document_proposal_links dpl ON d.document_id = dpl.document_id
            JOIN proposals p ON dpl.proposal_id = p.proposal_id
            WHERE p.project_code = ?
            ORDER BY d.modified_date DESC
        """
        return self.execute_query(sql, (project_code,))

    def search_documents(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search documents by filename

        Args:
            query: Search term
            limit: Max results

        Returns:
            List of matching documents
        """
        sql = """
            SELECT
                d.document_id,
                d.file_name,
                d.file_path,
                d.document_type,
                d.modified_date,
                d.project_code
            FROM documents d
            WHERE d.file_name LIKE ? OR d.project_code LIKE ?
            ORDER BY d.modified_date DESC
            LIMIT ?
        """
        search_term = f"%{query}%"
        return self.execute_query(sql, (search_term, search_term, limit))

    def get_document_types(self) -> List[Dict[str, Any]]:
        """Get all document types with counts"""
        sql = """
            SELECT
                document_type,
                COUNT(*) as count
            FROM documents
            WHERE document_type IS NOT NULL
            GROUP BY document_type
            ORDER BY count DESC
        """
        return self.execute_query(sql)

    def get_recent_documents(self, days: int = 7, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recently modified documents"""
        sql = """
            SELECT
                d.document_id,
                d.file_name,
                d.document_type,
                d.modified_date,
                d.project_code
            FROM documents d
            WHERE d.modified_date >= date('now', ?)
            ORDER BY d.modified_date DESC
            LIMIT ?
        """
        return self.execute_query(sql, (f'-{days} days', limit))

    def get_document_stats(self) -> Dict[str, Any]:
        """Get document statistics"""
        stats = {}

        stats['total_documents'] = self.count_rows('documents')
        stats['linked_to_proposals'] = self.count_rows('document_proposal_links')

        # Total file size
        sql = "SELECT SUM(file_size) as total_size FROM documents"
        result = self.execute_query(sql, fetch_one=True)
        stats['total_size_bytes'] = result['total_size'] or 0

        # Most common type
        sql = """
            SELECT document_type, COUNT(*) as count
            FROM documents
            WHERE document_type IS NOT NULL
            GROUP BY document_type
            ORDER BY count DESC
            LIMIT 1
        """
        result = self.execute_query(sql, fetch_one=True)
        stats['most_common_type'] = result['document_type'] if result else None

        return stats
