"""
Email Service

Handles all email-related operations:
- Email retrieval and filtering
- Categorization
- Email-proposal linking
- Email content analysis
"""

from typing import Optional, List, Dict, Any
from .base_service import BaseService


class EmailService(BaseService):
    """Service for email operations"""

    def get_all_emails(
        self,
        search_query: Optional[str] = None,
        category: Optional[str] = None,
        proposal_id: Optional[int] = None,
        page: int = 1,
        per_page: int = 20,
        sort_by: str = "date",
        sort_order: str = "DESC"
    ) -> Dict[str, Any]:
        """
        Get all emails with search, filtering, pagination, and sorting

        Args:
            search_query: Search in subject and sender fields
            category: Filter by category
            proposal_id: Filter by linked proposal
            page: Page number
            per_page: Results per page
            sort_by: Column to sort by (date, sender_email, subject)
            sort_order: ASC or DESC

        Returns:
            Paginated email results
        """
        sql = """
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.date,
                e.snippet,
                ec.category,
                ec.subcategory,
                ec.importance_score,
                ec.ai_summary,
                (
                    SELECT p.project_code
                    FROM email_proposal_links epl
                    JOIN proposals p ON epl.proposal_id = p.proposal_id
                    WHERE epl.email_id = e.email_id
                    ORDER BY epl.created_at DESC
                    LIMIT 1
                ) AS project_code,
                (
                    SELECT p.is_active_project
                    FROM email_proposal_links epl
                    JOIN proposals p ON epl.proposal_id = p.proposal_id
                    WHERE epl.email_id = e.email_id
                    ORDER BY epl.created_at DESC
                    LIMIT 1
                ) AS is_active_project
            FROM emails e
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE 1=1
        """
        params = []

        if search_query:
            sql += " AND (e.subject LIKE ? OR e.sender_email LIKE ?)"
            search_term = f"%{search_query}%"
            params.extend([search_term, search_term])

        if category:
            sql += " AND ec.category = ?"
            params.append(category)

        if proposal_id:
            sql += """ AND e.email_id IN (
                SELECT email_id FROM email_proposal_links WHERE proposal_id = ?
            )"""
            params.append(proposal_id)

        # Validate sort parameters to prevent SQL injection
        allowed_columns = ['date', 'sender_email', 'subject', 'email_id']
        validated_sort_by = self.validate_sort_column(sort_by, allowed_columns)
        validated_sort_order = self.validate_sort_order(sort_order)

        sql += f" ORDER BY e.{validated_sort_by} {validated_sort_order}"

        return self.paginate(sql, tuple(params), page, per_page)

    def get_email_by_id(self, email_id: int) -> Optional[Dict[str, Any]]:
        """Get email by ID with full content"""
        sql = """
            SELECT
                e.*,
                ec.clean_body,
                ec.category,
                ec.subcategory,
                ec.importance_score,
                ec.ai_summary,
                ec.sentiment,
                ec.entities
            FROM emails e
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE e.email_id = ?
        """
        return self.execute_query(sql, (email_id,), fetch_one=True)

    def get_emails_by_category(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get emails by category"""
        sql = """
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.date,
                ec.importance_score,
                ec.ai_summary
            FROM emails e
            JOIN email_content ec ON e.email_id = ec.email_id
            WHERE ec.category = ?
            ORDER BY e.date DESC
            LIMIT ?
        """
        return self.execute_query(sql, (category, limit))

    def get_categorized_count(self) -> Dict[str, int]:
        """Get count of emails by category"""
        sql = """
            SELECT
                category,
                COUNT(*) as count
            FROM email_content
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
        """
        results = self.execute_query(sql)

        # Convert to dict
        return {row['category']: row['count'] for row in results}

    def get_categories_list(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get structured list of all email categories with metadata including subcategories

        Returns:
            Dict with 'categories' list containing {value, label, count, subcategories, constraints}
        """
        sql = """
            SELECT
                category,
                COUNT(*) as count
            FROM email_content
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY category ASC
        """
        results = self.execute_query(sql)

        # Convert category codes to display labels
        label_map = {
            'contract': 'Contract',
            'invoice': 'Invoice',
            'design': 'Design',
            'rfi': 'RFI / Question',
            'schedule': 'Schedule',
            'meeting': 'Meeting',
            'general': 'General',
            'proposal': 'Proposal',
            'project_update': 'Project Update'
        }

        # Define subcategories for each category
        subcategories_map = {
            'contract': [
                {'value': 'proposal', 'label': 'Proposal Contract'},
                {'value': 'mou', 'label': 'Memorandum of Understanding'},
                {'value': 'nda', 'label': 'Non-Disclosure Agreement'},
                {'value': 'service', 'label': 'Service Agreement'},
                {'value': 'amendment', 'label': 'Contract Amendment'}
            ],
            'invoice': [
                {'value': 'initial', 'label': 'Initial Payment'},
                {'value': 'milestone', 'label': 'Milestone Payment'},
                {'value': 'final', 'label': 'Final Payment'},
                {'value': 'expense', 'label': 'Expense Reimbursement'}
            ],
            'design': [
                {'value': 'concept', 'label': 'Concept Design'},
                {'value': 'schematic', 'label': 'Schematic Design'},
                {'value': 'detail', 'label': 'Detail Design'},
                {'value': 'revision', 'label': 'Design Revision'},
                {'value': 'approval', 'label': 'Design Approval'}
            ],
            'meeting': [
                {'value': 'kickoff', 'label': 'Project Kickoff'},
                {'value': 'review', 'label': 'Design Review'},
                {'value': 'client', 'label': 'Client Meeting'},
                {'value': 'internal', 'label': 'Internal Team Meeting'}
            ]
        }

        # Define constraints for specific categories
        constraints_map = {
            'rfi': {
                'active_projects_only': True,
                'description': 'RFIs can only be assigned to emails linked to active projects'
            }
        }

        categories = []
        for row in results:
            category_value = row['category']
            category_data = {
                'value': category_value,
                'label': label_map.get(category_value, category_value.title()),
                'count': row['count'],
                'subcategories': subcategories_map.get(category_value, [])
            }

            # Add constraints if they exist for this category
            if category_value in constraints_map:
                category_data['constraints'] = constraints_map[category_value]

            categories.append(category_data)

        return {'categories': categories}

    def get_emails_for_proposal(self, project_code: str) -> List[Dict[str, Any]]:
        """Get all emails linked to a proposal"""
        sql = """
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.date,
                e.snippet,
                ec.category,
                ec.importance_score,
                epl.confidence_score
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            JOIN proposals p ON epl.proposal_id = p.proposal_id
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE p.project_code = ?
            ORDER BY e.date DESC
        """
        return self.execute_query(sql, (project_code,))

    def get_unprocessed_emails(self) -> List[Dict[str, Any]]:
        """Get emails that haven't been AI-processed yet"""
        sql = """
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.date
            FROM emails e
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE ec.email_id IS NULL
            AND e.body_full IS NOT NULL
            ORDER BY e.date DESC
        """
        return self.execute_query(sql)

    def search_emails(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search emails by subject or sender

        Args:
            query: Search term
            limit: Max results

        Returns:
            List of matching emails
        """
        sql = """
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.date,
                e.snippet
            FROM emails e
            WHERE e.subject LIKE ? OR e.sender_email LIKE ?
            ORDER BY e.date DESC
            LIMIT ?
        """
        search_term = f"%{query}%"
        return self.execute_query(sql, (search_term, search_term, limit))

    def get_email_stats(self) -> Dict[str, Any]:
        """Get email statistics"""
        stats = {}

        stats['total_emails'] = self.count_rows('emails')
        stats['processed'] = self.count_rows('email_content')
        stats['unprocessed'] = stats['total_emails'] - stats['processed']
        stats['with_full_body'] = self.count_rows('emails', 'body_full IS NOT NULL')
        stats['linked_to_proposals'] = self.count_rows('email_proposal_links')

        return stats

    def update_email_category(
        self,
        email_id: int,
        new_category: str,
        feedback: Optional[str] = None,
        subcategory: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update the category for an email and log human feedback

        Args:
            email_id: Target email ID
            new_category: Correct category label
            feedback: Optional reviewer comment

        Returns:
            Updated email metadata or None if email not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    e.email_id,
                    e.subject,
                    e.sender_email,
                    e.snippet,
                    e.body_full,
                    ec.clean_body,
                    ec.category AS previous_category
                FROM emails e
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
                WHERE e.email_id = ?
            """, (email_id,))
            row = cursor.fetchone()

            if row is None:
                return None

            previous_category = row["previous_category"]

            # Ensure email_content row exists
            cursor.execute(
                "SELECT content_id FROM email_content WHERE email_id = ?",
                (email_id,)
            )
            content_row = cursor.fetchone()

            if content_row:
                cursor.execute(
                    "UPDATE email_content SET category = ?, subcategory = ? WHERE email_id = ?",
                    (new_category, subcategory, email_id)
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO email_content (
                        email_id,
                        category,
                        subcategory,
                        importance_score,
                        ai_summary
                    ) VALUES (?, ?, ?, 0.5, '')
                    """,
                    (email_id, new_category, subcategory)
                )

            # Insert into training_data for future fine-tuning
            body_text = row["clean_body"] or row["body_full"] or row["snippet"] or ""
            input_payload = (
                f"Subject: {row['subject'] or ''}\n"
                f"Sender: {row['sender_email'] or ''}\n"
                f"Body: {body_text[:2000]}"
            )

            cursor.execute(
                """
                INSERT INTO training_data (
                    task_type,
                    input_data,
                    output_data,
                    model_used,
                    confidence,
                    human_verified,
                    feedback
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "categorize_email",
                    input_payload,
                    new_category,
                    "human_supervision",
                    1.0,
                    1,
                    feedback or previous_category or ""
                )
            )

            conn.commit()

            return {
                "email_id": row["email_id"],
                "subject": row["subject"],
                "sender_email": row["sender_email"],
                "category": new_category,
                "subcategory": subcategory,
                "previous_category": previous_category,
                "feedback": feedback
            }
