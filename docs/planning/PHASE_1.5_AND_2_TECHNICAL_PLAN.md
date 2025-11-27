# Phase 1.5 & Phase 2 Technical Implementation Plan
## Grounded in Stanford CS336 Principles + Software Engineering Best Practices

**Created:** November 25, 2025
**Alignment:** 2_MONTH_MVP_PLAN.md + COMPLETE_ARCHITECTURE_ASSESSMENT.md + Stanford CS336
**Status:** Ready for implementation

---

## 🎓 Stanford CS336 Foundation - What We're Actually Building

Before diving into tasks, let's ground this in **actual computer science principles** from Stanford CS336 (Large Language Models):

### Core Concepts We're Implementing:

**1. RLHF (Reinforcement Learning from Human Feedback)**
- **What it is:** Training models by collecting human feedback on outputs
- **How we use it:** Capture user corrections (thumbs down + context) to improve AI categorization
- **Why it matters:** Phase 2 fine-tuning requires quality training data from Phase 1
- **Implementation:** Feedback loop with issue types, expected vs actual values, text explanations

**2. RAG (Retrieval-Augmented Generation)**
- **What it is:** Combining vector search with LLM generation for accurate, grounded responses
- **How we use it:** Search contracts/emails semantically, then generate answers with context
- **Why it matters:** Prevents hallucinations, grounds answers in actual BDS data
- **Implementation:** ChromaDB + embeddings + Claude API

**3. Model Distillation**
- **What it is:** Training smaller/cheaper model to mimic larger/expensive model
- **How we use it:** Collect Claude API responses → fine-tune local Llama → reduce costs 80%
- **Why it matters:** $200/month cloud costs → $20/month (saves $2,160/year)
- **Implementation:** Training pipeline collecting Claude outputs for Llama fine-tuning

**4. Agents with Tool Calling**
- **What it is:** LLMs that can execute functions (API calls, database queries, calculations)
- **How we use it:** "Show me overdue RFIs for BK-070" → agent queries DB → returns results
- **Why it matters:** Natural language interface beats manual SQL queries
- **Implementation:** Function calling with structured outputs (Pydantic models)

**5. Human-in-the-Loop (HITL)**
- **What it is:** AI suggests, human approves before action
- **How we use it:** AI categorizes email → show confidence → require approval if <90%
- **Why it matters:** Safety rails prevent AI mistakes from corrupting data
- **Implementation:** Confidence thresholds, locked fields, audit trails

---

## 📊 Current State Assessment

### What's Working (✅):
- Backend API (93+ endpoints)
- Database schema (operational + intelligence + relationship)
- Email categorization (AI-powered)
- Contract parsing (Claude API)
- Dashboard framework (Next.js)
- Provenance tracking (partial)

### What's Broken (🔴 CRITICAL):
1. Proposal status update error ("no such column: updated_by")
2. Project names not showing in UI
3. Recent emails widget shows old data
4. RLHF is just thumbs up (no context)

### What's Missing (⚠️ GAPS):
- Local LLM infrastructure (Ollama)
- RAG/vector database (ChromaDB)
- Model distillation pipeline
- 6 of 8 autonomous agents
- Production deployment

---

## 🎯 PHASE 1.5: Critical Fixes + Phase 1 Completion
**Timeline:** 2-3 weeks
**Goal:** Fix broken features, complete dashboard MVP

### Week 1: Critical Bug Fixes

#### Task 1.5.1: Fix Proposal Status Update Error
**Problem:** "no such column: updated_by" when saving proposal status
**Root Cause:** Typo in SQL (updated_BY vs updated_by) or Pydantic model mismatch
**Owner:** Claude 4 (Proposals)

**Technical Implementation:**
```python
# backend/services/proposal_tracker_service.py
# FIND THE BUG:
def update_proposal_status(self, project_code: str, status: str, updated_by: str):
    cursor.execute("""
        UPDATE proposals
        SET status = ?, updated_by = ?  -- Must be lowercase!
        WHERE project_code = ?
    """, (status, updated_by, project_code))
```

**Testing:**
- [ ] Browser DevTools: Capture exact request/response
- [ ] Backend logs: Check SQL statement
- [ ] Database schema: Verify column name is `updated_by` (lowercase)
- [ ] Frontend: Verify API call sends `updated_by` not `updated_BY`

