"""
Suggestion Handlers Package

This package provides a handler-based architecture for processing AI suggestions.
Each suggestion type has a dedicated handler that knows how to validate, preview,
apply, and rollback changes.

Usage:
    from backend.services.suggestion_handlers import HandlerRegistry, register_handler

    # Get a handler for a suggestion type
    handler = HandlerRegistry.get_handler('follow_up_needed', db_connection)
    if handler:
        errors = handler.validate(suggested_data)
        if not errors:
            preview = handler.preview(suggestion, suggested_data)
            result = handler.apply(suggestion, suggested_data)

    # Create a new handler
    @register_handler
    class MyHandler(BaseSuggestionHandler):
        suggestion_type = 'my_type'
        target_table = 'my_table'
        ...
"""

from .base import BaseSuggestionHandler, ChangePreview, SuggestionResult
from .registry import HandlerRegistry, register_handler

# Export public API
__all__ = [
    "BaseSuggestionHandler",
    "ChangePreview",
    "SuggestionResult",
    "HandlerRegistry",
    "register_handler",
]

# Handler imports - auto-register when package is imported
from .task_handler import FollowUpHandler
from .transcript_handler import TranscriptLinkHandler
from .contact_handler import ContactHandler
from .proposal_handler import FeeChangeHandler
from .deadline_handler import DeadlineHandler
from .info_handler import InfoHandler
from .email_link_handler import EmailLinkHandler
from .status_handler import ProposalStatusHandler
from .contact_link_handler import ContactLinkHandler
from .link_review_handler import LinkReviewHandler

# Add handlers to exports
__all__.extend([
    "FollowUpHandler",
    "TranscriptLinkHandler",
    "ContactHandler",
    "FeeChangeHandler",
    "DeadlineHandler",
    "InfoHandler",
    "EmailLinkHandler",
    "ProposalStatusHandler",
    "ContactLinkHandler",
    "LinkReviewHandler",
])
