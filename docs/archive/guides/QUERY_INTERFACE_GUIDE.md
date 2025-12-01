# Query Interface - Natural Language SQL Guide

**Status:** ✅ Complete and Ready to Use
**Created:** 2025-11-24 by Claude 2 (Query Specialist)

---

## 🎯 What This Is

A **natural language query interface** that lets users ask questions in plain English and get instant answers from the database. Think of it as "ChatGPT for your business data."

### Examples:
- "Show me all unpaid invoices"
- "What proposals did we send in November?"
- "Which projects are overdue by more than 90 days?"
- "Find all emails about Ritz Carlton"

The system converts these questions to SQL, executes them safely, and displays results with context.

---

## 📦 What Was Built

### ✅ Backend (Complete)

**1. Service Layer:** `backend/services/query_service.py`
- AI-powered NL → SQL using GPT-4o (OpenAI)
- Pattern matching fallback using QueryBrain
- Safe SQL execution (SELECT only, no DELETE/DROP/etc)
- Natural language result summaries
- Query suggestions

**2. API Endpoints:** `backend/api/main.py`
```
POST /api/query/ask         - Ask a question (AI or pattern matching)
GET  /api/query/ask         - Ask a question (GET method for easy testing)
GET  /api/query/suggestions - Get example questions
GET  /api/query/examples    - Get query type documentation
```

**3. Query Brain:** `query_brain.py` (root directory)
- Pattern matching engine for common queries
- Works without AI API key (free fallback)

### ✅ Frontend (Complete)

**1. Query Page:** `frontend/src/app/(dashboard)/query/page.tsx`
- Full-page query interface
- Accessible at http://localhost:3002/query
- Navigation link already added to sidebar

**2. Query Component:** `frontend/src/components/query-interface.tsx`
- Input field with natural language support
- 8 example questions (clickable)
- Results display (table format)
- AI summary of results
- SQL query display (debugging)
- Error handling and loading states

**3. Navigation Integration:**
- Query link already exists in app-shell.tsx (Search icon)
- No additional navigation changes needed

---

## 🚀 How to Use

### Step 1: Set Up Environment (Optional - for AI)

If you want AI-powered queries (recommended), add OpenAI API key to `.env`:

```bash
# Get API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-...
```

**Without API key:** Pattern matching still works for common queries!

### Step 2: Start the Backend

```bash
# From project root
DATABASE_PATH=database/bensley_master.db python3 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Important:** Run from project root with `DATABASE_PATH` environment variable set!

### Step 3: Start the Frontend

```bash
cd frontend
npm run dev
```

### Step 4: Open Query Interface

Navigate to: **http://localhost:3002/query**

Or click the "Query" link in the sidebar (Search icon)

---

## 🧪 Testing the Query Interface

### Test Backend API Directly

```bash
# Test with GET method (simple)
curl "http://localhost:8000/api/query/ask?q=Show%20me%20all%20proposals&use_ai=false"

# Test with POST method (more flexible)
curl -X POST http://localhost:8000/api/query/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me all active projects", "use_ai": false}'
```

### Test Frontend UI

1. Open http://localhost:3002/query
2. Click any example question
3. Or type your own question
4. Press Enter or click "Search"
5. View results in table format

---

## 📚 Example Queries

### Proposals
```
- "Show me all proposals from 2024"
- "Find proposals for hotel clients"
- "Which proposals have low health scores?"
- "Show proposals that need follow-up"
- "List all proposals with status won"
```

### Projects
```
- "Show me all active projects"
- "Find projects with no contact in 30 days"
- "Which projects are overdue?"
- "Show me projects in Dubai"
```

### Invoices
```
- "Show me all unpaid invoices"
- "Which invoices are overdue by more than 90 days?"
- "What's the total revenue for BK-033?"
- "Find invoices for Ritz Carlton project"
```

### Emails
```
- "Show me emails from this month"
- "Find emails about contracts"
- "List all emails for BK-069"
- "What are the unread emails?"
```

### Contacts
```
- "List all contacts"
- "Find contacts for hotel projects"
- "Who have we emailed most?"
```

---

## 🎨 UI Features

### Input Field
- Type natural language questions
- Press Enter to submit
- Auto-focuses on page load

### Example Questions
- 8 clickable examples
- Pre-filled into input when clicked
- Covers common use cases

### Results Display
- **Summary:** AI-generated natural language summary
- **Count:** Number of results found
- **Confidence:** AI confidence level (if using AI)
- **Table:** All results in sortable table
- **SQL:** View generated SQL query (debugging)

### Error Handling
- Clear error messages
- Handles API failures gracefully
- Shows loading state during query

---

## 🔧 Technical Architecture

```
[User Question]
      ↓
