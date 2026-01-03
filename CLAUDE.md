# BDS Operations Platform - Claude Entry Point

> **You are a professional software engineer.** Follow this workflow exactly.

---

## EVERY SESSION - DO THIS FIRST

```bash
# 1. SETUP (first time only)
./scripts/setup-repo.sh   # Configures git hooks

# 2. WHERE AM I? (every session)
git branch --show-current
git status

# 3. GET ON YOUR BRANCH (if not already)
# Use this command - it works whether branch exists or not:
git fetch origin
git checkout feat/my-feature-123 2>/dev/null || git checkout -b feat/my-feature-123 origin/main

# 4. SET EXPECTED_BRANCH (enforced by pre-commit hook)
export EXPECTED_BRANCH=feat/my-feature-123

# 5. VERIFY
git branch --show-current  # MUST match your issue's branch
```

**WARNING:** Do NOT run `git checkout main`. Stay on your feature branch.
If you need latest main: `git fetch origin && git rebase origin/main`

---

## BRANCH NAMING (MANDATORY)

| Type | Pattern | Example |
|------|---------|---------|
| Bug fix | `fix/short-desc-ISSUE#` | `fix/pattern-tracking-6` |
| Feature | `feat/short-desc-ISSUE#` | `feat/claude-email-workflow-7` |
| Cleanup | `chore/short-desc-ISSUE#` | `chore/archive-scripts-0` |

**NEVER** use random branch names like `claude/debug-xxx-abc123`.

**ALWAYS** reference an Issue number. If no Issue exists, create one first:
```bash
gh issue create --title "Short description" --body "Details..."
# Returns: https://github.com/.../issues/42
git checkout -b fix/short-desc-42
```

---

## TECH STACK

| Layer | Tech | Port | Command |
|-------|------|------|---------|
| Backend | FastAPI | 8000 | `cd backend && uvicorn api.main:app --reload --port 8000` |
| Frontend | Next.js 15 | 3002 | `cd frontend && npm run dev` |
| Database | SQLite | - | `database/bensley_master.db` |
| AI | Claude CLI | - | You are here |

---

## MCP DATABASE ACCESS

Claude Code has direct database access via the Model Context Protocol (MCP). This means you can query `bensley_master.db` directly during conversations.

### How It Works
The `.mcp.json` file configures the SQLite MCP server. When Claude Code starts in this project, it connects to the database automatically.

### Available Tools
| Tool | Purpose |
|------|---------|
| `read_query` | Execute SELECT statements |
| `write_query` | Execute INSERT/UPDATE/DELETE |
| `list_tables` | Show all tables in database |
| `describe_table` | Show column definitions |

### Example Queries

```
# Instead of running sqlite3 commands in bash, just ask:
"How many unlinked emails do we have?"
"Show me proposals created this month"
"What are the most used email patterns?"
```

### Check MCP Status
```bash
claude mcp list  # Shows connected MCP servers
```

### Security Note
- The database contains sensitive business data
- MCP access is local-only (no network exposure)
- Changes are logged in sqlite - be careful with write operations

---

## COMMIT MESSAGES (MANDATORY)

```bash
# Format: type(scope): description #ISSUE

git commit -m "fix(patterns): increment times_used on match #6"
git commit -m "feat(emails): add Claude CLI analysis workflow #7"
git commit -m "chore(scripts): archive one-time backfill scripts"
```

| Type | When |
|------|------|
| `fix` | Bug fix |
| `feat` | New feature |
| `chore` | Cleanup, refactoring, no behavior change |
| `docs` | Documentation only |

---

## MULTI-AGENT RULES

When multiple Claude agents work on the same codebase:

1. **Each agent = one Issue = one branch** - Never share branches
2. **Use worktrees for parallel work** (see below)
3. **Set EXPECTED_BRANCH** - The hook enforces it
4. **Push before ending** - Don't leave uncommitted work
5. **Create PRs, don't merge directly** - main is protected
6. **Notify related issues after merge** - Comment on affected issues

### Worktrees (RECOMMENDED for parallel agents)

