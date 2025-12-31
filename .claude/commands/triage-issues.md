# Issue Triage Agent

Periodically organizes all GitHub issues, categorizes them, and creates work packages.

## When to Run
- Weekly (Sunday evening)
- After logging many quick issues
- Before planning next sprint of work

## What This Agent Does

### Step 1: Audit Current State

```bash
# Get all open issues
gh issue list --state open --limit 100 --json number,title,labels,body

# Get issues needing triage
gh issue list --state open --label "needs-triage" --json number,title,body

# Get issue counts by label
gh issue list --state open --json labels | jq 'group_by(.labels[].name) | map({label: .[0].labels[0].name, count: length})'
```

### Step 2: Categorize Untriaged Issues

For each `needs-triage` issue, determine:

**Area** (pick one):
- `area/frontend` - UI, components, pages
- `area/backend` - API, services, database
- `area/database` - Schema, migrations, data quality
- `area/emails` - Email sync, categorization, linking
- `area/proposals` - Proposal tracking
- `area/projects` - Project management
- `area/learning` - AI patterns, suggestions
- `area/infrastructure` - Build, deploy, DevOps

**Type** (pick one):
- `bug` - Something is broken
- `enhancement` - New feature or improvement
- `documentation` - Docs needed
- `cleanup` - Tech debt, refactoring

**Priority** (pick one):
- `priority:p0` - Critical, blocking work
- `priority:p1` - High, needed soon
- `priority:p2` - Medium, nice to have

**Phase** (pick one based on roadmap):
- `phase:1-operations` - Q1 2026 (current)
- `phase:2-projects` - Q2 2026
- `phase:3-intelligence` - Q3-Q4 2026
- `phase:4-local-ai` - 2027

### Step 3: Apply Labels

```bash
# Example: categorize issue #123
gh issue edit 123 --add-label "area/frontend,bug,priority:p1,phase:1-operations" --remove-label "needs-triage"
```

### Step 4: Group Related Issues

Look for issues that should be worked on together:
- Same area + same feature
- Dependencies (issue A blocks issue B)
- Related bugs

Create a comment linking related issues:
```bash
gh issue comment 123 --body "Related to #124, #125 - should be fixed together"
```

### Step 5: Update Work Packages Summary

Create/update `.claude/WORK_PACKAGES.md` with:

```markdown
# Work Packages

## Ready to Work (Phase 1, P0/P1)
### Package: Proposal Dashboard Polish
- #XXX - Fix loading state
- #XXX - Add quick actions
- #XXX - Status filter bug
**Estimated effort:** 1 agent session

### Package: Email Linking Improvements
- #XXX - Pattern management UI
- #XXX - Suggestion review fixes
**Estimated effort:** 1-2 agent sessions

## Backlog (Phase 1, P2)
- #XXX - Description
- #XXX - Description

## Future (Phase 2+)
- #XXX - Description
```

### Step 6: Report Summary

Output a summary:
```
TRIAGE COMPLETE
===============
- Triaged: 5 issues
- Total open: 18 issues
- Ready to work: 3 packages (8 issues)
- Backlog: 7 issues
- Future: 3 issues

NEXT RECOMMENDED WORK:
1. Package "Proposal Dashboard Polish" (3 issues, ~2 hours)
2. Package "Email Linking" (2 issues, ~3 hours)
```

## Labels Reference

| Category | Labels |
|----------|--------|
| Area | area/frontend, area/backend, area/database, area/emails, area/proposals, area/projects, area/learning, area/infrastructure |
| Type | bug, enhancement, documentation, cleanup |
| Priority | priority:p0, priority:p1, priority:p2 |
| Phase | phase:1-operations, phase:2-projects, phase:3-intelligence, phase:4-local-ai |
| Status | needs-triage, blocked, in-progress |
