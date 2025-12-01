# Bensley Intelligence Architecture
**Date:** November 24, 2025
**Status:** Architecture Proposal - Revised for 10,000+ Email Scale

---

## Executive Summary

Based on Stanford CS336 LLM course review and actual system requirements, this document proposes a **RAG + Fine-Tuned LLM architecture** for the Bensley intelligence system.

**Key Scale Factors:**
- 10,000+ emails across multiple sources (RFIs, scheduling, invoices, finance, proposals)
- Need: parsing, categorization, database organization, analytics, query agents, automations, report generation
- Privacy preferred (local processing)
- Self-improving system that learns from corrections

**Recommended Approach:** Hybrid RAG + Fine-Tuned Llama3 on Ollama

---

## Critical Findings from Stanford CS336 Audit

### What We Were Doing Wrong:

1. **Pattern Matching ≠ Learning**
   - Current `smart_email_matcher.py` uses regex and keyword matching
   - Storing corrections doesn't create learning - it's just a lookup table
   - No training loop, no loss function, no weight updates

2. **Over-Engineering for Wrong Scale**
   - Building custom pattern matchers for 395 emails was overkill
   - But with 10,000+ emails, we need MORE sophistication, not less

3. **Missing the Actual "Intelligence"**
   - Intelligence comes from LLMs understanding context, not matching patterns
   - Need semantic understanding, not syntactic matching

### What Stanford Teaches Works:

1. **Pre-trained Models + Fine-Tuning**
   - Don't train from scratch (requires billions of tokens, $millions)
   - Use existing models (Llama3, Mistral) and adapt them
   - Fine-tuning on 1,000-5,000 examples costs $100-500

2. **RAG (Retrieval Augmented Generation)**
   - Store approved examples as embeddings
   - Retrieve similar examples for context
   - LLM generates response based on retrieved examples
   - This IS learning: better examples = better predictions

3. **Human-in-the-Loop RLHF**
   - User approves/rejects AI suggestions
   - Approved examples become training data
   - System improves with every correction
   - This is how ChatGPT was trained

---

## Proposed Architecture: 3-Layer Intelligence System

### Layer 1: Document Processing Pipeline
**Purpose:** Ingest and parse raw documents into structured data

```
Email/PDF/Document → Parser → Structured JSON → Database
```

**Technology:**
- Python email parsing (already have)
- PDF extraction: PyPDF2, pdfplumber
- Document classification: Ollama Llama3
- Storage: SQLite with full-text search

**Tables:**
```sql
-- Universal document store
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    source_type TEXT,  -- 'email', 'rfi', 'invoice', 'proposal'
    document_date DATETIME,
    raw_content TEXT,
    parsed_json JSON,
    category TEXT,
    confidence_score REAL,
    processed_at DATETIME
);

-- Extracted intelligence
CREATE TABLE document_intelligence (
    id INTEGER PRIMARY KEY,
    document_id INTEGER,
    entity_type TEXT,  -- 'project_update', 'fee_change', 'status_change'
    entity_data JSON,
    confidence REAL,
    approved BOOLEAN,
    approved_by TEXT,
    approved_at DATETIME
);

-- Embeddings for RAG
CREATE TABLE document_embeddings (
    id INTEGER PRIMARY KEY,
    document_id INTEGER,
    embedding BLOB,  -- 768-dim vector from sentence-transformers
    chunk_text TEXT
);
```

### Layer 2: RAG + LLM Intelligence Extraction
**Purpose:** Extract structured intelligence from documents with learning capability

**Workflow:**
```python
def extract_intelligence(document):
    # 1. Get document embedding
    embedding = embed(document.content)

    # 2. Find 5 most similar approved examples (RAG)
    similar_examples = vector_search(embedding, limit=5)

    # 3. Build few-shot prompt
    prompt = f"""
    Here are 5 correctly processed Bensley documents:

    {format_examples(similar_examples)}

    Now extract intelligence from this document:
    Type: {document.source_type}
    Content: {document.content}

    Extract:
    - Project code (if any)
    - Status update (if any)
    - Fee/value changes (if any)
    - Action items
    - Key dates

    Return as JSON.
    """

    # 4. Call LLM (Ollama or OpenAI)
    result = ollama.chat(model='llama3:8b', prompt=prompt)

    # 5. Store with confidence score
    save_extraction(document.id, result, confidence=0.85)

    # 6. Return for user review
    return result
```

