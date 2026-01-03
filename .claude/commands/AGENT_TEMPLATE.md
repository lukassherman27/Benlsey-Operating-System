# Agent Prompt Template

> **COPY THIS TEMPLATE** for every new agent. Fill in the blanks.

---

## MANDATORY HEADER (Include in EVERY prompt)

```
You are working on the Bensley Operating System.

## STEP 0: BRANCH SETUP (MANDATORY - ENFORCED BY HOOKS)

# 1. Setup hooks (first time only)
./scripts/setup-repo.sh

# 2. Get on your branch (works whether it exists or not)
git fetch origin
git checkout [BRANCH_NAME] 2>/dev/null || git checkout -b [BRANCH_NAME] origin/main

# 3. SET THIS - the pre-commit hook will BLOCK commits if wrong
export EXPECTED_BRANCH=[BRANCH_NAME]

# 4. VERIFY
git branch --show-current   # MUST show: [BRANCH_NAME]

The hook will block your commit if you're on the wrong branch.
```

---

## TEMPLATE

```
You are working on the Bensley Operating System.

## STEP 0: BRANCH SETUP (ENFORCED BY HOOKS)

./scripts/setup-repo.sh   # First time only

git fetch origin
git checkout [INSERT: feat/my-feature-123] 2>/dev/null || git checkout -b [INSERT: feat/my-feature-123] origin/main
export EXPECTED_BRANCH=[INSERT: feat/my-feature-123]
git branch --show-current   # MUST show your branch

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