[Query Interface Component] (frontend/src/components/query-interface.tsx)
      ↓
[API Endpoint] (POST /api/query/ask)
      ↓
[Query Service] (backend/services/query_service.py)
      ↓ (if AI enabled)
[GPT-4o] → Generates SQL
      ↓ (or pattern matching)
[Query Brain] → Pattern matches SQL
      ↓
[Database] (database/bensley_master.db)
      ↓
[Results] → Enriched with context
      ↓
[AI Summary] (GPT-4o-mini)
      ↓
[Display to User]
```

---

## 🛡️ Safety Features

### SQL Injection Prevention
- Only SELECT queries allowed
- Blocks: DROP, DELETE, INSERT, UPDATE, ALTER, CREATE, TRUNCATE
- Input sanitization
- Parameterized queries

### Result Limits
- Default: 100 rows max
- Can be adjusted per query
- Prevents overwhelming the UI

### Error Handling
- Graceful fallback to pattern matching if AI fails
- Clear error messages to user
- Logging for debugging

---

## 🚨 Known Issues & Limitations

### Backend Path Issue
**Problem:** Backend must be started from project root with `DATABASE_PATH` env var
**Solution:** Use this command:
```bash
DATABASE_PATH=database/bensley_master.db python3 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### AI Dependency
**Problem:** AI queries require OpenAI API key (costs money)
**Solution:** Pattern matching fallback works without API key for common queries

### Pattern Matching Limitations
**Problem:** Pattern matching only understands specific query formats
**Solution:** Use AI mode for complex or unusual questions

---

## 📈 Future Enhancements

### Phase 2 (Optional Improvements)

1. **Query History**
   - Save last 20 queries per user
   - Quick replay of recent queries
   - Database table: Add `query_history` table

2. **Saved Queries**
   - Name and save frequently used queries
   - Share queries with team
   - Database table: Add `saved_queries` table

3. **Export Functionality**
   - Export to CSV button
   - Export to JSON button
   - Export to Excel (complex)

4. **Visualization**
   - Auto-detect numeric data → bar chart
   - Auto-detect time series → line chart
   - Auto-detect categories → pie chart
   - Use recharts library (already installed)

5. **Query Suggestions**
   - Learn from common queries
   - Suggest similar queries
   - Auto-complete query input

---

## 🎓 For Developers

### Adding New Query Patterns

Edit `query_brain.py` to add pattern matching rules:

```python
# Example: Add pattern for "Find contacts in {city}"
def parse_query(self, question: str):
    # ... existing code ...

    # New pattern
    match = re.search(r'find contacts in (\w+)', question, re.I)
    if match:
        city = match.group(1)
        sql = "SELECT * FROM contacts WHERE city = ?"
        return sql, [city]
```

### Testing New Features

```bash
# Run backend tests
pytest backend/tests/test_query_service.py

# Test API endpoint
curl "http://localhost:8000/api/query/ask?q=YOUR_QUESTION&use_ai=false"
```

### Database Tables Used

The query service can access all tables:
- `projects` (51 rows)
- `proposal_tracker` (87 rows)
- `emails` (3,356 rows)
- `invoices` (253 rows)
- `contacts` (465 rows)
- And 60+ other tables

---

## ✅ Completion Checklist

- [x] Backend service created (`query_service.py`)
- [x] API endpoints added (`/api/query/ask`, etc.)
- [x] Frontend component built (`query-interface.tsx`)
- [x] Query page created (`/query/page.tsx`)
- [x] Navigation link added (already existed)
- [x] Environment variables documented (`.env.example`)
- [x] Safety features implemented (SQL injection prevention)
- [x] Error handling and loading states
- [x] Example queries provided (8 examples)
- [x] Documentation created (this file!)

---

## 🎉 Ready to Use!

The query interface is **100% functional and ready for testing**.

### Quick Start:
1. Start backend: `DATABASE_PATH=database/bensley_master.db python3 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open: http://localhost:3002/query
4. Ask a question!

**Optional:** Add `OPENAI_API_KEY` to `.env` for AI-powered queries.

---

**Built by:** Claude 2 - Query Specialist
**Date:** 2025-11-24
**Coordination:** See `COORDINATION_MASTER.md`
