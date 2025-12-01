# Email Intelligence System - Complete Explanation

**Created:** November 25, 2025
**Purpose:** Explain the email linking, validation, and intelligence system

---

## The Big Picture

You have an **email intelligence system** that:
1. **Imports** all your emails (historical + ongoing)
2. **AI links** emails to projects/proposals automatically
3. **Validates** those links (you manually review/correct)
4. **Extracts insights** from email content (meetings, decisions, sentiment)
5. **Trains the AI** using your corrections (RLHF!)
6. **Builds project context** for querying (RAG in Phase 2)

**Goal:** Every email, attachment, meeting note linked to the right project → Complete project intelligence

---

## Database Architecture

### Core Tables

**1. `emails` (All Email Data)**
```
- email_id, message_id, thread_id
- date, sender, recipient, subject, body_full
- category (contract/invoice/design/rfi/meeting/general)
- ai_confidence, processed, has_attachments
- folder, collection, stage
```

**2. `email_project_links` (THE CRITICAL ONE)**
```sql
email_id       → Which email
project_id     → Which project it belongs to
project_code   → Project code (25-BK-018)
confidence     → 0.0 - 1.0 (how sure AI is)
link_method    → 'ai' | 'manual' | 'alias' | 'subject_match'
evidence       → "Found '25-BK-018' in subject line"
created_at     → When linked
```

**This table is what you want to review/correct in the UI!**

**3. `email_content` (AI-Extracted Intelligence)**
```sql
email_id
category         → contract/invoice/design/rfi/schedule/meeting/general
subcategory      → More specific
key_points       → JSON: ["fee discussion", "deadline set"]
entities         → JSON: {amounts: [$5M], dates: [2025-12-01], people: [Bill]}
sentiment        → positive/neutral/concerned/urgent
client_sentiment → positive/neutral/negative/frustrated
urgency_level    → low/medium/high/critical
action_required  → 0 or 1
follow_up_date   → When to follow up
ai_summary       → "Client approved design direction"
```

**4. `email_attachments` (Contract Detection)**
```sql
filename, filepath, mime_type
document_type    → bensley_contract | invoice | proposal | design_document
contract_direction → outgoing | incoming
is_signed, is_executed
extracted_text   → Full text for search
ai_summary       → What this document is
key_terms        → JSON: extracted terms, dates, amounts
proposal_id      → Links to proposal
```

**5. `email_threads` (Conversations)**
```sql
subject_normalized  → "RE: Mumbai Project Fee Discussion" → "Mumbai Project Fee Discussion"
proposal_id
emails             → JSON: [email_id_1, email_id_2, ...] in chronological order
status             → open | resolved | waiting
resolution         → "Fee agreed at $2.5M"
```

---

## The AI Linking Pipeline

### Step 1: Import Emails
**Script:** `import_all_emails.py`
- Imports from Gmail API
- Stores in `emails` table
- Extracts basic metadata
- Downloads attachments

### Step 2: AI Linking
**Script:** `ai_email_linker.py`
```python
# What it does:
1. Finds unlinked emails (no entry in email_project_links)
2. Sends to Claude API with:
   - Email subject + body
   - List of all active projects with codes
3. Claude returns:
   - Best matching project_code
   - Confidence score (0-1)
   - Evidence/reasoning
4. Creates entry in email_project_links with link_method='ai'
```

**Example:**
```
Email subject: "25-BK-018 Mumbai - Design Comments"
AI → Matches to project_id=45, project_code='25-BK-018'
Evidence: "Found project code '25-BK-018' in subject"
Confidence: 0.95
```

### Step 3: Validation (WHAT YOU WANT IN THE UI!)
**Script:** `smart_email_validator.py`

**What it does:**
- Shows you AI-linked emails
- You review: ✅ Correct or ❌ Wrong or 🔗 Change Link
- Your corrections go to `training_data` table
- Re-links if you change

**This is what the frontend "Emails" tab needs to show!**

---

## What the Frontend Needs

### 🎯 Tab 1: "Email Links" (Main View)

