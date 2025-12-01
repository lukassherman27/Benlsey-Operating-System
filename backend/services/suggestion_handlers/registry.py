"""
Handler registry for suggestion handlers.

The registry provides:
- Automatic registration via @register_handler decorator
- Lookup of handlers by suggestion type
- List of all registered types
"""

from typing import Dict, List, Optional, Type

from .base import BaseSuggestionHandler


class HandlerRegistry:
    """
    Central registry for suggestion handlers.

    Handlers register themselves using the @register_handler decorator.
    The registry maps suggestion_type strings to handler classes.
    """

    _handlers: Dict[str, Type[BaseSuggestionHandler]] = {}

    @classmethod
    def register(cls, handler_class: Type[BaseSuggestionHandler]) -> None:
        """
        Register a handler class for its suggestion_type.

        Args:
            handler_class: A subclass of BaseSuggestionHandler
        """
        if not handler_class.suggestion_type:
            raise ValueError(
                f"Handler {handler_class.__name__} must define suggestion_type"
            )
        cls._handlers[handler_class.suggestion_type] = handler_class

    @classmethod
    def get_handler(
        cls, suggestion_type: str, conn
    ) -> Optional[BaseSuggestionHandler]:
        """
        Get an instantiated handler for a suggestion type.

        Args:
            suggestion_type: The type of suggestion (e.g., 'follow_up_needed')
            conn: Database connection to pass to the handler

        Returns:
            Instantiated handler, or None if no handler registered
        """
        handler_class = cls._handlers.get(suggestion_type)
        if handler_class:
            return handler_class(conn)
        return None

    @classmethod
    def get_registered_types(cls) -> List[str]:
        """
        Get list of all registered suggestion types.

        Returns:
            List of suggestion type strings
        """
        return list(cls._handlers.keys())

    @classmethod
    def has_handler(cls, suggestion_type: str) -> bool:
        """
        Check if a handler exists for a suggestion type.

        Args:
            suggestion_type: The type to check

        Returns:
            True if handler is registered
        """
        return suggestion_type in cls._handlers

    @classmethod
    def get_actionable_types(cls) -> List[str]:
        """
        Get list of suggestion types that make database changes.

        Returns:
            List of suggestion types where is_actionable=True
        """
        return [
            stype for stype, handler in cls._handlers.items()
            if handler.is_actionable
        ]

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered handlers. Mainly for testing.
        """
        cls._handlers = {}


def register_handler(cls: Type[BaseSuggestionHandler]) -> Type[BaseSuggestionHandler]:
    """
    Decorator to register a handler class with the registry.

    Usage:
        @register_handler
        class FollowUpHandler(BaseSuggestionHandler):
            suggestion_type = 'follow_up_needed'
            ...

    Args:
        cls: The handler class to register

    Returns:
        The same class (unchanged)
    """
    HandlerRegistry.register(cls)
    return cls
