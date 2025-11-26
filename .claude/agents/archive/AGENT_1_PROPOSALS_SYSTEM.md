# Agent 1: Proposals System Fixes

## Your Mission
You are responsible for fixing the Proposals system - import, display, status tracking, and analytics.

## Context
- **Codebase**: Bensley Design Studio Operations Platform
- **Backend**: FastAPI (Python) at `backend/api/main.py`
- **Frontend**: Next.js 15 at `frontend/src/`
- **Database**: SQLite at `database/bensley_master.db`

## Current State & Problems

### Problem 1: Proposal Import is Broken
**File**: `import_proposals.py`
**Issues**:
- Imports from Excel "Proposals.xlsx" sheet "Weekly proposal"
- Missing location, currency, country data (all NULL in database)
- Status always defaults to 'proposal' instead of actual status
- Countries are wrong (France, Japan, UK, Australia shouldn't be there)

**Current Schema**:
```sql
CREATE TABLE proposals (
    proposal_id INTEGER PRIMARY KEY,
    project_code TEXT UNIQUE NOT NULL,
    project_name TEXT,
    client_company TEXT,
    location TEXT,              -- ❌ ALL NULL
    currency TEXT DEFAULT 'USD',  -- ❌ Not populated from Excel
    status TEXT DEFAULT 'proposal',  -- ❌ Should be: won/lost/pending/shelved
    project_value REAL,
    is_active_project INTEGER DEFAULT 0,
    ...
)
```

**Database State**: 89 proposals total, 8 status='won', 81 status='proposal'

### Problem 2: Page Layout Too Wide
**File**: `frontend/src/app/(dashboard)/proposals/[projectCode]/page.tsx`
**Issue**: Page wider than screen, needs horizontal scroll - should fit on one screen

### Problem 3: Missing Status Progression
**Issue**: No visual timeline showing: 1st contact → drafting → proposal sent → negotiating → contract signed
**Need**: Add status tracking with dates, visual timeline UI

### Problem 4: Wrong Analytics
**Current metrics** in proposals page:
- "Total Sent" - doesn't exist, need this for conversion rate
- "Active contract value 1st contact" - confusing metric showing wrong countries
- Need to count ALL proposals sent in 2025 (even canceled) for conversion rate

### Problem 5: No Follow-up Flags
**Issue**: Need system to flag proposals that need follow-up (e.g., meeting scheduled but no response)

## Your Tasks

### Task 1: Investigate & Fix Proposal Import
1. Read the Excel file "Proposals.xlsx" to understand structure
2. Update `import_proposals.py` to:
   - Extract location, country, currency from Excel (or add columns if missing)
   - Determine status based on data (check if contract signed, payment received, etc.)
   - Add status_change_date tracking
   - Clean up incorrect countries
3. Ask user for Excel file path if needed
4. Create backup of current data before re-import
5. Re-import all proposals with correct data

### Task 2: Add Status Progression System
1. Create database migration for status tracking:
   - Add `status_history` table or JSON field
   - Track: status, changed_date, changed_by, notes
2. Update API endpoints in `backend/api/main.py`:
   - Add `/api/proposals/{id}/status` endpoint for status updates
   - Add `/api/proposals/{id}/history` endpoint for timeline
3. Create Pydantic models for status changes

### Task 3: Build Timeline UI
1. Create new component: `frontend/src/components/proposals/proposal-timeline.tsx`
2. Display visual timeline with:
   - Status badges (color-coded)
   - Dates
   - Notes/comments
   - Email context for each status change
3. Add to proposal detail page

### Task 4: Fix Page Layout
1. Edit `frontend/src/app/(dashboard)/proposals/[projectCode]/page.tsx`
2. Make responsive, fit on one screen without horizontal scroll
3. Adjust column widths, remove unnecessary fields, use dropdowns/accordions

### Task 5: Add "Total Sent 2025" Metric
1. Create API endpoint: `/api/proposals/metrics/conversion-rate`
2. Query ALL proposals with `proposal_sent_date >= '2025-01-01'`
3. Include canceled/lost proposals in count
4. Calculate: (contracts_signed / proposals_sent) * 100
5. Add to proposals dashboard

### Task 6: Add Follow-up Flags
1. Create logic to flag proposals:
   - Last email > 7 days ago AND status = 'pending'
   - Meeting scheduled but no follow-up
   - Proposal sent > 14 days ago with no response
2. Add flag icon to proposals list
3. Add filter for "Needs Follow-up"

## Expected Deliverables

1. **Updated import_proposals.py** with full data extraction
2. **Database migration** for status tracking
3. **API endpoints** for status updates and history
4. **Timeline UI component** showing status progression
5. **Fixed proposals page layout** (responsive, one screen)
6. **New metric**: Total Sent 2025 + Conversion Rate
7. **Follow-up flag system** with visual indicators
8. **Test data**: Re-imported proposals with correct countries/locations

## Success Criteria

- ✅ All 89 proposals have location, country, currency populated
- ✅ Status reflects reality (won/lost/pending/shelved, not all "proposal")
- ✅ No incorrect countries (France, UK, Australia removed)
- ✅ Proposals page fits on one screen without scrolling
- ✅ Visual timeline shows status progression for each proposal
- ✅ "Total Sent 2025" metric displays correctly
- ✅ Follow-up flags appear on proposals needing attention

## Notes
- User will provide Excel file path if you ask
- Backup data before re-importing
- Test with sample proposal before full re-import
- Coordinate with Agent 4 (Email Intelligence) for email-to-proposal linking
