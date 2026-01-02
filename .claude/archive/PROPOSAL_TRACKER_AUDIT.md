# Proposal Tracker Frontend/Backend Audit

**Date:** 2025-12-10
**Prepared for:** Frontend Agent
**Purpose:** Fix proposal tracker pages to properly display data

---

## Executive Summary

The proposal tracker has **good backend endpoints** but **broken frontend integration**. The main issues:

1. **History endpoint works** - Returns data correctly, but frontend component expects wrong field names
2. **Emails endpoint broken** - Backend queries wrong table (`email_project_links` instead of `email_proposal_links`)
3. **Timeline endpoint works** - Returns correct data structure
4. **Frontend expects data that doesn't exist** - Components look for fields that aren't in the API responses

---

## Database Schema

### Core Tables

**proposals** (102 records)
- Primary table for proposal tracking
- Fields: `proposal_id`, `project_code`, `project_name`, `client_company`, `status`, `health_score`, `days_since_contact`, etc.
- Schema: 75+ columns (see STATUS.md for full list)

**proposal_status_history** (369 records)
- Tracks status changes over time
- Fields: `history_id`, `proposal_id`, `project_code`, `old_status`, `new_status`, `status_date`, `changed_by`, `notes`, `source`
- Working correctly ✅

**email_proposal_links** (1,941 records)
- Links emails to proposals
- Fields: `link_id`, `email_id`, `proposal_id`, `confidence_score`, `match_method`, `match_reason`
- Working correctly ✅

**email_project_links** (519 records)
- Links emails to active PROJECTS (NOT proposals)
- This is for SIGNED contracts only
- Backend incorrectly queries this for proposal emails ❌

---

## Backend Endpoints Audit

### ✅ WORKING ENDPOINTS

#### 1. `/api/proposal-tracker/{project_code}/history`
**File:** `backend/api/routers/proposals.py:467-476`

**Returns:**
```json
{
  "data": [
    {
      "id": 237,
      "project_code": "25 BK-003",
      "old_status": "proposal",
      "new_status": "Proposal Sent",
      "changed_date": "2025-12-08",
      "changed_by": "system",
      "source": "trigger",
      "notes": "Auto-logged: Status changed..."
    }
  ],
  "meta": {...},
  "history": [...] // Backward compat
}
```

**Data source:** `proposal_status_history` table
**Query:** Lines 449-462 in `proposal_tracker_service.py`

**Issues:** None - working correctly ✅

---

#### 2. `/api/proposals/{project_code}/timeline`
**File:** `backend/api/routers/proposals.py:586-711`

**Returns:**
```json
{
  "success": true,
  "project_code": "25 BK-003",
  "project_name": "The George Hotel in Lagos, Nigeria",
  "timeline": [
    {
      "id": 2024931,
      "type": "email",
      "date": "2025-07-06 18:06:58+07:00",
      "title": "Re: tomorrow we need to decide...",
      "summary": "Are we taking this Nigeria project?...",
      "sender_email": "Brian Kent Sherman <bsherman@bensley.com>",
      "confidence_score": 0.95,
      "match_method": "ai_suggestion_approved"
    }
  ],
  "total": 6,
  "item_counts": {
    "email": 6,
    "meeting": 0,
    "event": 0
  }
}
```

**Data source:**
- `email_proposal_links` JOIN `emails` (for emails)
- `meeting_transcripts` (for meetings)
- `proposal_events` (for events)

**Issues:** None - working correctly ✅

---

#### 3. `/api/proposal-tracker/{project_code}` (Detail)
**File:** `backend/api/routers/proposals.py:437-450`

**Returns:** Full proposal detail with all fields from `proposals` table
**Service:** `proposal_tracker_service.get_proposal_by_code()`

**Issues:** None - working correctly ✅

---

#### 4. `/api/proposals/{project_code}/stakeholders`
**File:** `backend/api/routers/proposals.py:714-802`

**Returns:**
```json
{
  "success": true,
  "project_code": "25 BK-003",
  "stakeholders": [
    {
      "contact_id": 123,
      "name": "John Doe",
      "email": "john@example.com",
      "role": "Client",
      "company": "...",
      "is_primary": 1
    }
  ],
  "count": 5
}
```