**Purpose:** Review and correct AI-linked emails

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Email Links - Review AI Suggestions                         │
├─────────────────────────────────────────────────────────────┤
│ Filters: [All | AI-Linked | Manual | High Confidence | Low] │
│ Search: [____________________]                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Email                     | Linked To  | Confidence | Action│
│━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│ 📧 25-BK-018 Mumbai       │ 25-BK-018  │ 95% 🟢    │ ✅ ✏️ ❌│
│    From: client@xyz.com   │ Mumbai     │ (AI)      │       │
│    Nov 24, 2025           │            │           │       │
│    "Design comments..."   │            │           │       │
│                           │            │           │       │
│ 📧 RE: Bali Fee Quote     │ 25-BK-030  │ 60% 🟡    │ ✅ ✏️ ❌│
│    From: bill@bensley...  │ Bali       │ (AI)      │       │
│    Nov 23, 2025           │            │           │       │
│    "Following up on..."   │            │           │       │
│                           │            │           │       │
│ 📧 Meeting notes          │ [None]     │ N/A       │ 🔗 Link│
│    From: bill@bensley...  │            │           │       │
│    Nov 22, 2025           │            │           │       │
│    "Met with client..."   │            │           │       │
└─────────────────────────────────────────────────────────────┘
```

**Actions:**
- ✅ **Confirm** → Marks as validated, increases training_data weight
- ✏️ **Edit Link** → Opens dialog to change project
- ❌ **Unlink** → Removes link, logs as "AI was wrong" (trains AI!)
- 🔗 **Link** → Manually link unlinked email

**Click on email → Expands to show:**
```
┌─────────────────────────────────────────────────────────────┐
│ 📧 RE: 25-BK-018 Mumbai Clubhouse - Design Comments         │
│ From: sarah@mumbaiclub.com                                  │
│ To: bill@bensley.com, team@bensley.com                      │
│ Date: November 24, 2025 10:42 AM                            │
├─────────────────────────────────────────────────────────────┤
│ Current Link: 25-BK-018 Mumbai Clubhouse ($2.5M)            │
│ Confidence: 95% (AI) - Evidence: "Found '25-BK-018' in..."  │
├─────────────────────────────────────────────────────────────┤
│ AI Insights:                                                 │
│ • Category: Design Feedback                                 │
│ • Sentiment: Positive                                       │
│ • Action Required: Yes                                      │
│ • Key Points:                                               │
│   - Client loves landscape concept                          │
│   - Wants to adjust pool placement                          │
│   - Schedule meeting for Dec 1                              │
│                                                              │
│ Attachments: (2)                                            │
│ 📎 Site_Photos.pdf (2.4 MB) - Design Document               │
│ 📎 Markups.pdf (1.1 MB) - Design Document                   │
├─────────────────────────────────────────────────────────────┤
│ Email Thread: (5 messages)                                  │
│ → Nov 18: Initial design sent                               │
│ → Nov 20: Client questions                                  │
│ → Nov 21: Bill responds                                     │
│ → Nov 23: Client requests changes                           │
│ → Nov 24: This message (design comments)                    │
├─────────────────────────────────────────────────────────────┤
│ [Change Link] [Unlink] [✅ Confirm Correct]                 │
└─────────────────────────────────────────────────────────────┘
```

---

### 🎯 Tab 2: "Email Validation" (Review Queue)

**Purpose:** Show only emails needing validation (low confidence, unlinked)

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Needs Review (47)                                            │
│ ┌────────┬────────┬─────────┬─────────┐                    │
│ │ Unlinked│Low Conf│ Medium │  High  │                     │
│ │   12    │   18   │   15   │    2   │                     │
│ └────────┴────────┴─────────┴─────────┘                    │
├─────────────────────────────────────────────────────────────┤
│ Priority Queue (Process these first):                       │
│                                                              │
│ 🔴 HIGH PRIORITY (Unlinked with attachments)                │
│ 📧 "Contract for review" - Nov 24                           │
│    📎 Contract_v3.pdf (SIGNED CONTRACT DETECTED!)           │
│    [Link to Project...]                                     │
│                                                              │
│ 🟡 MEDIUM PRIORITY (Low confidence)                         │
│ 📧 "RE: Fee discussion" - Nov 23                            │
│    AI guessed: 25-BK-030 (Confidence: 45%)                  │
│    [Review...]                                              │
│                                                              │
│ 🟢 LOW PRIORITY (Medium confidence)                         │
│ 📧 "Design update" - Nov 22                                 │
│    AI guessed: 25-BK-018 (Confidence: 72%)                  │
│    [Quick Confirm...]                                       │
└─────────────────────────────────────────────────────────────┘
```

---

### 🎯 Tab 3: "Project Email Timeline"

