# PARALLEL SPRINT PLAN - TIER 1 Data Foundation

**Created:** 2025-12-01
**Target Completion:** 2025-12-22 (3 weeks)
**End Goal:** Weekly proposal reports for Bill with email/transcript context

---

## Agent Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      COORDINATOR AGENT                           │
│  - Assigns tasks to workers                                      │
│  - Reviews completed work                                        │
│  - Manages dependencies between tasks                            │
│  - Makes go/no-go decisions on phase gates                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
┌─────────────────────────┐    ┌─────────────────────────────────┐
│    ORGANIZER AGENT      │    │         WORKER AGENTS           │
│    (Always Running)     │    │    (3 parallel sessions)        │
│                         │    │                                 │
│ - SSOT file updates     │    │ ┌─────────┐ ┌─────────┐ ┌─────┐│
│ - Path/structure fixes  │    │ │Backend  │ │Frontend │ │Data ││
│ - Help workers find     │    │ │Worker   │ │Worker   │ │Worker│
│   files                 │    │ └─────────┘ └─────────┘ └─────┘│
│ - Health checks         │    │                                 │
│ - Documentation         │    │ Rotate based on current needs   │
└─────────────────────────┘    └─────────────────────────────────┘
```

---

## Communication Protocol

### File-Based Coordination
All agents read/write to shared files:

| File | Purpose | Updated By |
|------|---------|------------|
| `.claude/LIVE_STATE.md` | Current status, blockers, metrics | Organizer |
| `.claude/TASK_BOARD.md` | Active tasks, assignments, status | Coordinator |
| `.claude/WORKER_REPORTS.md` | Worker completion reports | Workers |

### Handoff Flow
```
1. Coordinator assigns task in TASK_BOARD.md
2. Worker picks up task, marks "in_progress"
3. Worker completes, writes report to WORKER_REPORTS.md
4. Organizer updates LIVE_STATE.md with new metrics
5. Coordinator reviews, assigns next task
```

---

## 3-Week Sprint Schedule

### WEEK 1: Foundation (Dec 1-7)
**Goal:** Backend stable, data audited, feedback infrastructure started

| Day | Backend Worker | Frontend Worker | Data Worker | Organizer |
|-----|----------------|-----------------|-------------|-----------|
| 1-2 | Test all 27 routers, fix 500s | Fix TypeScript errors | Audit email→proposal (100 sample) | Fix DB paths, SSOT |
| 3-4 | Suggestions API (CRUD) | Suggestions list UI | Audit email→project (50 sample) | Document findings |
| 5-7 | Bulk approve endpoint | Bulk approve button | Audit contacts, create backup | Update metrics |

**Week 1 Gate:**
- [ ] Zero 500 errors on all endpoints
- [ ] Suggestions workflow API complete
- [ ] Baseline data quality metrics documented
- [ ] DB backup created

---

### WEEK 2: Data Quality (Dec 8-14)
**Goal:** Clean data via suggestions workflow, transcripts linked

| Day | Backend Worker | Frontend Worker | Data Worker | Organizer |
|-----|----------------|-----------------|-------------|-----------|
| 1-2 | Transcript linking API | Suggestion detail modal | Run transcript_linker.py | Verify no path issues |
| 3-4 | Contact CRUD API | Contact management UI | Process transcript suggestions | Track approval rate |
| 5-7 | Email context API | Email context widget | Extract contacts, create suggestions | Update LIVE_STATE |

**Week 2 Gate:**
- [ ] All 39 transcripts reviewed (human approved/rejected)
- [ ] Contact suggestions created and reviewed
- [ ] Email→Proposal accuracy ≥90% (re-sample to verify)
- [ ] Suggestions approval rate documented

---

### WEEK 3: Reports & Polish (Dec 15-22)
**Goal:** Weekly report working, system demo-ready

| Day | Backend Worker | Frontend Worker | Data Worker | Organizer |
|-----|----------------|-----------------|-------------|-----------|
| 1-2 | Weekly report API | Report preview page | Verify data quality | Final path check |
| 3-4 | Email/transcript context in report | Projects detail polish | Backfill missing data | Performance audit |
| 5-7 | Report scheduling | Admin consolidation | Final data validation | Demo prep docs |

**Week 3 Gate (TIER 1 COMPLETE):**
- [ ] Weekly report generates with email/transcript context
- [ ] Bill can use it (get feedback)
- [ ] All pages load <2s
- [ ] Zero console errors
- [ ] Data quality ≥95%

---

## Daily Standup Template

Each day, Coordinator reviews and posts:

```markdown
## Standup: YYYY-MM-DD

### Yesterday Completed
- [Worker 1]: What they finished
- [Worker 2]: What they finished
- [Worker 3]: What they finished
- [Organizer]: SSOT updates

### Today's Assignments
| Agent | Task | Depends On |
|-------|------|------------|
| Backend Worker | [task] | - |
| Frontend Worker | [task] | Backend task |
| Data Worker | [task] | - |
| Organizer | [task] | - |

### Blockers
- [List any blockers]

### Notes
- [Any coordination notes]
```

---

## Task Board Template

Create `.claude/TASK_BOARD.md`:

```markdown
# TASK BOARD

## In Progress
| Task | Assigned To | Started | Blocked By |
|------|-------------|---------|------------|
| Test all routers | Backend Worker | Dec 1 | - |
| Fix TS errors | Frontend Worker | Dec 1 | - |
| Audit email links | Data Worker | Dec 1 | - |

## Ready (Pick Next)
| Task | Priority | Depends On |
|------|----------|------------|
| Suggestions CRUD API | P0 | Routers tested |
| Suggestions list UI | P0 | API ready |
| Contact audit | P1 | - |

