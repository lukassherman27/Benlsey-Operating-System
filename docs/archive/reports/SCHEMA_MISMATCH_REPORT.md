# Backend Schema Mismatch Report

## Issue

After database migration from Desktop → OneDrive, the backend API broke because it expects Desktop schema but database now uses OneDrive schema.

## Root Cause

During migration, we merged TWO different databases with DIFFERENT schemas:
- **Desktop DB**: Had more fields, different naming
- **OneDrive DB**: Cleaner schema, different structure
- **Result**: Backend code written for Desktop schema, database uses OneDrive schema

## Mismatches Found

### 1. ✅ FIXED: `project_name` → `project_title`
- **Fixed**: 191 replacements across 27 backend files
- **Status**: DONE

### 2. ❌ BROKEN: `client_company` location
- **Backend expects**: `projects.client_company`
- **Database has**: `proposals.client_company` (different table!)
- **Files affected**: 13 backend files
- **Fix needed**: Either:
  - Join projects → proposals to get client_company
  - Remove client_company from projects queries
  - Add client_company column to projects table

### 3. Potentially More Mismatches
Need to check for other column differences between expected vs actual schema.

## Impact

**Backend API endpoints failing**:
- `/api/projects/active` - Returns "no such column: p.client_company"
- Likely many other endpoints broken
- Frontend can only show proposals, not projects

## Solutions

### Option A: Add Missing Columns to Projects Table (QUICK FIX)
Add `client_company` to projects table by joining/denormalizing from proposals:

```sql
ALTER TABLE projects ADD COLUMN client_company TEXT;

UPDATE projects
SET client_company = (
    SELECT client_company
    FROM proposals
    WHERE proposals.project_code = projects.project_code
    LIMIT 1
);
```

**Pros**: Quick, minimal code changes
**Cons**: Data duplication

### Option B: Fix Backend Queries (PROPER FIX)
Update all backend queries to NOT use `projects.client_company`, instead:
- Join with proposals table when needed
- Use proposals data directly
- Remove references where not needed

**Pros**: Clean data model, no duplication
**Cons**: Requires updating 13+ files, more complex queries

### Option C: Hybrid Approach (RECOMMENDED)
1. Add `client_company` view/computed field for projects
2. Update critical endpoints first (projects/active)
3. Gradually refactor queries to proper joins

## Next Steps

1. **Immediate**: Fix `/api/projects/active` endpoint
2. **Short-term**: Audit all API endpoints for schema mismatches
3. **Long-term**: Align backend expectations with database reality

## Files Needing Attention

```
backend/services/financial_service.py
backend/services/context_service.py
backend/services/outreach_service.py
backend/services/proposal_query_service.py
backend/services/rfi_service.py
backend/services/meeting_service.py
backend/services/milestone_service.py
backend/services/contract_service.py
backend/services/proposal_service.py
backend/api/main.py
```

## Temporary Workaround

The frontend works for proposals because proposals table schema is compatible. Only projects endpoints are broken.

**User can still use**:
- Proposals dashboard ✅
- Proposal tracker ✅
- Email intelligence ✅

**User cannot use**:
- Projects dashboard ❌
- Financial summaries (may be broken) ❌
- Project-specific queries ❌
