# Codex Onboarding - Bensley Intelligence Platform

## Project Overview
You're joining the **Bensley Intelligence Platform** - a business intelligence system for Bensley Design Studios. Claude Code has been building the backend foundation, and you'll be working alongside (through Git collaboration).

## Critical Architecture - CODE vs DATA

### 1. CODE REPOSITORY (Git - Where You Work)
```
/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/
```
- This is the **Git repository** with all scripts, migrations, documentation
- This is where you and Claude Code collaborate through branches
- You'll edit code here, commit, and push to branches
- **Current working branch:** `claude/bensley-operations-platform-011CV3dp9CnqP1L5Rkjm6NYm`
- **Main branch:** `main`

### 2. DATA STORAGE (Desktop - Active Database & Files)
```
/Users/lukassherman/Desktop/BDS_SYSTEM/
├── 01_DATABASES/
│   └── bensley_master.db          # Main SQLite database (29 MB)
├── 02_ONEDRIVE_EMAIL/             # Email cache
├── 03_PROPOSALS/                  # Proposal files
├── 04_CONTACTS/                   # Contact files
└── 05_FILES/                      # Documents (852 files)
```
- This is the **active working data** (NOT in git)
- All scripts connect to this database via `.env` configuration
- Do NOT edit database files directly - use scripts

## 📝 Session Logs & Progress Tracking

**IMPORTANT:** After each significant session or when you hit context limits:

1. **Open `SESSION_LOGS.md`** in the repo root
2. **Add your session summary** using the template provided
3. **Include:** Date, what you built, files created, next steps
4. **This helps:** Claude (backend) and Codex (frontend) see each other's work without re-reading full conversations

**Example:**
```markdown
## 2025-01-14 - Codex - Built Phase 1 Dashboard
**What was done:**
- Built Next.js frontend with proposal tracker
- Connected to Claude's REST API
**Files:** frontend/src/components/dashboard/*.tsx
**Next:** Add financials screen
```

This is the **single source of truth** for "what's been done" across both AIs.

---

## Environment Configuration

All configuration is in `.env` at the repo root:

```bash
# Primary database (on Desktop)
DATABASE_PATH=/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db

# Email credentials
EMAIL_USERNAME=lukas@bensley.com
EMAIL_PASSWORD=0823356345
EMAIL_SERVER=tmail.bensley.com
EMAIL_PORT=587

# AI Configuration (when you need it)
ANTHROPIC_API_KEY=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
# Note: No credits currently on Anthropic account
OPENAI_API_KEY=
```

## What Claude Code Has Built

### ✅ Completed Systems

1. **Database Foundation** (SQLite)
   - 87 proposals with health scoring
   - 181 emails (from 2,347 total)
   - 852 documents indexed
   - 205 external contacts
   - 84 performance indexes
   - 12 migrations applied

2. **Email Intelligence** (`backend/services/`)
   - `email_content_processor_smart.py` - AI email processing (Claude/OpenAI)
   - `smart_email_matcher.py` - Fuzzy matching emails to proposals
   - Enhanced categorization (11 categories + subcategories)

3. **Daily Accountability System**
   - `daily_accountability_system.py` - Main orchestrator
   - `tracking/change_tracker.py` - Tracks all changes over time
   - `reports/enhanced_report_generator.py` - Beautiful HTML reports
   - Runs at 9 PM daily via cron
   - Two AI agents: Daily Summary + Critical Auditor

4. **Query System**
   - `query_brain.py` - Natural language queries
   - "Show me all proposals" → SQL → Results
   - Pattern matching (no AI needed)

### 📊 Database Schema

Key tables:
- `proposals` - 87 projects with health scores, status
- `emails` - Email messages
- `email_content` - AI-processed email analysis
- `email_proposal_links` - Links emails to proposals
- `documents` - 852 indexed files
- `document_proposal_links` - Links documents to proposals
- `contacts_only` - 205 external contacts

Full schema: `database/schema/bensley_master_schema.sql`

## How to Collaborate with Claude Code

### Git Workflow

1. **Claude Code works on:** Feature branches like `claude/bensley-operations-platform-*`
2. **You should work on:** Your own branches like `codex/feature-name`
3. **Lukas merges:** Both branches to `main` after review
4. **Stay in sync:** Pull from `main` regularly to get each other's work

### Avoiding Conflicts

**DO NOT work on the same files simultaneously:**
- If Claude Code is editing `daily_accountability_system.py`, work on something else
- Use different feature areas to minimize conflicts
- Coordinate with Lukas on what to build

**Database safety:**
- Only ONE agent should run database scripts at a time
- SQLite locks the database during writes
- Check if Claude Code is running scripts before you start

