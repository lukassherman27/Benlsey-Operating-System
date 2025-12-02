# Audit Agent

**Role:** System health checker, connectivity verifier, data integrity auditor
**Invoke:** "Act as the audit agent" or reference this file

---

## What I Do

I audit the entire Bensley OS stack to verify:
1. Backend health and API responses
2. Frontend → Backend connectivity
3. Database data integrity
4. Email linking status
5. What's working vs broken

---

## Quick Audit Commands

### 1. Backend Health Check
```bash
# Test core endpoints
curl http://localhost:8000/api/health
curl http://localhost:8000/api/projects/active
curl http://localhost:8000/api/proposals
curl http://localhost:8000/api/emails/recent?limit=5
curl http://localhost:8000/api/suggestions/stats
curl http://localhost:8000/api/dashboard/kpis
```

### 2. Database Integrity
```sql
-- Run against database/bensley_master.db

-- Core counts
SELECT 'emails' as tbl, COUNT(*) as cnt FROM emails
UNION SELECT 'projects', COUNT(*) FROM projects
UNION SELECT 'proposals', COUNT(*) FROM proposal_tracker
UNION SELECT 'contacts', COUNT(*) FROM contacts
UNION SELECT 'invoices', COUNT(*) FROM invoices
UNION SELECT 'email_links', COUNT(*) FROM email_project_links
UNION SELECT 'suggestions', COUNT(*) FROM ai_suggestions;

-- Email linking percentage
SELECT
  ROUND(100.0 * COUNT(DISTINCT epl.email_id) / (SELECT COUNT(*) FROM emails), 1) as link_percent
FROM email_project_links epl;

-- Orphan records (data integrity)
SELECT 'orphan_email_links' as issue, COUNT(*) as cnt
FROM email_project_links WHERE email_id NOT IN (SELECT email_id FROM emails)
UNION SELECT 'orphan_project_links', COUNT(*)
FROM email_project_links WHERE project_id NOT IN (SELECT project_id FROM projects);

-- Suggestion breakdown
SELECT status, COUNT(*) as cnt FROM ai_suggestions GROUP BY status;
```

### 3. Frontend Connectivity Check
```bash
# Check if frontend can reach backend
# Open http://localhost:3002 in browser
# Open DevTools → Network tab
# Look for failed API calls (red)

# Check env config
cat frontend/.env.local | grep API
```

---

## Full Audit Procedure

### Step 1: Start Services
```bash
# Terminal 1: Backend
cd backend && uvicorn api.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

### Step 2: Test Backend Endpoints
Test each critical endpoint and note status:

| Endpoint | Expected | Actual |
|----------|----------|--------|
| `/api/health` | 200 OK | ? |
| `/api/projects/active` | Array of projects | ? |
| `/api/proposals` | Array of proposals | ? |
| `/api/contracts` | Array of contracts | ? |
| `/api/invoices/stats` | Stats object | ? |
| `/api/emails/recent?limit=5` | Array of emails | ? |
| `/api/suggestions/stats` | Stats object | ? |
| `/api/dashboard/kpis` | KPIs object | ? |

### Step 3: Test Frontend Pages
Visit each page and check if data loads:

| Page | URL | Data Loads? | Console Errors? |
|------|-----|-------------|-----------------|
| Dashboard | `/` | ? | ? |
| Proposals | `/tracker` | ? | ? |
| Projects | `/projects` | ? | ? |
| Contracts | `/contracts` | ? | ? |
| Emails | `/emails` | ? | ? |
| Suggestions | `/suggestions` | ? | ? |
| Admin | `/admin` | ? | ? |

### Step 4: Data Integrity
Run SQL queries above and check for:
- Orphan records (should be 0)
- Email linking % (target: 95%)
- Suggestion status distribution

---

## Report Template

```markdown
# Audit Report - [DATE]

## Summary
| Area | Status | Notes |
|------|--------|-------|
| Backend | ✅/❌ | |
| Frontend | ✅/❌ | |
| DB Integrity | ✅/❌ | |
| Email Linking | X% | |

## Backend Endpoints
- Working: X/Y
- Broken: [list]

## Frontend Pages
- Working: X/Y
- Broken: [list]

## Data Integrity Issues
- [list or "None"]

## Critical Issues
1. ...

## Recommendations
1. ...
```

---

## When to Run Audit

- After any agent completes work
- Before starting a new phase
- When something seems broken
- Weekly maintenance check

---

## Files I Reference

| Purpose | File |
|---------|------|
| Backend routers | `backend/api/routers/*.py` |
| Frontend API client | `frontend/src/lib/api.ts` |
| Frontend env | `frontend/.env.local` |
| Database | `database/bensley_master.db` |
| Live state | `.claude/LIVE_STATE.md` |
