# WAVE 1 - Backend Stability

Run these in PARALLEL (no dependencies between them).

---

## Agent 1A: Schema + Sort Fixes (#379, #359)

```
You are a Builder Agent for the Bensley Operating System.

## Assignment
- Issues: #379, #359
- Branch: fix/schema-sort-379-359

## Setup
Launch via: ./launch_agent.sh claude 379
This creates your worktree and sets the branch automatically.

## MANDATORY WORKFLOW

### 1. AUDIT (10 min)
Read these files:
- CLAUDE.md
- AGENTS.md
- database/SCHEMA.md (canonical schema reference)
- backend/services/proposal_service.py

If live DB available (BENSLEY_DB_PATH set):
```bash
sqlite3 "$BENSLEY_DB_PATH" ".schema proposals" | rg -E "project_title|project_name"
```

If DB not available, use SCHEMA.md as source of truth.

Find mismatches:
```bash
rg -n "project_title" backend/ frontend/
```

Post findings:
gh issue comment 379 --body "AUDIT: Database uses [column]. Found X mismatched references in [files]"

### 2. PLAN (5 min)
gh issue comment 379 --body "PLAN: Update files [list] to use correct column name [name]"

### 3. IMPLEMENT

For #379 (Schema):
- Update all files to use correct column name (project_name per SCHEMA.md)

For #359 (DB Path):
```bash
rg -n "DATABASE_PATH|DB_PATH" backend/
```
- Standardize to BENSLEY_DB_PATH (this is what the codebase uses - 82+ files)
- Update backend/api/dependencies.py and any outliers

```bash
git commit -m "fix(schema): standardize project_name column #379"
git commit -m "fix(config): standardize BENSLEY_DB_PATH env var #359"
```

### 4. VERIFY
```bash
cd backend
python -c "from services.proposal_service import ProposalService; print('OK')"
uvicorn api.main:app --reload --port 8000
curl http://localhost:8000/api/proposals/?sort_by=project_name
```

### 5. DOCUMENT
```bash
git push -u origin fix/schema-sort-379-359
gh pr create --title "fix(schema): standardize project_name and DB path #379 #359" \
  --body "Fixes #379 and #359. All references updated."
gh issue close 379 --comment "Fixed in PR. All references now use project_name"
gh issue close 359 --comment "Fixed in PR. DB path standardized to BENSLEY_DB_PATH"
```
```

---

## Agent 1B: Service Logic Bugs (#382)

```
You are a Builder Agent for the Bensley Operating System.

## Assignment
- Issue: #382
- Branch: fix/service-bugs-382

## Setup
Launch via: ./launch_agent.sh claude 382
This creates your worktree and sets the branch automatically.

## MANDATORY WORKFLOW

### 1. AUDIT (10 min)
Read these files:
- CLAUDE.md
- AGENTS.md
- backend/services/proposal_service.py
- database/SCHEMA.md (check table existence)

Bugs to find:
1. get_unhealthy_proposals() - Line ~286: WHERE is_active_project = 1 (may be wrong filter)
2. get_proposal_timeline() - Lines ~330-342: References document_proposal_links table
3. Unused imports in proposals.py - Lines 32-33

Check if table exists in SCHEMA.md or live DB:
```bash
rg "document_proposal_links" database/SCHEMA.md
# Or if DB available:
sqlite3 "$BENSLEY_DB_PATH" ".tables" | rg document
```

Post findings:
gh issue comment 382 --body "AUDIT: Found 3 bugs: [details]"

### 2. PLAN (5 min)
gh issue comment 382 --body "PLAN: Fix filter logic, handle missing table, remove unused imports"

### 3. IMPLEMENT
- Fix filter logic in get_unhealthy_proposals()
- Handle missing document_proposal_links table (create or remove dead code)
- Remove unused imports

```bash
git commit -m "fix(services): fix get_unhealthy_proposals filter #382"
git commit -m "fix(services): handle missing document_proposal_links #382"
git commit -m "chore(services): remove unused imports #382"
```

### 4. VERIFY
```bash
cd backend
python -c "from services.proposal_service import ProposalService; s = ProposalService(); print('Methods OK')"
```

### 5. DOCUMENT
```bash
git push -u origin fix/service-bugs-382
gh pr create --title "fix(services): fix logic bugs in proposal_service #382" \
  --body "Fixes #382. Fixed filter logic, handled missing tables, removed unused imports."
gh issue close 382 --comment "Fixed in PR."
```
```

---

## Agent 1C: Data Quality (#365)

```
You are a Builder Agent for the Bensley Operating System.

## Assignment
- Issue: #365
- Branch: fix/data-quality-365

## Setup
Launch via: ./launch_agent.sh claude 365
This creates your worktree and sets the branch automatically.

## MANDATORY WORKFLOW

### 1. AUDIT (10 min)
Read these files:
- CLAUDE.md
- AGENTS.md

Check the problem (requires BENSLEY_DB_PATH):
```sql
SELECT COUNT(*) FROM proposals WHERE project_value IS NULL OR project_value = 0;
```

Get details:
```sql
SELECT proposal_id, project_code, project_name
FROM proposals
WHERE project_value IS NULL OR project_value = 0;
```

Post findings:
gh issue comment 365 --body "AUDIT: Found X proposals missing project_value: [list first 5]"

### 2. PLAN (5 min)
gh issue comment 365 --body "PLAN: Create backfill report script, add validation to API"

### 3. IMPLEMENT
1. Create scripts/data/backfill_proposal_values.py
   - Generate report of missing values
   - Check if data exists elsewhere (emails, attachments, notes)

2. Update API validation to prevent future nulls

```bash
git commit -m "fix(data): add backfill report for missing project_value #365"
git commit -m "feat(api): add validation to prevent null project_value #365"
```

### 4. VERIFY
```bash
python scripts/data/backfill_proposal_values.py --dry-run
```

### 5. DOCUMENT
```bash
git push -u origin fix/data-quality-365
gh pr create --title "fix(data): address missing project_value #365" \
  --body "Fixes #365. Report generated, validation added."
gh issue comment 365 --body "Report generated. X proposals need manual value entry."
```
```
