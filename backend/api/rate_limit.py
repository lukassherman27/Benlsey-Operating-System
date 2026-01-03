"""
Rate limiting configuration for API endpoints.

Uses slowapi to limit requests per client IP.
Import the limiter here to avoid circular imports.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Global limiter instance - import this in routers
limiter = Limiter(key_func=get_remote_address)
