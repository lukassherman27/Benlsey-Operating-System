# Start Session - Professional Workflow

Run this at the start of EVERY Claude session. No exceptions.

## Step 1: Git Status

```bash
git branch --show-current
git status
git log --oneline -3
```

If there are uncommitted changes, ask user what to do with them.

## Step 2: Check Open Issues

```bash
gh issue list --state open --limit 10
```

Show the user the list and ask: "Which issue should I work on?"

## Step 3: Create or Switch Branch

If user picks an issue:
```bash
# Fetch latest main
git fetch origin main

# Create branch from main (not current branch!)
git checkout main
git pull origin main
git checkout -b fix/short-desc-ISSUE#
```

Branch naming rules:
- `fix/` = bug fix
- `feat/` = new feature
- `chore/` = cleanup, no behavior change

## Step 4: Confirm Scope

Before writing ANY code, tell the user:
- "I will be working on Issue #X"
- "I will create branch `fix/xxx-X`"
- "This involves files: [list them]"
- "Expected changes: [brief summary]"

Wait for user confirmation.

---

## If User Has a New Task (Not an Issue)

Create the issue FIRST:
```bash
gh issue create --title "Title" --body "Description" --label "bug"
```

Then follow steps 3-4 above.

---

## Never Do These:
- Start coding without knowing which Issue
- Use random branch names
- Work on multiple Issues in one branch
- Merge directly to main
