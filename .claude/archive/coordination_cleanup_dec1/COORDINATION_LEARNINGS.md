# Coordination Learnings

**Purpose:** Document coordination failures and lessons so future agents don't repeat mistakes.
**Protocol:** Add new learnings as they occur. Read before starting any coordination session.

---

## How to Use This File

**Coordinators:** Read this BEFORE creating task assignments
**Organizers:** Reference this when monitoring for problems
**All Agents:** If you spot a coordination failure, document it here

---

## Communication Flow (The Rules)

State files ARE the communication channel between agents:

| File | Direction | Purpose |
|------|-----------|---------|
| `TASK_BOARD.md` | Coordinator → Workers | Task assignments |
| `WORKER_REPORTS.md` | Workers → Coordinator | Completion reports |
| `LIVE_STATE.md` | Organizer → Everyone | System state |

**If it's not in a state file, other agents can't see it.**

---

## Learnings Log

### 2025-12-01: Coordinator Role Clarity

**What Happened:**
Coordinator accidentally executed code (fixed bugs, implemented features) instead of creating prompts for workers. When workers received their tasks, some work was already done, causing confusion and wasted effort.

**Root Cause:**
Coordinator didn't have clear boundaries on what they should/shouldn't do directly.

**Lesson:**
Coordinator NEVER executes code - only orchestrates. Coordinator's job is to:
- Read state files
- Create task prompts for workers
- Update TASK_BOARD.md with assignments
- Review worker reports
- Plan next phase

**Protocol:**
If Coordinator accidentally does implementation work:
1. Document what was done in WORKER_REPORTS.md
2. Update TASK_BOARD.md to mark those tasks complete
3. Remove from worker assignments to avoid duplication

---

### 2025-12-01: State File Sync Before Launch

**What Happened:**
Coordinator created a plan with 4 worker tasks but didn't update TASK_BOARD.md. Organizer couldn't see what was happening because state files weren't synced.

**Root Cause:**
No checklist for Coordinator before launching workers.

**Lesson:**
ALWAYS update TASK_BOARD.md BEFORE launching agents. Organizer relies on TASK_BOARD.md to know current assignments.

**Protocol - Coordinator Pre-Launch Checklist:**
1. [ ] Update TASK_BOARD.md with new phase/tasks
2. [ ] Mark previous phase complete
3. [ ] List all worker assignments with status "PENDING"
4. [ ] THEN launch workers

---

### 2025-12-01: Duplicate Task Assignment

**What Happened:**
Worker 1 was assigned to "refactor _apply_suggestion() to use handler registry" but this was already done in a previous session. Worker discovered the task was complete and reported no work needed.

**Root Cause:**
TASK_BOARD.md showed task as pending when it was actually done. State files weren't accurate.

**Lesson:**
Before assigning tasks, verify they aren't already complete. Check:
1. Actual code state (does the feature exist?)
2. WORKER_REPORTS.md (was it reported done?)
3. LIVE_STATE.md (is it documented as complete?)

**Protocol:**
When creating task assignments, Coordinator should:
1. Read recent WORKER_REPORTS.md entries
2. Verify code state for complex tasks
3. Ask Organizer to audit if unsure

---

### 2025-12-01: Check Before Creating - CRITICAL

**What Happened:**
Coordinator created prompt for "Email Processor" agent to build new email processing functionality. In reality, 10+ existing services already handle email processing:
- `ai_learning_service.py` - generate_suggestions_from_email()
- `email_content_processor.py` - AI categorization
- `email_intelligence_service.py` - Timeline, linking
- `email_category_service.py` - Category management
- `email_importer.py` - IMAP import
- And 5+ more email-related services/scripts

**Root Cause:**
Coordinator didn't audit existing codebase before defining new work. Created prompt that would duplicate existing functionality.

**Lesson:**
EVERY agent prompt MUST include "check existing code first" as step 1. Workers should:
1. Search for existing files/services that do similar things
2. Read existing implementations before writing new code
3. EXTEND or ORCHESTRATE existing code, never duplicate
4. Report back if task is already implemented

**Protocol - MANDATORY in ALL agent prompts:**
```
## BEFORE WRITING ANY CODE

1. Search for existing implementations:
   - grep -r "ClassName" backend/services/
   - grep -r "function_name" backend/
   - find . -name "*keyword*" -type f

2. If similar code exists:
   - READ it first
   - EXTEND it, don't duplicate
   - Or create ORCHESTRATOR that calls existing services

3. If task is already done:
   - Report "ALREADY EXISTS" in WORKER_REPORTS.md
   - Document where it exists
   - Suggest improvements if needed
```

**Anti-Pattern:**
Creating `email_processor.py` when `email_content_processor.py`, `email_content_processor_smart.py`, and `ai_learning_service.py` already exist.

**Correct Pattern:**
Creating `email_orchestrator.py` that CALLS existing services to coordinate them.

---

## Adding New Learnings

When a coordination failure occurs, document:

```markdown
### YYYY-MM-DD: Brief Title

**What Happened:**
[Describe the failure]

**Root Cause:**
[Why did it happen?]

**Lesson:**
[What should we do differently?]

**Protocol:**
[Specific steps to prevent recurrence]
```

---

## Quick Reference: Coordination Anti-Patterns

| Anti-Pattern | Correct Behavior |
|--------------|------------------|
| Coordinator writes code | Create prompts, let workers implement |
| Launch workers before updating TASK_BOARD.md | Update state files first, launch second |
| Assign tasks without checking if done | Verify code state before assignment |
| Workers don't write to WORKER_REPORTS.md | Every completion must be documented |
| Organizer updates LIVE_STATE.md inconsistently | Update after EVERY worker completion |
| **Create new file without checking existing** | **Search first, extend/orchestrate existing code** |
| **Duplicate functionality** | **Call existing services, don't reimplement** |

---

## Version History

| Date | Update |
|------|--------|
| 2025-12-01 | Initial creation with Dec 1 learnings |
