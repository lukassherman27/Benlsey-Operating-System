# How The System Actually Works

**Read this in 5 minutes. Then you'll get it.**

---

## There Are Only 3 Things

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   1. CRON JOBS          2. BROWSER           3. CLAUDE      │
│   (automatic)           (you review)         (you build)    │
│                                                             │
│   Runs every hour       localhost:3002       Claude CLI     │
│   You don't touch       5-10 min/day         When building  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

That's the whole system. Let me explain each one.

---

## 1. CRON JOBS (Automatic - You Don't Touch)

These scripts run on a schedule. You set them up ONCE and forget.

### What Runs Automatically

| Script | When | What It Does |
|--------|------|--------------|
| `scheduled_email_sync.py` | Every hour | Fetches new emails from Gmail |
| `email_linker.py` | After sync | Links emails to proposals (pattern matching) |
| `daily_followup_check.py` | 8am daily | Finds stale proposals, sends alert |
| `health_scorer.py` | After sync | Updates proposal health scores |

### How To Set Up Cron (One Time)

```bash
# Open cron editor
crontab -e

# Add these lines:
0 * * * * cd /path/to/project && python scripts/core/scheduled_email_sync.py >> logs/sync.log 2>&1
0 8 * * * cd /path/to/project && python scripts/core/daily_followup_check.py >> logs/followup.log 2>&1
```

**That's it.** Now emails sync automatically. You never run these manually.

### How You Know It's Working

```bash
# Check last sync
sqlite3 database/bensley_master.db "SELECT MAX(created_at) FROM emails;"

# Check cron logs
tail -20 logs/sync.log
```

---

## 2. BROWSER (You Review - 5-10 min/day)

This is where YOU make decisions. The automated system creates suggestions. You approve or reject them.

### Your Daily Review (5-10 minutes)

**Step 1:** Open `localhost:3002/admin/suggestions`

**Step 2:** Review the queue:
```
┌─────────────────────────────────────────────────────────────┐
│  "Link john@client.com to 25 BK-045?"                       │
│  Confidence: 85%                                            │
│  Reason: Same domain as 3 other linked emails               │
│                                                             │
│  [Approve]  [Reject]  [Edit]                                │
└─────────────────────────────────────────────────────────────┘
```

**Step 3:** Click Approve or Reject

**That's it.** Every approval teaches the system. Next time, similar emails link automatically.

### The Learning Loop

```
Week 1: 100 emails → 60 need your review
Week 2: 100 emails → 40 need your review (20 auto-linked)
Week 4: 100 emails → 15 need your review (85 auto-linked)
```

**The more you review, the smarter it gets.**

---

## 3. CLAUDE (You Build Features)

This is when you open Claude CLI and build something. Could be fixing a bug, adding a page, whatever.

