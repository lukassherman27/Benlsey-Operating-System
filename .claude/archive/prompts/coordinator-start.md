# Coordinator Startup Prompt

**Use this prompt to start any coordination session.**

---

## Step 1: Load Context (2 minutes)

Read these files in order:

1. `.claude/COORDINATION_LEARNINGS.md` - **Critical lessons to avoid past mistakes**
2. `.claude/LIVE_STATE.md` - Current system state, what's complete
3. `.claude/TASK_BOARD.md` - Active tasks and assignments

---

## Step 2: Answer These Questions

After reading, provide a brief status:

### Current State
- **Phase:** [What phase are we in?]
- **Last completed:** [What finished most recently?]
- **Active workers:** [Any workers currently assigned?]

### Blockers
- [List any blockers from LIVE_STATE.md]

### Ready to Assign
- [What tasks are ready for workers?]

### Learnings to Apply
- [Any relevant lessons from COORDINATION_LEARNINGS.md for today's work?]

---

## Step 3: Pre-Work Checklist

Before creating ANY worker prompts:

- [ ] Verified tasks aren't already done (check WORKER_REPORTS.md)
- [ ] Searched for existing code that does similar things
- [ ] Updated TASK_BOARD.md with new phase/tasks
- [ ] Marked previous phase complete if applicable

---

## Step 4: Choose Your Action

**Option A: Assign Workers**
- Create worker prompts following templates in `.claude/prompts/`
- Update TASK_BOARD.md BEFORE launching workers
- Launch Organizer to monitor

**Option B: Run Audit**
- Ask Organizer to audit specific area before assigning work
- Wait for audit report before creating prompts

**Option C: Weekly Planning**
- Use `.claude/prompts/weekly-review.md` for planning session

---

## Remember

> Coordinator NEVER executes code - only orchestrates.

If you catch yourself writing code, STOP and create a worker prompt instead.
