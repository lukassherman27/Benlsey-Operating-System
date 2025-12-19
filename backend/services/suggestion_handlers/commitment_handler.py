"""
Commitment handler for commitment suggestions.

Creates commitments in the commitments table when commitment suggestions are approved.
These track promises made by us or by clients/partners.
"""

from datetime import datetime
from typing import Any, Dict, List

from .base import BaseSuggestionHandler, ChangePreview, SuggestionResult
from .registry import register_handler


@register_handler
class CommitmentHandler(BaseSuggestionHandler):
    """
    Handler for commitment suggestions.

    Creates a commitment record in the commitments table.
    Tracks both our commitments and their commitments.
    """

    suggestion_type = "commitment"
    target_table = "commitments"
    is_actionable = True

    def validate(self, suggested_data: Dict[str, Any]) -> List[str]:
        """
        Validate the suggested data for creating a commitment.
        """
        errors = []

        description = suggested_data.get("description")
        if not description:
            errors.append("Commitment requires a description")

        commitment_type = suggested_data.get("commitment_type")
        if commitment_type and commitment_type not in ("our_commitment", "their_commitment"):
            errors.append(f"Invalid commitment type: {commitment_type}")

        return errors

    def preview(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> ChangePreview:
        """
        Generate preview of the commitment that will be created.
        """
        description = suggested_data.get("description", "Commitment")
        commitment_type = suggested_data.get("commitment_type", "our_commitment")
        committed_by = suggested_data.get("committed_by")
        due_date = suggested_data.get("due_date")
        project_code = suggestion.get("project_code") or suggested_data.get("project_code")

        # Build summary based on type
        if commitment_type == "our_commitment":
            type_label = "We promised"
        else:
            type_label = "They promised"

        summary = f"Track commitment: {type_label}: '{description[:40]}'"
        if project_code:
            summary += f" ({project_code})"

        changes = [
            {"field": "description", "new": description},
            {"field": "commitment_type", "new": commitment_type},
            {"field": "fulfillment_status", "new": "pending"},
        ]

        if committed_by:
            changes.append({"field": "committed_by", "new": committed_by})

        if due_date:
            changes.append({"field": "due_date", "new": due_date})

        if project_code:
            changes.append({"field": "project_code", "new": project_code})

        return ChangePreview(
            table="commitments",
            action="insert",
            summary=summary,
            changes=changes
        )

    def apply(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> SuggestionResult:
        """
        Create a commitment in the commitments table.
        """
        cursor = self.conn.cursor()

        description = suggested_data.get("description", "Commitment")
        commitment_type = suggested_data.get("commitment_type", "our_commitment")
        committed_by = suggested_data.get("committed_by")
        due_date = suggested_data.get("due_date")
        source_quote = suggested_data.get("source_quote")

        project_code = suggestion.get("project_code") or suggested_data.get("project_code")
        proposal_id = suggestion.get("proposal_id") or suggested_data.get("proposal_id")
        suggestion_id = suggestion.get("suggestion_id")
        source_email_id = suggestion.get("source_id") if suggestion.get("source_type") == "email" else None

        # Lookup proposal_id from project_code if not provided
        if project_code and not proposal_id:
            result = cursor.execute(
                "SELECT proposal_id FROM proposals WHERE project_code = ?",
                (project_code,)
            ).fetchone()
            if result:
                proposal_id = result[0]

        # Insert the commitment
        cursor.execute("""
            INSERT INTO commitments (
                commitment_type, description, committed_by, due_date,
                fulfillment_status, project_code, proposal_id,
                source_email_id, source_suggestion_id, created_at
            )
            VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?, datetime('now'))
        """, (
            commitment_type,
            description,
            committed_by,
            due_date,
            project_code,
            proposal_id,
            source_email_id,
            suggestion_id
        ))

        commitment_id = cursor.lastrowid
        self.conn.commit()

        # Record the change in audit trail
        self._record_change(
            suggestion_id=suggestion_id,
            table_name="commitments",
            record_id=commitment_id,
            field_name=None,
            old_value=None,
            new_value=f"commitment_id={commitment_id}",
            change_type="insert"
        )
        self.conn.commit()

        # Build message based on type
        if commitment_type == "our_commitment":
            type_label = "our commitment"
        else:
            type_label = "their commitment"

        return SuggestionResult(
            success=True,
            message=f"Tracking {type_label} #{commitment_id}: {description[:40]}",
            changes_made=[{
                "table": "commitments",
                "record_id": commitment_id,
                "change_type": "insert"
            }],
            rollback_data={"commitment_id": commitment_id}
        )

    def rollback(self, rollback_data: Dict[str, Any]) -> bool:
        """
        Delete the created commitment.
        """
        commitment_id = rollback_data.get("commitment_id")
        if not commitment_id:
            return False

        cursor = self.conn.cursor()

        cursor.execute("DELETE FROM commitments WHERE commitment_id = ?", (commitment_id,))

        cursor.execute("""
            UPDATE suggestion_changes
            SET rolled_back = 1, rolled_back_at = datetime('now')
            WHERE table_name = 'commitments' AND record_id = ? AND change_type = 'insert'
        """, (commitment_id,))

        self.conn.commit()

        return cursor.rowcount > 0 or True
