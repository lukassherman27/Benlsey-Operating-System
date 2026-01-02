# Strategic Audit - January 2026

> Generated: 2026-01-02 | Context: Pre-Production Deployment Planning

---

## EXECUTIVE SUMMARY

**Bottom line:** The system works locally but is bloated. We need to ruthlessly cut unused code, consolidate to 5-6 core pages, and deploy to production for real testing.

**Stats:**
- 154 database tables (should be ~30)
- 37 frontend pages (should be ~8)
- 38 API routers (should be ~12)
- 23 open issues (need triage)

---

## SECTION 1: WHAT'S ACTUALLY USED vs DEAD CODE

### Core Features (KEEP & POLISH)

| Feature | Status | Users | Files |
|---------|--------|-------|-------|
| **Proposals Dashboard** | Working | Bill | `/proposals`, `/tracker` |
| **Executive Dashboard** | NEW | Bill/Brian | `/executive` |
| **Email Linking** | Working | Lukas | Pattern linker + suggestions |
| **Suggestion Review** | Working | Lukas | `/suggestions` |
| **Projects List** | Basic | PMs | `/projects` |
| **Contacts** | Basic | All | `/contacts` |
| **Pattern Admin** | Working | Lukas | `/admin/patterns` |

### Questionable Features (AUDIT NEEDED)

| Feature | Used? | Recommendation |
|---------|-------|----------------|
| `/transcripts` | 39 records, rarely used | KEEP but hide from nav |
| `/recorder` | Never used? | REMOVE or hide |
| `/query` | NLQ - not working? | PHASE 3 - hide |
| `/analytics` | Charts exist? | CONSOLIDATE into dashboard |
| `/rfis` | 0 RFIs | KEEP but low priority |
| `/meetings` | 7 meetings | KEEP - will grow |
| `/tasks` | 41 tasks | KEEP - PM priority |
| `/deliverables` | EMPTY? | PM priority |
| `/emails/intelligence` | Unused | REMOVE |
| `/emails/links` | Duplicate of suggestions? | CONSOLIDATE |
| `/admin/*` (8 pages) | Lukas only | CONSOLIDATE to 2-3 |

### Database Table Bloat

**Tables to KEEP (Core):**
```
emails, proposals, projects, contacts, invoices, staff
meetings, tasks, deliverables, rfis
ai_suggestions, email_learned_patterns
email_proposal_links, email_project_links
```

**Tables to AUDIT (Possibly Dead):**
```
batch_emails, proposal_embeddings, document_embeddings, email_embeddings
training_data, training_feedback, training_data_feedback
low_confidence_log, low_confidence_review_view
suggestion_batches, suggestion_changes, suggestion_tags
50+ views (v_*) - many likely unused
```

---

## SECTION 2: PAGE CONSOLIDATION PLAN

### Target Navigation (8 Pages)

```
SIDEBAR NAVIGATION
──────────────────
📊 Dashboard (executive view)     → /executive
📋 Proposals                      → /proposals
🏗️ Projects                       → /projects
👥 Contacts                       → /contacts
💰 Finance                        → /finance
📧 Emails (review queue)          → /suggestions (renamed)
⚙️ Admin (patterns, data)         → /admin
👤 Profile/Settings               → /settings
```

### Pages to REMOVE or HIDE

```
REMOVE (dead code):
- /emails/intelligence
- /recorder
- /system (empty?)

HIDE (future phases):
- /query → Phase 3
- /analytics → Merge into dashboard
- /transcripts → Hide in nav, keep route

CONSOLIDATE:
- /tracker + /proposals → single /proposals with tabs
- /emails/* → single /suggestions with filters
- /admin/* → single /admin with tabs
```

---

## SECTION 3: DEPLOYMENT PLAN

### Infrastructure Options

| Option | Cost | Pros | Cons |
|--------|------|------|------|
| **Vercel + PlanetScale** | ~$50/mo | Easy, scalable, Next.js optimized | DB migration needed |
| **Railway** | ~$20/mo | Simple, SQLite works | Less mature |
| **DigitalOcean Droplet** | ~$24/mo | Full control, SQLite native | More DevOps |
| **Azure (Bensley existing?)** | Varies | Corporate IT aligned | Complex setup |

### Recommended: Vercel + Railway

```
ARCHITECTURE
────────────
┌─────────────┐     ┌─────────────┐
│   Vercel    │────▶│   Railway   │
│  (Frontend) │     │  (Backend)  │
└─────────────┘     └─────────────┘
       │                   │
       │                   ▼
       │            ┌─────────────┐
       │            │   SQLite    │
       │            │  (Railway)  │
       │            └─────────────┘
       │
       ▼
┌─────────────┐
│  OneDrive   │
│   (Files)   │
└─────────────┘
```

