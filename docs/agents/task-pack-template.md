# Task Pack Template

**Purpose:** Give an agent everything they need to complete a scoped task.

---

## Template

```markdown
# Task Pack: [Epic Name]

**Created:** [Date]
**Assigned To:** [Agent Name]
**Priority:** [P0/P1/P2]
**Estimated:** [Hours]

---

## Objective

[1-2 sentences describing the goal]

---

## Context to Read First

- [ ] `docs/roadmap.md` - Current sprint priorities
- [ ] `docs/context/[relevant].md` - Domain context
- [ ] [Any other specific files needed]

---

## Scope

### In Scope
- [Specific deliverable 1]
- [Specific deliverable 2]
- [Specific deliverable 3]

### Out of Scope (Don't Touch)
- [Thing to explicitly avoid]
- [File/feature not to modify]

---

## Files to Edit

| File | Action | Notes |
|------|--------|-------|
| `path/to/file1.py` | Modify | Add X functionality |
| `path/to/file2.tsx` | Create | New component |
| `path/to/file3.sql` | Create | Migration |

---

## Acceptance Criteria

- [ ] [Testable requirement 1]
- [ ] [Testable requirement 2]
- [ ] [Testable requirement 3]

---

## Commands to Run

```bash
# Test your changes
[command 1]

# Verify it works
[command 2]

# Final check
[command 3]
```

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Tests pass
- [ ] No lint errors
- [ ] Context files updated if needed
- [ ] Handoff note written below

---

## Handoff Note

**Completed By:** [Agent Name]
**Date:** [Date]

### What Changed
- [File 1]: [What was added/modified]
- [File 2]: [What was added/modified]

### What's Left
- [Any remaining work]
- [Any blockers discovered]

### Gotchas for Next Agent
- [Important thing to know]
- [Potential issue]

### Files Affected (for Organizer)
- [List of all files changed]
```

---

## Example Task Pack

See `docs/tasks/connect-orphaned-services.md` for a real example.
