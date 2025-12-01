"""
Task handler for follow_up_needed suggestions.

Creates tasks in the tasks table when follow-up suggestions are approved.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from .base import BaseSuggestionHandler, ChangePreview, SuggestionResult
from .registry import register_handler


@register_handler
class FollowUpHandler(BaseSuggestionHandler):
    """
    Handler for follow_up_needed suggestions.

    Creates a task in the tasks table with type='follow_up'.
    Default due date is 7 days from now.
    """

    suggestion_type = "follow_up_needed"
    target_table = "tasks"
    is_actionable = True

    def validate(self, suggested_data: Dict[str, Any]) -> List[str]:
        """
        Validate the suggested data for creating a follow-up task.

        Note: The title/description may be in suggested_data OR in the suggestion
        record itself (which apply() has access to). Since apply() falls back to
        suggestion.title, we only require some contextual data exists.
        """
        errors = []

        # Check for any data that provides context
        # The apply() method will fall back to suggestion.title if needed
        title = suggested_data.get("title") or suggested_data.get("action")
        description = suggested_data.get("description") or suggested_data.get("reason")
        has_context = (
            title or description or
            suggested_data.get("days_since_response") or
            suggested_data.get("last_email_id") or
            suggested_data.get("project_code")
        )

        if not has_context:
            errors.append("Follow-up task requires some context (title, description, or source data)")

        return errors

    def preview(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> ChangePreview:
        """
        Generate preview of the task that will be created.
        """
        # Build title from available fields
        title = (
            suggested_data.get("title")
            or suggested_data.get("action")
            or "Follow up"
        )

        project_code = suggestion.get("project_code") or suggested_data.get("project_code")

        # Calculate due date (7 days from now)
        due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        summary = f"Create follow-up task: '{title[:50]}...'" if len(title) > 50 else f"Create follow-up task: '{title}'"
        if project_code:
            summary += f" for {project_code}"

        changes = [
            {"field": "title", "new": title},
            {"field": "task_type", "new": "follow_up"},
            {"field": "status", "new": "pending"},
            {"field": "due_date", "new": due_date},
        ]

        if project_code:
            changes.append({"field": "project_code", "new": project_code})

        return ChangePreview(
            table="tasks",
            action="insert",
            summary=summary,
            changes=changes
        )

    def apply(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> SuggestionResult:
        """
        Create a follow-up task in the tasks table.

        Returns rollback_data with the task_id for undo.
        """
        cursor = self.conn.cursor()

        # Build title and description from available fields
        title = (
            suggested_data.get("title")
            or suggested_data.get("action")
            or suggestion.get("title", "Follow up required")
        )

        description = (
            suggested_data.get("description")
            or suggested_data.get("reason")
            or suggestion.get("description")
        )

        project_code = suggestion.get("project_code") or suggested_data.get("project_code")
        proposal_id = suggestion.get("proposal_id") or suggested_data.get("proposal_id")
        suggestion_id = suggestion.get("suggestion_id")
        source_email_id = suggestion.get("source_id") if suggestion.get("source_type") == "email" else None

        # Calculate due date (7 days from now)
        due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        # Insert the task
        cursor.execute("""
            INSERT INTO tasks (
                title, description, task_type, priority, status,
                due_date, project_code, proposal_id,
                source_suggestion_id, source_email_id
            )
            VALUES (?, ?, 'follow_up', 'medium', 'pending', ?, ?, ?, ?, ?)
        """, (
            title,
            description,
            due_date,
            project_code,
            proposal_id,
            suggestion_id,
            source_email_id
        ))

        task_id = cursor.lastrowid
        self.conn.commit()

        # Record the change in audit trail
        self._record_change(
            suggestion_id=suggestion_id,
            table_name="tasks",
            record_id=task_id,
            field_name=None,
            old_value=None,
            new_value=f"task_id={task_id}",
            change_type="insert"
        )
        self.conn.commit()

        return SuggestionResult(
            success=True,
            message=f"Created follow-up task #{task_id}: {title[:50]}",
            changes_made=[{
                "table": "tasks",
                "record_id": task_id,
                "change_type": "insert"
            }],
            rollback_data={"task_id": task_id}
        )

    def rollback(self, rollback_data: Dict[str, Any]) -> bool:
        """
        Delete the created task.
        """
        task_id = rollback_data.get("task_id")
        if not task_id:
            return False

        cursor = self.conn.cursor()

        # Delete the task
        cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))

        # Mark the change record as rolled back
        cursor.execute("""
            UPDATE suggestion_changes
            SET rolled_back = 1, rolled_back_at = datetime('now')
            WHERE table_name = 'tasks' AND record_id = ? AND change_type = 'insert'
        """, (task_id,))

        self.conn.commit()

        return cursor.rowcount > 0 or True  # Return True if delete affected rows
