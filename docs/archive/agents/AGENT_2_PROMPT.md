# AGENT 2: Database Schema Migration

**Your Mission:** Create and run database schema unification migration

**What You're Building:**
- `database/migrations/026_email_proposal_unification.sql` - Schema improvements for email-proposal integration

**CRITICAL RULES:**
- ✅ Test migration on backup database first
- ✅ Create indexes for performance
- ❌ DO NOT drop existing tables
- ❌ DO NOT delete existing data

---

## Task 2.1: Schema Migration

Create `database/migrations/026_email_proposal_unification.sql`:

```sql
-- Email-Proposal Integration Schema Unification
-- Created: 2025-11-26
-- Purpose: Add indexes and improve email-proposal linkage

-- Add thread_id to emails if not exists
ALTER TABLE emails ADD COLUMN thread_id INTEGER;

-- Add proposal_id to email_project_links for easier joins
ALTER TABLE email_project_links ADD COLUMN proposal_id INTEGER;

-- Update proposal_id in email_project_links from project_code
UPDATE email_project_links
SET proposal_id = (
    SELECT proposal_id
    FROM proposals
    WHERE proposals.project_code = email_project_links.project_code
)
WHERE proposal_id IS NULL;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_emails_thread_id ON emails(thread_id);
CREATE INDEX IF NOT EXISTS idx_emails_date ON emails(date DESC);
CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender_email);

CREATE INDEX IF NOT EXISTS idx_email_content_email_id ON email_content(email_id);
CREATE INDEX IF NOT EXISTS idx_email_content_category ON email_content(category);
CREATE INDEX IF NOT EXISTS idx_email_content_urgency ON email_content(urgency_level);

CREATE INDEX IF NOT EXISTS idx_email_threads_proposal ON email_threads(proposal_id);
CREATE INDEX IF NOT EXISTS idx_email_threads_root ON email_threads(root_email_id);

CREATE INDEX IF NOT EXISTS idx_email_proposal_links_email ON email_proposal_links(email_id);
CREATE INDEX IF NOT EXISTS idx_email_proposal_links_proposal ON email_proposal_links(proposal_id);

CREATE INDEX IF NOT EXISTS idx_proposal_status_history_proposal ON proposal_status_history(proposal_id);
CREATE INDEX IF NOT EXISTS idx_proposal_status_history_date ON proposal_status_history(changed_at DESC);

-- Create view for easy email-proposal joins
CREATE VIEW IF NOT EXISTS v_proposal_emails AS
SELECT
    e.email_id,
    e.subject,
    e.sender_email,
    e.date,
    e.thread_id,
    ec.ai_summary,
    ec.sentiment,
    ec.category,
    ec.urgency_level,
    p.proposal_id,
    p.project_code,
    p.project_name,
    p.current_status,
    epl.confidence_score,
    epl.link_type
FROM emails e
LEFT JOIN email_content ec ON e.email_id = ec.email_id
LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
LEFT JOIN proposals p ON epl.proposal_id = p.proposal_id
WHERE p.proposal_id IS NOT NULL;

-- Create view for email threads with proposal context
CREATE VIEW IF NOT EXISTS v_email_threads_full AS
SELECT
    et.thread_id,
    et.thread_subject,
    et.email_count,
    et.first_email_date,
    et.last_email_date,
    p.proposal_id,
    p.project_code,
    p.project_name,
    e.sender_email as root_sender
FROM email_threads et
LEFT JOIN proposals p ON et.proposal_id = p.proposal_id
LEFT JOIN emails e ON et.root_email_id = e.email_id;

-- Add comments for documentation
PRAGMA table_info(emails);
PRAGMA table_info(email_content);
PRAGMA table_info(email_threads);

-- Verification queries
SELECT 'Emails with threads: ' || COUNT(*) FROM emails WHERE thread_id IS NOT NULL;
SELECT 'Email content records: ' || COUNT(*) FROM email_content;
SELECT 'Email threads: ' || COUNT(*) FROM email_threads;
SELECT 'Proposal-email links: ' || COUNT(*) FROM email_proposal_links WHERE proposal_id IS NOT NULL;
```

---

## Test & Run Migration

**Step 1: Backup database**
```bash
cp database/bensley_master.db database/bensley_master.db.backup_pre_migration
```

**Step 2: Test on backup**
```bash
sqlite3 database/bensley_master.db.backup_pre_migration < database/migrations/026_email_proposal_unification.sql
```

**Step 3: If successful, run on real database**
```bash
sqlite3 database/bensley_master.db < database/migrations/026_email_proposal_unification.sql
```

**Step 4: Verify indexes created**
```bash
sqlite3 database/bensley_master.db ".indexes emails"
sqlite3 database/bensley_master.db ".indexes email_content"
sqlite3 database/bensley_master.db ".indexes email_threads"
```

**Step 5: Verify views created**
```bash
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM v_proposal_emails"
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM v_email_threads_full"
```

---

## SUCCESS CRITERIA

```bash
# Should show new indexes
sqlite3 database/bensley_master.db ".indexes emails" | grep idx_emails_

# Views should return data
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM v_proposal_emails"

# No errors when running migration
sqlite3 database/bensley_master.db "PRAGMA integrity_check"
```

**Report back:** "Agent 2 complete. Migration applied successfully. X indexes created, 2 views created."
