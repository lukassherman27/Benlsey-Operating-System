# 2-Week Sprint Plan: November 26 - December 9, 2025

**Created:** November 26, 2025
**Phase:** Phase 1 - Weeks 5-6 (Active Projects Dashboard Completion)
**Goal:** Complete Projects Dashboard, Polish UI, User Testing with Bill

---

## Executive Summary

### What We Have (Current State)
| Component | Status | Notes |
|-----------|--------|-------|
| Proposal Dashboard (`/tracker`) | **100%** | Fully functional with filters, stats, CRUD, export |
| Main Dashboard (`/`) | **95%** | KPIs, invoice aging, emails, proposal widget |
| Projects Dashboard (`/projects`) | **80%** | Has invoice widgets, missing RFI + Milestones |
| Finance Dashboard (`/finance`) | **60%** | Has widgets but KPIs are hardcoded |
| Proposal Detail (`/proposals/[code]`) | **90%** | Working |
| Project Detail (`/projects/[code]`) | **85%** | Working with email/hierarchy views |

### What's Missing (Gap from MVP Plan Week 5-6)
1. **RFI Tracker Widget** - API exists (`/api/rfis`), no UI
2. **Upcoming Milestones Widget** - API exists (`/api/milestones`), no UI
3. **Finance KPIs** - Currently hardcoded, need to connect to real APIs
4. **Mobile Responsiveness** - Needs testing and polish
5. **Auto-refresh** - Not implemented yet

### Blocker Status
- **Finance Excel**: 2+ weeks waiting - **PROCEED WITHOUT IT**
- **Plan B**: Ship with current invoice data (253 invoices), backfill later

---

## Sprint Goal

> **By December 9th, Bill can use the Operations Dashboard daily to:**
> 1. Track all active proposals and their status
> 2. See outstanding invoices and RFIs at a glance
> 3. Know what milestones are coming up
> 4. Make follow-up decisions without opening email/Excel

---

## Daily Task Breakdown

### Day 0: DEPLOYMENT (Nov 26 - Priority 1)
**Focus: Get Bill Access TODAY**

Before building more features, ship what we have so Bill can start using it.

#### Step 1: Deploy Frontend to Vercel (30 min)
```bash
# From project root
cd frontend

# Install Vercel CLI if needed
npm i -g vercel

# Deploy (follow prompts)
vercel

# Set environment variable for API URL
vercel env add NEXT_PUBLIC_API_URL
# Enter: https://your-railway-app.railway.app (after Step 2)
```

**Vercel Settings:**
- Framework: Next.js
- Build Command: `npm run build`
- Output Directory: `.next`
- Root Directory: `frontend`

#### Step 2: Deploy Backend to Railway (1 hour)
```bash
# Create railway.json in backend/ folder first
# Then from project root
cd backend

# Install Railway CLI
brew install railway

# Login and init
railway login
railway init

# Create new project, then deploy
railway up
```

**Backend Requirements:**
- [ ] Create `backend/requirements.txt` if not exists
- [ ] Create `backend/Procfile`: `web: uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- [ ] Set env vars in Railway dashboard:
  - `DATABASE_URL` - Railway SQLite or upload file
  - `ANTHROPIC_API_KEY` - For Claude API calls

#### Step 3: Database Options

**Option A: SQLite on Railway (Simplest)**
- Upload `bensley_master.db` to Railway volume
- Set `DATABASE_PATH=/data/bensley_master.db`
- Limitation: File-based, no concurrent writes

**Option B: Turso (SQLite in the cloud)**
```bash
# Install Turso CLI
brew install tursodatabase/tap/turso
turso auth login

# Create database
turso db create bensley-prod

# Get connection URL
turso db show bensley-prod --url
```
- Cost: Free tier available
- Better for production

**Option C: Keep SQLite, Sync Manually**
- Export DB periodically
- Upload to Railway
- Good enough for MVP single-user

#### Step 4: Connect Frontend to Backend
```bash
# In Vercel dashboard, add environment variable:
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

#### Step 5: Test & Share with Bill
- [ ] Test all dashboard pages on deployed URL
- [ ] Verify API calls work (check browser console)
- [ ] Send URL to Bill
- [ ] Document any issues

**Deliverable:** Bill has a working URL to access dashboards

---

### Week 1: Feature Completion (Nov 26 - Dec 2)

#### Day 1 - Tuesday, Nov 26
**Focus: RFI Tracker Widget** (after deployment is live)

