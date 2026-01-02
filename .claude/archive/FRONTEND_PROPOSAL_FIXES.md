# Frontend Proposal Tracker - Required Fixes

**Date:** 2025-12-10
**Based on:** User feedback audit
**Priority:** HIGH - Multiple display issues affecting usability

---

## SECTION 1: Proposal Overview Page Issues

### 1.1 Year Overview Stats - WRONG LABELS

**Current:** "Total Pipeline", "Won", "Lost", "Still Active"

**Should be:**
- Total Proposals (sent this year)
- Won (Contract Signed)
- Lost/Declined
- Still Active

**Add NEW metric:** "Total Value of Proposals Sent" - so we know total $ actually sent to clients

### 1.2 Pipeline Stages Section - WRONG HEADER

**Current:** "Pipeline by Stage"

**Should be:** "Active Proposals by Stage"

**Stages should be (in order):**
1. First Contact
2. Drafting / Preparing Proposal (combine Proposal Prep)
3. Proposal Sent
4. Waiting for Client (ball_in_court = 'them')
5. Negotiation
6. On Hold / Paused

### 1.3 Status Colors - ALL SAME COLOR

**Problem:** First Contact, Dormant, Declined, Proposal Prep all have the same color

**Fix:** Each status needs a distinct color:
- First Contact: Blue
- Proposal Prep / Drafting: Yellow/Orange
- Proposal Sent: Green
- Waiting for Client: Light Green
- Negotiation: Purple
- On Hold: Gray
- Contract Signed / Won: Dark Green
- Lost / Declined: Red
- Dormant: Gray (muted)

### 1.4 Proposal Table Issues

**Columns:** Project Number | Project Name | Value | Last Contact | Status | Days in Status | Remark

**Issues found:**

1. **Text overlap** - UI issue with column widths
2. **Days in Status hardcoded** - Should come from `proposal_status_history` table, not when manually entered
3. **Remarks empty** - Should show `correspondence_summary` from proposals table
4. **Last Contact empty** - Should show most recent email date from `email_proposal_links`
5. **Wrong statuses showing** - "Currently in first contact" for things that are clearly Proposal Sent

---

## SECTION 2: Proposal Detail Page Issues

### 2.1 Vahine Island Example (25 BK-087)

**Database has:**
```
contact_person: Jean Pierre Fourcade
contact_email: jp.fourcade@pearlresortsoftahiti.com
status: Proposal Sent
correspondence_summary: Pearl Resorts redevelopment - Vahine Island & Queens Residence. Proposal $3.75M sent Nov 21. Dec 9: Zoom meeting scheduled for Dec 11, 10AM Bangkok.
ball_in_court: them
```

**Emails linked:** 53 emails from June 2025 to Nov 2025

**Frontend shows:**
- Client: "Not specified" - WRONG (should be Jean Pierre Fourcade)
- Contact Information: Shows stakeholder not client - WRONG
- Last Contact: "Never" - WRONG (last email was Nov 28)
- Win Probability: Empty - OK (not tracked)
- Next Action: Empty - Should show "Meeting Dec 11, 10AM Bangkok"

**Fix:**
- Use `contact_person` field for Client
- Use `contact_email` for contact info
- Calculate Last Contact from MAX(emails.date) for linked emails
- Parse `correspondence_summary` for next action items

### 2.2 Contact/Stakeholder Confusion

**Problem:** Showing Bensley employees as stakeholders instead of client contacts

**Example from Ritz Reserve (25 BK-033):**
- Shows: Putu, Chenique, Astuti (all Bensley employees)
- Should show: Mr. Ferry Murruf (client contact from `contact_person` field)

**Fix:**
- Filter stakeholders by checking if email contains `@bensley.com`
- Bensley emails = Internal team, not stakeholders
- Only show external contacts as stakeholders

### 2.3 Status Timeline Issues

**Problem:** Confusing status transitions

**Example from Ritz Reserve:**
```
Initial → First Contact (May 24) ✓
First Contact → Proposal Sent (June 17) ✓
Proposal Sent → Contract Signed (July 3) ✓
Contract Signed → Contract Signed (Nov 25) ✗ WRONG
Won → Contract Signed (Dec 8) ✗ CONFUSING
```

**Required Status Flow:**
1. **Initial / First Contact** - First email received
2. **Drafting / Proposal Prep** - Working on proposal
3. **Proposal Sent** - Sent to client
4. **Negotiation** - Contract discussions
5. **Contract Signed** - Agreement signed
6. **Won / Active** - Mobilization fee paid, project is live

**Fix:**
- Clean up duplicate statuses (Contract Signed vs Contract signed)
- "Won" means mobilization paid, different from Contract Signed
- Show clear progression, not duplicates

### 2.4 Timeline Should Be Based on Emails

**Current:** Shows status changes from `proposal_status_history` table

**Should show:** Email-based timeline
- First email = First Contact date
- Meeting invites/summaries = Meeting dates
- Proposal attachment sent = Proposal Sent date
- Contract attachment = Contract Signed date
- Payment confirmation = Won date

**Data available:**
- `emails` table has dates and subjects
- `email_proposal_links` links emails to proposals
- Can parse subjects for: "Proposal", "Contract", "Meeting", "Invoice"

---

## SECTION 3: Data Fixes Needed in Backend

### 3.1 Last Contact Calculation

**Current:** Not calculated or shows "Never"

**Should be:**
```sql
SELECT MAX(e.date) as last_contact
FROM emails e
JOIN email_proposal_links epl ON e.email_id = epl.email_id
WHERE epl.proposal_id = ?
```

### 3.2 Days in Status Calculation

**Current:** Hardcoded or wrong

