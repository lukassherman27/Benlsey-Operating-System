# Architecture Context Bundle

**Owner:** Brain/Organizer Agent
**Last Updated:** 2025-11-27
**Full Document:** `docs/architecture/COMPLETE_ARCHITECTURE_ASSESSMENT.md`

---

## Quick Summary

BDS Operations Platform: AI-powered business ops for Bensley Design Studios
- **Progress:** ~50% complete (up from 40% on Nov 19)
- **Phase:** 1.5 - Integration & Data Quality
- **Launch Target:** Jan 15, 2026

---

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        EXTERNAL SOURCES                          │
│   Email (IMAP) ✅  │  Calendar ❌  │  Meetings ❌  │  OneDrive ✅  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      INGESTION LAYER                             │
│  Email Processor ✅  │  PDF Parser ✅  │  Contract AI ✅  │        │
│  Meeting Transcriber ❌  │  Calendar Sync ❌                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER                              │
│                 SQLite (107MB, 115 tables)                       │
│  ┌────────────┐ ┌────────────────┐ ┌─────────────────┐          │
│  │ Operational│ │ Relationship   │ │ Intelligence    │          │
│  │ (90%)      │ │ (100%)         │ │ (85%)           │          │
│  │ projects   │ │ email_project_ │ │ ai_suggestions  │          │
│  │ proposals  │ │ links          │ │ training_data   │          │
│  │ invoices   │ │ project_contact│ │ learned_patterns│          │
│  │ contracts  │ │ _links         │ │                 │          │
│  └────────────┘ └────────────────┘ └─────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API LAYER                                 │
│              FastAPI: 93+ endpoints (exceeds vision!)            │
│                                                                  │
│  PROBLEM: 14 services NOT connected, 20 scripts CLI-only        │
│  See: docs/ALIGNMENT_AUDIT_REPORT.md                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND LAYER                              │
│               Next.js 15 @ localhost:3002                        │
│                                                                  │
│  PROBLEM: Only ~40% of APIs have UI                             │
│  Missing: Calendar, Transcripts, Contracts, RFIs, Admin         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI INTELLIGENCE (Phase 2)                     │
│   Local LLM ❌  │  RAG/Vectors ❌  │  Claude API ✅ (20% usage)   │
│   Target: 80% local, 20% cloud by Phase 4                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Critical Integration Gap (Nov 27 Audit)

```
| Issue                             | Count        |
|-----------------------------------|--------------|
| Orphaned Backend Services         | 14 files     |
| Backend APIs with No Frontend     | 15+ features |
| CLI-Only Scripts (not integrated) | 20 scripts   |
| Duplicate Endpoints               | 6 areas      |
```

**Root Cause:** Agents built features independently without integration.
**Fix:** Connect orphaned services before building new features.

---

## Tech Decisions

| Decision | Current | Rationale | Change When |
|----------|---------|-----------|-------------|
| Database | SQLite | Simple, <1GB | 10GB or concurrent writes |
| AI | Claude API | Works, ~$100/mo | >$200/mo or need speed |
| LLM | Cloud only | Phase 1 focus | Phase 4 (local Llama) |
| RAG | None | Defer complexity | Phase 4 (ChromaDB) |
| Deploy | Local dev | Not ready | Jan 15 (Vercel + Railway) |

---

## Schema Quick Reference

### Operational (90% complete)
- `projects`, `proposals`, `clients`, `contracts`
- `invoices`, `rfis`, `deliverables`, `milestones`
- Missing: `employees` table

### Relationship (100% complete)
- `email_project_links`, `email_proposal_links`
- `project_contact_links`, `project_documents`
- `document_proposal_links`, `client_aliases`

### Intelligence (85% complete)
- `ai_suggestions`, `training_data`, `learned_patterns`
- `audit_log`, `change_log`, `data_quality_tracking`
- Missing: `automations`, `notifications`

---

## Phase Roadmap

| Phase | Timeline | Focus | Status |
|-------|----------|-------|--------|
| 1.0 | Complete | Data foundation | Done |
| 1.5 | Now - Dec 15 | Integration + Quality | In Progress |
| 2.0 | Dec - Jan 15 | Intelligence Layer | Not Started |
| 3.0 | Jan - Feb | Multi-user + Production | Not Started |
| 4.0 | Feb - May | Local AI + RAG | Not Started |

---

## Agent Integration (2 of 8 built)

- [x] Email Categorizer Agent
- [x] Contract Analyzer Agent
- [ ] Proposal Follow-up Agent
- [ ] RFI Tracker Agent
- [ ] Invoice Collector Agent
- [ ] Schedule Monitor Agent
- [ ] Meeting Summarizer Agent
- [ ] Project Intelligence Agent

---

## Key Files

| Purpose | File |
|---------|------|
| Full architecture | `docs/architecture/COMPLETE_ARCHITECTURE_ASSESSMENT.md` |
| API endpoints | `backend/api/main.py` (10K+ lines) |
| Database | `database/bensley_master.db` |
| Migrations | `database/migrations/*.sql` (70 files) |
| Alignment audit | `docs/ALIGNMENT_AUDIT_REPORT.md` |

---

## Queries This Context Answers

- "What's the overall system architecture?"
- "How complete is the system?"
- "What databases/tables exist?"
- "What's the tech stack?"
- "What's missing/not built?"
- "What phase are we in?"