- [ ] Review `/api/rfis` endpoint response structure
- [ ] Create `RFITrackerWidget` component in `frontend/src/components/dashboard/`
  - Display: RFI count, overdue count, list of unanswered RFIs
  - Actions: "Mark Answered", "View Thread" links
  - Color coding: Overdue (red), Due Soon (yellow), Normal (green)
- [ ] Add RFI widget to Projects Dashboard (`/projects/page.tsx`)
- [ ] Test with existing RFI data in database

**Deliverable:** RFI Tracker widget visible on Projects Dashboard

---

#### Day 2 - Wednesday, Nov 27
**Focus: Milestones Widget**

- [ ] Review `/api/milestones` endpoint response structure
- [ ] Create `UpcomingMilestonesWidget` component
  - Show next 14 days of milestones
  - Group by: Overdue | Next 3 Days | Next 7 Days | Next 14 Days
  - Display: Project code, milestone name, due date
  - Color coding by urgency
- [ ] Add Milestones widget to Projects Dashboard
- [ ] Test milestone display with existing data

**Deliverable:** Milestones widget showing upcoming deadlines

---

#### Day 3 - Thursday, Nov 28 (Thanksgiving)
**Focus: Light Work Day - Polish + Testing**

- [ ] Test RFI and Milestones widgets end-to-end
- [ ] Fix any bugs discovered
- [ ] Add loading states and error handling
- [ ] Document any data quality issues found

**Deliverable:** Both widgets stable and tested

---

#### Day 4 - Friday, Nov 29
**Focus: Finance Dashboard Live Data**

- [ ] Audit Finance page (`/finance/page.tsx`) - identify hardcoded values
- [ ] Create API calls for KPI cards:
  - Total Outstanding → `/api/invoices/stats`
  - Avg Days to Pay → Need to calculate or add endpoint
  - Critical (>90d) → `/api/invoices/outstanding` with filter
  - Collection Rate → Calculate from paid vs issued
- [ ] Replace hardcoded values with live API data
- [ ] Add loading states for KPI cards

**Deliverable:** Finance KPIs show real data

---

#### Day 5 - Saturday, Nov 30
**Focus: Projects Dashboard Summary Cards**

Per the MVP plan, Projects Dashboard should have 4 summary cards:
1. **Active Projects** count
2. **Outstanding Invoices** total ($)
3. **Upcoming Milestones** (next 14 days) count
4. **Unanswered RFIs** count

- [ ] Add summary cards row to top of Projects Dashboard
- [ ] Connect to existing APIs:
  - `/api/projects/active` → count
  - `/api/invoices/outstanding` → sum
  - `/api/milestones` → filter next 14 days, count
  - `/api/rfis` → filter unanswered, count
- [ ] Match design style with Proposal Dashboard cards

**Deliverable:** Projects Dashboard has 4 KPI summary cards

---

#### Day 6 - Sunday, Dec 1
**Focus: Navigation + Quick Actions**

- [ ] Review navigation flow between dashboards
- [ ] Ensure breadcrumbs work on detail pages
- [ ] Add "View All RFIs" link from widget
- [ ] Add "View All Milestones" link from widget
- [ ] Test keyboard navigation

**Deliverable:** Smooth navigation between all dashboard pages

---

#### Day 7 - Monday, Dec 2
**Focus: Week 1 Review + Bug Fixes**

- [ ] Run through all pages as a user would
- [ ] List all bugs/issues found
- [ ] Prioritize: Critical (blocks usage) vs. Nice-to-have
- [ ] Fix critical bugs
- [ ] Update PROJECT_CONTEXT.md with current status

**Deliverable:** All critical Week 1 bugs fixed

---

### Week 2: Polish & User Testing (Dec 3 - Dec 9)

#### Day 8 - Tuesday, Dec 3
**Focus: Mobile Responsiveness**

- [ ] Test all dashboard pages on tablet viewport (iPad)
- [ ] Test on mobile viewport (iPhone)
- [ ] Fix card layouts that don't stack properly
- [ ] Ensure tables are scrollable on mobile
- [ ] Test touch targets are large enough

**Deliverable:** Dashboard usable on tablet

---

#### Day 9 - Wednesday, Dec 4
**Focus: Auto-refresh + Loading States**

- [ ] Implement 5-minute auto-refresh on dashboard pages
- [ ] Add "Last updated" timestamp to each dashboard
- [ ] Add manual refresh button
- [ ] Implement skeleton loaders during data fetch
- [ ] Add React Query stale time configuration

**Deliverable:** Dashboards auto-refresh every 5 minutes

