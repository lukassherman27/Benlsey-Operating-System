# End of Session - Sync Protocol

**Run this at the end of EVERY coordination session.**

---

## Sync Checklist

### 1. Update LIVE_STATE.md

Add to the top of the file:
- What was completed this session
- Any new blockers discovered
- Updated metrics if applicable

```markdown
**Last Updated:** [YYYY-MM-DD HH:MM]
**Updated By:** [Your role] (Brief description of session)
```

### 2. Update TASK_BOARD.md

- [ ] Mark completed tasks as ✅ DONE
- [ ] Update status of in-progress tasks
- [ ] Add any new tasks discovered
- [ ] Note any blocked items

### 3. Check WORKER_REPORTS.md Size

If file is > 3000 lines:
```bash
# Archive old reports
mv .claude/WORKER_REPORTS.md .claude/archive/worker_reports_$(date +%Y%m%d).md

# Create fresh file with header
echo "# Worker Reports\n\n**Archive:** See .claude/archive/ for historical reports\n\n---" > .claude/WORKER_REPORTS.md
```

### 4. Document Learnings (If Applicable)

If any coordination issues occurred:
- Add entry to `.claude/COORDINATION_LEARNINGS.md`
- Follow the template: What Happened → Root Cause → Lesson → Protocol

### 5. Git Commit (If Changes Made)

```bash
git add .claude/
git commit -m "sync: [Brief description of session work]

Updated: LIVE_STATE.md, TASK_BOARD.md
Completed: [List major completions]

🤖 Generated with Claude Code"
```

---

## Quick Sync (Minimal Version)

If short on time, at minimum:

1. Update `LIVE_STATE.md` header with timestamp
2. Mark completed tasks in `TASK_BOARD.md`
3. Commit changes

---

## Handoff Note Template

If another agent/session will continue this work:

```markdown
## Handoff - [Date]

**Session completed:** [What was done]

**Next steps:**
1. [Immediate next task]
2. [Following task]

**Watch out for:**
- [Any gotchas or context needed]

**Files changed:**
- [List key files modified]
```