**Technology Stack:**
- **LLM**: Ollama Llama3:8b (8 billion parameters) - runs on MacBook, free, private
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (fast, 768-dim vectors)
- **Vector Search**: SQLite with vector extension or FAISS
- **Fallback**: OpenAI GPT-4 API for complex cases

### Layer 3: Self-Improving Learning Loop
**Purpose:** Learn from user corrections to improve over time

**Human-in-the-Loop Workflow:**
```
1. AI extracts intelligence → 2. User reviews in dashboard
3. User approves/corrects → 4. Store as training example
5. Re-embed and index → 6. Used in future RAG retrieval
```

**User Review Interface:**
```typescript
// Dashboard component
<IntelligenceReviewQueue>
  {unreviewed.map(extraction => (
    <ExtractionCard>
      <Label>AI Extracted:</Label>
      <JSONEditor value={extraction.data} />

      <Actions>
        <Button onClick={() => approve(extraction)}>
          Approve ✓
        </Button>
        <Button onClick={() => editAndApprove(extraction)}>
          Edit & Approve
        </Button>
        <Button onClick={() => reject(extraction)}>
          Reject ✗
        </Button>
      </Actions>
    </ExtractionCard>
  ))}
</IntelligenceReviewQueue>
```

**Learning Mechanism:**
```python
def handle_user_approval(extraction_id, user_action):
    extraction = get_extraction(extraction_id)

    if user_action == "approve":
        # This becomes a training example
        mark_as_approved(extraction_id)
        create_embedding(extraction)
        add_to_rag_index(extraction)

    elif user_action == "edit_and_approve":
        # User corrected the extraction
        update_extraction(extraction_id, user_edits)
        mark_as_approved(extraction_id)
        create_embedding(extraction)  # Embed the CORRECT version
        add_to_rag_index(extraction)

        # Track the correction for fine-tuning
        log_correction(
            original=extraction.data,
            corrected=user_edits,
            document=extraction.document
        )

    elif user_action == "reject":
        # Learn what NOT to do
        mark_as_rejected(extraction_id)
        add_to_negative_examples(extraction)
```

**Fine-Tuning Trigger:**
```python
# After 1,000 approved examples, trigger fine-tuning
if count_approved_examples() >= 1000:
    training_data = prepare_training_jsonl()
    # Fine-tune Llama3 on Bensley data
    fine_tune_model(
        base_model="llama3:8b",
        training_file=training_data,
        output_model="bensley-llama3:v1"
    )
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
**Goal:** Get basic LLM extraction working

**Tasks:**
1. Set up Ollama locally
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull llama3:8b
   ```

2. Create document ingestion pipeline
   - Extend current email importer
   - Add RFI/invoice/proposal parsers
   - Store in unified `documents` table

3. Build basic extraction service
   ```python
   # backend/services/intelligence_service.py
   class IntelligenceService:
       def extract_from_document(self, doc_id):
           """Extract intelligence using Ollama"""
           pass

       def get_pending_review(self):
           """Get extractions needing user review"""
           pass

       def approve_extraction(self, extraction_id, edits=None):
           """Mark extraction as approved, store as example"""
           pass
   ```

4. Create review UI in dashboard
   - New tab: "Intelligence Review"
   - Show pending extractions
   - Approve/Edit/Reject buttons

**Success Criteria:**
- Can process 1 email through LLM
- User can review and approve in dashboard
- Approved extraction stored in database

### Phase 2: RAG + Learning (Week 2)
**Goal:** Add retrieval and learning capability

**Tasks:**
1. Set up embedding pipeline
   ```python
   from sentence_transformers import SentenceTransformer

   model = SentenceTransformer('all-MiniLM-L6-v2')
   embedding = model.encode(document.content)
   ```

