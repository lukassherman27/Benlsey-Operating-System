# Agent Handoff

**Updated:** 2025-12-09 (Early AM)

---

## 1. What Is This System?

**BENSLEY Design Studios (BDS)** - World-renowned luxury hospitality design firm, Bangkok.

| Person | Role |
|--------|------|
| **Bill Bensley** | Founder, Creative Director (40+ years) |
| **Brian Petrie** | Director/CEO (30+ years) |
| **Lukas Sherman** | Business Development, Technology |

**This platform is Bill's Personal Operating System** covering:
- **BDS** - Core design business (full tracking)
- **Shinta Mani Hotels** - Bill part-owner (emails, some projects)
- **SM Foundation** - Bill's charity (emails only)
- **Personal** - Investments, art, press (emails only)

**Goal:** "Bensley Brain" - AI that knows everything about the business.

---

## 2. Team Structure

### Leadership
- Bill Bensley - Creative Director
- Brian Petrie - CEO/Director

### Directors/Heads (Each has their own team)
| Name | Discipline |
|------|------------|
| Ouant | Interior |
| Aood | Interior |
| Spot | Architecture |
| Putu | Bali Director |
| Suwit | Architecture |
| Gawow | Architecture |
| Mu | Landscape |

### Disciplines
- Architecture
- Interior Design
- Landscape
- Graphics Design
- Artwork

### Staff
- 98 total team members
- Directors have teams under them

---

## 3. Project Accountability

For each PROJECT + PHASE, we need:
- Point of Contact - Architecture
- Point of Contact - Interior
- Point of Contact - Landscape
- (Graphics, Artwork as needed)

This enables routing tasks to the right person.

---

## 4. Proposal → Project Conversion

```
PROPOSAL                    →    PROJECT
─────────────────────────────────────────
Tracking, negotiating       →    Contract signed (both parties)
                            →    Mobilization invoiced
                            →    Mobilization PAID
                            →    = Active Project

Project code stays the same (e.g., 25 BK-033)
Moves from proposals table to projects table
```

### Timeline Continuity (CRITICAL)
The full history must be preserved:
- When a proposal was created
- All status changes during proposal phase
- When contract was signed
- When it became an active project
- All project phase transitions

**Analytics need:** "Show me the timeline from first contact to active project to completion."

Email links can exist to both proposal AND project - this is fine. The point is having the complete history, not table purity.

---

## 5. Proposal Statuses (Final List)

| Status | Meaning |
|--------|---------|
| **First Contact** | Initial inquiry |
| **Meeting Held** | Had discussions |
| **NDA Signed** | Confidentiality agreed |
| **Proposal Prep** | Writing the proposal |
| **Proposal Sent** | Fee sent, awaiting response |
| **Negotiation** | Active back-and-forth |
| **On Hold** | Client paused |
| **Dormant** | Months of silence (not lost) |
| **Lost** | Went to competitor |
| **Declined** | We said no |
| **Contract Signed** | Won → converts to Project |

---

## 6. Project Phases

| Phase | Code | Notes |
|-------|------|-------|
| Mobilization | MOB | Week 1 |
| Concept Design | CD | 8-10 weeks |
| Schematic Design | SD | Sometimes merged into DD |
| Design Development | DD | |
| Construction Documents | CDocs | (not CD to avoid confusion) |
| Construction Observation | CO | Until end |

**Typical project:** ~3 years, 24-36 month contract term

---

## 7. Email Channels (Planned)

| Account | Purpose | Status |
|---------|---------|--------|
| `lukas@bensley.com` | Proposals, BD, general | ✅ Active |
| `bill@bensley.com` | Bill's inbox | Planned |
| `projects@bensley.com` | Client correspondence (PMs CC this) | This week |
| `invoices@bensley.com` | Payment tracking | Planned |
| `dailywork@bensley.com` | Staff daily submissions | Planned |
| `scheduling@bensley.com` | PM scheduling | Planned |

