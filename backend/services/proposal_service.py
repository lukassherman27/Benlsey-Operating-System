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
from .base_service import BaseService


class ProposalService(BaseService):
    """Service for proposal operations"""

    DEFAULT_ACTIVE_STATUSES = ['proposal', 'active_project', 'active']
    STATUS_ALIASES = {
        'project': 'active',
        'projects': 'active',
        'active_project': 'active',
        'active_projects': 'active',
        'proposal': 'proposal',
        'proposals': 'proposal',
        'pipeline': 'proposal',
    }

    def _resolve_statuses(
        self,
        status: Optional[str],
        default_statuses: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Normalize incoming status filters.

        Args:
            status: Optional comma-delimited status list (e.g. "proposal,active")
            default_statuses: Default statuses when no explicit filter supplied

        Returns:
            List of normalized status strings. Empty list means "no filter".
        """
        if not status:
            return list(default_statuses or [])

        statuses = []
        for part in status.split(','):
            value = part.strip()
            if not value:
                continue
            lowered = value.lower()
            if lowered in ('all', '*'):
                return []
            normalized = self.STATUS_ALIASES.get(lowered, value)
            statuses.append(normalized)

        return statuses

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
                current_status,
                days_in_current_status,
                first_contact_date,
                proposal_sent_date,
                last_week_status,
                days_in_drafting,
                days_in_review,
                health_score,
                days_since_contact,
                is_active_project,
                country,
                location,
                currency,
                project_value,
                contact_person,
                contact_email,
                contact_phone,
                client_company,
                created_at,
                updated_at
            FROM proposals
            WHERE 1=1
        """
        params: List[Any] = []
        statuses = self._resolve_statuses(status, self.DEFAULT_ACTIVE_STATUSES)

        if statuses:
            placeholders = ",".join(["?"] * len(statuses))
            sql += f" AND status IN ({placeholders})"
            params.extend(statuses)

        if is_active_project is not None:
            sql += " AND is_active_project = ?"
            params.append(1 if is_active_project else 0)

        # Validate sort parameters to prevent SQL injection
        allowed_columns = [
            'proposal_id', 'project_code', 'project_title', 'status',
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
            FROM proposals p
            LEFT JOIN email_proposal_links epl ON p.project_id = epl.proposal_id
            LEFT JOIN emails e ON epl.email_id = e.email_id
            LEFT JOIN document_proposal_links dpl ON p.project_id = dpl.proposal_id
            LEFT JOIN documents d ON dpl.document_id = d.document_id
            WHERE p.project_code = ?
            GROUP BY p.project_id
        """
        result = self.execute_query(sql, (project_code,), fetch_one=True)
        return self._enhance_proposal(result)

    def get_proposal_by_id(self, proposal_id: int) -> Optional[Dict[str, Any]]:
        """Get proposal by ID"""
        sql = "SELECT * FROM proposals WHERE proposal_id = ?"
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
                project_title,
                health_score,
                days_since_contact,
                status
            FROM proposals
            WHERE health_score < ?
            AND is_active_project = 1
        """
        params: List[Any] = [threshold]
        statuses = self._resolve_statuses(None, self.DEFAULT_ACTIVE_STATUSES)
        if statuses:
            placeholders = ",".join(["?"] * len(statuses))
            sql += f" AND status IN ({placeholders})"
            params.extend(statuses)
        sql += " ORDER BY health_score ASC"

        results = self.execute_query(sql, tuple(params))
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
        stats: Dict[str, Any] = {}
        statuses = self._resolve_statuses(None, self.DEFAULT_ACTIVE_STATUSES)
        status_clause = ""
        status_params: tuple = ()

        if statuses:
            placeholders = ",".join(["?"] * len(statuses))
            status_clause = f"status IN ({placeholders})"
            status_params = tuple(statuses)

        def combine_clause(extra: Optional[str]) -> Optional[str]:
            parts = []
            if status_clause:
                parts.append(status_clause)
            if extra:
                parts.append(extra)
            if not parts:
                return None
            return " AND ".join(parts)

        def count_proposals(extra: Optional[str]) -> int:
            clause = combine_clause(extra)
            if clause:
                params = status_params if status_clause else ()
                return self.count_rows('proposals', clause, params)
            return self.count_rows('proposals')

        stats['total_proposals'] = count_proposals(None)
        stats['active_projects'] = count_proposals("is_active_project = 1")
        stats['healthy'] = count_proposals("health_score >= 70")
        stats['at_risk'] = count_proposals("health_score < 70 AND health_score >= 40")
        stats['critical'] = count_proposals("health_score < 40")
        stats['active_last_week'] = count_proposals("days_since_contact <= 7")
        stats['need_followup'] = count_proposals(
            "days_since_contact > 14 AND is_active_project = 1"
        )
        stats['needs_attention'] = stats['need_followup']

        avg_clause = combine_clause("health_score IS NOT NULL")
        avg_sql = "SELECT AVG(health_score) as avg_health FROM proposals"
        avg_params: tuple = ()
        if avg_clause:
            avg_sql += f" WHERE {avg_clause}"
            avg_params = status_params if status_clause else ()
        else:
            avg_sql += " WHERE health_score IS NOT NULL"

        avg_row = self.execute_query(avg_sql, avg_params, fetch_one=True)
        stats['avg_health_score'] = (
            avg_row['avg_health'] if avg_row and avg_row['avg_health'] is not None else None
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
                project_title,
                status,
                health_score,
                is_active_project
            FROM proposals
            WHERE (project_code LIKE ? OR project_title LIKE ?)
        """
        search_term = f"%{query}%"
        params: List[Any] = [search_term, search_term]
        statuses = self._resolve_statuses(None, self.DEFAULT_ACTIVE_STATUSES)
        if statuses:
            placeholders = ",".join(["?"] * len(statuses))
            sql += f" AND status IN ({placeholders})"
            params.extend(statuses)

        sql += """
            ORDER BY health_score ASC
            LIMIT 20
        """

        results = self.execute_query(sql, tuple(params))
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
            UPDATE proposals
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE project_code = ?
        """
        rows_affected = self.execute_update(sql, (status, project_code))
        return rows_affected > 0

    def get_weekly_changes(self, days: int = 7) -> Dict[str, Any]:
        """
        Get proposal pipeline changes in the last N days

        Args:
            days: Number of days to look back (default 7)

        Returns:
            Dict with period info, summary stats, and categorized changes
        """
        from datetime import datetime, timedelta

        # Calculate period
        end_date = datetime.now().date()
        start_date = (datetime.now() - timedelta(days=days)).date()

        # Get new proposals (created in the last N days)
        new_proposals_sql = """
            SELECT
                proposal_id,
                project_code,
                project_title,
                client_company,
                project_value as fee,
                status,
                created_at as created_date
            FROM proposals
            WHERE date(created_at) >= date(?)
            ORDER BY created_at DESC
        """
        new_proposals = self.execute_query(new_proposals_sql, (start_date,))

        # Get status changes from change_log
        status_changes_sql = """
            SELECT
                p.project_code,
                p.project_title,
                COALESCE(pr.client_company, 'Unknown'),
                c.old_value as previous_status,
                c.new_value as new_status,
                c.changed_at as changed_date
            FROM change_log c
            JOIN proposals p ON c.entity_id = p.project_id
            WHERE c.entity_type = 'proposal'
            AND c.field_changed = 'status'
            AND date(c.changed_at) >= date(?)
            ORDER BY c.changed_at DESC
        """
        status_changes = self.execute_query(status_changes_sql, (start_date,))

        # Get stalled proposals (no contact in 21+ days, still active)
        stalled_sql = """
            SELECT
                proposal_id,
                project_code,
                project_title,
                client_company,
                days_since_contact,
                last_contact_date
            FROM proposals
            WHERE days_since_contact >= 21
            AND is_active_project = 1
            AND status IN ('proposal', 'active', 'active_project')
            ORDER BY days_since_contact DESC
        """
        stalled_proposals = self.execute_query(stalled_sql, ())

        # Get won proposals (status changed to 'won' or contract_signed_date set in period)
        won_proposals_sql = """
            SELECT DISTINCT
                p.project_id,
                p.project_code,
                p.project_title,
                COALESCE(pr.client_company, 'Unknown'),
                p.project_value as fee,
                COALESCE(p.contract_signed_date, c.changed_at) as signed_date
            FROM proposals p
            LEFT JOIN change_log c ON c.entity_id = p.project_id
                AND c.entity_type = 'proposal'
                AND c.field_changed = 'status'
                AND c.new_value IN ('won', 'active', 'active_project')
                AND date(c.changed_at) >= date(?)
            WHERE (
                (date(p.contract_signed_date) >= date(?) AND p.contract_signed_date IS NOT NULL)
                OR (c.changed_at IS NOT NULL)
            )
            ORDER BY signed_date DESC
        """
        won_proposals = self.execute_query(won_proposals_sql, (start_date, start_date))

        # Calculate total pipeline value (all active proposals)
        pipeline_value_sql = """
            SELECT COALESCE(SUM(project_value), 0) as total_value
            FROM proposals
            WHERE status IN ('proposal', 'active', 'active_project')
            AND is_active_project = 1
        """
        pipeline_result = self.execute_query(pipeline_value_sql, (), fetch_one=True)
        total_pipeline_value = pipeline_result['total_value'] if pipeline_result else 0

        # Build summary
        summary = {
            'new_proposals': len(new_proposals),
            'status_changes': len(status_changes),
            'stalled_proposals': len(stalled_proposals),
            'won_proposals': len(won_proposals),
            'total_pipeline_value': f"${total_pipeline_value / 1000000:.1f}M" if total_pipeline_value >= 1000000 else f"${total_pipeline_value:,.0f}"
        }

        return {
            'period': {
                'start_date': str(start_date),
                'end_date': str(end_date),
                'days': days
            },
            'summary': summary,
            'new_proposals': new_proposals,
            'status_changes': status_changes,
            'stalled_proposals': stalled_proposals,
            'won_proposals': won_proposals
        }