**Purpose:** See ALL emails for a specific project (complete context)

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Project: 25-BK-018 Mumbai Clubhouse                         │
│ Complete Email & Attachment History                         │
├─────────────────────────────────────────────────────────────┤
│ Timeline View: [Chronological ▼] | Group by: [Thread ▼]    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ ══════════════════════════════════════════════════════════  │
│ 📅 November 2025                                            │
│ ══════════════════════════════════════════════════════════  │
│                                                              │
│ Nov 24, 10:42 AM  📧 Design Comments (Thread: 5 messages)   │
│                   From: client@mumbaiclub.com               │
│                   📎 Site_Photos.pdf, Markups.pdf           │
│                   💡 Client loves concept, wants pool moved │
│                                                              │
│ Nov 23, 3:15 PM   📧 Fee Breakdown Request                  │
│                   From: bill@bensley.com                    │
│                   📎 Fee_Schedule.xlsx                      │
│                   💡 Sent detailed phase breakdown          │
│                                                              │
│ Nov 20, 9:00 AM   📧 Contract Signed! 🎉                    │
│                   From: client@mumbaiclub.com               │
│                   📎 Contract_Signed.pdf ✅ EXECUTED        │
│                   💡 Contract fully executed - $2.5M        │
│                                                              │
│ ══════════════════════════════════════════════════════════  │
│ 📅 October 2025                                             │
│ ══════════════════════════════════════════════════════════  │
│                                                              │
│ Oct 15, 2:30 PM   📧 Proposal Sent                          │
│                   From: bill@bensley.com                    │
│                   📎 Mumbai_Proposal.pdf                    │
│                   💡 Initial proposal - $2.5M value         │
│                                                              │
│ Oct 12, 11:00 AM  📧 Initial Meeting Notes                  │
│                   From: bill@bensley.com                    │
│                   💡 First contact - scope discussion       │
│                                                              │
│ ══════════════════════════════════════════════════════════  │
│                                                              │
│ 📊 Summary:                                                 │
│ • Total Emails: 47                                          │
│ • Attachments: 23 (12 design docs, 4 contracts, 7 misc)    │
│ • Key Decisions: 8 identified                               │
│ • Action Items: 3 open                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## The AI Training Loop (RLHF)

### How Your Corrections Train the AI

**Current State:**
```
Email: "RE: Bali project"
AI Links to: 25-BK-030 (Bali Resort)
Confidence: 60%
```

**You correct it:**
```
You: "No, this is actually 25-BK-040 (Bali Branding)"
```

**What happens:**
1. `email_project_links` updated:
   ```sql
   DELETE WHERE email_id=123 AND project_id=30
   INSERT (email_id=123, project_id=40, link_method='manual', evidence='User correction')
   ```

2. `training_data` logged:
   ```sql
   INSERT INTO training_data (
     feature_type='email_project_linking',
     helpful=false,
     issue_type='incorrect_project',
     feedback_text='Email about branding, not resort',
     expected_value='25-BK-040',
     current_value='25-BK-030',
     context_json='{"email_subject": "RE: Bali project", "actual_body": "..."}'
   )
   ```

3. **Phase 2 (Fine-tuning):**
   - Collect 500+ corrections like this
   - Fine-tune local Llama model
   - AI learns: "Branding emails go to branding projects, not resorts"
   - Accuracy improves from 60% → 85%+

---

## The Complete Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. IMPORT                                                    │
│ Gmail API → import_all_emails.py → emails table             │
│ Downloads attachments → email_attachments table              │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│ 2. AI LINKING                                                │
│ ai_email_linker.py:                                          │
│ - Finds unlinked emails                                      │
│ - Sends to Claude API                                        │
│ - Gets project match + confidence                            │
│ - Creates email_project_links (link_method='ai')             │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│ 3. INTELLIGENCE EXTRACTION                                   │
│ email_content table populated:                               │
│ - Category, sentiment, urgency                               │
│ - Key points, entities                                       │
│ - AI summary                                                 │
│ - Action items                                               │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│ 4. FRONTEND VALIDATION (YOU!)                                │
│ Email Links UI:                                              │
│ - Shows AI links with confidence                             │
│ - You review: ✅ Correct / ✏️ Change / ❌ Wrong             │
│ - Corrections saved to training_data                         │
│ - email_project_links updated (link_method='manual')         │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│ 5. PROJECT CONTEXT (QUERY TIME)                              │
│ When you ask: "What did the Mumbai client say about fees?"  │
│                                                              │
│ System queries:                                              │
│ - email_project_links WHERE project_code='25-BK-018'        │
│ - Gets all email_ids                                         │
│ - Joins email_content to get AI summaries + key points      │
│ - Builds context: "12 emails about fees, client approved     │
│   $2.5M on Oct 20, concerned about phase 3 costs..."        │
│ - RAG system (Phase 2) uses this for accurate answers       │
└─────────────────────────────────────────────────────────────┘
```

---

## API Endpoints Needed

### For Frontend "Email Links" Tab

**1. Get emails needing validation**
```python
GET /api/emails/validation-queue
Query params:
  - priority: high|medium|low|all
  - status: unlinked|low_confidence|all
  - limit: 50