**Data source:** `proposal_stakeholders` table (110 records) OR derived from `emails`
**Issues:** None - working correctly ✅

---

### ❌ BROKEN ENDPOINTS

#### 1. `/api/proposal-tracker/{project_code}/emails`
**File:** `backend/api/routers/proposals.py:479-488`
**Service:** `proposal_tracker_service.get_email_intelligence()` (lines 466-504)

**PROBLEM:** Queries wrong table
```python
# Line 497 - WRONG TABLE
FROM emails e
INNER JOIN email_project_links epl ON e.email_id = epl.email_id  # ❌
WHERE epl.project_code = ?
```

**Should be:**
```python
FROM emails e
INNER JOIN email_proposal_links epl ON e.email_id = epl.email_id  # ✅
WHERE epl.proposal_id = (SELECT proposal_id FROM proposals WHERE project_code = ?)
```

**Current behavior:** Returns empty array for all proposals (only works for signed projects)

**Data available:**
- 1,941 email→proposal links exist
- Sample: project "25 BK-003" has 6 emails linked
- But endpoint returns `{"data": [], "emails": []}`

**Fix location:** `backend/services/proposal_tracker_service.py:497`

---

## Frontend Components Audit

### Pages

#### 1. `/frontend/src/app/(dashboard)/proposals/page.tsx`
**Purpose:** List page - redirects to `/tracker`
**Status:** Working ✅ (simple redirect)

---

#### 2. `/frontend/src/app/(dashboard)/proposals/[projectCode]/page.tsx`
**Purpose:** Proposal detail page
**Status:** Mostly working, but has issues

**API Calls:**
1. `api.getProposalDetail(projectCode)` → `/api/proposal-tracker/{code}` ✅
2. `api.getProposalHealth(projectCode)` → `/api/intelligence/proposals/{code}/context` ✅
3. `api.getProposalTimeline(projectCode)` → Custom Promise.all ⚠️
4. `api.getProposalBriefing(projectCode)` → Returns empty object ⚠️

**Issues:**

**A. Timeline data structure mismatch**

Frontend expects (line 217-232 in `api.ts`):
```typescript
{
  proposal: {...},
  emails: [...],
  documents: [...],
  timeline: [...],
  stats: {total_emails, total_documents, timeline_events}
}
```

Frontend constructs this by calling TWO endpoints:
- `/history` for timeline
- `/emails` for emails

But since `/emails` is broken, `emails` array is always empty.

**B. Missing documents**

Frontend shows "Documents" tab (line 541-598) but:
- `timeline.documents` is always `[]` (hardcoded in api.ts line 225)
- No backend endpoint populates document data
- Database has `proposal_documents` table (empty) and `documents` table with attachments

Should query: `email_attachments` WHERE proposal_id = X

**C. Briefing data**

Frontend uses `getProposalBriefing()` for:
- Client contact info (lines 373-384)
- Financial data (lines 617-680)
- Milestones (lines 436-468)

But `getProposalBriefing()` just returns empty object (line 234-236 in api.ts).

Should call: `/api/intelligence/proposals/{code}/context` or build from proposal detail data

---

### Components

#### 1. `/frontend/src/components/proposals/proposal-timeline.tsx`
**Purpose:** Show status change timeline
**Status:** Working but has field name issues ⚠️

**API Call:** `api.getProposalHistory(projectCode)` → `/api/proposal-tracker/{code}/history`

**Issue:** Backend returns `changed_date`, frontend expects `status_date`

Line 96-99:
```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ["proposalHistory", projectCode],
  queryFn: () => api.getProposalHistory(projectCode),
});
```

Backend returns:
```json
{
  "data": [{
    "id": 237,
    "changed_date": "2025-12-08",  // ✅ This field
    "old_status": "...",
    "new_status": "..."
  }]
}
```

Component uses (line 186-244):
```typescript
timeline.map((event: TimelineEvent) => {
  // Uses event.status_date, event.created_at
  formatDate(event.status_date)  // Field exists in DB but not returned by API
  formatDate(timeline[0]?.created_at)  // Field exists in DB and returned
})
```

