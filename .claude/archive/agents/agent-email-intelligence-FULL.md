# Email Intelligence Agent - Full Implementation Guide

**Owner:** Email processing, categorization, linking, and AI training pipeline
**Goal:** Make email categorization and linking so accurate it's "overwhelmingly easy"
**Priority:** CRITICAL - The feedback loop is completely broken

---

## CRITICAL AUDIT FINDINGS (Nov 27, 2025)

### The Duplicate Crisis
| Metric | Value | Problem |
|--------|-------|---------|
| Total contact suggestions | 1,786 | - |
| Unique emails in suggestions | **237** | - |
| **Duplicate rate** | **87%** | System is useless |

**Worst offenders (same person suggested 30-50 times!):**
- Madhavi Y: 52 duplicates
- Amigo Wang: 45 duplicates
- Keith Ying: 41 duplicates
- Nigel Franklyn: 37 duplicates

**ROOT CAUSE:** `smart_email_brain.py` creates a suggestion EVERY time it sees a contact, without checking if:
1. Contact already exists in `contacts` table
2. Contact was already suggested (pending in queue)
3. Contact was previously rejected

### The Feedback Loop is Dead
| Metric | Count | Problem |
|--------|-------|---------|
| Pending suggestions | 3,450 | Overwhelming |
| Approved | 13 | Nobody uses it |
| Rejected | 1 | Nobody uses it |
| Human-approved emails | **0** | Zero feedback! |
| Learned patterns | 1 | Nothing learned |
| Training feedback records | **0** | No training! |

**WHY:** Users see 3,400+ suggestions, 87% duplicates, give up immediately.

### Email Linking Status
| Metric | Count | % |
|--------|-------|---|
| Total emails | 3,356 | 100% |
| Linked to projects | 521 | 16% |
| Linked to proposals | 1,723 | 51% |
| **Total linked** | 1,754 | **52%** |
| **Unlinked** | 1,602 | **48%** |
| With full body | 3,292 | 98% |
| AI categorized | 3,356 | 100% |

---

## PHASE 1: EMERGENCY FIXES (Do First!)

### Fix 1.1: Clean Up Duplicate Suggestions NOW

```sql
-- Step 1: Count duplicates before cleanup
SELECT 'Before cleanup:' as status, COUNT(*) as total FROM ai_suggestions_queue;

-- Step 2: Delete duplicates (keep oldest)
DELETE FROM ai_suggestions_queue
WHERE suggestion_id NOT IN (
    SELECT MIN(suggestion_id)
    FROM ai_suggestions_queue
    WHERE field_name = 'new_contact'
    GROUP BY json_extract(suggested_value, '$.email')
)
AND field_name = 'new_contact';

-- Step 3: Also dedupe project_alias suggestions
DELETE FROM ai_suggestions_queue
WHERE suggestion_id NOT IN (
    SELECT MIN(suggestion_id)
    FROM ai_suggestions_queue
    WHERE field_name = 'project_alias'
    GROUP BY suggested_value
)
AND field_name = 'project_alias';

-- Step 4: Verify cleanup
SELECT 'After cleanup:' as status, COUNT(*) as total FROM ai_suggestions_queue;
```

**Expected result:** Queue drops from 3,450 → ~400

### Fix 1.2: Prevent Future Duplicates

**File to modify:** `scripts/core/smart_email_brain.py`

Find the contact suggestion creation code and add dedup check:

```python
def create_contact_suggestion(self, email: str, name: str, company: str, project_code: str):
    """Create contact suggestion with dedup check"""
    conn = self.get_connection()
    cursor = conn.cursor()

    # CHECK 1: Already in contacts table?
    cursor.execute("SELECT 1 FROM contacts WHERE LOWER(email) = LOWER(?)", (email,))
    if cursor.fetchone():
        return None  # Already exists

    # CHECK 2: Already pending in suggestions?
    cursor.execute("""
        SELECT 1 FROM ai_suggestions_queue
        WHERE field_name = 'new_contact'
        AND json_extract(suggested_value, '$.email') = ?
        AND status = 'pending'
    """, (email,))
    if cursor.fetchone():
        return None  # Already suggested

    # CHECK 3: Previously rejected?
    cursor.execute("""
        SELECT 1 FROM ai_suggestions_queue
        WHERE field_name = 'new_contact'
        AND json_extract(suggested_value, '$.email') = ?
        AND status = 'rejected'
    """, (email,))
    if cursor.fetchone():
        return None  # Was rejected, don't suggest again

    # OK to create suggestion
    # ... existing code ...
```

### Fix 1.3: Auto-Approve Obvious Contacts

Add to the contact creation flow:

