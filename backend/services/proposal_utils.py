"""
Proposal Utilities - Shared query helpers and calculations.

Consolidates duplicated query patterns from proposal_service.py,
proposal_tracker_service.py, and other proposal-related services.

Issue #378: Extract shared logic to reduce duplication
"""

from typing import Optional, List, Dict, Any, Tuple
from .proposal_constants import (
    DEFAULT_ACTIVE_STATUSES,
    STATUS_ALIASES,
    HEALTH_SCORE_HEALTHY,
    HEALTH_SCORE_AT_RISK,
    DAYS_CRITICAL,
    DAYS_AT_RISK,
    DAYS_NEEDS_ATTENTION,
    LOST_STATUSES,
    WON_STATUS,
    map_field_name,
)


# =============================================================================
# STATUS RESOLUTION
# =============================================================================

def resolve_statuses(
    status: Optional[str],
    default_statuses: Optional[List[str]] = None,
) -> List[str]:
    """
    Normalize incoming status filters to actual status values.

    Handles:
    - Comma-separated status lists: "First Contact,Meeting Held"
    - Aliases: "active", "pipeline", "won", "lost"
    - Special values: "all", "*" returns empty list (no filter)

    Args:
        status: Optional comma-delimited status list or alias
        default_statuses: Default statuses when no explicit filter supplied

    Returns:
        List of normalized status strings. Empty list means "no filter".

    Examples:
        >>> resolve_statuses("active")
        ['First Contact', 'Meeting Held', 'NDA Signed', ...]

        >>> resolve_statuses("First Contact,Proposal Sent")
        ['First Contact', 'Proposal Sent']

        >>> resolve_statuses("all")
        []

        >>> resolve_statuses(None)
        ['First Contact', 'Meeting Held', ...]  # DEFAULT_ACTIVE_STATUSES
    """
    if not status:
        return list(default_statuses or DEFAULT_ACTIVE_STATUSES)

    statuses = []
    for part in status.split(','):
        value = part.strip()
        if not value:
            continue

        lowered = value.lower()

        # Special "all" value returns empty list (no filter)
        if lowered in ('all', '*'):
            return []

        # Check if this is an alias that maps to multiple statuses
        alias_statuses = STATUS_ALIASES.get(lowered)
        if alias_statuses:
            for real_status in alias_statuses:
                if real_status not in statuses:
                    statuses.append(real_status)
        else:
            # Not an alias, use the value as-is
            if value not in statuses:
                statuses.append(value)

    return statuses


def build_status_filter(
    statuses: List[str],
    column: str = "status",
) -> Tuple[str, List[Any]]:
    """
    Build SQL WHERE clause for status filtering.

    Args:
        statuses: List of status values to filter by
        column: Column name (default "status")

    Returns:
        Tuple of (SQL clause, params list)

    Examples:
        >>> build_status_filter(['First Contact', 'Proposal Sent'])
        ("status IN (?, ?)", ['First Contact', 'Proposal Sent'])

        >>> build_status_filter([])
        ("", [])
    """
    if not statuses:
        return "", []

    placeholders = ", ".join(["?"] * len(statuses))
    return f"{column} IN ({placeholders})", list(statuses)


# =============================================================================
# EMAIL STATS SUBQUERY
# =============================================================================

EMAIL_STATS_SUBQUERY = """
    (
        SELECT
            epl.proposal_id,
            COUNT(*) as email_count,
            MAX(e.date) as last_email_date,
            MIN(e.date) as first_email_date
        FROM email_proposal_links epl
        JOIN emails e ON epl.email_id = e.email_id
        GROUP BY epl.proposal_id
    )
"""


def get_email_stats_join(alias: str = "email_stats") -> str:
    """
    Get the email stats subquery for LEFT JOINing to proposals.

    Args:
        alias: Alias for the subquery (default "email_stats")

    Returns:
        SQL for LEFT JOIN with email_stats
    """
    return f"""
        LEFT JOIN {EMAIL_STATS_SUBQUERY} {alias}
        ON p.proposal_id = {alias}.proposal_id
    """


# =============================================================================
# DAYS CALCULATIONS
# =============================================================================

def days_since_sql(date_column: str, fallback_column: str = "created_at") -> str:
    """
    Generate SQL for calculating days since a date.

    Uses JULIANDAY for SQLite compatibility.

    Args:
        date_column: Primary date column to use
        fallback_column: Fallback if primary is NULL

    Returns:
        SQL expression that returns integer days

    Example:
        >>> days_since_sql("last_contact_date", "created_at")
        "CAST(JULIANDAY('now') - JULIANDAY(COALESCE(last_contact_date, created_at)) AS INTEGER)"
    """
    return f"CAST(JULIANDAY('now') - JULIANDAY(COALESCE({date_column}, {fallback_column})) AS INTEGER)"


DAYS_SINCE_CONTACT_SQL = days_since_sql("last_contact_date", "created_at")


