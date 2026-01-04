"""
Proposal status handler for proposal_status_update suggestions.

Updates proposal status when "proposal sent" is detected from sent emails.
Creates audit trail and updates relevant date fields.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import BaseSuggestionHandler, ChangePreview, SuggestionResult
from .registry import register_handler


# Valid status transitions for proposals - Full Lifecycle
# IMPORTANT: These use TitleCase to match database values
# Flow: First Contact → Meeting Held → NDA Signed → Proposal Prep → Proposal Sent
#       → Negotiation → MOU Signed → Contract Signed (win) or Lost/Declined/Dormant
VALID_STATUSES = [
    # Early stages (TitleCase - matches DB)
    'First Contact',     # New lead comes in
    'Meeting Held',      # Call/meeting completed
    'NDA Signed',        # NDA executed
    'Proposal Prep',     # Working on proposal

    # Proposal sent and beyond
    'Proposal Sent',     # Proposal sent to client
    'Negotiation',       # Discussing fees, scope, terms
    'MOU Signed',        # MOU signed, contract pending

    # Final outcomes
    'Contract Signed',   # Won - contract signed!
    'Lost',              # Did not win
    'Declined',          # We declined to pursue
    'Dormant',           # No activity, may revive
    'On Hold',           # Temporarily paused

    # Legacy lowercase aliases (for backwards compatibility with GPT suggestions)
    'proposal_sent',     # → maps to 'Proposal Sent'
    'first_contact',     # → maps to 'First Contact'
    'meeting_held',      # → maps to 'Meeting Held'
    'nda_signed',        # → maps to 'NDA Signed'
    'proposal_prep',     # → maps to 'Proposal Prep'
    'negotiation',       # → maps to 'Negotiation'
    'mou_signed',        # → maps to 'MOU Signed'
    'contract_signed',   # → maps to 'Contract Signed'
    'lost',              # → maps to 'Lost'
    'declined',          # → maps to 'Declined'
    'dormant',           # → maps to 'Dormant'
    'on_hold',           # → maps to 'On Hold',
]

# Mapping from lowercase to TitleCase (for normalization)
STATUS_NORMALIZE = {
    'proposal_sent': 'Proposal Sent',
    'first_contact': 'First Contact',
    'meeting_held': 'Meeting Held',
    'nda_signed': 'NDA Signed',
    'proposal_prep': 'Proposal Prep',
    'negotiation': 'Negotiation',
    'mou_signed': 'MOU Signed',
    'contract_signed': 'Contract Signed',
    'lost': 'Lost',
    'declined': 'Declined',
    'dormant': 'Dormant',
    'on_hold': 'On Hold',
}


@register_handler
class ProposalStatusHandler(BaseSuggestionHandler):
    """
    Handler for proposal_status_update suggestions.

    Updates the status field in the proposals table when:
    - A proposal email is detected in Sent folder
    - Status change is suggested based on email activity

    Does NOT auto-update - creates suggestion for human approval.
    """

    suggestion_type = "proposal_status_update"
    target_table = "proposals"
    is_actionable = True

    def validate(self, suggested_data: Dict[str, Any]) -> List[str]:
        """
        Validate the suggested data for updating proposal status.

        Required: new_status (or suggested_status) and project_code
        """
        errors = []

        # Accept either 'new_status' or 'suggested_status' (GPT uses the latter)
        new_status = suggested_data.get("new_status") or suggested_data.get("suggested_status")
        if not new_status:
            errors.append("Status update requires 'new_status' field")
        elif new_status not in VALID_STATUSES:
            errors.append(f"Invalid status '{new_status}'. Valid: {VALID_STATUSES}")

        # project_code comes from suggestion record, but check if in data too
        if not suggested_data.get("project_code") and not suggested_data.get("proposal_id"):
            # Will be checked against suggestion record in apply
            pass

        return errors

    def preview(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> ChangePreview:
        """
        Generate preview of the status update.
        """
        project_code = suggestion.get("project_code") or suggested_data.get("project_code")
        # Accept either 'new_status' or 'suggested_status' (GPT uses the latter)
        new_status = suggested_data.get("new_status") or suggested_data.get("suggested_status")

        # Normalize lowercase status to TitleCase
        if new_status and new_status in STATUS_NORMALIZE:
            new_status = STATUS_NORMALIZE[new_status]

        # Get current status from database
        old_status = None
        project_name = None
        if project_code:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT status, project_name FROM proposals WHERE project_code = ?",
                (project_code,)
            )
            row = cursor.fetchone()
            if row:
                old_status, project_name = row

        # Format display
        old_display = old_status or "Not set"
        new_display = new_status or "Unknown"
        name_display = f" ({project_name})" if project_name else ""

        summary = f"Update status for {project_code}{name_display}: {old_display} → {new_display}"

        changes = [
            {"field": "status", "old": old_status, "new": new_status},
        ]

        # If updating to Proposal Sent, also update proposal_sent_date
        if new_status == "Proposal Sent":
            email_date = suggested_data.get("email_date")
            changes.append({
                "field": "proposal_sent_date",
                "old": None,
                "new": email_date or datetime.now().strftime("%Y-%m-%d")
            })

        # Include evidence email info
        if suggested_data.get("evidence_email_id"):
            changes.append({
                "field": "evidence",
                "info": f"Email ID: {suggested_data['evidence_email_id']}"
            })

        return ChangePreview(
            table="proposals",
            action="update",
            summary=summary,
            changes=changes
        )

    def apply(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> SuggestionResult:
        """
        Update the proposal status and related fields.

        Returns rollback_data with old values for undo.
        """
        cursor = self.conn.cursor()

        project_code = suggestion.get("project_code") or suggested_data.get("project_code")
        suggestion_id = suggestion.get("suggestion_id")
        # Accept either 'new_status' or 'suggested_status' (GPT uses the latter)
        new_status = suggested_data.get("new_status") or suggested_data.get("suggested_status")

        # Normalize lowercase status to TitleCase for database consistency
        if new_status and new_status in STATUS_NORMALIZE:
            new_status = STATUS_NORMALIZE[new_status]

        if not project_code:
            return SuggestionResult(
                success=False,
                message="No project_code provided for status update",
                changes_made=[]
            )

        if not new_status:
            return SuggestionResult(
                success=False,
                message="No new_status provided for status update",
                changes_made=[]
            )

        # Get current values
        cursor.execute(
            """SELECT proposal_id, status, proposal_sent_date, last_status_change,
                      num_proposals_sent FROM proposals WHERE project_code = ?""",
            (project_code,)
        )
        row = cursor.fetchone()

        if not row:
            return SuggestionResult(
                success=False,
                message=f"No proposal found with project_code: {project_code}",
                changes_made=[]
            )

        proposal_id, old_status, old_sent_date, old_change_date, old_num_sent = row

        # Prepare update fields
        update_fields = ["status = ?", "last_status_change = date('now')", "status_changed_by = 'ai_suggestion'"]
        update_values = [new_status]

        # If Proposal Sent, update additional fields
        if new_status == "Proposal Sent":
            email_date = suggested_data.get("email_date", datetime.now().strftime("%Y-%m-%d"))
            update_fields.append("proposal_sent_date = ?")
            update_values.append(email_date)

            # Increment proposals sent count
            new_num_sent = (old_num_sent or 0) + 1
            update_fields.append("num_proposals_sent = ?")
            update_values.append(new_num_sent)

        # Add project_code for WHERE clause
        update_values.append(project_code)

        # Execute update
        cursor.execute(
            f"UPDATE proposals SET {', '.join(update_fields)} WHERE project_code = ?",
            update_values
        )
        self.conn.commit()

        # Record the changes
        changes_made = []

        # Record status change
        self._record_change(
            suggestion_id=suggestion_id,
            table_name="proposals",
            record_id=proposal_id,
            field_name="status",
            old_value=old_status,
            new_value=new_status,
            change_type="update"
        )
        changes_made.append({
            "table": "proposals",
            "record_id": proposal_id,
            "field": "status",
            "old_value": old_status,
            "new_value": new_status,
            "change_type": "update"
        })

        # If we updated sent date, record that too
        if new_status == "Proposal Sent":
            email_date = suggested_data.get("email_date", datetime.now().strftime("%Y-%m-%d"))
            self._record_change(
                suggestion_id=suggestion_id,
                table_name="proposals",
                record_id=proposal_id,
                field_name="proposal_sent_date",
                old_value=old_sent_date,
                new_value=email_date,
                change_type="update"
            )
            changes_made.append({
                "table": "proposals",
                "record_id": proposal_id,
                "field": "proposal_sent_date",
                "old_value": old_sent_date,
                "new_value": email_date,
                "change_type": "update"
            })

        self.conn.commit()

        return SuggestionResult(
            success=True,
            message=f"Updated {project_code} status: {old_status} → {new_status}",
            changes_made=changes_made,
            rollback_data={
                "proposal_id": proposal_id,
                "project_code": project_code,
                "old_status": old_status,
                "old_sent_date": old_sent_date,
                "old_change_date": old_change_date,
                "old_num_sent": old_num_sent
            }
        )

    def rollback(self, rollback_data: Dict[str, Any]) -> bool:
        """
        Restore the previous status and related fields.
        """
        proposal_id = rollback_data.get("proposal_id")
        project_code = rollback_data.get("project_code")
        old_status = rollback_data.get("old_status")
        old_sent_date = rollback_data.get("old_sent_date")
        old_change_date = rollback_data.get("old_change_date")
        old_num_sent = rollback_data.get("old_num_sent")

        if not proposal_id and not project_code:
            return False

        cursor = self.conn.cursor()

        # Restore all old values
        if proposal_id:
            cursor.execute(
                """UPDATE proposals
                   SET status = ?,
                       proposal_sent_date = ?,
                       last_status_change = ?,
                       num_proposals_sent = ?
                   WHERE proposal_id = ?""",
                (old_status, old_sent_date, old_change_date, old_num_sent, proposal_id)
            )
        else:
            cursor.execute(
                """UPDATE proposals
                   SET status = ?,
                       proposal_sent_date = ?,
                       last_status_change = ?,
                       num_proposals_sent = ?
                   WHERE project_code = ?""",
                (old_status, old_sent_date, old_change_date, old_num_sent, project_code)
            )

        # Mark change records as rolled back
        cursor.execute("""
            UPDATE suggestion_changes
            SET rolled_back = 1, rolled_back_at = datetime('now')
            WHERE table_name = 'proposals' AND record_id = ?
            AND field_name IN ('status', 'proposal_sent_date')
        """, (proposal_id,))

        self.conn.commit()

        return cursor.rowcount > 0 or True
