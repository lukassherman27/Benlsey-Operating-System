# Review Unlinked Emails

When user says "review unlinked emails" or runs /review-unlinked-emails:

## 1. Get Current State

```sql
-- Total unlinked emails
SELECT COUNT(*) as unlinked_count
FROM emails
WHERE email_id NOT IN (SELECT email_id FROM email_proposal_links);

-- Breakdown by age
SELECT
    CASE
        WHEN date >= date('now', '-7 days') THEN 'Last 7 days'
        WHEN date >= date('now', '-30 days') THEN 'Last 30 days'
        ELSE 'Older'
    END as age_bucket,
    COUNT(*) as count
FROM emails
WHERE email_id NOT IN (SELECT email_id FROM email_proposal_links)
GROUP BY age_bucket;
```

## 2. Present Summary

```
📧 UNLINKED EMAILS REVIEW
━━━━━━━━━━━━━━━━━━━━━━━━

Total unlinked: XX emails
- Last 7 days: XX
- Last 30 days: XX
- Older: XX

Learned patterns: XX (used XX times)
```

## 3. Process in Batches

For each batch of 10-20 emails, I will:

### A. Query the email with context
```sql
SELECT
    e.email_id,
    e.subject,
    e.sender_email,
    e.sender_name,
    e.date,
    e.snippet,
    e.primary_category,
    -- Check if sender is known
    c.contact_id,
    c.company,
    -- Get sender's linked projects
    (SELECT GROUP_CONCAT(DISTINCT epl.project_code)
     FROM email_proposal_links epl
     JOIN emails e2 ON epl.email_id = e2.email_id
     WHERE e2.sender_email = e.sender_email) as sender_projects
FROM emails e
LEFT JOIN contacts c ON e.sender_email = c.email
WHERE e.email_id NOT IN (SELECT email_id FROM email_proposal_links)
ORDER BY e.date DESC
LIMIT 20;
```

### B. For each email, check existing patterns
```sql
-- Check learned patterns that might match
SELECT pattern_type, pattern_value, project_code, confidence, times_used
FROM email_learned_patterns
WHERE (
    pattern_type = 'sender_email' AND pattern_value = :sender_email
    OR pattern_type = 'sender_domain' AND pattern_value = :sender_domain
    OR pattern_type = 'subject_keyword' AND :subject LIKE '%' || pattern_value || '%'
)
ORDER BY confidence DESC, times_used DESC;
```

### C. Look up potential project matches
```sql
-- Find proposals by client company
SELECT project_code, project_name, client_company, status
FROM proposals
WHERE client_company LIKE '%' || :company_hint || '%'
OR project_name LIKE '%' || :keyword || '%';
```

## 4. Present Each Email for Decision

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📧 Email #1 of 20
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

From: john.smith@marriott.com (John Smith)
Date: Dec 20, 2024
Subject: RE: Ritz Carlton Nusa Dua - Design Review

Snippet: "Thanks for sending the updated drawings. The team has reviewed..."

🔍 ANALYSIS:
- Sender previously linked to: 25 BK-033 (Ritz Carlton Nusa Dua)
- Subject contains project code hint: "Ritz Carlton Nusa Dua"
- High confidence match: 25 BK-033

📋 SUGGESTION:
→ Link to: 25 BK-033 (Ritz Carlton Nusa Dua)
→ Learn pattern: sender_email → 25 BK-033

[A]pprove  [S]kip  [M]anual link  [R]ead full email
```

## 5. On Approval

When user approves (A):

```sql
-- 1. Create the link
INSERT INTO email_proposal_links (email_id, project_code, link_source, confidence, created_at)
VALUES (:email_id, :project_code, 'claude_suggestion', 0.95, datetime('now'));

-- 2. Learn the pattern (if not already learned)
INSERT OR IGNORE INTO email_learned_patterns
(pattern_type, pattern_value, project_code, confidence, times_used, created_at, last_used)
VALUES ('sender_email', :sender_email, :project_code, 0.95, 1, datetime('now'), datetime('now'));

-- 3. Update times_used if pattern already exists
UPDATE email_learned_patterns
SET times_used = times_used + 1, last_used = datetime('now')
WHERE pattern_type = 'sender_email' AND pattern_value = :sender_email AND project_code = :project_code;
```

## 6. On Skip

Move to next email without action.

## 7. On Manual Link

Ask user for project code:
```
Enter project code (e.g., 25 BK-033): _
```

Then proceed as approval with user-provided code.

## 8. End Summary

After batch:
```
━━━━━━━━━━━━━━━━━━━━━━━━
BATCH COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━

Processed: 20 emails
- Approved: 15
- Skipped: 4
- Manual: 1

New patterns learned: 8
Remaining unlinked: XX

Continue with next batch? [Y/n]
```

## Key Tables Reference

- `emails` - All emails
- `email_proposal_links` - Links between emails and projects
- `email_learned_patterns` - Patterns learned from approvals
- `proposals` - Proposal info with client details
- `contacts` - Known contacts with companies