**Fix:** Backend should return `status_date` field from database (it exists but was renamed to `changed_date` in the SELECT)

---

#### 2. `/frontend/src/components/proposals/proposals-manager.tsx`
**Purpose:** Main proposals list table
**Status:** Working ✅

**API Calls:**
- `api.getProposals()` → `/api/proposals` ✅
- `api.getProposalStats()` → `/api/proposals/stats` ✅

**No issues** - This is the working table that shows all proposals

---

#### 3. `/frontend/src/components/proposals/proposals-weekly-report.tsx`
**Purpose:** Weekly changes report
**Status:** Working ✅

**API Call:** `api.getProposalWeeklyChanges(days)` → `/api/proposals/weekly-changes`

**No issues**

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ Frontend: /proposals/[projectCode]                              │
│                                                                 │
│ Calls 4 APIs:                                                   │
│ 1. getProposalDetail()     → ✅ Works                          │
│ 2. getProposalHealth()     → ✅ Works                          │
│ 3. getProposalTimeline()   → ⚠️  Emails empty (broken)         │
│ 4. getProposalBriefing()   → ⚠️  Returns {} (not implemented)  │
└─────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
        ┌──────────────────┐ ┌──────────────┐ ┌──────────────┐
        │ /history         │ │ /emails      │ │ /timeline    │
        │ ✅ Works         │ │ ❌ Broken    │ │ ✅ Works     │
        └──────────────────┘ └──────────────┘ └──────────────┘
                    │               │               │
                    ▼               ▼               ▼
        ┌──────────────────┐ ┌──────────────┐ ┌──────────────┐
        │ proposal_status  │ │ email_project│ │ email_proposal│
        │ _history         │ │ _links ❌    │ │ _links ✅    │
        │ (369 records)    │ │ (519 wrong)  │ │ (1,941 right)│
        └──────────────────┘ └──────────────┘ └──────────────┘
```

---

## What Frontend Expects vs What Backend Returns

### Proposal Detail Page Tabs

#### Tab: Overview
**Data Source:** `getProposalDetail()` + `getProposalHealth()` + `getProposalBriefing()`

| Field | Frontend Expects | Backend Returns | Status |
|-------|------------------|-----------------|--------|
| Project name | `proposal.project_name` | ✅ `project_name` | ✅ |
| Client | `proposal.client_name` | ✅ `client_company` | ✅ (both exist) |
| Health score | `health.health_score` | ✅ `health_score` | ✅ |
| Client contact | `briefing.client.contact` | ❌ Not provided | ❌ |
| Client email | `briefing.client.email` | ❌ Not provided | ❌ |
| Milestones | `briefing.milestones[]` | ❌ Not provided | ❌ |

---

#### Tab: Emails
**Data Source:** `getProposalTimeline()` → combines `/history` + `/emails`

| Field | Frontend Expects | Backend Returns | Status |
|-------|------------------|-----------------|--------|
| Email list | `timeline.emails[]` | ✅ `/timeline` endpoint works | ⚠️ |
| Email subject | `email.subject` | ❌ `/emails` endpoint broken | ❌ |
| Email sender | `email.sender_email` | ❌ `/emails` endpoint broken | ❌ |
| Email category | `email.category` | ❌ `/emails` endpoint broken | ❌ |

**Note:** `/timeline` endpoint DOES return emails correctly. The broken `/emails` endpoint is redundant.

---

#### Tab: Documents
**Data Source:** `getProposalTimeline()`

| Field | Frontend Expects | Backend Returns | Status |
|-------|------------------|-----------------|--------|
| Documents | `timeline.documents[]` | ❌ Always `[]` | ❌ |
| File name | `doc.file_name` | ❌ Not queried | ❌ |
| File size | `doc.file_size` | ❌ Not queried | ❌ |
| Document type | `doc.document_type` | ❌ Not queried | ❌ |

**Available data:**
- `email_attachments` table has 2,070 attachments
- 838 attachments linked to proposals via `attachment_proposal_links`
- Should query: attachments for this proposal

---

#### Tab: Financials
**Data Source:** `getProposalBriefing()`

| Field | Frontend Expects | Backend Returns | Status |
|-------|------------------|-----------------|--------|
| Total value | `briefing.financials.total_contract_value` | ❌ Empty object | ❌ |
| Paid amount | `briefing.financials.initial_payment_received` | ❌ Empty object | ❌ |
| Outstanding | `briefing.financials.outstanding_balance` | ❌ Empty object | ❌ |
| Currency | `briefing.financials.currency` | ❌ Empty object | ❌ |

**Available data:**
- `proposals.project_value` has contract value
- `proposals.currency` has currency (defaults to USD)
- For signed projects: `invoices` table has payment data
- For proposals: usually no payment data (pre-contract)

---

#### Tab: Timeline
**Data Source:** `getProposalTimeline()` (using `/history` endpoint)

| Field | Frontend Expects | Backend Returns | Status |
|-------|------------------|-----------------|--------|
| Timeline events | `timeline.timeline[]` | ✅ BUT wrong field name | ⚠️ |
| Event type | `event.type` | ✅ `type` | ✅ |
| Event date | `event.date` | ✅ `changed_date` (should be `status_date`) | ⚠️ |

---

## Specific Bugs to Fix

### Bug 1: Email Intelligence Endpoint Queries Wrong Table
**File:** `backend/services/proposal_tracker_service.py:497`
**Line:** 497
**Current:**
```python
INNER JOIN email_project_links epl ON e.email_id = epl.email_id
```

**Should be:**
```python
INNER JOIN email_proposal_links epl ON e.email_id = epl.email_id
```

**Also fix line 499:**
```python
# Current:
WHERE epl.project_code = ?

