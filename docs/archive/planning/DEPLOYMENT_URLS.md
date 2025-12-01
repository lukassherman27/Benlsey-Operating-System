# BDS Operations Platform - Deployment URLs

**Last Updated:** 2025-11-26
**Status:** Frontend LIVE, Backend BLOCKED (Railway requires payment)

---

## Production URLs

| Service | URL | Status |
|---------|-----|--------|
| Frontend (Vercel) | https://frontend-olive-ten-82.vercel.app | ✅ LIVE |
| Backend (Railway) | `BLOCKED` | ⚠️ Requires paid plan |

---

## Current State

### Frontend - DEPLOYED ✅
- **URL:** https://frontend-olive-ten-82.vercel.app
- **Vercel Project:** lukas-shermans-projects/frontend
- **Note:** Currently points to localhost:8000 for API (will show errors until backend deployed)

### Backend - BLOCKED ⚠️
- **Reason:** Railway requires Hobby plan ($5/month) or credit card to deploy
- **Options:**
  1. Add payment method at https://railway.com/account/plans
  2. Use alternative: Render.com (free tier) or Fly.io
  3. Keep running locally until ready for cloud

---

## Next Steps to Complete Deployment

1. **Upgrade Railway Plan** (or choose alternative)
   ```bash
   # After adding payment method:
   cd backend
   railway up
   railway domain  # Get the URL
   ```

2. **Set Backend Environment Variables**
   ```bash
   railway variables set BENSLEY_DB_PATH=/data/bensley_master.db
   railway variables set OPENAI_API_KEY=sk-...
   railway variables set CORS_ORIGINS=https://frontend-olive-ten-82.vercel.app,http://localhost:3002
   ```

3. **Create Database Volume**
   - Railway Dashboard → Project → New → Volume
   - Mount path: `/data`
   - Upload `database/bensley_master.db`

4. **Update Frontend with Backend URL**
   ```bash
   cd frontend
   vercel env add NEXT_PUBLIC_API_URL production
   # Enter: https://YOUR-BACKEND.railway.app
   vercel --prod
   ```

---

## Alternative Backend Hosting (If Railway Not Preferred)

### Option A: Render.com (Free Tier Available)
```bash
# Create render.yaml in backend/
# Deploy via Render dashboard
```

### Option B: Fly.io
```bash
brew install flyctl
fly auth login
cd backend
fly launch
fly secrets set BENSLEY_DB_PATH=/data/bensley_master.db
fly secrets set OPENAI_API_KEY=sk-...
```

---

## Files Created for Deployment

| File | Purpose |
|------|---------|
| `frontend/vercel.json` | Vercel config |
| `backend/requirements.txt` | Python dependencies |
| `backend/Procfile` | Railway/Heroku process config |
| `backend/railway.json` | Railway deployment config |

---

## Testing (Once Backend Deployed)

### Backend Health Check
```bash
curl https://[backend-url]/api/health
```

### New Endpoints to Test
```bash
curl https://[backend-url]/api/meeting-transcripts
curl https://[backend-url]/api/projects/24001/unified-timeline
curl https://[backend-url]/api/rfis?limit=5
```

### End-to-End
1. Open https://frontend-olive-ten-82.vercel.app
2. Navigate to Projects Dashboard
3. Verify data loads from backend

---

## Notes

- Database env var is `BENSLEY_DB_PATH` (not `DATABASE_PATH`)
- CORS already configured to read from `CORS_ORIGINS` env var
- Backend listens on `$PORT` (Railway/Render provide this)
- ESLint rules relaxed in `frontend/eslint.config.mjs` for deployment (TODO: fix warnings)
