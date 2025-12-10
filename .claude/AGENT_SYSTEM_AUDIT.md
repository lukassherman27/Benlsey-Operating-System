# Agent System Audit: Why Things Break

**Generated:** 2025-12-10
**Auditor:** Audit Agent (Brutal Edition)

---

## Executive Summary

Your agent system is **fundamentally broken at the coordination layer**. Individual agents work, but they don't talk to each other. There's no memory, no state management, no verification loop. You're building features in isolation that break when combined. The result: 71 stuck suggestions, schema mismatches, and constant "fix:" commits.

**Root Cause:** You have prompts for agents but no **system for agents**. Each Claude session starts fresh, makes changes, and leaves. The next session doesn't know what happened.

---

## The 7 Deadly Sins of Your Agent Architecture

### Sin 1: No Shared Memory

**Problem:** Each agent session starts from zero. There's no way to say "remember that the status values are TitleCase" because there IS no memory.

**Evidence:**
- `status_handler.py` line 19-42 defines VALID_STATUSES as `['inquiry', 'meeting_scheduled', ...]`
- Database actually uses: `['First Contact', 'Meeting Held', ...]`
- 16 proposal_status_update suggestions are stuck because of this mismatch
- **Nobody remembers to update the handler when statuses are defined elsewhere**

**What Should Exist:**
```
SHARED FACTS (persistent):
- Proposal statuses: ['First Contact', 'Meeting Held', ...]
- Project codes format: "YY BK-XXX"
- Database path: database/bensley_master.db
- API base: localhost:8000

Every agent reads this before starting.
Every agent updates this when they discover new facts.
```

### Sin 2: No Verification Loop

**Problem:** Agents mark things "done" without testing. The next agent finds broken code.

**Evidence:**
- 72 commits total
- 20+ "fix:" commits (28%)
- Common pattern: Feature commit → Fix commit → Another fix commit

**Git history pattern:**
```
a8f0390 fix: Fix project linking API and correction dialog Select error
12bde3f fix: Enhanced Review UI - show project names and fix correction dialog
87d5238 fix: Fix patterns page build error
142ac56 Revert dashboard-page.tsx to fix missing component errors
```

**What Should Exist:**
```
VERIFICATION CHECKLIST (mandatory before "done"):
□ npm run build passes (0 errors)
□ uvicorn starts without import errors
□ Core endpoints return data:
  - curl localhost:8000/api/proposals/stats
  - curl localhost:8000/api/emails/recent?limit=5
□ Frontend loads at localhost:3002
□ Changes committed with clear message
```

### Sin 3: Prompts Are Too Long and Unfocused

**Problem:** Your agent prompts are 200-450 lines of instructions. Agents lose focus. They cherry-pick tasks and skip others.

**Evidence:**
- `audit-agent.md`: 193 lines
- `data-engineer-agent.md`: 476 lines
- `builder-agent.md`: 220 lines
- `proposal-enrichment-agent.md`: 253 lines

**What Happens:**
1. Agent reads first 50 lines
2. Gets excited, starts working
3. Forgets the verification section at line 180
4. Leaves broken code

**What Should Exist:**
```markdown
# Agent Prompt Template (MAX 50 lines)

## Mission (1 sentence)
Fix frontend TypeScript build errors.

## Context (3 sentences)
Project: Bensley Operations Platform
Tech: Next.js 15, TypeScript, FastAPI
Location: /frontend/

## Tasks (numbered, specific)
1. Run `npm run build` and capture errors
2. Fix each TypeScript error in order
3. Run build again to verify

## Verification (mandatory)
Before marking done:
□ `npm run build` exits with code 0
□ Screenshot of successful build

## Do Not
- Touch backend code
- Add new features
- Refactor working code
```

### Sin 4: No Coordinator Actually Exists

**Problem:** The docs mention a "Coordinator Agent" that routes work and updates SSOT files. **It doesn't exist.** It's a concept in roadmap.md, not a real thing.