---

#### Day 10 - Thursday, Dec 5
**Focus: Performance Optimization**

- [ ] Audit bundle size (`npm run build`)
- [ ] Add pagination to any list > 50 items
- [ ] Lazy load detail page components
- [ ] Cache API responses with React Query
- [ ] Measure and record load times

**Deliverable:** Dashboard loads in < 2 seconds

---

#### Day 11 - Friday, Dec 6
**Focus: User Testing Prep**

- [ ] Create test scenarios for Bill walkthrough:
  1. "Find a proposal that needs follow-up"
  2. "See which invoices are overdue"
  3. "Check status of RFIs for project X"
  4. "What milestones are due next week"
- [ ] Prepare sample data that demonstrates each feature
- [ ] Set up screen recording for feedback session
- [ ] List questions to ask Bill

**Deliverable:** User testing plan ready

---

#### Day 12 - Saturday, Dec 7
**Focus: User Testing Session with Bill**

- [ ] 30-minute walkthrough session with Bill
- [ ] Observe: What's confusing? What's missing?
- [ ] Take notes on feedback
- [ ] Identify quick wins vs. future improvements
- [ ] Prioritize feedback items

**Deliverable:** User feedback documented

---

#### Day 13 - Sunday, Dec 8
**Focus: Critical Feedback Fixes**

- [ ] Implement top 3-5 critical feedback items
- [ ] Skip "nice-to-have" items for now
- [ ] Re-test fixed areas
- [ ] Update any confusing labels/text

**Deliverable:** Critical UX issues resolved

---

#### Day 14 - Monday, Dec 9
**Focus: Sprint Closeout**

- [ ] Final testing of all features
- [ ] Update CLAUDE.md with current status
- [ ] Update PROJECT_CONTEXT.md
- [ ] Create handoff notes for next sprint
- [ ] Commit all changes
- [ ] Celebrate!

**Deliverable:** Sprint complete, dashboards production-ready

---

## Dependencies & Blockers

### Blocked Items (Require External Input)
| Item | Blocked By | Workaround |
|------|------------|------------|
| Accurate invoice data | Finance Excel (2+ weeks) | Use current 253 invoices, note data may be incomplete |
| Historical email import | Email access | Skip for now, focus on dashboard UI |
| Contract PDFs | Finance team | Ship without, backfill later |

### Not Blocked (Can Proceed)
| Item | Status |
|------|--------|
| RFI data | Have data in DB (`/api/rfis` works) |
| Milestone data | Have data in DB (`/api/milestones` works) |
| Invoice widgets | Already working with current data |
| Proposal tracking | Fully functional |

---

## Risk Mitigation

### Risk 1: Finance Data Never Arrives
**Mitigation:**
- Ship with current invoice data (253 invoices)
- Add disclaimer: "Data as of Nov 2025 - awaiting finance update"
- Build manual invoice entry UI as fallback (Phase 2)
- Focus on proposal tracking which has complete data

### Risk 2: RFI/Milestone Data is Sparse
**Mitigation:**
- **VERIFIED:** Only 3 RFIs exist (all open), 0 milestones have future dates
- Still build widgets with proper empty states
- Focus on structure - data can be backfilled post-launch
- Consider adding quick-entry capability for manual milestone/RFI creation
- Document data entry needs for Bill to populate going forward

### Risk 3: Bill Has Major UX Concerns
**Mitigation:**
- Schedule testing session early (Dec 7)
- Leave buffer days (Dec 8-9) for critical fixes
- Prioritize ruthlessly: Must-fix vs. nice-to-have
- Document remaining items for next sprint

### Risk 4: Performance Issues
**Mitigation:**
- Test load times daily
- Use React Query caching
- Lazy load non-critical components
- Add pagination early if lists grow large

---

## Success Criteria

### By End of Sprint (Dec 9):
- [ ] Projects Dashboard has RFI Tracker widget
- [ ] Projects Dashboard has Milestones widget
- [ ] Projects Dashboard has 4 summary KPI cards
- [ ] Finance Dashboard KPIs show real data
- [ ] All dashboards mobile-responsive (tablet+)
- [ ] Auto-refresh working (5-min interval)
- [ ] Bill has tested and approved for daily use
- [ ] Load time < 2 seconds on all pages
- [ ] Zero critical bugs

### Acceptance Test (Bill's Perspective):
1. Can I see which proposals need follow-up? **YES** (Proposal Dashboard)
2. Can I see outstanding invoices by project? **YES** (Projects Dashboard)
3. Can I see unanswered RFIs? **YES** (RFI Widget)
4. Can I see upcoming deadlines? **YES** (Milestones Widget)
5. Is it faster than email + Excel? **YES** (All in one place)

