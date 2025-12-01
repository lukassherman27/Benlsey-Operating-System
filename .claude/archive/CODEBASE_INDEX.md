# Codebase Index

**Auto-maintained by Organizer Agent | Last updated: 2025-11-26**

Quick lookup for where things live. Use Ctrl+F to find what you need.

---

## By Feature

### Proposals (Sales Pipeline)
- **API:** `backend/api/main.py` (search "proposals")
- **Service:** `backend/services/proposal_service.py`, `proposal_tracker_service.py`
- **Frontend Page:** `frontend/src/app/(dashboard)/tracker/page.tsx`
- **Components:** `frontend/src/components/proposals/`
- **Database:** `proposals`, `proposal_tracker`, `proposal_status_history`

### Projects (Active Contracts)
- **API:** `backend/api/main.py` (search "projects")
- **Service:** `backend/services/project_creator.py`
- **Frontend Page:** `frontend/src/app/(dashboard)/projects/page.tsx`
- **Components:** `frontend/src/components/dashboard/active-projects-*.tsx`
- **Database:** `projects`, `project_milestones`, `project_fee_breakdown`

### Invoices & Finance
- **API:** `backend/api/main.py` (search "invoices", "finance")
- **Service:** `backend/services/financial_service.py`, `invoice_service.py`
- **Components:** `frontend/src/components/dashboard/invoice-*.tsx`
- **Database:** `invoices`, `payments`

### Emails
- **API:** `backend/api/main.py` (search "emails")
- **Service:** `backend/services/email_service.py`, `email_content_processor*.py`
- **Importer:** `backend/services/email_importer.py`
- **Frontend:** `frontend/src/components/emails/`
- **Database:** `emails`, `email_project_links`, `email_proposal_links`

### RFIs
- **API:** `backend/api/main.py` (search "rfis")
- **Service:** `backend/services/rfi_service.py`
- **Detector:** `scripts/core/rfi_detector.py`
- **Database:** `rfis`
- **API Endpoints:**
  - `GET /api/rfis` - List with filters: `project_code`, `status`, `overdue_only`, `limit`

### Meeting Transcripts (NEW - Nov 26)
- **API:** `backend/api/main.py` (search "meeting-transcripts")
- **Database:** `meeting_transcripts`
- **API Endpoints:**
  - `GET /api/meeting-transcripts` - List transcripts with `project_code` filter
  - `GET /api/meeting-transcripts/{id}` - Get single transcript with full details
  - `GET /api/meeting-transcripts/{id}/action-items` - Get action items from transcript

### Unified Timeline (NEW - Nov 26)
- **API:** `backend/api/main.py` (search "unified-timeline")
- **API Endpoints:**
  - `GET /api/projects/{code}/unified-timeline` - Combined view of emails, meetings, RFIs, invoices, milestones for a project
  - Supports `types` filter: `email,meeting,rfi,invoice,milestone`

### Contracts
- **Service:** `backend/services/contract_service.py`
- **Parser:** `scripts/core/parse_contracts.py` (Claude AI)
- **Database:** `contract_metadata`, `contract_phases`, `contract_terms`

### Documents
- **Service:** `backend/services/document_service.py`
- **Database:** `documents`, `project_documents`, `document_intelligence`

### Query/Search
- **API:** `backend/api/main.py` (search "query")
- **Service:** `backend/services/query_service.py`
- **Brain:** `scripts/core/query_brain.py`
- **Frontend:** `frontend/src/components/query-interface.tsx`

### Intelligence & Learning (NEW - Nov 26)
- **Learning Service:** `backend/services/ai_learning_service.py`
- **Follow-up Agent:** `backend/services/follow_up_agent.py`
- **Proposal Intelligence:** `backend/services/proposal_intelligence_service.py`
- **Frontend Admin:** `frontend/src/app/(dashboard)/admin/intelligence/page.tsx`
- **Database:** `learned_patterns`, `ai_suggestions_queue`, `training_data`
- **API Endpoints:**
  - `/api/learning/*` - Rule generation, pattern validation
  - `/api/agent/follow-up/*` - Proposal follow-up agent
  - `/api/query/ask-enhanced` - Pattern-enhanced queries

---

## By Agent (January 2026 Plan)

| Agent | Focus | Files Owned | Prompt |
|-------|-------|-------------|--------|
| **Agent 1** | Backend API | `backend/` | `.claude/agents/agent1-backend-api.md` |
| **Agent 2** | Frontend | `frontend/src/` | `.claude/agents/agent2-frontend.md` |
| **Agent 3** | Deployment | configs, CI/CD | `.claude/agents/agent3-deployment.md` |
| **Agent 4** | Data Pipeline | `scripts/`, `voice_transcriber/` | `.claude/agents/agent4-data-pipeline.md` |
| **Agent 5** | Intelligence | `query_brain.py`, AI services | `.claude/agents/agent5-intelligence.md` |
| **Organizer** | File structure | All (read), archives | `.claude/agents/organizer.md` |

**Master Plan:** `docs/planning/MASTER_JANUARY_PLAN.md`

---

## By File Type

### Python Scripts
| Location | Purpose |
|----------|---------|
| `scripts/core/` | Active production scripts |
| `scripts/analysis/` | Audit & analysis |
| `scripts/maintenance/` | Fixes & upkeep |
| `scripts/imports/` | Data imports |
| `scripts/archive/` | Deprecated |

### Markdown Docs
| Location | Purpose |
|----------|---------|
| `docs/architecture/` | System design |
| `docs/guides/` | How-to guides |
| `docs/sessions/` | Session notes |
| `docs/planning/` | Plans & roadmaps |
| `docs/archive/` | Old docs |

### Database
| File | Purpose |
|------|---------|
| `database/bensley_master.db` | THE database |
| `database/migrations/*.sql` | Schema migrations |
| `database/SCHEMA.md` | Schema documentation |
| `database/backups/` | Backup files |

---

## Search Patterns

```bash
# Find where a function is defined
grep -r "def function_name" backend/

# Find API endpoint
grep -r "@app.get\|@app.post" backend/api/main.py | grep "keyword"

# Find React component usage
grep -r "ComponentName" frontend/src/

# Find database table usage
grep -r "FROM table_name\|INTO table_name" backend/

# Find imports of a module
grep -r "from backend.services.module import\|import module" .
```

---

## Health Commands

```bash
make health-check    # Run full health check
make test           # Run tests
make lint           # Check code style
make db-stats       # Show database counts
make db-schema      # Show table list
```

---

## Recently Modified (Check Git)

```bash
git log --oneline -20                    # Last 20 commits
git diff --name-only HEAD~5              # Files changed in last 5 commits
git log --since="1 week ago" --oneline   # Last week's commits
```
