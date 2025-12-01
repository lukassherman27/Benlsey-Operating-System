# PHASE F: Polish Agent Prompt

**Phase:** F - Polish & Demo Ready
**Role:** Frontend Agent
**Goal:** UI polish, fix remaining issues, make system demo-ready

---

## Context Files to Read First

1. `docs/planning/TIER1_PHASED_PLAN.md` - Your phase definition
2. `.claude/LIVE_STATE.md` - All previous phase completions
3. `docs/context/frontend.md` - Page structure
4. `docs/context/backend.md` - API endpoints

---

## Prerequisites Check

Before starting, verify Phase E is complete:
- Weekly report generates successfully
- Report includes email/transcript context
- API endpoint works

---

## Your Tasks

### Task 1: Email/Suggestions Page UI Fixes

**Page:** `/admin/suggestions`

**Checklist:**
- [ ] Page loads without errors
- [ ] Filters work (status, type, priority)
- [ ] Table displays properly
- [ ] Approve/Reject/Correct buttons work
- [ ] Bulk approve works
- [ ] Loading states shown
- [ ] Error states handled

**Smoke test after:**
```bash
# Open in browser
open http://localhost:3002/admin/suggestions

# Test actions:
# 1. Load page - no console errors
# 2. Filter by status
# 3. Click a suggestion - detail loads
# 4. Approve one - updates immediately
```

### Task 2: Projects Detail Widgets

**Page:** `/dashboard/projects/[id]`

**Widgets to verify:**
- [ ] Project header with status badge
- [ ] Fee breakdown widget
- [ ] Payment schedule widget
- [ ] RFI list widget
- [ ] Deliverables widget
- [ ] Email activity widget
- [ ] Meeting transcripts widget

**Smoke test after:**
```bash
# Open a project detail
open "http://localhost:3002/dashboard/projects/25%20BK-025"

# Verify:
# 1. All widgets render
# 2. Data displays correctly
# 3. No console errors
# 4. Actions work (if any)
```

### Task 3: Proposals Dashboard Polish

**Page:** `/dashboard/proposals`

**Checklist:**
- [ ] Proposal cards display correctly
- [ ] Status badges accurate
- [ ] Filters work
- [ ] Search works
- [ ] Detail view loads
- [ ] Email context shows
- [ ] Transcript summaries show

### Task 4: Admin Page Consolidation

**Review admin routes:**
- `/admin/emails` - Email management
- `/admin/suggestions` - Suggestions workflow
- `/admin/imports` - Data import tools
- `/admin/brain` - AI query interface

**Ensure:**
- [ ] All routes accessible from admin nav
- [ ] Consistent styling
- [ ] No dead links
- [ ] No 404 errors

### Task 5: UI Polish

**Visual review checklist:**
- [ ] Consistent color scheme
- [ ] Proper spacing
- [ ] Readable fonts
- [ ] Mobile responsive (basic)
- [ ] Loading spinners
- [ ] Empty states
- [ ] Error states

### Task 6: Performance Check

**Target:** Page load <2 seconds

```bash
# Check API response times
time curl -s http://localhost:8000/api/proposals/stats > /dev/null
time curl -s http://localhost:8000/api/projects/active > /dev/null
time curl -s http://localhost:8000/api/emails/recent > /dev/null

# Should be <500ms each
```

**If slow:**
- Add database indexes
- Implement pagination
- Add caching

---

## Smoke Test Protocol

**Run after EVERY backend fix:**

```bash
# Quick endpoint sweep
for endpoint in "/api/health" "/api/proposals/stats" "/api/projects/active" "/api/emails/recent"; do
    echo "Testing $endpoint:"
    curl -s "http://localhost:8000$endpoint" | head -c 100
    echo ""
done

# Frontend smoke
open http://localhost:3002/dashboard/proposals
open http://localhost:3002/dashboard/projects
open http://localhost:3002/admin/suggestions
```

**Check for:**
- No 500 errors
- No console errors
- Data displays
- Actions work

---

## Gate Criteria

Before declaring Phase F complete:

- [ ] Suggestions page fully functional
- [ ] Projects detail page widgets work
- [ ] Proposals dashboard polished
- [ ] Admin pages consolidated
- [ ] No console errors on any page
- [ ] Page load <2s
- [ ] Demo-ready appearance

---

## Final Checklist (Demo Ready)

```markdown
### Demo Flow (Bill's Daily Use)

1. Open Proposals Dashboard
   - [ ] Shows active proposals
   - [ ] Can filter by status
   - [ ] Can search

2. Click a Proposal
   - [ ] See full details
   - [ ] See recent emails
   - [ ] See meeting notes

3. Open Projects Dashboard
   - [ ] Shows active projects
   - [ ] Payment status visible

4. Click a Project
   - [ ] All widgets render
   - [ ] Fee breakdown shows
   - [ ] RFIs listed

5. Generate Weekly Report
   - [ ] Report generates
   - [ ] Includes email context
   - [ ] Includes meeting notes

6. Admin Features (optional demo)
   - [ ] Suggestions workflow
   - [ ] AI Brain queries
```

---

## DO NOT Do

- Do NOT add new features
- Do NOT refactor working code
- Do NOT change database schema
- Do NOT break existing functionality
- ONLY polish and fix

---

## Handoff

When complete, update `.claude/LIVE_STATE.md`:

```markdown
## Phase F Status: COMPLETE

### Tier 1 Complete!

All phases (A-F) completed. System is:
- Stable (no 500 errors)
- Data verified (Phase D metrics met)
- Reports working (weekly proposal reports)
- UI polished (demo-ready)

### Next: Tier 2 (Intelligence)

With clean, verified data, we can now begin:
- Local embeddings for semantic search
- RAG for intelligent queries
- Advanced AI features

### Final Metrics
- Backend uptime: 100%
- API response time: <500ms avg
- Frontend pages: X working
- Data quality: X% verified
- Reports: Working
```

---

## Tier 1 Completion Ceremony

When Phase F is done, create:

**File:** `.claude/TIER1_COMPLETE.md`

```markdown
# TIER 1: DATA FOUNDATION - COMPLETE

**Completed:** YYYY-MM-DD
**Duration:** X weeks

## What We Built

### Phase A: Infrastructure
- Backend stable on canonical DB
- All 27 routers working
- No hardcoded paths

### Phase B: Data Audit
- Baseline metrics established
- Sampling methodology documented
- Rollback points created

### Phase C: Feedback Infrastructure
- Suggestions workflow complete
- Bulk approve feature
- Decision tracking

### Phase D: Data Quality
- Email accuracy: X%
- Transcripts: 100% linked
- Contacts: Verified

### Phase E: Reports
- Weekly proposal report working
- Email context integrated
- Transcript summaries included

### Phase F: Polish
- UI demo-ready
- Performance optimized
- No console errors

## Ready for Tier 2

We now have clean, verified data ready for:
- Vector embeddings
- Semantic search
- RAG system
- Advanced AI features
```