```python
def should_auto_approve_contact(self, email: str, company: str, project_code: str) -> bool:
    """
    Auto-approve if:
    1. Email domain matches an existing contact from same company
    2. Project code is actively being worked on
    3. Confidence > 0.9
    """
    conn = self.get_connection()
    cursor = conn.cursor()

    # Get domain
    domain = email.split('@')[1].lower() if '@' in email else None
    if not domain:
        return False

    # Check if domain matches existing contact's company
    cursor.execute("""
        SELECT 1 FROM contacts c
        JOIN proposals p ON c.contact_id = p.primary_contact_id
        WHERE LOWER(c.email) LIKE ?
        AND p.status IN ('active', 'drafting', 'sent', 'negotiating')
        LIMIT 1
    """, (f'%@{domain}',))

    return cursor.fetchone() is not None
```

---

## PHASE 2: Email Linking Strategies

### Strategy 2.1: Sender-Based Matching (Quick Win)

```python
def link_emails_by_sender(self):
    """Link unlinked emails by matching sender to known contacts"""
    conn = self.get_connection()
    cursor = conn.cursor()

    # Find unlinked emails where sender is a known contact
    cursor.execute("""
        SELECT DISTINCT e.email_id, e.sender_email, c.contact_id,
               p.project_code, p.proposal_id
        FROM emails e
        JOIN contacts c ON LOWER(e.sender_email) = LOWER(c.email)
        JOIN proposals p ON c.contact_id = p.primary_contact_id
        WHERE e.email_id NOT IN (SELECT email_id FROM email_project_links)
          AND e.email_id NOT IN (SELECT email_id FROM email_proposal_links)
    """)

    links_created = 0
    for row in cursor.fetchall():
        # Create link with high confidence
        cursor.execute("""
            INSERT INTO email_proposal_links (email_id, proposal_id, confidence, link_type)
            VALUES (?, ?, 0.95, 'sender_match')
        """, (row['email_id'], row['proposal_id']))
        links_created += 1

    conn.commit()
    return links_created
```

**Expected impact:** 300-500 new links

### Strategy 2.2: Subject Line Project Code Extraction

```python
import re

def link_emails_by_subject_code(self):
    """Extract BK codes from subjects and link"""
    conn = self.get_connection()
    cursor = conn.cursor()

    # Patterns for BK codes
    patterns = [
        r'\b(\d{2}\s*BK[-_]?\d{3})\b',  # "25 BK-001"
        r'\b(BK[-_]?\d{3,4})\b',         # "BK-001" or "BK-0001"
    ]

    cursor.execute("""
        SELECT email_id, subject FROM emails
        WHERE email_id NOT IN (SELECT email_id FROM email_project_links)
          AND email_id NOT IN (SELECT email_id FROM email_proposal_links)
          AND subject IS NOT NULL
    """)

    links_created = 0
    for row in cursor.fetchall():
        subject = row['subject']
        for pattern in patterns:
            match = re.search(pattern, subject, re.IGNORECASE)
            if match:
                code = match.group(1).upper().replace(' ', ' ')
                # Normalize to "XX BK-XXX" format
                code = re.sub(r'(\d{2})\s*(BK)[-_]?(\d{3})', r'\1 \2-\3', code)

                # Find matching proposal
                cursor.execute("""
                    SELECT proposal_id FROM proposals
                    WHERE project_code LIKE ?
                """, (f'%{code}%',))

                result = cursor.fetchone()
                if result:
                    cursor.execute("""
                        INSERT INTO email_proposal_links (email_id, proposal_id, confidence, link_type)
                        VALUES (?, ?, 0.99, 'subject_code')
                    """, (row['email_id'], result['proposal_id']))
                    links_created += 1
                break

    conn.commit()
    return links_created
```

**Expected impact:** 200-400 new links

### Strategy 2.3: Thread-Based Linking

```python
def link_emails_by_thread(self):
    """If any email in thread is linked, link all others"""
    conn = self.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        -- Find unlinked emails that share a thread with linked emails
        SELECT DISTINCT
            e.email_id,
            epl.proposal_id
        FROM emails e
        JOIN emails linked_e ON e.thread_id = linked_e.thread_id
        JOIN email_proposal_links epl ON linked_e.email_id = epl.email_id
        WHERE e.email_id NOT IN (SELECT email_id FROM email_proposal_links)
          AND e.thread_id IS NOT NULL
    """)

    links_created = 0
    for row in cursor.fetchall():
        cursor.execute("""
            INSERT INTO email_proposal_links (email_id, proposal_id, confidence, link_type)
            VALUES (?, ?, 0.90, 'thread_link')
        """, (row['email_id'], row['proposal_id']))
        links_created += 1

    conn.commit()
    return links_created
```

**Expected impact:** 100-300 new links

---

## PHASE 3: Fix the Feedback Loop

### 3.1: When User Approves a Suggestion

