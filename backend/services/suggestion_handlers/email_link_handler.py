"""
Email link handler for email_link suggestions.

Links emails to proposals or projects when suggestions are approved.
"""

from typing import Any, Dict, List

from .base import BaseSuggestionHandler, ChangePreview, SuggestionResult
from .registry import register_handler


@register_handler
class EmailLinkHandler(BaseSuggestionHandler):
    """
    Handler for email_link suggestions.

    Creates a link in email_proposal_links or email_project_links table
    depending on whether the suggestion contains proposal_id or project_id.
    """

    suggestion_type = "email_link"
    target_table = "email_proposal_links"  # Default, may use email_project_links
    is_actionable = True

    def _get_target_table(self, suggested_data: Dict[str, Any]) -> str:
        """Determine which link table to use based on suggestion data."""
        if suggested_data.get("proposal_id"):
            return "email_proposal_links"
        elif suggested_data.get("project_id"):
            return "email_project_links"
        return "email_proposal_links"

    def validate(self, suggested_data: Dict[str, Any]) -> List[str]:
        """
        Validate the suggested data for linking an email.

        Required: email_id and either proposal_id or project_id.
        """
        errors = []

        email_id = suggested_data.get("email_id")
        if not email_id:
            errors.append("Email ID is required")
            return errors

        proposal_id = suggested_data.get("proposal_id")
        project_id = suggested_data.get("project_id")

        if not proposal_id and not project_id:
            errors.append("Either proposal_id or project_id is required")
            return errors

        # Verify email exists
        cursor = self.conn.cursor()
        cursor.execute("SELECT email_id, subject FROM emails WHERE email_id = ?", (email_id,))
        if not cursor.fetchone():
            errors.append(f"Email #{email_id} not found")
            return errors

        # Check for duplicate link
        if proposal_id:
            cursor.execute("""
                SELECT link_id FROM email_proposal_links
                WHERE email_id = ? AND proposal_id = ?
            """, (email_id, proposal_id))
            if cursor.fetchone():
                errors.append(f"Email #{email_id} is already linked to proposal #{proposal_id}")
        elif project_id:
            cursor.execute("""
                SELECT email_id FROM email_project_links
                WHERE email_id = ? AND project_id = ?
            """, (email_id, project_id))
            if cursor.fetchone():
                errors.append(f"Email #{email_id} is already linked to project #{project_id}")

        return errors

    def preview(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> ChangePreview:
        """
        Generate preview of the email link that will be created.
        """
        email_id = suggested_data.get("email_id")
        proposal_id = suggested_data.get("proposal_id")
        project_id = suggested_data.get("project_id")
        project_code = suggested_data.get("project_code")

        # Get email subject for display
        cursor = self.conn.cursor()
        cursor.execute("SELECT subject FROM emails WHERE email_id = ?", (email_id,))
        row = cursor.fetchone()
        email_subject = row[0][:50] if row and row[0] else f"Email #{email_id}"

        target_table = self._get_target_table(suggested_data)

        if proposal_id:
            target_desc = project_code or f"proposal #{proposal_id}"
        else:
            target_desc = project_code or f"project #{project_id}"

        summary = f"Link email '{email_subject}' to {target_desc}"

        changes = [{"field": "email_id", "new": email_id}]

        if proposal_id:
            changes.append({"field": "proposal_id", "new": proposal_id})
        if project_id:
            changes.append({"field": "project_id", "new": project_id})
        if suggested_data.get("confidence_score"):
            changes.append({"field": "confidence_score", "new": suggested_data["confidence_score"]})
        if suggested_data.get("match_method"):
            changes.append({"field": "match_method", "new": suggested_data["match_method"]})

        return ChangePreview(
            table=target_table,
            action="insert",
            summary=summary,
            changes=changes
        )

    def apply(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> SuggestionResult:
        """
        Create a link in the appropriate email link table.

        Returns rollback_data with link identifiers for undo.
        """
        cursor = self.conn.cursor()

        email_id = suggested_data.get("email_id")
        proposal_id = suggested_data.get("proposal_id")
        project_id = suggested_data.get("project_id")
        project_code = suggested_data.get("project_code")
        confidence_score = suggested_data.get("confidence_score", 0.9)
        match_method = suggested_data.get("match_method", "ai_suggestion")
        match_reason = suggested_data.get("match_reason") or suggested_data.get("reason")
        suggestion_id = suggestion.get("suggestion_id")

        target_table = self._get_target_table(suggested_data)

        if proposal_id:
            # Insert into email_proposal_links
            cursor.execute("""
                INSERT INTO email_proposal_links (
                    email_id, proposal_id, confidence_score, match_method, match_reason
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                email_id,
                proposal_id,
                confidence_score,
                match_method,
                match_reason
            ))

            link_id = cursor.lastrowid
            self.conn.commit()

            # Record the change in audit trail
            self._record_change(
                suggestion_id=suggestion_id,
                table_name="email_proposal_links",
                record_id=link_id,
                field_name=None,
                old_value=None,
                new_value=f"email_id={email_id},proposal_id={proposal_id}",
                change_type="insert"
            )
            self.conn.commit()

            target_desc = project_code or f"proposal #{proposal_id}"
            return SuggestionResult(
                success=True,
                message=f"Linked email #{email_id} to {target_desc}",
                changes_made=[{
                    "table": "email_proposal_links",
                    "record_id": link_id,
                    "change_type": "insert"
                }],
                rollback_data={
                    "table": "email_proposal_links",
                    "link_id": link_id,
                    "email_id": email_id,
                    "proposal_id": proposal_id
                }
            )
        else:
            # Insert into email_project_links (composite primary key)
            cursor.execute("""
                INSERT INTO email_project_links (
                    email_id, project_id, confidence, link_method, evidence, project_code
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                email_id,
                project_id,
                confidence_score,
                match_method,
                match_reason,
                project_code
            ))

            self.conn.commit()

            # Record the change in audit trail (use email_id as record_id since no link_id)
            self._record_change(
                suggestion_id=suggestion_id,
                table_name="email_project_links",
                record_id=email_id,
                field_name=None,
                old_value=None,
                new_value=f"email_id={email_id},project_id={project_id}",
                change_type="insert"
            )
            self.conn.commit()

            target_desc = project_code or f"project #{project_id}"
            return SuggestionResult(
                success=True,
                message=f"Linked email #{email_id} to {target_desc}",
                changes_made=[{
                    "table": "email_project_links",
                    "record_id": email_id,
                    "change_type": "insert"
                }],
                rollback_data={
                    "table": "email_project_links",
                    "email_id": email_id,
                    "project_id": project_id
                }
            )

    def rollback(self, rollback_data: Dict[str, Any]) -> bool:
        """
        Delete the created email link.
        """
        table = rollback_data.get("table")
        if not table:
            return False

        cursor = self.conn.cursor()

        if table == "email_proposal_links":
            link_id = rollback_data.get("link_id")
            if not link_id:
                return False

            cursor.execute("DELETE FROM email_proposal_links WHERE link_id = ?", (link_id,))

            # Mark the change record as rolled back
            cursor.execute("""
                UPDATE suggestion_changes
                SET rolled_back = 1, rolled_back_at = datetime('now')
                WHERE table_name = 'email_proposal_links' AND record_id = ? AND change_type = 'insert'
            """, (link_id,))

        elif table == "email_project_links":
            email_id = rollback_data.get("email_id")
            project_id = rollback_data.get("project_id")
            if not email_id or not project_id:
                return False

            cursor.execute("""
                DELETE FROM email_project_links
                WHERE email_id = ? AND project_id = ?
            """, (email_id, project_id))

            # Mark the change record as rolled back
            cursor.execute("""
                UPDATE suggestion_changes
                SET rolled_back = 1, rolled_back_at = datetime('now')
                WHERE table_name = 'email_project_links' AND record_id = ? AND change_type = 'insert'
            """, (email_id,))

        else:
            return False

        self.conn.commit()
        return True
