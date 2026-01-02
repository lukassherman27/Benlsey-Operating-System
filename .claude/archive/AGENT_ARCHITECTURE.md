# Bensley Multi-Agent Architecture

## The Big Picture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA PIPELINE AGENTS                               │
│  (Run automatically - hourly/daily)                                         │
│                                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ IMPORTER │ →→ │ LINKER   │ →→ │SUGGESTER │ →→ │ LEARNER  │              │
│  │          │    │          │    │          │    │          │              │
│  │ Fetch    │    │ Match    │    │ Create   │    │ Extract  │              │
│  │ emails   │    │ emails   │    │ review   │    │ patterns │              │
│  │ from     │    │ to       │    │ queue    │    │ from     │              │
│  │ Gmail    │    │ proposals│    │ items    │    │ feedback │              │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
│       ↓               ↓               ↓               ↓                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         SQLITE DATABASE                              │   │
│  │  emails → email_proposal_links → ai_suggestions → learned_patterns   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HUMAN REVIEW LAYER                                   │
│  (Bill/Lukas reviews in browser)                                            │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Frontend: localhost:3002/admin/suggestions                          │  │
│  │                                                                       │  │
│  │  "Link john@client.com to 25 BK-045?"     [Approve] [Reject] [Edit]  │  │
│  │  "Update status to Proposal Sent?"        [Approve] [Reject] [Edit]  │  │
│  │  "New contact: Sarah Kim, Developer?"     [Approve] [Reject] [Edit]  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    ↓                                        │
│                          feedback saved to DB                               │
│                                    ↓                                        │
│                    LEARNER agent extracts patterns                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INTELLIGENCE AGENTS                                  │
│  (Run on-demand or scheduled)                                               │
│                                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ FOLLOW-UP│    │ PAYMENT  │    │ HEALTH   │    │ BRIEFING │              │
│  │ DETECTOR │    │ TRACKER  │    │ SCORER   │    │ WRITER   │              │
│  │          │    │          │    │          │    │          │              │
│  │ Find     │    │ Find     │    │ Calculate│    │ Generate │              │
│  │ proposals│    │ overdue  │    │ proposal │    │ daily    │              │
│  │ needing  │    │ invoices │    │ health   │    │ summary  │              │
│  │ follow-up│    │ & alerts │    │ scores   │    │ for Bill │              │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BUILDER AGENTS                                       │
│  (Human-directed, build features)                                           │
│                                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ FRONTEND │    │ BACKEND  │    │ DATA ENG │    │ AUDITOR  │              │
│  │ BUILDER  │    │ BUILDER  │    │          │    │          │              │
│  │          │    │          │    │          │    │          │              │
│  │ React    │    │ FastAPI  │    │ SQL      │    │ Find     │              │
│  │ components│   │ endpoints│    │ migrations│   │ bugs     │              │
│  │ & pages  │    │ & services│   │ & scripts│    │ & issues │              │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Data Pipeline Agents (Automated)

These run on schedule. No human needed. Pure Python scripts.

### Agent 1A: IMPORTER
**When:** Every hour via cron
**What:** Fetches new emails from Gmail API
**Script:** `scripts/core/scheduled_email_sync.py`

```python
# Already exists! Just needs to run on schedule
# crontab -e
# 0 * * * * cd /path/to/project && python scripts/core/scheduled_email_sync.py
```

**Input:** Gmail API
**Output:** New rows in `emails` table

---

### Agent 1B: LINKER
**When:** After import completes
**What:** Matches emails to proposals (NO API calls - pure SQL/Python)
**Script:** `scripts/core/email_linker.py` (exists but needs cleanup)

```python
# Pattern matching hierarchy (no GPT needed):
def link_email(email):
    # 1. Project code in subject/body (regex)
    if match := re.search(r'\d{2}\s*BK-\d{3}', email.subject + email.body):
        return link_by_code(match.group(), confidence=0.95)

    # 2. Sender matches proposal contact_email
    if proposal := find_proposal_by_contact_email(email.sender):
        return link_to_proposal(proposal, confidence=0.90)

    # 3. Sender domain matches learned pattern
    if pattern := find_learned_pattern(email.sender_domain):
        return link_to_proposal(pattern.proposal_id, confidence=pattern.confidence)

    # 4. No match - create suggestion for human review
    return create_link_suggestion(email)
```

