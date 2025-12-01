"""
Info handler for non-actionable suggestion types.

Handles informational suggestions that don't make database changes.
These suggestions are for display/awareness only.
"""

from typing import Any, Dict, List

from .base import BaseSuggestionHandler, ChangePreview, SuggestionResult
from .registry import register_handler


@register_handler
class InfoHandler(BaseSuggestionHandler):
    """
    Handler for informational suggestions that don't modify the database.

    Use this for suggestion types that:
    - Provide context/awareness only
    - Don't require any action
    - Should be marked as "acknowledged" rather than "applied"
    """

    suggestion_type = "info"
    target_table = ""
    is_actionable = False

    def validate(self, suggested_data: Dict[str, Any]) -> List[str]:
        """
        Validate the suggested data.

        Informational suggestions always pass validation since they
        don't make any changes.

        Returns:
            Empty list (no validation errors)
        """
        return []

    def preview(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> ChangePreview:
        """
        Generate a preview for this informational suggestion.

        Returns:
            ChangePreview indicating no changes will be made
        """
        return ChangePreview(
            table="",
            action="none",
            summary="Informational only - no database changes",
            changes=[]
        )

    def apply(self, suggestion: Dict[str, Any], suggested_data: Dict[str, Any]) -> SuggestionResult:
        """
        Apply the suggestion (no-op for informational types).

        Returns:
            SuggestionResult with success=True but no changes made
        """
        return SuggestionResult(
            success=True,
            message="Suggestion acknowledged (informational only)",
            changes_made=[],
            rollback_data=None
        )

    def rollback(self, rollback_data: Dict[str, Any]) -> bool:
        """
        Rollback the suggestion (no-op for informational types).

        Returns:
            True (nothing to undo)
        """
        return True