**Success Criteria:**
- ✅ Can change proposal status without error
- ✅ Status saves to database
- ✅ Status history records change with timestamp + user

---

#### Task 1.5.2: Fix Project Names Not Showing
**Problem:** "Project Name" column blank in proposals tracker and widgets
**Root Cause:** Backend query missing project_name field OR database has NULLs

**Technical Implementation:**
```python
# backend/services/proposal_tracker_service.py
def get_all_proposals(self):
    cursor.execute("""
        SELECT
            p.project_code,
            p.project_name,  -- ADD THIS if missing
            p.status,
            p.project_value,
            p.client_company
        FROM proposals p
        ORDER BY p.created_at DESC
    """)
```

**Database Fix (if project_name is NULL):**
```sql
-- Populate project_name from projects table
UPDATE proposals
SET project_name = (
    SELECT name FROM projects
    WHERE projects.code = proposals.project_code
)
WHERE project_name IS NULL OR project_name = '';
```

**Frontend Display:**
```typescript
// frontend/src/app/(dashboard)/tracker/page.tsx
<TableCell>{proposal.project_name || proposal.project_code}</TableCell>
```

**Success Criteria:**
- ✅ API returns `project_name` in response
- ✅ Database has project_name populated (not NULL)
- ✅ UI displays project names in all tables/widgets

---

#### Task 1.5.3: Fix Recent Emails Widget
**Problem:** Shows "super fucking old emails" with wrong dates
**Root Cause:** Query not filtering by date OR sorting wrong OR frontend formatting bad

**Technical Implementation:**
```python
# backend/api/main.py
@app.get("/api/emails/recent")
def get_recent_emails(limit: int = 5):
    cursor.execute("""
        SELECT *
        FROM emails
        WHERE date_received >= date('now', '-30 days')
        ORDER BY date_received DESC
        LIMIT ?
    """, (limit,))
    # Return only last 30 days, sorted newest first
```

**Frontend Display:**
```typescript
// frontend/src/components/dashboard/recent-emails-widget.tsx
import { format } from 'date-fns'

{emails?.map(email => (
  <div className="flex justify-between py-2 border-b">
    <div className="flex-1 min-w-0">
      <p className="text-sm font-medium truncate">{email.subject}</p>
      <p className="text-xs text-muted-foreground">{email.sender_email}</p>
    </div>
    <div className="text-xs text-muted-foreground">
      {format(new Date(email.date_received), 'MMM d')}
    </div>
  </div>
))}
```

**Success Criteria:**
- ✅ Shows 5 most recent emails (last 30 days)
- ✅ Dates formatted as "Nov 25" not timestamp
- ✅ Subject lines truncate cleanly (no overflow)
- ✅ Sorted newest first

---

#### Task 1.5.4: Implement Proper RLHF Feedback System
**Problem:** Current RLHF is just thumbs up/down (useless for training)
**Required:** Contextual feedback with issue types, explanations, expected values

**Why This Matters (CS336):**
- RLHF training requires **rich signals** not just binary thumbs up/down
- Need to know **what** was wrong, **why** it was wrong, **what** was expected
- This creates training data for Phase 2 fine-tuning

**Technical Implementation:**

**Database Schema:**
```sql
-- Add to training_data table
ALTER TABLE training_data ADD COLUMN issue_type TEXT;
ALTER TABLE training_data ADD COLUMN expected_value TEXT;
ALTER TABLE training_data ADD COLUMN current_value TEXT;
```

**Backend Service:**
```python
# backend/services/training_data_service.py
def log_feedback(
    self,
    feature_type: str,
    feature_id: str,
    helpful: bool,
    issue_type: Optional[str] = None,  # "incorrect_data", "wrong_calculation", etc.
    feedback_text: str = None,         # REQUIRED for negative feedback
    expected_value: Optional[str] = None,
    current_value: Optional[str] = None
):
    if not helpful and not feedback_text:
        raise ValueError("feedback_text is REQUIRED when helpful=False")

    # Log to training_data with full context
```

**Frontend Component:**
```typescript
// frontend/src/components/ui/feedback-buttons.tsx
// On thumbs down → show dialog with:
// - Issue type checkboxes (5 categories)
// - Required text explanation
// - Expected value field
// - Current value display
```

