"""
Meeting handler for meeting_detected suggestions.

Creates meetings in the meetings table when meeting suggestions are approved.
These are meetings detected from email content by GPT analysis.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .base import BaseSuggestionHandler, ChangePreview, SuggestionResult
from .registry import register_handler


@register_handler
class MeetingHandler(BaseSuggestionHandler):
    """
    Handler for meeting_detected suggestions.

    Creates a meeting in the meetings table with details extracted from email.
    Handles meeting requests, confirmations, and reschedules.
    """

    suggestion_type = "meeting_detected"
    target_table = "meetings"
    is_actionable = True

    def validate(self, suggested_data: Dict[str, Any]) -> List[str]:
        """
        Validate the suggested data for creating a meeting.
        """
        errors = []

        meeting_purpose = suggested_data.get("meeting_purpose")
        if not meeting_purpose:
            errors.append("Meeting requires a purpose/title")

        return errors

    def preview(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> ChangePreview:
        """
        Generate preview of the meeting that will be created.
        """
        meeting_purpose = suggested_data.get("meeting_purpose", "Meeting")
        meeting_type = suggested_data.get("meeting_type", "request")
        proposed_date = suggested_data.get("proposed_date")
        proposed_time = suggested_data.get("proposed_time")
        participants = suggested_data.get("participants", [])
        location_hint = suggested_data.get("location_hint")
        project_code = suggestion.get("project_code") or suggested_data.get("project_code")

        # Format date/time
        if proposed_date:
            date_str = proposed_date
        else:
            date_str = "TBD"

        if proposed_time:
            time_str = proposed_time
        else:
            time_str = "TBD"

        summary = f"Create meeting: '{meeting_purpose[:40]}' ({date_str})"
        if project_code:
            summary += f" for {project_code}"

        # Determine status based on meeting type
        if meeting_type == "confirmation":
            status = "confirmed"
        elif meeting_type == "reschedule":
            status = "pending"
        else:
            status = "tentative"

        changes = [
            {"field": "title", "new": meeting_purpose},
            {"field": "meeting_date", "new": date_str},
            {"field": "start_time", "new": time_str},
            {"field": "status", "new": status},
            {"field": "meeting_type", "new": meeting_type},
        ]

        if participants:
            changes.append({"field": "participants", "new": ", ".join(participants[:3]) + ("..." if len(participants) > 3 else "")})

        if location_hint:
            changes.append({"field": "location", "new": location_hint})

        if project_code:
            changes.append({"field": "project_code", "new": project_code})

        return ChangePreview(
            table="meetings",
            action="insert",
            summary=summary,
            changes=changes
        )

    def apply(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> SuggestionResult:
        """
        Create a meeting in the meetings table.
        """
        cursor = self.conn.cursor()

        meeting_purpose = suggested_data.get("meeting_purpose", "Meeting")
        meeting_type = suggested_data.get("meeting_type", "request")
        proposed_date = suggested_data.get("proposed_date")
        proposed_time = suggested_data.get("proposed_time")
        participants = suggested_data.get("participants", [])
        location_hint = suggested_data.get("location_hint")
        source_quote = suggested_data.get("source_quote")

        project_code = suggestion.get("project_code") or suggested_data.get("project_code")
        proposal_id = suggestion.get("proposal_id") or suggested_data.get("proposal_id")
        suggestion_id = suggestion.get("suggestion_id")
        source_email_id = suggestion.get("source_id") if suggestion.get("source_type") == "email" else None

        # Determine status based on meeting type
        if meeting_type == "confirmation":
            status = "confirmed"
        elif meeting_type == "reschedule":
            status = "pending"
        else:
            status = "tentative"

        # Build notes with source quote
        notes = f"Detected from email. Type: {meeting_type}"
        if source_quote:
            notes += f"\n\nFrom email: \"{source_quote}\""

        # Format participants as JSON for storage
        participants_json = json.dumps(participants) if participants else None

        # Lookup proposal_id from project_code if not provided
        if project_code and not proposal_id:
            result = cursor.execute(
                "SELECT proposal_id FROM proposals WHERE project_code = ?",
                (project_code,)
            ).fetchone()
            if result:
                proposal_id = result[0]

        # Insert the meeting
        cursor.execute("""
            INSERT INTO meetings (
                title, meeting_date, start_time, status,
                location, participants, notes,
                project_code, proposal_id, source_email_id,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            meeting_purpose,
            proposed_date,
            proposed_time,
            status,
            location_hint,
            participants_json,
            notes,
            project_code,
            proposal_id,
            source_email_id
        ))

        meeting_id = cursor.lastrowid
        self.conn.commit()

        # Record the change in audit trail
        self._record_change(
            suggestion_id=suggestion_id,
            table_name="meetings",
            record_id=meeting_id,
            field_name=None,
            old_value=None,
            new_value=f"meeting_id={meeting_id}",
            change_type="insert"
        )
        self.conn.commit()

        date_str = proposed_date or "TBD"
        return SuggestionResult(
            success=True,
            message=f"Created meeting #{meeting_id}: {meeting_purpose[:40]} ({date_str})",
            changes_made=[{
                "table": "meetings",
                "record_id": meeting_id,
                "change_type": "insert"
            }],
            rollback_data={"meeting_id": meeting_id}
        )

    def rollback(self, rollback_data: Dict[str, Any]) -> bool:
        """
        Delete the created meeting.
        """
        meeting_id = rollback_data.get("meeting_id")
        if not meeting_id:
            return False

        cursor = self.conn.cursor()

        cursor.execute("DELETE FROM meetings WHERE meeting_id = ?", (meeting_id,))

        cursor.execute("""
            UPDATE suggestion_changes
            SET rolled_back = 1, rolled_back_at = datetime('now')
            WHERE table_name = 'meetings' AND record_id = ? AND change_type = 'insert'
        """, (meeting_id,))

        self.conn.commit()

        return cursor.rowcount > 0 or True
