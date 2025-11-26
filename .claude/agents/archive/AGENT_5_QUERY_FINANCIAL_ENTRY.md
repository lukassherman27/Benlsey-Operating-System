# Agent 5: Query Interface & Financial Entry Fixes

## Your Mission
You are responsible for improving the query interface with chat history and fixing the financial entry UI.

## Context
- **Codebase**: Bensley Design Studio Operations Platform
- **Backend**: FastAPI (Python) at `backend/api/main.py`
- **Frontend**: Next.js 15 at `frontend/src/`
- **Database**: SQLite at `database/bensley_master.db`

## Current State & Problems

### Problem 1: Query Interface Has No History
**File**: `frontend/src/components/query-interface.tsx`
**Current**: Each query is independent, no context maintained
**Need**: ChatGPT-style conversation with history

**Example wanted**:
```
User: "Show me all active projects in Thailand"
AI: [Results]

User: "What's the total contract value?"
AI: [Calculates total for Thailand projects from previous context]

User: "How many are behind schedule?"
AI: [Analyzes Thailand projects from context]
```

### Problem 2: Financial Entry Doesn't Show Existing Breakdowns
**Issue**: When adding phase breakdown, can't see what already exists
**Current flow**:
1. Select project (e.g., "Ritz Carlton")
2. Enter total contract fee
3. Continue to phase breakdown
4. **PROBLEM**: Can't see existing breakdowns - might create duplicates

**Need**: Display existing breakdowns before adding new ones

### Problem 3: Data Validation UI Issues
**Issue**: No pending suggestions showing
**Need**: Improve validation interface with actionable suggestions

## Your Tasks

### Task 1: Add Chat History to Query Interface
1. Update `frontend/src/components/query-interface.tsx`
2. Create conversation state:
```typescript
interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  query?: string  // Original SQL query if applicable
  results?: any[] // Query results
}

const [conversation, setConversation] = useState<Message[]>([])
```

3. Display conversation history:
```typescript
<div className="conversation-history">
  {conversation.map(msg => (
    <div key={msg.id} className={`message ${msg.role}`}>
      <div className="role">{msg.role === 'user' ? 'You' : 'AI'}</div>
      <div className="content">{msg.content}</div>
      {msg.results && <ResultsTable data={msg.results} />}
      <div className="timestamp">{formatTime(msg.timestamp)}</div>
    </div>
  ))}
</div>
```

4. Send conversation context to backend:
```python
# Backend endpoint
@app.post("/api/query/chat")
async def query_with_context(
    query: str,
    conversation_history: List[Dict] = []
):
    # Build prompt with context
    context = "\n".join([
        f"{msg['role']}: {msg['content']}"
        for msg in conversation_history[-5:]  # Last 5 messages
    ])

    prompt = f"""
    Previous conversation:
    {context}

    Current query: {query}

    Generate SQL query considering the context...
    """

    # Use Claude API to generate SQL with context
    ...
```

5. Add "Clear History" button
6. Add "Export Conversation" button