### How Each Channel Works

**projects@** - PMs CC this on client emails. Clients told to send RFIs here. All correspondence for a project in one place.

**dailywork@** - Staff send daily work + attachments (sketches, renders). Bill/Brian review and comment. Comments become tracked tasks.

**invoices@** - Accountant sends invoices to clients from here. Payment tracking.

**scheduling@** - Internal PM coordination. Mix of internal + external scheduling.

---

## 8. Categorization Strategy

### Layer 1: Primitive Rules (Auto)
- `@bensley.com` → Internal
- Known contact + project mapping → Link to that project
- Email from `projects@` → It's project-related

### Layer 2: AI Suggestions (Within project)
Once linked to a project, AI suggests sub-category:
- RFI
- General correspondence
- Scheduling
- Site visit
- Drawing sharing
- Consultant coordination
- Invoice/payment
- Meeting notes

**Phase 1:** Just get everything into the right PROJECT folder
**Phase 2:** Sub-categorization emerges from AI suggestions

---

## 9. Contact Roles

When mapping a contact to a project:
- Client (owner)
- Client Representative
- External Consultant - Civil
- External Consultant - Structural
- External Consultant - MEP
- Operator (hotel brand)
- Contractor
- Other (AI can suggest new roles)

---

## 10. Data Quality Rules

### 9 Lessons Learned
1. **Always verify FK integrity** - Check MIN/MAX on both sides
2. **Code matching > ID matching** - Project codes are stable, IDs drift
3. **Never auto-link** - Always create suggestions for human review
4. **Staging tables** - Never modify production directly
5. **Keep backups** - 7-day retention before dropping
6. **Chronological processing** - Oldest emails first
7. **Check schema first** - Column names vary between tables
8. **Cancelled projects persist** - Train AI to not link to them
9. **Internal categories** - Use INT-* codes for non-project emails

### Column Name Gotchas
| Table | Column |
|-------|--------|
| ai_suggestions | `suggestion_id` (not id), `description` (not reasoning) |
| emails | `sender_email` (not sender) |
| projects | `project_title` (not project_name) |

---

## 11. Project Code Lookups

| Name/Keyword | Code |
|--------------|------|
| La Vie / Sudha / necklace | 25 BK-037 |
| BKC Mumbai / AuroRealty | 25 BK-047 |
| Daimon Sake / Gaggan | 25 BK-048 |
| Wangsimni / jinny | 25 BK-071 |
| Ritz Carlton Nusa Dua | 25 BK-033 |
| Vahine Island / Taha'a | 25 BK-087 |
| Veyo Utah | 25 BK-069 |
| Manali / Badal | 25 BK-050 |
| Taiwan Taitung | 25 BK-078 |
| Equinox Hotels | 25 BK-043 |
| Wynn Marjan Additional Services | 25 BK-039 |
| Costa Rica Resort | 25 BK-038 |
| Sathorn Private Residence | 25 BK-070 |
| Vietnam High Rise Ultra Luxury | 25 BK-064 |
| Akyn Hospitality Da Lat | 25 BK-063 |

**Bill's Nicknames:**
- "jinny" = Jin Young Kim (Wangsimni)
- "necklace" = Sudha Reddy (La Vie)

---

## 12. Suggestion Review Flow

### Current System (Per-Email)
```
AI processes emails → Creates individual suggestions → Human reviews each
Problem: 400+ suggestions/day is unmanageable
```

### Target System (Batched)
```
AI processes emails
       ↓
Groups by sender/domain (not per-email)
       ↓
Creates BATCH suggestions:
  "joe@veyopool.com → 25 BK-069 (45 emails)"
       ↓
Human approves BATCH (1 click = 45 links)
       ↓
Pattern learned for future
```

