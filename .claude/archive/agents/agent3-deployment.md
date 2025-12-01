# Agent 3: Deployment & Infrastructure

**Role:** Deploy the BDS Operations Platform to cloud so Bill can access it
**Owner:** Deployment configs, environment variables, CI/CD
**Do NOT touch:** Application code (unless fixing deployment bugs)

---

## Context

You are deploying a full-stack application:
- **Frontend:** Next.js 15 → Deploy to Vercel
- **Backend:** FastAPI → Deploy to Railway
- **Database:** SQLite → Railway volume or Turso

**Read these files FIRST:**
1. `CLAUDE.md` - Project context
2. `frontend/package.json` - Frontend dependencies
3. `backend/api/main.py` - Backend entry point

---

## Your Tasks (Priority Order)

### P0: Deploy Frontend to Vercel (Do First)

#### Step 1: Create Vercel Config

**Create file:** `frontend/vercel.json`

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "regions": ["sin1"],
  "env": {
    "NEXT_PUBLIC_API_URL": "@api_url"
  }
}
```

#### Step 2: Deploy via CLI

```bash
cd frontend

# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy (follow prompts)
# - Set up and deploy: Yes
# - Which scope: Select your account
# - Link to existing project: No
# - Project name: bensley-ops (or similar)
# - Directory: ./
# - Override settings: No

vercel

# Note the deployment URL (e.g., bensley-ops.vercel.app)
```

#### Step 3: Set Environment Variables

```bash
# After backend is deployed, set the API URL
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://your-backend.railway.app
```

---

### P0: Deploy Backend to Railway (Do Second)

#### Step 1: Check/Create Requirements

**Verify file exists:** `backend/requirements.txt`

If missing, create it:
```
fastapi==0.109.0
uvicorn==0.27.0
python-multipart==0.0.6
pydantic==2.5.3
httpx==0.26.0
anthropic>=0.18.0
openai>=1.0.0
python-dateutil>=2.8.2
aiofiles>=23.0.0
```

#### Step 2: Create Procfile

**Create file:** `backend/Procfile`

```
web: uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

#### Step 3: Create Railway Config

**Create file:** `backend/railway.json`

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn api.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### Step 4: Deploy via CLI

```bash
cd backend

# Install Railway CLI
brew install railway

# Login
railway login

# Initialize project
railway init
# - Create new project: Yes
# - Project name: bensley-api

# Link to project
railway link

# Deploy
railway up

# Note the deployment URL
railway domain
```

#### Step 5: Set Environment Variables

