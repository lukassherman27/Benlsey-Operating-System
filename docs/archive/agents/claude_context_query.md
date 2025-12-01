# CLAUDE 2: QUERY INTERFACE CONTEXT
**Role:** Natural Language Query Specialist
**Priority:** HIGH (Bill & Brian need to understand data)
**Estimated Time:** 6-8 hours

---

## 🎯 YOUR MISSION

Build a **natural language query interface** that lets Bill and Brian ask questions in plain English and get instant answers from the database. This is critical because:

1. **Bill asks:** "Show me all unpaid invoices for Ritz Carlton project"
2. **Brian asks:** "What proposals did we send in November?"
3. **Finance asks:** "Which projects are overdue by more than 90 days?"

You convert natural language → SQL → Results with context.

---

## 🏗️ ARCHITECTURE CONTEXT

```
[User Question] → [Your NL Parser] → [SQL Generator] → [Database]
                                                            ↓
                    [Results] ← [Context Enricher] ← [Raw Data]
                         ↓
                  [Smart Display with Charts/Tables]
```

### What You Provide
- Natural language understanding (GPT-4o mini for parsing)
- SQL generation with safety checks (no DELETE/DROP)
- Smart result display (tables, charts, summaries)
- Query history and saved queries
- Export functionality (CSV, JSON)

---

## 📚 FILES TO READ FIRST

**Must Read:**
1. `BENSLEY_OPERATIONS_PLATFORM_FORWARD_PLAN.md` - System vision
2. `database/bensley_master.db` - Database schema (66 tables)
3. `backend/api/main.py` - How to add endpoints
4. `frontend/src/app/(dashboard)/query/page.tsx` - Query UI location

**Database Schema (Key Tables):**
- `emails` (3,356 rows) - email_id, subject, sender, date, category, project_code
- `projects` (51 rows) - project_id, project_code, project_title, status, client_name
- `proposals` (87 rows) - proposal_id, project_code, project_name, status, sent_date
- `invoices` (253 rows) - invoice_id, project_id, invoice_number, invoice_amount, payment_date
- `contacts` (465 rows) - contact_id, name, email, company

---

## 🛠️ FILES TO CREATE/MODIFY

### Backend

#### 1. `backend/services/query_service.py` (NEW FILE)
```python
class QueryService:
    def parse_natural_language(self, question: str) -> dict:
        """Use GPT-4o-mini to understand intent and extract entities"""

    def generate_sql(self, parsed_query: dict) -> str:
        """Convert parsed intent to safe SQL"""

    def execute_query(self, sql: str) -> list:
        """Run SQL and return results"""

    def enrich_results(self, results: list, context: dict) -> dict:
        """Add context: project names, client names, etc."""

    def suggest_viz(self, results: list) -> str:
        """Suggest visualization: table, bar, line, pie"""
```

#### 2. `backend/api/main.py` (ADD ENDPOINTS)
```python
@app.post("/api/query/ask")
async def ask_question(question: str)

@app.get("/api/query/history")
async def get_query_history(limit: int = 20)

@app.post("/api/query/save")
async def save_query(query_name: str, question: str, sql: str)

@app.get("/api/query/saved")
async def get_saved_queries()

@app.get("/api/query/suggestions")
async def get_query_suggestions()  # Common questions
```

### Frontend

#### 3. `frontend/src/app/(dashboard)/query/page.tsx` (NEW FILE)
Full query interface with:
- Input box for natural language questions
- Example questions (clickable)
- Results display (table, chart, or summary)
- Query history sidebar
- Saved queries dropdown
- Export button (CSV, JSON)

#### 4. `frontend/src/components/query/` (NEW DIRECTORY)
- `query-input.tsx` - Input with suggestions
- `query-results.tsx` - Display results (table/chart)
- `query-history.tsx` - Recent queries sidebar
- `query-examples.tsx` - Common question templates

---

## ✅ YOUR TASKS (Checklist)

### Phase 1: NL Parser & SQL Generator
- [ ] Create `query_service.py` with GPT-4o-mini integration
- [ ] Parse common question patterns:
  - "Show me {entity} where {condition}"
  - "How many {entity} are {status}?"
  - "What's the total {metric} for {project}?"
- [ ] Generate safe SQL (whitelist SELECT only)
- [ ] Test with 10 example questions

### Phase 2: Backend API
- [ ] Add 5 query endpoints to main.py
- [ ] Implement query history (store in database)
- [ ] Implement saved queries
- [ ] Add safety checks (max 1000 rows, no DROP/DELETE)

### Phase 3: Frontend UI
- [ ] Create query page with input
- [ ] Add 10-15 example questions (clickable)
- [ ] Display results in smart table
- [ ] Add loading/error states

### Phase 4: Visualization
- [ ] Detect numeric data → suggest bar chart
- [ ] Detect time series → suggest line chart
- [ ] Detect categories → suggest pie chart
- [ ] Use recharts library for charts

### Phase 5: Export & History
- [ ] Export to CSV button
- [ ] Export to JSON button
- [ ] Query history sidebar (last 20 queries)
- [ ] Saved queries dropdown

---

## 🔗 DEPENDENCIES

### You Depend On
**Nothing!** Work independently.

### Others Depend On You
**Claude 5 (Overview):** Will embed query widget in dashboard

---

## 🎨 UI MOCKUP

```
┌─────────────────────────────────────────────────────────────┐
│  📊 Query Intelligence                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Ask a question about your data:                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Show me all unpaid invoices                 [Ask 🔍]│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Try these:                                                 │
│  • What proposals did we send last month?                   │
│  • Show me projects with overdue invoices                   │
│  • List all emails about Ritz Carlton                       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Results (15 invoices found):                               │
│                                                             │
│  Project       Invoice    Amount     Days Late              │
│  BK-033       I24-015    $250,000   45 days                │
│  BK-074       I24-017    $180,000   32 days                │
│  ...                                                        │
│                                                             │
│  [Export CSV] [Export JSON] [Save Query]                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 EXAMPLE QUERIES TO SUPPORT

```python
QUERY_TEMPLATES = [
    "Show me all {status} {entity}",
    "What {entity} are related to {project_code}",
    "How many {entity} were {action} in {month}",
    "List {entity} where {field} is {value}",
    "What's the total {metric} for {project}",
    "Show me {entity} older than {days} days",
]

EXAMPLE_QUESTIONS = [
    "Show me all unpaid invoices",
    "What proposals did we send in November?",
    "List emails about Ritz Carlton project",
    "How many active projects do we have?",
    "What's the total revenue for BK-033?",
    "Show me invoices overdue by more than 90 days",
    "List all proposals with status won",
    "What emails did we receive this week?",
    "Show me projects with no invoices",
    "What's the average proposal value?",
]
```

---

## 🧪 TESTING CHECKLIST

```bash
# Test query endpoint
curl -X POST http://localhost:8000/api/query/ask \
  -d '{"question": "Show me all unpaid invoices"}'

# Test suggestions
curl http://localhost:8000/api/query/suggestions
```

**Frontend Tests:**
- [ ] Type question, get results
- [ ] Click example question, runs query
- [ ] Export to CSV downloads file
- [ ] Query history shows last 20
- [ ] Saved queries persist across sessions

---

## 🚀 READY TO START?

1. Read database schema thoroughly
2. Update COORDINATION_MASTER.md
3. Build NL parser with GPT-4o-mini
4. Create query service backend
5. Build frontend query interface
6. Test with example questions
7. Mark complete when done!

**This is a game-changer feature.** Make it intuitive! 🎯