**What Gets Logged (Example):**
```json
{
  "feature_type": "email_category",
  "feature_id": "email_12345",
  "helpful": false,
  "issue_type": "incorrect_data, wrong_calculation",
  "feedback_text": "This email is about an invoice payment, not a proposal. Should be categorized as 'invoice' not 'proposal'.",
  "expected_value": "invoice",
  "current_value": "proposal",
  "context": {
    "email_subject": "RE: Payment for Invoice #I24-045",
    "sender": "finance@client.com",
    "ai_confidence": 0.72
  }
}
```

**Success Criteria:**
- ✅ Thumbs down opens dialog with issue types
- ✅ Cannot submit without text explanation
- ✅ Logs include expected vs current values
- ✅ Data suitable for fine-tuning in Phase 2

---

### Week 2: Complete Phase 1 Dashboard Features

#### Task 1.5.5: Hierarchical Project Breakdown
**User Request:** "I want to see Project → Discipline → Phase → Invoices"

**Data Model:**
```
Project: 25-BK-018 Mumbai Clubhouse ($2.5M)
├── Landscape ($800K)
│   ├── Mobilization ($50K)
│   │   ├── Invoice #001: $25K (Paid)
│   │   └── Invoice #002: $25K (Paid)
│   ├── Concept Design ($200K)
│   │   ├── Invoice #003: $100K (Paid 50%)
│   │   └── [Not yet invoiced]: $100K
│   ├── Design Development ($300K)
│   └── ...
├── Interior ($1.2M)
└── Architecture ($500K)
```

**Database Query:**
```python
# backend/services/project_service.py
def get_project_hierarchy(self, project_code: str):
    # Get fee breakdown from project_fee_breakdown table
    cursor.execute("""
        SELECT
            discipline,
            phase,
            fee_amount,
            phase_order
        FROM project_fee_breakdown
        WHERE project_code = ?
        ORDER BY discipline, phase_order
    """, (project_code,))

    breakdown = cursor.fetchall()

    # Get invoices for each phase
    cursor.execute("""
        SELECT
            invoice_number,
            invoice_amount,
            paid_date,
            discipline,
            phase
        FROM invoices
        WHERE project_code = ?
    """, (project_code,))

    invoices = cursor.fetchall()

    # Build hierarchy: Project → Discipline → Phase → Invoices
    return build_hierarchy_tree(breakdown, invoices)
```

**Frontend Component:**
```typescript
// frontend/src/components/projects/project-hierarchy-tree.tsx
// Collapsible tree view with:
// - Expandable disciplines
// - Phases with progress bars
// - Invoice status badges
// - Total/paid/remaining calculations
```

**Success Criteria:**
- ✅ Can drill down: Project → Discipline → Phase → Invoice
- ✅ Shows fee breakdown from project_fee_breakdown table
- ✅ Links invoices to correct phases
- ✅ Calculates remaining balance per phase
- ✅ Visual tree structure (expandable/collapsible)

---

#### Task 1.5.6: Add Trend Indicators to KPIs
**User Request:** "I love the trend indicators (+8.2%)"

**Technical Implementation:**
```python
# backend/services/dashboard_service.py
def get_kpi_with_trends(self):
    # Current period
    current_active_proposals = self.get_active_proposals_count()

    # Previous period (same time last month)
    previous_active_proposals = self.get_active_proposals_count(
        start_date=date.today() - timedelta(days=30),
        end_date=date.today() - timedelta(days=30)
    )

    # Calculate trend
    if previous_active_proposals > 0:
        trend_pct = ((current_active_proposals - previous_active_proposals)
                     / previous_active_proposals * 100)
    else:
        trend_pct = 0

    return {
        "active_proposals": current_active_proposals,
        "trend": {
            "value": trend_pct,
            "direction": "up" if trend_pct > 0 else "down",
            "label": f"+{trend_pct:.1f}%" if trend_pct > 0 else f"{trend_pct:.1f}%"
        }
    }
```

**Frontend Display:**
```typescript
// frontend/src/components/dashboard/kpi-card.tsx
<div className="kpi-card">
  <h3>Active Proposals</h3>
  <p className="text-4xl font-bold">{kpi.active_proposals}</p>
  <div className={cn(
    "trend",
    kpi.trend.direction === "up" ? "text-green-600" : "text-red-600"
  )}>
    <TrendingUp className="h-4 w-4" />
    {kpi.trend.label}
  </div>
</div>
```

