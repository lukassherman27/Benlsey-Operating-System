# Daily Email Processing Workflow

Run this every day (or every other day) to process new emails with full business context.

## Step 1: Sync & Summarize

First, sync new emails and give me a summary:

```sql
-- Run this query to get the daily briefing
SELECT
  'EMAILS' as section,
  COUNT(*) as total,
  SUM(CASE WHEN date >= date('now', '-1 day') THEN 1 ELSE 0 END) as last_24h,
  SUM(CASE WHEN date >= date('now', '-3 days') THEN 1 ELSE 0 END) as last_3_days
FROM emails;
```

Then check for:
1. **New unprocessed emails** (no category, no proposal link) in last 3 days
2. **Meeting summary emails** that need task extraction
3. **Proposals with stale contact** (no email in 7+ days)
4. **Tasks overdue** (ball with client, past due date)

## Step 2: Process Emails by Priority

### Priority 1: Meeting Summaries
For each email with subject containing "Meeting Summary":
- Read the full email body
- Extract action items with owner, deadline, ball tracking
- Create tasks linked to the proposal
- Update proposal health

### Priority 2: Client Responses
For emails FROM clients (not @bensley.com):
- What proposal/project does this relate to?
- Is this a response we were waiting for? (check tasks with ball=them)
- Does this change proposal status?
- Any new action items?

### Priority 3: New Leads
For emails that might be new business:
- Is this a new project inquiry?
- Should we create a proposal?
- Who's the client contact?

### Priority 4: Internal
For emails FROM @bensley.com:
- Categorize (scheduling, content, legal, etc.)
- Link to proposal if project-related
- Skip if purely internal chatter

## Step 3: Update Proposal Health

After processing, update each affected proposal:
- Last contact date
- Ball tracking (us vs them)
- Next action needed
- Health score

## Step 4: Generate Nudge List

Show proposals where:
- Ball is with client
- Last contact > 7 days OR task overdue
- Suggest follow-up email

---

## Quick Commands

When I say:
- **"process emails"** → Run full workflow above
- **"check [project code]"** → Show all emails/tasks for that proposal
- **"nudge list"** → Show overdue client items
- **"new leads"** → Show potential new business emails
- **"ball status"** → Show ball tracking for all active proposals
