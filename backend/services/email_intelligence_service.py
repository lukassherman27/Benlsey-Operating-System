"""
Email Intelligence Service - Validation, Linking, Timeline

Handles:
- Validation queue (unlinked emails, low confidence links)
- Email details with AI insights
- Email link management with RLHF training
- Project email timeline
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from .base_service import BaseService
from .training_data_service import TrainingDataService


class EmailIntelligenceService(BaseService):
    """Service for email intelligence and validation operations"""

    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.training_service = TrainingDataService(db_path)

    # ============================================================================
    # VALIDATION QUEUE
    # ============================================================================

    def get_validation_queue(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get emails needing validation

        Priority levels:
        - high: Unlinked emails with attachments (potential contracts!)
        - medium: Low confidence links (<70%)
        - low: Medium confidence links (70-85%)

        Args:
            status: 'unlinked', 'low_confidence', 'all'
            priority: 'high', 'medium', 'low', 'all'
            limit: Max results

        Returns:
            Dict with emails and counts
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            emails = []

            if status == "unlinked":
                # Emails with no project OR proposal link
                cursor.execute("""
                    SELECT
                        e.email_id,
                        e.subject,
                        e.sender_email,
                        e.sender_name,
                        e.date,
                        e.date_normalized,
                        e.has_attachments,
                        ec.category,
                        e.snippet,
                        ec.ai_summary,
                        ec.sentiment,
                        ec.urgency_level,
                        (SELECT COUNT(*) FROM email_attachments ea WHERE ea.email_id = e.email_id) as attachment_count
                    FROM emails e
                    LEFT JOIN email_project_links eprl ON e.email_id = eprl.email_id
                    LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
                    LEFT JOIN email_content ec ON e.email_id = ec.email_id
                    WHERE eprl.email_id IS NULL AND epl.email_id IS NULL
                    ORDER BY e.has_attachments DESC, e.date DESC
                    LIMIT ?
                """, (limit,))

            elif status == "low_confidence":
                # Emails with AI links below 70% confidence
                cursor.execute("""
                    SELECT
                        e.email_id,
                        e.subject,
                        e.sender_email,
                        e.sender_name,
                        e.date,
                        e.date_normalized,
                        e.has_attachments,
                        ec.category,
                        e.snippet,
                        ec.ai_summary,
                        ec.sentiment,
                        ec.urgency_level,
                        epl.project_code,
                        p.project_title as project_name,
                        epl.confidence,
                        epl.link_method,
                        epl.evidence,
                        (SELECT COUNT(*) FROM email_attachments ea WHERE ea.email_id = e.email_id) as attachment_count
                    FROM emails e
                    INNER JOIN email_project_links epl ON e.email_id = epl.email_id
                    LEFT JOIN projects p ON epl.project_code = p.project_code
                    LEFT JOIN email_content ec ON e.email_id = ec.email_id
                    WHERE epl.confidence < 0.70
                    ORDER BY epl.confidence ASC, e.date DESC
                    LIMIT ?
                """, (limit,))

            else:  # all
                cursor.execute("""
                    SELECT
                        e.email_id,
                        e.subject,
                        e.sender_email,
                        e.sender_name,
                        e.date,
                        e.date_normalized,
                        e.has_attachments,
                        ec.category,
                        e.snippet,
                        ec.ai_summary,
                        ec.sentiment,
                        ec.urgency_level,
                        epl.project_code,
                        p.project_title as project_name,
                        epl.confidence,
                        epl.link_method,
                        (SELECT COUNT(*) FROM email_attachments ea WHERE ea.email_id = e.email_id) as attachment_count
                    FROM emails e
                    LEFT JOIN email_project_links epl ON e.email_id = epl.email_id
                    LEFT JOIN projects p ON epl.project_code = p.project_code
                    LEFT JOIN email_content ec ON e.email_id = ec.email_id
                    ORDER BY e.date DESC
                    LIMIT ?
                """, (limit,))

            columns = [desc[0] for desc in cursor.description]
            emails = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Get counts for summary - check BOTH link tables
            cursor.execute("""
                SELECT COUNT(*) as unlinked
                FROM emails e
                LEFT JOIN email_project_links eprl ON e.email_id = eprl.email_id
                LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
                WHERE eprl.email_id IS NULL AND epl.email_id IS NULL
            """)
            unlinked_count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) as low_conf
                FROM (
                    SELECT email_id, confidence_score as confidence FROM email_proposal_links
                    UNION ALL
                    SELECT email_id, confidence FROM email_project_links
                )
                WHERE confidence < 0.70
            """)
            low_conf_count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(DISTINCT email_id) as total_linked
                FROM (
                    SELECT email_id FROM email_proposal_links
                    UNION
                    SELECT email_id FROM email_project_links
                )
            """)
            total_linked = cursor.fetchone()[0]

            return {
                "success": True,
                "counts": {
                    "unlinked": unlinked_count,
                    "low_confidence": low_conf_count,
                    "total_linked": total_linked,
                    "returned": len(emails)
                },
                "emails": emails
            }

    # ============================================================================
    # EMAIL DETAILS
    # ============================================================================

    def get_email_details(self, email_id: int) -> Dict[str, Any]:
        """
        Get complete email details including:
        - Basic email data
        - Current project link (if exists)
        - AI insights from email_content
        - Attachments
        - Thread information
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get email basics with project link
            cursor.execute("""
                SELECT
                    e.*,
                    epl.project_code,
                    p.project_title as project_name,
                    epl.confidence,
                    epl.link_method,
                    epl.evidence
                FROM emails e
                LEFT JOIN email_project_links epl ON e.email_id = epl.email_id
                LEFT JOIN projects p ON epl.project_code = p.project_code
                WHERE e.email_id = ?
            """, (email_id,))

            row = cursor.fetchone()
            if not row:
                return {"success": False, "error": "Email not found"}

            columns = [desc[0] for desc in cursor.description]
            email = dict(zip(columns, row))

            # Get AI insights
            cursor.execute("""
                SELECT
                    category,
                    subcategory,
                    key_points,
                    sentiment,
                    client_sentiment,
                    urgency_level,
                    action_required,
                    ai_summary,
                    importance_score,
                    entities
                FROM email_content
                WHERE email_id = ?
            """, (email_id,))

            content_row = cursor.fetchone()
            if content_row:
                content_columns = [desc[0] for desc in cursor.description]
                email['ai_insights'] = dict(zip(content_columns, content_row))
            else:
                email['ai_insights'] = None

            # Get attachments
            cursor.execute("""
                SELECT
                    attachment_id,
                    filename,
                    filesize,
                    mime_type,
                    document_type,
                    is_signed,
                    is_executed,
                    ai_summary
                FROM email_attachments
                WHERE email_id = ?
            """, (email_id,))

            att_columns = [desc[0] for desc in cursor.description]
            email['attachments'] = [dict(zip(att_columns, row)) for row in cursor.fetchall()]

            # Get thread info
            cursor.execute("""
                SELECT
                    thread_id,
                    subject_normalized,
                    message_count,
                    status,
                    first_email_date,
                    last_email_date
                FROM email_threads
                WHERE emails LIKE '%' || ? || '%'
            """, (str(email_id),))

            thread_row = cursor.fetchone()
            if thread_row:
                thread_columns = [desc[0] for desc in cursor.description]
                email['thread'] = dict(zip(thread_columns, thread_row))
            else:
                email['thread'] = None

            return {"success": True, "email": email}

    # ============================================================================
    # LINK MANAGEMENT
    # ============================================================================

    def update_email_link(
        self,
        email_id: int,
        project_code: str,
        reason: str,
        updated_by: str = "bill"
    ) -> Dict[str, Any]:
        """
        Update email's project link

        This does 3 things:
        1. Updates email_project_links
        2. Logs to training_data (RLHF!)
        3. Returns success
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                # Get current link (if exists)
                cursor.execute("""
                    SELECT project_code, confidence
                    FROM email_project_links
                    WHERE email_id = ?
                """, (email_id,))

                current = cursor.fetchone()
                old_project_code = current[0] if current else None

                # Get project_id from project_code
                cursor.execute("""
                    SELECT project_id FROM projects WHERE project_code = ?
                """, (project_code,))

                project = cursor.fetchone()
                if not project:
                    return {"success": False, "error": f"Project {project_code} not found"}

                project_id = project[0]

                # Delete old link if exists
                if current:
                    cursor.execute("""
                        DELETE FROM email_project_links
                        WHERE email_id = ?
                    """, (email_id,))

                # Insert new link
                cursor.execute("""
                    INSERT INTO email_project_links
                    (email_id, project_id, project_code, confidence, link_method, evidence, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                """, (email_id, project_id, project_code, 1.0, 'manual', reason))

                conn.commit()

                # Log to training_data for RLHF
                try:
                    self.training_service.log_feedback(
                        feature_type='email_project_linking',
                        feature_id=str(email_id),
                        helpful=False,  # AI was wrong
                        issue_type='incorrect_project',
                        feedback_text=reason,
                        expected_value=project_code,
                        current_value=old_project_code or 'unlinked',
                        context={
                            'email_id': email_id,
                            'old_project': old_project_code,
                            'new_project': project_code,
                            'updated_by': updated_by
                        }
                    )
                except Exception as e:
                    # Don't fail the main operation if training log fails
                    pass

                return {
                    "success": True,
                    "message": f"Email linked to {project_code}",
                    "training_logged": True
                }

            except Exception as e:
                conn.rollback()
                return {"success": False, "error": str(e)}

    def confirm_email_link(
        self,
        email_id: int,
        confirmed_by: str = "bill"
    ) -> Dict[str, Any]:
        """
        Confirm AI link is correct

        This:
        1. Sets confidence to 1.0
        2. Logs positive feedback to training_data
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                # Get current link
                cursor.execute("""
                    SELECT project_code, confidence, link_method
                    FROM email_project_links
                    WHERE email_id = ?
                """, (email_id,))

                link = cursor.fetchone()
                if not link:
                    return {"success": False, "error": "No link found for this email"}

                project_code, original_confidence, link_method = link

                # Update confidence to 1.0
                cursor.execute("""
                    UPDATE email_project_links
                    SET confidence = 1.0
                    WHERE email_id = ?
                """, (email_id,))

                conn.commit()

                # Log positive feedback
                try:
                    self.training_service.log_feedback(
                        feature_type='email_project_linking',
                        feature_id=str(email_id),
                        helpful=True,  # AI was correct!
                        feedback_text="Link confirmed by user",
                        current_value=project_code,
                        context={
                            'email_id': email_id,
                            'project_code': project_code,
                            'original_confidence': original_confidence,
                            'confirmed_by': confirmed_by
                        }
                    )
                except Exception as e:
                    pass

                return {
                    "success": True,
                    "message": "Link confirmed",
                    "training_logged": True
                }

            except Exception as e:
                conn.rollback()
                return {"success": False, "error": str(e)}

    def unlink_email(
        self,
        email_id: int,
        reason: str,
        updated_by: str = "bill"
    ) -> Dict[str, Any]:
        """
        Remove project link from email

        Logs to training_data that AI was wrong
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                # Get current link
                cursor.execute("""
                    SELECT project_code
                    FROM email_project_links
                    WHERE email_id = ?
                """, (email_id,))

                link = cursor.fetchone()
                if not link:
                    return {"success": False, "error": "No link to remove"}

                old_project = link[0]

                # Delete link
                cursor.execute("""
                    DELETE FROM email_project_links
                    WHERE email_id = ?
                """, (email_id,))

                conn.commit()

                # Log to training_data
                try:
                    self.training_service.log_feedback(
                        feature_type='email_project_linking',
                        feature_id=str(email_id),
                        helpful=False,
                        issue_type='wrong_project',
                        feedback_text=reason,
                        current_value=old_project,
                        expected_value='unlinked',
                        context={
                            'email_id': email_id,
                            'removed_project': old_project,
                            'updated_by': updated_by
                        }
                    )
                except Exception as e:
                    pass

                return {
                    "success": True,
                    "message": "Email unlinked",
                    "training_logged": True
                }

            except Exception as e:
                conn.rollback()
                return {"success": False, "error": str(e)}

    # ============================================================================
    # PROJECT EMAIL TIMELINE
    # ============================================================================

    def get_project_email_timeline(
        self,
        project_code: str,
        include_attachments: bool = True,
        include_threads: bool = True
    ) -> Dict[str, Any]:
        """
        Get complete email history for a project

        Returns:
        - All emails linked to this project
        - Sorted chronologically
        - With AI summaries, key points
        - Attachments
        - Thread grouping
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get project info
            cursor.execute("""
                SELECT project_code, project_title, total_fee_usd, status
                FROM projects
                WHERE project_code = ?
            """, (project_code,))

            project_row = cursor.fetchone()
            if not project_row:
                return {"success": False, "error": f"Project {project_code} not found"}

            project = {
                "code": project_row[0],
                "name": project_row[1],
                "project_value": project_row[2],
                "status": project_row[3]
            }

            # Get all emails for this project
            cursor.execute("""
                SELECT
                    e.email_id,
                    e.subject,
                    e.sender_email,
                    e.sender_name,
                    e.date,
                    e.date_normalized,
                    e.snippet,
                    e.thread_id,
                    e.has_attachments,
                    ec.category,
                    ec.subcategory,
                    ec.ai_summary,
                    ec.key_points,
                    ec.sentiment,
                    ec.urgency_level,
                    ec.action_required,
                    epl.confidence,
                    epl.link_method
                FROM emails e
                INNER JOIN email_project_links epl ON e.email_id = epl.email_id
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
                WHERE epl.project_code = ?
                ORDER BY e.date DESC
            """, (project_code,))

            columns = [desc[0] for desc in cursor.description]
            emails = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Get attachments if requested
            if include_attachments and emails:
                email_ids = [e['email_id'] for e in emails]
                placeholders = ','.join('?' * len(email_ids))

                cursor.execute(f"""
                    SELECT
                        attachment_id,
                        email_id,
                        filename,
                        filesize,
                        document_type,
                        is_signed,
                        is_executed
                    FROM email_attachments
                    WHERE email_id IN ({placeholders})
                """, email_ids)

                att_columns = [desc[0] for desc in cursor.description]
                attachments = [dict(zip(att_columns, row)) for row in cursor.fetchall()]

                # Group attachments by email_id
                att_by_email = {}
                for att in attachments:
                    eid = att['email_id']
                    if eid not in att_by_email:
                        att_by_email[eid] = []
                    att_by_email[eid].append(att)

                # Assign attachments to emails
                for email in emails:
                    email['attachments'] = att_by_email.get(email['email_id'], [])

            # Thread grouping if requested
            if include_threads:
                threads = {}
                for email in emails:
                    thread_id = email.get('thread_id')
                    if thread_id:
                        if thread_id not in threads:
                            threads[thread_id] = []
                        threads[thread_id].append(email['email_id'])

                for email in emails:
                    thread_id = email.get('thread_id')
                    if thread_id and thread_id in threads:
                        email['thread_position'] = threads[thread_id].index(email['email_id']) + 1
                        email['total_in_thread'] = len(threads[thread_id])

            # Get stats
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT e.email_id) as total_emails,
                    COUNT(DISTINCT ea.attachment_id) as total_attachments,
                    SUM(CASE WHEN ea.document_type = 'bensley_contract' THEN 1 ELSE 0 END) as contract_count,
                    SUM(CASE WHEN ea.document_type = 'design_document' THEN 1 ELSE 0 END) as design_doc_count
                FROM emails e
                INNER JOIN email_project_links epl ON e.email_id = epl.email_id
                LEFT JOIN email_attachments ea ON e.email_id = ea.email_id
                WHERE epl.project_code = ?
            """, (project_code,))

            stats_row = cursor.fetchone()
            stats = {
                "total_emails": stats_row[0] or 0,
                "total_attachments": stats_row[1] or 0,
                "contract_count": stats_row[2] or 0,
                "design_doc_count": stats_row[3] or 0
            }

            return {
                "success": True,
                "project": project,
                "emails": emails,
                "stats": stats
            }

    # ============================================================================
    # HELPER: GET PROJECTS FOR LINKING
    # ============================================================================

    def get_projects_for_linking(self, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Get list of projects for the email link dropdown
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    project_code as code,
                    project_title as name,
                    status,
                    is_active_project
                FROM projects
                WHERE project_code IS NOT NULL
                ORDER BY
                    is_active_project DESC,
                    project_code DESC
                LIMIT ?
            """, (limit,))

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    # ============================================================================
    # REVIEW QUEUE - Emails with pending suggestions
    # ============================================================================

    def get_review_queue(self, limit: int = 50) -> Dict[str, Any]:
        """
        Get emails with pending AI suggestions for review.

        Returns emails that have:
        - Pending email_link suggestions
        - Pending contact_link suggestions
        - Any other pending suggestions

        Each email includes:
        - Email content (subject, sender, snippet)
        - The AI suggestion with confidence and reason
        - Sender context (other emails from same sender, linked projects)

        Used by the Email Review Queue page for batch reviewing.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get emails with pending suggestions
            # Note: ai_suggestions uses target_table, project_code, description, suggested_data
            cursor.execute("""
                SELECT
                    e.email_id,
                    e.subject,
                    e.sender_email,
                    e.sender_name,
                    COALESCE(e.date, e.date_normalized) as date,
                    e.snippet,
                    e.has_attachments,
                    ec.category,
                    ec.ai_summary,
                    s.suggestion_id,
                    s.suggestion_type,
                    s.target_table,
                    s.target_id,
                    s.project_code as target_code,
                    s.confidence_score,
                    s.title as match_method,
                    s.description as match_reason,
                    s.suggested_data as suggested_value,
                    s.detected_entities as context,
                    s.created_at as suggestion_created,
                    -- Get project/proposal name for display
                    COALESCE(p.project_name, pr.project_title) as target_name
                FROM ai_suggestions s
                INNER JOIN emails e ON s.source_id = e.email_id AND s.source_type = 'email'
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
                LEFT JOIN proposals p ON s.target_table = 'proposals' AND s.target_id = p.proposal_id
                LEFT JOIN projects pr ON s.target_table = 'projects' AND s.target_id = pr.project_id
                WHERE s.status = 'pending'
                AND s.suggestion_type IN ('email_link', 'contact_link', 'project_alias')
                ORDER BY s.confidence_score DESC, s.created_at DESC
                LIMIT ?
            """, (limit,))

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            # Build email list with suggestions
            emails = []
            for row in rows:
                email_data = dict(zip(columns, row))

                # Extract suggestion into nested object
                suggestion = {
                    'suggestion_id': email_data.pop('suggestion_id'),
                    'type': email_data.pop('suggestion_type'),
                    'target_type': email_data.pop('target_table'),  # renamed from target_type
                    'target_id': email_data.pop('target_id'),
                    'target_code': email_data.pop('target_code'),
                    'target_name': email_data.pop('target_name'),
                    'confidence': email_data.pop('confidence_score'),
                    'match_method': email_data.pop('match_method'),
                    'reason': email_data.pop('match_reason'),
                    'suggested_value': email_data.pop('suggested_value'),
                    'context': email_data.pop('context'),
                    'created_at': email_data.pop('suggestion_created'),
                }
                email_data['suggestion'] = suggestion

                emails.append(email_data)

            # Get sender context for each unique sender
            sender_emails = list(set(e.get('sender_email') for e in emails if e.get('sender_email')))

            sender_context = {}
            if sender_emails:
                for sender in sender_emails:
                    if not sender:
                        continue

                    # Count emails from this sender
                    cursor.execute("""
                        SELECT COUNT(*) FROM emails WHERE sender_email = ?
                    """, (sender,))
                    total = cursor.fetchone()[0]

                    # Get linked projects for this sender
                    cursor.execute("""
                        SELECT DISTINCT epl.project_code
                        FROM emails e
                        INNER JOIN email_proposal_links epl ON e.email_id = epl.email_id
                        WHERE e.sender_email = ?
                        LIMIT 5
                    """, (sender,))
                    linked_projects = [row[0] for row in cursor.fetchall()]

                    # Check if known contact
                    cursor.execute("""
                        SELECT contact_id FROM contacts WHERE email = ?
                    """, (sender,))
                    is_contact = cursor.fetchone() is not None

                    sender_context[sender] = {
                        'total_emails': total,
                        'linked_projects': linked_projects,
                        'is_known_contact': is_contact
                    }

            # Attach sender context to each email
            for email in emails:
                sender = email.get('sender_email')
                if sender and sender in sender_context:
                    email['sender_context'] = sender_context[sender]
                else:
                    email['sender_context'] = {
                        'total_emails': 0,
                        'linked_projects': [],
                        'is_known_contact': False
                    }

            # Get queue stats
            cursor.execute("""
                SELECT COUNT(*) FROM ai_suggestions
                WHERE status = 'pending'
                AND suggestion_type IN ('email_link', 'contact_link', 'project_alias')
            """)
            total_pending = cursor.fetchone()[0]

            cursor.execute("""
                SELECT suggestion_type, COUNT(*)
                FROM ai_suggestions
                WHERE status = 'pending'
                GROUP BY suggestion_type
            """)
            by_type = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                'success': True,
                'count': len(emails),
                'total_pending': total_pending,
                'by_type': by_type,
                'emails': emails
            }