```bash
# Create isolated worktrees - agents CAN'T commit to wrong branch
git worktree add ../bds-agent-1 -b feat/feature-1-123
git worktree add ../bds-agent-2 -b feat/feature-2-124

# Each agent works in their own directory
# Agent 1 prompt: "cd ../bds-agent-1 && ..."
# Agent 2 prompt: "cd ../bds-agent-2 && ..."
```

### Cross-Issue Notification (MANDATORY)

After merging a PR, check if your changes impact other open issues:

```bash
# 1. List open issues
gh issue list --state open --limit 20

# 2. For each issue that shares area/* labels or touches same files:
gh issue comment ISSUE_NUMBER --body "FYI: PR #XX modified [what]. This may affect this issue because [why]."
```

**Examples:**
- PR changes `pattern_first_linker.py` → Comment on #7 (email learning loop), #17 (email review queue)
- PR changes proposal API → Comment on #13 (email thread view), #14 (PM dashboard)

**Check `.github/CODEOWNERS`** to understand which areas your changes touch.

---

## MANDATORY RULES (LUKAS SAID SO)

### Before Every Commit
1. **Test it works** - Run the code, verify no crashes
2. **Check vision** - Does this fit the bigger picture?
3. **Explain in plain English** - Lukas doesn't code, no jargon

### When You Find Broken Code
1. **Tell Lukas first** - "I found X is broken"
2. **Create an Issue** - `gh issue create --title "Bug: description" --label "bug"`
3. **Fix if quick (<5 min)** - Otherwise leave for dedicated session

### How to Report Back
Always give Lukas **bullet points**:
- **What changed**: What files, what features
- **Why**: What problem this solves
- **What's next**: What should happen after this

### Other Rules
1. **Never auto-link emails** → Create suggestions for human review
2. **Always include project name** → "25 BK-033 (Ritz-Carlton Nusa Dua)" not just "25 BK-033"
3. **Small commits** → One logical change per commit
4. **Reference Issues** → `git commit -m "fix(patterns): tracking #6"`

---

## KEY FILES

| What | Where |
|------|-------|
| Email sync | `scripts/core/scheduled_email_sync.py` |
| Pattern matching | `backend/services/pattern_first_linker.py` |
| Learning | `backend/services/learning_service.py` |
| API routes | `backend/api/routers/*.py` |
| Database | `database/bensley_master.db` |

---

## WHEN YOU FINISH

```bash
# 1. Commit your changes
git add -A
git commit -m "feat: Description of change #IssueNumber"

# 2. Push your branch
git push -u origin your-branch-name

# 3. Create PR (optional, or tell user to review)
gh pr create --title "Description" --body "Fixes #IssueNumber"

# 4. Update STATUS.md with what you did
```

---

## FOR MORE CONTEXT

| Doc | When to Read |
|-----|--------------|
| `.claude/STATUS.md` | Current numbers, what's working/broken |
| `.claude/HANDOFF.md` | Deep business context, patterns, rules |
| `docs/ARCHITECTURE.md` | System design, database schema |
| `docs/ROADMAP.md` | Future plans, phases |

---

## QUICK DATABASE CHECK

```sql
-- Basic counts
SELECT 'emails' as tbl, COUNT(*) FROM emails
UNION SELECT 'proposals', COUNT(*) FROM proposals
UNION SELECT 'projects', COUNT(*) FROM projects
UNION SELECT 'patterns', COUNT(*) FROM email_learned_patterns;
```

---

## THE VISION

**READ THE FULL VISION:** `docs/roadmap.md`

That file contains:
- Complete system vision (Bensley Brain)
- Phase timeline (what's built when)
- Success metrics
- Agent structure

### Quick Summary (but read roadmap.md for full picture)
- **January 2026**: Bill & PMs testing proposals, projects, meetings
- **Priority #1**: Proposals (Bill's daily tool)
- **Priority #2**: Email linking (makes proposals useful)
- **Priority #3**: Projects (PM testing in February)

### The Learning Loop
```
Email arrives → Pattern-first linker tries to match
     ↓
No match? → Claude CLI analyzes with database context
     ↓
Claude creates suggestion → Human approves
     ↓
Approval → Pattern learned for next time
```
