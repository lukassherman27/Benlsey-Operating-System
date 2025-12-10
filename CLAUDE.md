# BDS Operations Platform - Claude Context

---

## ⚠️ CRITICAL: READ THIS FIRST

**DO NOT CREATE NEW FILES.** This system has 4 SSOT files. Update them, don't create new ones.

| File | Purpose |
|------|---------|
| `.claude/STATUS.md` | Live numbers, what's working/broken |
| `.claude/HANDOFF.md` | Business context, data rules, agent instructions |
| `docs/roadmap.md` | Plan, phases, priorities, folder structure |
| `docs/ARCHITECTURE.md` | System design, database schema, services |

**If you want to create a file:**
1. **DON'T.** Update an existing SSOT file instead.
2. If you MUST create something, it goes in an existing folder (scripts/core/, backend/services/, etc.)
3. NEVER create files at root level
4. NEVER create new .md files in docs/

---

## Quick Start

```
1. Read .claude/STATUS.md - Live numbers, what's working/broken
2. Read .claude/HANDOFF.md - Agent context, patterns, don't-do-this
3. Read docs/ROADMAP.md - Current priorities, phase timeline
4. Read docs/ARCHITECTURE.md - System design, data flows
```

---

## Tech Stack

| Layer | Technology | Port |
|-------|------------|------|
| AI | OpenAI GPT-4o-mini | API |
| Backend | FastAPI (Python) | 8000 |
| Frontend | Next.js 15 | 3002 |
| Database | SQLite | - |

**Database:** `database/bensley_master.db` (~107MB, 108 tables)

---

## Core Principles

### 1. Always Name Projects
- Wrong: "25 BK-033 has issues"
- Right: "25 BK-033 (Ritz-Carlton Reserve Nusa Dua) has issues"
- Look up: `SELECT project_code, project_name FROM proposals WHERE project_code = ?`

### 2. Clean Data is Sacred
- NO junk in database
- Validate before inserting
- Test on sample data first

### 3. Always Test
- NEVER assume code works
- Run it, verify it works

### 4. Update Docs When Code Changes
- Changed something? Update the relevant doc
- Next agent needs to know

### 5. Never Auto-Link
- Always create suggestions
- Let humans approve

---

## Proposals vs. Projects

| Proposals | Projects |
|-----------|----------|
| Pre-contract, sales pipeline | Won contracts |
| Track: health, follow-ups | Track: payments, RFIs |
| **Bill's #1 priority** | Secondary |
| Table: `proposals` | Table: `projects` |

---

## Run Commands

```bash
# Backend
cd backend && uvicorn api.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev

# Sync emails
python scripts/core/scheduled_email_sync.py

# Check database
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM emails;"
```

---

## Session Protocol

### When Starting
1. Read `.claude/STATUS.md` for numbers
2. Read `docs/ROADMAP.md` for priorities
3. Check `.claude/HANDOFF.md` for context

### When Ending
1. Update `.claude/STATUS.md` with new numbers
2. Note what you changed
3. Commit and push to GitHub

---

## Key Files

| Purpose | File |
|---------|------|
| Email import | `backend/services/email_importer.py` |
| Email pipeline | `backend/services/email_orchestrator.py` |
| Transcription | `voice_transcriber/transcriber.py` |
| Suggestions | `backend/services/suggestion_writer.py` |
| Handlers | `backend/services/suggestion_handlers/*.py` |

---

## Philosophy

> "Ask questions, don't assume"

> "Clean data > fancy features"

> "Proposals are priority #1"
