# Consolidated Build Plan

**Date:** 2025-12-30
**Based on:** Comprehensive System Audit
**Goal:** Transform the current system into a functional operating system for Bensley

---

## PHASE 0: CLEANUP (Do First)

Before building new features, clean up the mess.

### 0.1 Database Cleanup

| Task | Priority | Effort | Issue # |
|------|----------|--------|---------|
| Merge `proposal_tracker` → `proposals` | CRITICAL | 2-3 hrs | Create new |
| Delete empty unused tables (calendar_blocks, commitments, etc.) | High | 1 hr | #61 |
| Fix legacy category column sync | Medium | 1 hr | #100 |

**Tables to DELETE:**
```sql
DROP TABLE IF EXISTS calendar_blocks;
DROP TABLE IF EXISTS commitments;
DROP TABLE IF EXISTS contract_terms;
DROP TABLE IF EXISTS project_colors;
DROP TABLE IF EXISTS project_status_tracking;
DROP TABLE IF EXISTS project_pm_history;
DROP TABLE IF EXISTS project_outreach;
DROP TABLE IF EXISTS learned_user_patterns;
```

**Tables to KEEP (empty but needed):**
- `deliverables` - Needs UI (Phase 1)
- `daily_work` - Needs email intake (Phase 1)
- `*_embeddings` - Phase 3 vector store

### 0.2 Script Consolidation

| Action | Scripts | Result |
|--------|---------|--------|
| KEEP | `scheduled_email_sync.py` | Hourly email import |
| KEEP | `daily_accountability_system.py` | Daily accountability |
| KEEP | `backup_database.py` | LaunchD backups |
| MERGE | `smart_email_brain.py` + `claude_email_analyzer.py` + `smart_categorizer.py` | One analysis script |
| ARCHIVE | `backfill_*.py`, `review_enrichment_*.py` | Move to `scripts/archive/` |
| DELETE | `continuous_email_processor.py` | Redundant |

### 0.3 Frontend Cleanup

| Action | Current | Target |
|--------|---------|--------|
| Consolidate | `/tracker` + `/overview` | Single `/proposals` page |
| Remove | 6 hidden pages | Keep only if needed |
| Merge | 10 admin pages | 3-4 admin pages |

### 0.4 API Cleanup

| Action | Issue # | Notes |
|--------|---------|-------|
| Standardize response formats | #126 | Inconsistent across endpoints |
| Remove `proposal_tracker` endpoints | - | After merge |

---

## PHASE 1: CORE FEATURES (P1 - Build Now)

These are the features that make the system useful.

### 1.1 Deliverables Input UI (#245)

**What:** Allow PMs to input project milestones and tasks.

**Structure:**
```
Project
└── Discipline (Landscape, Interior, etc.)
    └── Milestone (25%, 50%, 100%)
        └── Task (design-level deliverable)
```

**Requirements:**
- Dynamic structure (not rigid dropdowns)
- Link to project
- Connect tasks to people
- Support deadline tracking

**Backend:** `deliverables` table exists, needs API endpoints
**Frontend:** New page + form components

### 1.2 Daily Work System (#244)

**What:** Capture architect work, route to Bill/Brian for review, create tasks from feedback.

**Flow:**
```
Architect emails dailywork@bensley.com
        ↓
System imports to daily_work table
        ↓
Bill/Brian see review UI
        ↓
Review creates feedback
        ↓
Feedback becomes task
```

**Requirements:**
- Email intake (new address or existing?)
- Review UI with approve/feedback actions
- Task creation from feedback
- NO rigid format - architects write freeform

**Backend:** `daily_work` table exists, needs intake + API
**Frontend:** New review interface

### 1.3 Task Enhancement (#247)

**What:** Enhance existing task system with hierarchy and sources.

**Requirements:**
- Parent/child task relationships
- Multiple sources: Meeting, Daily Work, PM Input, Manual
- Link tasks to projects and people
- Support different task types

**Backend:** Enhance `tasks` table schema
**Frontend:** Update task views

### 1.4 AI Suggestions Bug Fix (#241)

**What:** Fix linking UI overflow and category issues.

**Backend:** Check category mappings
**Frontend:** Fix overflow CSS, expand categories

---

## PHASE 2: PROJECT MANAGEMENT (P2 - After Phase 1)

### 2.1 Phase Progress Visualization (#246)

- Show milestone progress (25%, 50%, 100%)
- Visual indicators per discipline
- Connect to invoice triggers