Response:
{
  "unlinked": 12,
  "low_confidence": 18,
  "emails": [
    {
      "email_id": 123,
      "subject": "RE: Bali project",
      "sender": "client@example.com",
      "date": "2025-11-24T10:42:00",
      "linked_to": {
        "project_code": "25-BK-030",
        "project_name": "Bali Resort",
        "confidence": 0.60,
        "link_method": "ai",
        "evidence": "Found 'Bali' in subject"
      },
      "ai_insights": {
        "category": "design_feedback",
        "sentiment": "positive",
        "action_required": true
      },
      "has_attachments": true,
      "attachment_count": 2
    }
  ]
}
```

**2. Update email link**
```python
PATCH /api/emails/{email_id}/link
Body:
{
  "project_code": "25-BK-040",  // New project
  "reason": "Email about branding, not resort",
  "updated_by": "bill"
}

Action:
- Updates email_project_links
- Logs to training_data (RLHF!)
- Returns success
```

**3. Confirm AI link**
```python
POST /api/emails/{email_id}/confirm-link
Body:
{
  "confirmed_by": "bill"
}

Action:
- Marks link as validated
- Increases confidence to 1.0
- Logs positive feedback to training_data
```

**4. Get project email timeline**
```python
GET /api/projects/{project_code}/emails
Query params:
  - include_attachments: true
  - include_threads: true

Response:
{
  "project": {...},
  "emails": [
    {
      "email_id": 123,
      "date": "2025-11-24",
      "subject": "...",
      "sender": "...",
      "thread_id": 45,
      "thread_position": 3,
      "total_in_thread": 5,
      "ai_summary": "Client approved design",
      "key_points": ["loves concept", "wants pool moved"],
      "attachments": [...]
    }
  ],
  "stats": {
    "total_emails": 47,
    "total_attachments": 23,
    "contracts": 4,
    "design_docs": 12
  }
}
```

---

## Why This Matters for Queries

**Without this system:**
```
You: "What did the Mumbai client say about the pool?"
AI: "I don't have access to your emails..."
```

**With this system (Phase 2 RAG):**
```
You: "What did the Mumbai client say about the pool?"

System:
1. Finds project_code = 25-BK-018
2. Queries email_project_links → gets 47 email_ids
3. Searches email_content where "pool" mentioned → 8 emails
4. Builds context with AI summaries
5. Feeds to LLM

AI: "The client has mentioned the pool in 8 emails:
  - Oct 15: Wants infinity edge pool with ocean view
  - Nov 10: Concerned about pool deck material (teak vs stone)
  - Nov 24: **Latest - wants pool moved 5m west** for better sunset view

  Current status: Waiting on revised pool placement drawings"
```

**The email links are the foundation for intelligent querying!**

---

## Implementation Priority

### Phase 1.5 (This Week)
1. ✅ Backend endpoints for email validation
2. ✅ Frontend "Email Links" tab (basic)
3. ✅ Manual link correction UI
4. ✅ Training data logging (RLHF)

### Phase 2 (4-6 weeks)
1. ✅ RAG system using email context
2. ✅ Local LLM fine-tuning with corrections
3. ✅ Automatic project timeline generation
4. ✅ Smart email summarization

---

## Summary

**What you wanted:**
> "A place where I can see all these emails are being linked to - and manually change them if required (and this will train the AI further) and then this way we have an entire chain of like every attachment, every email context for every project"

**What you're building:**

1. **Email Links Tab** → See all AI-linked emails with confidence scores
2. **Validation Queue** → Review low-confidence links first
3. **Manual Correction** → Change wrong links (trains AI via RLHF!)
4. **Project Timeline** → See complete email history per project
5. **Attachment Tracking** → All contracts, designs, docs linked
6. **Context Building** → Foundation for intelligent queries in Phase 2

**End Result:**
- Every email correctly linked to projects
- Complete project communication history
- AI learns from your corrections
- Can query: "Show me all emails about fees for Mumbai project"
- Can ask: "What did client say about design changes?"
- All context available for decision-making

---

**This is the foundation for true project intelligence!**

---

**Next Steps:**
1. Build the "Email Links" frontend tab (assign to Claude 6?)
2. Create validation queue API endpoints
3. Implement manual correction workflow
4. Connect to RLHF training_data table

Ready to build this?
