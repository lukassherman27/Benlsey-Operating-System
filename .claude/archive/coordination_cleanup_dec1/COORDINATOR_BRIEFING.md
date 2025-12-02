# Coordinator Briefing

**Last Updated:** 2025-12-01 12:20
**Current Phase:** E3 Week 2 (Handler Integration)

---

## Quick Status

| Item | Status |
|------|--------|
| **Phases Complete** | A, B, D, E3 Week 1, E5.1-E5.2 |
| **Current Focus** | E3 Week 2 - Refactor _apply_suggestion() |
| **Next Up** | E4 (Broken Pages) → E1 (Email Automation) |
| **Blockers** | IMAP login, Finance Excel |

---

## Files to Read (Priority Order)

1. `.claude/COORDINATION_LEARNINGS.md` - **READ FIRST: Avoid past mistakes**
2. `.claude/LIVE_STATE.md` - Current metrics, worker reports
3. `.claude/TASK_BOARD.md` - Active tasks
4. `.claude/WORKER_REPORTS.md` - Worker completion logs
5. `docs/planning/TIER1_PHASED_PLAN.md` - Phase A-F definitions

---

## Pre-Launch Checklist (BEFORE launching workers)

**Coordinator must do these BEFORE sending prompts to workers:**

- [ ] Read `.claude/COORDINATION_LEARNINGS.md` - Learn from past failures
- [ ] Check WORKER_REPORTS.md - Is assigned work already done?
- [ ] Verify code state for complex tasks - Does feature already exist?
- [ ] Update TASK_BOARD.md with new phase/tasks
- [ ] Mark previous phase complete
- [ ] List all worker assignments with status "PENDING"
- [ ] THEN launch workers

**Remember:** Coordinator NEVER executes code - only orchestrates.

---

## What's Done (Dec 1)

### Data Foundation (Phases A-B-D)
- ✅ **Phase A:** 9 hardcoded paths fixed, 27 routers tested
- ✅ **Phase B:** Audit found 100% orphaned links (4,872 broken)
- ✅ **Phase D:** Link tables rebuilt
  - `email_proposal_links`: 660 valid (100% FK)
  - `email_project_links`: 200 valid (100% FK)

### Phase E Progress
- ✅ **E3 Week 1:** Handler framework complete
  - Migration 049: `tasks`, `suggestion_changes` tables
  - Package: `backend/services/suggestion_handlers/`
  - Handlers: FollowUpHandler, TranscriptLinkHandler, ContactHandler
  - Types: `['follow_up_needed', 'transcript_link', 'new_contact']`

- ✅ **E5.1-E5.2:** Weekly report with email counts
  - 81 proposals, $246.9M pipeline
  - 18 proposals with email activity, 418 linked emails

---

## What's Next (E3 Week 2)

### Immediate Tasks (3 workers recommended)

**Worker 1:** Refactor `ai_learning_service.py`
- Change `_apply_suggestion()` to use handler registry
- Pattern: `HandlerRegistry.get_handler(type, conn).apply(suggestion, data)`

**Worker 2:** Create remaining handlers
- `FeeChangeHandler` (149 pending suggestions)
- `DeadlineHandler` (1 pending suggestion)

**Worker 3:** Add API endpoints
- `POST /api/suggestions/{id}/preview` - Preview changes before apply
- `POST /api/suggestions/{id}/rollback` - Undo applied suggestion
- `GET /api/suggestions/{id}/source` - Get source email/transcript

### Priority Order
```
E3 (Week 2-3) → E4 (Broken Pages) → E1 (Email Automation) → E5 (Enhancements) → E2 (Finance)
```

---

## Phase E Breakdown

| Section | Description | Status |
|---------|-------------|--------|
| E3 | AI Suggestions Redesign | Week 1 ✅, Week 2 🎯 |
| E4 | Fix Broken Admin Pages | NOT STARTED |
| E1 | Email-Driven Proposal Automation | NOT STARTED |
| E5 | Weekly Report Script | E5.1-E5.2 ✅ |
| E2 | Projects Page Financial Fixes | NOT STARTED |

---

## Key Files Created Today

```
database/migrations/049_suggestion_handler_system.sql

backend/services/suggestion_handlers/
├── __init__.py
├── base.py              # BaseSuggestionHandler
├── registry.py          # HandlerRegistry + @register_handler
├── task_handler.py      # FollowUpHandler
├── transcript_handler.py # TranscriptLinkHandler
└── contact_handler.py   # ContactHandler
```

---

## Blockers

| Blocker | Impact | Action |
|---------|--------|--------|
| IMAP LOGIN error | No new email import | Debug tmail connection |
| Finance team Excel | Can't reconcile invoices | Send reminder |

---

## Commands

```bash
# Start backend
cd backend && DATABASE_PATH="../database/bensley_master.db" python3 -m uvicorn api.main:app --reload --port 8000

# Test handlers
python -c "from backend.services.suggestion_handlers import HandlerRegistry; print(HandlerRegistry.get_registered_types())"

# Generate weekly report
DATABASE_PATH="database/bensley_master.db" python3 scripts/core/generate_weekly_proposal_report.py
```

---

## Coordinator Role

**DO:**
- Read state files before assigning work
- Create detailed prompts for workers
- Monitor WORKER_REPORTS.md
- Update LIVE_STATE.md after workers complete
- Flag blockers

**DON'T:**
- Write code directly (workers do that)
- Skip reading current state
- Assign work without checking dependencies

---

## Update Protocol

After each session, update:
1. `.claude/LIVE_STATE.md` - Current state
2. `.claude/TASK_BOARD.md` - Task status
3. `docs/roadmap.md` - If sprint items completed
4. `.claude/WORKER_REPORTS.md` - Worker logs
