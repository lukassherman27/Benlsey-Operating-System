# Email Intelligence Agent

**Owner:** Email processing, categorization, linking, and AI training pipeline
**Goal:** Make email categorization and linking so accurate it's "overwhelmingly easy"

---

## Current State (Audit Results)

### Email Statistics
| Metric | Count | % |
|--------|-------|---|
| Total emails | 3,356 | 100% |
| Linked to projects | 521 | 16% |
| Linked to proposals | 1,723 | 51% |
| **Linked (either)** | 1,754 | **52%** |
| **Unlinked** | 1,602 | **48%** |
| With full body | 3,292 | 98% |
| AI categorized | 3,356 | 100% |

### AI Training Data
| Table | Records | Notes |
|-------|---------|-------|
| `training_data` | 3,576 | Raw training examples |
| `training_data_feedback` | 0 | **No feedback collected!** |
| `user_feedback` | 5 | Minimal |
| `ai_suggestions` | 973 | Suggestions generated |
| `ai_suggestions_queue` | 3,450 | **Queue not processed!** |
| `learned_patterns` | 1 | Almost nothing learned |

### Key Problems
1. **48% of emails unlinked** - 1,602 emails not connected to any project/proposal
2. **No feedback loop** - `training_data_feedback` is empty
3. **Suggestions queue backed up** - 3,450 items never processed
4. **No pattern learning** - Only 1 pattern in `learned_patterns`
5. **Human approval not improving AI** - Feedback not being used

---

## Files to Read First

### Core Services (understand these)
```
backend/services/email_content_processor.py      # Main email processor
backend/services/email_content_processor_smart.py # Smart processor variant
backend/services/email_intelligence_service.py   # Intelligence/validation
backend/services/email_importer.py               # Email import
backend/services/training_data_service.py        # Training data management
backend/core/bensley_brain.py                    # Unified context provider
```

### Scripts
```
scripts/core/smart_email_brain.py                # Email brain logic
scripts/core/continuous_email_processor.py       # Continuous processing
scripts/core/email_meeting_extractor.py          # Meeting extraction
```

### Database Schema
```sql
-- Run these to understand the schema:
.schema emails
.schema email_content
.schema email_project_links
.schema email_proposal_links
.schema training_data
.schema training_data_feedback
.schema ai_suggestions
.schema ai_suggestions_queue
.schema learned_patterns
```

---

## Ideas for Linking the 1,602 Unlinked Emails

### Strategy 1: Sender-Based Matching
```
For each unlinked email:
1. Get sender_email
2. Look up sender in contacts table
3. Find projects/proposals linked to that contact
4. If single match → auto-link with high confidence
5. If multiple matches → add to suggestions queue for human review
```

**Why this works:** Most emails from a client are about their project

### Strategy 2: Subject Line Parsing
```
For each unlinked email:
1. Extract project codes from subject (e.g., "BK-023", "25 BK-001")
2. Match to projects/proposals table
3. Auto-link if exact match found
```

**Regex patterns:**
- `\b(BK[-_]?\d{3,4})\b` - Standard BK codes
- `\b(\d{2}\s*BK[-_]?\d{3})\b` - Year-prefixed codes

### Strategy 3: Thread-Based Linking
```
For each unlinked email:
1. Check if email is part of a thread (thread_id)
2. Find other emails in same thread
3. If any thread email is linked → link this one too
```

**Why this works:** Replies to linked emails should have same project

### Strategy 4: Content Similarity (ML)
```
For each unlinked email:
1. Get embeddings of email content
2. Compare to embeddings of linked emails
3. Find most similar linked email
4. If similarity > threshold → suggest same project
```

**Requires:** Running embeddings script, similarity search

### Strategy 5: AI-Powered Classification
```
For each unlinked email:
1. Send to Claude/GPT with context:
   - Email subject + body
   - List of all active projects with descriptions
   - Sender history
2. Ask AI to classify to most likely project
3. Return confidence score
```

---

## Ideas for Improving AI Training

### Problem: Feedback Loop Not Working

The system generates suggestions but:
- `ai_suggestions_queue`: 3,450 items waiting
- `training_data_feedback`: 0 records
- Human approvals not being captured

### Fix 1: Process the Suggestions Queue
```python
# In suggestions UI:
# When user approves/rejects a suggestion:
1. Record in training_data_feedback
2. Update learned_patterns
3. Remove from queue
4. If approved → apply the suggestion
```

### Fix 2: Build Pattern Learning
```python
# When user approves email → project link:
patterns_to_learn = [
    (sender_email → project_code),
    (sender_domain → client_company),
    (subject_keywords → category),
]
# Store in learned_patterns table
# Use patterns for future auto-classification
```

