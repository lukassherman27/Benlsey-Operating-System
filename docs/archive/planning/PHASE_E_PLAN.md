# Phase E Plan - Dec 2025

**Created:** 2025-12-01
**Updated:** 2025-12-01
**Goal:** Weekly proposal reports for Bill with email/transcript context

---

## MASTER PLAN OVERVIEW

| Section | Description | Detailed Plan | Status |
|---------|-------------|---------------|--------|
| E1 | Email-Driven Proposal Automation | This file | NOT STARTED |
| E2 | Projects Page Financial Fixes | This file | NOT STARTED |
| **E3** | **AI Suggestions Redesign** | **See: `~/.claude/plans/tingly-juggling-nova.md`** | **PLANNED** |
| E4 | Fix Broken Admin Pages | This file | NOT STARTED |
| E5 | Weekly Report Script | This file | NOT STARTED |

**Recommended Order:** E3 → E4 → E1 → E5 → E2

---

---

## Phase Status

| Phase | Status | Notes |
|-------|--------|-------|
| A - Infrastructure | ✅ COMPLETE | Fixed paths, tested routers |
| B - Data Audit | ✅ COMPLETE | Found 100% orphaned links |
| C - Feedback System | ✅ COMPLETE | Already existed, verified working |
| D - Data Rebuild | ✅ COMPLETE | 660 proposal links, 200 project links |
| **E - Intelligence & Reports** | 🎯 CURRENT | This plan |
| F - Polish | ⏳ WAITING | After E |

---

## Phase E Structure

### E1: Email-Driven Proposal Automation (P0)
**Goal:** Proposal status updates automatically from email activity

| Task | Details | Effort |
|------|---------|--------|
| E1.1 | Parse IMAP Sent folder for proposal emails | M |
| E1.2 | Auto-detect "proposal sent" → update status | M |
| E1.3 | Store email as evidence for status change | S |
| E1.4 | Fix status timeline component (not loading) | S |
| E1.5 | Show context: WHY status is what it is | M |
| E1.6 | Display risks, contacts, important dates | M |
| E1.7 | Win probability field (manual or calculated) | S |

**Acceptance:** When I send a proposal email, the system detects it and updates status with context.

---

### E2: Projects Page Financial Fixes (P1)
**Goal:** Clear financial picture per project

| Task | Details | Effort |
|------|---------|--------|
| E2.1 | Top 5 widgets: show names not codes | S |
| E2.2 | Fix "0% invoice" broken widget | S |
| E2.3 | Financial summary: Contract → Invoiced → Paid → Outstanding → Remaining | M |
| E2.4 | Multi-segment progress bar (invoiced/paid/remaining) | M |
| E2.5 | Collapse invoice details by default | S |
| E2.6 | Fee breakdown: group by SCOPE for multi-venue projects (like Wynn) | M |
| E2.7 | Phase order: Mob → Concept → DD → CD → CO | S |
| E2.8 | Dedupe fee breakdown data (Wynn has duplicates) | S |

**Acceptance:** Opening a project shows clear financial status at a glance, with scope-based breakdown for complex projects.

---

### E3: AI Suggestions Clarity (P2)
**Goal:** Understand what each suggestion will do

| Task | Details | Effort |
|------|---------|--------|
| E3.1 | Show source email snippet that triggered suggestion | M |
| E3.2 | Show "This will add X to database" explanation | S |
| E3.3 | Show affected proposal/project with link | S |
| E3.4 | Preview diff before approve | M |
| E3.5 | Link transcripts to proposals via suggestion workflow | M |

**Acceptance:** Each suggestion shows: source email, what it will change, preview of change.

---

### E4: Fix Broken Pages (P3)
**Goal:** No 404s, no confusion

| Task | Details | Effort |
|------|---------|--------|
| E4.1 | Remove `/admin/intelligence` from sidebar (or create page) | S |
| E4.2 | Remove `/admin/audit` from sidebar (or create page) | S |
| E4.3 | Consolidate admin navigation (two menus is confusing) | S |
| E4.4 | Fix `/proposals` listing page (currently 404) | M |

**Acceptance:** All sidebar links work, no 404s.

---

### E5: Weekly Report Script (P1)
**Goal:** Generate PDF report for Bill

| Task | Details | Effort |
|------|---------|--------|
| E5.1 | Fix PosixPath bug in script | S |
| E5.2 | Add email context to report (recent emails per proposal) | M |
| E5.3 | Add transcript context (meeting notes) | M |
| E5.4 | Add contact info per proposal | S |
| E5.5 | Show status timeline in report | M |

**Acceptance:** `python scripts/core/generate_weekly_proposal_report.py` produces PDF with email/transcript context.

---

## Effort Key

- **S** = Small (< 2 hours)
- **M** = Medium (2-4 hours)
- **L** = Large (4+ hours)

---

## Suggested Execution Order

```
Week 1 (Dec 2-8):
  - E1.1-E1.4: Email detection + status timeline fix
  - E4.1-E4.3: Fix broken admin pages
  - E5.1: Fix report script bug

Week 2 (Dec 9-15):
  - E1.5-E1.7: Proposal context enrichment
  - E2.1-E2.5: Projects financial fixes
  - E5.2-E5.5: Report enrichment

Week 3 (Dec 16-22):
  - E2.6-E2.8: Scope-based fee breakdown
  - E3.1-E3.5: Suggestions clarity
  - E4.4: Proposals listing page
```

---

## Questions to Resolve

1. **Win probability:** Manual entry or calculated? If calculated, what formula?

2. **Email status detection:** Should this be:
   - Automatic (just happens)
   - Create suggestion for approval
   - Hybrid (high confidence = auto, low = suggestion)

3. **Broken admin pages:** Remove links or create placeholder pages?

4. **Contacts page purpose:** Keep, redesign, or remove?

---

## Data Dependencies

| Task | Requires |
|------|----------|
| E1.x | IMAP credentials configured |
| E3.5 | 38 unlinked transcripts |
| E5.x | email_proposal_links (660 links ready) |

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Proposals with email links | 24/87 (28%) | 60/87 (70%) |
| Transcripts linked | 1/39 (3%) | 30/39 (77%) |
| Weekly report generation | Broken | Working |
| Admin 404 pages | 2 | 0 |

---

## Files Likely to Change

```
# Backend
backend/services/email_importer.py (E1.1-E1.3)
backend/services/proposal_service.py (E1.4-E1.7)
backend/api/routers/projects.py (E2.x)
scripts/core/generate_weekly_proposal_report.py (E5.x)

# Frontend
frontend/src/app/(dashboard)/proposals/[projectCode]/page.tsx (E1.4-E1.7)
frontend/src/app/(dashboard)/projects/[projectCode]/page.tsx (E2.x)
frontend/src/app/(dashboard)/admin/suggestions/page.tsx (E3.x)
frontend/src/app/(dashboard)/admin/layout.tsx (E4.1-E4.3)
```

---

**Ready for execution upon approval.**