2. Implement vector search
   - Option A: SQLite with vector extension
   - Option B: FAISS in-memory index
   - Store embeddings in `document_embeddings`

3. Build RAG retrieval
   - Find 5 similar approved examples
   - Include in LLM prompt
   - Test accuracy improvement

4. Create learning loop
   - User approval creates training example
   - Re-embed and index
   - Track accuracy over time

**Success Criteria:**
- Accuracy improves from 70% → 85% after 100 approvals
- Similar emails get similar extractions
- System learns from corrections

### Phase 3: Multi-Source Integration (Week 3)
**Goal:** Process all data sources (emails, RFIs, invoices, etc.)

**Tasks:**
1. Build RFI importer
   - Parse RFI documents (PDF/email)
   - Extract: project code, requirements, deadlines
   - Link to proposals

2. Build scheduling importer
   - Import schedule data (email/Excel/API)
   - Extract: milestones, deadlines, resources
   - Link to projects

3. Build invoice/finance importer
   - Parse invoices (PDF)
   - Extract: amounts, dates, project codes
   - Link to financial tracker

4. Create unified query interface
   ```python
   query_brain("Show me all invoices for BK-033")
   query_brain("What's the status of Dubai projects?")
   query_brain("Which proposals are waiting on client for >14 days?")
   ```

**Success Criteria:**
- All 5 data sources ingesting to unified `documents` table
- Can query across all sources
- Intelligence extracted from all document types

### Phase 4: Automation & Fine-Tuning (Week 4)
**Goal:** Automate workflows and improve accuracy with fine-tuning

**Tasks:**
1. Collect 1,000+ approved examples
2. Fine-tune Llama3 on Bensley data
   ```bash
   ollama create bensley-llama3 -f Modelfile
   ```

3. Build automation rules
   ```python
   # Auto-execute high-confidence changes
   if extraction.confidence > 0.95:
       auto_apply(extraction)
   ```

4. Create report generation
   - Weekly proposal status report (already have)
   - Financial summary report
   - Project health dashboard

5. Build query agent
   ```python
   # Natural language queries
   ask_bensley("What changed this week?")
   ask_bensley("Show me at-risk projects")
   ```

**Success Criteria:**
- Fine-tuned model accuracy >90%
- 50% of extractions auto-applied
- Can answer complex queries across all data

---

## Technology Stack

### LLM Layer
- **Primary**: Ollama + Llama3:8b (free, local, private)
- **Fallback**: OpenAI GPT-4 API for complex cases
- **Future**: Fine-tuned Bensley-Llama3

### Embedding & Search
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Vector Store**: FAISS (simple, fast, in-memory)
- **Text Search**: SQLite FTS5 (full-text search)

### Backend
- **Framework**: FastAPI (already using)
- **Database**: SQLite (already using)
- **Task Queue**: Python's asyncio for now, Celery if needed

### Frontend
- **Framework**: Next.js + React (already using)
- **UI**: Shadcn/UI components (already using)
- **State**: TanStack Query (already using)

### Infrastructure
- **Hosting**: Local for now (runs on MacBook)
- **Backup**: Cloud backup of database
- **Monitoring**: Simple logging to start

---

## Cost Analysis

### Option 1: Pure Ollama (Recommended)
- **Hardware**: Runs on existing MacBook
- **LLM Cost**: $0/month (local)
- **Embedding Cost**: $0/month (local)
- **Storage**: $0/month (local SQLite)
- **Total**: **$0/month**
- **Accuracy**: 85-90% after learning
- **Privacy**: 100% private

### Option 2: Hybrid Ollama + GPT-4 Fallback
- **Ollama**: $0/month (handles 90% of cases)
- **GPT-4 API**: ~$20/month (10% complex cases, 1,000 requests)
- **Storage**: $0/month (local)
- **Total**: **$20/month**
- **Accuracy**: 90-95% (GPT-4 handles edge cases)
- **Privacy**: 90% private, 10% to OpenAI