## Completed
| Task | Completed By | Date | Notes |
|------|--------------|------|-------|
| ... | ... | ... | ... |

## Blocked
| Task | Blocked By | Unblock Action |
|------|------------|----------------|
| ... | ... | ... |
```

---

## Worker Prompts (Updated for Parallel Ops)

### Backend Worker Prompt
```
Read .claude/COORDINATOR_BRIEFING.md, .claude/TASK_BOARD.md, docs/context/backend.md

You are BACKEND WORKER in a parallel agent swarm.

1. Check TASK_BOARD.md for your assigned tasks
2. Mark task "in_progress" when you start
3. Complete the task
4. Write completion report to .claude/WORKER_REPORTS.md
5. Mark task "completed" in TASK_BOARD.md
6. Check for next task or wait for Coordinator

If blocked, note in TASK_BOARD.md and move to next available task.
Test everything with curl before marking complete.
```

### Frontend Worker Prompt
```
Read .claude/COORDINATOR_BRIEFING.md, .claude/TASK_BOARD.md, docs/context/frontend.md

You are FRONTEND WORKER in a parallel agent swarm.

1. Check TASK_BOARD.md for your assigned tasks
2. Mark task "in_progress" when you start
3. Complete the task
4. Verify with: cd frontend && npx tsc --noEmit
5. Write completion report to .claude/WORKER_REPORTS.md
6. Mark task "completed" in TASK_BOARD.md

Check if your task depends on Backend - wait if API not ready.
Test in browser before marking complete.
```

### Data Worker Prompt
```
Read .claude/COORDINATOR_BRIEFING.md, .claude/TASK_BOARD.md, docs/context/data.md

You are DATA WORKER in a parallel agent swarm.

1. Check TASK_BOARD.md for your assigned tasks
2. Mark task "in_progress" when you start
3. For audits: READ ONLY, document findings
4. For changes: Create suggestions, never direct modify
5. Write findings/report to .claude/WORKER_REPORTS.md
6. Mark task "completed" in TASK_BOARD.md

Always create backup before any data operations.
Report metrics to Organizer for LIVE_STATE update.
```

### Organizer Prompt
```
Read .claude/COORDINATOR_BRIEFING.md, .claude/LIVE_STATE.md, .claude/WORKER_REPORTS.md

You are ORGANIZER AGENT running continuously alongside workers.

Continuous tasks:
1. Watch WORKER_REPORTS.md for new completions
2. Update LIVE_STATE.md with new metrics/status
3. Run periodic health checks:
   - curl localhost:8000/api/health
   - grep -r "Desktop.*bensley" scripts/
4. Fix any path issues you find
5. Help workers find files when asked
6. Keep documentation current

When idle, audit and document. Never stop running.
```

---

## Coordinator Daily Checklist

```markdown
## Morning
- [ ] Read WORKER_REPORTS.md for overnight completions
- [ ] Update TASK_BOARD.md with new assignments
- [ ] Check for blockers, reassign if needed
- [ ] Post standup

## Midday
- [ ] Check worker progress
- [ ] Unblock any stuck workers
- [ ] Verify Organizer is updating SSOT

## Evening
- [ ] Review day's completions
- [ ] Plan tomorrow's assignments
- [ ] Check gate criteria progress
- [ ] Update week status
```

---

## Phase Gates (Still Enforced)

Even with parallel work, gates must pass before advancing:

### Week 1 → Week 2 Gate
```
REQUIRED:
- Zero 500 errors (Backend Worker verified)
- Suggestions API working (Backend Worker)
- Suggestions UI loading (Frontend Worker)
- Data audit complete (Data Worker)
- LIVE_STATE.md updated (Organizer)

COORDINATOR: Review and approve before Week 2 tasks
```

### Week 2 → Week 3 Gate
```
REQUIRED:
- Transcripts 100% reviewed
- Contacts verified
- Email accuracy ≥90%
- Suggestions workflow proven (used for real)

COORDINATOR: Review and approve before Week 3 tasks
```

### Week 3 → TIER 2 Gate (TIER 1 COMPLETE)
```
REQUIRED:
- Weekly report working
- Bill has used it
- Performance <2s
- Zero console errors
- Data quality verified

COORDINATOR: Create TIER1_COMPLETE.md, plan TIER 2
```

---

## TIER 2 Preview (After Dec 22)

Once TIER 1 is complete with clean data:

| Week | Focus | Workers |
|------|-------|---------|
| 4-5 | Local embeddings + vector store | Backend + Data |
| 6-7 | Semantic search + RAG | Backend + Frontend |
| 8 | AI query interface polish | All workers |

---

## Starting the Swarm

**Step 1:** Create the shared files
```bash
touch .claude/TASK_BOARD.md
touch .claude/WORKER_REPORTS.md
```

**Step 2:** Open 5 sessions
1. Coordinator (you, main session)
2. Organizer Agent
3. Backend Worker
4. Frontend Worker
5. Data Worker

**Step 3:** Seed TASK_BOARD.md with Week 1, Day 1 tasks

**Step 4:** Give each session their prompt

**Step 5:** Workers execute, you coordinate

---

## Quick Reference

| I need to... | Do this |
|--------------|---------|
| Assign work | Update TASK_BOARD.md |
| Check progress | Read WORKER_REPORTS.md |
| See current state | Read LIVE_STATE.md |
| Unblock someone | Update TASK_BOARD.md blockers |
| Check a gate | Review gate criteria in this doc |
| Move to next week | Verify gate, update TASK_BOARD.md |
