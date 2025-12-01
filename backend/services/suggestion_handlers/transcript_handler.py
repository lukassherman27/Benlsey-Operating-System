"""
Transcript handler for transcript_link suggestions.

Links meeting transcripts to proposals when suggestions are approved.
"""

from typing import Any, Dict, List

from .base import BaseSuggestionHandler, ChangePreview, SuggestionResult
from .registry import register_handler


@register_handler
class TranscriptLinkHandler(BaseSuggestionHandler):
    """
    Handler for transcript_link suggestions.

    Updates meeting_transcripts to set proposal_id and detected_project_code.
    Stores old values for rollback.
    """

    suggestion_type = "transcript_link"
    target_table = "meeting_transcripts"
    is_actionable = True

    def validate(self, suggested_data: Dict[str, Any]) -> List[str]:
        """
        Validate the suggested data for linking a transcript.

        Required: transcript_id and either proposal_id or project_code.
        """
        errors = []

        transcript_id = suggested_data.get("transcript_id") or suggested_data.get("meeting_id")
        if not transcript_id:
            errors.append("Transcript ID is required")

        proposal_id = suggested_data.get("proposal_id")
        project_code = suggested_data.get("project_code")

        if not proposal_id and not project_code:
            errors.append("Either proposal_id or project_code is required")

        return errors

    def preview(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> ChangePreview:
        """
        Generate preview of the transcript link that will be created.
        """
        transcript_id = suggested_data.get("transcript_id") or suggested_data.get("meeting_id")
        proposal_id = suggested_data.get("proposal_id") or suggestion.get("proposal_id")
        project_code = suggested_data.get("project_code") or suggestion.get("project_code")

        # Get current values for comparison
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT proposal_id, detected_project_code, meeting_title
            FROM meeting_transcripts
            WHERE id = ?
        """, (transcript_id,))
        current = cursor.fetchone()

        meeting_title = current[2] if current else "Unknown transcript"
        current_proposal = current[0] if current else None
        current_project = current[1] if current else None

        summary = f"Link transcript '{meeting_title[:40]}' to {project_code or f'proposal #{proposal_id}'}"

        changes = []
        if proposal_id and proposal_id != current_proposal:
            changes.append({
                "field": "proposal_id",
                "old": current_proposal,
                "new": proposal_id
            })
        if project_code and project_code != current_project:
            changes.append({
                "field": "detected_project_code",
                "old": current_project,
                "new": project_code
            })

        return ChangePreview(
            table="meeting_transcripts",
            action="update",
            summary=summary,
            changes=changes
        )

    def apply(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> SuggestionResult:
        """
        Update meeting_transcripts to link to proposal/project.

        Returns rollback_data with old values for undo.
        """
        cursor = self.conn.cursor()

        transcript_id = suggested_data.get("transcript_id") or suggested_data.get("meeting_id")
        proposal_id = suggested_data.get("proposal_id") or suggestion.get("proposal_id")
        project_code = suggested_data.get("project_code") or suggestion.get("project_code")
        suggestion_id = suggestion.get("suggestion_id")

        # Get current values for rollback
        cursor.execute("""
            SELECT proposal_id, detected_project_code
            FROM meeting_transcripts
            WHERE id = ?
        """, (transcript_id,))
        old_values = cursor.fetchone()

        if not old_values:
            return SuggestionResult(
                success=False,
                message=f"Transcript #{transcript_id} not found",
                changes_made=[],
                rollback_data=None
            )

        old_proposal_id = old_values[0]
        old_project_code = old_values[1]

        # Build update query dynamically based on what we're updating
        updates = []
        params = []

        if proposal_id:
            updates.append("proposal_id = ?")
            params.append(proposal_id)

        if project_code:
            updates.append("detected_project_code = ?")
            params.append(project_code)

        if not updates:
            return SuggestionResult(
                success=False,
                message="No updates to apply",
                changes_made=[],
                rollback_data=None
            )

        params.append(transcript_id)

        cursor.execute(f"""
            UPDATE meeting_transcripts
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)

        self.conn.commit()

        # Record changes in audit trail
        if proposal_id and proposal_id != old_proposal_id:
            self._record_change(
                suggestion_id=suggestion_id,
                table_name="meeting_transcripts",
                record_id=transcript_id,
                field_name="proposal_id",
                old_value=old_proposal_id,
                new_value=proposal_id,
                change_type="update"
            )

        if project_code and project_code != old_project_code:
            self._record_change(
                suggestion_id=suggestion_id,
                table_name="meeting_transcripts",
                record_id=transcript_id,
                field_name="detected_project_code",
                old_value=old_project_code,
                new_value=project_code,
                change_type="update"
            )

        self.conn.commit()

        message = f"Linked transcript #{transcript_id}"
        if project_code:
            message += f" to {project_code}"
        elif proposal_id:
            message += f" to proposal #{proposal_id}"

        return SuggestionResult(
            success=True,
            message=message,
            changes_made=[{
                "table": "meeting_transcripts",
                "record_id": transcript_id,
                "change_type": "update"
            }],
            rollback_data={
                "transcript_id": transcript_id,
                "old_proposal_id": old_proposal_id,
                "old_project_code": old_project_code
            }
        )

    def rollback(self, rollback_data: Dict[str, Any]) -> bool:
        """
        Restore old proposal_id and project_code values.
        """
        transcript_id = rollback_data.get("transcript_id")
        if not transcript_id:
            return False

        cursor = self.conn.cursor()

        old_proposal_id = rollback_data.get("old_proposal_id")
        old_project_code = rollback_data.get("old_project_code")

        # Restore old values (including None if they were originally null)
        cursor.execute("""
            UPDATE meeting_transcripts
            SET proposal_id = ?, detected_project_code = ?
            WHERE id = ?
        """, (old_proposal_id, old_project_code, transcript_id))

        # Mark the change records as rolled back
        cursor.execute("""
            UPDATE suggestion_changes
            SET rolled_back = 1, rolled_back_at = datetime('now')
            WHERE table_name = 'meeting_transcripts' AND record_id = ?
            AND change_type = 'update' AND rolled_back = 0
        """, (transcript_id,))

        self.conn.commit()

        return True