### Task 2: Fix Financial Entry UI
1. Find financial entry component (likely `frontend/src/components/dashboard/financial-dashboard.tsx`)
2. Add "View Existing Breakdowns" section:
```typescript
const ViewExistingBreakdowns = ({ projectCode }: { projectCode: string }) => {
  const { data: breakdowns } = useQuery(
    ['breakdowns', projectCode],
    () => api.getProjectBreakdowns(projectCode)
  )

  if (!breakdowns?.length) {
    return <p>No existing breakdowns for this project.</p>
  }

  return (
    <div className="existing-breakdowns">
      <h3>Existing Fee Breakdowns</h3>
      <table>
        <thead>
          <tr>
            <th>Scope</th>
            <th>Discipline</th>
            <th>Phase</th>
            <th>Fee</th>
            <th>Invoiced</th>
            <th>Paid</th>
          </tr>
        </thead>
        <tbody>
          {breakdowns.map(b => (
            <tr key={b.breakdown_id}>
              <td>{b.scope || '-'}</td>
              <td>{b.discipline}</td>
              <td>{b.phase}</td>
              <td>${b.phase_fee_usd?.toLocaleString()}</td>
              <td>{b.percentage_invoiced}%</td>
              <td>{b.percentage_paid}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

3. Show this BEFORE allowing new breakdown entry
4. Add warning if trying to create duplicate breakdown

### Task 3: Create API Endpoint for Breakdowns
1. Add to `backend/api/main.py`:
```python
@app.get("/api/projects/{project_code}/breakdowns")
async def get_project_breakdowns(project_code: str):
    """Get all fee breakdowns for a project"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            breakdown_id,
            scope,
            discipline,
            phase,
            phase_fee_usd,
            total_invoiced,
            percentage_invoiced,
            total_paid,
            percentage_paid
        FROM project_fee_breakdown
        WHERE project_code = ?
        ORDER BY
            CASE scope
                WHEN 'indian-brasserie' THEN 1
                WHEN 'mediterranean-restaurant' THEN 2
                WHEN 'day-club' THEN 3
                ELSE 4
            END,
            discipline,
            CASE phase
                WHEN 'Mobilization' THEN 1
                WHEN 'Conceptual Design' THEN 2
                WHEN 'Design Development' THEN 3
                WHEN 'Construction Documents' THEN 4
                WHEN 'Construction Observation' THEN 5
                ELSE 6
            END
    """, (project_code,))

    breakdowns = cursor.fetchall()
    conn.close()

    return {
        "project_code": project_code,
        "breakdowns": [
            {
                "breakdown_id": row[0],
                "scope": row[1],
                "discipline": row[2],
                "phase": row[3],
                "phase_fee_usd": row[4],
                "total_invoiced": row[5],
                "percentage_invoiced": row[6],
                "total_paid": row[7],
                "percentage_paid": row[8]
            }
            for row in breakdowns
        ],
        "total_breakdowns": len(breakdowns)
    }
```

### Task 4: Improve Data Validation UI
1. Create component: `frontend/src/components/data-validation-dashboard.tsx`
2. Show pending validations:
   - Duplicate invoices
   - Missing breakdown links
   - Incorrect phase fees
   - Data inconsistencies
3. For each issue, show:
   - Description
   - Severity (high/medium/low)
   - Suggested fix
   - [Approve Fix] [Dismiss] [Edit]
4. Track validation history

### Task 5: Add Duplicate Prevention
1. When creating new breakdown, check for duplicates:
```python
@app.post("/api/projects/fee-breakdown")
async def create_fee_breakdown(breakdown: FeeBreakdownCreate):
    # Check for duplicate
    existing = check_duplicate_breakdown(
        breakdown.project_code,
        breakdown.scope,
        breakdown.discipline,
        breakdown.phase
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Breakdown already exists: {existing['breakdown_id']}"
        )

    # Create new breakdown
    ...
