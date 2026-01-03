# WAVE 0 - Security Foundation

Run these SEQUENTIALLY (each depends on previous).

---

## Agent 0A: Add Auth to Proposal Endpoints (#383)

```
You are a Builder Agent for the Bensley Operating System.

## Assignment
- Issue: #383
- Branch: fix/auth-proposal-endpoints-383

## Setup
Launch via: ./launch_agent.sh claude 383
This creates your worktree and sets the branch automatically.

## MANDATORY WORKFLOW

### 1. AUDIT (5 min)
Read these files completely before changing anything:
- CLAUDE.md
- AGENTS.md
- backend/api/dependencies.py (understand existing auth)
- backend/api/routers/proposals.py (find unprotected routes)

Post findings to issue:
gh issue comment 383 --body "AUDIT: Found X unprotected endpoints: [list them]"

### 2. PLAN (5 min)
Write your plan as a GitHub issue comment (NOT a new file):
gh issue comment 383 --body "PLAN: Will add Depends(get_current_user) to: [list endpoints]"

### 3. IMPLEMENT
Ensure all routes in proposals.py use:
current_user: dict = Depends(get_current_user)

- READ endpoints can be viewer-accessible
- WRITE endpoints (POST, PUT, DELETE) must require auth

Small commits, reference issue #:
git commit -m "fix(security): add auth to GET /proposals #383"
git commit -m "fix(security): add auth to POST /proposals #383"

### 4. VERIFY
```bash
cd backend
python -c "from api.routers.proposals import router; print('OK')"

# Start backend (requires BENSLEY_DB_PATH set)
uvicorn api.main:app --reload --port 8000

# Test without auth (should fail)
curl http://localhost:8000/api/proposals/
# Should return 401 Unauthorized
```

### 5. DOCUMENT
```bash
git push -u origin fix/auth-proposal-endpoints-383
gh pr create --title "fix(security): require auth on proposal endpoints #383" \
  --body "Fixes #383. Added auth to X endpoints. All WRITE operations require authentication."
gh issue comment 383 --body "DONE: PR created. Auth added to all proposal endpoints."
```
```

---

## Agent 0B: Add Rate Limiting (#361)

```
You are a Builder Agent for the Bensley Operating System.

## Assignment
- Issue: #361
- Branch: fix/rate-limiting-361

## Setup
Launch via: ./launch_agent.sh claude 361
This creates your worktree and sets the branch automatically.

## MANDATORY WORKFLOW

### 1. AUDIT (5 min)
Read these files completely:
- CLAUDE.md
- AGENTS.md
- backend/api/rate_limit.py (existing limiter config)
- backend/api/routers/proposals.py (chat endpoint ~line 1230)

Post findings:
gh issue comment 361 --body "AUDIT: Limiter exists in rate_limit.py. Chat endpoint at line X needs protection."

### 2. PLAN (5 min)
gh issue comment 361 --body "PLAN: Apply @limiter.limit() to chat endpoint (10/min)"

### 3. IMPLEMENT
Apply rate limits:
- /proposals/{code}/chat - 10/minute

Return clear 429 error when limit exceeded.

```bash
git add backend/
git commit -m "fix(security): add rate limiting to AI chat endpoint #361"
```

### 4. VERIFY
```bash
# Test rate limiting
for i in {1..15}; do
  curl -X POST http://localhost:8000/api/proposals/TEST/chat \
    -H "Content-Type: application/json" \
    -d '{"question": "test"}'
  echo ""
done
# Should see 429 after 10 requests
```

### 5. DOCUMENT
```bash
git push -u origin fix/rate-limiting-361
gh pr create --title "fix(security): add rate limiting to AI chat endpoint #361" \
  --body "Fixes #361. Rate limiting: chat=10/min"
gh issue comment 361 --body "DONE: PR created. Rate limiting active."
```
```