**Success Criteria:**
- ✅ All KPI cards show trend indicators
- ✅ Trends calculated month-over-month
- ✅ Color-coded: green (up), red (down), gray (no change)
- ✅ Tooltip explains calculation period

---

### Week 3: Data Quality + Production Prep

#### Task 1.5.7: Complete Provenance Tracking Implementation
**Current State:**
- ✅ proposal_tracker_status_history working
- ✅ emails.source_type working
- ❌ audit_log table empty
- ❌ proposal_tracker missing created_by/source_type

**Technical Implementation:**
```sql
-- Add provenance fields to proposal_tracker
ALTER TABLE proposal_tracker ADD COLUMN source_type TEXT DEFAULT 'manual';
ALTER TABLE proposal_tracker ADD COLUMN source_reference TEXT;
ALTER TABLE proposal_tracker ADD COLUMN created_by TEXT DEFAULT 'bill';
ALTER TABLE proposal_tracker ADD COLUMN is_locked BOOLEAN DEFAULT 0;
```

**Service Layer Enforcement:**
```python
# backend/services/proposal_tracker_service.py
def update_proposal(self, project_code: str, updates: dict, source_type: str, updated_by: str):
    # Check if fields are locked
    locked_fields = self.get_locked_fields(project_code)

    for field in updates.keys():
        if field in locked_fields and source_type == 'ai':
            raise ValueError(f"Field {field} is locked and cannot be updated by AI")

    # Proceed with update, recording provenance
    cursor.execute("""
        UPDATE proposal_tracker
        SET {field} = ?, source_type = ?, updated_by = ?
        WHERE project_code = ?
    """)
```

**Audit Logging:**
```python
# backend/services/audit_service.py
def log_change(self, table: str, record_id: str, field: str, old_value: Any, new_value: Any, changed_by: str):
    cursor.execute("""
        INSERT INTO audit_log (
            timestamp, table_name, record_id, field_name,
            old_value, new_value, changed_by, change_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'UPDATE')
    """, (datetime.now(), table, record_id, field, old_value, new_value, changed_by))
```

**Success Criteria:**
- ✅ All tables have source_type, source_reference, created_by
- ✅ Service layer enforces locked field rules
- ✅ audit_log captures all changes
- ✅ Can trace any data point back to original source

---

#### Task 1.5.8: Production Deployment Preparation
**Goal:** Make system ready for production use

**Checklist:**
- [ ] **Error Handling:**
  - All API endpoints have try/catch
  - User-friendly error messages
  - Backend logs errors to file
  - Frontend shows graceful error states

- [ ] **Performance:**
  - API responses <500ms
  - Dashboard loads <2 seconds
  - Database queries optimized (indexes)
  - Frontend code-split (lazy loading)

- [ ] **Security:**
  - No API keys in frontend code
  - No SQL injection vulnerabilities
  - CORS configured correctly
  - Rate limiting on API endpoints

- [ ] **Monitoring:**
  - Health check endpoint (/health)
  - Logs structured (JSON format)
  - Can tail logs for debugging
  - Database backup script

- [ ] **Documentation:**
  - API documentation (Swagger) complete
  - README.md has production setup steps
  - Known issues documented
  - Rollback procedure documented

**Success Criteria:**
- ✅ Can deploy to Mac Mini server
- ✅ Survives restarts (systemd services)
- ✅ Logs errors for debugging
- ✅ Bill can use daily without developer help

---

## 🤖 PHASE 2: Intelligence Layer (Stanford CS336 Implementation)
**Timeline:** 4-6 weeks (December/January)
**Goal:** Add local AI, RAG, model distillation, autonomous agents

### Theoretical Foundation (CS336)

Before building, understand **why** we're building each component:

#### 1. The RAG Pipeline (Retrieval-Augmented Generation)

**The Problem RAG Solves:**
- LLMs hallucinate when asked about specific data they weren't trained on
- "What's the payment status of BK-070?" → LLM makes up answer (BAD!)

**How RAG Fixes It:**
```
User Question: "Show me overdue invoices for BK-070"
    ↓
1. Convert to vector embedding (all-MiniLM-L6 model)
    ↓
2. Search ChromaDB for similar documents
    ↓
3. Retrieve top 5 relevant contracts/invoices/emails
    ↓
4. Give LLM the retrieved context + original question
    ↓
5. LLM generates answer GROUNDED in retrieved data
    ↓
User gets factual, verifiable answer
```

