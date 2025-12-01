# AI & Agents Context Bundle

**Owner:** Intelligence Agent
**Last Updated:** 2025-12-01
**Key Files:** `backend/core/bensley_brain.py`, `scripts/core/query_brain.py`, `backend/services/learning_service.py`

---

## AI System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI INTELLIGENCE SYSTEM                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │ OpenAI API       │    │ Query Brain      │                   │
│  │ (gpt-4o-mini)    │───▶│ Natural language │                   │
│  │ contract parsing │    │ "What's BK-070?" │                   │
│  │ email categorize │    └──────────────────┘                   │
│  └──────────────────┘                                           │
│           │                                                      │
│           ▼                                                      │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │ Bensley Brain    │───▶│ AI Suggestions   │                   │
│  │ Unified context  │    │ 152 pending      │                   │
│  │ Project intel    │    │ 8 handler types  │                   │
│  └──────────────────┘    └──────────────────┘                   │
│                                                                  │
│  FUTURE (Phase 4):                                              │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │ Local LLM        │    │ RAG System       │                   │
│  │ Llama 3.1 70B    │    │ ChromaDB         │                   │
│  │ 80% of queries   │    │ Vector search    │                   │
│  └──────────────────┘    └──────────────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Current AI Capabilities

### Working (Phase 1)
- **Email Categorization:** Auto-categorize by type (RFI, invoice, meeting, etc.)
- **Contract Parsing:** Extract terms, phases, fees from PDFs
- **Email-Project Linking:** Match emails to projects (68% linked)
- **Natural Language Query:** Basic Q&A about projects
- **Bensley Brain:** Unified context aggregation

### Not Working Yet (Phase 2-4)
- Local LLM (no Ollama)
- RAG/Vector search (no embeddings)
- Model distillation (training pipeline not built)
- Meeting transcription (no Whisper)
- Autonomous agents (6 of 8 not built)

---

## Query System (Chain of Thought)

### How Query Brain Works

```python
# scripts/core/query_brain.py

# 1. Parse user question
question = "What's happening with BK-070?"

# 2. Extract entities
entities = extract_entities(question)
# → project_code: "BK-070"

# 3. Gather context
context = {
    "project": get_project_details("BK-070"),
    "emails": get_recent_emails("BK-070", limit=10),
    "invoices": get_invoices("BK-070"),
    "timeline": get_project_timeline("BK-070"),
}

# 4. Build prompt with context
prompt = f"""
Based on this context about project {entities['project_code']}:

Project: {context['project']}
Recent Emails: {context['emails']}
Invoices: {context['invoices']}

Question: {question}

Provide a clear, concise answer.
"""

# 5. Call OpenAI API
response = openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}]
)

# 6. Return formatted response
return response.content
```

### Query Examples

| Question | Entities Extracted | Context Gathered |
|----------|-------------------|------------------|
| "What's happening with BK-070?" | project_code | project + emails + timeline |
| "Who's the PM for Grand Hyatt?" | client_name | client + contacts + projects |
| "Outstanding invoices over $100k" | amount_threshold | invoices filtered |
| "Follow-ups needed this week" | time_range | proposals + emails |

---

## Bensley Brain (Unified Context)

```python
# backend/core/bensley_brain.py

class BensleyBrain:
    """Unified intelligence layer for project context"""

    def get_project_context(self, project_code: str) -> dict:
        """Get complete context for a project"""
        return {
            "project": self._get_project(project_code),
            "proposal": self._get_proposal(project_code),
            "emails": self._get_emails(project_code),
            "invoices": self._get_invoices(project_code),
            "contacts": self._get_contacts(project_code),
            "timeline": self._get_timeline(project_code),
            "rfis": self._get_rfis(project_code),
            "meetings": self._get_meetings(project_code),
            "documents": self._get_documents(project_code),
        }

    def answer_question(self, question: str) -> str:
        """Natural language Q&A"""
        # Extract entities, gather context, call OpenAI
        ...
```

---

## AI Database Tables

### Suggestions Queue
```sql
-- ai_suggestions (152 pending after Dec 1 cleanup)
-- 7,758 rejected (mostly junk follow_up_needed)
suggestion_id, suggestion_type, priority, confidence_score,
source_type, source_id, source_reference,
title, description, suggested_action, suggested_data,
target_table, target_id, project_code, proposal_id,
status ('pending', 'approved', 'rejected', 'modified'),
reviewed_by, reviewed_at, review_notes,
rollback_data, is_actionable, created_at, expires_at
```

