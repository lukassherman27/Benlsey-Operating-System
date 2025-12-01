# RESUME PROMPT - Phase E3 Week 2

**Copy everything below this line into a new Claude Code session:**

---

```
Read .claude/RESUME_PHASE_E3_WEEK2.md
Read /Users/lukassherman/.claude/plans/tingly-juggling-nova.md
Read .claude/WORKER_REPORTS.md
Read docs/planning/PHASE_E_PLAN.md

You are the COORDINATOR AGENT resuming the Bensley Operating System project.

## CONTEXT - What Happened

Today (Dec 1, 2025) we completed:
1. Phase D (Data Rebuild) - Fixed broken email links (660 proposal links, 200 project links)
2. Audited system - gathered user feedback on what's working/not
3. Created detailed Phase E3 plan for Suggestion System Redesign
4. Launched Week 1 parallel agents (DB migration, Handler architecture, Core handlers)

## CURRENT STATUS

Phase E (Dec 2025 Sprint):
- E1: Email-Driven Automation - NOT STARTED
- E2: Projects Page Fixes - NOT STARTED
- **E3: Suggestions Redesign - WEEK 1 COMPLETE, WEEK 2 STARTING**
- E4: Fix Broken Pages - NOT STARTED
- E5: Weekly Report Script - NOT STARTED

## PHASE E3 OVERVIEW

The suggestion system was half-built:
- 566 pending suggestions existed
- Most did NOTHING when approved (no handlers)
- User couldn't see what would change
- No undo capability

We're fixing this with:
1. Handler architecture (validate/preview/apply/rollback)
2. Tasks table (follow_up_needed creates tasks)
3. Inline email snippets + attachments
4. Grouped view by project
5. Undo capability

## WEEK 1 COMPLETED (Verify in WORKER_REPORTS.md)

- [x] Migration 049 - tasks table, suggestion_changes table, new columns
- [x] Handler base class + registry in backend/services/suggestion_handlers/
- [x] FollowUpHandler (follow_up_needed → INSERT task)
- [x] TranscriptLinkHandler (transcript_link → UPDATE meeting_transcripts)
- [x] ContactHandler (new_contact → INSERT contact)

## WEEK 2 TASKS (YOUR FOCUS NOW)

1. **Refactor ai_learning_service.py** - Replace _apply_suggestion() to use handlers
2. **Add API endpoints:**
   - GET /api/suggestions/{id}/preview
   - POST /api/suggestions/{id}/rollback
   - GET /api/suggestions/{id}/source
3. **Implement remaining handlers:**
   - EmailLinkHandler (email_link)
   - DeadlineHandler (deadline_detected)
   - FeeChangeHandler (fee_change)
   - InfoHandler (missing_data, etc - is_actionable=False)
4. **Add audit trail recording** to suggestion_changes table

## KEY FILES

| File | Purpose |
|------|---------|
| `/Users/lukassherman/.claude/plans/tingly-juggling-nova.md` | DETAILED E3 plan (read this!) |
| `backend/services/ai_learning_service.py` | Has _apply_suggestion() to refactor |
| `backend/services/suggestion_handlers/` | Handler classes from Week 1 |
| `backend/api/routers/suggestions.py` | Add new endpoints here |
| `docs/planning/PHASE_E_PLAN.md` | Master Phase E overview |

## ARCHITECTURE

- Backend: FastAPI on port 8000
- Frontend: Next.js on port 3002
- Database: SQLite at database/bensley_master.db
- AI: OpenAI (gpt-4o-mini) NOT Claude

## YOUR FIRST STEPS

1. Verify Week 1 complete:
   sqlite3 database/bensley_master.db ".tables" | grep -E "tasks|suggestion_changes"
   python -c "from backend.services.suggestion_handlers import HandlerRegistry; print(HandlerRegistry.get_registered_types())"

2. If Week 1 incomplete, check WORKER_REPORTS.md and finish remaining items

3. If Week 1 complete, start Week 2:
   - Read ai_learning_service.py lines 466-521 (_apply_suggestion method)
   - Plan the refactor to use HandlerRegistry
   - Create remaining handlers
   - Add new API endpoints

4. For parallel execution, you can launch:
   - Agent A: Refactor ai_learning_service + audit trail
   - Agent B: Remaining handlers (email_link, deadline, fee_change, info)
   - Agent C: New API endpoints (preview, rollback, source)

## SUCCESS CRITERIA FOR WEEK 2

- [ ] ai_learning_service uses handlers (not hardcoded if/elif)
- [ ] All suggestion types have handlers registered
- [ ] Preview endpoint returns what will change
- [ ] Rollback endpoint can undo approved suggestions
- [ ] Source endpoint returns email/transcript content
- [ ] Changes recorded in suggestion_changes table

## WEEK 3 PREVIEW (After Week 2)

- Enriched suggestions API (inline snippets, attachments)
- Grouped suggestions API (by project)
- Update frontend suggestions page
- Create /tasks page
- Add grouped view toggle

Ask the user if they want to proceed with Week 2, or if they have questions first.
```

---

## QUICK VERIFICATION COMMANDS

After pasting the prompt, run these to verify Week 1 status:

```bash
# Check tables exist
sqlite3 database/bensley_master.db ".tables" | grep -E "tasks|suggestion"

# Check handlers registered
python -c "from backend.services.suggestion_handlers import HandlerRegistry; print(HandlerRegistry.get_registered_types())"

# Check Week 1 reports
cat .claude/WORKER_REPORTS.md | tail -100
```
