# PHASE C: Feedback Infrastructure Agent Prompt

**Phase:** C - Human Feedback Infrastructure
**Role:** Full-Stack Agent
**Goal:** Build the workflow for humans to review, approve, and correct AI suggestions

---

## Context Files to Read First

1. `docs/planning/TIER1_PHASED_PLAN.md` - Your phase definition
2. `docs/context/backend.md` - Router map, endpoint list
3. `docs/context/frontend.md` - Page structure
4. `.claude/LIVE_STATE.md` - Phase B results
5. `backend/api/routers/suggestions.py` - Existing suggestions API

---

## Prerequisites Check

Before starting, verify Phase B is complete:
- Baseline metrics documented in LIVE_STATE.md
- DB backup exists

---

## Your Tasks

### Task 1: Complete Suggestions Approval Workflow

**Backend API endpoints needed:**

```python
# In backend/api/routers/suggestions.py

GET /api/suggestions
# List all suggestions with filters: status, type, priority, confidence

GET /api/suggestions/{id}
# Get single suggestion with full details

POST /api/suggestions/{id}/approve
# Body: { "reviewer_notes": "optional" }
# Action: Apply the suggestion, update status to 'approved'

POST /api/suggestions/{id}/reject
# Body: { "rejection_reason": "required" }
# Action: Mark as 'rejected', store reason

POST /api/suggestions/{id}/correct
# Body: { "corrected_data": {...}, "correction_reason": "required" }
# Action: Apply corrected version, store as 'corrected'
```

**Frontend UI needed:**

```
/admin/suggestions
├── List view (table with filters)
│   ├── Filter by: status, type, priority
│   ├── Sort by: confidence, date
│   └── Columns: title, type, confidence, status, actions
├── Detail modal/panel
│   ├── Full suggestion details
│   ├── Source reference (clickable link)
│   ├── Suggested action preview
│   └── Approve / Reject / Correct buttons
└── Bulk actions
    └── "Approve all >0.85 confidence" button
```

### Task 2: Bulk Approve High-Confidence

```python
POST /api/suggestions/bulk-approve
# Body: { "min_confidence": 0.85, "suggestion_type": "optional" }
# Action: Approve all pending suggestions >= confidence threshold

# Response should include:
{
    "approved_count": 42,
    "skipped_count": 5,  # Already processed
    "details": [...]
}
```

### Task 3: Track Decisions with Context

**Database schema additions:**

```sql
-- Add to ai_suggestions table (if not exists)
ALTER TABLE ai_suggestions ADD COLUMN reviewed_by TEXT;
ALTER TABLE ai_suggestions ADD COLUMN reviewed_at TEXT;
ALTER TABLE ai_suggestions ADD COLUMN review_notes TEXT;
ALTER TABLE ai_suggestions ADD COLUMN rejection_reason TEXT;
ALTER TABLE ai_suggestions ADD COLUMN corrected_data TEXT;
```

**Every decision must store:**
- suggestion_id
- decision (approved/rejected/corrected)
- reviewer (who made decision)
- timestamp
- reason/notes

### Task 4: Schema Migrations

Create migration file `database/migrations/048_feedback_infrastructure.sql`:

```sql
-- Contact enrichment tracking
ALTER TABLE contacts ADD COLUMN enrichment_source TEXT;
ALTER TABLE contacts ADD COLUMN enrichment_date TEXT;

-- Transcript suggestion linking
ALTER TABLE meeting_transcripts ADD COLUMN linked_via_suggestion_id INTEGER;

-- Suggestion review tracking (if columns don't exist)
-- Check first with: PRAGMA table_info(ai_suggestions);
```

### Task 5: SSOT Update Protocol

**Create file:** `docs/guides/SSOT_UPDATE_PROTOCOL.md`

```markdown
# SSOT Update Protocol

After EVERY agent session, update these files:

## Required Updates

### 1. `.claude/LIVE_STATE.md`
- Current metrics
- What changed this session
- Any blockers
- Phase status

### 2. `.claude/COORDINATOR_BRIEFING.md`
- Only if major changes occurred
- Strategic updates for coordinator

### 3. `docs/roadmap.md`
- Mark completed sprint items
- Update priorities if changed

### 4. `docs/context/index.md`
- If files were added or changed
- Update last-modified dates

## Update Template

At end of session, add to LIVE_STATE.md:

\`\`\`markdown
### Session: YYYY-MM-DD HH:MM

**Agent:** [Agent Name]
**Phase:** [Current Phase]

**Completed:**
- Item 1
- Item 2

**Metrics Changed:**
- X increased from Y to Z

**Blockers:**
- None / List any

**Next Steps:**
- What the next agent should do
\`\`\`
```

---

## Testing Requirements

After each feature, test:

```bash
# Start backend
cd backend && uvicorn api.main:app --reload --port 8000

# Test suggestions endpoint
curl -s http://localhost:8000/api/suggestions | jq '.[:3]'

# Test approval
curl -X POST http://localhost:8000/api/suggestions/1/approve \
  -H "Content-Type: application/json" \
  -d '{"reviewer_notes": "Test approval"}'

# Verify database updated
sqlite3 database/bensley_master.db "SELECT status, reviewed_at FROM ai_suggestions WHERE id = 1"
```

---

## Gate Criteria

Before declaring Phase C complete:

- [ ] GET /api/suggestions returns filtered list
- [ ] POST /api/suggestions/{id}/approve works
- [ ] POST /api/suggestions/{id}/reject works
- [ ] POST /api/suggestions/{id}/correct works
- [ ] Bulk approve endpoint works
- [ ] Frontend suggestions page loads
- [ ] User can review → approve → see update
- [ ] Schema migrations applied
- [ ] SSOT_UPDATE_PROTOCOL.md created

---

## DO NOT Do

- Do NOT auto-approve anything without UI confirmation
- Do NOT modify business logic unrelated to suggestions
- Do NOT skip frontend testing
- Do NOT forget to run migrations

---

## Handoff

When complete, update `.claude/LIVE_STATE.md`:

```markdown
## Phase C Status: COMPLETE

### Delivered
- Suggestions approval workflow (API + UI)
- Bulk approve feature
- Decision tracking with context
- Schema migrations applied
- SSOT update protocol documented

### How to Use
1. Go to /admin/suggestions
2. Review pending suggestions
3. Click Approve/Reject/Correct
4. Use bulk approve for high-confidence items

### Ready for Phase D
Phase D (Data Quality) can now begin using this infrastructure.
```
