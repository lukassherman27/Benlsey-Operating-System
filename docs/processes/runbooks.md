# Runbooks - Single Source of Truth

**Owner:** Ops Agent
**Last Updated:** 2025-11-27
**Purpose:** How to do common operations

---

## Quick Start

### Run Everything Locally
```bash
# Terminal 1: Backend
cd backend && uvicorn api.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev

# Access:
# - Frontend: http://localhost:3002
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Health Check
```bash
make health-check
# Or manually:
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM projects;"
curl http://localhost:8000/health
```

---

## Development Workflows

### Adding a New API Endpoint

1. **Find or create service:**
   ```
   backend/services/{feature}_service.py
   ```

2. **Add endpoint to main.py:**
   ```python
   # backend/api/main.py
   from services.{feature}_service import FeatureService

   @app.get("/api/{feature}")
   async def get_feature():
       service = FeatureService(get_db())
       return service.get_all()
   ```

3. **Test:**
   ```bash
   curl http://localhost:8000/api/{feature}
   ```

4. **Update context:**
   - Add to `docs/context/backend.md`
   - Update `docs/context/index.md` integration table

### Adding a New Frontend Page

1. **Create page file:**
   ```
   frontend/src/app/(dashboard)/{feature}/page.tsx
   ```

2. **Create component if needed:**
   ```
   frontend/src/components/{feature}/{feature}-table.tsx
   ```

3. **Add API types:**
   ```
   frontend/src/lib/types.ts
   ```

4. **Add API call:**
   ```
   frontend/src/lib/api.ts
   ```

5. **Test:**
   ```bash
   cd frontend && npm run build
   # Visit http://localhost:3002/{feature}
   ```

6. **Update context:**
   - Add to `docs/context/frontend.md`
   - Update `docs/context/index.md` integration table

### Adding a Database Migration

1. **Find next migration number:**
   ```bash
   ls database/migrations/ | tail -5
   ```

2. **Create migration file:**
   ```
   database/migrations/071_add_{feature}.sql
   ```

3. **Run migration:**
   ```bash
   sqlite3 database/bensley_master.db < database/migrations/071_add_{feature}.sql
   ```

4. **Verify:**
   ```bash
   sqlite3 database/bensley_master.db ".schema {table_name}"
   ```

5. **Update context:**
   - Add to `docs/context/data.md`

---

## Testing

### Run All Tests
```bash
make check
# Or:
pytest tests/ -v
```

### Run Specific Tests
```bash
pytest tests/test_services.py -v
pytest tests/test_email_api.py -v -k "test_link"
```

### Check Frontend Types
```bash
cd frontend && npx tsc --noEmit
```

### Lint Everything
```bash
# Backend
black backend/ scripts/ --check
ruff check backend/ scripts/

# Frontend
cd frontend && npm run lint
```

---

## Data Operations

### Email Processing
```bash
# Process new emails (dry run)
python scripts/core/smart_email_brain.py --dry-run

# Actually process
python scripts/core/smart_email_brain.py

# Link emails to projects
python scripts/core/email_linker.py

# Check linking status
sqlite3 database/bensley_master.db "
SELECT
  (SELECT COUNT(*) FROM email_project_links) as linked,
  (SELECT COUNT(*) FROM emails) as total
"
```

### Process AI Suggestions
```bash
# View pending
python scripts/core/suggestion_processor.py --status

# Auto-approve high confidence
python scripts/core/suggestion_processor.py --auto-approve --confidence 0.9

# Manual review mode
python scripts/core/suggestion_processor.py --interactive
```

### Database Backup
```bash
# Create dated backup
cp database/bensley_master.db "database/backups/bensley_master_$(date +%Y%m%d).db"

# Verify backup
sqlite3 "database/backups/bensley_master_$(date +%Y%m%d).db" "SELECT COUNT(*) FROM projects;"
```

### Full Data Audit
```bash
python scripts/analysis/audit_complete_database.py
```

---

## Deployment

### Pre-deployment Checklist
- [ ] All tests pass: `make check`
- [ ] No uncommitted changes: `git status`
- [ ] Frontend builds: `cd frontend && npm run build`
- [ ] Database backed up
- [ ] Environment variables set

### Deploy Frontend (Vercel)
```bash
cd frontend
vercel --prod
```

### Deploy Backend (Railway)
```bash
# Push to main triggers auto-deploy
git push origin main
```

---

## Troubleshooting

### Backend Won't Start
```bash
# Check if port in use
lsof -i :8000
kill -9 <PID>

# Check Python env
which python
pip list | grep fastapi
```

### Frontend Won't Start
```bash
# Check if port in use
lsof -i :3002
kill -9 <PID>

# Reinstall deps
cd frontend && rm -rf node_modules && npm install
```

### Database Locked
```bash
# Find processes
lsof database/bensley_master.db

# Kill if needed
kill -9 <PID>
```

### Email Import Fails
```bash
# Check IMAP connection
python -c "
import imaplib
mail = imaplib.IMAP4_SSL('tmail.bensley.com')
print('Connection OK')
"

# Check credentials in .env
cat .env | grep IMAP
```

---

## Git Operations

### Commit Message Format
```
[type](agent): Brief description

- Detail 1
- Detail 2

Affects: context/backend.md
Unblocks: frontend admin UI
```

### Branch Naming
```
phase1/agent1-{feature}
feature/{feature-name}
fix/{bug-description}
```

### PR Checklist
- [ ] Tests pass
- [ ] Lint passes
- [ ] Context files updated if needed
- [ ] Handoff note written

---

## Adding a New Agent

1. **Create agent definition:**
   ```
   docs/agents/{agent-name}.md
   ```

2. **Use contract template from registry.md**

3. **Add to registry:**
   - Update `docs/agents/registry.md`

4. **Create context bundle if needed:**
   - Add to `docs/context/`
   - Update `docs/context/index.md`

---

## Environment Variables

### Required (.env)
```bash
DATABASE_PATH=database/bensley_master.db
ANTHROPIC_API_KEY=sk-ant-...
IMAP_HOST=tmail.bensley.com
IMAP_USER=...
IMAP_PASS=...
```

### Optional
```bash
LOG_LEVEL=INFO
FRONTEND_URL=http://localhost:3002
BACKEND_URL=http://localhost:8000
```

---

## Scheduled Jobs (Future)

| Job | Schedule | Script | Purpose |
|-----|----------|--------|---------|
| Email sync | Hourly | `smart_email_brain.py` | Process new emails |
| Suggestion cleanup | Daily | `suggestion_processor.py` | Auto-approve high confidence |
| Backup | Daily | `sync_database.sh` | Database backup |
| Weekly report | Monday 9am | `generate_weekly_proposal_report.py` | Proposal summary |

---

## Emergency Contacts

| Issue | Who | Contact |
|-------|-----|---------|
| System down | Lukas | - |
| Data questions | Bill | - |
| Finance data | Finance team | - |
