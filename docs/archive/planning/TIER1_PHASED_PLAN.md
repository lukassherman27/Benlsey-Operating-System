# TIER 1: DATA FOUNDATION - Phased Development Plan

**Owner:** Coordinator Agent
**Created:** 2025-12-01
**Status:** Active

---

## Overview

This document defines the sequenced phases for Tier 1 (Data Foundation). Each phase builds on the previous. Do not skip phases.

**End Goal:** Weekly proposal status reports for Bill with accurate, human-verified email/transcript context.

---

## PHASE A: Infrastructure Integrity

### Gate Criteria (Must Pass Before Phase B)
- [ ] Backend running with canonical DB path (`database/bensley_master.db`)
- [ ] Zero 500 errors on core endpoints
- [ ] `/api/health` returns 200
- [ ] `/api/finance/*` endpoints all return 200
- [ ] All 27 routers verified working
- [ ] DB path sanity check passes (no hardcoded Desktop paths)

### Tasks

| # | Task | Verification |
|---|------|--------------|
| 1 | Verify backend starts with `DATABASE_PATH=database/bensley_master.db` | `curl localhost:8000/api/health` returns 200 |
| 2 | Fix any hardcoded DB paths in scripts (especially `generate_weekly_proposal_report.py`) | `grep -r "Desktop.*bensley_master" scripts/` returns empty |
| 3 | Test all finance endpoints | `curl localhost:8000/api/finance/summary` returns data |
| 4 | Test all 27 routers for 500 errors | Automated endpoint sweep, log failures |
| 5 | Verify frontend connects to backend | Pages load without API errors |

### Agent Assignment
**Organizer Agent** - Paths, routing, structure verification

### Definition of Done
All gate criteria pass. No 500 errors on any endpoint.

---

## PHASE B: Data Audit & Baseline

### Prerequisites
- Phase A gate passed

### Tasks

| # | Task | Output |
|---|------|--------|
| 1 | **Email→Proposal Link Audit** | Sample 100 random links, manually verify accuracy, document % correct |
| 2 | **Email→Project Link Audit** | Sample 50 links, verify, document |
| 3 | **Contact Data Quality Audit** | Count nulls, duplicates, malformed emails, document |
| 4 | **Transcript Data Audit** | Inventory all 39 transcripts, check content quality |
| 5 | **Establish Rollback Point** | Create DB backup before any data changes |
| 6 | **Document Baseline Metrics** | Write to LIVE_STATE.md: X% email accuracy, Y contacts with nulls, etc. |

### Sampling Rules
- Email audits: Random sample of 100 (statistically significant)
- If accuracy <70%, flag for full re-processing in Phase D
- Document sampling methodology for reproducibility

### Rollback Rules
- Always backup DB before bulk operations: `cp bensley_master.db bensley_master.db.backup_$(date +%Y%m%d)`
- If audit reveals >50% bad data in a table, plan for full rebuild in Phase D

### Agent Assignment
**Data Audit Agent** (read-only, reports findings)

### Definition of Done
Baseline metrics documented in LIVE_STATE.md. Rollback point created.

---

## PHASE C: Human Feedback Infrastructure

### Prerequisites
- Phase B completed (baseline known)

### Tasks

| # | Task | Details |
|---|------|---------|
| 1 | **Suggestions Approval Workflow** | Complete UI: list → review → approve/reject/correct → save decision |
| 2 | **Bulk Approve High-Confidence** | UI to approve all suggestions ≥0.85 confidence with one click |
| 3 | **Track Decisions with Context** | Store: suggestion_id, decision, reason, reviewer, timestamp |
| 4 | **Schema Migrations** | Add fields: `contact.enrichment_source`, `transcript.suggestion_id`, new suggestion types |
| 5 | **SSOT Update Protocol** | Agents MUST update these files daily: LIVE_STATE.md, COORDINATOR_BRIEFING.md, roadmap.md, context/index.md |

### Required Schema Migrations
```sql
-- Contact enrichment tracking
ALTER TABLE contacts ADD COLUMN enrichment_source TEXT;
ALTER TABLE contacts ADD COLUMN enrichment_date TEXT;

-- Transcript suggestion linking
ALTER TABLE meeting_transcripts ADD COLUMN linked_via_suggestion_id INTEGER;

-- Suggestion types (if not already added)
-- transcript_link, contact_enrichment already added in migration 047
```

### SSOT Update Requirements
After EVERY agent session, update:
1. `.claude/LIVE_STATE.md` - Current metrics, blockers, what changed
2. `.claude/COORDINATOR_BRIEFING.md` - If major changes
3. `docs/roadmap.md` - If sprint items completed
4. `docs/context/index.md` - If files added/changed

### Agent Assignment
**Full-Stack Agent** (backend API + frontend UI for suggestions workflow)

### Definition of Done
- User can review suggestion → approve/reject/correct → decision stored
- SSOT update protocol documented and enforced

---

## PHASE D: Data Quality Improvement

### Prerequisites
- Phase C completed (feedback infrastructure exists)

### Tasks

| # | Task | Method |
|---|------|--------|
| 1 | **Process Email→Proposal Suggestions** | Human reviews via Phase C UI, bulk approve high-confidence |
| 2 | **Process Email→Project Suggestions** | Same |
| 3 | **Link Transcripts via Suggestions ONLY** | Run transcript_linker.py, create suggestions, human reviews each |
| 4 | **Contact Extraction & Enrichment** | Extract new contacts from emails, create suggestions, human verifies |
| 5 | **Transcript Grouping** | Group transcripts by meeting, verify project associations |
| 6 | **Backfill Missing Data** | Fill null contact names, company fields where determinable |