### The Process (Every Session)

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  START SESSION                                               │
│  ─────────────────                                           │
│  1. Read STATE.md (what's the current task?)                 │
│  2. Run smoke_test.py (is everything working?)               │
│                                                              │
│  DO WORK                                                     │
│  ─────────────────                                           │
│  3. Make ONE change                                          │
│  4. Test it works                                            │
│  5. Commit                                                   │
│                                                              │
│  END SESSION                                                 │
│  ─────────────────                                           │
│  6. Run smoke_test.py again                                  │
│  7. Update STATE.md (what did you do? what's next?)          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### STATE.md (The Memory)

This is how Claude sessions "remember" what happened:

```markdown
# STATE

## Current Task
Fix proposal tracking bugs

## Last Session
- Fixed status_handler.py
- Verified with smoke test
- Remaining: frontend changes

## Next Steps
1. Add slide-in panel to tracker
2. Test with real data

## Updated
2025-12-10 15:00
```

**Every session reads this first, updates it last.**

---

## How They Connect

```
CRON JOBS create data
     ↓
     ↓  (emails, suggestions, scores)
     ↓
DATABASE holds everything
     ↑
     │
BROWSER shows data, you approve suggestions
     │
     ↓  (your approvals become patterns)
     ↓
CRON JOBS use patterns to auto-link more

Meanwhile...

CLAUDE builds new features that show the data better
```

**The database is the coordination layer.** Everything reads from it, writes to it.

---

## Running Multiple Claudes (Parallelism)

You CAN run 2-3 Claude sessions at once to do more work.

### The Rule: Different Directories = Safe

```
✅ SAFE: Different parts of codebase
   Claude 1: Working on frontend/src/
   Claude 2: Working on backend/services/

✅ SAFE: Different task types
   Claude 1: Fixing bugs (writes code)
   Claude 2: Auditing data (read-only)

❌ DANGEROUS: Same files
   Claude 1: Editing proposals.py
   Claude 2: Also editing proposals.py
   → They'll overwrite each other
```

### The Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  CLAUDE 1 (Frontend)        CLAUDE 2 (Backend)              │
│  "Fix the tracker page"     "Fix the at-risk endpoint"      │
│                                                             │
│  Only touches:              Only touches:                   │
│  - frontend/src/            - backend/api/                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    Both commit separately
                              ↓
                    You merge/coordinate
```

### How To Scope Claude Sessions

**Session 1:**
```
"You are Frontend Builder. Only touch frontend/src/.
Fix the tracker page. Don't touch backend."
```

**Session 2:**
```
"You are Backend Builder. Only touch backend/.
Fix the at-risk endpoint. Don't touch frontend."
```

**Session 3:**
```
"You are Data Auditor. Read-only. Don't modify files.
Run queries. Report issues."
```

**YOU are the coordinator.** You scope the tasks, you merge the results.

---

## Your Actual Day

### Morning (5 min)
1. Open `localhost:3002/admin/suggestions`
2. Approve/reject 5-20 suggestions
3. Done

### When Building (1-3 Claude sessions)
1. Open Claude CLI
2. Scope it: "Only touch X, do Y"
3. Let it work
4. Verify it works
5. Repeat with another Claude if needed

### What You DON'T Do
- Run email sync manually (cron does it)
- Coordinate agents (there are no agents - just scoped Claude sessions)
- Update complex docs (just STATE.md, 30 lines)

---

## Terminal Setup

**What you need running:**
```
Terminal 1: cd backend && uvicorn api.main:app --reload --port 8000
Terminal 2: cd frontend && npm run dev
```

**That's it.** Two terminals for servers.

Claude sessions are separate terminal windows when you're building.

Cron jobs run in background - no terminal needed.

---

## The Mental Model

```
"Agents"       = cron jobs (scripts on schedule)
"Coordination" = the database (everything reads/writes to SQLite)
"Memory"       = STATE.md (30 lines, updated each Claude session)
"Human loop"   = you in browser clicking approve/reject
"Building"     = Claude sessions, scoped by directory
"Parallelism"  = multiple Claudes on different directories
```

**There is no complex multi-agent framework.**

It's just:
- Scripts (cron)
- Database (SQLite)
- Browser (localhost:3002)
- Claude CLI (when building)

---

## Quick Reference

| What | How | When |
|------|-----|------|
| Emails sync | Cron job | Automatic, hourly |
| Review suggestions | Browser | Daily, 5-10 min |
| Build features | Claude CLI | When you want |
| Parallel work | Multiple Claudes | Scope by directory |
| Remember state | STATE.md | Every Claude session |
| Verify nothing broke | smoke_test.py | Before/after Claude work |

---

## FAQ

**Q: Do I need CrewAI/AutoGen/LangGraph?**
A: No. Cron + Browser + Claude CLI does everything.

**Q: How do agents talk to each other?**
A: Through the database. Script A writes rows. Script B reads them.

**Q: What if Claude breaks something?**
A: Run smoke_test.py before and after. If it fails, undo.

**Q: Can I run 5 Claudes at once?**
A: Yes, if they're all scoped to different directories. You coordinate.

**Q: Where's the coordinator agent?**
A: You. You're the coordinator. You scope tasks, you merge results.