---

## Technical Notes

### Key Files to Modify

**New Components:**
```
frontend/src/components/dashboard/rfi-tracker-widget.tsx (NEW)
frontend/src/components/dashboard/milestones-widget.tsx (NEW)
```

**Files to Update:**
```
frontend/src/app/(dashboard)/projects/page.tsx - Add widgets
frontend/src/app/(dashboard)/finance/page.tsx - Live data for KPIs
frontend/src/components/dashboard/kpi-cards.tsx - May need updates
```

### API Endpoints Used

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `GET /api/rfis` | RFI list | Exists |
| `GET /api/milestones` | Milestone list | Exists |
| `GET /api/projects/active` | Active project count | Exists |
| `GET /api/invoices/outstanding` | Outstanding amount | Exists |
| `GET /api/invoices/stats` | Invoice statistics | Exists |

### Data Quality Check (Verified Nov 26, 2025)

**RFIs:**
- Total: 3 RFIs in database
- All status: "open" (unanswered)
- Widget will work but show sparse data
- **Action:** Build widget, handle empty state gracefully

**Milestones:**
- Total: 110 milestones in database
- **Issue:** All 110 have NULL `planned_date` (only `actual_date` for completed ones)
- No pending/in-progress milestones with future dates
- **Action:** Build widget with empty state, add milestone entry capability later
- **Note:** Most milestone data is historical tracking, not forward-looking schedule

**Implication for Sprint:**
- RFI widget: Build as planned, will show 3 items
- Milestones widget: Build structure, will show "No upcoming milestones"
- Both widgets prove architecture works, data can be backfilled
- Per CLAUDE.md: "Ship with 80% data quality, iterate based on real usage"

---

## Post-Sprint: What's Next

After Dec 9, remaining MVP tasks (Week 7-8 per plan):
1. Error handling improvements
2. Retry logic for failed requests
3. Production deployment preparation
4. Security review
5. Final polish

---

## PHASE 2 PREP: The Bensley Machine (AI Infrastructure)

**Timeline:** December/January (Holiday Period)
**Goal:** Turn the database into an intelligent system that learns and automates

### Hardware Requirements

**Option A: Mac Mini (Recommended for Local LLM)**
| Component | Spec | Why | Cost |
|-----------|------|-----|------|
| Mac Mini M2 Pro | 32GB RAM | Runs Llama 3.1 8B locally | ~$1,500 |
| External SSD | 1TB | Store models + vector DB | ~$100 |
| UPS | Basic | Prevent data loss | ~$100 |

**Option B: Linux Server (More Power)**
| Component | Spec | Why | Cost |
|-----------|------|-----|------|
| Used Server | 64GB RAM, GPU | Runs Llama 70B | ~$1,000-2,000 |
| RTX 3090/4090 | 24GB VRAM | Fast inference | ~$1,000-1,500 |

**Option C: Cloud GPU (Pay-per-use)**
- RunPod, Lambda Labs, or Vast.ai
- ~$0.50-2/hour for inference
- Good for testing before buying hardware

### Software Stack to Install

```bash
# 1. Ollama - Local LLM runtime
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b  # Start with 8B, upgrade to 70B if hardware supports

# 2. ChromaDB - Vector database for RAG
pip install chromadb

# 3. Sentence Transformers - Generate embeddings
pip install sentence-transformers

# 4. LangChain (optional) - Orchestration
pip install langchain langchain-community
```

### Database Tables Already Ready

You already have the intelligence schema built:

| Table | Purpose | Status |
|-------|---------|--------|
| `training_data` | Store Claude responses for fine-tuning | Ready |
| `ai_suggestions_queue` | AI-generated suggestions awaiting review | Ready |
| `learned_patterns` | Patterns the system has learned | Ready |
| `document_intelligence` | AI analysis of documents | Ready |
| `data_confidence_scores` | Confidence levels for AI predictions | Ready |

### Phase 2 Build Plan (4-6 weeks)

#### Week 1-2: Local LLM Setup
- [ ] Install Ollama on Mac Mini/server
- [ ] Download Llama 3.1 8B model
- [ ] Create API wrapper to swap Claude → Ollama
- [ ] Test: Can local LLM answer "What's the status of BK-095?"
- [ ] Benchmark: Response time, quality vs Claude

