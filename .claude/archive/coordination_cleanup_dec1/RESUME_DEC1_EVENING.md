# RESUME PROMPT - Dec 1 Evening Session

**Created:** 2025-12-01 ~16:00
**Context:** Coordinator Agent handoff after E5 completion

---

## WHAT WAS COMPLETED TODAY

| Phase | Status | Key Deliverables |
|-------|--------|------------------|
| E3 | ✅ DONE | 7 suggestion handlers, preview/rollback/source API |
| E4 | ✅ DONE | EmailLinkHandler, Tasks page, Proposals page, Admin cleanup |
| E5 Wave 1 | ✅ DONE | Tasks API, Category Schema, Frontend Polish |
| E5 Wave 2 | ✅ DONE | Wired orchestrator, refactored processors, added detection methods |
| Pipeline Test | ✅ DONE | Fixed 2 column name bugs (project_title→project_name, client_name→client_company) |

---

## CURRENT SYSTEM STATE

**Email Intelligence Pipeline: FULLY WORKING**
- EmailOrchestrator.process_new_emails() triggers categorization + suggestion generation
- 7 handlers registered: follow_up_needed, fee_change, transcript_link, new_contact, deadline_detected, email_link, info
- 580 pending suggestions in database
- All services wired together

**Servers:**
- Backend: localhost:8000 ✅
- Frontend: localhost:3002 ✅

---

## TASKS TO DO (User requested A, B, C, D)

**IMPORTANT: You are COORDINATOR. Create prompts for workers, don't execute yourself!**

### A) Finish E5 Small Items - WORKER PROMPT
```
You are a BACKEND WORKER. Task: Create email categories API router.

READ FIRST:
- backend/services/email_category_service.py
- backend/api/routers/tasks.py (pattern to follow)

CREATE: backend/api/routers/email_categories.py
ENDPOINTS:
- GET /api/email-categories - list all categories
- GET /api/email-categories/stats - category statistics
- GET /api/email-categories/uncategorized - emails needing review
- POST /api/email-categories/{id}/assign/{email_id} - assign category
- GET /api/email-categories/rules - get categorization rules

UPDATE: backend/api/main.py - register router

TEST: curl http://localhost:8000/api/email-categories

REPORT TO: .claude/WORKER_REPORTS.md
```

### B) Process Existing Data - WORKER PROMPT
```
You are a DATA WORKER. Task: Process all emails through pipeline.

RUN:
python3 -c "
from backend.services.email_orchestrator import EmailOrchestrator
orch = EmailOrchestrator()
for batch in range(10):
    result = orch.process_new_emails(limit=500)
    print(f'Batch {batch+1}: {result}')
"

REPORT: Total processed, categorized, suggestions generated

REPORT TO: .claude/WORKER_REPORTS.md
```

### C) E1 - Email-Driven Proposal Automation - WORKER PROMPT
```
You are a BACKEND WORKER. Task: Add sent email detection for proposal status.

READ FIRST:
- docs/planning/PHASE_E_PLAN.md (E1 section)
- backend/services/email_importer.py
- backend/services/ai_learning_service.py

TASK:
1. Add method to scan IMAP Sent folder for proposal emails
2. Detect "proposal sent" pattern (attachments, subject keywords)
3. Create suggestion: "Update BK-XXX status to 'proposal_sent'"
4. Link email as evidence

DO NOT auto-update status - create suggestion for approval

REPORT TO: .claude/WORKER_REPORTS.md
```

### D) E5 Report Enhancements - WORKER PROMPT
```
You are a BACKEND WORKER. Task: Enhance weekly proposal report.

READ FIRST:
- scripts/core/generate_weekly_proposal_report.py
- backend/services/meeting_service.py (transcript access)

ADD TO REPORT:
1. Transcript context - recent meeting notes per proposal
2. Contact info - key contacts per proposal
3. Email activity summary - last 5 emails per proposal

TEST: python scripts/core/generate_weekly_proposal_report.py

REPORT TO: .claude/WORKER_REPORTS.md
```

---

## KEY FILES

| Purpose | File |
|---------|------|
| Orchestrator | `backend/services/email_orchestrator.py` |
| Category Service | `backend/services/email_category_service.py` |
| AI Learning | `backend/services/ai_learning_service.py` |
| Handlers | `backend/services/suggestion_handlers/*.py` |
| Scheduled Sync | `scripts/core/scheduled_email_sync.py` |
| Weekly Report | `scripts/core/generate_weekly_proposal_report.py` |
| TASK_BOARD | `.claude/TASK_BOARD.md` |
| LIVE_STATE | `.claude/LIVE_STATE.md` |
| Learnings | `.claude/COORDINATION_LEARNINGS.md` |

---

## COORDINATION LEARNINGS (Critical)

1. **Coordinator doesn't execute** - creates prompts for workers
2. **Update TASK_BOARD.md BEFORE launching agents**
3. **Check if code exists BEFORE creating new code** - use Organizer to audit
4. **State files are communication channel** - TASK_BOARD, WORKER_REPORTS, LIVE_STATE

---

## QUICK START COMMANDS

```bash
# Test pipeline
python3 -c "from backend.services.email_orchestrator import EmailOrchestrator; print(EmailOrchestrator().process_new_emails(limit=10))"

# Check suggestion stats
curl http://localhost:8000/api/suggestions/stats

# Run weekly report
python scripts/core/generate_weekly_proposal_report.py

# Check handlers
python3 -c "from backend.services.suggestion_handlers import HandlerRegistry; print(HandlerRegistry.get_registered_types())"
```

---

## RESUME INSTRUCTION

Read this file, then:
1. Check TASK_BOARD.md for current status
2. Continue with Tasks A, B, C, D above
3. Update TASK_BOARD.md as you complete items
4. Write to WORKER_REPORTS.md when done