**Should be:**
```sql
SELECT
    julianday('now') - julianday(
        (SELECT MAX(status_date)
         FROM proposal_status_history
         WHERE proposal_id = ? AND new_status = proposals.status)
    ) as days_in_status
FROM proposals
WHERE proposal_id = ?
```

### 3.3 Remark/Summary Display

**Current:** Empty

**Should show:** `correspondence_summary` field from proposals table

**Example for Vahine:**
```
Pearl Resorts redevelopment - Vahine Island & Queens Residence.
Proposal $3.75M sent Nov 21.
Dec 9: Zoom meeting scheduled for Dec 11, 10AM Bangkok.
```

### 3.4 Filter Internal vs External Contacts

**Add to stakeholders query:**
```sql
WHERE email NOT LIKE '%@bensley.com%'
```

---

## SECTION 4: Status Definitions

### Proposal Lifecycle (Correct Order)

| Stage | Database Status | Description | Color |
|-------|-----------------|-------------|-------|
| 1 | First Contact | Initial inquiry received | Blue |
| 2 | Meeting Held | Met with client | Light Blue |
| 3 | Proposal Prep | Drafting proposal | Yellow |
| 4 | Proposal Sent | Sent to client | Green |
| 5 | Negotiation | Contract discussions | Purple |
| 6 | Contract Signed | Agreement signed | Dark Green |
| 7 | Won | Mobilization paid, active | Gold |
| - | On Hold | Paused by agreement | Gray |
| - | Lost | Lost to competitor | Red |
| - | Declined | We declined | Red (muted) |
| - | Dormant | No activity 60+ days | Gray (muted) |

### Ball in Court Indicator

| Value | Meaning | Display |
|-------|---------|---------|
| `us` | We need to take action | Red indicator "Our Turn" |
| `them` | Waiting on client | Green indicator "Their Turn" |
| `on_hold` | Paused | Gray indicator "On Hold" |
| `mutual` | Both parties working | Yellow indicator |

---

## SECTION 5: Specific UI Fixes

### 5.1 Proposal List Table

```
| Project # | Project Name | Value | Last Contact | Status | Days | Remark |
|-----------|--------------|-------|--------------|--------|------|--------|
```

- **Value:** Format as $X.XM (from `project_value`)
- **Last Contact:** MAX date from linked emails
- **Status:** Color-coded badge
- **Days:** Calculate from status_date in history
- **Remark:** Truncate `correspondence_summary` to ~100 chars

### 5.2 Proposal Detail - Contact Card

**Show:**
- Client Name: `contact_person`
- Client Email: `contact_email`
- Company: `client_company`
- Last Contact: MAX(email date)
- Ball in Court: `ball_in_court` indicator

**Don't show:**
- Bensley employee emails as contacts

### 5.3 Timeline View

**Show in order:**
1. Email correspondence (grouped by thread if possible)
2. Meeting summaries (where subject contains "Meeting")
3. Proposal sent (where subject contains "Proposal")
4. Status changes from history table

**Mark key milestones:**
- First Contact (first email)
- Proposal Sent (email with proposal attachment)
- Contract Signed (email with contract attachment)

---

## SECTION 6: Database Fields Reference

### proposals table (key fields)

| Field | Purpose | Used For |
|-------|---------|----------|
| `project_code` | ID like "25 BK-087" | Primary identifier |
| `project_name` | Full name | Display |
| `project_value` | Contract value | Value column |
| `status` | Current status | Status badge |
| `contact_person` | Client contact name | Contact card |
| `contact_email` | Client email | Contact card |
| `client_company` | Company name | Contact card |
| `correspondence_summary` | Status summary | Remark column |
| `ball_in_court` | us/them/on_hold | Action indicator |

### email_proposal_links table

| Field | Purpose |
|-------|---------|
| `email_id` | Links to emails table |
| `proposal_id` | Links to proposals table |
| `confidence_score` | How sure we are of link |

### proposal_status_history table

| Field | Purpose |
|-------|---------|
| `proposal_id` | Which proposal |
| `old_status` | Previous status |
| `new_status` | Current status |
| `status_date` | When changed |
| `changed_by` | Who/what changed it |

---

## SECTION 7: Test Cases

### Test 1: Vahine Island (25 BK-087)
- Should show: Jean Pierre Fourcade as client
- Should show: 53 emails linked
- Should show: Last contact Nov 28
- Should show: Meeting Dec 11 in next action
- Status: Proposal Sent (green)

### Test 2: Ritz Reserve Nusa Dua (25 BK-033)
- Should show: Mr. Ferry Murruf as client (NOT Bensley employees)
- Status: Contract Signed (dark green)
- Timeline: Clean progression without duplicates

### Test 3: ShanXiangfeng (25 BK-058)
- Should show: Ball in OUR court (red indicator)
- Should show: Deadline Dec 16 prominently
- Status: Proposal Sent

---

## Summary for Frontend Agent

**Priority 1 (Display Bugs):**
1. Fix text overlap in table columns
2. Show `correspondence_summary` in Remark column
3. Calculate Last Contact from emails
4. Calculate Days in Status from history table
5. Show `contact_person` as Client, not "Not specified"

**Priority 2 (Logic Bugs):**
1. Filter out @bensley.com emails from stakeholders
2. Fix status color coding (each status = unique color)
3. Clean up timeline to show proper progression
4. Use `ball_in_court` for action indicators

**Priority 3 (New Features):**
1. Add "Total Value of Proposals Sent" metric
2. Parse correspondence_summary for next actions
3. Group timeline by milestone type (emails, meetings, status changes)

**Files to check:**
- `frontend/src/components/proposals/proposals-manager.tsx` - List table
- `frontend/src/app/(dashboard)/proposals/[projectCode]/page.tsx` - Detail page
- `frontend/src/lib/api.ts` - API calls
- `backend/services/proposal_tracker_service.py` - Backend queries
