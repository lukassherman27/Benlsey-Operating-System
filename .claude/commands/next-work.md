# Next Work - Coordinator Command

When user asks "what's next?" or runs `/next-work`, generate the next batch of agent prompts.

## How It Works

### Step 1: Check Current State

```bash
# What's in progress?
gh issue list --state open --label "in-progress"

# What's ready to work? (Phase 1, P0/P1, not blocked)
gh issue list --state open --label "phase:1-operations" --label "priority:p0" --json number,title,labels
gh issue list --state open --label "phase:1-operations" --label "priority:p1" --json number,title,labels

# Check work packages file
cat .claude/WORK_PACKAGES.md
```

### Step 2: Select Next Work Package

Priority order:
1. Any P0 issues (critical)
2. Work packages from WORK_PACKAGES.md (grouped issues)
3. Individual P1 issues
4. P2 issues if nothing else

Aim for 3-5 parallel agents per batch.

### Step 3: Generate Agent Prompts

For each selected issue/package, generate a v2.0 agent prompt:

```
## AGENT X: [Title] (#issue)

You are [doing what] for the Bensley Operations Platform.

## PHASE 1: UNDERSTAND
1. Read: CLAUDE.md, docs/roadmap.md, gh issue view [number]
2. Explore: [relevant files]
3. Query: [relevant SQL]
4. Ask yourself: [key questions]

## PHASE 2: RESEARCH
Search for: [relevant searches]
Document findings.

## PHASE 3: PLAN
Create: .claude/plans/[name].md
Include: [what to cover]
STOP for approval.

## PHASE 4: EXECUTE
1. Branch: git checkout -b [type]/[name]-[issue]
2. [Implementation steps]
3. Create PR

## SUCCESS
[Criteria]
```

### Step 4: Output Format

```markdown
# Next Work Batch - [Date]

**Status:**
- In progress: X issues
- Ready: Y issues
- Selected for this batch: Z issues

---

## AGENT 1: [Title]
[Full prompt]

---

## AGENT 2: [Title]
[Full prompt]

---

[etc.]

---

## Summary Table

| Agent | Issue | Type | Estimated Effort |
|-------|-------|------|------------------|
| 1 | #XXX | bug | 1 hour |
| 2 | #XXX | feature | 2 hours |

Copy each prompt into a separate Claude window.
```

### Step 5: Mark Issues In Progress

After user confirms they're starting the batch:
```bash
gh issue edit XXX --add-label "in-progress"
```

## Quick Reference

**User says:** "what's next?" / "next batch" / "more work" / `/next-work`
**Claude does:** Generate 3-5 agent prompts from prioritized backlog

**User says:** "triage first" / "organize issues"
**Claude does:** Run triage agent first, then generate prompts

**User says:** "just give me one thing"
**Claude does:** Pick single highest priority item
