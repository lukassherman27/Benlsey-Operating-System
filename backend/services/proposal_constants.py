"""
Proposal Constants - Shared status definitions and field mappings.

Consolidates duplicated constants from proposal_service.py, proposal_tracker_service.py,
and other proposal-related services.

Issue #378: Extract shared logic to reduce duplication
"""

from typing import List, Dict, Set

# =============================================================================
# STATUS DEFINITIONS
# =============================================================================

# All possible proposal statuses in workflow order
PROPOSAL_STATUSES = [
    'First Contact',
    'Meeting Held',
    'NDA Signed',
    'Proposal Prep',
    'Proposal Sent',
    'Negotiation',
    'MOU Signed',
    'On Hold',
    'Contract Signed',
    'Lost',
    'Declined',
    'Dormant',
    'Cancelled',
]

# Active pipeline statuses (proposals being actively worked)
ACTIVE_PIPELINE_STATUSES = [
    'First Contact',
    'Meeting Held',
    'NDA Signed',
    'Proposal Prep',
    'Proposal Sent',
    'Negotiation',
    'MOU Signed',
]

# Statuses where proposal is still "alive" but paused
PAUSED_STATUSES = ['On Hold']

# Terminal statuses (deal is closed)
TERMINAL_STATUSES = ['Contract Signed', 'Lost', 'Declined', 'Dormant', 'Cancelled']

# Won status
WON_STATUS = 'Contract Signed'

# Lost statuses (grouped as "Lost" in UI)
LOST_STATUSES = ['Lost', 'Declined']

# Default statuses for list views (active + paused, excludes terminal)
DEFAULT_ACTIVE_STATUSES = ACTIVE_PIPELINE_STATUSES + PAUSED_STATUSES

# Status aliases for query convenience
STATUS_ALIASES: Dict[str, List[str]] = {
    'active': DEFAULT_ACTIVE_STATUSES,
    'pipeline': ACTIVE_PIPELINE_STATUSES,
    'won': [WON_STATUS],
    'lost': LOST_STATUSES,
    'dormant': ['Dormant'],
    'on_hold': ['On Hold'],
    'terminal': TERMINAL_STATUSES,
    # Legacy aliases for backward compatibility
    'proposal': ['Proposal Sent'],
    'proposals': ACTIVE_PIPELINE_STATUSES,
}

# Status display order (for sorting)
STATUS_ORDER: Dict[str, int] = {
    'First Contact': 1,
    'Meeting Held': 2,
    'NDA Signed': 3,
    'Proposal Prep': 4,
    'Proposal Sent': 5,
    'Negotiation': 6,
    'MOU Signed': 7,
    'On Hold': 8,
    'Contract Signed': 9,
    'Lost': 10,
    'Declined': 11,
    'Dormant': 12,
    'Cancelled': 13,
}


# =============================================================================
# FIELD MAPPINGS
# =============================================================================

# Maps tracker/API field names to database column names
FIELD_NAME_MAPPING: Dict[str, str] = {
    'current_status': 'status',
    'current_remark': 'remarks',
    'project_summary': 'notes',
    'waiting_on': 'waiting_for',
    'next_steps': 'next_action',
    'internal_notes': 'status_notes',
}

# Fields allowed to be updated via API
UPDATABLE_PROPOSAL_FIELDS: Set[str] = {
    'project_name',
    'project_value',
    'country',
    'current_status',
    'current_remark',
    'project_summary',
    'waiting_on',
    'next_steps',
    'proposal_sent_date',
    'first_contact_date',
    'contact_person',
    'contact_email',
    'contact_phone',
    'ball_in_court',
    'waiting_for',
    'remarks',
    'status',
    # Action tracking
    'action_owner',
    'action_source',
    'next_action',
    'next_action_date',
    # Quick actions
    'won_date',
    'lost_date',
    'lost_reason',
    'lost_to_competitor',
    'contract_signed_date',
    'internal_notes',
}

# Sortable columns for proposals list
SORTABLE_PROPOSAL_COLUMNS = [
    'proposal_id',
    'project_code',
    'project_name',
    'status',
    'health_score',
    'days_since_contact',
    'is_active_project',
    'created_at',
    'updated_at',
    'project_value',
]


# =============================================================================
# HEALTH SCORE THRESHOLDS
# =============================================================================

HEALTH_SCORE_HEALTHY = 70
HEALTH_SCORE_AT_RISK = 40
HEALTH_SCORE_CRITICAL = 0

# Days thresholds for health calculations
DAYS_CRITICAL = 30
DAYS_AT_RISK = 14
DAYS_NEEDS_ATTENTION = 7

# Stalled threshold (for weekly changes report)
DAYS_STALLED = 21


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def resolve_status_alias(alias: str) -> List[str]:
    """
    Resolve a status alias to actual status values.

    Args:
        alias: Status alias like 'active', 'pipeline', 'won', etc.

    Returns:
        List of actual status values
    """
    return STATUS_ALIASES.get(alias.lower(), [alias])


def is_active_status(status: str) -> bool:
    """Check if a status is considered active (in pipeline)."""
    return status in ACTIVE_PIPELINE_STATUSES


def is_terminal_status(status: str) -> bool:
    """Check if a status is terminal (deal closed)."""
    return status in TERMINAL_STATUSES


def get_status_order(status: str) -> int:
    """Get the display order for a status (for sorting)."""
    return STATUS_ORDER.get(status, 99)


def map_field_name(field: str) -> str:
    """
    Map API/tracker field name to database column name.

    Args:
        field: Field name from API/tracker

    Returns:
        Corresponding database column name
    """
    return FIELD_NAME_MAPPING.get(field, field)