**File to modify:** `backend/services/ai_learning_service.py` (approve_suggestion method)

```python
def approve_suggestion(self, suggestion_id: int, reviewed_by: str, edits: dict = None):
    """
    Approve suggestion AND capture feedback for learning
    """
    # Get the suggestion
    suggestion = self.get_suggestion(suggestion_id)
    if not suggestion:
        return {'success': False, 'error': 'Not found'}

    # 1. Apply the suggestion
    if suggestion['field_name'] == 'new_contact':
        self._apply_contact_suggestion(suggestion, edits)
    elif suggestion['field_name'] == 'project_alias':
        self._apply_alias_suggestion(suggestion, edits)

    # 2. Record feedback for training
    self._record_feedback(
        suggestion_id=suggestion_id,
        action='approved',
        reviewed_by=reviewed_by,
        original_value=suggestion['suggested_value'],
        final_value=edits or suggestion['suggested_value']
    )

    # 3. Create learned pattern
    self._create_pattern_from_approval(suggestion)

    # 4. Update suggestion status
    self._update_suggestion_status(suggestion_id, 'approved', reviewed_by)

    return {'success': True, 'message': 'Applied and learned'}

def _record_feedback(self, suggestion_id, action, reviewed_by, original_value, final_value):
    """Record feedback for future training"""
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO training_data_feedback (
                suggestion_id, action, reviewed_by,
                original_value, final_value, created_at
            ) VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (suggestion_id, action, reviewed_by,
              json.dumps(original_value), json.dumps(final_value)))
        conn.commit()

def _create_pattern_from_approval(self, suggestion):
    """Create learned pattern from approved suggestion"""
    if suggestion['field_name'] == 'new_contact':
        value = json.loads(suggestion['suggested_value'])
        email = value.get('email', '')
        domain = email.split('@')[1] if '@' in email else None
        company = value.get('company', '')
        project = value.get('related_project', '')

        if domain and company:
            # Learn: emails from this domain → this company
            self._save_pattern(
                pattern_type='email_domain_company',
                condition=f"sender_domain = '{domain}'",
                action=f"company = '{company}'",
                confidence=0.8
            )

        if domain and project:
            # Learn: emails from this domain → this project
            self._save_pattern(
                pattern_type='email_domain_project',
                condition=f"sender_domain = '{domain}'",
                action=f"project_code = '{project}'",
                confidence=0.7
            )
```

### 3.2: Tiered Auto-Processing

```python
def process_suggestion_by_confidence(self, suggestion):
    """
    Process based on confidence level:
    - High (>0.9): Auto-apply
    - Medium (0.7-0.9): Apply + queue for review
    - Low (<0.7): Queue for human review only
    """
    confidence = suggestion.get('confidence', 0)

    if confidence >= 0.9:
        # Auto-apply high confidence
        self.auto_apply_suggestion(suggestion)
        return 'auto_applied'

    elif confidence >= 0.7:
        # Apply but mark for optional review
        self.apply_with_review_option(suggestion)
        return 'applied_pending_review'

    else:
        # Just queue for human review
        return 'queued'
```

---

## PHASE 4: Smart Categorization Tiers

Create a new categorization flow:

