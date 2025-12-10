# System Audit

Run a comprehensive audit of the Bensley Operating System. Check data quality, find gaps, and identify issues.

## Instructions

You are the AUDIT AGENT. Your job is to check the health of the entire system and report findings.

### Step 1: Read Context Files
Read these files first to understand current state:
- `.claude/STATUS.md` - Live numbers
- `.claude/HANDOFF.md` - Business rules

### Step 2: Run Database Health Checks

Run these SQL queries against `database/bensley_master.db`:

```sql
-- CORE COUNTS
SELECT 'Emails' as entity, COUNT(*) as count FROM emails
UNION ALL SELECT 'Proposals', COUNT(*) FROM proposals
UNION ALL SELECT 'Projects', COUNT(*) FROM projects
UNION ALL SELECT 'Contacts', COUNT(*) FROM contacts
UNION ALL SELECT 'Email-Proposal Links', COUNT(*) FROM email_proposal_links
UNION ALL SELECT 'Email-Project Links', COUNT(*) FROM email_project_links
UNION ALL SELECT 'Learned Patterns', COUNT(*) FROM email_learned_patterns;

-- PROPOSAL STATUS DISTRIBUTION
SELECT status, COUNT(*) as count FROM proposals GROUP BY status ORDER BY count DESC;

-- EMAILS WITHOUT LINKS OR CATEGORY
SELECT COUNT(*) as unhandled_emails
FROM emails e
WHERE NOT EXISTS (SELECT 1 FROM email_proposal_links WHERE email_id = e.email_id)
  AND NOT EXISTS (SELECT 1 FROM email_project_links WHERE email_id = e.email_id)
  AND NOT EXISTS (SELECT 1 FROM email_content WHERE email_id = e.email_id AND category IS NOT NULL);

-- PENDING SUGGESTIONS BY TYPE
SELECT suggestion_type, COUNT(*) as pending
FROM ai_suggestions
WHERE status = 'pending'
GROUP BY suggestion_type;

-- PROPOSALS WITH ZERO EMAILS
SELECT p.project_code, p.project_name, p.status
FROM proposals p
WHERE NOT EXISTS (SELECT 1 FROM email_proposal_links WHERE proposal_id = p.proposal_id)
ORDER BY p.project_code;

-- PROJECTS WITH ZERO EMAILS
SELECT p.project_code, p.project_title, p.status
FROM projects p
WHERE NOT EXISTS (SELECT 1 FROM email_project_links WHERE project_id = p.project_id)
ORDER BY p.project_code;

-- STALE PROPOSALS (no contact in 60+ days, not Dormant/Lost/Declined/Contract Signed)
SELECT project_code, project_name, status, last_contact_date,
       CAST(julianday('now') - julianday(last_contact_date) AS INTEGER) as days_silent
FROM proposals
WHERE last_contact_date IS NOT NULL
  AND julianday('now') - julianday(last_contact_date) > 60
  AND status NOT IN ('Dormant', 'Lost', 'Declined', 'Contract Signed')
ORDER BY days_silent DESC;

-- CONTACTS WITHOUT EMAIL
SELECT COUNT(*) as contacts_no_email FROM contacts WHERE email IS NULL OR email = '';

-- DUPLICATE CONTACTS (same email)
SELECT email, COUNT(*) as dupes FROM contacts WHERE email IS NOT NULL GROUP BY email HAVING COUNT(*) > 1;

-- PATTERN EFFECTIVENESS
SELECT pattern_type, COUNT(*) as patterns, SUM(times_used) as total_uses
FROM email_learned_patterns
GROUP BY pattern_type
ORDER BY total_uses DESC;

-- RECENT SUGGESTION PERFORMANCE (last 7 days)
SELECT suggestion_type, status, COUNT(*) as count
FROM ai_suggestions
WHERE created_at > datetime('now', '-7 days')
GROUP BY suggestion_type, status
ORDER BY suggestion_type, status;
```

### Step 3: Check for Common Issues

1. **Orphaned Links**: Links pointing to deleted proposals/projects
2. **Category Consistency**: Emails with category but no link (should be fine) vs emails with link but wrong category
3. **Contact Gaps**: Proposals without contact_email filled in
4. **Status Inconsistencies**: Proposals marked "Contract Signed" but no matching project

### Step 4: Generate Report

Create a report with these sections:

```
## System Health Report - [DATE]

### Summary
- Total emails: X
- Email coverage: X% (linked or categorized)
- Pending suggestions: X
- Critical issues: X

### Data Quality
| Check | Status | Details |
|-------|--------|---------|
| Unhandled emails | OK/WARN | X emails need attention |
| Orphaned links | OK/WARN | X orphaned links found |
| Duplicate contacts | OK/WARN | X duplicates |
| Stale proposals | OK/WARN | X proposals need follow-up |

### Proposals Needing Attention
[List any proposals with issues]

### Suggestions Backlog
[Pending suggestions by type]

### Recommendations
1. [Top priority action]
2. [Second priority]
3. [Third priority]
```

### Step 5: Update STATUS.md if Numbers Changed

If you find the numbers in STATUS.md are out of date, update them.

## What to Flag

- **CRITICAL**: Unhandled emails, broken links, data corruption
- **WARNING**: Stale proposals, duplicate contacts, pending suggestions > 50
- **INFO**: Statistics, patterns, trends

## Output

Present findings clearly. Always include:
1. Quick summary (1-2 sentences)
2. Numbers table
3. Issues found (if any)
4. Recommended actions
