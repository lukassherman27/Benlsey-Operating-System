# COORDINATOR HANDOFF - Dec 1, 2025 (Phase E3 Start)

**Purpose:** Resume work on Phase E with detailed E3 (Suggestions Redesign) plan ready.

---

## QUICK STATUS

```
Phase D: ✅ COMPLETE (data rebuilt, 660 proposal links, 200 project links)
Phase E: 🎯 STARTING NOW
  - E3 (Suggestions): PLANNED - ready for implementation
  - E1, E2, E4, E5: NOT STARTED
```

---

## WHAT WAS DONE TODAY

1. **Audited Phase D completion** - Link tables rebuilt, all workers done
2. **Gathered user feedback** on what's working/not working
3. **Deep-planned E3 (Suggestions Redesign)** with user input:
   - Handler architecture with validation/preview/rollback
   - Tasks table for follow_up_needed suggestions
   - Inline email snippets, attachments display
   - Grouped view by project
   - Undo capability

---

## KEY FILES TO READ

| File | Purpose |
|------|---------|
| `docs/planning/PHASE_E_PLAN.md` | Master Phase E overview |
| `~/.claude/plans/tingly-juggling-nova.md` | **DETAILED E3 plan (574 lines)** |
| `.claude/LIVE_STATE.md` | Current system status |
| `.claude/WORKER_REPORTS.md` | What workers completed |

---

## E3 IMPLEMENTATION - 3 WEEKS

### Week 1: Foundation (START HERE)
- [ ] Migration 049 (tasks, suggestion_changes, columns)
- [ ] Handler base class + registry
- [ ] FollowUpHandler, TranscriptLinkHandler, ContactHandler

### Week 2: Core Features
- [ ] Remaining handlers (email_link, deadline, fee_change)
- [ ] Preview/rollback API endpoints
- [ ] Refactor ai_learning_service to use handlers

### Week 3: Enhanced UX
- [ ] Enriched suggestions API (inline snippets, attachments)
- [ ] Grouped suggestions API
- [ ] Update suggestions page
- [ ] Tasks page with project grouping

---

## PARALLEL AGENT PROMPTS FOR WEEK 1

### Agent 1: Database Migration
```
Read ~/.claude/plans/tingly-juggling-nova.md

You are the DATABASE AGENT. Create migration 049 for the suggestion system redesign.

Create file: database/migrations/049_suggestion_handler_system.sql

Include:
1. tasks table (for follow_up_needed suggestions)
2. suggestion_changes table (audit trail)
3. ALTER ai_suggestions to add rollback_data and is_actionable columns
4. Indexes for tasks table

After creating the migration, run it:
cd database && python migrate.py

Verify the tables exist with correct schema.

Report: Tables created, row counts, any issues.
```

### Agent 2: Handler Architecture
```
Read ~/.claude/plans/tingly-juggling-nova.md

You are the BACKEND ARCHITECTURE AGENT. Create the suggestion handler framework.

Create these files:
1. backend/services/suggestion_handlers/__init__.py
2. backend/services/suggestion_handlers/base.py - BaseSuggestionHandler abstract class
3. backend/services/suggestion_handlers/registry.py - HandlerRegistry + @register_handler decorator

The base class needs:
- validate(suggested_data) -> List[str] errors
- preview(suggestion, suggested_data) -> ChangePreview dict
- apply(suggestion, suggested_data) -> SuggestionResult dict
- rollback(rollback_data) -> bool

Test by importing: python -c "from backend.services.suggestion_handlers import HandlerRegistry; print('OK')"

Report: Files created, import test result.
```

### Agent 3: Core Handlers
```
Read ~/.claude/plans/tingly-juggling-nova.md
Read backend/services/suggestion_handlers/base.py
Read backend/services/suggestion_handlers/registry.py

You are the HANDLER IMPLEMENTATION AGENT. Implement the P0 handlers.

Create:
1. backend/services/suggestion_handlers/task_handler.py - FollowUpHandler
2. backend/services/suggestion_handlers/transcript_handler.py - TranscriptLinkHandler
3. backend/services/suggestion_handlers/contact_handler.py - ContactHandler

Each must implement: validate, preview, apply, rollback

Update __init__.py to import all handlers.

Test: python -c "from backend.services.suggestion_handlers import HandlerRegistry; print(HandlerRegistry.get_registered_types())"
Should print: ['follow_up_needed', 'transcript_link', 'new_contact']

Report: Handlers created, registration test result.
```

---

## RESUME PROMPT FOR COORDINATOR

```
Read .claude/COORDINATOR_HANDOFF_20251201_E3.md

You are the COORDINATOR AGENT resuming Phase E implementation.

Current status:
- Phase D COMPLETE (data quality fixed)
- Phase E3 (Suggestions Redesign) has detailed plan at ~/.claude/plans/tingly-juggling-nova.md
- Week 1 parallel agents need to be launched

Your tasks:
1. Check if Week 1 is complete by reviewing WORKER_REPORTS.md
2. If not started, launch the 3 parallel agents for Week 1
3. If Week 1 done, proceed to Week 2 integration work
4. Track progress, help unblock workers

The goal: Make suggestions actually DO something when approved.
```

---

## ARCHITECTURE CONTEXT

**Tech Stack:**
- Backend: FastAPI on port 8000
- Frontend: Next.js on port 3002
- Database: SQLite at database/bensley_master.db
- AI: OpenAI (gpt-4o-mini) NOT Claude

**Current Suggestion Types (566 pending):**
- follow_up_needed: 452 → Will CREATE task
- fee_change: 81 → Will UPDATE proposal value
- transcript_link: 31 → Will LINK transcript to proposal
- deadline_detected: 1 → Will CREATE deadline task
- new_contact: 1 → Will INSERT contact

---

## SUCCESS CRITERIA

1. Every suggestion type has defined behavior when approved
2. User sees preview of what will change
3. Approved suggestions can be undone (rollback)
4. follow_up_needed creates tasks visible in /tasks page
5. Clean handler architecture for future extension

---

**Created:** 2025-12-01 by Coordinator
**For:** Next session resume
