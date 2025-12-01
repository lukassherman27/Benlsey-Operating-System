# Agent Registry - Single Source of Truth

**Owner:** Organizer Agent
**Last Updated:** 2025-11-27

---

## Active Agents

### Brain/Planner Agent
**Purpose:** Strategic direction, roadmap ownership, scope gating
**Inputs:** All planning docs, metrics, blockers
**Outputs:** Updated `docs/roadmap.md`, sprint priorities
**Key Files:**
- `docs/roadmap.md` (owns)
- `2_MONTH_MVP_PLAN.md` (reads)
- `docs/architecture/COMPLETE_ARCHITECTURE_ASSESSMENT.md` (reads)
**Run:** Weekly planning session, ad-hoc for scope decisions
**Definition of Done:** Roadmap updated with clear sprint goals

---

### Organizer/Indexer Agent
**Purpose:** Maintain file maps, context packs, prevent drift
**Inputs:** Git diffs, file changes, agent handoffs
**Outputs:** Updated indexes, context bundles, file routing
**Key Files:**
- `docs/agents/registry.md` (owns)
- `docs/context/index.md` (owns)
- `.claude/CODEBASE_INDEX.md` (owns)
**Run:** After every PR/merge, after significant changes
**Definition of Done:** All indexes reflect current state

---

### Backend Builder Agent
**Purpose:** FastAPI endpoints, services, database
**Inputs:** Task packs from Organizer, context bundles
**Outputs:** Working API code, migrations, tests
**Key Files:**
- `backend/api/main.py`
- `backend/services/*.py`
- `database/migrations/*.sql`
**Run:** Per task assignment
**Commands:**
```bash
cd backend && uvicorn api.main:app --reload --port 8000
pytest tests/ -v
```
**Definition of Done:** Endpoints work, tests pass, handoff written

---

### Frontend Builder Agent
**Purpose:** React/Next.js UI, dashboard pages
**Inputs:** Task packs, API documentation, design specs
**Outputs:** Working UI components and pages
**Key Files:**
- `frontend/src/app/(dashboard)/*.tsx`
- `frontend/src/components/**/*.tsx`
- `frontend/src/lib/api.ts`
**Run:** Per task assignment
**Commands:**
```bash
cd frontend && npm run dev
cd frontend && npm run build
cd frontend && npm run lint
```
**Definition of Done:** UI works, connects to API, no type errors

---

### Data Pipeline Agent
**Purpose:** Imports, scripts, email processing, data quality
**Inputs:** Task packs, data sources, quality metrics
**Outputs:** Clean data in database, processing scripts
**Key Files:**
- `scripts/core/*.py`
- `backend/core/*.py`
- `database/bensley_master.db`
**Run:** Per task, scheduled jobs
**Commands:**
```bash
python scripts/core/smart_email_brain.py
python scripts/core/email_linker.py
make health-check
```
**Definition of Done:** Data imported, validated, metrics improved

---

### Intelligence Agent
**Purpose:** AI features, queries, learning, RAG prep
**Inputs:** Task packs, training data, user feedback
**Outputs:** AI endpoints, query improvements, learning data
**Key Files:**
- `backend/services/query_service.py`
- `backend/services/intelligence_service.py`
- `backend/core/bensley_brain.py`
**Run:** Per task
**Commands:**
```bash
python scripts/core/query_brain.py --test
```
**Definition of Done:** AI features work, accuracy measured

---

### QA/Reviewer Agent
**Purpose:** Integration checks, test coverage, drift detection
**Inputs:** PRs, code changes, task packs
**Outputs:** Review comments, test reports, alignment checks
**Key Files:**
- `tests/*.py`
- `.github/workflows/ci.yml`
**Run:** Every PR, weekly integration audit
**Commands:**
```bash
make check
pytest tests/ --cov
python scripts/analysis/audit_complete_database.py
```
**Definition of Done:** All checks pass, no integration drift

---

### Ops/Runbook Agent
**Purpose:** Git hygiene, deployment, env management, backups
**Inputs:** Deployment needs, env changes, runbook gaps
**Outputs:** Updated runbooks, deployment scripts, env configs
**Key Files:**
- `docs/processes/runbooks.md` (owns)
- `Makefile`
- `.env.example`
- `docker-compose.yml`
**Run:** Per deployment, weekly maintenance
**Definition of Done:** Deployment succeeds, runbooks current

---

## Agent Contract Template

```markdown
# Agent: [Name]

**Purpose:** [One sentence]

**Inputs/Context to read:**
- [File or context bundle]

**Key files to edit:**
- [Specific files this agent touches]

**Commands:**
- [Shell commands to run/test]

**Definition of done:**
- [Concrete acceptance criteria]

**Handoff note required:** Yes/No
```

---

## Communication Protocol

### Before Starting Work
1. Read `docs/roadmap.md` for current priorities
2. Get task pack from Organizer
3. Read relevant context bundles
4. Check for blockers

### After Completing Work
1. Write handoff note in task pack
2. Notify Organizer of file changes
3. Update `docs/roadmap.md` if completing sprint item
4. Commit with structured message

### Commit Message Format
```
[type](agent-name): Brief description

- Detail 1
- Detail 2

Affects: [context bundles affected]
Unblocks: [what this enables]
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`