**Input:** Unlinked emails
**Output:** `email_proposal_links` rows OR `ai_suggestions` rows

---

### Agent 1C: SUGGESTER
**When:** After linking completes
**What:** Creates human-reviewable suggestions for uncertain matches
**Script:** `backend/services/suggestion_writer.py` (exists)

```python
# Types of suggestions it creates:
SUGGESTION_TYPES = [
    'email_link',           # "Link this email to 25 BK-045?"
    'contact_link',         # "Add john@client.com to 25 BK-045 contacts?"
    'proposal_status_update', # "Update status to Proposal Sent?"
    'new_contact',          # "Create contact: John Smith?"
    'new_proposal',         # "Create proposal for this inquiry?"
]
```

**Input:** Uncertain matches from Linker
**Output:** `ai_suggestions` rows with status='pending'

---

### Agent 1D: LEARNER
**When:** After human reviews suggestions
**What:** Extracts patterns from approved/rejected suggestions
**Script:** `backend/services/ai_learning_service.py` (exists)

```python
# When human approves "Link john@clientcorp.com to 25 BK-045":
def learn_from_approval(suggestion):
    # Extract pattern
    domain = extract_domain(suggestion.email)  # "clientcorp.com"
    proposal = suggestion.proposal_id

    # Save pattern
    save_pattern({
        'pattern_type': 'domain_to_proposal',
        'pattern_value': domain,
        'proposal_id': proposal,
        'confidence': 0.85,
        'learned_from': f'suggestion_{suggestion.id}'
    })

    # Next time: emails from clientcorp.com auto-link to 25 BK-045
```

**Input:** Approved/rejected suggestions
**Output:** `email_learned_patterns` rows

---

## Layer 2: Human Review (The Feedback Loop)

This is where Bill/Lukas review suggestions in the browser.

### The Review Queue

**URL:** `localhost:3002/admin/suggestions`

```
┌─────────────────────────────────────────────────────────────────────┐
│  AI Suggestions (23 pending)                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ EMAIL LINK                                        85% conf   │   │
│  │                                                              │   │
│  │ Link email from john.kim@samsung.com                         │   │
│  │ Subject: "Re: Busan Hotel Landscape"                         │   │
│  │ To: 25 BK-045 (Busan Marriott)                              │   │
│  │                                                              │   │
│  │ Reason: Sender domain matches 3 other linked emails          │   │
│  │                                                              │   │
│  │ [✓ Approve]  [✗ Reject]  [✎ Edit]  [Skip]                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ STATUS UPDATE                                     90% conf   │   │
│  │                                                              │   │
│  │ Update 25 BK-071 (Wangsimni Tower)                          │   │
│  │ From: "Proposal Prep" → "Proposal Sent"                      │   │
│  │                                                              │   │
│  │ Evidence: Found proposal PDF attached to sent email          │   │
│  │ Email date: 2025-12-08                                       │   │
│  │                                                              │   │
│  │ [✓ Approve]  [✗ Reject]  [✎ Edit]  [Skip]                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### The Feedback Loop

```
Human clicks [Approve]
       ↓
suggestion.status = 'approved'
       ↓
Handler applies the change (email_link_handler.py, etc.)
       ↓
LEARNER agent extracts pattern
       ↓
Pattern saved to email_learned_patterns
       ↓
Next similar email auto-links (no human needed)
```

### Learning in Action

**Week 1:**
- 100 emails come in
- 60 need human review
- Human approves 50 link suggestions

**Week 2:**
- 100 emails come in
- 40 need human review (20 auto-linked by patterns)
- Human approves 35

**Week 4:**
- 100 emails come in
- 15 need human review (85 auto-linked)
- System is learning!

---

## Layer 3: Intelligence Agents (Insights)

These analyze the data and surface actionable insights.

### Agent 3A: FOLLOW-UP DETECTOR
**When:** Daily at 8am
**What:** Finds proposals needing follow-up

```python
# scripts/core/detect_follow_ups.py
def find_stale_proposals():
    return db.query("""
        SELECT p.project_code, p.project_name, p.contact_email,
               p.status, p.last_contact_date,
               julianday('now') - julianday(p.last_contact_date) as days_silent
        FROM proposals p
        WHERE p.status IN ('Proposal Sent', 'Negotiation', 'Meeting Held')
          AND julianday('now') - julianday(p.last_contact_date) > 14
        ORDER BY days_silent DESC
    """)