**Evidence from roadmap.md:**
```markdown
## 6. Agent Structure

COORDINATOR AGENT (only one who updates SSOT)
├── Develops tasks and roadmap
├── Updates STATUS.md, HANDOFF.md, roadmap.md, ARCHITECTURE.md
├── Routes work to specialist agents
├── Receives summaries from all agents
└── Makes final decisions on approach
```

**Reality:**
- Every agent updates every file
- STATUS.md has conflicting numbers
- HANDOFF.md is 450 lines (too long to read)
- No one actually "routes work"

**What Should Exist:**

An actual coordination protocol:
```
SESSION START PROTOCOL:
1. Read STATUS.md (numbers, what's broken)
2. Read HANDOFF.md Section 1-3 only (business context)
3. Identify ONE task to complete
4. Do that task
5. Update STATUS.md with new numbers
6. Write 3-sentence summary in HANDOFF.md

That's it. Don't read everything. Don't update everything.
Just do one thing well.
```

### Sin 5: Suggestion System is Untestable

**Problem:** Suggestions get created but nobody knows if they'll apply successfully until approval time. Then they fail silently.

**Evidence:**
- 71 "approved" suggestions that couldn't be applied
- Breakdown:
  - 37 contact_link - Missing contact_id or already linked
  - 16 proposal_status_update - Wrong status format
  - 15 new_contact - Contacts already exist
  - 2 new_proposal - No handler exists
  - 1 transcript_link - Transcript not found

**Root Cause:**
The code that CREATES suggestions (gpt_suggestion_analyzer.py, batch_suggestion_service.py) doesn't validate against the code that APPLIES suggestions (suggestion_handlers/*.py).

**Example of the mismatch:**

Creation code (gpt_suggestion_analyzer.py line 128):
```python
"project_code": "XX BK-XXX",  # Template
```

Handler code (status_handler.py line 73):
```python
elif new_status not in VALID_STATUSES:  # Uses lowercase
    errors.append(f"Invalid status '{new_status}'")
```

**What Should Exist:**
```python
# Before creating any suggestion:
def create_suggestion(type, data):
    handler = HandlerRegistry.get_handler(type)
    errors = handler.validate(data)  # DRY-RUN validation
    if errors:
        log.warning(f"Would fail to apply: {errors}")
        return None  # Don't create broken suggestions
    return save_suggestion(type, data)
```

### Sin 6: Schema Drift Goes Unnoticed

**Problem:** The database schema, handler code, and API assumptions drift apart. Nobody notices until runtime.

**Evidence:**

1. **proposals.status** values:
   - Database: `First Contact`, `Meeting Held`, `Proposal Sent`, etc.
   - status_handler.py: `inquiry`, `meeting_scheduled`, `submitted`, etc.
   - Frontend types.ts: ???

2. **Column name inconsistencies:**
   - proposals table: `proposal_id` (primary key)
   - email_proposal_links: references `proposal_id`
   - Some handlers look for `confidence` (wrong), should be `confidence_score`

3. **Table confusion:**
   - `projects` vs `proposals` - both have similar columns
   - `/api/proposals/at-risk` queries `projects` table for columns that don't exist
   - Code assumes `projects` has `proposal_id`, `client_company` - it doesn't

**What Should Exist:**
```
SCHEMA TRUTH FILE: database/SCHEMA_TRUTH.md

## proposals table
- proposal_id (INTEGER, PK)
- project_code (TEXT, UNIQUE) - format "YY BK-XXX"
- status (TEXT) - ENUM: ['First Contact', 'Meeting Held', ...]
- ...

## ai_suggestions table
- suggestion_id (INTEGER, PK)
- suggestion_type (TEXT) - ENUM: ['email_link', 'contact_link', ...]
- confidence_score (REAL) - NOT 'confidence'
- ...

Every handler imports valid values from this file.
No hardcoded enums in handlers.
```

### Sin 7: No Incremental Testing

**Problem:** You build features end-to-end before testing anything. When it breaks, you don't know which part failed.