---

## Suggestion Handlers (NEW Dec 2025)

Located in: `backend/services/suggestion_handlers/`

| Handler | Type | Action |
|---------|------|--------|
| `task_handler.py` | `follow_up_needed` | Creates task in `tasks` table |
| `transcript_handler.py` | `transcript_link` | Links transcript to proposal |
| `contact_handler.py` | `new_contact` | Creates contact record |
| `proposal_handler.py` | `fee_change` | Updates proposal fee |
| `deadline_handler.py` | `deadline_detected` | Creates deadline task |
| `info_handler.py` | `info` | Non-actionable, just info |
| `email_link_handler.py` | `email_link` | Links email to proposal/project |
| `status_handler.py` | `proposal_status_update` | Updates proposal status |

### Handler Pattern
```python
# All handlers inherit from SuggestionHandler base class
class FeeChangeHandler(SuggestionHandler):
    suggestion_type = "fee_change"

    def validate(self, suggestion, data) -> bool:
        return 'new_fee' in data

    def preview(self, suggestion, data) -> ChangePreview:
        return ChangePreview(action="update", table="proposals", ...)

    def apply(self, suggestion, data) -> bool:
        # Execute the change, store rollback data
        return True

    def rollback(self, rollback_data) -> bool:
        # Undo the change
        return True
```

### API Endpoints
- `GET /api/suggestions/{id}/preview` - See what will change
- `POST /api/suggestions/{id}/approve` - Apply the suggestion
- `POST /api/suggestions/{id}/reject` - Reject with reason
- `POST /api/suggestions/{id}/rollback` - Undo approved suggestion
- `GET /api/suggestions/{id}/source` - Get source email/transcript

---

### Training Data
```sql
-- training_data
id, input_text, expected_output, actual_output,
category, is_correct, feedback,
created_at, verified_by
```

### Learned Patterns (General)
```sql
-- learned_patterns
id, pattern_type, pattern_data, confidence,
times_applied, success_rate,
created_at, last_used_at
```

---

## Email Link Learning System (NEW Dec 2025)

Located in: `backend/services/learning_service.py`

### How It Works

The system learns from human approvals to improve future email->project suggestions:

```
┌─────────────────────────────────────────────────────────────────┐
│                    EMAIL LEARNING LOOP                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. USER APPROVES:                                              │
│     "Link email from nigel@rosewood.com → BK-070"               │
│                                                                  │
│  2. PATTERNS EXTRACTED:                                         │
│     • sender_to_project: nigel@rosewood.com → BK-070            │
│     • domain_to_project: @rosewood.com → BK-070                 │
│     • sender_name_to_project: Nigel Smith → BK-070              │
│                                                                  │
│  3. NEXT EMAIL FROM SAME SENDER:                                │
│     • System checks email_learned_patterns                       │
│     • Finds match: nigel@rosewood.com → BK-070                  │
│     • Auto-suggests BK-070 with higher confidence               │
│     • Evidence: "Based on 5 previous approvals"                 │
│                                                                  │
│  4. CONFIDENCE ADJUSTS:                                         │
│     • Approval → confidence += 0.05 (up to 0.95)                │
│     • Rejection → confidence -= 0.10 (down to 0.50)             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Pattern Types

| Type | Example | Confidence |
|------|---------|------------|
| `sender_to_project` | nigel@rosewood.com → BK-070 | 0.75 (high) |
| `sender_to_proposal` | client@company.com → Proposal | 0.75 (high) |
| `domain_to_project` | @rosewood.com → Rosewood project | 0.65 (medium) |
| `domain_to_proposal` | @domain.com → Related proposal | 0.65 (medium) |
| `sender_name_to_project` | "Nigel Smith" → BK-070 | 0.60 (lower) |
| `keyword_to_project` | "Dubai villa" → Dubai project | 0.55 (fuzzy) |

### Database Tables

```sql
-- email_learned_patterns (stores learned patterns)
pattern_id, pattern_type, pattern_key, pattern_key_normalized,
target_type ('project'/'proposal'), target_id, target_code, target_name,
confidence, times_used, times_correct, times_rejected,
created_from_suggestion_id, created_from_email_id,
is_active, created_at, updated_at, last_used_at

