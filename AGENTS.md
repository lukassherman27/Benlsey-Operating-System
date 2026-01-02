# AGENTS.md - Multi-Agent Coordination Rules

> **This file is LAW.** All AI agents (Claude, Codex, Gemini, etc.) must follow these rules.

---

## Agent Workflow (MANDATORY)

Every task follows this sequence:

```
1. AUDIT    → Understand what exists before touching anything
2. PLAN     → Write plan in GitHub issue comment (NOT a new file)
3. IMPLEMENT → Do the work, small commits, reference issue #
4. VERIFY   → Test it works, run relevant tests
5. DOCUMENT → Update issue with what you did, close or comment
```

**NO EXCEPTIONS.**

---

## File Rules

### NEVER Create:
- New markdown files in root (only CLAUDE.md, AGENTS.md, README.md, CONTRIBUTING.md allowed)
- New folders at repository root
- Duplicate documentation
- Files named `TEMP_*`, `NEW_*`, `OLD_*`, `DRAFT_*`

### WHERE Files Go:

| Type | Location |
|------|----------|
| Agent prompts/commands | `.claude/commands/` |
| Working notes (temporary) | `docs/notes/` (delete after use) |
| Architecture decisions | `docs/decisions/` |
| Old/obsolete docs | `docs/archive/` |
| Research you find online | `.claude/research-inbox/` |

### Single Source of Truth:
- Vision & Roadmap → `docs/roadmap.md`
- Architecture → `docs/ARCHITECTURE.md`
- Agent instructions → `CLAUDE.md`
- Agent rules → `AGENTS.md` (this file)

---

## GitHub Issue Rules

### Every Issue MUST Have:
1. **Clear title** with prefix: `[FEATURE]`, `[BUG]`, `[AUDIT]`, `[RESEARCH]`
2. **Acceptance criteria** - What does "done" look like?
3. **Labels** - At minimum: area/*, priority:*

### When You Find a Problem:
```bash
gh issue create --title "[BUG] Short description" --body "Details..." --label "bug"
```

### When You Finish Work:
```bash
# Comment with summary
gh issue comment 123 --body "Completed: [what you did]. PR: #XXX"

# Or close if fully done
gh issue close 123 --comment "Fixed in commit abc123"
```

---

## Commit Rules

### Format:
```
type(scope): description #ISSUE

Examples:
fix(auth): add JWT validation #351
feat(dashboard): proposal status cards #352
chore(docs): archive old files
```

### Types:
- `fix` - Bug fix
- `feat` - New feature
- `chore` - Cleanup, no behavior change
- `docs` - Documentation only
- `refactor` - Code restructure, no behavior change
- `test` - Adding tests

---

## Branch Rules

### Naming:
```
fix/short-desc-ISSUE#     # Bug fixes
feat/short-desc-ISSUE#    # New features
chore/short-desc-ISSUE#   # Cleanup
```

### Before Starting:
```bash
git checkout main
git pull origin main
git checkout -b feat/your-feature-123
```

### Before Pushing:
```bash
# Verify it works
npm run build  # frontend
pytest         # backend

# Then push
git push -u origin your-branch
```

---

## Worktree Usage (Parallel Agents)

Each agent works in its own worktree:

```bash
# Claude (main orchestrator)
/Bensley/Benlsey-Operating-System/  (main)

# Codex (security/audit)
/Bensley/bds-security/  (fix/security-351)

# Build agent
/Bensley/bds-dashboard/  (feat/dashboard-352)
```

### Rules:
- Each worktree = one issue = one branch
- Don't touch files in other worktrees
- Merge via PR, not direct push to main

---

## Definition of Done

A task is DONE when:

1. [ ] Code works (tested locally)
2. [ ] Relevant tests pass
3. [ ] No new linting errors
4. [ ] Commit references issue number
5. [ ] Issue updated with summary
6. [ ] PR created (if applicable)
7. [ ] No new files created outside allowed locations

---

## Forbidden Actions

1. **Never** push directly to main
2. **Never** create new root-level files
3. **Never** delete production data
4. **Never** commit secrets/API keys
5. **Never** modify files outside your assigned scope
6. **Never** create markdown files for temporary notes (use issue comments)

---

## Agent Communication

### To report findings:
→ Create GitHub issue

### To ask questions:
→ Comment on existing issue or create new one with `[QUESTION]` prefix

### To hand off work:
→ Comment on issue: "Handing off: [context]. Next steps: [1, 2, 3]"

### To coordinate with other agents:
→ Reference issues: "This relates to #123"

---

## Quick Reference

```bash
# Check open issues
gh issue list --state open --limit 20

# Create issue for bug found
gh issue create --title "[BUG] description" --label "bug"

# Update issue with progress
gh issue comment 123 --body "Progress: completed X, next Y"

# Create PR
gh pr create --title "description" --body "Fixes #123"

# Check your branch
git branch --show-current
git status
```

---

*Last updated: 2026-01-02*
