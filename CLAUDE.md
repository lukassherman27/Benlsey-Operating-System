# BDS Operations Platform - Claude Entry Point

> **You are a professional software engineer.** Follow this workflow exactly.

---

## EVERY SESSION - DO THIS FIRST

```bash
# 1. Where am I?
git branch --show-current
git status

# 2. What Issues exist?
gh issue list --state open --limit 10

# 3. Am I on main? If so, pick an issue and create a branch
git checkout main && git pull origin main
```

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
2. **Pull before starting** - `git pull origin main`
3. **Push before ending** - Don't leave uncommitted work
4. **Don't touch files another agent owns** - Check `git log --oneline -5 FILE`
5. **Create PRs, don't merge directly** - Let human review
6. **Notify related issues after merge** - Comment on other open issues your changes affect

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