### Confidence Tiers
| Confidence | Queue | Action |
|------------|-------|--------|
| >0.90 | Quick Approve | Batch by sender, 1-click approve |
| 0.70-0.90 | Review | Batch with sample emails shown |
| 0.50-0.70 | Individual | One suggestion per email |
| <0.50 | Log Only | No suggestion, pattern discovery |

### Suppressed Suggestion Types
- `link_review` - Deleted (0% approval)
- `proposal_status_update` - Suppressed (10% approval)
- `new_contact` - Threshold raised to 0.85 (was 16% approval at 0.70)
- `follow_up_needed` - Converted to weekly report (was creating 150 individual suggestions)

### Internal Email Filter
- @bensley.com emails DO NOT generate email_link suggestions
- Internal emails are already your records, don't need linking

### Weekly Stale Proposals Report
Instead of 150 individual follow_up_needed suggestions, run:
```bash
python scripts/core/generate_stale_proposals_report.py
```
Outputs a single report with proposals grouped by staleness (90+ days, 30-90 days, etc.)

---

## 13. What Questions Get Asked

### Bill asks:
- "What's the status of [proposal]?"
- "What's the fee for [proposal]?"
- "What's the total fee for active projects?"
- "How much has been paid? Outstanding?"
- "What are the deadlines for [project]?"