# Should be:
WHERE epl.proposal_id = (
    SELECT proposal_id FROM proposals WHERE project_code = ?
)
```

---

### Bug 2: History Endpoint Returns Wrong Field Name
**File:** `backend/services/proposal_tracker_service.py:455`
**Current:**
```python
status_date as changed_date,
```

**Should be:**
```python
status_date,  -- Keep original field name
```

**Why:** Frontend component expects `status_date` to match the database column

---

### Bug 3: Timeline Doesn't Include Documents
**File:** `frontend/src/lib/api.ts:225`
**Current:**
```typescript
documents: [],  // Hardcoded empty
```

**Should call:** `/api/proposals/{code}/documents` endpoint (needs to be created)

**Backend fix needed:** Add new endpoint in `proposals.py`:
```python
@router.get("/proposals/{project_code}/documents")
async def get_proposal_documents(project_code: str):
    """Get documents/attachments for a proposal"""
    # Query email_attachments JOIN attachment_proposal_links
    # WHERE proposal_id = (SELECT proposal_id FROM proposals WHERE project_code = ?)
```

---

### Bug 4: Briefing Returns Empty Object
**File:** `frontend/src/lib/api.ts:315-319`

**Current:** Returns empty `{}` with a catch

**Should:** Build briefing data from proposal detail response OR create real endpoint

**Option A:** Transform `getProposalDetail()` response to include briefing fields
**Option B:** Create `/api/proposals/{code}/briefing` endpoint that returns financial + milestone data

---

## Recommended Fixes (Priority Order)

### Priority 1: Fix Broken Email Endpoint
**Impact:** High - Emails tab shows "No emails found" even though emails exist
**Effort:** 5 minutes
**Files:**
- `backend/services/proposal_tracker_service.py:497,499`

**Changes:**
```python
# Line 497
INNER JOIN email_proposal_links epl ON e.email_id = epl.email_id

