# Bensley Intelligence Integration Plan

**Status:** DRAFT - Ready to implement at 1,000 emails processed
**Created:** 2025-11-26
**Current Progress:** 454/3,356 emails processed

---

## Vision

An AI assistant that:
1. Knows everything about every proposal/project
2. Drafts replies and follow-ups with verified information
3. Has guardrails for uncertain info (asks you first)
4. Sets calendar reminders and to-dos automatically
5. Answers natural language queries about any project

---

## Phase 1: Data Foundation (Current)

### Already Complete
- [x] Email import (3,356 emails)
- [x] Email threading (1,041 threads)
- [x] AI content extraction (in progress - 454+)
- [x] Attachment indexing (1,164 clean files)
- [x] Proposal status history (180 records)
- [x] Folder categorization fix

### In Progress
- [ ] Complete AI processing to 1,000+ emails
- [ ] Build project-email link coverage

---

## Phase 2: Intelligence Layer (Next)

### 2.1 Proposal Context Builder
Build rich context for each proposal by aggregating:

```sql
-- Per-proposal context view
CREATE VIEW proposal_intelligence AS
SELECT
    p.proposal_id,
    p.project_code,
    p.project_name,
    p.current_status,
    p.first_contact_date,
    p.proposal_sent_date,
    p.contract_signed_date,

    -- Email summary
    (SELECT COUNT(*) FROM email_content WHERE linked_project_code = p.project_code) as email_count,
    (SELECT MAX(e.date) FROM emails e
     JOIN email_content ec ON e.email_id = ec.email_id
     WHERE ec.linked_project_code = p.project_code) as last_email_date,

    -- Key contacts
    (SELECT GROUP_CONCAT(DISTINCT c.contact_name)
     FROM project_contacts_junction pcj
     JOIN contacts c ON pcj.contact_id = c.contact_id
     WHERE pcj.project_code = p.project_code) as key_contacts,

    -- Attachments
    (SELECT COUNT(*) FROM email_attachments ea
     JOIN email_content ec ON ea.email_id = ec.email_id
     WHERE ec.linked_project_code = p.project_code
     AND ea.is_junk = 0) as attachment_count,

    -- Days since last contact
    CAST(julianday('now') - julianday((
        SELECT MAX(e.date) FROM emails e
        JOIN email_content ec ON e.email_id = ec.email_id
        WHERE ec.linked_project_code = p.project_code
    )) AS INTEGER) as days_since_contact

FROM proposals p;
```

### 2.2 AI Summary Generation
For each proposal, generate and store:

```python
proposal_summary = {
    "executive_summary": "3-sentence overview",
    "current_status": "What's happening now",
    "next_actions": ["Action 1", "Action 2"],
    "blockers": ["What's holding this up"],
    "confidence_level": 0.85,  # How sure we are
    "needs_review": ["Unclear fee structure", "Missing scope details"]
}
```

**Table:**
```sql
CREATE TABLE proposal_summaries (
    summary_id INTEGER PRIMARY KEY,
    proposal_id INTEGER REFERENCES proposals(proposal_id),
    summary_type TEXT,  -- executive, timeline, financial, blockers
    content TEXT,       -- JSON or plain text
    confidence REAL,    -- 0-1 how confident AI is
    needs_review TEXT,  -- What AI is unsure about
    generated_at DATETIME,
    reviewed_by TEXT,
    reviewed_at DATETIME
);
```

### 2.3 Contract/Attachment Analysis
Extract key info from PDFs and contracts:

```python
contract_analysis = {
    "contract_value": "$450,000",
    "fee_structure": "25% mobilization, 25% SD, 25% DD, 25% CD",
    "key_dates": {
        "signed": "2025-09-15",
        "sd_delivery": "2025-12-01"
    },
    "scope_items": ["Master planning", "Landscape design", "Pool design"],
    "special_terms": ["Client approval required for travel"],
    "confidence": 0.9
}
```

---

## Phase 3: Frontend Integration

### 3.1 Proposal Detail Page Enhancement
Add to each proposal page:

```
┌─────────────────────────────────────────────────────────────┐
│ 25 BK-045: MDM World - Haeundae Project                     │
├─────────────────────────────────────────────────────────────┤
│ AI Summary                                        [Refresh] │
│ ─────────────────────────────────────────────────────────── │
│ "Active proposal for luxury resort in Busan. Proposal sent  │
│ Aug 8, 2025. Client requested scope clarification on Nov 3. │
│ Waiting for client response on revised fee structure."      │
│                                                             │
│ ⚠️ AI Unsure: Fee negotiation outcome unclear               │
├─────────────────────────────────────────────────────────────┤
│ Next Actions                                                │
│ • Follow up on fee structure (7 days overdue)               │
│ • Schedule site visit call                                  │
├─────────────────────────────────────────────────────────────┤
│ Email History (21 emails)                        [View All] │
│ ─────────────────────────────────────────────────────────── │
│ Nov 15 │ RE: Scope clarification    │ Client responded      │
│ Nov 3  │ FW: Revised fee proposal   │ You sent              │
│ Oct 28 │ RE: Haeundae questions     │ Client questions      │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Query Interface
Natural language queries:

```
You: "What's the status of MDM World?"