### Pre-Deployment Checklist

```
[ ] Environment variables setup (BENSLEY_DB_PATH, API keys)
[ ] HTTPS/TLS configured
[ ] Authentication tested (NextAuth)
[ ] CORS configured for production domains
[ ] Database backup/restore tested
[ ] Error monitoring (Sentry - Issue #211)
[ ] Health check endpoint working
[ ] Rate limiting on API
[ ] File upload limits configured
```

---

## SECTION 4: AI ENGINEERING PRINCIPLES

### Applying Research to Our System

#### 1. Recursive Logic Loop (Claude Pattern)
**What it means:** Self-improving through feedback loops
**Our implementation:**
- Pattern linker learns from approved suggestions ✅
- Missing: Feedback on rejected suggestions improving future outputs

#### 2. Context Architect Framing
**What it means:** Structured context windows for optimal reasoning
**Our implementation:**
- Email analysis passes project context, recent emails, patterns ✅
- Missing: Better chunking of long email threads

#### 3. Pre-computation Behavior
**What it means:** Compute expensive things ahead of time
**Our implementation:**
- Patterns cached for 5 min ✅
- Missing: Pre-compute "needs attention" items on schedule

#### 4. Internal Playbook Evolution
**What it means:** Codified rules that improve over time
**Our implementation:**
- CONFIDENCE_THRESHOLDS in suggestion_writer ✅
- Missing: Auto-adjust thresholds based on approval rates

#### 5. RAG Hit Rate with LLM as Judge
**What it means:** Measure retrieval quality, not just existence
**Our implementation:**
- We track times_used, times_correct, times_rejected ✅
- Missing: Automated quality scoring of pattern matches

#### 6. Human-in-the-Loop (HITL)
**What it means:** Strategic human review at decision points
**Our implementation:**
- Suggestion review queue ✅
- Missing: Confidence-based routing (high conf = auto-approve)

### Proposed Improvements

```python
# 1. Auto-approve high-confidence suggestions
if suggestion.confidence >= 0.95 and pattern.times_correct >= 10:
    auto_approve(suggestion)

# 2. Threshold evolution
def adjust_thresholds():
    for type in CONFIDENCE_THRESHOLDS:
        approval_rate = get_approval_rate(type, last_30_days)
        if approval_rate < 0.5:
            CONFIDENCE_THRESHOLDS[type] += 0.05  # Raise bar
        elif approval_rate > 0.9:
            CONFIDENCE_THRESHOLDS[type] -= 0.02  # Lower bar slightly

# 3. Pre-compute needs attention (cron job)
def precompute_attention_items():
    # Run daily at 6am
    items = compute_all_attention_items()
    cache.set("needs_attention", items, ttl=3600)
```

---

## SECTION 5: OPEN ISSUES TRIAGE

### P0 - Critical (Do Now)

| Issue | What | Action |
|-------|------|--------|
| #308 | 33 orphaned invoice_aging | Run cleanup script |
| #307 | 47 duplicate invoices | Dedupe + investigate |
| #309 | PM System Epic | Break into sub-tasks |

### P1 - High (This Week)

| Issue | What | Action |
|-------|------|--------|
| #311 | Daily work collection | PM feature, define MVP |
| #312 | Weekly scheduling UI | PM feature, define MVP |
| #313 | Deliverables CRUD | PM feature, table exists |

### P2 - Medium (This Month)

| Issue | What | Action |
|-------|------|--------|
| #314 | Meeting → Task pipeline | Nice to have |
| #210 | Gantt chart | Phase 2 |
| #209 | Calendar integration | Phase 2 |

### Backlog (Later Phases)

| Issue | What | Phase |
|-------|------|-------|
| #198 | Vector embeddings | Phase 3 |
| #199 | AI query interface | Phase 3 |
| #200 | Proactive alerts | Phase 3 |
| #201-203 | Local AI / Fine-tune | Phase 4 |

### Should Close (Stale or Done)

| Issue | Why |
|-------|-----|
| #214 | Data linking reference - doc task, not code |
| #151 | UI library research - done (using shadcn) |
| #22 | OneDrive cleanup - out of scope for this system |
| #60 | $0.9M invoices - business review, not code |
| #205 | Research agent - meta/ongoing, not actionable |

---

## SECTION 6: RECOMMENDED NEXT ACTIONS

### This Session