**Key Insight:** RAG = Search + Generate (not just generate)

---

#### 2. Model Distillation (Teacher-Student Training)

**The Economics:**
- Claude API (teacher): $10 per 1M tokens
- Local Llama 70B (student): $0 (runs on your hardware)

**How Distillation Works:**
```
Phase 2.1: Collect Training Data (RLHF from Phase 1)
- User asks: "Categorize this email"
- Claude API responds: "This is a 'proposal' email (95% confidence)"
- We log: { input: email_text, output: "proposal", confidence: 0.95 }
- Repeat 10,000+ times

Phase 2.2: Fine-tune Local Model
- Take pre-trained Llama 3.1 70B
- Fine-tune on our 10,000 Claude responses
- Model learns BDS-specific patterns

Phase 2.3: Test & Compare
- Send same email to both Claude and Llama
- Compare outputs
- If Llama accuracy >90% → use Llama (free!)
- If Llama accuracy <90% → still use Claude (expensive but accurate)

Result: 80% of queries handled by local model (saves $160/month @ $200/month usage)
```

**Key Insight:** Distillation = Teaching cheap model to mimic expensive model

---

#### 3. Agents with Tool Calling (Function Calling)

**The Problem:**
- LLMs can't access real-time data
- "What's the current status of BK-070?" → LLM doesn't know (it's not in training data)

**How Tool Calling Works:**
```python
# Define tools the LLM can use
tools = [
    {
        "name": "get_project_status",
        "description": "Get current status of a project",
        "parameters": {
            "project_code": {"type": "string", "description": "Project code like BK-070"}
        }
    },
    {
        "name": "get_overdue_invoices",
        "description": "Get list of overdue invoices",
        "parameters": {
            "project_code": {"type": "string", "optional": True}
        }
    }
]

# LLM decides which tool to call
user_query = "What's overdue for BK-070?"
llm_response = llm.generate(query=user_query, tools=tools)

# LLM outputs:
{
    "tool": "get_overdue_invoices",
    "parameters": {"project_code": "BK-070"}
}

# We execute the function:
result = get_overdue_invoices(project_code="BK-070")
# Returns: [{"invoice": "I24-045", "amount": "$85,000", "days_overdue": 87}]

# Give result back to LLM:
final_answer = llm.generate(
    query=user_query,
    tool_result=result
)

# LLM responds:
"BK-070 has one overdue invoice: I24-045 for $85,000, which is 87 days overdue."
```

**Key Insight:** Tool calling = LLM decides WHAT to do, we execute HOW to do it

---

### Phase 2 Implementation Tasks

#### Week 4-5: Local LLM Setup + RAG

**Task 2.1: Install Ollama + Download Llama Model**
```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Download Llama 3.1 70B (or 8B for testing)
ollama pull llama3.1:70b

# Test inference
ollama run llama3.1:70b "Categorize this email: Subject: Payment for Invoice #I24-045"
```

**Task 2.2: Set Up ChromaDB (Vector Database)**
```python
# backend/services/rag_service.py
from chromadb import Client
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

class RAGService:
    def __init__(self):
        self.client = Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="./chromadb"
        ))

        self.collection = self.client.get_or_create_collection("bds_documents")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

    def index_document(self, doc_id: str, text: str, metadata: dict):
        """Add document to vector database"""
        embedding = self.embedder.encode(text)
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding.tolist()],
            documents=[text],
            metadatas=[metadata]
        )

    def search(self, query: str, n_results: int = 5):
        """Search for relevant documents"""
        query_embedding = self.embedder.encode(query)
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results
        )
        return results
```

**Task 2.3: Index All Documents**
```python
# scripts/index_documents_to_chromadb.py
def index_all_documents():
    rag = RAGService()

    # Index contracts
    contracts = db.execute("SELECT * FROM contract_metadata").fetchall()
    for contract in contracts:
        rag.index_document(
            doc_id=f"contract_{contract['id']}",
            text=contract['full_text'],
            metadata={
                "type": "contract",
                "project_code": contract['project_code'],
                "date": contract['signed_date']
            }
        )

    # Index emails
    emails = db.execute("SELECT * FROM emails").fetchall()
    for email in emails:
        rag.index_document(
            doc_id=f"email_{email['email_id']}",
            text=f"{email['subject']} {email['body_text']}",
            metadata={
                "type": "email",
                "sender": email['sender_email'],
                "date": email['date_received']
            }
        )

    # Index proposals, invoices, etc.
```

