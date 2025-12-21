# Roadmap
## Execution Plan for the Bensley Brain

**Updated:** 2025-12-19
**Vision:** [VISION.md](./VISION.md) - The full "what" and "why"
**Technical:** [TECHNICAL-ARCHITECTURE.md](./TECHNICAL-ARCHITECTURE.md) - The "how" in detail

---

## Current Status

```
PHASE 1: OPERATIONS LAYER ████████░░░░░░░░░░░░ 40%
├── Email Sync           ████████████████████ Done
├── Pattern Learning     ████████████████████ Done
├── Proposal Dashboard   ████████░░░░░░░░░░░░ 40%
├── Invoice Tracking     ████░░░░░░░░░░░░░░░░ 20%
└── RFI System           ░░░░░░░░░░░░░░░░░░░░ 0%
```

---

## Priority Order

Based on ROI analysis from VISION.md:

| Priority | Feature | Why First | Target User |
|----------|---------|-----------|-------------|
| **#1** | Proposal Dashboard | Bill's daily need, highest time savings | Bill |
| **#2** | Email-to-Project Linking | Makes everything else useful | All |
| **#3** | Weekly Proposal Report | Automated status, no manual work | Bill |
| **#4** | Invoice Tracking | Cash flow visibility | Bill/Finance |
| **#5** | RFI System | Deadline tracking, accountability | PMs |
| **#6** | Meeting Transcription | Context capture | All |

---

## Phase 1: Operations Layer (Now - Q1 2026)

### 1.1 Proposal Dashboard (January 2026)

**Goal:** Bill opens dashboard Monday morning, sees exactly what needs attention.

```
DELIVERABLES
────────────
[x] proposals table with all fields
[x] /api/proposals/stats endpoint
[ ] Dashboard UI showing:
    [ ] Proposals by status (pie chart)
    [ ] Proposals needing follow-up (14+ days)
    [ ] Recently sent proposals
    [ ] Win/loss metrics
[ ] Status filters (sent, negotiating, won, lost)
[ ] Quick actions (mark won, mark lost, create follow-up)
[ ] Last contact date tracking
```

**Success Metric:** Bill can answer "what proposals need attention?" in <30 seconds.

### 1.2 Email Linking (January 2026)

**Goal:** Emails automatically linked to correct projects/proposals.

```
DELIVERABLES
────────────
[x] Email sync working (3,700+ emails)
[x] Pattern-first linker
[x] 341 learned patterns
[ ] 80%+ emails auto-linked (currently ~65%)
[ ] Suggestion review queue in dashboard
[ ] Bulk approve/reject interface
[ ] Pattern management UI (view, edit, delete patterns)
```

**Success Metric:** New emails from known contacts auto-link within 5 minutes.

### 1.3 Weekly Proposal Report (January 2026)

**Goal:** Auto-generated report every Monday, no manual compilation.

```
DELIVERABLES
────────────
[ ] Scheduled script (Monday 7am)
[ ] Report includes:
    [ ] New proposals sent last week
    [ ] Proposals won/lost
    [ ] Stale proposals (no response 14+ days)
    [ ] Total pipeline value
    [ ] Win rate trends
[ ] Email report to Bill
[ ] Archive reports for history
```

**Success Metric:** Report lands in Bill's inbox Monday morning, zero manual work.

### 1.4 Draft-Ready Follow-ups (February 2026)

**Goal:** AI drafts follow-up emails for stale proposals.

```
DELIVERABLES
────────────
[ ] Identify proposals needing follow-up (7, 14, 21 days)
[ ] AI generates draft follow-up email
[ ] Draft stored in suggestions queue
[ ] One-click approve & send
[ ] Track when follow-ups were sent
[ ] Learn from edits to improve future drafts
```

**Success Metric:** Follow-up drafts ready for review, 2-minute approval process.

### 1.5 Invoice Tracking (February 2026)

**Goal:** Real-time visibility into what's owed and what's overdue.