# =============================================================================
# HEALTH SCORE CALCULATION
# =============================================================================

def calculate_health_score(proposal: Dict[str, Any]) -> float:
    """
    Calculate health score based on proposal data.

    Scoring logic:
    - Start at 100
    - Deduct for days since contact
    - Deduct if ball in court is 'us' and stale
    - Bonus for active communication
    - Consider status

    Args:
        proposal: Dict with proposal data (needs days_since_contact, ball_in_court,
                  status, email_count)

    Returns:
        Health score between 0-100
    """
    score = 100.0

    # Days since contact penalty
    days = proposal.get('days_since_contact')
    if days is not None:
        if days > DAYS_CRITICAL:
            score -= 40  # Critical
        elif days > DAYS_AT_RISK:
            score -= 20  # At risk
        elif days > DAYS_NEEDS_ATTENTION:
            score -= 10  # Needs attention

    # Ball in court penalty (if ball is with us and we're not acting)
    ball = (proposal.get('ball_in_court') or '').lower()
    if ball == 'us':
        if days is not None and days > DAYS_AT_RISK:
            score -= 20  # We're dropping the ball
        elif days is not None and days > DAYS_NEEDS_ATTENTION:
            score -= 10

    # Status-based adjustments
    status = proposal.get('status', '')
    if status in LOST_STATUSES:
        score = 0  # Terminal states
    elif status == WON_STATUS:
        score = 100  # Won
    elif status == 'Dormant':
        score = 20  # Low but not dead
    elif status == 'On Hold':
        score = 40  # Paused

    # Bonus for active communication
    email_count = proposal.get('email_count', 0) or 0
    if email_count > 20:
        score = min(100, score + 10)
    elif email_count > 10:
        score = min(100, score + 5)

    return max(0, min(100, score))  # Clamp to 0-100


def get_health_recommendation(health_score: Optional[float]) -> str:
    """
    Get action recommendation based on health score.

    Args:
        health_score: Health score (0-100) or None

    Returns:
        Human-readable recommendation string
    """
    if health_score is None:
        return "Insufficient data to assess health"

    if health_score >= 80:
        return "Healthy - Continue current engagement"
    elif health_score >= 60:
        return "Moderate - Consider follow-up"
    elif health_score >= HEALTH_SCORE_AT_RISK:
        return "At Risk - Immediate follow-up recommended"
    else:
        return "Critical - Urgent action required"


# =============================================================================
# PROPOSAL ENHANCEMENT
# =============================================================================

def enhance_proposal(proposal: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Enhance a proposal dict with calculated fields.

    Adds:
    - health_score: Calculated if not set or 0
    - health_calculated: Boolean flag

    Args:
        proposal: Proposal dict from database

    Returns:
        Enhanced proposal dict (same dict, mutated)
    """
    if proposal is None:
        return None

    # Calculate health_score if not set or 0
    stored_health = proposal.get('health_score')
    if stored_health is None or stored_health == 0:
        proposal['health_score'] = calculate_health_score(proposal)
        proposal['health_calculated'] = True
    else:
        proposal['health_score'] = stored_health
        proposal['health_calculated'] = True

    return proposal


def enhance_proposals(proposals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Enhance a list of proposals with calculated fields."""
    return [enhance_proposal(p) for p in proposals]


# =============================================================================
# ERROR RESPONSE HELPERS
# =============================================================================

class ProposalNotFoundError(Exception):
    """Raised when a proposal is not found."""

    def __init__(self, identifier: str, message: Optional[str] = None):
        self.identifier = identifier
        self.message = message or f"Proposal '{identifier}' not found"
        super().__init__(self.message)


def not_found_response(identifier: str) -> Dict[str, Any]:
    """
    Generate a standard "not found" response.

    Args:
        identifier: Project code or proposal ID that wasn't found

    Returns:
        Dict with success=False and error message
    """
    return {
        'success': False,
        'error': f"Proposal '{identifier}' not found"
    }


def success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrap data in a standard success response.

    Args:
        data: The data to return

    Returns:
        Dict with success=True and merged data
    """
    return {'success': True, **data}


def error_response(message: str) -> Dict[str, Any]:
    """
    Generate a standard error response.

    Args:
        message: Error message

    Returns:
        Dict with success=False and error message
    """
    return {'success': False, 'error': message}


# =============================================================================
# FIELD MAPPING FOR UPDATES
# =============================================================================

def map_update_fields(
    updates: Dict[str, Any],
    allowed_fields: set,
) -> Dict[str, Any]:
    """
    Filter and map update fields for database write.

    Args:
        updates: Raw update dict from API
        allowed_fields: Set of allowed field names

    Returns:
        Dict with only allowed fields, mapped to DB column names
    """
    result = {}
    for key, value in updates.items():
        if key in allowed_fields:
            db_key = map_field_name(key)
            result[db_key] = value
    return result
