# Agent Coordination Guide

**Created:** 2025-12-01
**Purpose:** Prevent coordination chaos, ensure agents get substantial work

---

## THE GOLDEN RULES

### 1. One Agent = Substantial Work

**BAD:** "Agent A: Fix one typo. Agent B: Fix another typo."
**GOOD:** "Agent A: Fix all data quality issues in the email system."

Each agent should have **2-4 hours of coherent work**, not 5-minute tasks.

### 2. Default to Single Session

For 90% of work, **use one Claude session** that does everything sequentially.

Only use parallel agents when:
- Tasks are truly independent (different subsystems)
- Time pressure requires parallel execution
- Tasks would exceed a single session's context

### 3. Scope by SUBSYSTEM, Not by Task Type

**BAD:**
- Agent 1: All database changes
- Agent 2: All API changes
- Agent 3: All frontend changes

**GOOD:**
- Agent 1: Email intelligence system (DB + API + frontend)
- Agent 2: Proposal tracking system (DB + API + frontend)
- Agent 3: Financial reporting system (DB + API + frontend)

Why? Because features span layers. One agent owning a feature end-to-end is cleaner than coordinating across layers.

---

## TASK SIZING GUIDE

### Minimum Viable Agent Task

An agent task should include AT LEAST:

| Component | Minimum |
|-----------|---------|
| Files touched | 3-5 |
| Commits | 1-3 |
| Test scenarios | 2-5 |
| Time (if human) | 1-2 hours |

### Example Task Packs

**TOO SMALL (don't do this):**
```
Task: Add a new API endpoint
- Create GET /api/foo
Done.
```

**RIGHT SIZE:**
```
Task: Implement Email Category System
1. Create email_category_service.py
2. Add 5 API endpoints (list, stats, assign, rules, uncategorized)
3. Create frontend page /admin/email-categories
4. Add database table + migration
5. Connect to email import pipeline
6. Test categorization rules
7. Update docs/context/backend.md
Done.
```

---

## COORDINATION FILES

### What We Use (Simple)

```
.claude/
└── STATUS.md    ← THE ONLY COORDINATION FILE
```

That's it. Update STATUS.md when you finish work.

### What We DON'T Use (Killed Dec 1)

- ~~LIVE_STATE.md~~
- ~~TASK_BOARD.md~~
- ~~WORKER_REPORTS.md~~
- ~~COORDINATOR_BRIEFING.md~~
- ~~COORDINATION_LEARNINGS.md~~

These created chaos. One file is enough.

---

## HANDOFF PROTOCOL

### When Starting a Session

1. Read `CLAUDE.md` (always)
2. Read `.claude/STATUS.md` (current state)
3. Read `docs/roadmap.md` (priorities)
4. Ask: "What's the most impactful thing I can do in this session?"

### When Ending a Session

1. Update `.claude/STATUS.md` with:
   - What you changed
   - What's broken
   - What's next
2. Commit your code with clear message
3. Write a handoff prompt if context is complex

### Handoff Prompt Template

```
## Session Summary

### What I Did
- [List of changes with file paths]

### What Works Now
- [Features that are working]

### What's Still Broken
- [Issues remaining]

### Suggested Next Steps
1. [Priority 1]
2. [Priority 2]
3. [Priority 3]

### Key Files Changed
- path/to/file1.py - [what changed]
- path/to/file2.tsx - [what changed]
```

---

## PARALLEL AGENTS (When Necessary)

### Prerequisites

Only run parallel agents if:
- [ ] Tasks are independent (no shared files)
- [ ] Each agent has 2+ hours of work
- [ ] You have clear boundaries (Agent A = emails, Agent B = proposals)
- [ ] You've defined who updates STATUS.md (usually last to finish)

### Coordination Pattern

```
COORDINATOR (you):
1. Define agent scopes
2. Start agents with clear prompts
3. Wait for completion
4. Merge STATUS.md updates
5. Verify no conflicts

AGENTS:
1. Read their scope
2. Do their work
3. Update STATUS.md section
4. Report completion
```

### Agent Prompt Template

```
You are [ROLE] Agent working on [SUBSYSTEM].

## Your Scope
- [Specific files/features you own]
- [What you should NOT touch]

## Your Tasks
1. [Task with acceptance criteria]
2. [Task with acceptance criteria]
3. [Task with acceptance criteria]

## Context
[Paste relevant STATUS.md section]

## Output Expected
- Working code (test before done)
- Updated STATUS.md section
- Handoff notes if needed

## DON'T
- Touch files outside your scope
- Create new coordination files
- Leave broken code
```

---

## COMMON MISTAKES (Learned Dec 1, 2025)

### Mistake 1: Too Many Coordination Files

**What happened:** 10+ coordination files, all out of sync.
**Fix:** One file only: STATUS.md

### Mistake 2: Tiny Agent Tasks

**What happened:** 13 "workers" for small tasks, massive overhead.
**Fix:** Give each agent 2-4 hours of coherent work.

### Mistake 3: Agents Using Stale Data

**What happened:** Audit agent reported old numbers.
**Fix:** Always query live data, don't trust cached counts.

### Mistake 4: Not Testing After Changes

**What happened:** Endpoints broken but marked "done."
**Fix:** Test every change before marking complete.

### Mistake 5: Documentation Drift

**What happened:** Docs said "66 tables" when there were 115.
**Fix:** Update docs when you change code. Same session.

---

## CHECKLIST: Before Deploying Parallel Agents

- [ ] Is this actually faster than sequential?
- [ ] Are task boundaries clean (no file conflicts)?
- [ ] Does each agent have substantial work (2+ hours)?
- [ ] Is there a clear merge strategy for STATUS.md?
- [ ] Did you define what each agent should NOT touch?
- [ ] Will you verify results before calling it done?

If any answer is "no," use single session instead.

---

## PRIORITY SYSTEM

When planning work, always ask:

1. **Does this help Bill?** (Weekly proposal reports, email automation)
2. **Does this fix something broken?** (Errors, bugs, data issues)
3. **Does this improve workflow?** (Speed, UX, automation)
4. **Is this polish?** (Nice to have, not essential)

Do in that order. Don't do #4 until #1-3 are solid.

---

## TL;DR

1. **One session for most work**
2. **Substantial tasks per agent (2-4 hours)**
3. **One coordination file (STATUS.md)**
4. **Update docs when you change code**
5. **Test before marking done**
6. **Scope by feature, not by layer**