**Task 2.4: Build RAG Query Endpoint**
```python
# backend/api/main.py
@app.post("/api/query/rag")
def query_with_rag(query: str):
    # 1. Search for relevant documents
    rag = RAGService()
    results = rag.search(query, n_results=5)

    # 2. Build context from retrieved documents
    context = "\n\n".join([
        f"Document: {r['metadata']['type']}\n{r['document']}"
        for r in results['documents']
    ])

    # 3. Generate answer with LLM + context
    llm = OllamaService()  # or ClaudeService()
    prompt = f"""Based on the following documents, answer the question.

Documents:
{context}

Question: {query}

Answer:"""

    answer = llm.generate(prompt)

    return {
        "query": query,
        "answer": answer,
        "sources": results['metadatas'],
        "confidence": results['distances']
    }
```

**Success Criteria:**
- ✅ Ollama running locally
- ✅ ChromaDB indexed with all documents
- ✅ RAG queries return relevant documents
- ✅ Answers grounded in actual data

---

#### Week 6-7: Model Distillation Pipeline

**Task 2.5: Collect Training Data from Phase 1 RLHF**
```python
# backend/services/distillation_service.py
def export_training_data():
    """Export RLHF data for fine-tuning"""
    cursor.execute("""
        SELECT
            feature_type,
            feature_id,
            context_json,
            feedback_text,
            expected_value,
            current_value
        FROM training_data
        WHERE helpful = 1  -- Only correct examples
    """)

    training_data = []
    for row in cursor.fetchall():
        # Convert to fine-tuning format
        training_data.append({
            "instruction": f"Categorize this {row['feature_type']}",
            "input": json.loads(row['context_json']),
            "output": row['expected_value']
        })

    # Save in format for Llama fine-tuning
    with open('training_data_llama.jsonl', 'w') as f:
        for item in training_data:
            f.write(json.dumps(item) + '\n')
```

**Task 2.6: Fine-Tune Llama on BDS Data**
```bash
# Use Axolotl or Unsloth for fine-tuning
pip install unsloth

# Fine-tune Llama 3.1 8B on BDS data
python scripts/finetune_llama.py \
    --base_model "unsloth/llama-3.1-8b-bnb-4bit" \
    --data "training_data_llama.jsonl" \
    --output "models/bds-llama-8b" \
    --epochs 3 \
    --learning_rate 2e-5
```

**Task 2.7: Benchmark Fine-Tuned Model**
```python
# scripts/benchmark_models.py
def compare_models():
    test_cases = get_test_cases()  # 100 real examples

    claude_correct = 0
    llama_correct = 0

    for test in test_cases:
        # Test Claude
        claude_result = claude.categorize(test['input'])
        if claude_result == test['expected']:
            claude_correct += 1

        # Test fine-tuned Llama
        llama_result = llama_finetuned.categorize(test['input'])
        if llama_result == test['expected']:
            llama_correct += 1

    print(f"Claude accuracy: {claude_correct/100:.1%}")
    print(f"Llama accuracy: {llama_correct/100:.1%}")

    # If Llama >90% accuracy → deploy as primary model
```

**Success Criteria:**
- ✅ Collected 1,000+ training examples from RLHF
- ✅ Fine-tuned Llama model deployed
- ✅ Llama accuracy >90% on test set
- ✅ Cost reduced by 80% (use Llama for routine tasks)

---

#### Week 8: Autonomous Agents

**Task 2.8: Build Invoice Collector Agent**
```python
# backend/agents/invoice_collector_agent.py
class InvoiceCollectorAgent:
    """Monitors unpaid invoices and sends reminders"""

    def run_daily(self):
        # Get overdue invoices
        overdue = self.get_overdue_invoices(days=60)

        for invoice in overdue:
            # Check if we already sent reminder recently
            last_reminder = self.get_last_reminder(invoice['invoice_number'])
            if last_reminder and last_reminder < 7:  # Don't spam
                continue

            # Generate reminder email (use LLM)
            email_body = self.generate_reminder_email(
                invoice=invoice,
                client=invoice['client_name'],
                days_overdue=invoice['days_overdue']
            )

            # Human-in-loop: Don't send automatically, log suggestion
            self.log_suggestion(
                type="send_invoice_reminder",
                invoice_number=invoice['invoice_number'],
                email_body=email_body,
                confidence=0.95,
                requires_approval=True
            )
```