-- email_pattern_usage_log (analytics)
log_id, pattern_id, suggestion_id, email_id,
action ('matched'/'suggested'/'approved'/'rejected'),
match_score, confidence_contribution, created_at
```

### Integration Points

1. **On Suggestion Approved** (`ai_learning_service.approve_suggestion()`):
   - Extracts patterns from the approved email link
   - Stores patterns in `email_learned_patterns`
   - Boosts confidence if pattern exists

2. **On Suggestion Rejected** (`ai_learning_service.reject_suggestion()`):
   - Penalizes matching patterns
   - Decreases confidence by 0.10

3. **When Creating Suggestions** (`ai_learning_service._detect_email_links()`):
   - Checks `email_learned_patterns` first
   - If match found, creates high-confidence suggestion
   - Falls back to content-based matching

### API to View Pattern Stats

```bash
# Get pattern statistics
curl /api/intel/patterns

# Get patterns for specific project
# (In LearningService.get_patterns_for_project())
```

### Example Flow

```python
# 1. First email from nigel@rosewood.com
#    → No pattern match
#    → AI analyzes content, suggests BK-070 (confidence: 0.6)
#    → User approves

# 2. Pattern created:
#    sender_to_project | nigel@rosewood.com | BK-070 | confidence: 0.75

# 3. Second email from nigel@rosewood.com
#    → Pattern match! confidence: 0.75 × 1.0 = 0.75
#    → Suggests BK-070 (confidence: 0.90 with boost)
#    → User approves

# 4. Pattern boosted:
#    confidence: 0.75 → 0.80, times_correct: 2

# 5. Third email...
#    → Even higher confidence suggestion
```

### Definition of Done Test

1. Approve 5 emails from same sender to same project
2. Next email from that sender auto-suggests same project
3. Suggestion shows "Based on 5 previous approvals"
4. Pattern visible in database:
   ```sql
   SELECT * FROM email_learned_patterns
   WHERE pattern_key_normalized = 'nigel@rosewood.com';
   ```

---

## Email Intelligence Pipeline

```
┌─────────────────┐
│ Email Arrives   │
│ (IMAP sync)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ smart_email_    │
│ brain.py        │
│ - Extract text  │
│ - Identify type │
│ - Find project  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ OpenAI API      │
│ - Categorize    │
│ - Extract info  │
│ - Score conf.   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ email_linker.py │────▶│ email_project_  │
│ - Match project │     │ links table     │
│ - Create link   │     │ (2,290 linked)  │
└─────────────────┘     └─────────────────┘
```

---

## Key Scripts (CLI-Only - Need API)

| Script | Purpose | Status |
|--------|---------|--------|
| `smart_email_brain.py` | Email AI processor | CLI only |
| `query_brain.py` | Natural language Q&A | CLI only |
| `email_linker.py` | Email-project linking | CLI only |
| `suggestion_processor.py` | Process AI suggestions | CLI only |

**Action:** Create API endpoints for these scripts.

---

## OpenAI API Usage (gpt-4o-mini)

### Current Integration Points
```python
# Contract parsing
# backend/core/parse_contracts.py
response = anthropic.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": prompt}]
)

# Email categorization
# backend/services/email_content_processor_claude.py
# (ORPHANED - not connected to API)
```

### Cost Tracking
- Current: ~$100-200/month
- Target (Phase 4): $20-50/month (80% local LLM)

---

## Phase 4 Local LLM Plan

```
1. Install Ollama on server
2. Download Llama 3.1 70B (or 8B for testing)
3. Build API wrapper for local inference
4. Collect Claude responses as training data
5. Fine-tune Llama on BDS-specific data
6. Benchmark: Claude vs fine-tuned Llama
7. Gradual shift: 80% local, 20% cloud
```

---

## Adding AI to a Feature

### Pattern: Query → Context → Prompt → Response

```python
# 1. Define what context you need
def get_feature_context(entity_id):
    return {
        "main_data": get_main_data(entity_id),
        "related_data": get_related_data(entity_id),
        "history": get_history(entity_id),
    }

# 2. Build a good prompt
def build_prompt(question, context):
    return f"""
    Context:
    {json.dumps(context, indent=2)}

    Question: {question}

    Instructions:
    - Be concise
    - Cite specific data
    - If unsure, say so
    """

# 3. Call OpenAI
def ask_openai(prompt):
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# 4. Format response
def format_response(raw_response):
    return {
        "answer": raw_response,
        "confidence": "high",  # or calculate
        "sources": ["emails", "invoices"],
    }
```

---

## Queries This Context Answers

- "How does the query system work?"
- "Where is AI used in the system?"
- "How do I add AI to a feature?"
- "What's the email intelligence pipeline?"
- "What's the plan for local LLM?"
- "How do AI suggestions work?"