AI: "MDM World (25 BK-045) - Haeundae Project in Busan
    Status: Proposal Sent (Aug 8, 2025)
    Last Contact: Nov 15, 2025 (11 days ago)

    Recent Activity:
    - Client requested scope clarification
    - You sent revised fee proposal ($450K)
    - Awaiting client decision

    Suggested Action: Follow up email - it's been 11 days"
```

### 3.3 Draft Email Generator

```
You: "Draft a follow-up for MDM World"

AI: "Subject: RE: Haeundae Project - Following Up

Dear Mr. Kim,

I hope this message finds you well. Following our revised
proposal sent on November 3rd for the Haeundae luxury resort
project, I wanted to check in on your team's review progress.

We're excited about the possibility of bringing our
regenerative design approach to Busan...

[Draft continues - Click to edit before sending]

⚠️ AI Note: I included the $450,000 fee from our last email.
   Verify this is still accurate before sending."
```

---

## Phase 4: Automation & Guardrails

### 4.1 Smart Notifications
```python
daily_digest = {
    "overdue_follow_ups": [
        {"project": "MDM World", "days_overdue": 7, "last_contact": "Nov 15"},
        {"project": "Sabrah Hotel", "days_overdue": 3, "last_contact": "Nov 23"}
    ],
    "proposals_expiring": [
        {"project": "Grenada Wellness", "expires_in": 5}
    ],
    "contracts_needing_action": [
        {"project": "Ritz Carlton Bali", "action": "Invoice due Dec 1"}
    ]
}
```

### 4.2 Confidence & Guardrails

**High Confidence (AI can act):**
- Project code, name, status from database
- Email dates, senders, subjects
- Contract values from signed documents
- Meeting times from calendar invites

**Medium Confidence (AI suggests, you confirm):**
- Inferred next actions
- Draft email content
- Status interpretations from email tone

**Low Confidence (AI asks first):**
- Fee negotiations (unless explicitly stated)
- Scope changes (requires your review)
- Anything contradictory in email thread

### 4.3 Calendar Integration
```python
# Auto-detect meeting requests from emails
if "let's schedule" in email_body or "available on" in email_body:
    suggested_meeting = {
        "title": f"Call: {project_name}",
        "attendees": extracted_emails,
        "suggested_times": parse_times_from_email(email_body),
        "action": "SUGGEST_TO_USER"  # Don't auto-create
    }
```

### 4.4 To-Do Generation
```python
# Auto-generate from email context
todos = [
    {
        "task": "Send revised fee proposal to MDM World",
        "project_code": "25 BK-045",
        "priority": "HIGH",
        "due_date": "2025-11-27",  # Inferred: "by end of week"
        "source": "Email from Nov 15",
        "confidence": 0.8,
        "status": "PENDING_APPROVAL"  # User must approve
    }
]
```

---

## Implementation Priority

### Week 1 (After 1,000 emails)
1. Create `proposal_intelligence` view
2. Build summary generation endpoint
3. Add email timeline to frontend

### Week 2
4. Query interface (natural language)
5. Draft email generator
6. Confidence scoring system

### Week 3
7. Calendar integration
8. To-do generation
9. Daily digest notifications

### Week 4
10. Contract PDF analysis
11. Full guardrail system
12. Production hardening

---

## API Endpoints Needed

```
POST /api/proposals/{code}/generate-summary
GET  /api/proposals/{code}/intelligence
POST /api/query                          # Natural language
POST /api/proposals/{code}/draft-email
GET  /api/dashboard/daily-digest
POST /api/todos/generate
```

---

## Database Changes Needed

```sql
-- Already have from email processing
-- Need to add:

CREATE TABLE proposal_summaries (...);      -- AI-generated summaries
CREATE TABLE ai_suggestions (              -- Draft emails, todos
    suggestion_id INTEGER PRIMARY KEY,
    suggestion_type TEXT,  -- email_draft, todo, meeting, follow_up
    proposal_id INTEGER,
    content TEXT,          -- JSON
    confidence REAL,
    status TEXT,           -- pending, approved, rejected, sent
    created_at DATETIME,
    reviewed_at DATETIME,
    reviewed_by TEXT
);

CREATE TABLE confidence_audit (            -- Track AI accuracy
    audit_id INTEGER PRIMARY KEY,
    suggestion_id INTEGER,
    was_accurate BOOLEAN,
    user_correction TEXT,
    created_at DATETIME
);
```

---

## Success Metrics

- [ ] Query response time < 2 seconds
- [ ] Draft email accuracy > 80% (minimal edits needed)
- [ ] Follow-up detection > 90% recall
- [ ] Zero incorrect auto-actions (guardrails work)
- [ ] User saves 5+ hours/week

---

## Notes

This builds on the existing infrastructure:
- `email_content` table has AI extractions
- `email_threads` groups conversations
- `proposal_status_history` tracks changes
- `proposal_documents` tracks versions

The key is aggregating all this into actionable intelligence.
