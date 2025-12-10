# Proposal Audit

Audit all proposals for completeness, staleness, and data quality. Proposals are Bill's #1 priority.

## Instructions

You are the PROPOSAL AUDIT AGENT. Check every proposal for issues.

### Step 1: Get All Proposals with Full Context

```sql
-- Full proposal overview
SELECT
    p.project_code,
    p.project_name,
    p.status,
    p.client_company,
    p.contact_person,
    p.contact_email,
    p.country,
    p.first_contact_date,
    p.last_contact_date,
    CAST(julianday('now') - julianday(COALESCE(p.last_contact_date, p.first_contact_date)) AS INTEGER) as days_silent,
    (SELECT COUNT(*) FROM email_proposal_links WHERE proposal_id = p.proposal_id) as email_count,
    p.project_value,
    p.internal_notes
FROM proposals p
ORDER BY
    CASE p.status
        WHEN 'First Contact' THEN 1
        WHEN 'Meeting Held' THEN 2
        WHEN 'NDA Signed' THEN 3
        WHEN 'Proposal Prep' THEN 4
        WHEN 'Proposal Sent' THEN 5
        WHEN 'Negotiation' THEN 6
        WHEN 'On Hold' THEN 7
        WHEN 'Dormant' THEN 8
        WHEN 'Contract Signed' THEN 9
        WHEN 'Lost' THEN 10
        WHEN 'Declined' THEN 11
        ELSE 12
    END,
    days_silent DESC;
```

### Step 2: Check for Issues

Run these checks:

```sql
-- PROPOSALS MISSING CONTACT INFO
SELECT project_code, project_name, status
FROM proposals
WHERE (contact_email IS NULL OR contact_email = '')
  AND status NOT IN ('Lost', 'Declined', 'Dormant')
ORDER BY project_code;

-- PROPOSALS MISSING CLIENT COMPANY
SELECT project_code, project_name, status
FROM proposals
WHERE (client_company IS NULL OR client_company = '')
  AND status NOT IN ('Lost', 'Declined', 'Dormant')
ORDER BY project_code;

-- PROPOSALS WITH ZERO EMAILS (active statuses only)
SELECT p.project_code, p.project_name, p.status
FROM proposals p
WHERE NOT EXISTS (SELECT 1 FROM email_proposal_links WHERE proposal_id = p.proposal_id)
  AND p.status NOT IN ('Lost', 'Declined', 'Dormant', 'Contract Signed')
ORDER BY p.project_code;

-- STALE PROPOSALS (should be Dormant?)
SELECT project_code, project_name, status, last_contact_date,
       CAST(julianday('now') - julianday(last_contact_date) AS INTEGER) as days_silent
FROM proposals
WHERE last_contact_date IS NOT NULL
  AND julianday('now') - julianday(last_contact_date) > 90
  AND status NOT IN ('Dormant', 'Lost', 'Declined', 'Contract Signed', 'On Hold')
ORDER BY days_silent DESC;

-- PROPOSALS IN "PROPOSAL SENT" > 30 DAYS (need follow-up)
SELECT project_code, project_name, proposal_sent_date,
       CAST(julianday('now') - julianday(proposal_sent_date) AS INTEGER) as days_since_sent
FROM proposals
WHERE status = 'Proposal Sent'
  AND proposal_sent_date IS NOT NULL
  AND julianday('now') - julianday(proposal_sent_date) > 30
ORDER BY days_since_sent DESC;

-- STATUS DISTRIBUTION
SELECT status, COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM proposals), 1) as pct
FROM proposals
GROUP BY status
ORDER BY count DESC;

-- COUNTRY DISTRIBUTION (active proposals)
SELECT country, COUNT(*) as count
FROM proposals
WHERE status NOT IN ('Lost', 'Declined', 'Dormant', 'Contract Signed')
GROUP BY country
ORDER BY count DESC;

-- PROPOSALS BY FIRST CONTACT MONTH (pipeline velocity)
SELECT strftime('%Y-%m', first_contact_date) as month,
       COUNT(*) as new_proposals,
       SUM(CASE WHEN status = 'Contract Signed' THEN 1 ELSE 0 END) as converted
FROM proposals
WHERE first_contact_date IS NOT NULL
GROUP BY month
ORDER BY month DESC
LIMIT 12;
```

### Step 3: Generate Report

```
## Proposal Audit Report - [DATE]

### Pipeline Summary
| Status | Count | % |
|--------|-------|---|
[Status distribution]

### Active Pipeline Value
Total value of active proposals: $X

### Issues Found

#### Missing Contact Info (X proposals)
[List]

#### Zero Emails (X proposals)
[List]

#### Stale - Should Be Dormant? (X proposals)
[List with days silent]

#### Proposal Sent > 30 Days (X proposals)
[List - need follow-up]

### Geographic Distribution
[Country breakdown]

### Recommendations
1. [Mark X proposals as Dormant]
2. [Follow up on X proposals]
3. [Fill in missing contact info for X proposals]
```

### Step 4: Suggest Status Changes

For any proposal that looks wrong, suggest a status change:
- 90+ days silent + active status → Suggest "Dormant"
- 0 emails + "Proposal Sent" → Flag as suspicious
- "Contract Signed" but no project exists → Flag for project creation

## Always Name Projects

When listing proposals, always use format:
`25 BK-033 (Ritz-Carlton Reserve Nusa Dua)` - not just the code.