**Evidence:**
The "Sent Email Linking + Proposal Version Tracking" feature (Dec 11):
- Created 2 migrations
- Created 2 new services
- Modified 1 existing service
- Added 4 new endpoints
- All at once, in one session

If any part breaks, debugging requires understanding all 4 pieces.

**What Should Exist:**
```
INCREMENTAL BUILD PATTERN:

Step 1: Create migration, verify with SQL query
Step 2: Create service, test with Python REPL
Step 3: Add endpoint, test with curl
Step 4: Add frontend, verify in browser

Each step is independently verifiable.
Don't move to step N+1 until step N works.
```

---

## The Coordination Problem (Core Issue)

### What You Have

```
Human: "Do X"
     ↓
Claude Session 1: Does part of X, leaves notes
     ↓
Human: "Continue"
     ↓
Claude Session 2: Starts fresh, reads 400 lines of docs, does Y instead
     ↓
Human: "Fix the bug from Session 1"
     ↓
Claude Session 3: Doesn't know what Session 1 did, makes it worse
```

### What You Need

```
Human: "Do X"
     ↓
Claude: Reads 20-line STATE file
        Sees: "Last session did A, B. Next: C"
        Does C
        Updates STATE: "Did C. Next: D"
     ↓
Human: "Continue"
     ↓
Claude: Reads STATE file (same 20 lines)
        Sees: "Did C. Next: D"
        Does D
        Updates STATE: "Did D. Verification passed. Task complete."
```

### The Minimal Coordination System

**File: `.claude/STATE.md` (MAX 30 lines)**

```markdown
# Current State

## Active Task
Fix frontend build errors

## Last Session
- Fixed: 3 TypeScript errors in admin/page.tsx
- Verified: `npm run build` passes
- Remaining: 2 errors in suggestions/page.tsx

## Next Steps
1. Fix line 347 useEffect dependency warning
2. Fix line 458 missing dependency warning
3. Run build and verify

## Blockers
None

## Updated
2025-12-10 14:30 UTC
```

**Rules:**
1. Every session reads STATE.md first
2. Every session updates STATE.md last
3. Never exceed 30 lines
4. Clear the file when task is complete

---

## Why Your Prompts Don't Work

### Current Prompt Structure (audit-agent.md)

```
Line 1-10: Intro and mission
Line 11-50: Database access and SQL examples
Line 51-100: Checklist items (6 categories)
Line 101-140: Detailed SQL queries
Line 141-177: Output format template
Line 178-193: Rules and philosophy
```

**Problem:** By line 50, Claude is already executing. The output format at line 141 gets ignored.

### Better Prompt Structure

```
Line 1-5: One-sentence mission + key constraint
Line 6-15: The ONLY 3 things to do (numbered)
Line 16-20: Output format (BEFORE the instructions)
Line 21-30: Verification checklist
Line 31-40: "Do not" list (what to avoid)
```

**Example Rewrite:**

```markdown
# Audit Agent

Mission: Find what's actually broken. Not what might be wrong—what IS wrong right now.

## Output First (Read This Before Doing Anything)
Your output is a single table:

| Issue | File:Line | Evidence | Impact |
|-------|-----------|----------|--------|
| Build fails | frontend/ | Exit code 1 | Can't deploy |
| ... | ... | ... | ... |

That's it. One table. Fill it with facts.

## Your 3 Tasks
1. Run `npm run build` - record errors
2. Run `uvicorn api.main:app` - record import errors
3. Query database for orphaned records

## Verification
Before reporting:
□ Every issue has a file:line reference
□ Every issue has evidence (error message, SQL result)
□ No speculation—only confirmed bugs

## Do Not
- Read all the documentation
- Fix anything (just report)
- Speculate about "might be wrong"
```

---

## The 71 Stuck Suggestions: Root Cause Analysis

### contact_link (37 stuck)