### Current State

**Branch:** `claude/bensley-operations-platform-011CV3dp9CnqP1L5Rkjm6NYm`

**Recent commits:**
```
cdbee32 Add manual email category verification tool
846ea8a Improve email categorization with proposal/project context
2d3186a Add migration 006: Distinguish proposals vs active projects
f858e0a Add comprehensive business case document
```

**Latest changes:**
- Enhanced daily agents with Claude API integration
- Built natural language query system
- Added AI-powered accountability reporting

## Key Files You Should Read

### Strategy & Planning
1. `BENSLEY_BRAIN_MASTER_PLAN.md` - Overall vision and roadmap ⭐ **READ THIS FIRST** ⭐
2. `README.md` - Quick start and overview
3. `BENSLEY_INTELLIGENCE_PLATFORM_BUSINESS_CASE.md` - Why we're building this
4. `IMPLEMENTATION_STATUS.md` - Current status and what's built

### Technical Documentation
1. `DAILY_ACCOUNTABILITY_SYSTEM.md` - How accountability system works
2. `ACCOUNTABILITY_SYSTEM_SUMMARY.md` - Quick summary of accountability features
3. `DEPLOYMENT_GUIDE.md` - Setup and deployment
4. `database/schema/bensley_master_schema.sql` - Full database schema (if exists)

### Code Entry Points
1. `query_brain.py` - Query system (just built)
2. `daily_accountability_system.py` - Accountability system
3. `backend/services/email_content_processor_smart.py` - Email AI processing
4. `database/migrations/` - All database migrations

## What Needs Building Next

### High Priority (What You Could Work On)

1. **Web Dashboard** (No UI exists yet!)
   - Proposal health dashboard
   - Email categorization interface
   - Document search interface
   - Query interface for query_brain.py

2. **Proposal Timeline Visualization**
   - Show proposal lifecycle
   - Communication history
   - Document timeline
   - Health score trends over time

3. **Advanced Email Features**
   - Thread grouping
   - Sentiment analysis visualization
   - Follow-up reminders
   - Email templates

4. **Enhanced Query Interface**
   - Web UI for query_brain.py
   - Saved queries
   - Query history
   - Export results

### Medium Priority

5. **Document Intelligence**
   - Extract text from PDFs
   - Search within documents
   - Automatic categorization
   - Version tracking

6. **Relationship Mapping**
   - Contact relationship graph
   - Communication patterns
   - Client interaction timeline

## Technical Stack

- **Language:** Python 3
- **Database:** SQLite 3
- **AI:** Claude Sonnet 4.5 or OpenAI GPT-4 (configurable)
- **Email:** IMAP/SMTP
- **Reporting:** HTML + Chart.js
- **Automation:** Cron jobs
- **Version Control:** Git

## Getting Started

1. **Navigate to repo:**
   ```bash
   cd /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/
   ```

2. **Check current state:**
   ```bash
   git status
   git log --oneline -10
   ```

3. **Create your branch:**
   ```bash
   git checkout -b codex/your-feature-name
   ```

4. **Test database connection:**
   ```bash
   python3 query_brain.py ~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db "Show me all proposals"
   ```

5. **Read key files:**
   - `BENSLEY_BRAIN_MASTER_PLAN.md` (start here!)
   - `README.md`
   - `IMPLEMENTATION_STATUS.md`

## Questions to Ask Lukas

Before starting work:
1. "Should I build the web dashboard or work on something else?"
2. "Are there any files Claude Code is actively editing that I should avoid?"
3. "What's the priority: UI, analytics, or data processing?"
4. "Do you want me to use React, Flask, or something else for the UI?"

## Communication Protocol

- **You and Claude Code DO NOT communicate directly**
- **All coordination goes through Lukas**
- **Use commit messages** to communicate what you built
- **Check git log** to see what Claude Code did
- **Pull from main** regularly to get integrated changes

## Important Notes

- The database has **only 181/2,347 emails** imported (8%) - this is intentional, more can be imported with `smart_email_matcher.py`
- **No AI credits** on Anthropic account currently - agents fall back to simple logic
- The system runs **daily at 9 PM** automatically via cron
- All reports go to `/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/reports/daily/`

## Success Criteria

Your work is successful when:
1. It integrates cleanly with Claude Code's backend
2. It reads from the same database without conflicts
3. Lukas can merge your branch to main without major conflicts
4. It follows the vision in `BENSLEY_BRAIN_MASTER_PLAN.md`
5. It's documented and tested

---

**Welcome to the team! You're building the future of business intelligence for Bensley Design Studios.**

*Last updated: 2025-11-14 by Claude Code*
