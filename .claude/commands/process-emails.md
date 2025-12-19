# Process Emails Command

When user says "process emails" or runs /process-emails:

## 1. Sync New Emails First
```bash
python scripts/core/scheduled_email_sync.py
```

## 2. Get Daily Briefing
Run these queries and present a summary:

```sql
-- New emails
SELECT COUNT(*) as new_emails FROM emails WHERE date >= date('now', '-3 days');

-- Unprocessed (no category, no link)
SELECT COUNT(*) as unprocessed FROM emails
WHERE date >= date('now', '-7 days')
AND (primary_category IS NULL OR primary_category = '')
AND NOT EXISTS (SELECT 1 FROM email_proposal_links WHERE email_proposal_links.email_id = emails.email_id);

-- Meeting summaries not yet processed into tasks
SELECT COUNT(*) as meeting_summaries FROM emails
WHERE subject LIKE '%Meeting Summary%'
AND date >= date('now', '-7 days')
AND NOT EXISTS (SELECT 1 FROM tasks WHERE tasks.source_email_id = emails.email_id);

-- Proposals needing attention (no contact in 7+ days)
SELECT COUNT(*) as stale_proposals FROM proposals
WHERE status NOT IN ('Contract Signed', 'Lost', 'On Hold')
AND (last_contact_date IS NULL OR last_contact_date < date('now', '-7 days'));

-- Overdue client tasks
SELECT COUNT(*) as overdue_client_tasks FROM tasks
WHERE assignee = 'them' AND status = 'pending'
AND due_date IS NOT NULL AND due_date < date('now');
```

## 3. Present Summary Like This:

```
📬 DAILY EMAIL BRIEFING
━━━━━━━━━━━━━━━━━━━━━━

📥 New Emails (last 3 days): XX
   - XX unprocessed (need review)
   - XX meeting summaries (need task extraction)

⚠️ Needs Attention:
   - XX proposals with no contact in 7+ days
   - XX client tasks overdue

Ready to process? I'll show you:
1. Meeting summaries first (extract tasks)
2. Client emails (check for responses)
3. Potential new leads
4. Internal to categorize
```

## 4. Then Process Each Category

### Meeting Summaries
For each, read full body and extract:
- Project code
- Action items (task, owner, deadline)
- Create tasks with ball tracking

### Client Emails
Show each with context:
- Which proposal it relates to
- What we were waiting for
- Suggested actions

### New Leads
Identify emails that might be new business:
- Unknown sender + project inquiry keywords
- Suggest creating proposal

### Internal
Bulk categorize obvious ones:
- Schedules → internal_scheduling
- Legal → INT-LEGAL
- Content → INT-CONTENT
- Bill shares → PERS-BILL

## 5. End with Ball Status

```
🎱 BALL STATUS
━━━━━━━━━━━━━

US (need to act):
- 25 BK-087: Revise contracts (Lukas, due tomorrow)
- 25 BK-033: Send fee proposal (Brian, due Friday)

THEM (waiting on client):
- 25 BK-042: Waiting on signed contract (5 days)
- 25 BK-058: Waiting on design brief (3 days) ⚠️ OVERDUE

Send nudges? [list which ones]
```
