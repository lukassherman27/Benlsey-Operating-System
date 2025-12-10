"""
Link review handler for link_review suggestions.

Reviews existing email links that were auto-created and flagged for review.
Approve = mark link as reviewed (needs_review = 0)
Reject = delete the link
"""

from datetime import datetime
from typing import Any, Dict, List

from .base import BaseSuggestionHandler, ChangePreview, SuggestionResult
from .registry import register_handler


@register_handler
class LinkReviewHandler(BaseSuggestionHandler):
    """
    Handler for link_review suggestions.

    Reviews existing links in email_proposal_links or email_project_links tables.
    These are links that were auto-created and flagged with needs_review = 1.

    Suggested data must contain:
    - link_type: 'proposal' or 'project'
    - email_id: The email ID
    - proposal_id or project_id: The target ID

    On approve: sets needs_review = 0, reviewed_at = now, reviewed_by = 'user'
    On reject: deletes the link from the table
    """

    suggestion_type = "link_review"
    target_table = "email_proposal_links"  # May use email_project_links
    is_actionable = True

    def _get_link_info(self, suggested_data: Dict[str, Any]) -> tuple:
        """
        Determine link type and get table/column info.

        Returns: (table_name, id_column, id_value)
        """
        link_type = suggested_data.get("link_type", "proposal")

        if link_type == "project":
            return (
                "email_project_links",
                "project_id",
                suggested_data.get("project_id")
            )
        else:
            return (
                "email_proposal_links",
                "proposal_id",
                suggested_data.get("proposal_id")
            )

    def validate(self, suggested_data: Dict[str, Any]) -> List[str]:
        """
        Validate the suggested data for reviewing a link.

        Required: email_id and either proposal_id or project_id.
        """
        errors = []

        email_id = suggested_data.get("email_id")
        if not email_id:
            errors.append("Email ID is required")
            return errors

        table, id_col, target_id = self._get_link_info(suggested_data)

        if not target_id:
            errors.append(f"{id_col} is required")
            return errors

        # Verify link exists
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT email_id FROM {table}
            WHERE email_id = ? AND {id_col} = ?
        """, (email_id, target_id))

        if not cursor.fetchone():
            errors.append(f"Link not found: email #{email_id} to {id_col.replace('_id', '')} #{target_id}")

        return errors

    def preview(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> ChangePreview:
        """
        Generate preview of the link review action.
        """
        email_id = suggested_data.get("email_id")
        table, id_col, target_id = self._get_link_info(suggested_data)
        project_code = suggested_data.get("project_code")

        # Get email subject for display
        cursor = self.conn.cursor()
        cursor.execute("SELECT subject FROM emails WHERE email_id = ?", (email_id,))
        row = cursor.fetchone()
        email_subject = row[0][:50] if row and row[0] else f"Email #{email_id}"

        # Get link method for context
        cursor.execute(f"""
            SELECT link_method, confidence, evidence FROM {table}
            WHERE email_id = ? AND {id_col} = ?
        """, (email_id, target_id)) if table == "email_project_links" else cursor.execute(f"""
            SELECT match_method, confidence_score, match_reason FROM {table}
            WHERE email_id = ? AND {id_col} = ?
        """, (email_id, target_id))

        link_row = cursor.fetchone()
        link_method = link_row[0] if link_row else "unknown"

        target_type = id_col.replace("_id", "")
        target_desc = project_code or f"{target_type} #{target_id}"

        summary = f"Review link: '{email_subject}' → {target_desc} (method: {link_method})"

        changes = [
            {"field": "needs_review", "old": 1, "new": 0},
            {"field": "reviewed_at", "old": None, "new": "now"},
            {"field": "reviewed_by", "old": None, "new": "user"}
        ]

        return ChangePreview(
            table=table,
            action="update",
            summary=summary,
            changes=changes
        )

    def apply(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> SuggestionResult:
        """
        Mark the link as reviewed (approved).

        Sets needs_review = 0 and records review timestamp.
        """
        cursor = self.conn.cursor()

        email_id = suggested_data.get("email_id")
        table, id_col, target_id = self._get_link_info(suggested_data)
        project_code = suggested_data.get("project_code")
        suggestion_id = suggestion.get("suggestion_id")

        now = datetime.now().isoformat()

        # Mark as reviewed
        cursor.execute(f"""
            UPDATE {table}
            SET needs_review = 0, reviewed_at = ?, reviewed_by = 'user'
            WHERE email_id = ? AND {id_col} = ?
        """, (now, email_id, target_id))

        self.conn.commit()

        # Record the change in audit trail
        self._record_change(
            suggestion_id=suggestion_id,
            table_name=table,
            record_id=email_id,
            field_name="needs_review",
            old_value=1,
            new_value=0,
            change_type="update"
        )
        self.conn.commit()

        target_type = id_col.replace("_id", "")
        target_desc = project_code or f"{target_type} #{target_id}"

        return SuggestionResult(
            success=True,
            message=f"Approved link: email #{email_id} → {target_desc}",
            changes_made=[{
                "table": table,
                "record_id": email_id,
                "change_type": "update"
            }],
            rollback_data={
                "table": table,
                "email_id": email_id,
                "id_col": id_col,
                "target_id": target_id
            }
        )

    def reject(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> SuggestionResult:
        """
        Delete the link (rejection).

        This is called when a link_review suggestion is rejected.
        Unlike other handlers, rejection deletes the link from the database.
        """
        cursor = self.conn.cursor()

        email_id = suggested_data.get("email_id")
        table, id_col, target_id = self._get_link_info(suggested_data)
        project_code = suggested_data.get("project_code")
        suggestion_id = suggestion.get("suggestion_id")

        # Get current link data for rollback
        if table == "email_project_links":
            cursor.execute(f"""
                SELECT email_id, project_id, confidence, link_method, evidence, project_code
                FROM {table}
                WHERE email_id = ? AND {id_col} = ?
            """, (email_id, target_id))
        else:
            cursor.execute(f"""
                SELECT email_id, proposal_id, confidence_score, match_method, match_reason
                FROM {table}
                WHERE email_id = ? AND {id_col} = ?
            """, (email_id, target_id))

        link_row = cursor.fetchone()

        # Delete the link
        cursor.execute(f"""
            DELETE FROM {table}
            WHERE email_id = ? AND {id_col} = ?
        """, (email_id, target_id))

        self.conn.commit()

        # Record the deletion in audit trail
        self._record_change(
            suggestion_id=suggestion_id,
            table_name=table,
            record_id=email_id,
            field_name=None,
            old_value=f"email_id={email_id},{id_col}={target_id}",
            new_value=None,
            change_type="delete"
        )
        self.conn.commit()

        target_type = id_col.replace("_id", "")
        target_desc = project_code or f"{target_type} #{target_id}"

        return SuggestionResult(
            success=True,
            message=f"Deleted link: email #{email_id} → {target_desc}",
            changes_made=[{
                "table": table,
                "record_id": email_id,
                "change_type": "delete"
            }],
            rollback_data={
                "table": table,
                "link_data": link_row,
                "columns": ["email_id", id_col, "confidence", "link_method" if table == "email_project_links" else "match_method", "evidence" if table == "email_project_links" else "match_reason"] + (["project_code"] if table == "email_project_links" else [])
            }
        )

    def rollback(self, rollback_data: Dict[str, Any]) -> bool:
        """
        Undo a link review action.

        For approve: set needs_review back to 1
        For reject: re-insert the deleted link
        """
        table = rollback_data.get("table")
        if not table:
            return False

        cursor = self.conn.cursor()

        # Check if this was an approval (has id_col) or rejection (has link_data)
        if rollback_data.get("link_data"):
            # This was a rejection - re-insert the link
            link_data = rollback_data["link_data"]
            columns = rollback_data.get("columns", [])

            if not link_data or not columns:
                return False

            placeholders = ", ".join(["?"] * len(columns))
            cols = ", ".join(columns)

            cursor.execute(f"""
                INSERT INTO {table} ({cols})
                VALUES ({placeholders})
            """, link_data[:len(columns)])

        else:
            # This was an approval - set needs_review back to 1
            email_id = rollback_data.get("email_id")
            id_col = rollback_data.get("id_col")
            target_id = rollback_data.get("target_id")

            if not email_id or not id_col or not target_id:
                return False

            cursor.execute(f"""
                UPDATE {table}
                SET needs_review = 1, reviewed_at = NULL, reviewed_by = NULL
                WHERE email_id = ? AND {id_col} = ?
            """, (email_id, target_id))

        self.conn.commit()
        return True
