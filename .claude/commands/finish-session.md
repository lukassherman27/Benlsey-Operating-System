# Finish Session - Professional Workflow

Run this at the END of every Claude session. No loose ends.

## Step 1: Check What Changed

```bash
git status
git diff --stat
```

Show user what files were modified.

## Step 2: Commit Changes

Small, focused commits with proper format:
```bash
git add -A
git commit -m "type(scope): description #IssueNumber"
```

Examples:
- `fix(patterns): increment times_used on match #6`
- `feat(emails): add Claude CLI workflow #7`
- `chore(scripts): archive unused backfill scripts`

## Step 3: Push Branch

```bash
git push -u origin $(git branch --show-current)
```

## Step 4: Update Issue

If work is done:
```bash
gh issue close ISSUE# --comment "Fixed in branch $(git branch --show-current)"
```

If work continues:
```bash
gh issue comment ISSUE# --body "Progress: [what was done]. Next: [what remains]."
```

## Step 5: Summary for User

Tell the user:
- "Worked on Issue #X"
- "Made N commits"
- "Branch pushed: `fix/xxx-X`"
- "Status: [complete/in-progress]"
- "Next steps: [if any]"

---

## Never Do These:
- Leave uncommitted changes
- Forget to push
- Close issues without linking commits
- Skip the summary