**Why They Fail:**
```sql
-- The suggestion says "Contact sent 5 emails to this project"
-- But the suggested_data JSON is:
{"contact_id": null, "project_id": null, "email_count": 5}

-- Handler validation (contact_link_handler.py:34):
contact_id = suggested_data.get("contact_id")
if not contact_id:
    errors.append("Contact ID is required")  -- FAILS HERE
```

**Fix:** The code that creates these suggestions must include actual IDs, not just counts.

### proposal_status_update (16 stuck)

**Why They Fail:**
```python
# Handler expects (status_handler.py:19):
VALID_STATUSES = ['inquiry', 'proposal', 'meeting_scheduled', ...]

# Database has:
['First Contact', 'Meeting Held', 'Proposal Sent', ...]

# Validation fails at line 73:
elif new_status not in VALID_STATUSES:
    errors.append(f"Invalid status '{new_status}'")
```

**Fix:** Update VALID_STATUSES to match actual database values.

### new_contact (15 stuck)

**Why They Fail:**
Contact already exists (duplicate check fails) OR the handler tries to insert with missing required fields.

### new_proposal (2 stuck)

**Why They Fail:**
```python
# In suggestion_handlers/__init__.py, there's no:
from .new_proposal_handler import NewProposalHandler

# The handler doesn't exist!
```

**Fix:** Create the missing handler or reject these suggestion types.

---

## What's Actually Working

Despite all the problems, some things work:

1. **Email sync pipeline** - Imports 173 emails/week automatically
2. **Pattern learning** - 151 patterns learned, 50 batches approved
3. **Data quality** - 99.9% email coverage, 0 orphaned records
4. **Frontend build** - Passes (with warnings)
5. **Core API endpoints** - `/api/proposals`, `/api/projects`, `/api/emails` work

---

## Recommendations: Fix the System, Not the Symptoms

### Immediate (Do This Week)

1. **Create STATE.md** - 30-line max, update every session
2. **Fix VALID_STATUSES** - Match database values
3. **Reject 71 stuck suggestions** - They're unfixable, clean the queue
4. **Shorten prompts** - Max 50 lines each

### Short-term (This Month)

5. **Add pre-creation validation** - Don't create suggestions that will fail
6. **Create SCHEMA_TRUTH.md** - Single source for column names, enums
7. **Add verification to all prompts** - Mandatory checklist at end
8. **Create a real coordinator protocol** - Not just documentation

### Long-term (Q1 2026)

9. **Add integration tests** - Test handler + creation code together
10. **Implement persistent agent memory** - MCP server with state
11. **Build coordinator dashboard** - Visual state of all agents

---

## The Real Problem

You're trying to build a **multi-agent system** using a **single-agent tool** (Claude CLI).

Claude CLI is great for one task at a time. It's not designed for:
- Persistent memory across sessions
- Coordination between multiple parallel agents
- State management
- Verification loops

**Your options:**

1. **Accept the limitation** - Use Claude for single, atomic tasks. Human coordinates.
2. **Build coordination infrastructure** - MCP server, state file, strict protocols.
3. **Switch to a multi-agent framework** - CrewAI, AutoGen, or similar.

You've been trying to do #2 with documentation alone. It's not working because **documentation is not infrastructure**. A 400-line HANDOFF.md doesn't help if Claude starts fresh every time.

---

## Conclusion

Your system is full of good ideas poorly executed. The core architecture (FastAPI + Next.js + SQLite + AI suggestions) is sound. The agent prompts are well-intentioned. The data quality is excellent.

But you have **no coordination layer**. Each session is an island. Bugs accumulate. State drifts. The 71 stuck suggestions are a symptom of a deeper problem: **nobody remembers what the rules are**.

Fix the system. Create STATE.md. Shorten the prompts. Add verification. Then the agents will actually help instead of creating new problems.

**Grade: C+**
- Architecture: B+
- Data quality: A
- Agent prompts: C (too long, no verification)
- Coordination: D (doesn't exist)
- Error recovery: C- (reactive, not preventive)
