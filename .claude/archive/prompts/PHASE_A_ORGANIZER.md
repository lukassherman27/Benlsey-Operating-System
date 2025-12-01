# PHASE A: Organizer Agent Prompt

**Phase:** A - Infrastructure Integrity
**Role:** Organizer Agent
**Goal:** Verify all paths, routing, and ensure backend runs with zero 500 errors

---

## Context Files to Read First

1. `docs/planning/TIER1_PHASED_PLAN.md` - Your phase definition
2. `docs/context/backend.md` - Router map, endpoint list
3. `.claude/LIVE_STATE.md` - Current system state

---

## Your Tasks

### Task 1: DB Path Sanity Check
Find and fix all hardcoded database paths pointing to Desktop or non-canonical locations.

```bash
# Search for wrong paths
grep -r "Desktop.*bensley" scripts/
grep -r "Desktop.*BDS_SYSTEM" .
grep -r "/Users/.*/Desktop" scripts/ backend/

# Correct path should be:
# os.getenv('DATABASE_PATH', 'database/bensley_master.db')
```

**Files to check specifically:**
- `scripts/core/generate_weekly_proposal_report.py` (KNOWN ISSUE - line 16)
- Any file in `scripts/core/`
- Any file in `backend/services/`

**Fix pattern:**
```python
# WRONG
DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

# CORRECT
DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')
```

### Task 2: Backend Health Verification
Verify all core endpoints return 200.

```bash
# Start backend if not running
cd backend && uvicorn api.main:app --reload --port 8000

# Test core endpoints
curl -s http://localhost:8000/api/health
curl -s http://localhost:8000/api/finance/summary
curl -s http://localhost:8000/api/proposals/stats
curl -s http://localhost:8000/api/projects/active
curl -s http://localhost:8000/api/emails/recent
```

### Task 3: Router Map Verification
Verify all 27 routers are imported and working.

Check `backend/api/main.py` for router imports. For each router, test at least one endpoint.

### Task 4: Document Findings
Update these files with your findings:

1. `.claude/LIVE_STATE.md` - Add section "Phase A Status"
2. `docs/context/backend.md` - Update if any endpoints changed

---

## Gate Criteria (You Must Verify)

Before declaring Phase A complete, confirm:

- [ ] `grep -r "Desktop.*bensley" scripts/` returns empty
- [ ] `curl localhost:8000/api/health` returns 200
- [ ] `curl localhost:8000/api/finance/summary` returns data (not 500)
- [ ] All 27 routers tested, no 500 errors
- [ ] `DATABASE_PATH` env var used everywhere

---

## Handoff

When complete, update `.claude/LIVE_STATE.md` with:

```markdown
## Phase A Status: COMPLETE

### Verified
- Backend running on canonical DB
- All endpoints return 200
- DB path issues fixed: [list files fixed]

### Ready for Phase B
Phase B (Data Audit) can now begin.
```

---

## Do NOT Do

- Do NOT write new features
- Do NOT modify business logic
- Do NOT change database schema
- ONLY verify paths and fix hardcoded DB paths