**Task 2.9: Build Proposal Follow-Up Agent**
```python
# backend/agents/proposal_followup_agent.py
class ProposalFollowUpAgent:
    """Monitors proposals needing follow-up"""

    def run_daily(self):
        # Get proposals with no contact in 7+ days
        needs_followup = self.get_stale_proposals(days=7)

        for proposal in needs_followup:
            # Analyze last email conversation
            last_email = self.get_last_email(proposal['project_code'])

            # Generate follow-up suggestion
            followup_text = self.generate_followup(
                proposal=proposal,
                last_email=last_email
            )

            # Log for human approval
            self.log_suggestion(
                type="send_proposal_followup",
                project_code=proposal['project_code'],
                email_body=followup_text,
                confidence=0.85,
                requires_approval=True
            )
```

**Task 2.10: Build Ops Inbox UI (Human-in-Loop)**
```typescript
// frontend/src/app/(dashboard)/ops-inbox/page.tsx
export default function OpsInboxPage() {
  const { data: suggestions } = useQuery({
    queryKey: ['ai-suggestions'],
    queryFn: () => api.get('/api/intel/suggestions')
  })

  return (
    <div className="ops-inbox">
      <h1>AI Suggestions (Human Approval Required)</h1>

      {/* Three buckets based on confidence */}
      <div className="suggestion-buckets">
        <div className="high-confidence">
          <h2>High Confidence (>90%)</h2>
          {suggestions?.filter(s => s.confidence > 0.9).map(suggestion => (
            <SuggestionCard
              suggestion={suggestion}
              onApprove={() => approveSuggestion(suggestion.id)}
              onReject={() => rejectSuggestion(suggestion.id)}
            />
          ))}
        </div>

        <div className="medium-confidence">
          <h2>Medium Confidence (70-90%)</h2>
          {/* Show evidence, require review */}
        </div>

        <div className="low-confidence">
          <h2>Needs Review (<70%)</h2>
          {/* Require manual correction */}
        </div>
      </div>
    </div>
  )
}
```

**Success Criteria:**
- ✅ Invoice collector agent runs daily
- ✅ Proposal follow-up agent runs daily
- ✅ All suggestions logged to ai_suggestions_queue
- ✅ Ops Inbox UI shows suggestions by confidence
- ✅ Can approve/reject with one click
- ✅ Approved suggestions execute automatically

---

## 👥 Claude Coordination Strategy

### Recommended Claude Assignments:

**Claude 1 (Emails & AI):**
- Task 1.5.3: Fix recent emails widget
- Task 2.1-2.4: RAG setup (ChromaDB, indexing, search)
- Task 2.8: Invoice collector agent
- Specialty: Email processing, AI integration

**Claude 2 (Intelligence & Training):**
- Task 1.5.4: Proper RLHF implementation
- Task 2.5-2.7: Model distillation pipeline
- Task 2.10: Ops Inbox UI
- Specialty: Training data, feedback loops, model evaluation

**Claude 3 (Projects & Hierarchy):**
- Task 1.5.5: Hierarchical project breakdown
- Task 1.5.7: Provenance tracking completion
- Specialty: Complex data structures, tree views

**Claude 4 (Proposals):**
- Task 1.5.1: Fix proposal status update bug
- Task 1.5.2: Fix project names missing
- Task 2.9: Proposal follow-up agent
- Specialty: Proposals, status tracking, business logic

**Claude 5 (Dashboard & KPIs):**
- Task 1.5.6: Add trend indicators to KPIs
- Task 1.5.8: Production deployment prep
- Specialty: Dashboard features, performance, monitoring

**NEW: Claude 6 (DevOps & Infrastructure)?**
- Optional: If local LLM setup gets complex
- Task 2.1: Ollama installation
- Production deployment automation
- Monitoring & logging setup

---

## 📊 Success Metrics

### End of Phase 1.5 (3 weeks):
- ✅ All critical bugs fixed (status update, project names, emails)
- ✅ RLHF collecting rich feedback (not just thumbs up)
- ✅ Hierarchical project view working
- ✅ Dashboard production-ready
- ✅ Bill uses daily without errors

