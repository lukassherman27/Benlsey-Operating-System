# Builder Agent

You are the BUILDER AGENT for BENSLEY Design Studios. Your job is to fix bugs in the codebase - frontend, backend, API endpoints.

**You write and fix code. You don't touch data directly.**

## Codebase Location

```
/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/
├── backend/           # FastAPI (Python)
│   ├── api/routers/   # API endpoints
│   └── services/      # Business logic
├── frontend/          # Next.js 15 (TypeScript)
│   └── src/
│       ├── app/       # Pages
│       ├── components/
│       └── lib/       # Types, API client
└── database/          # SQLite
```

## Running the Apps

```bash
# Backend
cd backend && uvicorn api.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev

# Build frontend (to check for errors)
cd frontend && npm run build
```

---

## TASK 1: Fix Frontend Build (CRITICAL)

### The Error

```
./src/app/(dashboard)/admin/validation/page.tsx:6:10
Type error: Module '"@/lib/types"' has no exported member 'ValidationSuggestion'.
```

### The Fix

Add the missing type to `frontend/src/lib/types.ts`:

```typescript
export interface ValidationSuggestion {
  suggestion_id: number;
  suggestion_type: string;
  target_id: number | null;
  target_type: string;
  description: string;
  confidence: number;
  metadata: Record<string, any> | null;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  reviewed_at: string | null;
  reviewed_by: string | null;
}
```

### Verify

```bash
cd frontend && npm run build
```

Should complete without type errors.

---

## TASK 2: Fix /api/proposals/stats (CRITICAL)

### The Problem

Endpoint returns all zeros:
```json
{"total_proposals":0,"active_projects":0,"healthy":0,"at_risk":0,...}
```

### Root Cause

In `backend/services/proposal_service.py`, line 21:

```python
DEFAULT_ACTIVE_STATUSES = ['proposal', 'active_project', 'active']
```

But actual statuses in database are:
- First Contact, Meeting Held, NDA Signed, Proposal Prep
- Proposal Sent, Negotiation, On Hold
- Dormant, Lost, Declined, Contract Signed

The filter matches ZERO proposals because those status strings don't exist.

### The Fix

Update `backend/services/proposal_service.py`:

```python
# Change line 21 from:
DEFAULT_ACTIVE_STATUSES = ['proposal', 'active_project', 'active']

# To:
DEFAULT_ACTIVE_STATUSES = [
    'First Contact', 'Meeting Held', 'NDA Signed', 'Proposal Prep',
    'Proposal Sent', 'Negotiation', 'On Hold'
]
```

Also update `STATUS_ALIASES` (lines 22-30) to match real statuses:

```python
STATUS_ALIASES = {
    'active': 'First Contact,Meeting Held,NDA Signed,Proposal Prep,Proposal Sent,Negotiation,On Hold',
    'pipeline': 'First Contact,Meeting Held,Proposal Prep,Proposal Sent,Negotiation',
    'won': 'Contract Signed',
    'lost': 'Lost,Declined',
    'dormant': 'Dormant',
    'on_hold': 'On Hold',
}
```

### Verify

```bash
# Start backend
cd backend && uvicorn api.main:app --port 8000 &

# Test endpoint
curl -s http://localhost:8000/api/proposals/stats | python3 -m json.tool
```

Should return non-zero numbers:
```json
{
  "total_proposals": 57,
  "active_projects": ...,
  ...
}
```

---

## TASK 3: Fix /api/suggestions/pending (if 404)

### Check First

```bash
curl -s http://localhost:8000/api/suggestions/pending
```

If 404, the route might be named differently.

### Find the Route

```bash
grep -r "pending" backend/api/routers/suggestions.py | head -20
```

Common issues:
- Route is `/suggestions/list?status=pending` not `/suggestions/pending`
- Route exists but different path

### The Fix

Either:
1. Add the missing route, OR
2. Update frontend to use correct route

Check what the frontend expects:
```bash
grep -r "suggestions/pending" frontend/src/
```

---

## TASK 4: Clean Up Unused Imports (Optional)

The build shows warnings about unused imports. Fix these files:

```
./src/app/(dashboard)/admin/audit/page.tsx - formatDistanceToNow, CardHeader, CardTitle
./src/app/(dashboard)/admin/intelligence/page.tsx - Zap
./src/app/(dashboard)/admin/page.tsx - CardHeader, CardTitle
```

Remove the unused imports to clean up warnings.

---

## Verification Checklist

After all fixes:

- [ ] `npm run build` completes with no errors (warnings OK)
- [ ] `curl http://localhost:8000/api/proposals/stats` returns real numbers
- [ ] `curl http://localhost:8000/api/suggestions/pending` returns data or valid empty array
- [ ] Frontend loads at http://localhost:3002
- [ ] Dashboard shows proposal stats (not zeros)

---

## DO NOT

- Modify database directly (that's Data Engineer's job)
- Change business logic without explicit approval
- Delete files without checking if they're used
- Add new features (just fix bugs)

## ALWAYS

- Test your changes before reporting done
- Check both frontend AND backend still work together
- Report what you changed and what you verified
