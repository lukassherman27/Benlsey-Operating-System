"""
Base class for suggestion handlers.

Each suggestion type has a corresponding handler that knows how to:
- validate: Check if the suggested data is valid
- preview: Generate a human-readable preview of what will change
- apply: Execute the changes in the database
- rollback: Undo the changes if needed
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ChangePreview:
    """Preview of what changes a suggestion will make."""
    table: str
    action: str  # 'insert', 'update', 'delete', 'none'
    summary: str  # Human-readable description
    changes: List[Dict[str, Any]] = field(default_factory=list)  # Field-level changes


@dataclass
class SuggestionResult:
    """Result of applying a suggestion."""
    success: bool
    message: str
    changes_made: List[Dict[str, Any]] = field(default_factory=list)
    rollback_data: Optional[Dict[str, Any]] = None


class BaseSuggestionHandler(ABC):
    """
    Abstract base class for all suggestion handlers.

    Subclasses must define:
    - suggestion_type: The type string this handler handles (e.g., 'follow_up_needed')
    - target_table: The primary table this handler modifies (e.g., 'tasks')
    - is_actionable: Whether this suggestion makes DB changes (default True)

    And implement all abstract methods.
    """

    suggestion_type: str = ""
    target_table: str = ""
    is_actionable: bool = True

    def __init__(self, db_connection):
        """
        Initialize handler with a database connection.

        Args:
            db_connection: SQLite connection object
        """
        self.conn = db_connection

    @abstractmethod
    def validate(self, suggested_data: Dict[str, Any]) -> List[str]:
        """
        Validate the suggested data before applying.

        Args:
            suggested_data: The data parsed from the suggestion

        Returns:
            List of validation error messages. Empty list if valid.
        """
        pass

    @abstractmethod
    def preview(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> ChangePreview:
        """
        Generate a preview of what changes will be made.

        Args:
            suggestion: The full suggestion record from ai_suggestions
            suggested_data: The parsed suggestion data

        Returns:
            ChangePreview with details of what will change
        """
        pass

    @abstractmethod
    def apply(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> SuggestionResult:
        """
        Apply the suggestion changes to the database.

        Args:
            suggestion: The full suggestion record from ai_suggestions
            suggested_data: The parsed suggestion data

        Returns:
            SuggestionResult with success status, message, and rollback data
        """
        pass

    @abstractmethod
    def rollback(self, rollback_data: Dict[str, Any]) -> bool:
        """
        Undo changes made by a previous apply() call.

        Args:
            rollback_data: Data returned from apply() to enable undo

        Returns:
            True if rollback succeeded, False otherwise
        """
        pass

    def _record_change(self, suggestion_id: int, table_name: str, record_id: int,
                       field_name: str, old_value: Any, new_value: Any,
                       change_type: str) -> None:
        """
        Record a change to the suggestion_changes audit table.

        Args:
            suggestion_id: ID of the suggestion being applied
            table_name: Table being modified
            record_id: ID of the record being modified
            field_name: Field being changed (or None for insert/delete)
            old_value: Previous value (or None for insert)
            new_value: New value (or None for delete)
            change_type: 'insert', 'update', or 'delete'
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO suggestion_changes
            (suggestion_id, table_name, record_id, field_name, old_value, new_value, change_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            suggestion_id,
            table_name,
            record_id,
            field_name,
            str(old_value) if old_value is not None else None,
            str(new_value) if new_value is not None else None,
            change_type
        ))
