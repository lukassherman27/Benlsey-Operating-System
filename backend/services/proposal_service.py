"""
Proposal Service

Handles all proposal-related operations (projects with status='proposal'):
- CRUD operations
- Health score calculations
- Timeline generation
- Statistics and analytics

Note: After migration 015, proposals are now stored in the unified 'projects' table
with status='proposal'. This service filters for proposal records.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from .base_service import BaseService


class ProposalService(BaseService):
    """Service for proposal operations"""

    def _enhance_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance proposal dict with calculated fields

        Args:
            proposal: Proposal dict from database

        Returns:
            Enhanced proposal dict
        """
        if proposal is None:
            return None

        # Add health_calculated boolean and ensure health_score is always a number
        health_score = proposal.get('health_score')
        proposal['health_calculated'] = health_score is not None
        proposal['health_score'] = health_score if health_score is not None else 0.0

        return proposal

    def _enhance_proposals(self, proposals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance a list of proposals"""
        return [self._enhance_proposal(p) for p in proposals]

    def get_all_proposals(
        self,
        status: Optional[str] = None,
        is_active_project: Optional[bool] = None,
        page: int = 1,
        per_page: int = 20,
        sort_by: str = 'health_score',
        sort_order: str = 'ASC'
    ) -> Dict[str, Any]:
        """
        Get all proposals with optional filtering and pagination

        Args:
            status: Filter by status
            is_active_project: Filter by active project flag
            page: Page number
            per_page: Results per page
            sort_by: Column to sort by
            sort_order: 'ASC' or 'DESC'

        Returns:
            Paginated results with proposals
        """
        sql = """
            SELECT
                proposal_id,
                project_code,
                project_name,
                status,
                health_score,
                days_since_contact,
                is_active_project,
                created_at,
                updated_at
            FROM projects
            WHERE status = 'proposal'
        """
        params = []

        # Note: status filter removed since we're already filtering for status='proposal'

        if is_active_project is not None:
            sql += " AND is_active_project = ?"
            params.append(1 if is_active_project else 0)

        # Validate sort parameters to prevent SQL injection
        allowed_columns = [
            'proposal_id', 'project_code', 'project_name', 'status',
            'health_score', 'days_since_contact', 'is_active_project',
            'created_at', 'updated_at'
        ]
        validated_sort_by = self.validate_sort_column(sort_by, allowed_columns)
        validated_sort_order = self.validate_sort_order(sort_order)

        sql += f" ORDER BY {validated_sort_by} {validated_sort_order}"

        result = self.paginate(sql, tuple(params), page, per_page)
        result['items'] = self._enhance_proposals(result['items'])
        return result

    def get_proposal_by_code(self, project_code: str) -> Optional[Dict[str, Any]]:
        """
        Get proposal by project code

        Args:
            project_code: Project code (e.g., 'BK-069')

        Returns:
            Proposal dict or None
        """
        sql = """
            SELECT
                p.*,
                COUNT(DISTINCT e.email_id) as email_count,
                COUNT(DISTINCT d.document_id) as document_count
            FROM projects p
            LEFT JOIN email_proposal_links epl ON p.proposal_id = epl.proposal_id
            LEFT JOIN emails e ON epl.email_id = e.email_id
            LEFT JOIN document_proposal_links dpl ON p.proposal_id = dpl.proposal_id
            LEFT JOIN documents d ON dpl.document_id = d.document_id
            WHERE p.project_code = ?
            AND p.status = 'proposal'
            GROUP BY p.proposal_id
        """
        result = self.execute_query(sql, (project_code,), fetch_one=True)
        return self._enhance_proposal(result)

    def get_proposal_by_id(self, proposal_id: int) -> Optional[Dict[str, Any]]:
        """Get proposal by ID"""
        sql = "SELECT * FROM projects WHERE proposal_id = ? AND status = 'proposal'"
        result = self.execute_query(sql, (proposal_id,), fetch_one=True)
        return self._enhance_proposal(result)

    def get_unhealthy_proposals(self, threshold: float = 50.0) -> List[Dict[str, Any]]:
        """
        Get proposals with health score below threshold

        Args:
            threshold: Health score threshold (default 50)

        Returns:
            List of unhealthy proposals
        """
        sql = """
            SELECT
                proposal_id,
                project_code,
                project_name,
                health_score,
                days_since_contact,
                status
            FROM projects
            WHERE health_score < ?
            AND is_active_project = 1
            AND status = 'proposal'
            ORDER BY health_score ASC
        """
        results = self.execute_query(sql, (threshold,))
        return self._enhance_proposals(results)

    def get_proposal_timeline(self, project_code: str) -> Dict[str, Any]:
        """
        Get complete timeline for a proposal

        Args:
            project_code: Project code

        Returns:
            Dict with proposal info, emails, documents, timeline events
        """
        proposal = self.get_proposal_by_code(project_code)
        if not proposal:
            return None

        proposal_id = proposal['proposal_id']

        # Get emails
        emails_sql = """
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.date,
                e.snippet
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            WHERE epl.proposal_id = ?
            ORDER BY e.date DESC
        """
        emails = self.execute_query(emails_sql, (proposal_id,))

        # Get documents
        docs_sql = """
            SELECT
                d.document_id,
                d.file_name,
                d.document_type,
                d.modified_date,
                d.file_size
            FROM documents d
            JOIN document_proposal_links dpl ON d.document_id = dpl.document_id
            WHERE dpl.proposal_id = ?
            ORDER BY d.modified_date DESC
        """
        documents = self.execute_query(docs_sql, (proposal_id,))

        # Combine into timeline
        timeline = []

        for email in emails:
            timeline.append({
                'type': 'email',
                'date': email['date'],
                'title': email['subject'],
                'description': f"From: {email['sender_email']}",
                'data': email
            })

        for doc in documents:
            timeline.append({
                'type': 'document',
                'date': doc['modified_date'],
                'title': doc['file_name'],
                'description': f"Type: {doc['document_type']}",
                'data': doc
            })

        # Sort timeline by date
        timeline.sort(key=lambda x: x['date'], reverse=True)

        return {
            'proposal': proposal,
            'timeline': timeline,
            'emails': emails,
            'documents': documents,
            'stats': {
                'total_emails': len(emails),
                'total_documents': len(documents),
                'last_activity': timeline[0]['date'] if timeline else None
            }
        }

    def get_proposal_health(self, project_code: str) -> Optional[Dict[str, Any]]:
        """
        Get health metrics for a proposal

        Args:
            project_code: Project code

        Returns:
            Dict with health metrics
        """
        proposal = self.get_proposal_by_code(project_code)
        if not proposal:
            return None

        # Calculate health factors
        health_factors = []

        if proposal['days_since_contact'] is not None:
            if proposal['days_since_contact'] < 7:
                health_factors.append({'factor': 'Recent contact', 'impact': 'positive'})
            elif proposal['days_since_contact'] > 30:
                health_factors.append({'factor': 'No contact in 30+ days', 'impact': 'negative'})

        if proposal['email_count'] > 10:
            health_factors.append({'factor': 'Active communication', 'impact': 'positive'})

        if proposal['document_count'] == 0:
            health_factors.append({'factor': 'No documents', 'impact': 'warning'})

        return {
            'project_code': project_code,
            'health_score': proposal['health_score'],
            'days_since_contact': proposal['days_since_contact'],
            'is_active_project': bool(proposal['is_active_project']),
            'factors': health_factors,
            'recommendation': self._get_health_recommendation(proposal['health_score'])
        }

    def _get_health_recommendation(self, health_score: Optional[float]) -> str:
        """Get recommendation based on health score"""
        if health_score is None:
            return "Insufficient data to assess health"

        if health_score >= 80:
            return "Healthy - Continue current engagement"
        elif health_score >= 60:
            return "Moderate - Consider follow-up"
        elif health_score >= 40:
            return "At Risk - Immediate follow-up recommended"
        else:
            return "Critical - Urgent action required"

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Get dashboard statistics

        Returns:
            Dict with overall statistics
        """
        stats = {}

        # Total counts
        stats['total_proposals'] = self.count_rows('projects', "status = 'proposal'")
        stats['active_projects'] = self.count_rows('projects', "status = 'proposal' AND is_active_project = 1")

        # Health distribution
        stats['healthy'] = self.count_rows('projects', "status = 'proposal' AND health_score >= 70")
        stats['at_risk'] = self.count_rows('projects', "status = 'proposal' AND health_score < 70 AND health_score >= 40")
        stats['critical'] = self.count_rows('projects', "status = 'proposal' AND health_score < 40")

        # Recent activity
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        stats['active_last_week'] = self.count_rows(
            'projects',
            "status = 'proposal' AND days_since_contact <= 7"
        )

        # Need follow-up
        stats['need_followup'] = self.count_rows(
            'projects',
            "status = 'proposal' AND days_since_contact > 14 AND is_active_project = 1"
        )

        return stats

    def search_proposals(self, query: str) -> List[Dict[str, Any]]:
        """
        Search proposals by name or code

        Args:
            query: Search query

        Returns:
            List of matching proposals
        """
        sql = """
            SELECT
                proposal_id,
                project_code,
                project_name,
                status,
                health_score,
                is_active_project
            FROM projects
            WHERE (project_code LIKE ? OR project_name LIKE ?)
            AND status = 'proposal'
            ORDER BY health_score ASC
            LIMIT 20
        """
        search_term = f"%{query}%"
        results = self.execute_query(sql, (search_term, search_term))
        return self._enhance_proposals(results)

    def update_proposal_status(self, project_code: str, status: str) -> bool:
        """
        Update proposal status

        Args:
            project_code: Project code
            status: New status

        Returns:
            True if updated, False otherwise
        """
        sql = """
            UPDATE projects
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE project_code = ?
        """
        rows_affected = self.execute_update(sql, (status, project_code))
        return rows_affected > 0