# Line 499
WHERE epl.proposal_id = (
    SELECT proposal_id FROM proposals WHERE project_code = ?
)
```

---

### Priority 2: Fix History Field Name
**Impact:** Medium - Timeline shows dates but component expects different field
**Effort:** 2 minutes
**Files:**
- `backend/services/proposal_tracker_service.py:455`

**Change:**
```python
status_date,  # Don't rename to changed_date
```

---

### Priority 3: Add Documents to Timeline
**Impact:** Medium - Documents tab always empty
**Effort:** 30 minutes
**Files:**
- `backend/api/routers/proposals.py` (new endpoint)
- `frontend/src/lib/api.ts:225` (call new endpoint)

**New endpoint:**
```python
@router.get("/proposals/{project_code}/documents")
async def get_proposal_documents(project_code: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            a.attachment_id as document_id,
            a.filename as file_name,
            a.file_size,
            a.mime_type as document_type,
            a.created_at as modified_date
        FROM email_attachments a
        JOIN attachment_proposal_links apl ON a.attachment_id = apl.attachment_id
        WHERE apl.proposal_id = (
            SELECT proposal_id FROM proposals WHERE project_code = ?
        )
        ORDER BY a.created_at DESC
    """, (project_code,))

    return {
        "success": True,
        "documents": [dict(row) for row in cursor.fetchall()],
        "count": cursor.rowcount
    }
```

---

### Priority 4: Implement Briefing Endpoint
**Impact:** Medium - Financials tab empty, contact info missing
**Effort:** 45 minutes
**Files:**
- `backend/api/routers/proposals.py` (new endpoint or expand existing)
- `frontend/src/lib/api.ts:315-319` (call real endpoint)

**Option A - Expand proposal detail:**
Add `financials` and `client` sections to existing `/proposal-tracker/{code}` response

**Option B - New endpoint:**
Create `/api/proposals/{code}/briefing` that returns:
```json
{
  "client": {
    "name": "...",
    "contact": "...",
    "email": "..."
  },
  "financials": {
    "total_contract_value": 1000000,
    "currency": "USD",
    "initial_payment_received": 0,
    "outstanding_balance": 0,
    "overdue_amount": 0
  },
  "milestones": []
}
```

---

## Testing Checklist

After fixes, test each scenario:

### ✅ Test 1: History Timeline
1. Go to `/proposals/25 BK-003`
2. Click "Timeline" tab
3. Verify status changes show with correct dates
4. Verify timeline events are sorted newest first

**Expected:**
- See multiple status changes
- Dates format correctly (no "Invalid date")
- Events show old_status → new_status

---

### ✅ Test 2: Emails Tab
1. Go to `/proposals/25 BK-003`
2. Click "Emails" tab
3. Verify emails display (should show 6 emails for this project)

**Expected:**
- Table shows 6 rows
- Each row has: Date, Subject, From, Category
- No "No emails found" message

---

### ✅ Test 3: Documents Tab
1. Go to `/proposals/25 BK-003`
2. Click "Documents" tab
3. Verify attachments display

**Expected:**
- Table shows attached files (if any exist)
- Shows file name, type, size

---

### ✅ Test 4: Financials Tab
1. Go to `/proposals/25 BK-003`
2. Click "Financials" tab
3. Verify financial data shows

**Expected:**
- Total contract value displays
- Currency shown (USD)
- If pre-contract: payment fields may be N/A

---

### ✅ Test 5: Overview Tab
1. Go to `/proposals/25 BK-003`
2. Verify all cards populate:
   - Health Breakdown
   - Identified Risks
   - Contact Information
   - Important Dates

**Expected:**
- Health score shows
- Contact info populated from proposal data
- Dates show correctly

---

## API Endpoint Reference

### Working Endpoints ✅

| Endpoint | Purpose | Returns |
|----------|---------|---------|
| `GET /api/proposals` | List all proposals | Paginated list |
| `GET /api/proposals/stats` | Dashboard stats | Counts, health avg |
| `GET /api/proposal-tracker/{code}` | Proposal detail | Full proposal object |
| `GET /api/proposal-tracker/{code}/history` | Status changes | Timeline of changes |
| `GET /api/proposals/{code}/timeline` | Unified timeline | Emails + events + meetings |
| `GET /api/proposals/{code}/stakeholders` | Contacts | List of stakeholders |

---

### Broken/Missing Endpoints ❌

| Endpoint | Issue | Fix Needed |
|----------|-------|------------|
| `GET /api/proposal-tracker/{code}/emails` | Queries wrong table | Change to `email_proposal_links` |
| `GET /api/proposals/{code}/documents` | Doesn't exist | Create new endpoint |
| `GET /api/proposals/{code}/briefing` | Returns `{}` | Implement or use detail data |

---

## Database Query Examples

### Get proposal with emails
```sql
SELECT
    p.project_code,
    p.project_name,
    COUNT(epl.email_id) as email_count
FROM proposals p
LEFT JOIN email_proposal_links epl ON p.proposal_id = epl.proposal_id
WHERE p.project_code = '25 BK-003'
GROUP BY p.proposal_id;
```

Result: `25 BK-003 | The George Hotel in Lagos, Nigeria | 6`

---

### Get emails for a proposal
```sql
SELECT
    e.email_id,
    e.subject,
    e.sender_email,
    e.date,
    epl.confidence_score,
    epl.match_method
FROM emails e
JOIN email_proposal_links epl ON e.email_id = epl.email_id
WHERE epl.proposal_id = (
    SELECT proposal_id FROM proposals WHERE project_code = '25 BK-003'
)
ORDER BY e.date DESC;
```

Result: 6 emails returned

---

### Get attachments for a proposal
```sql
SELECT
    a.attachment_id,
    a.filename,
    a.file_size,
    a.mime_type,
    a.created_at
FROM email_attachments a
JOIN attachment_proposal_links apl ON a.attachment_id = apl.attachment_id
WHERE apl.proposal_id = (
    SELECT proposal_id FROM proposals WHERE project_code = '25 BK-003'
)
ORDER BY a.created_at DESC;
```

---

### Get status history
```sql
SELECT
    history_id,
    old_status,
    new_status,
    status_date,
    changed_by,
    notes
FROM proposal_status_history
WHERE project_code = '25 BK-003'
ORDER BY status_date DESC;
```

Result: Multiple status changes returned

---

## Summary for Frontend Agent

**Good News:**
- Most backend APIs work correctly
- Database has all the data you need
- Timeline, history, stakeholders all functional

**Bad News:**
- Email intelligence endpoint queries wrong table (easy fix)
- Documents not being queried at all (needs new endpoint)
- Briefing returns empty object (needs implementation)
- Some field name mismatches between API and component

**Quick Wins:**
1. Fix email query table name (5 min) → Emails tab works
2. Fix history field name (2 min) → Timeline dates correct
3. Create documents endpoint (30 min) → Documents tab works

**Medium Effort:**
4. Implement briefing data (45 min) → Financials/contact info works

**Total time to full functionality:** ~90 minutes

---

## Files to Modify

### Backend (3 files)
1. `backend/services/proposal_tracker_service.py`
   - Line 497: Change table to `email_proposal_links`
   - Line 499: Change WHERE to use `proposal_id`
   - Line 455: Keep field name as `status_date`

2. `backend/api/routers/proposals.py`
   - Add new `/proposals/{code}/documents` endpoint (~20 lines)
   - Option: Add `/proposals/{code}/briefing` endpoint (~40 lines)

### Frontend (1 file)
3. `frontend/src/lib/api.ts`
   - Line 225: Call documents endpoint instead of hardcoded `[]`
   - Line 315-319: Call real briefing endpoint or transform detail data

---

## Next Steps

1. **Fix Priority 1** (Emails) - Backend team can do this in 5 min
2. **Test** - Verify emails tab works
3. **Fix Priority 2** (History field) - Backend team 2 min
4. **Test** - Verify timeline dates work
5. **Add Priority 3** (Documents endpoint) - Backend team 30 min
6. **Integrate** - Frontend connects to new endpoint
7. **Test** - Verify documents tab works
8. **Add Priority 4** (Briefing) - Backend team 45 min
9. **Integrate** - Frontend uses briefing data
10. **Test** - Verify financials/contact info works

**Total estimated time:** 90 minutes for full functionality

---

## Contact for Questions

- Backend API code: `backend/api/routers/proposals.py`
- Backend service code: `backend/services/proposal_tracker_service.py`
- Frontend page: `frontend/src/app/(dashboard)/proposals/[projectCode]/page.tsx`
- Frontend API client: `frontend/src/lib/api.ts`
- Database: `database/bensley_master.db`

**Test project code:** `25 BK-003` (has 6 emails, good test case)
