# PHASE E: Reports Agent Prompt

**Phase:** E - Basic Intelligence & Reports
**Role:** Intelligence Agent + Backend Agent
**Goal:** Generate weekly proposal status reports with email/transcript context

---

## Context Files to Read First

1. `docs/planning/TIER1_PHASED_PLAN.md` - Your phase definition
2. `.claude/LIVE_STATE.md` - Phase D metrics (data quality verified)
3. `scripts/core/generate_weekly_proposal_report.py` - Existing report script
4. `docs/context/backend.md` - API endpoints

---

## Prerequisites Check

Before starting, verify Phase D is complete:

```bash
# Check LIVE_STATE.md for Phase D completion
cat .claude/LIVE_STATE.md | grep -A 10 "Phase D Status"

# Should show:
# - Email accuracy ≥90%
# - Transcripts 100% linked
# - Contacts verified
```

If Phase D is not complete, STOP and report.

---

## Your Tasks

### Task 1: Fix Report Script DB Path

**File:** `scripts/core/generate_weekly_proposal_report.py`

```python
# WRONG (if exists)
DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

# CORRECT
DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')
```

**Test:**
```bash
cd scripts/core
python generate_weekly_proposal_report.py --help
```

### Task 2: Weekly Proposal Status Report

**Output format:** HTML (can be printed to PDF by user)

**Report sections:**

```
WEEKLY PROPOSAL STATUS REPORT
Generated: [Date]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUMMARY
- Active proposals: X
- Won this week: Y
- Lost this week: Z
- Pending follow-up: W

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROPOSALS BY STATUS

[HOT - ACTIVE]
┌─────────────────────────────────────────┐
│ 25 BK-087: Maldives Resort Expansion    │
│ Client: Four Seasons                     │
│ Value: $2.5M                            │
│ Status: Proposal sent, awaiting response │
│                                          │
│ Recent Activity:                         │
│ • [Nov 28] Email from client re: budget  │
│ • [Nov 25] Call with PM (transcript)     │
│ • [Nov 22] Revised proposal sent         │
│                                          │
│ Key Points from Last Meeting:            │
│ - Client wants phased approach           │
│ - Budget concerns on landscaping         │
│ - Decision expected by Dec 15            │
└─────────────────────────────────────────┘

[COLD - NEEDS FOLLOW-UP]
...

[WON THIS WEEK]
...

[LOST THIS WEEK]
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ACTION ITEMS
- Follow up with [Client] on [Proposal] - no response in 14 days
- Schedule meeting for [Proposal] - client requested
- Prepare revised budget for [Proposal]
```

### Task 3: Add Email Context to Reports

```python
def get_recent_emails_for_proposal(proposal_id: int, limit: int = 5):
    """Get last N emails linked to this proposal"""
    query = """
        SELECT e.subject, e.from_address, e.sent_date,
               SUBSTR(e.body, 1, 200) as preview
        FROM emails e
        JOIN email_proposal_links epl ON e.id = epl.email_id
        WHERE epl.proposal_id = ?
        ORDER BY e.sent_date DESC
        LIMIT ?
    """
    # Return formatted email list
```

### Task 4: Add Transcript Context to Reports

```python
def get_meeting_summaries_for_proposal(proposal_id: int):
    """Get meeting summaries linked to this proposal"""
    query = """
        SELECT mt.meeting_date, mt.meeting_title,
               mt.summary, mt.key_points
        FROM meeting_transcripts mt
        WHERE mt.proposal_id = ?
        ORDER BY mt.meeting_date DESC
    """
    # Return formatted summaries
```

### Task 5: API Endpoint for Report

```python
# In backend/api/routers/reports.py (create if needed)

@router.get("/api/reports/weekly-proposals")
async def get_weekly_proposal_report(
    format: str = "json",  # json or html
    include_emails: bool = True,
    include_transcripts: bool = True
):
    """Generate weekly proposal status report"""
    # Return report data
```

### Task 6: Test Report Generation

```bash
# Generate test report
python scripts/core/generate_weekly_proposal_report.py --output exports/test_report.html

# Verify it includes:
# - All active proposals
# - Recent emails per proposal
# - Meeting summaries
# - No 500 errors

# Open in browser
open exports/test_report.html
```

---

## Report Requirements

1. **Accurate data** - Only use verified data from Phase D
2. **Email context** - Last 5 emails per proposal
3. **Transcript context** - Meeting summaries and key points
4. **Actionable** - Include follow-up recommendations
5. **Bill-friendly** - Simple, scannable format

---

## Gate Criteria

Before declaring Phase E complete:

- [ ] Report script uses correct DB path
- [ ] Report generates without errors
- [ ] Report includes proposal summaries
- [ ] Report includes email context (last 5 per proposal)
- [ ] Report includes transcript summaries
- [ ] Report has action items section
- [ ] API endpoint works: GET /api/reports/weekly-proposals
- [ ] Bill can use it (get feedback)

---

## Testing Checklist

```bash
# 1. Script runs
python scripts/core/generate_weekly_proposal_report.py

# 2. API works
curl -s http://localhost:8000/api/reports/weekly-proposals | jq '.summary'

# 3. HTML output readable
python scripts/core/generate_weekly_proposal_report.py --format html > exports/report.html
open exports/report.html

# 4. Data accurate
# Manually verify 3 proposals have correct email/transcript data
```

---

## DO NOT Do

- Do NOT make up data
- Do NOT include unverified links
- Do NOT overcomplicate the report format
- Do NOT add features Bill didn't ask for

---

## Handoff

When complete, update `.claude/LIVE_STATE.md`:

```markdown
## Phase E Status: COMPLETE

### Delivered
- Weekly proposal status report generator
- Email context integration (last 5 per proposal)
- Transcript summary integration
- API endpoint: GET /api/reports/weekly-proposals
- HTML output format

### How to Generate Report
\`\`\`bash
python scripts/core/generate_weekly_proposal_report.py --output exports/weekly_report.html
\`\`\`

### Sample Output
[Screenshot or description]

### Ready for Phase F
Phase F (Polish) can begin to improve UI and appearance.
```