### Critical Rules
- **NEVER auto-link transcripts** - Always via suggestions, human approves
- **NEVER bulk-approve contacts** - Each contact reviewed individually (names matter)
- **Always create backup before bulk operations**

### Metrics to Track (update LIVE_STATE.md)
- Email→Proposal accuracy: Target 95%+
- Email→Project coverage: Target 80%+
- Transcript→Proposal links: Target 100% (all 39 reviewed)
- Contacts verified: Target 100% (all 578 reviewed)

### Agent Assignment
**Data Pipeline Agent** (creates suggestions) + **Human** (reviews)

### Definition of Done
- All transcripts linked (human verified)
- Email accuracy ≥90% (sampled and verified)
- Contact data cleaned (no critical nulls)
- Metrics in LIVE_STATE.md

---

## PHASE E: Basic Intelligence & Reports

### Prerequisites
- Phase D completed (clean, verified data)

### Tasks

| # | Task | Details |
|---|------|---------|
| 1 | **Weekly Proposal Status Report** | Generate PDF/HTML with: proposal list, status, linked email context, transcript summaries |
| 2 | **Fix Report Script DB Path** | Update `generate_weekly_proposal_report.py` to use env var |
| 3 | **Add Email Context to Reports** | Pull last 5 emails per proposal |
| 4 | **Add Transcript Context to Reports** | Pull linked meeting summaries |
| 5 | **Test Report Generation** | Generate sample, verify accuracy |

### Agent Assignment
**Intelligence Agent** (report logic) + **Backend Agent** (API endpoints if needed)

### Definition of Done
- Weekly report generates successfully
- Report includes accurate email/transcript context
- Bill can use it

---

## PHASE F: Polish & Demo

### Prerequisites
- Phase E completed (reports work)

### Tasks

| # | Task | Smoke Test After? |
|---|------|-------------------|
| 1 | **Email/Suggestions Page UI Fixes** | Yes - verify page loads, actions work |
| 2 | **Projects Detail Widgets** | Yes - verify widgets render with data |
| 3 | **Admin Page Consolidation** | Yes - verify admin routes work |
| 4 | **UI Polish** | Visual review |
| 5 | **Performance Check** | Page load <2s |

### Smoke Test Protocol
After each backend fix, run:
```bash
# Quick endpoint test
curl -s localhost:8000/api/health
curl -s localhost:8000/api/proposals/stats
curl -s localhost:8000/api/emails/recent

# Frontend smoke
# Open localhost:3002, verify pages load
```

### Agent Assignment
**Frontend Agent** (UI) + **Smoke tests after each change**

### Definition of Done
- All UI fixes complete
- Demo-ready appearance
- No console errors

---

## TIER 2 NOTE

**RAG / Vector Stores / Local Embeddings** are DELAYED until Phase D is complete.

When Phase D data quality metrics are met:
- Email accuracy ≥90%
- Transcripts 100% linked
- Contacts verified

THEN begin Tier 2 with local embeddings (budget-conscious).

---

## Phase Sequencing Summary

```
PHASE A (Infrastructure) ─── GATE: No 500s, DB path correct
    ↓
PHASE B (Audit) ─── Know baseline truth
    ↓
PHASE C (Feedback Infra) ─── Build mechanism to fix
    ↓
PHASE D (Data Quality) ─── Actually fix the data
    ↓
PHASE E (Reports) ─── Generate value from clean data
    ↓
PHASE F (Polish) ─── Make it beautiful
    ↓
TIER 2 (Intelligence) ─── RAG, embeddings, queries
```

---

## Current State (Update Daily)

| Phase | Status | Notes |
|-------|--------|-------|
| A | ✅ COMPLETE | Infrastructure verified, paths fixed |
| B | ✅ COMPLETE | Audit found 100% orphaned links |
| C | ⏭️ SKIPPED | Built on broken data - jumped to D |
| D | ✅ COMPLETE | Link tables rebuilt (660 proposal, 200 project) |
| E | 🟡 IN PROGRESS | E3 Week 2, E5.1-E5.2 done |
| F | ⏳ NOT STARTED | Waiting on E |

**Last Updated:** 2025-12-01 12:15
**Current Focus:** Phase E3 Week 2 (Handler Integration)

### Phase E Detailed Status

| Section | Description | Status |
|---------|-------------|--------|
| E3 | AI Suggestions Redesign | Week 1 ✅, Week 2 🎯 |
| E4 | Fix Broken Admin Pages | NOT STARTED |
| E1 | Email-Driven Proposal Automation | NOT STARTED |
| E5 | Weekly Report Script | E5.1-E5.2 ✅ |
| E2 | Projects Page Financial Fixes | NOT STARTED |

### E3 Week 2 TODO
- ❌ Refactor _apply_suggestion() to use handlers
- ❌ FeeChangeHandler (149 suggestions)
- ❌ DeadlineHandler (1 suggestion)
- ❌ Preview/rollback/source API endpoints

### What's Done Today (Dec 1)
- ✅ Phase A: Infrastructure verified, 9 paths fixed
- ✅ Phase B: Audit revealed 100% orphaned links
- ✅ Phase D: Both link tables rebuilt with 100% FK integrity
- ✅ E3 Week 1: Handler framework + 3 handlers (FollowUp, Transcript, Contact)
- ✅ E5.1-E5.2: Weekly report generates with email counts (18 proposals, 418 emails)
