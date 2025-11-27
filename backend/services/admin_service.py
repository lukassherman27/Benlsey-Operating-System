"""
Admin Service - Data Validation, Email Links, and System Management
"""
import sqlite3
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from .base_service import BaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdminService(BaseService):
    """Service for admin operations: validation, email links, bulk operations"""

    def __init__(self, db_path: str):
        super().__init__(db_path)

    # ============================================================================
    # TRAINING FEEDBACK RECORDING
    # ============================================================================

    def _record_training_feedback(
        self,
        feature_name: str,
        original_value: Optional[str],
        correction_value: Optional[str],
        helpful: bool,
        project_code: Optional[str] = None,
        context_data: Optional[Dict] = None,
        user_id: str = "system"
    ) -> bool:
        """
        Record human feedback to training_data_feedback table for RLHF.

        This captures all human decisions on AI suggestions so we can:
        1. Track accuracy of AI suggestions
        2. Learn patterns from corrections
        3. Build training data for future model improvement

        Args:
            feature_name: Type of feature (e.g., 'data_validation', 'email_category')
            original_value: What AI suggested
            correction_value: What human corrected to (or 'approved'/'rejected')
            helpful: Whether the suggestion was helpful (approved)
            project_code: Related project if applicable
            context_data: Additional context as dict (will be JSON-ified)
            user_id: Who made the decision

        Returns:
            True if recorded successfully
        """
        import json

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO training_data_feedback (
                        user_id, feature_name, component_name,
                        original_value, correction_value, helpful,
                        project_code, context_data, created_at, source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    feature_name,
                    'admin_validation',
                    original_value,
                    correction_value,
                    1 if helpful else 0,
                    project_code,
                    json.dumps(context_data) if context_data else None,
                    datetime.now().isoformat(),
                    'admin_ui'
                ))
                conn.commit()
                logger.info(f"Recorded training feedback: {feature_name}, helpful={helpful}")
                return True
        except Exception as e:
            logger.error(f"Failed to record training feedback: {e}")
            return False

    # ============================================================================
    # DATA VALIDATION SUGGESTIONS
    # ============================================================================

    def get_validation_suggestions(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get data validation suggestions with evidence

        Args:
            status: Filter by status (pending/approved/denied/applied)
            limit: Max results
            offset: Pagination offset

        Returns:
            Dict with suggestions list and metadata
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Build query
            where_clauses = []
            params = []

            if status:
                where_clauses.append("dvs.status = ?")
                params.append(status)

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            # Get suggestions with evidence
            query = f"""
                SELECT
                    dvs.suggestion_id,
                    dvs.entity_type,
                    dvs.entity_id,
                    dvs.project_code,
                    dvs.field_name,
                    dvs.current_value,
                    dvs.suggested_value,
                    dvs.evidence_source,
                    dvs.evidence_id,
                    dvs.evidence_snippet,
                    dvs.confidence_score,
                    dvs.reasoning,
                    dvs.suggested_action,
                    dvs.status,
                    dvs.created_at,
                    dvs.reviewed_by,
                    dvs.reviewed_at,
                    dvs.review_notes,
                    dvs.applied_at,
                    dvs.applied_by,
                    -- Get email details if evidence is from email
                    e.subject as evidence_email_subject,
                    e.sender_email as evidence_email_sender,
                    e.date as evidence_email_date,
                    -- Get entity details
                    CASE dvs.entity_type
                        WHEN 'proposal' THEN p.project_name
                        WHEN 'project' THEN proj.project_title
                        ELSE NULL
                    END as entity_name
                FROM data_validation_suggestions dvs
                LEFT JOIN emails e ON dvs.evidence_source = 'email' AND dvs.evidence_id = e.email_id
                LEFT JOIN proposals p ON dvs.entity_type = 'proposal' AND dvs.entity_id = p.proposal_id
                LEFT JOIN projects proj ON dvs.entity_type = 'project' AND dvs.entity_id = proj.project_id
                {where_sql}
                ORDER BY dvs.created_at DESC
                LIMIT ? OFFSET ?
            """

            params.extend([limit, offset])
            cursor.execute(query, params)

            columns = [desc[0] for desc in cursor.description]
            suggestions = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Get total count
            count_query = f"""
                SELECT COUNT(*) as total
                FROM data_validation_suggestions dvs
                {where_sql}
            """
            cursor.execute(count_query, params[:-2])  # Exclude limit/offset
            total = cursor.fetchone()[0]

            # Get stats
            stats_query = """
                SELECT
                    status,
                    COUNT(*) as count
                FROM data_validation_suggestions
                GROUP BY status
            """
            cursor.execute(stats_query)
            stats = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                "suggestions": suggestions,
                "total": total,
                "limit": limit,
                "offset": offset,
                "stats": {
                    "pending": stats.get("pending", 0),
                    "approved": stats.get("approved", 0),
                    "denied": stats.get("denied", 0),
                    "applied": stats.get("applied", 0),
                }
            }

    def get_suggestion_by_id(self, suggestion_id: int) -> Optional[Dict[str, Any]]:
        """Get single validation suggestion with full details"""
        result = self.get_validation_suggestions()
        suggestions = result.get("suggestions", [])

        for suggestion in suggestions:
            if suggestion["suggestion_id"] == suggestion_id:
                return suggestion

        return None

    def approve_suggestion(
        self,
        suggestion_id: int,
        reviewed_by: str,
        review_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve a validation suggestion and apply the change

        Args:
            suggestion_id: ID of suggestion to approve
            reviewed_by: Who is approving (username/email)
            review_notes: Optional notes about the approval

        Returns:
            Dict with success status and details
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                # Get the suggestion
                cursor.execute("""
                    SELECT
                        entity_type, entity_id, field_name,
                        current_value, suggested_value, project_code
                    FROM data_validation_suggestions
                    WHERE suggestion_id = ?
                """, (suggestion_id,))

                row = cursor.fetchone()
                if not row:
                    return {"success": False, "error": "Suggestion not found"}

                entity_type, entity_id, field_name, current_value, suggested_value, project_code = row

                # Update suggestion status to approved
                cursor.execute("""
                    UPDATE data_validation_suggestions
                    SET
                        status = 'approved',
                        reviewed_by = ?,
                        reviewed_at = ?,
                        review_notes = ?
                    WHERE suggestion_id = ?
                """, (reviewed_by, datetime.now().isoformat(), review_notes, suggestion_id))

                # Apply the change to the entity
                table_map = {
                    "proposal": "proposals",
                    "project": "projects",
                    "contract": "contracts",
                    "invoice": "invoices"
                }

                table = table_map.get(entity_type)
                if not table:
                    conn.rollback()
                    return {"success": False, "error": f"Unknown entity_type: {entity_type}"}

                # Determine primary key column
                pk_column = f"{entity_type}_id"

                # Apply the change
                update_query = f"""
                    UPDATE {table}
                    SET {field_name} = ?, updated_at = ?
                    WHERE {pk_column} = ?
                """
                cursor.execute(update_query, (suggested_value, datetime.now().isoformat(), entity_id))

                # Update suggestion status to applied
                cursor.execute("""
                    UPDATE data_validation_suggestions
                    SET
                        status = 'applied',
                        applied_by = ?,
                        applied_at = ?
                    WHERE suggestion_id = ?
                """, (reviewed_by, datetime.now().isoformat(), suggestion_id))

                # Log the application
                cursor.execute("""
                    INSERT INTO suggestion_application_log (
                        suggestion_id, entity_type, entity_id, field_name,
                        old_value, new_value, applied_by, applied_at, success
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    suggestion_id, entity_type, entity_id, field_name,
                    current_value, suggested_value, reviewed_by,
                    datetime.now().isoformat()
                ))

                conn.commit()

                # Record training feedback for RLHF
                self._record_training_feedback(
                    feature_name='data_validation_suggestion',
                    original_value=current_value,
                    correction_value=suggested_value,
                    helpful=True,  # Approved = helpful
                    project_code=project_code,
                    context_data={
                        'suggestion_id': suggestion_id,
                        'entity_type': entity_type,
                        'entity_id': entity_id,
                        'field_name': field_name,
                        'action': 'approved_and_applied',
                        'review_notes': review_notes
                    },
                    user_id=reviewed_by
                )

                return {
                    "success": True,
                    "suggestion_id": suggestion_id,
                    "entity_type": entity_type,
                    "project_code": project_code,
                    "field_name": field_name,
                    "old_value": current_value,
                    "new_value": suggested_value,
                    "message": f"✓ {entity_type.title()} {project_code} {field_name} updated successfully"
                }

            except Exception as e:
                conn.rollback()

                # Log the failure
                try:
                    cursor.execute("""
                        INSERT INTO suggestion_application_log (
                            suggestion_id, entity_type, entity_id, field_name,
                            old_value, new_value, applied_by, applied_at,
                            success, error_message
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                    """, (
                        suggestion_id, entity_type, entity_id, field_name,
                        current_value, suggested_value, reviewed_by,
                        datetime.now().isoformat(), str(e)
                    ))
                    conn.commit()
                except:
                    pass

                return {
                    "success": False,
                    "error": str(e),
                    "suggestion_id": suggestion_id
                }

    def deny_suggestion(
        self,
        suggestion_id: int,
        reviewed_by: str,
        review_notes: str
    ) -> Dict[str, Any]:
        """
        Deny a validation suggestion

        Args:
            suggestion_id: ID of suggestion to deny
            reviewed_by: Who is denying
            review_notes: Required notes explaining why denied

        Returns:
            Dict with success status
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                # First get the suggestion details for feedback recording
                cursor.execute("""
                    SELECT
                        entity_type, entity_id, field_name,
                        current_value, suggested_value, project_code
                    FROM data_validation_suggestions
                    WHERE suggestion_id = ?
                """, (suggestion_id,))

                row = cursor.fetchone()
                if not row:
                    return {"success": False, "error": "Suggestion not found"}

                entity_type, entity_id, field_name, current_value, suggested_value, project_code = row

                # Update status to denied
                cursor.execute("""
                    UPDATE data_validation_suggestions
                    SET
                        status = 'denied',
                        reviewed_by = ?,
                        reviewed_at = ?,
                        review_notes = ?
                    WHERE suggestion_id = ?
                """, (reviewed_by, datetime.now().isoformat(), review_notes, suggestion_id))

                conn.commit()

                # Record training feedback for RLHF (denied = not helpful)
                self._record_training_feedback(
                    feature_name='data_validation_suggestion',
                    original_value=suggested_value,  # What AI suggested
                    correction_value='rejected',  # Human rejected it
                    helpful=False,  # Denied = not helpful
                    project_code=project_code,
                    context_data={
                        'suggestion_id': suggestion_id,
                        'entity_type': entity_type,
                        'entity_id': entity_id,
                        'field_name': field_name,
                        'current_value': current_value,
                        'action': 'denied',
                        'denial_reason': review_notes
                    },
                    user_id=reviewed_by
                )

                return {
                    "success": True,
                    "suggestion_id": suggestion_id,
                    "message": "✓ Suggestion denied successfully"
                }
            except Exception as e:
                conn.rollback()
                return {"success": False, "error": str(e)}

    # ============================================================================
    # EMAIL LINK MANAGEMENT
    # ============================================================================

    def get_email_links(
        self,
        project_code: Optional[str] = None,
        confidence_min: Optional[float] = None,
        link_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get email-to-proposal links with evidence

        Args:
            project_code: Filter by project code
            confidence_min: Minimum confidence score (0-1)
            link_type: Filter by link type (auto/manual/ai_suggested)
            limit: Max results
            offset: Pagination offset

        Returns:
            Dict with links and metadata
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            where_clauses = []
            params = []

            if project_code:
                where_clauses.append("p.project_code = ?")
                params.append(project_code)

            if confidence_min is not None:
                where_clauses.append("epl.confidence_score >= ?")
                params.append(confidence_min)

            if link_type:
                if link_type == "auto":
                    where_clauses.append("epl.auto_linked = 1")
                elif link_type == "manual":
                    where_clauses.append("epl.auto_linked = 0")

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            query = f"""
                SELECT
                    epl.link_id,
                    epl.email_id,
                    epl.proposal_id,
                    epl.confidence_score,
                    CASE WHEN epl.auto_linked = 1 THEN 'auto' ELSE 'manual' END as link_type,
                    epl.match_reasons,
                    epl.created_at,
                    -- Email details
                    e.subject,
                    e.sender_email,
                    e.date as email_date,
                    e.snippet,
                    e.category,
                    -- Proposal details
                    p.project_code,
                    p.project_name,
                    p.status as proposal_status
                FROM email_proposal_links epl
                JOIN emails e ON epl.email_id = e.email_id
                JOIN proposals p ON epl.proposal_id = p.proposal_id
                {where_sql}
                ORDER BY epl.created_at DESC
                LIMIT ? OFFSET ?
            """

            params.extend([limit, offset])
            cursor.execute(query, params)

            columns = [desc[0] for desc in cursor.description]
            links = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Get total count
            count_query = f"""
                SELECT COUNT(*) as total
                FROM email_proposal_links epl
                JOIN proposals p ON epl.proposal_id = p.proposal_id
                {where_sql}
            """
            cursor.execute(count_query, params[:-2])
            total = cursor.fetchone()[0]

            return {
                "links": links,
                "total": total,
                "limit": limit,
                "offset": offset
            }

    def unlink_email(self, link_id: int, user: str) -> Dict[str, Any]:
        """Delete an email-to-proposal link with retry on OneDrive sync lock"""
        def _do_unlink():
            with self.get_connection() as conn:
                cursor = conn.cursor()

                try:
                    # Get link details for logging
                    cursor.execute("""
                        SELECT email_id, proposal_id FROM email_proposal_links
                        WHERE link_id = ?
                    """, (link_id,))

                    row = cursor.fetchone()
                    if not row:
                        return {"success": False, "error": "Link not found"}

                    email_id, proposal_id = row

                    # Delete the link
                    cursor.execute("DELETE FROM email_proposal_links WHERE link_id = ?", (link_id,))

                    conn.commit()

                    return {
                        "success": True,
                        "link_id": link_id,
                        "message": "✓ Email unlinked successfully"
                    }
                except Exception as e:
                    conn.rollback()
                    return {"success": False, "error": str(e)}

        return self._retry_on_lock(_do_unlink)

    def create_manual_link(
        self,
        email_id: int,
        proposal_id: int,
        user: str
    ) -> Dict[str, Any]:
        """Create a manual email-to-proposal link"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                # Check if link already exists
                cursor.execute("""
                    SELECT link_id FROM email_proposal_links
                    WHERE email_id = ? AND proposal_id = ?
                """, (email_id, proposal_id))

                if cursor.fetchone():
                    return {"success": False, "error": "Link already exists"}

                # Create the link
                cursor.execute("""
                    INSERT INTO email_proposal_links (
                        email_id, proposal_id, confidence_score,
                        match_reasons, auto_linked, created_at
                    ) VALUES (?, ?, 1.0, ?, 0, ?)
                """, (email_id, proposal_id, f"Manually linked by {user}", datetime.now().isoformat()))

                link_id = cursor.lastrowid
                conn.commit()

                return {
                    "success": True,
                    "link_id": link_id,
                    "message": "✓ Email linked successfully"
                }
            except Exception as e:
                conn.rollback()
                return {"success": False, "error": str(e)}

    def update_email_link(
        self,
        link_id: int,
        link_type: Optional[str] = None,
        confidence_score: Optional[float] = None,
        match_reasons: Optional[str] = None,
        user: str = None
    ) -> Dict[str, Any]:
        """
        Update an existing email-to-proposal link

        Args:
            link_id: ID of the link to update
            link_type: New link type (auto/manual/approved)
            confidence_score: New confidence score (0-1)
            match_reasons: New match reasoning
            user: User making the update

        Returns:
            Dict with success status and message
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                # Check if link exists
                cursor.execute("SELECT link_id FROM email_proposal_links WHERE link_id = ?", (link_id,))
                if not cursor.fetchone():
                    return {"success": False, "error": "Link not found"}

                # Build update query dynamically
                updates = []
                params = []

                # Convert link_type string to auto_linked boolean
                if link_type is not None:
                    # approved and manual both set auto_linked=0 (not auto)
                    auto_linked = 1 if link_type == 'auto' else 0
                    updates.append("auto_linked = ?")
                    params.append(auto_linked)

                    # For approved links, update match_reasons to indicate human approval
                    if link_type == 'approved' and not match_reasons:
                        updates.append("match_reasons = ?")
                        params.append(f"Approved by {user or 'user'}")

                if confidence_score is not None:
                    updates.append("confidence_score = ?")
                    params.append(confidence_score)

                if match_reasons is not None:
                    updates.append("match_reasons = ?")
                    params.append(match_reasons)

                if not updates:
                    return {"success": False, "error": "No updates provided"}

                # Add link_id for WHERE clause
                params.append(link_id)

                # Execute update
                query = f"UPDATE email_proposal_links SET {', '.join(updates)} WHERE link_id = ?"
                cursor.execute(query, params)
                conn.commit()

                # Log the approval if user provided
                if user and link_type == 'approved':
                    cursor.execute("""
                        INSERT INTO data_validation_log (
                            validation_type, entity_type, entity_id,
                            validated_by, validation_status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        'email_link_approval',
                        'email_proposal_link',
                        link_id,
                        user,
                        'approved',
                        datetime.now().isoformat()
                    ))
                    conn.commit()

                return {
                    "success": True,
                    "message": "✓ Link updated successfully",
                    "link_id": link_id
                }

            except Exception as e:
                conn.rollback()
                return {"success": False, "error": str(e)}