# Output: list of proposals for daily briefing
```

---

### Agent 3B: PAYMENT TRACKER
**When:** Daily at 9am
**What:** Finds overdue invoices, alerts

```python
# scripts/core/detect_overdue.py
def find_overdue_invoices():
    return db.query("""
        SELECT i.invoice_number, i.project_code, p.project_name,
               i.amount_usd, i.due_date,
               julianday('now') - julianday(i.due_date) as days_overdue
        FROM invoices i
        JOIN projects p ON i.project_code = p.project_code
        WHERE i.status = 'sent'
          AND julianday('now') > julianday(i.due_date)
        ORDER BY days_overdue DESC
    """)
```

---

### Agent 3C: HEALTH SCORER
**When:** After every email sync
**What:** Calculates proposal health scores

```python
# backend/services/health_scorer.py
def calculate_health(proposal):
    score = 100

    # Deduct for silence
    days_silent = days_since_contact(proposal)
    if days_silent > 7: score -= 10
    if days_silent > 14: score -= 20
    if days_silent > 30: score -= 30

    # Deduct for stuck status
    days_in_status = days_since_status_change(proposal)
    if days_in_status > 30: score -= 15

    # Boost for recent activity
    if days_silent < 3: score += 10

    return max(0, min(100, score))
```

---

### Agent 3D: BRIEFING WRITER
**When:** Daily at 7am
**What:** Generates Bill's daily briefing

```python
# scripts/core/generate_daily_briefing.py
def generate_briefing():
    return f"""
    # Daily Briefing - {today}

    ## Needs Attention (5)
    - 25 BK-045 Busan Marriott: 18 days silent, was in Negotiation
    - 25 BK-071 Wangsimni: Proposal sent 14 days ago, no response
    ...

    ## Payments Overdue (2)
    - 24 BK-089 Shinta Mani: $45,000 - 12 days overdue
    ...

    ## Won This Week (1)
    - 25 BK-092 Vahine Island: Contract signed Dec 8

    ## Pipeline Summary
    - Active proposals: 50
    - Total value: $4.2M
    - Avg health score: 67
    """
```

---

## Layer 4: Builder Agents (Human-Directed)

These are Claude sessions directed by you to build features.

### Agent 4A: FRONTEND BUILDER
**Scope:** React components, pages, UI
**Constraints:**
- Only touches `frontend/src/`
- Must run `npm run build` before done
- Updates types.ts when adding API calls

**Example Task:**
```
"Add a payment tracking widget to the dashboard that shows:
- Overdue invoices count
- Total outstanding amount
- List of top 5 overdue with days late"
```

---

### Agent 4B: BACKEND BUILDER
**Scope:** FastAPI endpoints, services
**Constraints:**
- Only touches `backend/`
- Must test endpoints with curl before done
- Updates API docs when adding endpoints

**Example Task:**
```
"Add endpoint GET /api/invoices/overdue that returns
invoices past due date, sorted by days overdue"
```

---

### Agent 4C: DATA ENGINEER
**Scope:** Database migrations, data fixes
**Constraints:**
- Always backup before changes
- Only touches `database/` and `scripts/`
- Verifies with SQL queries after

**Example Task:**
```
"Backfill last_contact_date on all proposals
based on actual email dates"
```

---

### Agent 4D: AUDITOR
**Scope:** Finding bugs, data issues
**Constraints:**
- Read-only (doesn't fix, just reports)
- Outputs structured report
- Tests everything it claims

**Example Task:**
```
"Find all broken API endpoints and data quality issues"
```

---

## The Coordination Protocol

### How It All Fits Together

```
AUTOMATED (runs without human):
├── Hourly: IMPORTER → LINKER → SUGGESTER
├── Daily 7am: BRIEFING WRITER
├── Daily 8am: FOLLOW-UP DETECTOR
├── Daily 9am: PAYMENT TRACKER
└── After approvals: LEARNER

HUMAN REVIEW (Bill/Lukas in browser):
└── Anytime: Review suggestions at /admin/suggestions