### Fix 3: Confidence Escalation
```
Low confidence (<50%)  → Queue for human review
Medium (50-80%)        → Auto-apply, show in "recent actions" for undo
High (>80%)            → Auto-apply silently
```

### Fix 4: Active Learning
```
1. Find emails AI is uncertain about
2. Present to user for classification
3. Use response to train model
4. Prioritize edge cases over easy ones
```

---

## Implementation Plan

### Phase 1: Link Existing Emails (Quick Wins)
1. **Sender matching** - Match unlinked emails by sender to known contacts
2. **Subject parsing** - Extract project codes from subjects
3. **Thread linking** - Link emails in same thread as linked emails

Expected impact: Link 500-800 more emails (30-50% of unlinked)

### Phase 2: Fix Feedback Loop
1. **Process suggestions queue** - Clear the 3,450 backlog
2. **Capture feedback** - When user approves/rejects, record it
3. **Update patterns** - Use feedback to build `learned_patterns`

### Phase 3: Improve Classification
1. **Confidence thresholds** - Auto-apply high confidence, queue low
2. **Better context** - Use Bensley Brain for full project context
3. **Pattern matching** - Use learned patterns before AI

### Phase 4: Advanced ML (Future)
1. **Embeddings** - Create email embeddings for similarity search
2. **Fine-tuning** - Use training data to fine-tune classifier
3. **Active learning** - Prioritize uncertain cases for human review

---

## Key Questions to Answer

1. **Why are suggestions not being processed?**
   - Is the UI broken?
   - Is there no UI?
   - Is the processing script not running?

2. **Why is feedback not being recorded?**
   - Check: Does the approve/reject flow call `training_data_service`?
   - Check: Are there API endpoints for feedback?

3. **What triggers email processing?**
   - On import?
   - On schedule?
   - Manual only?

4. **How does the AI currently categorize?**
   - What prompt is used?
   - What context is provided?
   - How is confidence calculated?

---

## API Endpoints to Check

```
GET  /api/emails/validation-queue      # Emails needing review
POST /api/emails/{id}/category         # Set category
POST /api/emails/{id}/link             # Link to project
GET  /api/admin/validation/suggestions # View suggestions
POST /api/training/feedback            # Submit feedback
```

---

## Database Queries for Investigation

```sql
-- Unlinked emails by sender domain
SELECT
    SUBSTR(sender_email, INSTR(sender_email, '@')+1) as domain,
    COUNT(*) as count
FROM emails
WHERE email_id NOT IN (SELECT email_id FROM email_project_links)
  AND email_id NOT IN (SELECT email_id FROM email_proposal_links)
GROUP BY domain ORDER BY count DESC LIMIT 20;

-- Unlinked emails with attachments (high value)
SELECT COUNT(*) FROM emails
WHERE email_id NOT IN (SELECT email_id FROM email_project_links)
  AND email_id NOT IN (SELECT email_id FROM email_proposal_links)
  AND has_attachments = 1;

-- Categories of unlinked emails
SELECT category, COUNT(*) as count FROM emails
WHERE email_id NOT IN (SELECT email_id FROM email_project_links)
  AND email_id NOT IN (SELECT email_id FROM email_proposal_links)
GROUP BY category ORDER BY count DESC;

-- Check if suggestions are actionable
SELECT suggestion_type, COUNT(*) as count
FROM ai_suggestions_queue
GROUP BY suggestion_type;

-- Training data by type
SELECT task_type, COUNT(*) as count
FROM training_data
GROUP BY task_type;
```

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Emails linked | 52% | 90%+ |
| Suggestions queue | 3,450 | <100 |
| Feedback records | 0 | 500+ |
| Learned patterns | 1 | 50+ |
| Auto-link accuracy | Unknown | 95%+ |

---

## Commands to Run

```bash
# Test Bensley Brain stats
python3 backend/core/bensley_brain.py

# Run email processor with brain context (sample)
python3 -c "
from backend.services.email_content_processor import EmailContentProcessor
processor = EmailContentProcessor('database/bensley_master.db')
processor.process_batch_with_brain(limit=10)
"

# Check current email categories
sqlite3 database/bensley_master.db "SELECT category, COUNT(*) FROM emails GROUP BY category ORDER BY COUNT(*) DESC;"
```

---

## Notes for the Agent

1. **Don't break existing functionality** - Test changes on small batches first
2. **Log everything** - Add logging to track what's being linked/categorized
3. **Confidence scores are key** - Always track how confident the system is
4. **Human approval is gold** - Every human decision is training data
5. **Start simple** - Sender matching alone could link 500+ emails
