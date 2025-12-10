# Documentation Restructure - Clean Up All The Mess

You are restructuring the Bensley Operating System documentation to have a clean, maintainable structure.

## THE GOAL

Go from messy scattered docs to **4 CORE FILES**:

```
.claude/
├── STATUS.md      # Live state - numbers, what's working/broken
├── HANDOFF.md     # Agent context - what you need to know to continue
└── commands/      # Reusable prompts for specific tasks

docs/
├── ROADMAP.md     # The plan - phases, priorities, what's next
├── ARCHITECTURE.md # How it works - system design, data flow
└── archive/       # Everything else goes here
```

## STEP 1: Understand Current Mess

Look at what exists:
- `.claude/STATUS.md` - 300+ lines, mixed with old session logs
- `.claude/HANDOFF.md` - Has useful stuff but also old cruft
- `docs/roadmap.md` - One version of the plan
- `docs/INFRASTRUCTURE_ROADMAP.md` - Another version
- `docs/SYSTEM_MAP.md` - 60K+ bytes of system info
- `docs/BENSLEY_BRAIN_VISION.md` - 156K vision doc
- `docs/context/*.md` - 8 context files
- `docs/tasks/*.md` - 17 task files
- `docs/audits/*.md` - 10 audit files

## STEP 2: Create Clean STATUS.md

Create `.claude/STATUS.md` with ONLY:

```markdown
# System Status

**Last Updated:** [date]
**Updated By:** [agent/human]

---

## Live Metrics

| Metric | Count | Target | Status |
|--------|-------|--------|--------|
| Total emails | X | - | ✅ |
| Uncategorized | X | 0 | ⏳/✅ |
| Pending suggestions | X | 0 | ⏳/✅ |
| Email→Proposal links | X | - | ✅ |
| Contact mappings | X | 300+ | 🟡 |

---

## Pipeline Status

| Component | Status | File |
|-----------|--------|------|
| Email sync | ✅/⏳/❌ | path/to/file |
| Categorizer | ✅/⏳/❌ | path/to/file |
| etc.

---

## What's Working
- [bullet list]

## What's Broken
- [bullet list]

## Recent Changes
| Date | Change | By |

## Current Phase
[One line: what phase, what's the focus]
```

Get the REAL numbers from the database to populate this.

## STEP 3: Create Clean HANDOFF.md

Create `.claude/HANDOFF.md` with ONLY:

```markdown
# Agent Handoff

**Last Updated:** [date]
**Current Focus:** [one line]

---

## Quick Context

You're working on **Bensley Operating System** - a business intelligence platform for BENSLEY design studio.

- **Database:** `database/bensley_master.db` (SQLite)
- **Backend:** FastAPI on port 8000
- **AI:** OpenAI gpt-4o-mini (NOT Claude API)

---

## Key Files

| Purpose | File |
|---------|------|
| Email sync | `scripts/core/scheduled_email_sync.py` |
| Categorizer | `scripts/core/smart_categorizer.py` |
| Project linker | `scripts/core/email_project_linker.py` |
| Main API | `backend/api/main.py` |

---

## Current Work

[What's being worked on, what's next]

---

## Patterns & Learnings

[Important patterns learned from data, things to remember]

---

## Don't Do

- Don't auto-apply suggestions without review
- Don't delete code without reading it first
- Don't create new doc files - update the 4 core files
- Always include project NAMES not just codes
```

## STEP 4: Create Clean ROADMAP.md

Create `docs/ROADMAP.md` consolidating from:
- `docs/roadmap.md`
- `docs/INFRASTRUCTURE_ROADMAP.md`
- Relevant parts of `docs/BENSLEY_BRAIN_VISION.md`

Structure:
```markdown
# Bensley Brain Roadmap

## Vision
[2-3 sentences max]

## Current Phase: [X]
- [ ] Task 1
- [ ] Task 2
- [x] Completed task

## Phase A: Clean Data (This Week)
[Tasks]

## Phase B: Live Pipeline (Next Week)
[Tasks]

## Phase C: Intelligence (January)
[Tasks]

## Phase D: The Brain (February+)
[Tasks]

## Completed
[List of done phases/major milestones]
```

## STEP 5: Create Clean ARCHITECTURE.md

Create `docs/ARCHITECTURE.md` consolidating from:
- `docs/SYSTEM_MAP.md`
- `docs/context/architecture.md`
- `docs/context/backend.md`
- `docs/context/data.md`

Structure:
```markdown
# System Architecture

## Overview
[One paragraph]

## Data Flow
[ASCII diagram of how data moves through system]

## Database
[Key tables and what they store]

## Services
[Key services and what they do]

## Tech Stack
- Backend: FastAPI
- Database: SQLite
- AI: OpenAI
- Frontend: Next.js
```

## STEP 6: Archive Everything Else

Move to `docs/archive/YYYY-MM-DD/`:
- All files from `docs/context/` (except keep as reference)
- All files from `docs/tasks/` that are completed
- All files from `docs/audits/` except DEEP_SERVICE_AUDIT.md
- `docs/BENSLEY_BRAIN_VISION.md` (keep for reference)
- `docs/SYSTEM_MAP.md` (merged into ARCHITECTURE.md)
- `docs/INFRASTRUCTURE_ROADMAP.md` (merged into ROADMAP.md)

## STEP 7: Update CLAUDE.md

Update the main `CLAUDE.md` file to point to the 4 core files:

```markdown
## Documentation Structure

| File | Purpose | When to Update |
|------|---------|----------------|
| `.claude/STATUS.md` | Live system state | After every change |
| `.claude/HANDOFF.md` | Agent context | End of every session |
| `docs/ROADMAP.md` | The plan | When priorities change |
| `docs/ARCHITECTURE.md` | How it works | When architecture changes |

**Rule:** Don't create new doc files. Update these 4 or archive.
```

## STEP 8: Verify

After restructure, you should have:
- `.claude/STATUS.md` - <100 lines, current numbers
- `.claude/HANDOFF.md` - <100 lines, agent context
- `docs/ROADMAP.md` - <200 lines, the plan
- `docs/ARCHITECTURE.md` - <300 lines, how it works
- Everything else in `docs/archive/`

## DO IT NOW

Start with Step 2 - create the clean STATUS.md by querying the database for real numbers. Show me the result before moving on.