### 2.2 My Day Dashboard

- Personal task view
- Today's meetings with AI prep
- Daily work feedback display
- Action items from meetings

### 2.3 Invoice Milestone Alerts

- Reminder at milestone completion
- NOT automatic invoice generation
- Link to deliverables progress

### 2.4 RFI Tracking (#204)

- Expand existing (2 records)
- Link to projects and contacts
- Track status and responses

### 2.5 Meeting Action Items (#194)

- Extract from transcripts (AI)
- Convert to tasks
- Link to meetings and projects

---

## PHASE 3: INTELLIGENCE (P3 - Future)

Requires more data accumulation first.

| Feature | Issue # | Prerequisite |
|---------|---------|--------------|
| Vector store embeddings | #198 | 5K+ documents |
| AI query interface | #199 | Vector store |
| Proactive alerts | #200 | More patterns |
| MCP SQLite integration | #256 | Research complete |

---

## PHASE 4: LOCAL AI (P4 - Much Later)

Based on research: NOT RECOMMENDED NOW.

| Feature | Issue # | Trigger |
|---------|---------|---------|
| Ollama integration | #201 | GPT costs > $500/mo |
| Fine-tuned model | #202 | 10K+ approved suggestions |

---

## IMPLEMENTATION ORDER

### Week 1: Cleanup
```
Day 1-2:
├── Merge proposal_tracker → proposals
├── Update all API references
├── Delete duplicate frontend pages
└── Create migration script

Day 3-4:
├── Delete unused database tables
├── Archive one-time scripts
├── Consolidate email analysis scripts
└── Clean admin navigation

Day 5:
├── Test everything works
├── Create cleanup PR
└── Document changes
```

### Week 2-3: Deliverables UI
```
├── Design deliverable data model
├── Build API endpoints (CRUD)
├── Create input form UI
├── Link to projects table
├── Connect to milestone system
└── Test with sample data
```

### Week 4-5: Daily Work System
```
├── Set up email intake
├── Build processing script
├── Create review UI
├── Implement feedback → task flow
└── Test full workflow
```

### Week 6-7: Task Enhancement
```
├── Update tasks table schema
├── Add parent/child relationships
├── Build source tracking
├── Update task UI
└── Connect to deliverables
```

### Week 8+: My Day Dashboard
```
├── Design personal dashboard
├── Implement meeting prep AI
├── Add task aggregation
├── Build action item tracking
└── Test with real users
```

---

## SUCCESS METRICS

| Metric | Current | Target |
|--------|---------|--------|
| Tables with data | ~50/129 | ~60/100 (cleanup + features) |
| Running scripts | 2 | 3-4 (add features) |
| Pages in navigation | ~20 | ~12 (consolidate) |
| Email link rate | 65.4% | 85%+ |
| Bill using daily | No | Yes |

---

## DEPENDENCIES

```
Cleanup ──────────────────────────────────┐
                                          │
Deliverables UI ──┐                       │
                  ├── Phase Progress ─────┼── My Day Dashboard
Task Enhancement ─┘                       │
                                          │
Daily Work System ────────────────────────┘
```

---

## GITHUB ISSUES TO CREATE

Based on audit, create these issues:

1. `[CLEANUP] Merge proposal_tracker into proposals table`
2. `[CLEANUP] Delete unused database tables`
3. `[CLEANUP] Archive one-time migration scripts`
4. `[CLEANUP] Consolidate admin pages (10 → 4)`
5. `[CLEANUP] Remove duplicate proposal pages`

---

## QUESTIONS BLOCKING PROGRESS

1. **Proposal tables:** Can we merge and delete `proposal_tracker`?
2. **Daily work email:** Is `dailywork@bensley.com` set up?
3. **Admin consolidation:** Approved to merge 10 → 4 pages?
4. **Embedding tables:** Keep for Phase 3 or delete now?
5. **Scheduling PDFs:** Build PDF parser for task extraction?

---

## APPENDIX: Current State Summary

| Category | Count | Healthy | Needs Work |
|----------|-------|---------|------------|
| Database tables | 129 | ~50 | 79 empty |
| Python scripts | 30 | 2 active | 28 standalone |
| Frontend pages | 35 | ~15 | 20 hidden/unused |
| GitHub issues | 33 | 17 valid P1/P2 | 16 future/stale |

**Bottom line:** Clean up first, then build deliverables + daily work + tasks. That's the foundation for everything else.
