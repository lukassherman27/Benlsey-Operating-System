# BDS Operations Platform - Claude Entry Point

## EVERY SESSION STARTS HERE

### Step 1: Check What's In Progress
```bash
# Check current branch
git branch --show-current

# Check open GitHub Issues
gh issue list --state open --limit 10

# Check uncommitted changes
git status
```

### Step 2: Pick Your Task
- If there's an open Issue assigned to you → Work on it
- If user gives you a task → Create an Issue first, then work on it
- If continuing previous work → Check the branch you're on

### Step 3: Create a Branch (if starting new work)
```bash
git checkout main
git pull origin main
git checkout -b fix/short-description-123  # 123 = Issue number
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

## KEY RULES

1. **Never auto-link emails** → Create suggestions for human review
2. **Always include project name** → "25 BK-033 (Ritz-Carlton Nusa Dua)" not just "25 BK-033"
3. **Test before committing** → Run the code, verify it works
4. **Small commits** → One logical change per commit
5. **Reference Issues** → `git commit -m "fix: Pattern tracking #42"`

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
