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

---

## KEY RULES

1. **Never auto-link emails** → Create suggestions for human review
2. **Always include project name** → "25 BK-033 (Ritz-Carlton Nusa Dua)" not just "25 BK-033"
3. **Test before committing** → Run the code, verify it works
4. **Small commits** → One logical change per commit
5. **Reference Issues** → `git commit -m "fix(patterns): tracking #6"`

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

**Bensley Brain** - AI-powered operations for luxury design firm.
- **Proposals** = Sales pipeline (Bill's #1 priority)
- **Projects** = Active contracts
- **Learning Loop** = Claude analyzes emails → Suggestions → Human approves → System learns