1. **Close stale issues** (#214, #151, #22 → convert to docs or close)
2. **Fix P0 data quality** (#307, #308 → run cleanup scripts)
3. **Create deployment checklist issue**
4. **Update roadmap.md with current state**

### This Week

1. **Page consolidation** - Remove/hide unused pages
2. **Navigation cleanup** - 8 pages max
3. **Database table audit** - Document which tables are dead
4. **Smoke test all core features**

### Before Go-Live

1. **Deployment infrastructure chosen**
2. **Environment variables documented**
3. **Backup/restore tested**
4. **Bill/Brian user testing session**
5. **Authentication flow verified**

---

## SECTION 7: QUICK WINS

Things that can be done in <30 minutes each:

```
[ ] Add "last_synced" timestamp to dashboard
[ ] Fix proposal quick actions if broken
[ ] Add keyboard shortcuts to suggestion review (j/k/a/r)
[ ] Pre-fill follow-up email templates
[ ] Add "Copy project code" button
[ ] Collapse admin pages into single page with tabs
[ ] Remove /recorder, /emails/intelligence routes
[ ] Update navigation to match 8-page structure
```

---

## APPENDIX: File Counts

```
Frontend Pages:     37 → Target: 8
Backend Routers:    38 → Target: 12
Backend Services:   30+ → Target: 15
Scripts:            40+ → Archive unused
Database Tables:    154 → Target: 40
```

---

## SECTION 8: ROLE-BASED VIEWS (What Each User Sees)

### Finance Lady
```
SEES:
├── Invoices (all)
│   ├── Outstanding / overdue
│   ├── When to send next invoice
│   └── Payment tracking
├── Proposals (read-only, for reference)
├── Signed Contracts (organized, searchable)
└── Reminders
    ├── "Invoice 25 BK-087 - 30 days since last"
    └── "Follow up on overdue payment"

DOESN'T SEE:
- Email linking, suggestions
- Design files, team management
- Admin/patterns
```

### Project Managers (Astuti, Brian K)
```
SEES:
├── Their Projects Only
│   ├── Team members
│   ├── Deliverables + due dates
│   ├── Meetings
│   └── Project emails
├── Their Tasks
├── Their Schedule
└── RFIs (assigned to them)

DOESN'T SEE:
- Other PM's projects
- Finance/invoices
- Proposals (unless assigned)
- Admin
```

### Executives (Bill Bensley, Brian Sherman)
```
SEES:
├── Executive Dashboard (high-level)
├── All Proposals + Pipeline
├── All Projects (overview)
├── Finance Summary
└── "Needs Attention" items

DOESN'T SEE:
- Admin/technical stuff
- Email linking details
- Pattern management
```

### Admin (Lukas)
```
SEES:
└── Everything
    ├── All data
    ├── Admin pages
    ├── Pattern management
    ├── Suggestions queue
    └── System config
```

### Implementation Notes
- Backend RBAC exists (`require_role()` in dependencies.py)
- Frontend needs role-based routing
- Each role = different default landing page
- Sidebar navigation changes per role

---

## SECTION 9: AGENT WORKFLOW (v3.0 Template)

All agents follow the 5-phase workflow from `.claude/prompts/TEMPLATE-v3.md`:

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: UNDERSTAND                                        │
│  - Read relevant files (DON'T code yet)                     │
│  - Run research commands                                    │
│  - Answer specific questions                                │
│  **STOP HERE** until you understand the current state       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: THINK HARD                                        │
│  - Design decisions & alternatives                          │
│  - Web research if needed                                   │
│  - Write explicit plan (1, 2, 3...)                         │
│  **Think through edge cases**                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: IMPLEMENT                                         │
│  - Follow the plan step by step                             │
│  - Use TodoWrite to track progress                          │
│  - Modify only necessary files                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 4: VERIFY                                            │
│  - Run tests/build                                          │
│  - Check against success criteria                           │
│  - Fix any issues found                                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 5: COMPLETE                                          │
│  - Commit with proper message                               │
│  - Create PR                                                │
│  - Cross-check other open issues                            │
└─────────────────────────────────────────────────────────────┘
```

### Key Principles (From Anthropic Research)

| Principle | What It Means | How We Apply |
|-----------|---------------|--------------|
| **Research First** | Read files before coding | Phase 1 mandatory |
| **Think Hard** | Explicit planning step | Phase 2 with plan |
| **Ground Truth** | Environment feedback | Tests, builds, type checks |
| **Verification Loops** | Test your work | Phase 4 before commit |
| **Context Management** | Keep prompts focused | Specific files + questions |

### Anti-Patterns

```
❌ Jumping straight to code (skip Phase 1)
❌ Vague instructions ("fix the thing")
❌ No verification commands
❌ Missing success criteria
❌ Over-constraining the agent
```

---

*Next update: After deployment infrastructure decision*