#### Week 3-4: RAG System (Semantic Search)
- [ ] Set up ChromaDB
- [ ] Generate embeddings for all emails (3,356)
- [ ] Generate embeddings for all documents
- [ ] Build semantic search endpoint: `/api/search/semantic`
- [ ] Test: "Find emails about payment delays" returns relevant results

#### Week 5-6: Model Distillation Pipeline
- [ ] Export all Claude conversations from `training_data`
- [ ] Format as instruction-tuning dataset
- [ ] Fine-tune Llama on BDS-specific data (using MLX or similar)
- [ ] Benchmark fine-tuned model vs base model
- [ ] Deploy: Route 80% queries to local, 20% to Claude

### Architecture: Hybrid AI Approach

```
┌─────────────────────────────────────────────────────────┐
│                    USER QUERY                           │
│            "What invoices are overdue?"                 │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   QUERY ROUTER                          │
│   Simple queries → Local LLM (80%)                      │
│   Complex queries → Claude API (20%)                    │
└─────────────────────────────────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            ▼                              ▼
┌───────────────────────┐    ┌────────────────────────────┐
│     LOCAL LLM         │    │      CLAUDE API            │
│  (Ollama + Llama)     │    │  (Complex reasoning)       │
│  - Fast (< 2 sec)     │    │  - Slower (3-5 sec)        │
│  - Free after setup   │    │  - $50-200/month           │
│  - BDS fine-tuned     │    │  - General knowledge       │
└───────────────────────┘    └────────────────────────────┘
            │                              │
            └──────────────┬───────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  RAG CONTEXT                            │
│   ChromaDB returns relevant docs/emails                 │
│   Adds context to LLM prompt                            │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    RESPONSE                             │
│   "You have 15 overdue invoices totaling $487,000.      │
│    The oldest is BK-070 Invoice #I24-045 at 87 days."   │
└─────────────────────────────────────────────────────────┘
```

### Cost Comparison: Cloud vs Local

**Current (100% Claude API):**
- ~$50-200/month depending on usage
- No hardware costs
- Scales automatically

**Phase 2 (80% Local, 20% Claude):**
- Hardware: $1,500-3,000 one-time
- Claude API: ~$10-40/month (reduced to 20%)
- Electricity: ~$20-30/month
- **Break-even:** 3-6 months

**Long-term (90% Local):**
- Monthly cost: ~$30-50 (electricity + minimal Claude)
- Full control over data (no external API calls)
- Faster responses for common queries

### Data Collection: Start Now!

Even during Phase 1, collect training data:

```python
# Every time Claude answers a query, log it:
INSERT INTO training_data (
    query_text,
    response_text,
    model_used,
    context_provided,
    user_rating,  -- NULL until user rates
    created_at
) VALUES (?, ?, 'claude-3-opus', ?, NULL, datetime('now'));
```

The more data you collect now, the better the fine-tuned model will be.

### Pre-Phase 2 Checklist (Do During Phase 1)

- [ ] Order Mac Mini M2 Pro (or equivalent hardware)
- [ ] Set up static IP or dynamic DNS for office network
- [ ] Document all query patterns Bill uses
- [ ] Ensure `training_data` table is being populated
- [ ] Export conversation logs periodically
- [ ] Research fine-tuning approaches (MLX, LoRA, QLoRA)

---

## Production Deployment: Long-term Architecture

**Target:** Mac Mini in Bangkok office + Azure Singapore backup

```
┌─────────────────────────────────────────────────────────┐
│                  BANGKOK OFFICE                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              MAC MINI (Primary)                 │   │
│  │  - FastAPI Backend (port 8000)                  │   │
│  │  - Next.js Frontend (port 3002)                 │   │
│  │  - SQLite Database                              │   │
│  │  - Ollama + Llama (local LLM)                   │   │
│  │  - ChromaDB (vector search)                     │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│                    WireGuard VPN                        │
│                    (encrypted sync)                     │
└─────────────────────────────────────────────────────────┘
                          │
                          │ Every 15 min
                          ▼
┌─────────────────────────────────────────────────────────┐
│                 AZURE SINGAPORE                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              BACKUP VM ($50-100/mo)             │   │
│  │  - Database replica (read-only)                 │   │
│  │  - Failover capability                          │   │
│  │  - Off-site backup                              │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**When to Set This Up:** After Phase 2 is working, before multi-user rollout (Phase 3)

---

**Remember:** Don't wait for perfect data. Ship with what we have, iterate based on real usage.

**Last Updated:** 2025-11-26
**Status:** Ready to Execute
