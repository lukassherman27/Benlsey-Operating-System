# 🧠 Bensley Brain — Master Plan (Updated 16 Nov 2025)

## Executive Snapshot

| Layer | Status | Highlights |
| --- | --- | --- |
| Data Foundation | ✅ Phase 1 complete | Clean SQLite schema, proposal/email/document imports, health scoring |
| Service/API Layer | ✅ Phase 2 (core) | FastAPI v1 live with proposals, timelines, briefing, decision tiles, overrides, intel queue |
| Frontend | ✅ Daily Briefing UI live | Next.js 16 + Tailwind + shadcn; Apple-style dashboard, intelligence inbox |
| Intelligence | ✅ Ops suggestions, 🚧 Comprehensive audit | `/api/intel/*` endpoints running; Phase 2 audit/learning system in build |
| Automation | 🚧 Manual overrides + MCP coordination | Manual override workflow wired; MCP-based multi-agent coordination active |

---

## Phase 1 — Data Foundation (✅ DONE)

- **Database**: 12 migrations, canonical schema exported to `database/schema/bensley_master_schema.sql`, schema_migrations ledger active.
- **Data Loaded**: 87 proposals, 774 categorized emails, 852 documents, manual overrides table, health metrics populated for 39 active projects.
- **Scripts**: `proposal_health_monitor.py`, `smart_email_matcher.py`, `document_indexer.py`, and full ingestion scripts standardized.
- **Reproducibility**: `setup.sh`, `setup_daily_cron.sh`, and init scripts updated to build the real schema with no fake data.

**Artifacts to keep current**
- `database/schema/` (canonical DDL)
- `SESSION_LOGS.md` (per-session work summary)
- `SYSTEM_AUDIT_YYYY-MM-DD.md` (daily integrity checks)

---

## Phase 2 — Live Services & Executive UX (✅ CORE, 🚧 Audit expansion)

### Backend (Claude)
- **FastAPI** (`backend/api/main.py`)
  - `/api/proposals`, CRUD, health, top-value, recent-activity
  - `/api/proposals/by-code/{code}/timeline`, `/emails/timeline`, `/emails/summary`, `/contacts`, `/attachments`
  - `/api/dashboard/decision-tiles`, `/api/dashboard/stats`
  - `/api/proposals/by-code/{code}/briefing` (pre-meeting)
  - `/api/briefing/daily` (executive feed)
  - `/api/manual-overrides` (create/apply)
  - `/api/intel/suggestions`, `/api/intel/patterns`, `/api/intel/suggestions/{id}/decision`, `/api/intel/decisions`, `/api/intel/training-data`
- **Services**: `backend/services/override_service.py`, `intelligence_service.py`, `proposal_service.py`, etc.

### Frontend (Codex)
- Next.js 16 + Tailwind + shadcn UI.
- `/` renders Daily Briefing dashboard:
  - Hero metrics (business health, revenue, meeting schedule).
  - Urgent / Needs Attention feeds using `/api/briefing/daily`.
  - Revenue snapshot pulling `/api/dashboard/stats`.
  - Query Brain modal (NL queries).
  - Manual overrides + Provide Context modal (hooks into `/api/manual-overrides`).
  - **Intelligence Inbox**: grouped suggestion cards, evidence modal, approve/snooze wired to `/api/intel/suggestions/...`.

### Coordination
- MCP filesystem sharing enabled; both Claude and Codex respond via `AI_DIALOGUE.md` and log in `SESSION_LOGS.md`.
- Manual overrides capture operator instructions with `NEXT_PUBLIC_OVERRIDE_AUTHOR`.

---

## Phase 2B — Comprehensive Audit & Learning System (🚧 IN BUILD)

### Goals
1. **Scope Verification** — disciplines (landscape/interiors/architecture) and fee allocation.
2. **Fee Breakdown by Phase** — mobilization → CA, with payment status.
3. **Timeline Tracking** — expected vs actual durations, presentation schedules.
4. **Contract Intelligence** — contract terms, payment schedules, invoice linkage.
5. **Continuous Learning** — Q&A workflows, user feedback stored, audit rules auto-improve.

### Database Expansion (planned migrations)
1. `project_scope`
2. `project_fee_breakdown`
3. `project_phase_timeline`
4. `contract_terms`
5. `user_context`
6. `audit_rules`

> Reference: `COMPREHENSIVE_AUDIT_SYSTEM_PLAN.md`

### Upcoming APIs
- `/api/projects/{code}/scope` (GET/POST)
- `/api/projects/{code}/fee-breakdown`
- `/api/projects/{code}/timeline`
- `/api/projects/{code}/contract`
- `/api/audit/scope-suggestions`, `/fee-suggestions`, `/timeline-suggestions`
- `/api/audit/feedback`, `/api/audit/re-audit/{code}`, `/api/audit/learning-stats`

### Frontend Deliverables (Codex)
1. **Audit Review Center** — grouped Q&A cards with Accept / Modify / Provide Context, reusing the suggestion component patterns.
2. **Fee Breakdown Manager** — editable table + chart, totals validation, ties to invoices.
3. **Phase Timeline Tracker** — timeline cards, delay alerts, expected vs actual.
4. **Learning Console** — stats from `audit_rules` + `user_context`, show auto-apply thresholds and recent decisions.

---

## Phase 3 — Advanced Queries & Analytics (Next)

| Capability | Status |
| --- | --- |
| Natural language queries (`POST /api/query`) | ✅ (query_brain.py live) |
| Proposal analytics endpoints | ✅ (dashboard stats/briefing) |
| Contact/relationship insights | 🚧 (depends on new tables) |
| Financial dashboards (forecast, cashflow) | 🚧 (needs finance ingestion) |
| Alerting / notifications | 🚧 |

Remaining work:
- Expand query_brain to use new audit tables (scope/fee/timeline).
- Build analytic widgets (cashflow forecast, unpaid breakdown, schedule view) once data exists.
- Introduce `/api/analytics/dashboard` v2 (with revenue vs cost trends, calendar data).

---

## Phase 4 — Automation & Agentic Workflows (Future)

- n8n / orchestration for:
  - Email ingestion → classification → auto-linking.
  - Scheduled audits (nightly) with alerts via Slack/email.
  - Auto-generated briefings before meetings.
  - Auto-reminders for invoices, RFIs, timeline slips.
- Agent actions: manual overrides currently log instructions; future steps include direct API-driven updates (with approval flows) from the AI assistants.

---

## Source of Truth Files

| Purpose | Path |
| --- | --- |
| Coordination & backlog | `AI_DIALOGUE.md`, `SESSION_LOGS.md`, `CODEX_TASKS.md` |
| Backend integration contract | `INTEGRATION_GUIDE.md`, `COMPREHENSIVE_AUDIT_SYSTEM_PLAN.md` |
| Frontend specs | `docs/dashboard/API_PHASE1_IMPLEMENTED.md`, `docs/dashboard/WIREFRAMES.md`, etc. |
| Master plan | `BENSLEY_BRAIN_MASTER_PLAN.md` (this file) |

Keep these synchronized whenever major functionality changes to avoid context drift between Claude and Codex.
