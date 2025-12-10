# Email Cleanup and Categorization Session

You are helping clean up and categorize emails in the Bensley Operating System database.

## CONTEXT
- Database: `database/bensley_master.db`
- 64 stale pending suggestions from Dec 3 that need rejecting
- 274 uncategorized emails (category IS NULL)
- ~950 internal emails that may need project links even though they're internal

## STEP 1: Reject Stale Suggestions

First, reject all 64 pending suggestions - they're from Dec 3 and the user has already manually updated proposals since then.

```python
import sqlite3
conn = sqlite3.connect('database/bensley_master.db')
cursor = conn.cursor()

# Reject all pending suggestions older than 3 days
cursor.execute("""
    UPDATE ai_suggestions
    SET status = 'rejected',
        rejection_reason = 'Batch rejected - stale suggestions from Dec 3, proposals already manually updated'
    WHERE status = 'pending'
""")
print(f"Rejected {cursor.rowcount} stale suggestions")
conn.commit()
conn.close()
```

Confirm this was done, then move to Step 2.

## STEP 2: Show Uncategorized Emails

Show the user the 274 uncategorized emails in batches of 20, grouped by sender pattern:

```python
import sqlite3
conn = sqlite3.connect('database/bensley_master.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
    SELECT email_id, subject, sender_email, recipient_emails, date,
           CASE
               WHEN sender_email LIKE '%bensley%' AND recipient_emails LIKE '%bensley%' THEN 'internal'
               WHEN sender_email LIKE '%bensley%' THEN 'outbound'
               ELSE 'inbound'
           END as direction
    FROM emails
    WHERE category IS NULL
    ORDER BY direction, date DESC
""")

emails = cursor.fetchall()
print(f"Found {len(emails)} uncategorized emails")

# Group by direction
internal = [e for e in emails if e['direction'] == 'internal']
outbound = [e for e in emails if e['direction'] == 'outbound']
inbound = [e for e in emails if e['direction'] == 'inbound']

print(f"- Internal (bensley→bensley): {len(internal)}")
print(f"- Outbound (bensley→external): {len(outbound)}")
print(f"- Inbound (external→bensley): {len(inbound)}")
```

## STEP 3: Categorize In Batches

For each email, determine:

### A) If INTERNAL (bensley→bensley), which internal category?
- **INT-OPS**: scheduling, daily work, resource allocation, BOS system
- **INT-FIN**: invoices, payments, accounting, expenses
- **INT-MKTG**: reels, instagram, social media, branding, PR
- **INT-LEGAL**: contracts, disputes, legal matters
- **INT-BILL**: Bill's personal matters (Bali land, Shintamani)

### B) If EXTERNAL, which category + project?
- **meeting**: meeting requests, scheduling calls
- **contract**: agreements, terms, signatures
- **design**: drawings, renders, design feedback
- **financial**: invoices, payments, budgets
- **rfi**: requests for information
- **general**: other project communication

### C) IMPORTANT: Even internal emails may reference projects!
Look for project codes like "25 BK-070" or project names. If found:
1. Set the internal category
2. ALSO create a link to that project

## STEP 4: Apply Categories

For each batch, use SQL like:

```python
# Single email category update
cursor.execute("""
    UPDATE emails SET category = ? WHERE email_id = ?
""", ('internal', email_id))

# For internal emails, also add to email_internal_links
cursor.execute("""
    INSERT INTO email_internal_links (email_id, category_id, confidence_score, match_method)
    VALUES (?, ?, 1.0, 'manual_cli_review')
""", (email_id, category_id))  # category_id: 1=INT-FIN, 2=INT-OPS, 3=INT-LEGAL, 4=INT-MKTG, 5=INT-BILL

# If internal email ALSO references a project, create project link too
cursor.execute("""
    INSERT OR IGNORE INTO email_project_links (email_id, project_id, confidence_score, link_source)
    SELECT ?, project_id, 0.9, 'manual_cli_internal_reference'
    FROM projects WHERE project_code = ?
""", (email_id, project_code))
```

## STEP 5: Document Patterns Learned

As you categorize, note patterns like:
- "Daily work" in subject + @bensley sender = INT-OPS
- "Schedule" in subject + internal = INT-OPS
- "Reels" or "Instagram" = INT-MKTG
- Invoice number pattern = INT-FIN

These will be used to build automated rules.

## INTERNAL CATEGORY IDs (for email_internal_links)
1 = INT-FIN (Financials)
2 = INT-OPS (Operations)
3 = INT-LEGAL (Legal)
4 = INT-MKTG (Marketing)
5 = INT-BILL (Bill Personal)

## GO!
Start with Step 1 (reject stale suggestions), then work through the uncategorized emails with the user.