```
DELIVERABLES
────────────
[x] invoices table with payment tracking
[ ] Dashboard widget: total outstanding
[ ] Aging report (30/60/90 days)
[ ] Per-project invoice history
[ ] Payment received logging
[ ] Overdue alerts
[ ] Draft payment reminder emails
```

**Success Metric:** "What's outstanding?" answered instantly with exact numbers.

### 1.6 RFI Tracking System (March 2026)

**Goal:** No RFI falls through the cracks, all deadlines tracked.

```
DELIVERABLES
────────────
[ ] Set up rfi@bensley.com email channel
[ ] Auto-create RFI ticket from email
[ ] Assign to PM with deadline
[ ] Dashboard: open RFIs by project
[ ] Deadline alerts (72h, 48h, 24h)
[ ] Response logging and closure
[ ] Average response time metrics
```

**Success Metric:** Zero RFIs >5 days without response.

---

## Phase 2: Project Knowledge Layer (Q2 2026)

### 2.1 Project Status View

**Goal:** Complete picture of any project in one view.

```
DELIVERABLES
────────────
[ ] Project detail page with:
    [ ] Basic info (code, name, client, status)
    [ ] All linked emails (timeline)
    [ ] All invoices and payment status
    [ ] All RFIs (open and closed)
    [ ] All meetings (linked transcripts)
    [ ] Team members and roles
    [ ] Key documents
[ ] Project health score (calculated)
[ ] Timeline visualization
```

### 2.2 Meeting Transcription

**Goal:** Meetings automatically transcribed, summarized, and linked.

```
DELIVERABLES
────────────
[ ] Audio upload interface (or OneDrive watch)
[ ] Whisper transcription (local or API)
[ ] AI summary generation
[ ] Action item extraction
[ ] Auto-link to project
[ ] Searchable transcript archive
```

### 2.3 Document Linking

**Goal:** Proposals, contracts, drawings linked to projects.

```
DELIVERABLES
────────────
[ ] OneDrive/SharePoint integration
[ ] Document indexing (PDF, Word, Excel)
[ ] Auto-link based on project code in filename
[ ] Document type classification
[ ] Version tracking for proposals/contracts
```

---

## Phase 3: Intelligence Layer (Q3-Q4 2026)

### 3.1 Semantic Search

**Goal:** Find anything by meaning, not just keywords.

```
DELIVERABLES
────────────
[ ] Vector embeddings for emails
[ ] Vector embeddings for documents
[ ] "Find similar projects" feature
[ ] "What did we discuss about X?" queries
[ ] ChromaDB integration
```

### 3.2 AI Query Interface

**Goal:** Ask questions in plain English, get answers.

```
DELIVERABLES
────────────
[ ] Natural language query input
[ ] Context retrieval from database
[ ] Claude/GPT generates answer with citations
[ ] Query history and favorites
[ ] Slack/Teams integration (optional)
```

### 3.3 Proactive Alerts

**Goal:** System notifies you before problems happen.

```
DELIVERABLES
────────────
[ ] Stale proposal alerts
[ ] Overdue invoice alerts
[ ] RFI deadline alerts
[ ] Scope creep detection
[ ] Payment pattern anomalies
[ ] Configurable alert preferences
```

---

## Phase 4: Local AI (2027)

### 4.1 Ollama Integration

**Goal:** Run AI locally for speed, privacy, and cost savings.

```
DELIVERABLES
────────────
[ ] Ollama installed and configured
[ ] Tiered model routing (small→medium→cloud)
[ ] Local model for categorization
[ ] Local model for simple drafts
[ ] Cloud fallback for complex tasks
[ ] Cost tracking and comparison
```

### 4.2 Model Fine-Tuning

**Goal:** Custom model trained on Bensley data.

