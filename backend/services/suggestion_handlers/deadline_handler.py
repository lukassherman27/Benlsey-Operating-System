"""
Deadline handler for deadline_detected suggestions.

Creates deliverables in the deliverables table when deadline suggestions are approved.
(Updated from tasks to deliverables with migration 086)
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .base import BaseSuggestionHandler, ChangePreview, SuggestionResult
from .registry import register_handler


def parse_deadline_date(date_str: str) -> Optional[str]:
    """
    Parse a deadline date string into YYYY-MM-DD format.

    Handles formats like:
    - "August" -> End of August current/next year
    - "2025-08-31" -> As-is
    - "August 15" -> August 15 current/next year
    - "end of August" -> Last day of August

    Returns None if unable to parse.
    """
    if not date_str:
        return None

    date_str = date_str.strip().lower()
    current_year = datetime.now().year
    current_month = datetime.now().month

    # Month name mapping
    months = {
        "january": 1, "jan": 1,
        "february": 2, "feb": 2,
        "march": 3, "mar": 3,
        "april": 4, "apr": 4,
        "may": 5,
        "june": 6, "jun": 6,
        "july": 7, "jul": 7,
        "august": 8, "aug": 8,
        "september": 9, "sep": 9, "sept": 9,
        "october": 10, "oct": 10,
        "november": 11, "nov": 11,
        "december": 12, "dec": 12,
    }

    # Try ISO format first
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
        return parsed.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # Try common date formats
    formats = ["%B %d", "%b %d", "%B %d, %Y", "%b %d, %Y", "%m/%d/%Y", "%m/%d"]
    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str, fmt)
            # Add current year if not specified
            if parsed.year == 1900:
                year = current_year if parsed.month >= current_month else current_year + 1
                parsed = parsed.replace(year=year)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Handle month names (e.g., "August", "end of August")
    for month_name, month_num in months.items():
        if month_name in date_str:
            # Determine year (use next year if month has passed)
            year = current_year if month_num >= current_month else current_year + 1

            # Default to end of month for just month name
            if month_num == 12:
                last_day = 31
            elif month_num in [4, 6, 9, 11]:
                last_day = 30
            elif month_num == 2:
                # Check leap year
                last_day = 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28
            else:
                last_day = 31

            return f"{year}-{month_num:02d}-{last_day:02d}"

    # Default: 30 days from now if can't parse
    return None


@register_handler
class DeadlineHandler(BaseSuggestionHandler):
    """
    Handler for deadline_detected suggestions.

    Creates a deliverable in the deliverables table.
    Uses the detected deadline date(s) from the suggestion.
    """

    suggestion_type = "deadline_detected"
    target_table = "deliverables"
    is_actionable = True

    def validate(self, suggested_data: Dict[str, Any]) -> List[str]:
        """
        Validate the suggested data for creating a deliverable.

        Required: deliverable_name or dates/context describing the deadline.
        """
        errors = []

        deliverable_name = suggested_data.get("deliverable_name")
        dates = suggested_data.get("dates", [])
        context = suggested_data.get("context", "")
        deadline_date = suggested_data.get("deadline_date")

        if not deliverable_name and not dates and not context:
            errors.append("Deliverable requires a name, dates, or context")

        return errors

    def preview(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> ChangePreview:
        """
        Generate preview of the deliverable that will be created.
        """
        deliverable_name = suggested_data.get("deliverable_name")
        deliverable_type = suggested_data.get("deliverable_type", "other")
        dates = suggested_data.get("dates", [])
        context = suggested_data.get("context", "")
        deadline_date = suggested_data.get("deadline_date")
        project_code = suggestion.get("project_code") or suggested_data.get("project_code")

        # Determine name
        if deliverable_name:
            name = deliverable_name
        elif context:
            name = context[:80] if len(context) <= 80 else context[:77] + "..."
        else:
            name = "Deliverable"

        # Try to parse the due date
        due_date = deadline_date
        if not due_date:
            for date_str in dates:
                parsed = parse_deadline_date(date_str)
                if parsed:
                    due_date = parsed
                    break

        # Default to 30 days if no date parseable
        if not due_date:
            due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        summary = f"Create deliverable: '{name[:40]}'"
        if project_code:
            summary += f" for {project_code}"
        summary += f" (due: {due_date})"

        changes = [
            {"field": "name", "new": name},
            {"field": "deliverable_type", "new": deliverable_type},
            {"field": "status", "new": "pending"},
            {"field": "due_date", "new": due_date},
            {"field": "priority", "new": "high"},
        ]

        if project_code:
            changes.append({"field": "project_code", "new": project_code})

        if dates:
            changes.append({"field": "detected_dates", "info": ", ".join(dates)})

        return ChangePreview(
            table="deliverables",
            action="insert",
            summary=summary,
            changes=changes
        )

    def apply(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> SuggestionResult:
        """
        Create a deliverable in the deliverables table.

        Returns rollback_data with the deliverable_id for undo.
        """
        cursor = self.conn.cursor()

        deliverable_name = suggested_data.get("deliverable_name")
        deliverable_type = suggested_data.get("deliverable_type", "other")
        dates = suggested_data.get("dates", [])
        context = suggested_data.get("context", "")
        deadline_date = suggested_data.get("deadline_date")
        description = suggested_data.get("description", "")
        source_quote = suggested_data.get("source_quote")

        project_code = suggestion.get("project_code") or suggested_data.get("project_code")
        suggestion_id = suggestion.get("suggestion_id")
        source_email_id = suggestion.get("source_id") if suggestion.get("source_type") == "email" else None

        # Determine name
        if deliverable_name:
            name = deliverable_name
        elif context:
            name = context[:100]
        else:
            name = "Deliverable detected"

        # Build description with detected dates and context
        full_description = description
        if dates and not full_description:
            full_description = f"Deadline detected: {', '.join(dates)}"
        if context and full_description:
            full_description = f"{full_description}\n\nContext: {context}"
        elif context:
            full_description = context
        if source_quote:
            full_description = f"{full_description}\n\nFrom email: \"{source_quote}\"" if full_description else f"From email: \"{source_quote}\""

        # Parse due date
        due_date = deadline_date
        if not due_date:
            for date_str in dates:
                parsed = parse_deadline_date(date_str)
                if parsed:
                    due_date = parsed
                    break

        # Default to 30 days if no date parseable
        if not due_date:
            due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        # Look up project_id from project_code
        project_id = None
        if project_code:
            result = cursor.execute(
                "SELECT project_id FROM projects WHERE project_code = ?",
                (project_code,)
            ).fetchone()
            if result:
                project_id = result[0]

        # Insert the deliverable
        cursor.execute("""
            INSERT INTO deliverables (
                name, description, deliverable_type, status, priority,
                due_date, project_code, project_id,
                created_at, created_by
            )
            VALUES (?, ?, ?, 'pending', 'high', ?, ?, ?, datetime('now'), 'ai_suggestion')
        """, (
            name,
            full_description,
            deliverable_type,
            due_date,
            project_code,
            project_id
        ))

        deliverable_id = cursor.lastrowid
        self.conn.commit()

        # Record the change in audit trail
        self._record_change(
            suggestion_id=suggestion_id,
            table_name="deliverables",
            record_id=deliverable_id,
            field_name=None,
            old_value=None,
            new_value=f"deliverable_id={deliverable_id}",
            change_type="insert"
        )
        self.conn.commit()

        return SuggestionResult(
            success=True,
            message=f"Created deliverable #{deliverable_id}: {name[:50]} (due: {due_date})",
            changes_made=[{
                "table": "deliverables",
                "record_id": deliverable_id,
                "change_type": "insert"
            }],
            rollback_data={"deliverable_id": deliverable_id}
        )

    def rollback(self, rollback_data: Dict[str, Any]) -> bool:
        """
        Delete the created deliverable.
        """
        deliverable_id = rollback_data.get("deliverable_id")
        if not deliverable_id:
            return False

        cursor = self.conn.cursor()

        cursor.execute("DELETE FROM deliverables WHERE deliverable_id = ?", (deliverable_id,))

        cursor.execute("""
            UPDATE suggestion_changes
            SET rolled_back = 1, rolled_back_at = datetime('now')
            WHERE table_name = 'deliverables' AND record_id = ? AND change_type = 'insert'
        """, (deliverable_id,))

        self.conn.commit()

        return cursor.rowcount > 0 or True
