"""
Proposal Tracker Service
Manages proposal tracking data, status updates, and reporting
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import sqlite3
from pathlib import Path
from .base_service import BaseService


class ProposalTrackerService(BaseService):
    """Service for managing proposal tracker operations"""

    def get_stats(self) -> Dict[str, Any]:
        """Get overall proposal tracker statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get overall stats from proposal_tracker (active tracking)
            # Pipeline = Only First Contact, Drafting, Proposal Sent (excludes On Hold, Contract Signed, etc)
            cursor.execute("""
                SELECT
                    COUNT(*) as total_proposals,
                    COALESCE(SUM(project_value), 0) as total_pipeline_value,
                    COALESCE(AVG(CAST(JULIANDAY('now') - JULIANDAY(status_changed_date) AS INTEGER)), 0) as avg_days_in_status
                FROM proposal_tracker
                WHERE is_active = 1
                    AND current_status IN ('First Contact', 'Drafting', 'Proposal Sent')
            """)
            stats = dict(cursor.fetchone())

            # Get status breakdown
            cursor.execute("""
                SELECT
                    current_status,
                    COUNT(*) as count,
                    COALESCE(SUM(project_value), 0) as total_value
                FROM proposal_tracker
                WHERE is_active = 1
                GROUP BY current_status
                ORDER BY
                    CASE current_status
                        WHEN 'Proposal Sent' THEN 1
                        WHEN 'Drafting' THEN 2
                        WHEN 'First Contact' THEN 3
                        WHEN 'On Hold' THEN 4
                        ELSE 5
                    END
            """)

            status_breakdown = []
            for row in cursor.fetchall():
                status_breakdown.append(dict(row))

            stats['status_breakdown'] = status_breakdown

            # Get proposals needing follow-up (>14 days in current status, not on hold)
            cursor.execute("""
                SELECT COUNT(*) as needs_followup
                FROM proposal_tracker
                WHERE is_active = 1
                AND CAST(JULIANDAY('now') - JULIANDAY(status_changed_date) AS INTEGER) > 14
                AND current_status != 'On Hold'
            """)
            stats['needs_followup'] = cursor.fetchone()['needs_followup']

            # COMPREHENSIVE STATS from proposals table (all proposals, not just tracked)
            # Total proposals (all time, all statuses)
            cursor.execute("""
                SELECT
                    COUNT(*) as all_proposals_total,
                    COALESCE(SUM(project_value), 0) as all_proposals_value
                FROM proposals
            """)
            all_proposals_row = dict(cursor.fetchone())
            stats['all_proposals_total'] = all_proposals_row['all_proposals_total']
            stats['all_proposals_value'] = all_proposals_row['all_proposals_value']

            # Active proposals (not lost/cancelled)
            cursor.execute("""
                SELECT
                    COUNT(*) as active_proposals_count,
                    COALESCE(SUM(project_value), 0) as active_proposals_value
                FROM proposals
                WHERE status NOT IN ('lost', 'cancelled')
            """)
            active_row = dict(cursor.fetchone())
            stats['active_proposals_count'] = active_row['active_proposals_count']
            stats['active_proposals_value'] = active_row['active_proposals_value']

            # Contracts signed in 2025
            cursor.execute("""
                SELECT
                    COUNT(*) as signed_2025_count,
                    COALESCE(SUM(project_value), 0) as signed_2025_value
                FROM proposals
                WHERE status = 'won'
                AND contract_signed_date >= '2025-01-01'
            """)
            signed_2025_row = dict(cursor.fetchone())
            stats['signed_2025_count'] = signed_2025_row['signed_2025_count']
            stats['signed_2025_value'] = signed_2025_row['signed_2025_value']

            # Proposals sent in 2025 (from proposals table for full history)
            cursor.execute("""
                SELECT
                    COUNT(*) as sent_2025_count,
                    COALESCE(SUM(project_value), 0) as sent_2025_value
                FROM proposals
                WHERE proposal_sent_date >= '2025-01-01'
            """)
            sent_2025_row = dict(cursor.fetchone())
            stats['sent_2025_count'] = sent_2025_row['sent_2025_count']
            stats['sent_2025_value'] = sent_2025_row['sent_2025_value']

            # Proposals sent in 2024
            cursor.execute("""
                SELECT
                    COUNT(*) as sent_2024_count,
                    COALESCE(SUM(project_value), 0) as sent_2024_value
                FROM proposals
                WHERE proposal_sent_date >= '2024-01-01'
                AND proposal_sent_date < '2025-01-01'
            """)
            sent_2024_row = dict(cursor.fetchone())
            stats['sent_2024_count'] = sent_2024_row['sent_2024_count']
            stats['sent_2024_value'] = sent_2024_row['sent_2024_value']

            return stats

    def get_proposals_list(
        self,
        status: Optional[str] = None,
        country: Optional[str] = None,
        search: Optional[str] = None,
        discipline: Optional[str] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """Get paginated list of proposals with filters"""

        # Build WHERE clauses
        where_clauses = ["pt.is_active = 1"]
        params = []

        if status:
            where_clauses.append("pt.current_status = ?")
            params.append(status)

        if country:
            where_clauses.append("pt.country = ?")
            params.append(country)

        if search:
            where_clauses.append("(pt.project_code LIKE ? OR pt.project_name LIKE ?)")
            search_term = f"%{search}%"
            params.extend([search_term, search_term])

        # Discipline filter - joins with proposals table
        if discipline:
            if discipline == 'landscape':
                where_clauses.append("p.is_landscape = 1")
            elif discipline == 'interior':
                where_clauses.append("p.is_interior = 1")
            elif discipline == 'architect':
                where_clauses.append("p.is_architect = 1")
            elif discipline == 'combined':
                # Combined = has 2+ disciplines
                where_clauses.append("(p.is_landscape + p.is_interior + p.is_architect) >= 2")

        where_sql = " AND ".join(where_clauses)

        # Get total count (with JOIN for discipline filter)
        count_sql = f"""
            SELECT COUNT(*) as total
            FROM proposal_tracker pt
            LEFT JOIN proposals p ON pt.project_code = p.project_code
            WHERE {where_sql}
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']

            # Get paginated data (with JOIN for discipline info)
            offset = (page - 1) * per_page
            data_sql = f"""
                SELECT
                    pt.id,
                    pt.project_code,
                    pt.project_name,
                    pt.project_value,
                    pt.country,
                    pt.current_status,
                    pt.last_week_status,
                    pt.status_changed_date,
                    CAST(JULIANDAY('now') - JULIANDAY(pt.status_changed_date) AS INTEGER) as days_in_current_status,
                    pt.first_contact_date,
                    pt.proposal_sent_date,
                    pt.proposal_sent,
                    pt.current_remark,
                    pt.latest_email_context,
                    pt.waiting_on,
                    pt.next_steps,
                    pt.last_email_date,
                    pt.updated_at,
                    COALESCE(p.is_landscape, 0) as is_landscape,
                    COALESCE(p.is_interior, 0) as is_interior,
                    COALESCE(p.is_architect, 0) as is_architect
                FROM proposal_tracker pt
                LEFT JOIN proposals p ON pt.project_code = p.project_code
                WHERE {where_sql}
                ORDER BY pt.project_code
                LIMIT ? OFFSET ?
            """

            cursor.execute(data_sql, params + [per_page, offset])
            proposals = [dict(row) for row in cursor.fetchall()]

            return {
                'proposals': proposals,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }

    def get_discipline_stats(self) -> Dict[str, Any]:
        """Get proposal counts and values by discipline"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get stats for each discipline
            cursor.execute("""
                SELECT
                    'landscape' as discipline,
                    COUNT(*) as count,
                    COALESCE(SUM(pt.project_value), 0) as total_value
                FROM proposal_tracker pt
                LEFT JOIN proposals p ON pt.project_code = p.project_code
                WHERE pt.is_active = 1 AND p.is_landscape = 1
                UNION ALL
                SELECT
                    'interior' as discipline,
                    COUNT(*) as count,
                    COALESCE(SUM(pt.project_value), 0) as total_value
                FROM proposal_tracker pt
                LEFT JOIN proposals p ON pt.project_code = p.project_code
                WHERE pt.is_active = 1 AND p.is_interior = 1
                UNION ALL
                SELECT
                    'architect' as discipline,
                    COUNT(*) as count,
                    COALESCE(SUM(pt.project_value), 0) as total_value
                FROM proposal_tracker pt
                LEFT JOIN proposals p ON pt.project_code = p.project_code
                WHERE pt.is_active = 1 AND p.is_architect = 1
                UNION ALL
                SELECT
                    'combined' as discipline,
                    COUNT(*) as count,
                    COALESCE(SUM(pt.project_value), 0) as total_value
                FROM proposal_tracker pt
                LEFT JOIN proposals p ON pt.project_code = p.project_code
                WHERE pt.is_active = 1 AND (p.is_landscape + p.is_interior + p.is_architect) >= 2
            """)

            disciplines = {}
            for row in cursor.fetchall():
                disciplines[row['discipline']] = {
                    'count': row['count'],
                    'total_value': row['total_value']
                }

            # Get all proposals count for "All Disciplines"
            cursor.execute("""
                SELECT COUNT(*) as count, COALESCE(SUM(project_value), 0) as total_value
                FROM proposal_tracker
                WHERE is_active = 1
            """)
            all_row = cursor.fetchone()
            disciplines['all'] = {
                'count': all_row['count'],
                'total_value': all_row['total_value']
            }

            return disciplines

    def get_proposal_by_code(self, project_code: str) -> Optional[Dict[str, Any]]:
        """Get single proposal by project code"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id,
                    project_code,
                    project_name,
                    project_value,
                    country,
                    current_status,
                    last_week_status,
                    status_changed_date,
                    CAST(JULIANDAY('now') - JULIANDAY(status_changed_date) AS INTEGER) as days_in_current_status,
                    first_contact_date,
                    proposal_sent_date,
                    proposal_sent,
                    current_remark,
                    project_summary,
                    latest_email_context,
                    waiting_on,
                    next_steps,
                    last_email_date,
                    last_email_id,
                    is_active,
                    created_at,
                    updated_at,
                    last_synced_at
                FROM proposal_tracker
                WHERE project_code = ?
            """, (project_code,))

            row = cursor.fetchone()
            return dict(row) if row else None

    def update_proposal(
        self,
        project_code: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update proposal fields"""

        allowed_fields = {
            'project_name', 'project_value', 'country',
            'current_status', 'current_remark', 'project_summary',
            'waiting_on', 'next_steps',
            'proposal_sent_date', 'first_contact_date',
            'proposal_sent',
            'contact_person', 'contact_email', 'contact_phone',
            'latest_email_context', 'last_email_date',
            # Provenance tracking fields
            'updated_by', 'source_type', 'change_reason'
        }

        # Filter to allowed fields
        update_fields = {k: v for k, v in updates.items() if k in allowed_fields}

        if not update_fields:
            return {'success': False, 'message': 'No valid fields to update'}

        # Check if status changed
        status_changed = 'current_status' in update_fields

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get current proposal
            current = self.get_proposal_by_code(project_code)
            if not current:
                return {'success': False, 'message': 'Proposal not found'}

            # If status changed, update status history fields
            if status_changed and update_fields['current_status'] != current['current_status']:
                update_fields['last_week_status'] = current['current_status']
                update_fields['status_changed_date'] = datetime.now().isoformat()

            # Always update updated_at
            update_fields['updated_at'] = datetime.now().isoformat()

            # Build UPDATE query
            set_clause = ', '.join([f"{k} = ?" for k in update_fields.keys()])
            values = list(update_fields.values()) + [project_code]

            sql = f"""
                UPDATE proposal_tracker
                SET {set_clause}
                WHERE project_code = ?
            """

            cursor.execute(sql, values)
            conn.commit()

            return {
                'success': True,
                'message': 'Proposal updated successfully',
                'updated_fields': list(update_fields.keys())
            }

    def get_status_history(self, project_code: str) -> List[Dict[str, Any]]:
        """Get status change history for a proposal"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id,
                    project_code,
                    old_status,
                    new_status,
                    changed_date,
                    changed_by,
                    source_email_id,
                    notes
                FROM proposal_status_history
                WHERE project_code = ?
                ORDER BY changed_date DESC
            """, (project_code,))

            return [dict(row) for row in cursor.fetchall()]

    def get_email_intelligence(
        self,
        project_code: str
    ) -> List[Dict[str, Any]]:
        """Get AI-extracted email intelligence for a proposal"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Query emails linked to this project with AI content
            cursor.execute("""
                SELECT
                    e.email_id,
                    e.subject as email_subject,
                    e.sender_email as email_from,
                    e.date as email_date,
                    e.snippet as email_snippet,
                    ec.category as ai_category,
                    ec.subcategory,
                    ec.key_points as key_information,
                    ec.ai_summary as action_items,
                    ec.sentiment as client_sentiment,
                    ec.importance_score as confidence_score,
                    ec.human_approved,
                    epl.project_code,
                    epl.confidence as link_confidence,
                    epl.link_method,
                    CASE
                        WHEN ec.action_required = 1 THEN 'Action Required'
                        WHEN ec.urgency_level = 'high' THEN 'High Priority'
                        ELSE NULL
                    END as status_update
                FROM emails e
                INNER JOIN email_project_links epl ON e.email_id = epl.email_id
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
                WHERE epl.project_code = ?
                ORDER BY e.date DESC
                LIMIT 20
            """, (project_code,))

            return [dict(row) for row in cursor.fetchall()]

    def get_countries_list(self) -> List[str]:
        """Get unique list of countries for filtering"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT country
                FROM proposal_tracker
                WHERE is_active = 1 AND country IS NOT NULL
                ORDER BY country
            """)

            return [row['country'] for row in cursor.fetchall()]

    def trigger_pdf_generation(self) -> Dict[str, Any]:
        """Trigger PDF report generation"""
        try:
            import subprocess
            from pathlib import Path

            script_path = Path(__file__).parent.parent.parent / "generate_weekly_proposal_report.py"

            result = subprocess.run(
                ['python3', str(script_path)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # Extract filename from output
                output = result.stdout
                if "Generated:" in output:
                    pdf_path = output.split("Generated:")[1].strip().split("\n")[0]
                    return {
                        'success': True,
                        'pdf_path': pdf_path,
                        'message': 'PDF generated successfully'
                    }

            return {
                'success': False,
                'message': f'PDF generation failed: {result.stderr}'
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error generating PDF: {str(e)}'
            }