In Railway dashboard (https://railway.app) or via CLI:

```bash
# Required
railway variables set DATABASE_PATH=/app/database/bensley_master.db
railway variables set ANTHROPIC_API_KEY=sk-ant-...

# Optional (for email features)
railway variables set OPENAI_API_KEY=sk-...

# CORS - allow frontend
railway variables set CORS_ORIGINS=https://bensley-ops.vercel.app,http://localhost:3002
```

---

### P1: Database Strategy

#### Option A: SQLite on Railway Volume (Simplest)

1. Create a volume in Railway dashboard
2. Mount at `/data`
3. Upload database file

```bash
# SSH into Railway (if available) or use volume upload
railway volume create bensley-data
railway variables set DATABASE_PATH=/data/bensley_master.db
```

**Limitation:** Single file, no concurrent writes

#### Option B: Turso (Recommended for Production)

Turso is SQLite at the edge - better for production.

```bash
# Install Turso CLI
brew install tursodatabase/tap/turso

# Login
turso auth login

# Create database
turso db create bensley-prod

# Get credentials
turso db show bensley-prod --url
turso db tokens create bensley-prod

# Set in Railway
railway variables set TURSO_DATABASE_URL=libsql://...
railway variables set TURSO_AUTH_TOKEN=...
```

**Note:** Requires code changes to use libsql driver. Ask Agent 1 if you go this route.

#### Option C: Keep Local, Sync Manually

For MVP, just:
1. Keep SQLite in repo (or volume)
2. Periodically upload new database file
3. Good enough for single user (Bill)

---

### P1: Update Backend for CORS

**Edit file:** `backend/api/main.py`

Find the CORS middleware and update:

```python
from fastapi.middleware.cors import CORSMiddleware
import os

# Get allowed origins from env or default
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3002").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### P1: Database Path Configuration

**Edit file:** `backend/api/main.py`

Ensure database path is configurable:

```python
import os

# At the top of the file
DB_PATH = os.getenv("DATABASE_PATH", "database/bensley_master.db")

# Make sure this is used everywhere instead of hardcoded path
```

---

### P2: Custom Domain (Optional)

If you want `ops.bensley.com` instead of `bensley-ops.vercel.app`:

1. In Vercel dashboard → Domains
2. Add `ops.bensley.com`
3. Add DNS records as instructed
4. Wait for propagation (5-30 min)

---

### P2: Monitoring & Logs

#### Vercel Logs
```bash
vercel logs bensley-ops --follow
```

#### Railway Logs
```bash
railway logs --follow
```

#### Set Up Alerts (Railway Dashboard)
- Go to Project → Settings → Notifications
- Add email alerts for deployment failures

---

## Testing Deployment

### Frontend Tests
```bash
# Open deployed URL in browser
open https://bensley-ops.vercel.app

# Check browser console for errors
# Verify API calls work
```

### Backend Tests
```bash
# Test API health
curl https://your-backend.railway.app/api/health

# Test an endpoint
curl https://your-backend.railway.app/api/proposals?limit=5
```

### End-to-End Test
1. Open frontend in browser
2. Navigate to Proposal Tracker
3. Verify data loads
4. Check network tab for any failed requests

---

## Troubleshooting

### Frontend Not Loading
```bash
# Check build logs
vercel logs --level=error

# Rebuild
vercel --force
```

### Backend 500 Errors
```bash
# Check logs
railway logs --filter=error

# Common issues:
# - DATABASE_PATH wrong
# - Missing environment variable
# - Module import errors (check requirements.txt)
```

### CORS Errors
- Check CORS_ORIGINS includes frontend URL
- Make sure no trailing slash
- Redeploy backend after changing env vars

### Database Not Found
- Check DATABASE_PATH is correct
- Ensure database file is uploaded/mounted
- Check file permissions

---

## Deployment Checklist

### Before Deploying
- [ ] Backend `requirements.txt` has all dependencies
- [ ] Backend `Procfile` exists
- [ ] Environment variables documented
- [ ] Database path is configurable

### After Frontend Deploy
- [ ] Note Vercel URL
- [ ] Check build succeeded
- [ ] Test homepage loads

### After Backend Deploy
- [ ] Note Railway URL
- [ ] Set all environment variables
- [ ] Test `/api/health` endpoint
- [ ] Upload/mount database

### After Both Deployed
- [ ] Set `NEXT_PUBLIC_API_URL` in Vercel
- [ ] Redeploy frontend
- [ ] Test end-to-end
- [ ] Share URL with Bill

---

## Files You'll Create/Edit

```
frontend/
├── vercel.json              # NEW

backend/
├── requirements.txt         # VERIFY/CREATE
├── Procfile                 # NEW
├── railway.json             # NEW
└── api/main.py             # EDIT (CORS, DB_PATH)
```

---

## When You're Done

1. Document deployed URLs in `docs/planning/DEPLOYMENT_URLS.md`
2. Test all major features work
3. Share URL with the team
4. Set up monitoring

---

## Do NOT

- Modify application logic (that's Agent 1/2's job)
- Add new features
- Change database schema
- Store secrets in code (use env vars)

---

**Estimated Time:** 4-6 hours total
**Start:** Can begin immediately (parallel with Agent 1)
**Checkpoint:** After both frontend and backend are accessible
**Blocker:** Need API URL for frontend env var → coordinate with backend deploy