### Option 3: Pure GPT-4 API
- **GPT-4 API**: ~$150/month (10,000 emails @ $0.015/request)
- **Embeddings**: ~$5/month (OpenAI embeddings)
- **Storage**: $0/month (local)
- **Total**: **$155/month**
- **Accuracy**: 95%+ (best accuracy)
- **Privacy**: All data to OpenAI

### Option 4: Fine-Tuned Llama3 (Future)
- **Fine-tuning**: $200 one-time (train on 2,000 examples)
- **Running**: $0/month (local)
- **Storage**: $0/month (local)
- **Total**: **$200 one-time, then $0/month**
- **Accuracy**: 90-95% (specialized for Bensley)
- **Privacy**: 100% private

**Recommendation:** Start with Option 1 (Pure Ollama), upgrade to Option 4 (Fine-Tuned) after 1,000 approved examples.

---

## Comparison: Old vs. New Approach

### Old Approach (Pattern Matching)
```python
# smart_email_matcher.py
if "BK-" in email.subject:
    project_code = extract_project_code(email.subject)
elif "dubai" in email.body.lower():
    project_code = guess_dubai_project()
else:
    project_code = None  # 53% of emails unlinked
```

**Problems:**
- ❌ Only matches exact patterns
- ❌ Can't understand context
- ❌ Doesn't actually learn
- ❌ Fails on new patterns
- ❌ 47% unlinked emails

### New Approach (RAG + LLM)
```python
# intelligence_service.py
def extract_intelligence(email):
    # Find similar approved examples
    examples = vector_search(email.embedding, limit=5)

    # LLM understands context
    result = ollama.chat(
        model='llama3',
        prompt=f"{examples}\n\nExtract from: {email.body}"
    )

    # Returns structured intelligence
    return {
        'project_code': 'BK-033',
        'status_update': 'Client approved Phase 2',
        'fee_change': None,
        'action_items': ['Send updated timeline', 'Schedule kickoff'],
        'confidence': 0.92
    }
```

**Benefits:**
- ✅ Understands semantic meaning
- ✅ Learns from every approval
- ✅ Handles new patterns automatically
- ✅ Gets smarter over time
- ✅ 85-95% accuracy

---

## Success Metrics

### Phase 1 (Foundation)
- 50 documents processed through LLM
- User can review and approve extractions
- Basic accuracy: 70%

### Phase 2 (RAG + Learning)
- 500 approved examples in RAG index
- Accuracy: 85%
- Linking rate: 75% (up from 53%)

### Phase 3 (Multi-Source)
- All 5 data sources connected
- 5,000+ documents processed
- Can answer cross-source queries

### Phase 4 (Automation)
- Fine-tuned model accuracy: 90%+
- 50% auto-applied (high confidence)
- Query agent handling natural language

---

## Next Steps

1. **Review and Approve**: Decide if this architecture fits requirements
2. **Set Up Ollama**: Install and test locally
3. **Build Phase 1**: Basic extraction + review UI
4. **Collect Examples**: User reviews 100-500 extractions
5. **Build Phase 2**: Add RAG and learning
6. **Scale Up**: Process all 10,000+ documents

---

## Questions This Solves

**"Can I train my own LLM?"**
- Not from scratch (too expensive), but YES through fine-tuning after Phase 2

**"Does this actually learn?"**
- YES: RAG retrieval = learning from examples
- YES: Fine-tuning = learning from corrections
- YES: More approvals = better accuracy

**"Is this better than pattern matching?"**
- YES: Understands context, not just keywords
- YES: Learns new patterns automatically
- YES: Actually improves over time

**"Can I keep data private?"**
- YES: Ollama runs 100% locally on MacBook

**"Does this scale to 10,000+ emails?"**
- YES: Architecture designed for this scale
- YES: RAG handles large example sets efficiently
- YES: Fine-tuning improves with more data

---

## Related Documentation

- **Provenance Tracking**: `PROVENANCE_TRACKING_SUMMARY.md`
- **Stanford CS336 Analysis**: In conversation history
- **Current System**: `SYSTEM_AUDIT_2025-11-15.md`