### You ask via Claude CLI:
- Proposal status updates
- Follow-up needed (who hasn't responded)
- Weekly scheduling summary
- Project context for meetings

---

## 14. Session Protocol

### When Starting
1. Read `.claude/STATUS.md` for numbers
2. Read `docs/roadmap.md` for priorities
3. Run quick DB check:
```sql
SELECT COUNT(*) FROM emails;
SELECT COUNT(*) FROM ai_suggestions WHERE status='pending';
```

### When Ending
1. Update `.claude/STATUS.md` with new numbers
2. Commit and push to GitHub

---

## 15. Don't Do These

1. **Don't auto-link** - Always create suggestions
2. **Don't create tables** without checking if similar exists
3. **Don't delete "orphaned" code** - It's usually CLI tools
4. **Don't assume** - Verify by reading code
5. **Don't rush** - Thoroughness > speed
6. **Don't mention project codes without names** - Always include project name
7. **Don't create random files** - Use existing structure

---

## 16. Key Files

| Purpose | File |
|---------|------|
| Email import | `backend/services/email_importer.py` |
| Email sync | `scripts/core/scheduled_email_sync.py` |
| Transcription | `voice_transcriber/transcriber.py` |
| Context building | `backend/services/context_bundler.py` |
| GPT analysis | `backend/services/gpt_suggestion_analyzer.py` |
| Suggestions | `backend/services/suggestion_writer.py` |
| **Batch suggestions** | `backend/services/batch_suggestion_service.py` |
| Handlers | `backend/services/suggestion_handlers/*.py` |
| Learning | `backend/services/learning_service.py` |
| AI Learning | `backend/services/ai_learning_service.py` |
| CLI review | `backend/services/cli_review_helper.py` |
| **Stale proposals report** | `scripts/core/generate_stale_proposals_report.py` |

---

## 17. Email Category Codes

### Non-Project Categories
| Code | Purpose | Domains/Senders |
|------|---------|-----------------|
| PERS-BILL | Bill's personal matters | Canggu land sale (12,000 sqm), hsfkramer.com, ahp.id |
| PERS-INVEST | Bill's investments | dentons.com, jpmorgan, ryan.padgett, binance |
| SM-WILD | Shinta Mani Wild (Bill's hotel) | shintamani.com, gm.wild@ |
| SM-ANGKOR | Shinta Mani Angkor (Bill's hotel) | Personal, not BDS work |
| SM-FOUNDATION | Shinta Mani Foundation (charity) | shintamanifoundation.org |
| INT-SCHED | Internal scheduling | pakheenai@icloud.com (Aood) |
| SKIP-SPAM | Newsletters, notifications | ghost.io, monday.com, sproutsocial |
| SKIP-AUTO | System notifications | atlassian, pipedrive, pandadoc |

### Shinta Mani Clarification
- **SM Wild, SM Angkor** = Bill's existing hotels. Personal, not BDS work.
- **SM Sabra (Saudi Arabia)** = Active BDS project! Shinta Mani is operator, but Bensley is designing it. Link to project 25 BK-042.

### Category Column Warning
- **USE:** `email_content.category` (correct, rule-based)
- **IGNORE:** `emails.category` (NULLed out, was garbage from bad GPT prompt)

---

## 18. Project Statuses

### Valid Project Statuses
| Status | Meaning |
|--------|---------|
| Active | Currently in progress |
| Completed | Project finished |
| Cancelled | Project cancelled |
| contract_expired | Contract term ended, needs review for renewal |

### Contract Expiry Logic
```
IF current_date > contract_end_date AND status = 'Active'
THEN flag for review → could become:
  - contract_expired (awaiting decision)
  - Completed (work done, closed out)
  - Renewed (new contract signed)
```

---

## 19. Two Staff Tables (Keep Both)

| Table | Purpose | Rows |
|-------|---------|------|
| `staff` | HR/admin view (employment, hierarchy, reports_to) | 100 |
| `team_members` | Scheduling/project view (disciplines, team leads) | 98 |

These serve different purposes. Don't consolidate.

---

## 20. Bug Fixes Applied (Dec 8)

| Bug | Fix | File |
|-----|-----|------|
| Email extraction broken | Added RFC 5322 regex | suggestion_writer.py:67-69 |
| Suggestion duplicates | Added unique index + code check | ai_learning_service.py, ai_suggestions table |
| emails.category garbage | NULLed + updated 5 files to use email_content.category | Multiple |
| follow_up flood | Converted to weekly report | follow_up_agent.py disabled, new script created |

---

## 21. Email Coverage Reality (Dec 9)

**Previous agents were measuring wrong.** They obsessed over "53% proposal linking" when that's not the goal.

### Correct Metrics
| Status | Count | % |
|--------|-------|---|
| Linked to proposal | 1,766 | 47% |
| Linked to project (not proposal) | 317 | 9% |
| Categorized only (no link needed) | 1,348 | 36% |
| **HANDLED TOTAL** | **3,431** | **92%** |
| Truly unhandled | 294 | 8% |

### What "Categorized Only" Means
These 1,348 emails don't NEED proposal/project links:
- internal_scheduling (901) - team calendars
- automated_notification (39) - system emails
- internal (85) - general internal comms

### The Real Gap
Only 294 emails (8%) are truly unhandled. Most are:
- SaaS marketing spam
- Bill's Canggu land sale lawyers
- Misc personal

### Pattern Matching Fixed (Dec 9)
Was broken - `times_used` counter wasn't incrementing in `batch_suggestion_service.py`.
Now working correctly. 142 patterns, 14 with active usage.

### INQUIRY-PENDING Emails (15)
These are potential project inquiries that need human review:
- Magandip Riar (Punjab India project)
- Gunjan Group (India resort)
- Zenesca (consultation request)
- Ayun Group (Raja Ampat)
- Jason Holdsworth (new project)

Query to find them:
```sql
SELECT e.sender_email, e.subject FROM emails e
JOIN email_content ec ON e.email_id = ec.email_id
WHERE ec.category = 'INQUIRY-PENDING';
```

---

## 22. Vision & User Requirements (Dec 10, 2025)

### The Ultimate Goal
**"Everyone at Bensley has AI power"**
- Bill: "What's happening with Nusa Dua?" → gets full context in seconds
- PM: "What RFIs are overdue?" → gets list with context
- System LEARNS from every interaction

### Why This Exists
- Store useful data for automation
- Make operations extremely efficient so Bensley can SCALE
- Free up Bill and Brian's time - business ops is bottlenecked with them
- Currently inefficient: too much sits with leadership

### Target Users & Their Needs

| User | Role | Needs |
|------|------|-------|
| **Bill** | Executive | Instant context on ANY project, pipeline health, financial overview, team workload |
| **Project Managers** | Operations | Their projects, deliverables, RFIs, team assignments |
| **Finance/Admin** | Back office | Invoicing, payments, aging reports, cash flow |

### Dashboard Design
**Role-based views** - NOT one-size-fits-all:
- Bill sees executive overview
- PM sees their projects
- Finance sees invoices

### Killer Features (Must Have)

1. **Instant Context**
   - "What's happening with Nusa Dua?" → full history (emails, meetings, fees, stakeholders, timeline)
   - Under 5 seconds

2. **Never Miss Follow-up**
   - NOT just days-since-contact
   - COMMITMENT tracking: "I said I'd send proposal by Friday" → system reminds
   - Proposal sent → 2 weeks no response → flag for follow-up

3. **Auto-Generated Reports**
   - Weekly pipeline report
   - Cash flow summary
   - PM workload

4. **Voice Transcription**
   - Record meetings → auto-summarize → link to projects → extract action items

### AI Suggestions Display
- **BOTH** inline on pages (yellow card: "No contact in 30 days") AND central queue for batch review
- **Push notifications**: Daily email/Slack with "Today's action items"

### Data Sources to Connect

| Source | Status | Notes |
|--------|--------|-------|
| lukas@bensley.com | ✅ Active | 3,773 emails |
| projects@bensley.com | Planned Jan | PMs CC this |
| bill@bensley.com | Planned Jan | Requires Bill approval |
| invoices@bensley.com | Planned Feb | Payment tracking |
| OneDrive | Planned | Contracts, drawings, proposals |
| Accounting software | Planned | Actual payment data |
| Calendar | Planned | Meetings, deadlines |

### Proposals Focus (What Bill Wants to See)
- Follow-up urgency (WHO to call TODAY and WHY)
- Value breakdown (total pipeline, by status, by country)
- Activity timeline (what happened this week)

### Projects Focus (What PMs Want to See)
- Payments & invoicing (outstanding, aging, cash flow)
- Deliverables & RFIs (what's due, what's overdue)
- Phases: Mobilization → CD → DD → CDocs → CO (NOT alphabetical!)

### PM Software Inspiration
- **Monday.com**: Visual boards, automations, timeline views
- **Notion**: Flexible databases, linked records, wiki-style
- **Asana**: Task hierarchy, workload view, portfolios
- **BUT**: Tailored to Bensley's workflow (proposals, projects, disciplines)

---

## 23. Autonomous Agent Prompts

Use these prompts to spawn specialized agents. Each agent figures out the details themselves - you provide context and guardrails, they diagnose and execute.

### Auditor Agent

**Purpose:** Find bugs, misalignments, broken code, stale data.

**Prompt:**
```
You are auditing the BENSLEY Design Studios Operations Platform.

CONTEXT:
- Backend: FastAPI (port 8000) | Frontend: Next.js (port 3002) | DB: SQLite
- Database: database/bensley_master.db (~108 tables)
- Key files: backend/services/*.py, backend/api/routers/*.py, frontend/src/**
- SSOT docs: .claude/STATUS.md, .claude/HANDOFF.md, docs/roadmap.md, docs/ARCHITECTURE.md

YOUR JOB:
1. Verify code actually works (run it, don't assume)
2. Find bugs: broken imports, missing endpoints, orphaned data
3. Check data integrity: FK violations, orphaned links, duplicates
4. Verify STATUS.md numbers match database reality
5. Identify unused/dead code vs CLI tools (don't delete CLI tools)

OUTPUT: A prioritized list of issues with severity (critical/medium/low) and file locations.

GUARDRAILS:
- DO NOT delete files without asking
- DO NOT auto-fix - report issues, let human decide
- DO NOT create new files - update existing SSOT docs
- Internal emails (@bensley.com) are NOT bugs - they're intentionally not linked
```

### Frontend Agent

**Purpose:** Fix UI bugs, implement features, improve UX.

**Prompt:**
```
You are working on the BENSLEY Platform frontend.

CONTEXT:
- Framework: Next.js 15 (App Router) | Port: 3002
- Location: frontend/src/
- API: localhost:8000 (FastAPI backend)
- UI: shadcn/ui components + Tailwind
- Types: frontend/src/lib/types.ts
- API calls: frontend/src/lib/api.ts

YOUR JOB:
1. Read current STATUS.md and roadmap.md for priorities
2. Fix any TypeScript errors (run npm run build to check)
3. Implement requested features
4. Ensure pages load without errors

GUARDRAILS:
- DO NOT touch backend/ folder
- DO NOT create random new pages - check if similar exists first
- DO NOT change api.ts contract without checking backend supports it
- Test in browser before marking done
- Keep components simple - avoid over-engineering
```

### Backend Agent

**Purpose:** Fix API bugs, implement endpoints, optimize queries.

**Prompt:**
```
You are working on the BENSLEY Platform backend.

CONTEXT:
- Framework: FastAPI | Port: 8000
- Location: backend/api/routers/*.py (endpoints), backend/services/*.py (logic)
- Database: database/bensley_master.db (SQLite)
- Entry point: backend/api/main.py

YOUR JOB:
1. Read current STATUS.md and roadmap.md for priorities
2. Fix broken endpoints (test with curl)
3. Implement requested features
4. Ensure proper error handling

KEY TABLES:
- emails, email_content, email_proposal_links, email_project_links
- proposals, projects, contacts
- ai_suggestions (suggestion_type, status, target_table, project_code)
- learned_patterns (pattern_type, pattern_value, target_value)

GUARDRAILS:
- DO NOT touch frontend/ folder
- DO NOT create tables without checking schema first
- DO NOT auto-link emails - create suggestions for human review
- Always include project_name with project_code
- Test endpoints with curl before marking done
```

### Data Engineer Agent

**Purpose:** Fix data quality, run migrations, clean orphans.

**Prompt:**
```
You are a data engineer for the BENSLEY Platform.

CONTEXT:
- Database: database/bensley_master.db (SQLite, ~108 tables)
- Migrations: database/migrations/*.sql
- Key tables: emails (3,742), proposals (102), projects (60), contacts (546)
- Linking tables: email_proposal_links, email_project_links, proposal_contacts

YOUR JOB:
1. Run data quality queries (orphans, duplicates, FK violations)
2. Fix data issues (backfill missing values, clean orphans)
3. Verify linking integrity (every link has valid source and target)
4. Update STATUS.md with new counts after changes

GUARDRAILS:
- DO NOT drop tables without backup
- DO NOT delete data without understanding what it is
- DO NOT create new tables - check if similar exists
- Always backup before destructive operations
- Test on sample data first

COMMON QUERIES:
-- Orphaned links
SELECT COUNT(*) FROM email_proposal_links WHERE email_id NOT IN (SELECT email_id FROM emails);

-- Duplicate links
SELECT email_id, proposal_id, COUNT(*) FROM email_proposal_links GROUP BY email_id, proposal_id HAVING COUNT(*) > 1;

-- Suggestion stats
SELECT suggestion_type, status, COUNT(*) FROM ai_suggestions GROUP BY suggestion_type, status;
```

### Coordinator (You)

**Your job:** Spawn agents, reconcile their findings, update SSOT docs.

**Workflow:**
1. Check STATUS.md for current state
2. Spawn agent(s) based on task type
3. Review agent output - they may conflict or be wrong
4. Update STATUS.md with verified results
5. Create tickets for human follow-up if needed

**Key principle:** Agents work autonomously, but YOU verify before updating docs.
