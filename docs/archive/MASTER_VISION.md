# Bensley Operating System - Master Vision and Roadmap
Updated: 2026-01-02

This is the single source of truth for what we are building, why, and in what order.
All other docs are supporting references and must align to this document.

## Goal
One platform that runs Bensley Design Studios end-to-end: win work, do work, get paid.

## Operating Modes
1) Track: see what is happening right now.
2) Assist: AI drafts, suggests, and alerts for review.
3) Automate: AI executes with explicit human approval.

## Domain Map
Core:
- Win Work (proposals, follow-ups, contracts, meetings)
- Do Work (projects, scheduling, RFIs, submissions, daily work)
- Get Paid (invoicing, payments, aging, forecasting)

Support:
- Social/Brand (content, captions, scheduling, analytics)
- Analytics/BI (cross-domain insights, trends, alerts)
- Knowledge (design archive, meeting memory, best practices)

AI Layer:
- Domain agents per core/support domain
- Human-in-the-loop approvals and audit trails

## Users and Outcomes
- Executive (Bill): pipeline status, cash position, approvals, alerts.
- PMs: project status, RFIs, schedules, client comms.
- Staff: daily work logging, submissions, internal updates.
- Finance: invoice tracking, payments, aging, reminders.

## Principles
- Human-in-the-loop: no silent automation on external communications.
- One source of truth: all status and decisions live in the database.
- Everything is linked to project + client + people + timeline.
- Auditability: changes and AI suggestions are always traceable.
- Minimal manual entry: ingest from email, docs, and transcripts first.
- Security-first: auth on all endpoints, least privilege roles.

## Current State (Jan 2026)
- Backend: FastAPI with core endpoints for proposals, projects, email, finance.
- Frontend: Next.js dashboard with proposal tracker and analytics.
- Email: import + categorization + pattern learning.
- Documents: OneDrive upload integration (local fallback).
- Meetings: transcription pipeline exists but is not yet end-to-end.

## Roadmap and Milestones

### Phase 1: Foundation (Q1 2026)
Must deliver:
- Security fixes (auth on all endpoints, RBAC, secret management).
- Email linking to 80%+ accuracy with review queue.
- Invoice tracking complete (aging, payments, reminders).
- Weekly proposal report automation.

Success metrics:
- Bill answers "what needs attention?" in under 30 seconds.
- New emails auto-link within 5 minutes.
- Outstanding invoices visible instantly.

### Phase 2: Operations (Q2 2026)
Must deliver:
- Project management redesign (timeline, phase tracking).
- RFI tracking (deadlines, owner, response log).
- Daily work logging + review workflow.
- PM assignment tracking.
- Executive dashboard across all domains.

Success metrics:
- Zero RFIs older than 5 days without response.
- PMs actively use project views.

### Phase 3: Intelligence (Q3 2026)
Must deliver:
- Draft follow-ups and reminders with approval workflow.
- Document indexing and search.
- Meeting transcripts linked to projects with summaries.
- Proactive alerts and exception monitoring.

Success metrics:
- Draft approval rate >80%.
- Meeting context searchable within minutes of upload.

### Phase 4: Content and Social (Q4 2026)
Must deliver:
- Bill's content hub and content calendar.
- Social analytics and scheduling.
- Draft caption generation with approvals.

### Phase 5: AI Layer (2027)
Must deliver:
- Local model hosting (Ollama) for sensitive workflows.
- Domain agents with explicit approval gates.
- Fine-tuned Bensley Brain models on internal data.

## Core Entities (System of Record)
- Proposals, Projects, Clients, Contacts
- Emails, Meetings, Transcripts
- RFIs, Tasks, Submissions
- Invoices, Payments, Forecasts
- Documents, Deliverables, Status History

## Non-Goals (For Now)
- Full accounting replacement (use existing accounting system).
- Generic HR/payroll/benefits.
- Public client portal (revisit after core ops stability).

## Open Decisions
- Accounting integration target (QuickBooks, Xero, other).
- Calendar integration (Google vs Microsoft).
- Timeline for SQLite to PostgreSQL migration.
- Standard taxonomy for tags, phases, and disciplines.

## Doc Governance
- Update this file first for any changes in scope or priorities.
- Supporting docs are references only and must link back here.