HUMAN DIRECTED (Claude sessions):
└── As needed: BUILDER agents for new features
```

### State Management

**File: `.claude/STATE.md`** (Updated by builder agents only)

```markdown
# Builder State

## Current Sprint
Payment tracking dashboard

## Last Session
- Agent: Frontend Builder
- Did: Created PaymentWidget component
- Verified: npm build passes
- Remaining: Connect to API endpoint

## Next Session
- Agent: Backend Builder
- Task: Create /api/invoices/overdue endpoint
- Then: Frontend Builder connects widget to endpoint

## Blockers
None
```

### The Review Queue is the Coordination Point

The key insight: **The suggestion queue IS your coordination layer.**

- Automated agents create suggestions
- Humans review suggestions
- Learner extracts patterns
- System improves

You don't need complex agent-to-agent communication. The database IS the communication channel.

---

## Implementation Plan

### Phase 1: Fix the Pipeline (Week 1)

1. **Fix LINKER** - Remove GPT calls, use pure pattern matching
2. **Fix LEARNER** - Actually extract patterns from approvals
3. **Clean suggestion queue** - Reject 71 stuck suggestions
4. **Fix handlers** - Match VALID_STATUSES to database

### Phase 2: Add Intelligence (Week 2)

5. **Add FOLLOW-UP DETECTOR** - Daily script
6. **Add PAYMENT TRACKER** - Daily script
7. **Add BRIEFING WRITER** - Daily email/dashboard
8. **Add HEALTH SCORER** - Real-time calculation

### Phase 3: Improve Review UI (Week 3)

9. **Batch approval** - Approve 10 similar suggestions at once
10. **Better context** - Show email thread in review
11. **Quick filters** - By type, confidence, project
12. **Keyboard shortcuts** - A=approve, R=reject, S=skip

### Phase 4: Analytics Dashboard (Week 4)

13. **Pipeline health** - Emails/day, suggestions/day, approval rate
14. **Proposal funnel** - Conversion by stage
15. **Payment aging** - Outstanding by client/project
16. **Follow-up queue** - Prioritized list

---

## What This Gets You

### Before (Current)
- Emails pile up, manually sorted
- Don't know what needs follow-up
- Payment tracking in spreadsheets
- Each Claude session starts fresh
- 71 stuck suggestions nobody handles

### After (This Architecture)
- Emails auto-categorized, auto-linked
- Daily briefing highlights attention needed
- Payment alerts automatic
- Builder agents have clear state
- Suggestion queue is clean, learning works

### The Learning Flywheel

```
More emails processed
       ↓
More suggestions created
       ↓
Human reviews suggestions
       ↓
Patterns extracted
       ↓
Better auto-linking
       ↓
Fewer suggestions needed
       ↓
Human spends less time reviewing
       ↓
System handles more emails
       ↓
(cycle continues)
```

---

## Files to Create/Modify

### New Scripts
```
scripts/core/
├── run_pipeline.sh          # Runs importer → linker → suggester
├── detect_follow_ups.py     # Daily follow-up detection
├── detect_overdue.py        # Daily payment tracking
├── generate_briefing.py     # Daily briefing
└── extract_patterns.py      # Learn from approvals
```

### Cron Schedule
```bash
# crontab -e
0 * * * *  cd /project && ./scripts/core/run_pipeline.sh      # Hourly
0 7 * * *  cd /project && python scripts/core/generate_briefing.py
0 8 * * *  cd /project && python scripts/core/detect_follow_ups.py
0 9 * * *  cd /project && python scripts/core/detect_overdue.py
```

### State Files
```
.claude/
├── STATE.md                 # Builder agent state (30 lines max)
├── PIPELINE_LOG.md          # Auto-generated pipeline stats
└── DAILY_BRIEFING.md        # Today's briefing output
```

---

## Key Principles

1. **Database is the message bus** - Agents communicate via tables, not direct calls
2. **Suggestions are the feedback loop** - Everything uncertain goes to human review
3. **Patterns are learned, not coded** - Start with rules, learn exceptions
4. **Builder agents are stateless** - STATE.md is the only memory
5. **Automated agents are dumb** - Just SQL and regex, no GPT needed for pipeline
6. **Intelligence is queries** - Complex insights = complex SQL, not complex code