### End of Phase 2 (6 weeks):
- ✅ Local LLM running (Ollama + Llama)
- ✅ RAG system operational (ChromaDB + semantic search)
- ✅ 1,000+ RLHF training examples collected
- ✅ Fine-tuned model deployed (>90% accuracy)
- ✅ 2 autonomous agents running (invoice, proposal follow-up)
- ✅ Ops Inbox UI showing AI suggestions
- ✅ 80% cost reduction (local vs cloud)

---

## 🎓 Educational Notes (Avoiding "Silly Mistakes")

### Common ML Mistakes to Avoid:

**1. Training on Test Data (Data Leakage)**
❌ **Wrong:** Using same examples for training AND testing
✅ **Right:** Split data: 80% train, 10% validation, 10% test (never seen by model)

**2. Overfitting to Small Dataset**
❌ **Wrong:** Fine-tuning on 100 examples → model memorizes, doesn't generalize
✅ **Right:** Collect 1,000+ diverse examples, use regularization, monitor validation loss

**3. Ignoring Confidence Scores**
❌ **Wrong:** Auto-applying all AI suggestions
✅ **Right:** Human-in-loop for confidence <90%, auto-apply only for >95%

**4. Not Versioning Models**
❌ **Wrong:** Overwriting model files, no way to rollback
✅ **Right:** Version models (v1.0, v1.1), track metrics per version, can rollback

**5. Hallucination in Production**
❌ **Wrong:** LLM makes up invoice amounts
✅ **Right:** Use RAG (retrieve actual data), cite sources, validate outputs

### Software Engineering Best Practices:

**1. Stateless API Design**
```python
# ❌ Bad: Store state in memory
cached_proposals = {}  # Lost on restart!

# ✅ Good: Store in database
def get_proposals():
    return db.execute("SELECT * FROM proposals").fetchall()
```

**2. Idempotent Operations**
```python
# ❌ Bad: Duplicate inserts if run twice
cursor.execute("INSERT INTO invoices VALUES (?)", (invoice,))

# ✅ Good: Check for duplicates
cursor.execute("INSERT OR IGNORE INTO invoices VALUES (?)", (invoice,))
```

**3. Database Transactions**
```python
# ❌ Bad: Partial updates if error
update_proposal_status()
update_proposal_timeline()  # If this fails, first update persists (inconsistent!)

# ✅ Good: All-or-nothing with transactions
conn.execute("BEGIN TRANSACTION")
try:
    update_proposal_status()
    update_proposal_timeline()
    conn.execute("COMMIT")
except Exception:
    conn.execute("ROLLBACK")
```

**4. Graceful Degradation**
```python
# ❌ Bad: Crash if AI unavailable
answer = claude.generate(query)  # Raises exception → app crashes

# ✅ Good: Fallback to simpler method
try:
    answer = claude.generate(query)
except Exception:
    answer = "AI temporarily unavailable. Please try again."
    log_error("Claude API failed")
```

---

## 🚀 Next Actions

### Immediate (This Week):
1. Send exact fix prompts to Claudes 4, 1, 2 (SEND_EXACT_FIXES_TO_CLAUDES_V2.md)
2. Coordinate fixes, require proof (screenshots + tests)
3. Verify all bugs actually fixed

### Phase 1.5 Start (Next Week):
1. Begin hierarchical project breakdown (Claude 3)
2. Add trend indicators to KPIs (Claude 5)
3. Complete provenance tracking (Claude 3)

### Phase 2 Planning (Week After):
1. Research Ollama setup (local LLM requirements)
2. Estimate ChromaDB data size (for hardware planning)
3. Review RLHF data quality (ready for distillation?)

---

**This plan is grounded in:**
- ✅ Stanford CS336 principles (RLHF, RAG, distillation, agents)
- ✅ Software engineering best practices (testing, transactions, versioning)
- ✅ Actual BDS needs (hierarchical breakdown, invoice tracking)
- ✅ Realistic timelines (3 weeks Phase 1.5, 6 weeks Phase 2)
- ✅ Cost optimization (local LLM saves $2,160/year)

**Total estimated effort:** 9 weeks (3 + 6)
**Total estimated cost:** $200-300 total (hardware + API during transition)
**ROI:** Saves 10-20 hours/week + $160/month ongoing

---

**Last Updated:** November 25, 2025
**Status:** Ready to implement
**Confidence:** 95% (grounded in real CS principles + tested architecture)
