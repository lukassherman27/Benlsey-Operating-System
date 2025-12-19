"""
Action item handler for action_item and action_required suggestions.

Creates tasks in the tasks table when action item suggestions are approved.
These are tasks detected from email content by GPT analysis.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from .base import BaseSuggestionHandler, ChangePreview, SuggestionResult
from .registry import register_handler


@register_handler
class ActionItemHandler(BaseSuggestionHandler):
    """
    Handler for action_item suggestions.

    Creates a task in the tasks table with details extracted from email.
    Uses the new category and assigned_staff_id fields.
    """

    suggestion_type = "action_item"
    target_table = "tasks"
    is_actionable = True

    def validate(self, suggested_data: Dict[str, Any]) -> List[str]:
        """
        Validate the suggested data for creating an action item task.
        """
        errors = []

        task_title = suggested_data.get("task_title")
        if not task_title:
            errors.append("Action item requires a task title")

        return errors

    def preview(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> ChangePreview:
        """
        Generate preview of the task that will be created.
        """
        task_title = suggested_data.get("task_title", "Action item")
        task_description = suggested_data.get("task_description", "")
        assignee_hint = suggested_data.get("assignee_hint", "us")
        due_date_hint = suggested_data.get("due_date_hint")
        priority_hint = suggested_data.get("priority_hint", "medium")
        category = suggested_data.get("category", "Project")
        project_code = suggestion.get("project_code") or suggested_data.get("project_code")

        # Calculate due date
        if due_date_hint:
            due_date = due_date_hint
        else:
            due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        summary = f"Create task: '{task_title[:50]}'"
        if project_code:
            summary += f" for {project_code}"

        changes = [
            {"field": "title", "new": task_title},
            {"field": "description", "new": task_description[:100] + "..." if len(task_description) > 100 else task_description},
            {"field": "task_type", "new": "action_item"},
            {"field": "status", "new": "pending"},
            {"field": "due_date", "new": due_date},
            {"field": "priority", "new": priority_hint},
            {"field": "category", "new": category},
            {"field": "assignee", "new": assignee_hint},
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
        Create an action item task in the tasks table.
        """
        cursor = self.conn.cursor()

        task_title = suggested_data.get("task_title", "Action item")
        task_description = suggested_data.get("task_description", "")
        assignee_hint = suggested_data.get("assignee_hint", "us")
        due_date_hint = suggested_data.get("due_date_hint")
        priority_hint = suggested_data.get("priority_hint", "medium")
        category = suggested_data.get("category", "Project")

        project_code = suggestion.get("project_code") or suggested_data.get("project_code")
        proposal_id = suggestion.get("proposal_id") or suggested_data.get("proposal_id")
        suggestion_id = suggestion.get("suggestion_id")
        source_email_id = suggestion.get("source_id") if suggestion.get("source_type") == "email" else None

        # Add source quote to description if available
        source_quote = suggested_data.get("source_quote")
        if source_quote and task_description:
            task_description = f"{task_description}\n\nFrom email: \"{source_quote}\""
        elif source_quote:
            task_description = f"From email: \"{source_quote}\""

        # Calculate due date
        if due_date_hint:
            due_date = due_date_hint
        else:
            due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        # Map priority
        priority_map = {"critical": "high", "high": "high", "medium": "medium", "low": "low"}
        priority = priority_map.get(priority_hint, "medium")

        # Insert the task with new category field
        cursor.execute("""
            INSERT INTO tasks (
                title, description, task_type, priority, status,
                due_date, project_code, proposal_id, assignee, category,
                source_suggestion_id, source_email_id
            )
            VALUES (?, ?, 'action_item', ?, 'pending', ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_title,
            task_description,
            priority,
            due_date,
            project_code,
            proposal_id,
            assignee_hint,
            category,
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
            message=f"Created task #{task_id}: {task_title[:50]}",
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

        cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))

        cursor.execute("""
            UPDATE suggestion_changes
            SET rolled_back = 1, rolled_back_at = datetime('now')
            WHERE table_name = 'tasks' AND record_id = ? AND change_type = 'insert'
        """, (task_id,))

        self.conn.commit()

        return cursor.rowcount > 0 or True


@register_handler
class ActionRequiredHandler(ActionItemHandler):
    """
    Handler for action_required suggestions.

    Inherits from ActionItemHandler - same logic, different suggestion type.
    GPT generates 'action_required' while the system also has 'action_item'.
    This handler ensures both types create tasks.
    """

    suggestion_type = "action_required"