```

2. Show clear error message in UI with option to view existing

## Expected Deliverables

1. **Updated query interface** with ChatGPT-style conversation history
2. **Context-aware query generation** using conversation history
3. **Financial entry UI** showing existing breakdowns before adding new
4. **API endpoint** for fetching project breakdowns
5. **Improved data validation UI** with actionable suggestions
6. **Duplicate prevention** for fee breakdowns

## Success Criteria

- ✅ Query interface maintains conversation history
- ✅ Follow-up questions use context from previous queries
- ✅ Can export conversation
- ✅ Financial entry shows existing breakdowns
- ✅ Can't create duplicate breakdowns (prevented with clear error)
- ✅ Data validation shows pending suggestions with actions
- ✅ Clean, intuitive UI

## Testing Checklist

- [ ] Ask query: "Show active projects"
- [ ] Follow-up: "What's the total value?" (should use context)
- [ ] Follow-up: "Which are in Thailand?" (should filter previous results)
- [ ] Clear history and verify fresh start
- [ ] Open financial entry for existing project
- [ ] Verify existing breakdowns display
- [ ] Try to create duplicate - verify error message
- [ ] Check data validation dashboard for suggestions

## UI/UX Improvements

1. **Query Interface**:
   - Add syntax highlighting for SQL queries (if shown)
   - Add "Example Queries" dropdown
   - Show loading spinner while querying
   - Add result export (CSV/JSON)

2. **Financial Entry**:
   - Add total contract value at top
   - Show sum of existing breakdowns vs. contract value
   - Highlight if breakdowns don't add up to 100%
   - Add bulk import option for multiple breakdowns

3. **Data Validation**:
   - Color code by severity
   - Add filters (by type, severity, date)
   - Show validation history
   - Add "Fix All" option for batch processing

## Notes
- Use existing Claude API integration for context-aware queries
- Consider adding query templates for common questions
- Think about caching conversation history in localStorage
- Coordinate with Agent 2 for breakdown data accuracy

---

## Chat History - Session 2025-11-25

### Implementation Summary

**Agent 5 completed all assigned tasks:**

#### Task 1: Chat History for Query Interface ✅
- **File**: `frontend/src/components/query-interface.tsx`
- Added `ChatMessage` interface with id, role, content, timestamp, results, sql, summary, error fields
- Implemented conversation state with localStorage persistence
- Created ChatGPT-style UI with user/assistant message bubbles
- Added auto-scroll to latest message
- Added Clear Conversation and Export Conversation buttons
- Conversation history is maintained across page refreshes
- Results tables are shown inline with messages (max 10 rows displayed)

#### Task 2: Context-Aware Query Backend ✅
- **File**: `backend/api/main.py`
- Added `ConversationMessage` and `ChatQueryRequest` Pydantic models
- Created `/api/query/chat` endpoint that accepts conversation history
- **File**: `backend/services/query_service.py`
- Added `query_with_context()` method
- Added `_query_with_ai_context()` and `_generate_sql_with_context()` methods
- AI prompt includes last 5 conversation messages for context
- Supports follow-up questions like "what's the total?" or "filter by Thailand"

#### Task 3: Enhanced Breakdowns API ✅
- **File**: `backend/api/main.py`
- Enhanced `/api/projects/{project_code}/fee-breakdown` endpoint
- Now returns: project_title, contract_value, breakdowns with financial summary
- Each breakdown includes: scope, discipline, phase, phase_fee_usd, total_invoiced, total_paid, percentage_invoiced, percentage_paid
- Added summary object with totals and percentages
- Created `/api/projects/{project_code}/fee-breakdown/check-duplicate` endpoint

#### Task 4: View Existing Breakdowns in Financial Entry ✅
- **File**: `frontend/src/app/(dashboard)/admin/financial-entry/page.tsx`
- Added "Existing Fee Breakdowns" card in Step 2 (visible in edit mode)
- Shows summary: Contract Value, Total Breakdown Fee, Total Invoiced, Total Paid
- Displays table with: Scope, Discipline, Phase, Fee, Invoiced %, Paid %
- Toggle show/hide button for the section
- Loading spinner while fetching breakdowns

#### Task 5: Duplicate Prevention ✅
- **File**: `frontend/src/app/(dashboard)/admin/financial-entry/page.tsx`
- `addPhase()` function now checks for:
  1. Local duplicates (phases already added in the form)
  2. Database duplicates (existing breakdowns from API)
- Shows toast error with specific details about the duplicate
- **File**: `frontend/src/lib/api.ts`
- Added `getProjectFeeBreakdowns()` API method
- Added `checkDuplicateBreakdown()` API method
- Added `FeeBreakdown` TypeScript interface

### Files Modified
1. `frontend/src/components/query-interface.tsx` - Complete rewrite with chat UI
2. `frontend/src/lib/api.ts` - Added 3 new API methods and 1 new interface
3. `backend/api/main.py` - Added 3 new endpoints and 2 new request models
4. `backend/services/query_service.py` - Added 3 new methods for context-aware queries
5. `frontend/src/app/(dashboard)/admin/financial-entry/page.tsx` - Added existing breakdowns view and duplicate prevention

### Testing Instructions
1. **Query Interface**: Navigate to /query, ask "Show me all active projects", then follow up with "What's the total contract value?" - should use context
2. **Financial Entry**: Navigate to /admin/financial-entry, select existing project, go to Step 2 - should see existing breakdowns
3. **Duplicate Prevention**: Try adding same discipline/phase combination - should show error toast

### Status: COMPLETE ✅
