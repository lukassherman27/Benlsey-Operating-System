"""
Proposal handler for fee_change suggestions.

Updates proposal project_value when fee change suggestions are approved.
"""

import re
from typing import Any, Dict, List, Optional

from .base import BaseSuggestionHandler, ChangePreview, SuggestionResult
from .registry import register_handler


def parse_fee_amount(amount_str: str) -> Optional[float]:
    """
    Parse a fee amount string into a numeric value.

    Handles formats like:
    - "$13.45M" -> 13450000.0
    - "$3.2M" -> 3200000.0
    - "$450,000" -> 450000.0
    - "1.5 million" -> 1500000.0

    Returns None if unable to parse.
    """
    if not amount_str:
        return None

    # Remove currency symbols and whitespace
    cleaned = amount_str.strip().replace("$", "").replace(",", "").replace(" ", "")

    # Check for M/million suffix
    multiplier = 1.0
    if cleaned.upper().endswith("M"):
        multiplier = 1_000_000
        cleaned = cleaned[:-1]
    elif cleaned.lower().endswith("million"):
        multiplier = 1_000_000
        cleaned = cleaned[:-7]
    elif cleaned.upper().endswith("K"):
        multiplier = 1_000
        cleaned = cleaned[:-1]

    try:
        return float(cleaned) * multiplier
    except ValueError:
        return None


@register_handler
class FeeChangeHandler(BaseSuggestionHandler):
    """
    Handler for fee_change suggestions.

    Updates the project_value field in the proposals table.
    The suggested_data contains 'amounts' array with fee values.
    """

    suggestion_type = "fee_change"
    target_table = "proposals"
    is_actionable = True

    def validate(self, suggested_data: Dict[str, Any]) -> List[str]:
        """
        Validate the suggested data for updating a proposal fee.

        Required: amounts array with at least one parseable value.
        The project_code comes from the suggestion record, not suggested_data.
        """
        errors = []

        amounts = suggested_data.get("amounts", [])
        if not amounts:
            errors.append("Fee change requires at least one amount value")
            return errors

        # Check if at least one amount can be parsed
        parsed_amounts = [parse_fee_amount(a) for a in amounts if parse_fee_amount(a) is not None]
        if not parsed_amounts:
            errors.append(f"Could not parse any amounts from: {amounts}")

        return errors

    def preview(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> ChangePreview:
        """
        Generate preview of the fee update that will be made.
        """
        project_code = suggestion.get("project_code") or suggested_data.get("project_code")
        amounts = suggested_data.get("amounts", [])

        # Get the first parseable amount as the new value
        new_value = None
        for amt in amounts:
            parsed = parse_fee_amount(amt)
            if parsed is not None:
                new_value = parsed
                break

        # Get current value from database
        old_value = None
        if project_code:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT project_value FROM proposals WHERE project_code = ?",
                (project_code,)
            )
            row = cursor.fetchone()
            if row:
                old_value = row[0]

        # Format for display
        old_display = f"${old_value:,.2f}" if old_value else "Not set"
        new_display = f"${new_value:,.2f}" if new_value else "Unknown"

        summary = f"Update fee for {project_code}: {old_display} → {new_display}"

        changes = [
            {"field": "project_value", "old": old_value, "new": new_value},
        ]

        if suggested_data.get("context"):
            changes.append({"field": "context", "info": suggested_data["context"][:100]})

        return ChangePreview(
            table="proposals",
            action="update",
            summary=summary,
            changes=changes
        )

    def apply(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> SuggestionResult:
        """
        Update the project_value in the proposals table.

        Returns rollback_data with the old value for undo.
        """
        cursor = self.conn.cursor()

        project_code = suggestion.get("project_code") or suggested_data.get("project_code")
        suggestion_id = suggestion.get("suggestion_id")
        amounts = suggested_data.get("amounts", [])

        if not project_code:
            return SuggestionResult(
                success=False,
                message="No project_code provided for fee change",
                changes_made=[]
            )

        # Get the first parseable amount as the new value
        new_value = None
        for amt in amounts:
            parsed = parse_fee_amount(amt)
            if parsed is not None:
                new_value = parsed
                break

        if new_value is None:
            return SuggestionResult(
                success=False,
                message=f"Could not parse any amounts from: {amounts}",
                changes_made=[]
            )

        # Get current value and proposal_id
        cursor.execute(
            "SELECT proposal_id, project_value FROM proposals WHERE project_code = ?",
            (project_code,)
        )
        row = cursor.fetchone()

        if not row:
            return SuggestionResult(
                success=False,
                message=f"No proposal found with project_code: {project_code}",
                changes_made=[]
            )

        proposal_id, old_value = row

        # Update the project_value
        cursor.execute(
            "UPDATE proposals SET project_value = ? WHERE project_code = ?",
            (new_value, project_code)
        )
        self.conn.commit()

        # Record the change in audit trail
        self._record_change(
            suggestion_id=suggestion_id,
            table_name="proposals",
            record_id=proposal_id,
            field_name="project_value",
            old_value=old_value,
            new_value=new_value,
            change_type="update"
        )
        self.conn.commit()

        old_display = f"${old_value:,.2f}" if old_value else "Not set"
        new_display = f"${new_value:,.2f}"

        return SuggestionResult(
            success=True,
            message=f"Updated {project_code} fee: {old_display} → {new_display}",
            changes_made=[{
                "table": "proposals",
                "record_id": proposal_id,
                "field": "project_value",
                "old_value": old_value,
                "new_value": new_value,
                "change_type": "update"
            }],
            rollback_data={
                "proposal_id": proposal_id,
                "project_code": project_code,
                "old_value": old_value
            }
        )

    def rollback(self, rollback_data: Dict[str, Any]) -> bool:
        """
        Restore the previous project_value.
        """
        proposal_id = rollback_data.get("proposal_id")
        project_code = rollback_data.get("project_code")
        old_value = rollback_data.get("old_value")

        if not proposal_id and not project_code:
            return False

        cursor = self.conn.cursor()

        # Restore the old value
        if proposal_id:
            cursor.execute(
                "UPDATE proposals SET project_value = ? WHERE proposal_id = ?",
                (old_value, proposal_id)
            )
        else:
            cursor.execute(
                "UPDATE proposals SET project_value = ? WHERE project_code = ?",
                (old_value, project_code)
            )

        # Mark the change record as rolled back
        cursor.execute("""
            UPDATE suggestion_changes
            SET rolled_back = 1, rolled_back_at = datetime('now')
            WHERE table_name = 'proposals' AND record_id = ? AND field_name = 'project_value'
        """, (proposal_id,))

        self.conn.commit()

        return cursor.rowcount > 0 or True
