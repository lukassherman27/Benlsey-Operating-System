# Weekly Review - Brain Agent Protocol

**Run this once per week (Sunday or Monday) to plan the upcoming week.**

---

## Part 1: Review Last Week (15 min)

### Read These Files
1. `.claude/TASK_BOARD.md` - What got done?
2. `.claude/WORKER_REPORTS.md` - Review recent completions
3. `.claude/COORDINATION_LEARNINGS.md` - Any new lessons?
4. `docs/roadmap.md` - Are we on track?

### Answer
- **Completed last week:** [List major completions]
- **Carried over:** [What didn't get done?]
- **Blockers encountered:** [What slowed us down?]
- **Learnings:** [Key lessons from the week]

---

## Part 2: Audit Current State (15 min)

### Run These Checks

```bash
# 1. Check build status
cd frontend && npm run build

# 2. Check handler registry
python3 -c "from backend.services.suggestion_handlers import HandlerRegistry; print(HandlerRegistry.get_registered_types())"

# 3. Check API health
curl -s http://localhost:8000/api/health | python3 -m json.tool

# 4. Check database stats
sqlite3 database/bensley_master.db "SELECT
  (SELECT COUNT(*) FROM emails) as emails,
  (SELECT COUNT(*) FROM ai_suggestions WHERE status='pending') as pending_suggestions,
  (SELECT COUNT(*) FROM tasks WHERE status='pending') as pending_tasks"
```

### Document State
Update `LIVE_STATE.md` with current metrics.

---

## Part 3: Plan Next Week (20 min)

### Priority Framework

| Priority | Criteria |
|----------|----------|
| P0 | Blocks Bill's weekly report or demo |
| P1 | Completes a user-facing feature |
| P2 | Improves developer experience |
| P3 | Nice to have / cleanup |

### Questions to Answer
1. **What does Bill need this week?** (Check with user)
2. **What's 80% done that should be finished?**
3. **What technical debt is slowing us down?**
4. **What new features are requested?**

### Create Week's Tasks

Update `TASK_BOARD.md` with:
```markdown
## Week of [Date] - Goals

**Primary Goal:** [One sentence]

**P0 Tasks:**
- [ ] Task 1
- [ ] Task 2

**P1 Tasks:**
- [ ] Task 3
- [ ] Task 4

**Stretch (P2-P3):**
- [ ] Task 5
```

---

## Part 4: Archive & Cleanup (10 min)

### Archive Old Reports
```bash
# If WORKER_REPORTS.md > 3000 lines
wc -l .claude/WORKER_REPORTS.md
# Archive if needed
```

### Archive Completed Phases
Move completed phase documentation to `.claude/archive/`

### Update Roadmap
Update `docs/roadmap.md` with:
- Completed items moved to "Done" section
- New items added to backlog
- Blockers updated

---

## Part 5: Output

Create summary in `LIVE_STATE.md`:

```markdown
## Week of [Date] Plan

**Goal:** [Primary goal]

**Focus Areas:**
1. [Area 1]
2. [Area 2]

**Success Criteria:**
- [ ] [Measurable outcome 1]
- [ ] [Measurable outcome 2]
```

---

## Weekly Review Cadence

| Day | Task |
|-----|------|
| Sunday/Monday | Run this full review |
| Wednesday | Quick check - are we on track? |
| Friday | Pre-weekend sync - document state |
