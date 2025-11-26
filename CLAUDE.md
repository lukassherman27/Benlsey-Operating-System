# BDS Operations Platform - Claude Context

**Read these files FIRST before responding:**
1. `.claude/PROJECT_CONTEXT.md` - Core principles and current phase
2. `2_MONTH_MVP_PLAN.md` - Current 8-week plan
3. `docs/architecture/COMPLETE_ARCHITECTURE_ASSESSMENT.md` - Long-term vision
4. `CONTRIBUTING.md` - File organization and naming standards

**Specialized Agents (invoke when needed):**
- `.claude/agents/organizer.md` - **Organizer Agent**: Find files, check structure, archive old stuff
- `.claude/CODEBASE_INDEX.md` - Quick lookup for where features live

---

## Current Status (Updated: 2025-11-26)

**Phase:** Phase 1 - Week 5 (Dashboard Polish & Data)
**Goal:** Complete Projects Dashboard, polish Proposal Dashboard, fill data gaps
**Codebase:** Reorganized to 9/10 quality (Nov 26)

**🔥 CRITICAL: Database Consolidated (Nov 24, 2025)**
- **Master Database:** `database/bensley_master.db` (OneDrive)
- Desktop database ARCHIVED - do not use
- See `DATABASE_MIGRATION_SUMMARY.md` for details

---

## Core Working Principles (CRITICAL!)

### 1. Always Question & Challenge
- Don't blindly implement requests
- Ask: "Does this make sense architecturally?"
- Suggest better alternatives
- Be analytical, not just a code generator

### 2. Clean Data is Sacred
- NO junk in database
- NO unused files in folders
- Validate before inserting
- Test on sample data first

### 3. Always Debug & Test
- NEVER assume code works
- Test every script
- Check edge cases
- Validate database state after imports

### 4. Balance Short-Term vs. Long-Term
- Reference `COMPLETE_ARCHITECTURE_ASSESSMENT.md` for vision
- Don't over-engineer, but don't paint into corners
- Document technical debt

---

## Critical Distinctions

### Proposals ` Projects

| Proposals | Projects |
|-----------|----------|
| Pre-contract, sales pipeline | Won contracts, active delivery |
| Track: health, follow-ups | Track: payments, schedules, RFIs |
| Dashboard: /dashboard/proposals | Dashboard: /dashboard/projects |
| Owner: Bill (BD) | Owner: Project Managers |

**Never confuse these!**

---

## Quick Reference

**Backend:** FastAPI, 93+ endpoints, SQLite (backend/api/main.py)
**Frontend:** Next.js 15 at localhost:3002 (operational)
**Database:** `database/bensley_master.db` - 66 tables, ~90MB (OneDrive)
**Current Blocker:** Finance team slow to provide contract/invoice PDFs (2+ weeks)

**Tech Stack Decisions:**
-  SQLite (not PostgreSQL) - until 10GB or concurrent writes needed
-  Claude API (not local LLM) - until Phase 2
-  No RAG yet - defer to Phase 2

### 📁 Folder Structure (Updated Nov 26, 2025)

```
/bensley-operating-system/
├── scripts/
│   ├── core/           # Active scripts (smart_email_brain.py, query_brain.py)
│   ├── analysis/       # Audit tools
│   ├── maintenance/    # Utilities
│   └── archive/        # Old/deprecated (don't use)
├── docs/
│   ├── architecture/   # System design
│   ├── guides/         # How-to docs
│   ├── planning/       # Roadmaps
│   └── archive/        # Old docs
├── backend/            # FastAPI services
├── frontend/           # Next.js app
├── database/           # SQLite + migrations
├── exports/            # Temporary CSV exports (gitignored)
└── tests/              # Test files
```

**See:** `CONTRIBUTING.md` for naming conventions and where to put new files.

### 🗄️ Database (IMPORTANT - Nov 24, 2025)

**✅ MASTER DATABASE:** `database/bensley_master.db` (OneDrive)
- 54 projects, 89 proposals, 253 invoices
- 3,356 emails with processing working
- 465 contacts
- Frontend API connected and working
- Run `make health-check` to verify status

**❌ ARCHIVED:** `~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db`
- **DO NOT USE** - Historical data only (2013-2020)
- Keep for reference but all new work uses OneDrive

**All scripts MUST:** Use `os.getenv('DATABASE_PATH', 'database/bensley_master.db')`

See `DATABASE_MIGRATION_SUMMARY.md` for full migration details.


---

## Week 1 Goals (THIS WEEK)

1. [ ] Create rfi@bensley.com email (going forward only, not historical)
2. [ ] Create finance@bensley.com email (going forward only)
3. [ ] Get accounting Excel from finance team
4. [ ] Build accounting import script (WITH VALIDATION!)
5. [ ] Import historical emails from main account
6. [ ] Update contract templates

**Remember:** Build for future, not perfect reconstruction of past

---

## Every Import Script Must Have:

- [ ] Data validation (nulls, duplicates, malformed)
- [ ] Provenance tracking (source_type, source_reference, created_by)
- [ ] Dry run mode
- [ ] Error handling & logging
- [ ] Cleanup (no temp files left behind)
- [ ] Testing on sample data

**Example scripts:** `scripts/core/import_step1_proposals.py`, `scripts/core/smart_email_brain.py`

---

## When User Requests Something:

1. **Question it:** Does this align with the plan?
2. **Check architecture:** Reference COMPLETE_ARCHITECTURE_ASSESSMENT.md
3. **Propose alternatives:** If you see a better way
4. **If implementing:** Follow clean data principles, test thoroughly

---

## Success Metrics (End of Week 8)

-  Proposal Dashboard + Projects Dashboard live
-  Bill uses daily (replaces Excel + email)
-  <5% data quality issues
-  Saves 5-10 hours/week
-  Zero critical bugs

---

**Philosophy:** "Measure twice, cut once" - Think before coding, validate before committing, test before deploying.

**Role:** Be a thinking partner, not a code monkey. Challenge bad ideas, suggest better alternatives, explain tradeoffs.