```python
class EmailCategorizer:
    """Three-tier email categorization"""

    def categorize(self, email: dict) -> dict:
        # TIER 1: Obvious patterns (no AI needed)
        result = self._tier1_patterns(email)
        if result['confident']:
            return result

        # TIER 2: Database matching (fast lookup)
        result = self._tier2_database_match(email)
        if result['confident']:
            return result

        # TIER 3: AI classification (expensive, last resort)
        return self._tier3_ai_classify(email)

    def _tier1_patterns(self, email: dict) -> dict:
        """Instant categorization for obvious cases"""
        sender = email.get('sender_email', '').lower()
        subject = email.get('subject', '').lower()

        # Social media / newsletters → Auto-ignore
        ignore_domains = ['linkedin.com', 'facebook.com', 'twitter.com',
                         'mailchimp.com', 'sendgrid.com', 'noreply']
        if any(d in sender for d in ignore_domains):
            return {'category': 'social_newsletter', 'confidence': 0.99, 'confident': True}

        # Bensley internal
        if '@bensley.com' in sender:
            return {'category': 'internal', 'confidence': 0.99, 'confident': True}

        # Invoices
        if 'invoice' in subject or 'payment' in subject:
            return {'category': 'financial', 'confidence': 0.95, 'confident': True}

        # Meeting requests
        if any(word in subject for word in ['meeting', 'call', 'zoom', 'teams']):
            return {'category': 'meeting', 'confidence': 0.90, 'confident': True}

        return {'confident': False}

    def _tier2_database_match(self, email: dict) -> dict:
        """Match against known contacts/projects"""
        sender = email.get('sender_email', '').lower()

        # Check if sender is known contact
        contact = self.db.execute("""
            SELECT c.*, p.project_code, p.project_name
            FROM contacts c
            JOIN proposals p ON c.contact_id = p.primary_contact_id
            WHERE LOWER(c.email) = ?
        """, (sender,)).fetchone()

        if contact:
            return {
                'category': 'project',
                'project_code': contact['project_code'],
                'confidence': 0.95,
                'confident': True,
                'reason': f"Known contact for {contact['project_name']}"
            }

        # Check domain against companies
        domain = sender.split('@')[1] if '@' in sender else None
        if domain:
            company = self.db.execute("""
                SELECT client_company, project_code
                FROM proposals
                WHERE LOWER(client_company) LIKE ?
                LIMIT 1
            """, (f'%{domain.split(".")[0]}%',)).fetchone()

            if company:
                return {
                    'category': 'project',
                    'project_code': company['project_code'],
                    'confidence': 0.80,
                    'confident': True,
                    'reason': f"Domain matches {company['client_company']}"
                }

        return {'confident': False}

    def _tier3_ai_classify(self, email: dict) -> dict:
        """AI classification as last resort"""
        # ... existing AI code ...
        pass
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `scripts/core/smart_email_brain.py` | Add dedup checks, auto-approve logic |
| `backend/services/ai_learning_service.py` | Fix feedback recording, add pattern learning |
| `backend/services/email_content_processor.py` | Add tiered categorization |
| `backend/api/main.py` | Ensure approve endpoints record feedback |

---

## SQL Queries for Investigation

```sql
-- Unlinked emails by sender domain (find patterns)
SELECT
    SUBSTR(sender_email, INSTR(sender_email, '@')+1) as domain,
    COUNT(*) as count
FROM emails
WHERE email_id NOT IN (SELECT email_id FROM email_project_links)
  AND email_id NOT IN (SELECT email_id FROM email_proposal_links)
GROUP BY domain ORDER BY count DESC LIMIT 20;

-- Categories of unlinked emails
SELECT category, COUNT(*) as count FROM emails
WHERE email_id NOT IN (SELECT email_id FROM email_project_links)
  AND email_id NOT IN (SELECT email_id FROM email_proposal_links)
GROUP BY category ORDER BY count DESC;

-- Contacts that could link emails
SELECT c.email, c.name, p.project_code, p.project_name,
       (SELECT COUNT(*) FROM emails WHERE LOWER(sender_email) = LOWER(c.email)) as email_count
FROM contacts c
JOIN proposals p ON c.contact_id = p.primary_contact_id
WHERE c.email IS NOT NULL
ORDER BY email_count DESC
LIMIT 20;

-- Duplicate suggestions to clean
SELECT json_extract(suggested_value, '$.email') as email, COUNT(*) as dupes
FROM ai_suggestions_queue
WHERE field_name = 'new_contact'
GROUP BY email
HAVING COUNT(*) > 1
ORDER BY dupes DESC;
```

---

## Success Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Suggestions queue | 3,450 | <100 | `SELECT COUNT(*) FROM ai_suggestions_queue WHERE status='pending'` |
| Duplicate rate | 87% | 0% | Should never create duplicate suggestions |
| Emails linked | 52% | 90%+ | `SELECT COUNT(*) FROM email_proposal_links` / total emails |
| Feedback records | 0 | 500+ | `SELECT COUNT(*) FROM training_data_feedback` |
| Learned patterns | 1 | 50+ | `SELECT COUNT(*) FROM learned_patterns` |
| Auto-approve rate | 0% | 60%+ | High confidence suggestions auto-applied |

---

## Implementation Order

1. **FIRST (5 min):** Run SQL to clean duplicate suggestions
2. **SECOND (30 min):** Add dedup check to smart_email_brain.py
3. **THIRD (30 min):** Implement sender-based email linking
4. **FOURTH (30 min):** Implement subject code extraction linking
5. **FIFTH (1 hr):** Fix feedback recording in approve flow
6. **SIXTH (1 hr):** Add tiered categorization

---

## Testing Commands

```bash
# Test dedup query first
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM ai_suggestions_queue;"

# After cleanup
sqlite3 database/bensley_master.db "SELECT field_name, COUNT(*) FROM ai_suggestions_queue GROUP BY field_name;"

# Test email linking
python3 -c "
from backend.services.email_intelligence_service import EmailIntelligenceService
svc = EmailIntelligenceService('database/bensley_master.db')
print('Unlinked emails:', svc.get_unlinked_count())
"

# Test pattern learning
sqlite3 database/bensley_master.db "SELECT * FROM learned_patterns ORDER BY created_at DESC LIMIT 10;"
```
