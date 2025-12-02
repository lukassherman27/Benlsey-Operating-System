# System Status

**Last Updated:** 2025-12-01 21:30 by Claude (docs fixed + coordination guide created)
**Backend:** Running on port 8000
**Frontend:** Running on port 3002

---

## Documentation Audit - Dec 1, 2025

### Summary

| Area | Documented | Actual | Gap |
|------|------------|--------|-----|
| Backend Routers | 28 | 29 | +1 (__init__.py) |
| Backend Services | 60+ | 46 | Overstated by 14+ |
| Suggestion Handlers | 8 types | 8 types | ✅ Accurate |
| Frontend Pages | 23 | 24 | Missing: `/search` |
| Database Tables | 80+ (data.md) / 66 (arch.md) | 115 | Understated by 35-49 |
| Migrations | 70 | 72 | +2 |
| Core Scripts | Not listed | 25 | Not documented |

### Critical Issues Found

1. **`docs/context/relationships.md` DOES NOT EXIST** - Referenced in index.md but file missing
2. **ai_agents.md outdated** - Last updated Nov 27, doesn't cover:
   - Email category system (`email_category_service.py`)
   - 8 suggestion handlers (contact, deadline, email_link, info, proposal, status, task, transcript)
   - Fact that system uses **OpenAI**, not Claude API
3. **architecture.md says 66 tables** - Actual is 115 (75% understated)
4. **Index.md references wrong API** - Says "Claude API" but system uses OpenAI

### Missing from Documentation

**Backend Services not documented:**
- `email_category_service.py` (NEW - categorization system)
- `email_orchestrator.py` (NEW - orchestration)
- `sent_email_detector.py` (NEW - detect sent proposals)
- `suggestion_handlers/` directory (8 handlers)

**Frontend Pages not documented:**
- `/search` - Search page

**Scripts not documented in context files:**
- 25 scripts in `scripts/core/` including:
  - `scheduled_email_sync.py`
  - `transcript_linker.py`
  - `email_project_linker.py`

### Outdated Information

| File | Issue |
|------|-------|
| `ai_agents.md` | Says "Claude API" - should say "OpenAI (gpt-4o-mini)" |
| `ai_agents.md` | 801 pending suggestions - now 152 after cleanup |
| `architecture.md` | 66 tables - actually 115 |
| `architecture.md` | "93+ endpoints" - need to recount |
| `data.md` | "80+ tables" - actually 115 |

---

## Data Counts (CORRECTED - Dec 1 21:00)

| Table | Count | Notes |
|-------|-------|-------|
| emails | 3,498 | |
| proposals | 87 | |
| projects | 62 | |
| email_proposal_links | 661 | Audit had stale data (1,001) |
| email_project_links | 788 | |
| ai_suggestions | 7,921 | Total all time |
| **pending_suggestions** | **152** | After cleanup (was 7,475) |
| rejected_suggestions | 7,758 | 7,322 junk purged this session |
| tasks | 2 | |
| contacts | 578 | |
| meeting_transcripts | 39 | |
| database tables total | 115 | |

---

## System Component Counts (Verified)

| Component | Count |
|-----------|-------|
| Backend routers | 29 |
| Backend services | 46 |
| Suggestion handlers | 8 types |
| Frontend pages | 24 |
| Core scripts | 25 |
| Migrations | 72 |

---

## What Works

- **Query endpoint** - `/api/query/ask` - natural language queries
- **Proposal tracker** - `/api/proposal-tracker/list` - proposal listing
- **Suggestions system** - approve/reject/preview all functional
- **Email import** - working (fixed Dec 1)
- **Suggestion handlers** - 8 handlers registered, creates tasks on approval
- **Email categorization** - rule-based system working
- **Frontend API connections** - fixed Dec 1 evening

---

## What's Broken / Needs Work

| Issue | Status |
|-------|--------|
| Proposal health stats return 0s | DATA issue - `health_score` not populated |
| `is_active_project` all 0 | DATA issue - not set on any proposal |
| 39 transcripts unlinked to proposals | Needs linking |
| `docs/context/relationships.md` missing | CREATE or remove reference |

---

## Documentation Fixes Applied (Dec 1)

| Issue | Status |
|-------|--------|
| `relationships.md` missing | ✅ Removed reference from index.md |
| `ai_agents.md` said Claude | ✅ Changed to OpenAI (gpt-4o-mini) |
| `ai_agents.md` missing handlers | ✅ Added 8 handlers documentation |
| `architecture.md` 66→115 tables | ✅ Fixed |
| `data.md` 80→115 tables | ✅ Fixed |
| `index.md` wrong counts | ✅ Fixed (46 services, 28 routers, 72 migrations) |

**Still TODO:** Document 25 core scripts in scripts/core/

## New: Coordination Guide

**Location:** `docs/processes/COORDINATION_GUIDE.md`

Key rules:
1. One agent = substantial work (2-4 hours)
2. Scope by SUBSYSTEM, not task type
3. One coordination file (STATUS.md)
4. Update docs when you change code
5. Test before marking done

---

## API Quick Reference

```bash
# Query
curl -X POST http://localhost:8000/api/query/ask -H "Content-Type: application/json" -d '{"query": "how many proposals?"}'

# Proposal tracker
curl http://localhost:8000/api/proposal-tracker/list

# Suggestions
curl "http://localhost:8000/api/suggestions?status=pending&limit=10"

# Approve suggestion
curl -X POST http://localhost:8000/api/suggestions/{id}/approve

# Preview suggestion
curl http://localhost:8000/api/suggestions/{id}/preview
```

---

## File Documentation

See `docs/context/` for detailed file maps:
- `index.md` - Main navigation (⚠️ references missing file)
- `backend.md` - API endpoints & services (mostly accurate)
- `frontend.md` - Pages & components (mostly accurate)
- `architecture.md` - System design (⚠️ table counts outdated)
- `data.md` - Database schema (⚠️ table counts outdated)
- `ai_agents.md` - AI features (⚠️ says Claude, uses OpenAI)

---

## How to Coordinate Multiple Agents

**Don't.** Use one Claude session at a time.

If you MUST run parallel agents:
1. Update this STATUS.md when done
2. That's it. No TASK_BOARD, WORKER_REPORTS, LIVE_STATE bullshit.
