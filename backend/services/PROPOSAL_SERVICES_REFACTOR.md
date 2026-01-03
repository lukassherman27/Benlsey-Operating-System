# Proposal Services Refactor Analysis

**Issue:** #378
**Date:** January 2026
**Status:** Phase 1 Complete - Minimal refactor with shared utilities

## Overview

This document summarizes the findings from analyzing proposal-related services and the refactoring work done in Phase 1.

## Services Analyzed

| Service | Lines | Purpose | Uses BaseService |
|---------|-------|---------|------------------|
| `proposal_service.py` | 732 | Core CRUD, health scores, stats | Yes |
| `proposal_tracker_service.py` | 740 | Tracker UI operations, updates | Yes |
| `proposal_query_service.py` | 261 | Search across proposals/projects | **No** (raw sqlite3) |
| `proposal_story_service.py` | 457 | Story/timeline generation | Yes |
| `proposal_detail_story_service.py` | 700+ | Detailed story with threads | Yes |
| `proposal_intelligence_service.py` | 401 | AI-powered context/assistance | Yes |

## Issues Found

### 1. Duplicate Query Patterns

**Status constants duplicated in 3+ files:**
- `proposal_service.py`: `DEFAULT_ACTIVE_STATUSES`, `STATUS_ALIASES`
- `proposal_tracker_service.py`: Hardcoded status lists in SQL
- `proposal_query_service.py`: No status constants

**Email stats subquery duplicated in 3+ places:**
```sql
SELECT proposal_id, COUNT(*) as email_count, MAX(e.date) as last_email_date, MIN(e.date) as first_email_date
FROM email_proposal_links epl JOIN emails e ON epl.email_id = e.email_id
GROUP BY proposal_id
```

**Days calculation duplicated:**
```sql
CAST(JULIANDAY('now') - JULIANDAY(COALESCE(last_contact_date, created_at)) AS INTEGER)
```

### 2. Inconsistent Error Handling

| Service | Not Found Response |
|---------|-------------------|
| `ProposalService` | Returns `None` |
| `ProposalTrackerService` | Returns `{'success': False, 'message': ...}` |
| `ProposalIntelligenceService` | Returns `{'success': False, 'error': ...}` |
| `ProposalDetailStoryService` | Raises `ValueError` |
| `ProposalStoryService` | Returns `{'success': False, 'error': ...}` |

### 3. Mixed Naming Conventions

- Response fields: `project_title` vs `project_name`
- Field mappings: `current_status` → `status`, `current_remark` → `remarks`
- Tracker vs core service use different field names for same data

### 4. ProposalQueryService Doesn't Use BaseService

This service creates raw SQLite connections, missing:
- Connection retry logic for OneDrive sync
- Consistent row factory
- PRAGMA settings (foreign keys, busy timeout)

## Phase 1 Changes (This PR)

### New Files Created

1. **`proposal_constants.py`**
   - Centralized status definitions
   - Status aliases and ordering
   - Field name mappings
   - Health score thresholds
   - Helper functions for status resolution

2. **`proposal_utils.py`**
   - `resolve_statuses()` - Shared status filter resolution
   - `build_status_filter()` - SQL WHERE clause builder
   - `calculate_health_score()` - Shared health calculation
   - `get_health_recommendation()` - Recommendation text
   - `enhance_proposal()` / `enhance_proposals()` - Proposal enhancement
   - Error response helpers (`not_found_response`, `success_response`, `error_response`)
   - `ProposalNotFoundError` exception class

### Services Updated

1. **`proposal_service.py`**
   - Imports shared constants and utilities
   - `_resolve_statuses()` now delegates to `resolve_statuses()`
   - `_calculate_health_score()` now delegates to `calculate_health_score()`
   - `_get_health_recommendation()` now delegates to `get_health_recommendation()`

2. **`proposal_tracker_service.py`**
   - Imports shared constants
   - Uses `UPDATABLE_PROPOSAL_FIELDS` instead of inline set
   - Uses `FIELD_NAME_MAPPING` instead of inline dict
   - Uses `WON_STATUS` and `LOST_STATUSES` constants

## Recommended Follow-up (Future Issues)

### Issue: Refactor ProposalQueryService to use BaseService
**Priority:** High
**Risk:** Low
**Effort:** 1-2 hours

ProposalQueryService creates raw SQLite connections, bypassing retry logic and proper connection handling. Should extend BaseService and use `execute_query()`.

### Issue: Standardize Error Handling Across Services
**Priority:** Medium
**Risk:** Medium (API contract changes)
**Effort:** 4-6 hours

Define a standard error response format and update all services to use it consistently. Consider:
- Always return `{'success': bool, 'data': ..., 'error': ...}`
- Use `ProposalNotFoundError` exception consistently
- Update API routers to handle both patterns during migration

### Issue: Consolidate Email Stats Subquery
**Priority:** Medium
**Risk:** Low
**Effort:** 2-3 hours

Use `proposal_utils.EMAIL_STATS_SUBQUERY` in all services that need email counts. Already defined in utils, just needs adoption.

### Issue: Merge Overlapping Services
**Priority:** Low (risky)
**Risk:** High (significant refactor)
**Effort:** 8+ hours

`ProposalStoryService` and `ProposalDetailStoryService` have significant overlap. Consider merging into a single service with options for detail level. Requires careful API router updates.

### Issue: Standardize Response Field Names
**Priority:** Low (breaking change)
**Risk:** High (frontend impacts)
**Effort:** 4+ hours

Standardize on consistent field names across all services. Requires frontend updates to handle new names.

## Testing Notes

After Phase 1 changes:
1. Run `python -c "from backend.services.proposal_service import ProposalService"` - should import without errors
2. Run `python -c "from backend.services.proposal_tracker_service import ProposalTrackerService"` - should import without errors
3. Test proposal list endpoint: `GET /api/proposals`
4. Test proposal update: `PATCH /api/proposals/{code}`
5. Test health score calculation returns same values as before

## Files Changed

```
backend/services/
├── proposal_constants.py    # NEW - Shared status constants
├── proposal_utils.py        # NEW - Shared utilities
├── proposal_service.py      # MODIFIED - Uses shared utilities
└── proposal_tracker_service.py  # MODIFIED - Uses shared constants
```
