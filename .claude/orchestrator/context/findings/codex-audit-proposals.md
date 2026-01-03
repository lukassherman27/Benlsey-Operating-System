## Codex Security Findings

**Area:** proposals
**Files Reviewed:** 8 files

### Critical (Immediate Fix Required)
- [C1] **Unauthenticated access to sensitive proposal data**: Most proposal and tracker GET endpoints do not require auth, exposing PII (contact emails/phones), internal notes, full email bodies, and document metadata.
  - File: `backend/api/routers/proposals.py:44` (list/stats/at-risk/needs-follow-up)
  - File: `backend/api/routers/proposals.py:456` (tracker detail/history/emails)
  - File: `backend/api/routers/proposals.py:737` (conversation returns full `body_full`)
  - File: `backend/api/routers/proposals.py:813` (stakeholders w/ emails/phones)
  - File: `backend/api/routers/proposals.py:913` (documents metadata)
  - File: `backend/api/routers/proposals.py:1068` (story returns internal notes + threads)
  - File: `backend/api/routers/proposals.py:1098` (summary)
  - Severity: CRITICAL
  - Fix: Add `Depends(get_current_user)` (or `get_current_user_optional` with redaction), then enforce RBAC/role scopes per endpoint.

- [C2] **Rate limiting not actually enforced on chat endpoint**: `@limiter.limit(...)` is used without importing `limiter`, so rate limiting is likely broken or the module fails to load. This leaves the OpenAI chat route open to abuse/cost spikes.
  - File: `backend/api/routers/proposals.py:16` (missing limiter import)
  - File: `backend/api/routers/proposals.py:1230-1234`
  - Severity: CRITICAL
  - Fix: `from api.rate_limit import limiter` and add rate limits to other high-cost endpoints.

### High (Fix Soon)
- [H1] **Authorization gap on updates**: Any authenticated user can update any proposal; no RBAC/ownership checks before writing changes (status, internal_notes, financials).
  - File: `backend/api/routers/proposals.py:472-483`
  - File: `backend/services/proposal_tracker_service.py:521-584`
  - Risk: Non-privileged users can alter pipeline values, statuses, or internal notes.
  - Fix: Enforce role-based access (executive/admin/pm) and/or per-project ownership.

- [H2] **No rate limits on other heavy proposal endpoints**: `/story`, `/conversation`, `/timeline`, `/proposal-tracker/list` can be hammered to exfiltrate data or degrade service.
  - File: `backend/api/routers/proposals.py:640-807` (timeline/conversation)
  - File: `backend/api/routers/proposals.py:1068-1224` (story/summary)
  - Fix: add `@limiter.limit(...)` with sane thresholds for read-heavy endpoints.

### Medium (Plan to Fix)
- [M1] **Unvalidated update payloads**: `updates: dict` accepts arbitrary values; only filters keys. No schema validation on dates, emails, or enums, increasing data integrity risk.
  - File: `backend/api/routers/proposals.py:472-477`
  - File: `backend/services/proposal_tracker_service.py:537-555`
  - Fix: Replace `dict` with a Pydantic model + validators.

- [M2] **Internal filepath exposure**: Proposal story returns attachment `filepath` values (likely internal OneDrive paths).
  - File: `backend/services/proposal_detail_story_service.py:140-155`
  - File: `backend/services/proposal_detail_story_service.py:258-275`
  - Fix: Redact/omit file paths, or return a safe download token.

- [M3] **CORS misconfig risk**: `allow_credentials=True` with env-driven origins. If `CORS_ORIGINS=*` or an untrusted host is set, cookies/tokens can be exposed.
  - File: `backend/api/main.py:79-129`
  - Fix: Restrict to explicit trusted domains; avoid `*` with credentials.

### Endpoints Missing Auth
- `GET /api/proposals`
- `GET /api/proposals/stats`
- `GET /api/proposals/at-risk`
- `GET /api/proposals/needs-follow-up`
- `GET /api/proposals/weekly-changes`
- `GET /api/proposals/needs-attention`
- `GET /api/proposal-tracker/stats`
- `GET /api/proposal-tracker/list`
- `GET /api/proposal-tracker/disciplines`
- `GET /api/proposal-tracker/countries`
- `GET /api/proposal-tracker/{project_code}`
- `GET /api/proposal-tracker/{project_code}/history`
- `GET /api/proposal-tracker/{project_code}/emails`
- `GET /api/proposals/{project_code}/versions`
- `GET /api/proposals/{project_code}/fee-history`
- `GET /api/proposals/search/by-client`
- `GET /api/proposals/{project_code}/timeline`
- `GET /api/proposals/{project_code}/conversation`
- `GET /api/proposals/{project_code}/stakeholders`
- `GET /api/proposals/{project_code}/documents`
- `GET /api/proposals/{project_code}/briefing`
- `GET /api/proposals/{project_code}/story`
- `GET /api/proposals/summary`

### Endpoints Missing Rate Limits
- `POST /api/proposals/{project_code}/chat` (limiter not imported)
- `GET /api/proposals/{project_code}/story`
- `GET /api/proposals/{project_code}/conversation`
- `GET /api/proposals/{project_code}/timeline`
- `GET /api/proposal-tracker/list`
- `GET /api/proposals/needs-attention`

### SQL Injection
- None found. Queries are parameterized and sort columns are whitelisted via `BaseService.validate_sort_column`.

### Recommendations
1. Require auth + RBAC for all proposal/tracker endpoints; redact PII for optional/public views.
2. Fix rate limiting import and add limits on heavy read endpoints.
3. Add Pydantic models for update payloads + explicit field validation.
4. Remove `filepath` from API responses or replace with signed download URLs.
5. Lock down CORS origins to explicit trusted hosts only.
