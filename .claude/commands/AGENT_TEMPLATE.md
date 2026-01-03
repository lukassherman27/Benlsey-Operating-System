# Agent Prompt Template

> **COPY THIS TEMPLATE** for every new agent. Fill in the blanks.

---

## MANDATORY HEADER (Include in EVERY prompt)

```
You are working on the Bensley Operating System.

## STEP 0: BRANCH VERIFICATION (DO THIS FIRST - NO EXCEPTIONS)

Run these commands BEFORE doing anything else:

git branch --show-current
git status

EXPECTED BRANCH: [BRANCH_NAME]

If you are NOT on [BRANCH_NAME]:
1. STOP immediately
2. Run: git checkout [BRANCH_NAME] || git checkout -b [BRANCH_NAME]
3. Verify: git branch --show-current
4. Only then continue

If the branch doesn't exist, create it from main:
git checkout main && git pull origin main && git checkout -b [BRANCH_NAME]

DO NOT PROCEED until you confirm you are on [BRANCH_NAME].
```

---

## TEMPLATE

```
You are working on the Bensley Operating System.

## STEP 0: BRANCH VERIFICATION (DO THIS FIRST - NO EXCEPTIONS)

Run these commands BEFORE doing anything else:

git branch --show-current
git status

EXPECTED BRANCH: [INSERT: feat/my-feature-123]

If you are NOT on the expected branch:
1. STOP immediately
2. Run: git checkout [EXPECTED_BRANCH] || git checkout -b [EXPECTED_BRANCH]
3. Verify again: git branch --show-current
4. Only then continue

---

ISSUE: #[INSERT_NUMBER] - [INSERT_TITLE]
BRANCH: [INSERT: feat/my-feature-123]

CONTEXT:
[INSERT: 2-3 sentences of background]

TASKS:
1. [INSERT: First task with specific file paths]
2. [INSERT: Second task]
3. [INSERT: Third task]

FILES TO MODIFY:
- [INSERT: exact/file/path.py]
- [INSERT: exact/file/path.tsx]

VERIFY:
- [INSERT: command to test it works]

BEFORE EVERY COMMIT:
1. Run: git branch --show-current
2. Confirm it shows: [EXPECTED_BRANCH]
3. Only then: git add -A && git commit -m "type(scope): description #ISSUE"

WHEN DONE:
- Push: git push -u origin [EXPECTED_BRANCH]
- Create PR: gh pr create --title "description" --body "Fixes #[ISSUE]"
- Comment on issue with summary
```

---

## WHY THIS MATTERS

Agents keep committing to wrong branches because:
1. They don't check which branch they're on
2. They assume `git checkout -b` worked (it silently fails if branch exists)
3. They don't verify before committing

The STEP 0 header fixes this by FORCING verification.

---

## WORKTREE ALTERNATIVE (For truly parallel work)

If you need agents to work in parallel without conflicts:

```bash
# Create isolated worktrees
git worktree add ../bds-agent-1 -b feat/feature-1-123
git worktree add ../bds-agent-2 -b feat/feature-2-124
git worktree add ../bds-agent-3 -b fix/bugfix-125

# Each agent works in their own directory
# Agent 1: cd ../bds-agent-1
# Agent 2: cd ../bds-agent-2
# Agent 3: cd ../bds-agent-3
```

This way agents CAN'T accidentally commit to wrong branch.
