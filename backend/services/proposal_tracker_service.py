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
        """Get overall proposal tracker statistics - queries from proposals table (source of truth)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Active pipeline stats (excludes Lost, Declined, Dormant, Contract Signed)
            cursor.execute("""
                SELECT
                    COUNT(*) as total_proposals,
                    COALESCE(SUM(project_value), 0) as total_pipeline_value,
                    COALESCE(AVG(CAST(JULIANDAY('now') - JULIANDAY(COALESCE(updated_at, created_at)) AS INTEGER)), 0) as avg_days_in_status
                FROM proposals
                WHERE status IN ('First Contact', 'Meeting Held', 'NDA Signed', 'Proposal Prep', 'Proposal Sent', 'Negotiation')
            """)
            stats = dict(cursor.fetchone())

            # Get status breakdown from proposals table
            cursor.execute("""
                SELECT
                    status as current_status,
                    COUNT(*) as count,
                    COALESCE(SUM(project_value), 0) as total_value
                FROM proposals
                WHERE status IS NOT NULL AND status != ''
                GROUP BY status
                ORDER BY
                    CASE status
                        WHEN 'First Contact' THEN 1
                        WHEN 'Meeting Held' THEN 2
                        WHEN 'NDA Signed' THEN 3
                        WHEN 'Proposal Prep' THEN 4
                        WHEN 'Proposal Sent' THEN 5
                        WHEN 'Negotiation' THEN 6
                        WHEN 'On Hold' THEN 7
                        WHEN 'Contract Signed' THEN 8
                        WHEN 'Lost' THEN 9
                        WHEN 'Declined' THEN 10
                        WHEN 'Dormant' THEN 11
                        ELSE 12
                    END
            """)

            status_breakdown = []
            for row in cursor.fetchall():
                status_breakdown.append(dict(row))

            stats['status_breakdown'] = status_breakdown

            # Proposals needing follow-up (>14 days since update, still active)
            cursor.execute("""
                SELECT COUNT(*) as needs_followup
                FROM proposals
                WHERE CAST(JULIANDAY('now') - JULIANDAY(COALESCE(updated_at, created_at)) AS INTEGER) > 14
                AND status NOT IN ('Contract Signed', 'Lost', 'Declined', 'Dormant', 'On Hold')
            """)
            stats['needs_followup'] = cursor.fetchone()['needs_followup']

            # COMPREHENSIVE STATS from proposals table
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

            # Active proposals (not closed - excludes won, lost, declined, dormant)
            cursor.execute("""
                SELECT
                    COUNT(*) as active_proposals_count,
                    COALESCE(SUM(project_value), 0) as active_proposals_value
                FROM proposals
                WHERE status NOT IN ('Contract Signed', 'Lost', 'Declined', 'Dormant', 'Cancelled')
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
                WHERE status = 'Contract Signed'
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

            # Won (Contract Signed) - all time
            cursor.execute("""
                SELECT
                    COUNT(*) as won_count,
                    COALESCE(SUM(project_value), 0) as won_value
                FROM proposals
                WHERE status = 'Contract Signed'
            """)
            won_row = dict(cursor.fetchone())
            stats['won_count'] = won_row['won_count']
            stats['won_value'] = won_row['won_value']

            # Lost/Declined - all time
            cursor.execute("""
                SELECT
                    COUNT(*) as lost_count,
                    COALESCE(SUM(project_value), 0) as lost_value
                FROM proposals
                WHERE status IN ('Lost', 'Declined')
            """)
            lost_row = dict(cursor.fetchone())
            stats['lost_count'] = lost_row['lost_count']
            stats['lost_value'] = lost_row['lost_value']

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
        """Get paginated list of proposals with filters - queries from proposals table (source of truth)"""

        # Build WHERE clauses - query from proposals table directly
        where_clauses = ["1=1"]  # Always true base
        params = []

        if status:
            # Handle "Lost" as a group filter (includes Lost + Declined)
            if status == "Lost":
                where_clauses.append("p.status IN ('Lost', 'Declined')")
            else:
                where_clauses.append("p.status = ?")
                params.append(status)

        if search:
            where_clauses.append("(p.project_code LIKE ? OR p.project_name LIKE ?)")
            search_term = f"%{search}%"
            params.extend([search_term, search_term])

        # Discipline filter
        if discipline:
            if discipline == 'landscape':
                where_clauses.append("p.is_landscape = 1")
            elif discipline == 'interior':
                where_clauses.append("p.is_interior = 1")
            elif discipline == 'architect':
                where_clauses.append("p.is_architect = 1")
            elif discipline == 'combined':
                where_clauses.append("(p.is_landscape + p.is_interior + p.is_architect) >= 2")

        where_sql = " AND ".join(where_clauses)

        # Get total count
        count_sql = f"""
            SELECT COUNT(*) as total
            FROM proposals p
            WHERE {where_sql}
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']

            # Get paginated data from proposals + email stats (NO proposal_tracker - it's stale)
            offset = (page - 1) * per_page
            data_sql = f"""
                SELECT
                    p.proposal_id as id,
                    p.project_code,
                    p.project_name,
                    p.project_value,
                    COALESCE(p.country, '') as country,
                    p.status as current_status,
                    '' as last_week_status,
                    -- Use status-appropriate date for when we entered this status
                    CASE
                        WHEN p.status = 'Proposal Sent' THEN COALESCE(p.proposal_sent_date, p.updated_at)
                        WHEN p.status = 'First Contact' THEN COALESCE(p.first_contact_date, email_stats.first_email_date, p.created_at)
                        WHEN p.status = 'Contract Signed' THEN COALESCE(p.contract_signed_date, p.updated_at)
                        ELSE p.updated_at
                    END as status_changed_date,
                    -- Days in status calculated from actual evidence dates
                    CAST(JULIANDAY('now') - JULIANDAY(
                        CASE
                            WHEN p.status = 'Proposal Sent' THEN COALESCE(p.proposal_sent_date, p.updated_at)
                            WHEN p.status = 'First Contact' THEN COALESCE(p.first_contact_date, email_stats.first_email_date, p.created_at)
                            WHEN p.status = 'Contract Signed' THEN COALESCE(p.contract_signed_date, p.updated_at)
                            ELSE p.updated_at
                        END
                    ) AS INTEGER) as days_in_current_status,
                    COALESCE(p.first_contact_date, email_stats.first_email_date, p.created_at) as first_contact_date,
                    COALESCE(p.proposal_sent_date, '') as proposal_sent_date,
                    CASE WHEN p.proposal_sent_date IS NOT NULL THEN 1 ELSE 0 END as proposal_sent,
                    COALESCE(p.remarks, p.status_notes, p.correspondence_summary, '') as current_remark,
                    '' as latest_email_context,
                    COALESCE(p.waiting_for, '') as waiting_on,
                    COALESCE(p.next_action, '') as next_steps,
                    p.action_owner,
                    p.next_action_date,
                    COALESCE(email_stats.last_email_date, '') as last_email_date,
                    COALESCE(email_stats.email_count, 0) as email_count,
                    COALESCE(email_stats.first_email_date, '') as first_email_date,
                    p.updated_at,
                    COALESCE(p.is_landscape, 0) as is_landscape,
                    COALESCE(p.is_interior, 0) as is_interior,
                    COALESCE(p.is_architect, 0) as is_architect,
                    p.client_company,
                    p.contact_person,
                    p.last_contact_date,
                    p.days_since_contact,
                    COALESCE(p.ball_in_court, '') as ball_in_court,
                    COALESCE(p.waiting_for, '') as waiting_for
                FROM proposals p
                LEFT JOIN (
                    SELECT
                        epl.proposal_id,
                        COUNT(*) as email_count,
                        MAX(e.date) as last_email_date,
                        MIN(e.date) as first_email_date
                    FROM email_proposal_links epl
                    JOIN emails e ON epl.email_id = e.email_id
                    GROUP BY epl.proposal_id
                ) email_stats ON p.proposal_id = email_stats.proposal_id
                WHERE {where_sql}
                ORDER BY p.project_code DESC
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
        """Get proposal counts and values by discipline - from proposals table"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Active status filter
            active_filter = "status NOT IN ('Contract Signed', 'Lost', 'Declined', 'Dormant', 'Cancelled')"

            # Get stats for each discipline from proposals table directly
            cursor.execute(f"""
                SELECT
                    'landscape' as discipline,
                    COUNT(*) as count,
                    COALESCE(SUM(project_value), 0) as total_value
                FROM proposals
                WHERE {active_filter} AND is_landscape = 1
                UNION ALL
                SELECT
                    'interior' as discipline,
                    COUNT(*) as count,
                    COALESCE(SUM(project_value), 0) as total_value
                FROM proposals
                WHERE {active_filter} AND is_interior = 1
                UNION ALL
                SELECT
                    'architect' as discipline,
                    COUNT(*) as count,
                    COALESCE(SUM(project_value), 0) as total_value
                FROM proposals
                WHERE {active_filter} AND is_architect = 1
                UNION ALL
                SELECT
                    'combined' as discipline,
                    COUNT(*) as count,
                    COALESCE(SUM(project_value), 0) as total_value
                FROM proposals
                WHERE {active_filter} AND (COALESCE(is_landscape, 0) + COALESCE(is_interior, 0) + COALESCE(is_architect, 0)) >= 2
            """)

            disciplines = {}
            for row in cursor.fetchall():
                disciplines[row['discipline']] = {
                    'count': row['count'],
                    'total_value': row['total_value']
                }

            # Get all active proposals count for "All Disciplines"
            cursor.execute(f"""
                SELECT COUNT(*) as count, COALESCE(SUM(project_value), 0) as total_value
                FROM proposals
                WHERE {active_filter}
            """)
            all_row = cursor.fetchone()
            disciplines['all'] = {
                'count': all_row['count'],
                'total_value': all_row['total_value']
            }

            return disciplines

    def get_proposal_by_code(self, project_code: str) -> Optional[Dict[str, Any]]:
        """Get single proposal by project code - queries proposals table (source of truth)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    p.proposal_id as id,
                    p.project_code,
                    p.project_name,
                    p.project_value,
                    COALESCE(p.country, '') as country,
                    p.status as current_status,
                    '' as last_week_status,
                    -- Use status-appropriate date
                    CASE
                        WHEN p.status = 'Proposal Sent' THEN COALESCE(p.proposal_sent_date, p.updated_at)
                        WHEN p.status = 'First Contact' THEN COALESCE(p.first_contact_date, email_stats.first_email_date, p.created_at)
                        WHEN p.status = 'Contract Signed' THEN COALESCE(p.contract_signed_date, p.updated_at)
                        ELSE p.updated_at
                    END as status_changed_date,
                    CAST(JULIANDAY('now') - JULIANDAY(
                        CASE
                            WHEN p.status = 'Proposal Sent' THEN COALESCE(p.proposal_sent_date, p.updated_at)
                            WHEN p.status = 'First Contact' THEN COALESCE(p.first_contact_date, email_stats.first_email_date, p.created_at)
                            WHEN p.status = 'Contract Signed' THEN COALESCE(p.contract_signed_date, p.updated_at)
                            ELSE p.updated_at
                        END
                    ) AS INTEGER) as days_in_current_status,
                    COALESCE(p.first_contact_date, email_stats.first_email_date, p.created_at) as first_contact_date,
                    COALESCE(p.proposal_sent_date, '') as proposal_sent_date,
                    CASE WHEN p.proposal_sent_date IS NOT NULL THEN 1 ELSE 0 END as proposal_sent,
                    COALESCE(p.remarks, p.status_notes, p.correspondence_summary, '') as current_remark,
                    COALESCE(p.scope_summary, '') as project_summary,
                    '' as latest_email_context,
                    COALESCE(p.waiting_for, '') as waiting_on,
                    COALESCE(p.next_action, '') as next_steps,
                    p.action_owner,
                    p.next_action_date,
                    COALESCE(email_stats.last_email_date, '') as last_email_date,
                    COALESCE(email_stats.email_count, 0) as email_count,
                    COALESCE(email_stats.first_email_date, '') as first_email_date,
                    0 as last_email_id,
                    1 as is_active,
                    p.created_at,
                    p.updated_at,
                    p.updated_at as last_synced_at,
                    COALESCE(p.is_landscape, 0) as is_landscape,
                    COALESCE(p.is_interior, 0) as is_interior,
                    COALESCE(p.is_architect, 0) as is_architect,
                    p.client_company,
                    p.contact_person,
                    p.contact_email,
                    p.contact_phone,
                    p.last_contact_date,
                    p.days_since_contact,
                    p.health_score,
                    p.win_probability
                FROM proposals p
                LEFT JOIN (
                    SELECT
                        epl.proposal_id,
                        COUNT(*) as email_count,
                        MAX(e.date) as last_email_date,
                        MIN(e.date) as first_email_date
                    FROM email_proposal_links epl
                    JOIN emails e ON epl.email_id = e.email_id
                    GROUP BY epl.proposal_id
                ) email_stats ON p.proposal_id = email_stats.proposal_id
                WHERE p.project_code = ?
            """, (project_code,))

            row = cursor.fetchone()
            return dict(row) if row else None

    def update_proposal(
        self,
        project_code: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update proposal fields - writes to proposals table (source of truth)"""

        # Map tracker field names to proposals table field names
        field_mapping = {
            'current_status': 'status',
            'current_remark': 'remarks',
            'project_summary': 'scope_summary',
            'waiting_on': 'waiting_for',
            'next_steps': 'next_action',
        }

        allowed_fields = {
            'project_name', 'project_value', 'country',
            'current_status', 'current_remark', 'project_summary',
            'waiting_on', 'next_steps',
            'proposal_sent_date', 'first_contact_date',
            'contact_person', 'contact_email', 'contact_phone',
            'ball_in_court', 'waiting_for', 'remarks', 'status',
            # Action tracking (Issue #95)
            'action_owner', 'action_source', 'next_action', 'next_action_date',
        }

        # Filter to allowed fields
        update_fields = {k: v for k, v in updates.items() if k in allowed_fields}

        if not update_fields:
            return {'success': False, 'message': 'No valid fields to update'}

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get current proposal
            current = self.get_proposal_by_code(project_code)
            if not current:
                return {'success': False, 'message': 'Proposal not found'}

            # Always update updated_at
            update_fields['updated_at'] = datetime.now().isoformat()

            # Map field names for proposals table
            db_fields = {}
            for k, v in update_fields.items():
                db_key = field_mapping.get(k, k)
                db_fields[db_key] = v

            # Build UPDATE query for proposals table
            set_clause = ', '.join([f"{k} = ?" for k in db_fields.keys()])
            values = list(db_fields.values()) + [project_code]

            sql = f"""
                UPDATE proposals
                SET {set_clause}
                WHERE project_code = ?
            """

            cursor.execute(sql, values)
            conn.commit()

            return {
                'success': True,
                'message': 'Proposal updated successfully',
                'updated_fields': list(db_fields.keys())
            }

    def get_status_history(self, project_code: str) -> List[Dict[str, Any]]:
        """Get status change history for a proposal"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    history_id as id,
                    project_code,
                    old_status,
                    new_status,
                    status_date,
                    changed_by,
                    source,
                    notes
                FROM proposal_status_history
                WHERE project_code = ?
                ORDER BY status_date DESC
            """, (project_code,))

            return [dict(row) for row in cursor.fetchall()]

    def get_email_intelligence(
        self,
        project_code: str
    ) -> List[Dict[str, Any]]:
        """Get AI-extracted email intelligence for a proposal"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Query emails linked to this proposal with AI content
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
                    p.project_code,
                    epl.confidence_score as link_confidence,
                    epl.match_method as link_method,
                    CASE
                        WHEN ec.action_required = 1 THEN 'Action Required'
                        WHEN ec.urgency_level = 'high' THEN 'High Priority'
                        ELSE NULL
                    END as status_update
                FROM emails e
                INNER JOIN email_proposal_links epl ON e.email_id = epl.email_id
                INNER JOIN proposals p ON epl.proposal_id = p.proposal_id
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
                WHERE p.project_code = ?
                ORDER BY e.date DESC
            """, (project_code,))

            return [dict(row) for row in cursor.fetchall()]

    def get_countries_list(self) -> List[str]:
        """Get unique list of countries for filtering - from proposals table"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT country
                FROM proposals
                WHERE country IS NOT NULL AND country != ''
                AND status NOT IN ('Contract Signed', 'Lost', 'Declined', 'Dormant', 'Cancelled')
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