```
PREREQUISITES
─────────────
[ ] 10,000+ approved suggestions collected
[ ] Training data prepared and cleaned
[ ] Hardware acquired (Mac with 64GB+ RAM or cloud GPU)

DELIVERABLES
────────────
[ ] LoRA fine-tuning on Llama 3
[ ] Evaluation against base model
[ ] Bensley-specific terminology recognition
[ ] Deploy as "bensley-brain" model in Ollama
```

---

## Phase 5: Future Vision (2027+)

### 5.1 Creative Archive (ESCAPISM)
- Digitize and index 40 years of design work
- Image recognition for auto-tagging
- Visual similarity search
- "Show me water features from Bali projects"

### 5.2 External Integrations
- Instagram analytics
- Google Analytics
- QuickBooks/Xero
- DocuSign
- Calendar integration

### 5.3 Bensley Philosophy Layer
- Design principles documentation
- Style guide enforcement
- "Is this design Bensley enough?"

---

## What's Complete

| Item | Completed | Notes |
|------|-----------|-------|
| Email sync (lukas@) | Dec 2025 | 3,700+ emails, hourly cron |
| Pattern-first linker | Dec 2025 | 341 patterns learned |
| Batch suggestion system | Dec 2025 | 48 batches processed |
| Frontend build fixes | Dec 2025 | Next.js 15 working |
| /api/proposals/stats | Dec 2025 | Real data returned |
| Date normalization | Dec 2025 | All ISO format |
| Duplicate link cleanup | Dec 2025 | 266 removed |

---

## What's Connected

| Source | Status | Records |
|--------|--------|---------|
| lukas@bensley.com | Active | 3,727 emails |
| Voice memos | Manual | 39 transcripts |
| proposals@ | Not connected | - |
| projects@ | Not connected | - |
| invoices@ | Not connected | - |
| rfi@ | Not created | - |

---

## Success Metrics

### January 2026
| Metric | Target | Current |
|--------|--------|---------|
| Proposal dashboard working | Yes | No |
| Email auto-link rate | 80% | ~65% |
| Weekly report automated | Yes | No |
| Bill using dashboard | Daily | Not yet |

### Q1 2026
| Metric | Target | Current |
|--------|--------|---------|
| Time to answer status question | <30 sec | 30+ min |
| Proposals with last_contact | 100% | ~70% |
| Invoice tracking live | Yes | Partial |
| RFI tracking live | Yes | No |

### Q2 2026
| Metric | Target | Current |
|--------|--------|---------|
| Project status view complete | Yes | No |
| Meeting transcripts linked | 50+ | 39 |
| PMs using system | 2+ | 0 |
| Draft approval rate | >80% | N/A |

---

## Quick Reference

### Run the System
```bash
# Backend
cd backend && uvicorn api.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev

# Email sync (manual)
python scripts/core/scheduled_email_sync.py
```

### Key Files
| Purpose | Location |
|---------|----------|
| Email sync | `scripts/core/scheduled_email_sync.py` |
| Pattern matching | `backend/services/pattern_first_linker.py` |
| Learning | `backend/services/learning_service.py` |
| Suggestions | `backend/services/context_aware_suggestion_service.py` |
| API routes | `backend/api/routers/*.py` |
| Database | `database/bensley_master.db` |

### Branch Naming
```
fix/short-desc-ISSUE#    # Bug fixes
feat/short-desc-ISSUE#   # New features
chore/short-desc-ISSUE#  # Cleanup/refactor
```

---

## Agent Rules (Enforced)

1. **Never auto-link emails** - Create suggestions for human review
2. **Always include project name** - "25 BK-033 (Ritz-Carlton Nusa Dua)"
3. **Test before committing** - Run code, verify it works
4. **Small commits** - One logical change per commit
5. **Reference issues** - `git commit -m "fix(patterns): tracking #6"`
6. **Update docs** - Next agent needs to know what changed
7. **Don't create random files** - Use existing structure

---

*For the full vision, see [VISION.md](./VISION.md)*
*For technical details, see [TECHNICAL-ARCHITECTURE.md](./TECHNICAL-ARCHITECTURE.md)*
