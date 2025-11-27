# Frontend-Backend Sync Plan
**Created:** 2025-11-24
**Status:** Ready to Execute

---

## THE CORE PROBLEM

Your backend has **TWO separate tables** with different purposes:

### 1. `proposals` table (87 records)
- **Purpose:** Sales pipeline, pre-contract opportunities
- **Primary Key:** `proposal_id`
- **Use Case:** Bill tracking potential projects, follow-ups, win probability
- **Key Fields:** `status`, `health_score`, `days_since_contact`, `project_value`

### 2. `projects` table (46 records)
- **Purpose:** Won contracts, active delivery, completed projects
- **Primary Key:** `project_id` (NO `proposal_id` column!)
- **Use Case:** Project delivery, contracts, invoices, RFIs
- **Key Fields:** `project_code`, `status`, `is_active_project`, `total_fee_usd`

---

## THE BUG

**Backend:** `proposal_service.py` is querying the `projects` table but trying to SELECT `proposal_id` which doesn't exist.

**Line 112 in proposal_service.py:**
```python
SELECT proposal_id, project_code, ...
FROM projects  -- ❌ WRONG TABLE! Should be 'proposals'
```

**This causes:**
```
GET /api/proposals → ERROR: "no such column: proposal_id"
```

---

## THE FIX PLAN

### Phase 1: Fix Backend Service (30 min)

1. **Update `backend/services/proposal_service.py`:**
   - Change all queries from `projects` table to `proposals` table
   - Update JOIN logic if proposals link to projects
   - Test `/api/proposals` endpoint returns data

2. **Verify other endpoints:**
   - `/api/proposals/stats` ✅ (works)
   - `/api/proposals/by-code/{code}` (check)
   - `/api/proposals/weekly-changes` (check)

### Phase 2: Update Frontend Types (20 min)

**Files to update:**
- `frontend/src/lib/types.ts` - Core type definitions
- `frontend/src/lib/api.ts` - API response mapping

**Key Type Fixes:**
```typescript
// Proposals (sales pipeline)
interface ProposalSummary {
  proposal_id: number;      // NOT project_id
  project_code: string;
  project_name: string;
  status: ProposalStatus;
  health_score: number;
  days_since_contact: number;
  project_value: number;
  // ...
}

// Projects (active delivery)
interface ProjectSummary {
  project_id: number;        // NOT proposal_id
  project_code: string;
  project_title: string;
  status: string;
  is_active_project: boolean;
  total_fee_usd: number;
  // ...
}
```

### Phase 3: Fix Frontend Components (40 min)

**Components needing updates:**

1. **Dashboard Page** (`frontend/src/app/(dashboard)/page.tsx`)
   - Uses: `/api/dashboard/stats` ✅ (works)
   - Uses: `/api/proposals/weekly-changes` (needs testing)

2. **Proposals Page** (`frontend/src/app/(dashboard)/proposals/`)
   - Uses: `/api/proposals` ❌ (broken)
   - Fix: Update to use corrected endpoint
   - Test: Can view proposals list

3. **Projects Page** (`frontend/src/app/(dashboard)/projects/page.tsx`)
   - Uses: `/api/projects/active` ✅ (works - returns {data, count})
   - Already fixed: Changed `.projects` to `.data`

4. **Tracker Page** (`frontend/src/app/(dashboard)/tracker/page.tsx`)
   - Uses proposal_tracker endpoints (separate from proposals)
   - Already fixed: Removed unsupported year filter

### Phase 4: Testing (30 min)

**Test each page:**
- [ ] Dashboard loads with real data
- [ ] Proposals page shows list
- [ ] Projects page shows active projects
- [ ] Tracker page shows proposal tracking
- [ ] No console errors

---

## EXPECTED API RESPONSE STRUCTURES

### ✅ Working Endpoints:

```json
// GET /api/dashboard/stats
{
  "total_proposals": 87,
  "active_projects": 46,
  "total_emails": 3356,
  "proposals": { ... },
  "revenue": { ... }
}

// GET /api/projects/active
{
  "data": [ {...}, {...} ],
  "count": 46
}
```

### ❌ Broken (needs backend fix):

```json
// GET /api/proposals
// Currently: {"detail": "no such column: proposal_id"}
// Should be: {"data": [...], "total": 87, "page": 1, "per_page": 20}
```

---

## IMPLEMENTATION ORDER

1. **Fix backend first** - Get `/api/proposals` working
2. **Test with curl** - Verify JSON structure
3. **Update frontend types** - Match backend reality
4. **Update components** - Use correct types
5. **Test in browser** - Verify everything loads

---

## QUICK WIN TO SHOW PROGRESS

**You can show progress NOW with these working pages:**

1. **Dashboard** - `/api/dashboard/stats` works ✅
2. **Projects** - `/api/projects/active` works ✅
3. **Tracker** - Proposal tracker endpoints work ✅

**Just fix the proposals endpoint and you'll have 90% working!**

---

## FILES TO MODIFY

### Backend:
- `backend/services/proposal_service.py` (main fix)

### Frontend:
- `frontend/src/lib/types.ts` (type definitions)
- `frontend/src/lib/api.ts` (already mostly correct)
- `frontend/src/app/(dashboard)/proposals/` (proposal list component)

---

## NEXT STEP

**Start with:** Fix `proposal_service.py` line 112 - change `FROM projects` to `FROM proposals`

**Then test:** `curl http://localhost:8000/api/proposals`

**Expected:** List of 87 proposals with correct data
