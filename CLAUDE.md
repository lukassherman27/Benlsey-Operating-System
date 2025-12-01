# BDS Operations Platform - Claude Context

## Single Sources of Truth (SSOT) - START HERE

| Document | Owner | Purpose |
|----------|-------|---------|
| `docs/roadmap.md` | Brain Agent | Sprint goals, priorities, blockers |
| `docs/agents/registry.md` | Organizer | Agent definitions, contracts |
| `docs/context/index.md` | Organizer | File maps, integration status |
| `docs/processes/runbooks.md` | Ops Agent | How-to guides, commands |

**Context Bundles:**
- `docs/context/architecture.md` - System diagram, tech decisions
- `docs/context/backend.md` - API, services, endpoints
- `docs/context/frontend.md` - Pages, components, state
- `docs/context/ai_agents.md` - AI features, query system
- `docs/context/business.md` - Bensley studio context, voice/tone
- `docs/context/workspaces.md` - Multi-context OS documentation

**Active Task Packs:**
- `docs/tasks/connect-orphaned-services.md`
- `docs/tasks/ux-design-system.md`
- `docs/tasks/backend-router-refactor.md`
- `docs/tasks/missing-frontend-pages.md`

---

## Current Status (Updated: 2025-12-01)

**Phase:** 1.5 - Integration & Data Quality
**Sprint:** Dec 1-15 - "Beautiful, Connected, Demo-Ready"
**Primary Goal:** Weekly proposal status reports for Bill + email/contract drafting

**See:** `docs/roadmap.md` for current sprint priorities

---

## CURRENT PRIORITY (Dec 2025)

**#1 Focus:** Generate weekly proposal status reports for Bill using:
- Meeting transcripts linked to proposals
- Emails linked to proposals
- Contacts extracted from both

**Near-term deliverables:**
1. Link transcripts → proposals (via suggestions, never auto-link)
2. Improve email → proposal linking
3. Extract contacts from emails/transcripts
4. Generate weekly proposal status reports
5. Draft follow-up emails with context
6. Draft contracts using existing templates

**NOT the priority right now:** RAG, vector stores, fancy AI features

---

## Tech Stack

**AI:** OpenAI API (gpt-4o-mini) - NOT Claude/Anthropic API
**Backend:** FastAPI on port 8000, 27 router files (main.py is only 255 lines)
**Frontend:** Next.js 15 on port 3002
**Database:** SQLite at `database/bensley_master.db` (80+ tables, ~107MB)

---

## Core Working Principles

### 1. Always Question & Challenge
- Don't blindly implement requests
- Ask: "Does this make sense architecturally?"
- Suggest better alternatives

### 2. Clean Data is Sacred
- NO junk in database
- Validate before inserting
- Test on sample data first

### 3. Always Debug & Test
- NEVER assume code works
- Test every script
- Validate database state after changes

### 4. Update Docs When You Change Code
- API endpoint changed → update `docs/context/backend.md`
- Frontend changed → update `docs/context/frontend.md`
- Database changed → create migration in `database/migrations/`
- Always update `docs/context/index.md` integration status

### 5. SSOT Enforcement - DO NOT CREATE NEW FILES
**⚠️ CRITICAL: Only these markdown files should exist outside of `docs/archive/`:**

| Location | Files |
|----------|-------|
| `docs/` root | `roadmap.md` only |
| `docs/context/` | 8 context bundles (architecture, backend, frontend, ai_agents, business, data, index, workspaces) |
| `docs/agents/` | `registry.md`, `task-pack-template.md` |
| `docs/guides/` | `DESIGN_SYSTEM.md` only |
| `docs/processes/` | `runbooks.md` only |
| `docs/tasks/` | Active task packs only |
| `.claude/` | `STATUS.md`, `commands/*.md` only |

**Rules:**
1. **NEVER create new planning/architecture/session docs** → Update `docs/roadmap.md` instead
2. **NEVER create new context docs** → Update existing `docs/context/*.md`
3. **NEVER create new agent docs** → Update `docs/agents/registry.md`
4. **When you find stale info in SSOT** → Fix it immediately, don't create a new file
5. **Historical/completed work** → Archive to `docs/archive/` or `.claude/archive/`

---

## Proposals vs. Projects

| Proposals | Projects |
|-----------|----------|
| Pre-contract, sales pipeline | Won contracts, active delivery |
| Track: health, follow-ups, status | Track: payments, schedules, RFIs |
| **Bill's #1 priority** | Secondary priority |
| Tables: `proposals`, `proposal_tracker` | Tables: `projects`, `invoices` |
| Links: `email_proposal_links` | Links: `email_project_links` |

**Never confuse these!**

---

## Quick Reference

**Run Commands:**
```bash
# Backend
cd backend && uvicorn api.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev

# Health check
make health-check
```

**Database:**
- Master: `database/bensley_master.db`
- All scripts use: `os.getenv('DATABASE_PATH', 'database/bensley_master.db')`

**Git:**
- See `docs/processes/runbooks.md` for commit format, branch naming, PR checklist
- Always push changes to GitHub after completing work

---

## When You Start a Session

1. Read `docs/roadmap.md` - Current sprint priorities
2. Check for assigned task pack in `docs/tasks/`
3. Read relevant context bundle from `docs/context/`
4. Check blockers in roadmap
5. **Ask questions if anything is unclear**

## When You End a Session

1. Write handoff note in task pack
2. Update relevant context files if you changed code
3. Update `docs/roadmap.md` if completing sprint item
4. Update `docs/context/index.md` if integration status changed
5. Commit and push to GitHub with structured message:
   ```
   [type](agent): Brief description
   Affects: [context bundles]
   ```

---

## Agent Communication Protocol

From `docs/agents/registry.md`:
- **Before work:** Read roadmap, get task pack, read context, check blockers
- **After work:** Write handoff, notify Organizer of changes, update roadmap
- **Always:** Ask questions if unsure, update docs when code changes

**Live State:**
- `.claude/STATUS.md` - Current system state and active work

---

## Philosophy

> "Ask questions, don't assume" - Build context through dialogue

> "Clean data > fancy features" - Get linking right before adding AI

> "Update docs when you change code" - Next agent needs to know

> "Proposals are priority #1" - Everything supports Bill's weekly reports
