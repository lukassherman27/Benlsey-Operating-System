# 📊 Agent 5: Dashboard Coordinator & Widget Fixes

**Wave:** 2 (Intelligence)
**Priority:** MEDIUM - Polish & UX improvements
**Status:** AWAITING AUDIT

---

## ⚠️ MANDATORY PROTOCOL

1. ✅ **READ** `.claude/MASTER_ARCHITECTURE.md`
2. ✅ **READ** `.claude/ALIGNMENT_AUDIT.md`
3. 🔍 **AUDIT** your assigned area
4. 📊 **REPORT** findings (create `AGENT5_AUDIT_REPORT.md`)
5. ⏸️ **WAIT** for user approval
6. ✅ **EXECUTE** only after approval
7. 📝 **DOCUMENT** changes

---

## 🎯 YOUR MISSION

Fix remaining dashboard issues and improve UX:
- Invoice aging bar increments (use 0.5M scale)
- Active projects phase ordering (Mobilization first, not last)
- Add summary bar to active projects tab
- Debug query interface
- Fix email content loading in frontend
- Ensure all widgets use correct data fields

**User Context:** Dashboard already live but has several UX/display issues that need polishing

---

## 🔍 PHASE 1: AUDIT

### Your Audit Checklist:

**1. Invoice Aging Widget Audit**
```bash
# Check invoice aging widget code
grep -A 30 "Invoice Aging" frontend/src/components/dashboard/financial-dashboard.tsx

# Check backend data
curl http://localhost:8000/api/invoices/aging

# Verify the scale calculation
sqlite3 database/bensley_master.db "SELECT MAX(total_outstanding) FROM invoice_aging"
```

**Report:**
- [ ] What's the max outstanding amount?
- [ ] What scale is widget currently using? (1M? 500K?)
- [ ] Are bar widths calculating correctly?
- [ ] What needs to change to use 0.5M increments?

**2. Active Projects Phase Ordering**
```bash
# Check active projects component
grep -A 50 "Active Projects" frontend/src/components/dashboard/active-projects-tab.tsx

# Check phase order logic
grep -n "sort\|order" frontend/src/components/dashboard/active-projects-tab.tsx

# Check backend data
curl http://localhost:8000/api/projects/active
```

**Report:**
- [ ] How is phase ordering currently done?
- [ ] Is it alphabetical? (that would put Mobilization last)
- [ ] Where is the sort logic? (frontend or backend?)
- [ ] What's the correct phase order?

**3. Summary Bar Assessment**
```bash
# Check if summary bar exists
grep -n "summary\|total" frontend/src/components/dashboard/active-projects-tab.tsx

# Check what data is available
curl http://localhost:8000/api/projects/active | grep -o "project_code\|percentage_invoiced\|total_value"
```

**Report:**
- [ ] Does summary bar exist?
- [ ] What should it show? (total contract value? total invoiced? project count?)
- [ ] Is backend data available for summary calculations?

**4. Query Interface Debug**
```bash
# Check query interface component
ls -lh frontend/src/app/query/
ls -lh frontend/src/components/query-interface.tsx

# Check if there's a query API endpoint
grep -n "query\|search" backend/api/main.py | head -20
```

**Report:**
- [ ] Does query interface component exist?
- [ ] What's the issue? (not loading? errors? missing backend?)
- [ ] Is there a backend endpoint for queries?
- [ ] What needs to be built/fixed?

**5. Email Content Loading**
```bash
# Check email display components
find frontend/src/components -name "*email*" -type f

# Check email API endpoints
grep -A 20 "@app.get.*email" backend/api/main.py | head -40

# Verify email_content table
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM email_content"
```

**Report:**
- [ ] How is email content currently displayed?
- [ ] What's the issue? (empty? error? not loading?)
- [ ] Is email_content table populated? (Agent 1 dependency!)
- [ ] What component needs fixing?

**6. Field Name Consistency Check**
```bash
# Check for remaining project_name vs project_title issues
grep -r "project_name" frontend/src/components/dashboard/

# Check API responses
curl http://localhost:8000/api/dashboard/kpis | python3 -m json.tool | grep "project"
```

**Report:**
- [ ] Are there remaining project_name references?
- [ ] What other field mismatches exist?
- [ ] List all widgets that need field updates

---

## 📊 PHASE 2: REPORT

Create `AGENT5_AUDIT_REPORT.md` with:

**Findings:**
- Invoice aging scale issue details
- Phase ordering problem root cause
- Summary bar requirements
- Query interface status
- Email content loading dependency on Agent 1

**Proposed Solution:**
- Invoice aging: Change scale to 0.5M increments
- Phase ordering: Implement custom sort order array
- Summary bar: Design and data calculation approach
- Query interface: Build vs fix existing
- Email content: Wait for Agent 1 or build placeholder

**Architecture Alignment:**
- Uses existing backend APIs? YES/NO
- Requires new endpoints? WHICH ONES
- Frontend-only fixes? YES/NO
- Dependencies on other agents? AGENT 1 for email content

**Questions for User:**
1. For summary bar: Show total contract value? Or total invoiced? Both?
2. Phase order preference: Mobilization → Design → Construction → Closeout?
3. Query interface priority: High or defer to later?
4. Should email loading wait for Agent 1 or show placeholder?

---

## ⏸️ PHASE 3: AWAIT APPROVAL

---

## ✅ PHASE 4: EXECUTION

### Task 1: Fix Invoice Aging Bar Increments

**File:** `frontend/src/components/dashboard/financial-dashboard.tsx`

**Problem:** Bar scale doesn't match data (e.g., $3.15M appears small)

**Fix:**
```tsx
// Around line 150 - Update scale calculation
const InvoiceAgingWidget = ({ data }: { data: InvoiceAging[] }) => {
  // Find max value for scale
  const maxValue = Math.max(...(data?.map(item => item.total_outstanding) || [0]))

  // Use 0.5M increments: round up to nearest 0.5M
  const scale = Math.ceil(maxValue / 500000) * 500000

  // Format scale labels
  const formatScale = (value: number) => {
    return `$${(value / 1000000).toFixed(1)}M`
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Invoice Aging</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {data?.map((item) => (
            <div key={item.aging_bucket} className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{item.aging_bucket} days</span>
                <span className="font-medium">
                  {formatScale(item.total_outstanding)}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-6">
                <div
                  className={cn(
                    "h-6 rounded-full flex items-center justify-end pr-2 text-xs text-white font-medium",
                    item.aging_bucket.includes("600+") && "bg-red-600",
                    item.aging_bucket.includes("180") && "bg-orange-500",
                    item.aging_bucket.includes("90") && "bg-yellow-500",
                    item.aging_bucket.includes("60") && "bg-blue-500",
                    item.aging_bucket.includes("30") && "bg-green-500",
                    item.aging_bucket.includes("Current") && "bg-green-600"
                  )}
                  style={{
                    width: `${Math.min((item.total_outstanding / scale) * 100, 100)}%`
                  }}
                >
                  {((item.total_outstanding / scale) * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Scale reference */}
        <div className="mt-4 pt-4 border-t">
          <div className="flex justify-between text-xs text-gray-500">
            <span>$0</span>
            <span>{formatScale(scale / 2)}</span>
            <span>{formatScale(scale)}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
```

### Task 2: Fix Active Projects Phase Ordering

**File:** `frontend/src/components/dashboard/active-projects-tab.tsx`

**Problem:** Phases sorted alphabetically (Mobilization appears last)

**Fix:**
```tsx
// Add phase order constant at top of file
const PHASE_ORDER = [
  'Mobilization',
  'Concept Design',
  'Schematic Design',
  'Design Development',
  'Construction Documents',
  'Construction Administration',
  'Closeout'
]

// Update the component to sort by phase order
export default function ActiveProjectsTab() {
  const { data: projects } = useQuery({
    queryKey: ['active-projects'],
    queryFn: () => api.getActiveProjects()
  })

  // Sort projects by phase order
  const sortedProjects = useMemo(() => {
    if (!projects) return []

    return [...projects].sort((a, b) => {
      const aIndex = PHASE_ORDER.findIndex(p =>
        a.current_phase?.toLowerCase().includes(p.toLowerCase())
      )
      const bIndex = PHASE_ORDER.findIndex(p =>
        b.current_phase?.toLowerCase().includes(p.toLowerCase())
      )

      // If phase not found, put at end
      const aOrder = aIndex === -1 ? 999 : aIndex
      const bOrder = bIndex === -1 ? 999 : bIndex

      return aOrder - bOrder
    })
  }, [projects])

  return (
    <div className="space-y-4">
      {sortedProjects.map((project) => (
        <ProjectCard key={project.project_code} project={project} />
      ))}
    </div>
  )
}
```

### Task 3: Add Summary Bar to Active Projects

**File:** `frontend/src/components/dashboard/active-projects-tab.tsx`

**Addition:**
```tsx
// Add summary component above project list
const ActiveProjectsSummary = ({ projects }: { projects: Project[] }) => {
  const totalValue = projects.reduce((sum, p) => sum + (p.total_value || 0), 0)
  const totalInvoiced = projects.reduce((sum, p) => sum + (p.total_invoiced || 0), 0)
  const avgProgress = projects.reduce((sum, p) => sum + (p.percentage_invoiced || 0), 0) / projects.length

  return (
    <Card className="bg-blue-50 border-blue-200">
      <CardContent className="pt-6">
        <div className="grid grid-cols-4 gap-4">
          <div>
            <div className="text-sm text-gray-600">Active Projects</div>
            <div className="text-2xl font-bold">{projects.length}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Total Contract Value</div>
            <div className="text-2xl font-bold">
              ${(totalValue / 1000000).toFixed(2)}M
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Total Invoiced</div>
            <div className="text-2xl font-bold">
              ${(totalInvoiced / 1000000).toFixed(2)}M
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Avg. Progress</div>
            <div className="text-2xl font-bold">
              {avgProgress.toFixed(0)}%
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Update main component
export default function ActiveProjectsTab() {
  const { data: projects } = useQuery({
    queryKey: ['active-projects'],
    queryFn: () => api.getActiveProjects()
  })

  const sortedProjects = useMemo(() => {
    // ... sorting logic from Task 2
  }, [projects])

  return (
    <div className="space-y-6">
      {/* Summary Bar */}
      {projects && <ActiveProjectsSummary projects={projects} />}

      {/* Projects List */}
      <div className="space-y-4">
        {sortedProjects.map((project) => (
          <ProjectCard key={project.project_code} project={project} />
        ))}
      </div>
    </div>
  )
}
```

### Task 4: Debug Query Interface

**File:** Check if `frontend/src/app/query/page.tsx` exists

**If exists, fix it:**
```tsx
'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { QueryInterface } from '@/components/query-interface'

export default function QueryPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)

  const handleQuery = async (queryText: string) => {
    setQuery(queryText)
    try {
      // Call backend query endpoint
      const response = await api.executeQuery(queryText)
      setResults(response)
    } catch (error) {
      console.error('Query error:', error)
      setResults({ error: 'Query failed' })
    }
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Query Interface</h1>
      <QueryInterface onQuery={handleQuery} results={results} />
    </div>
  )
}
```

**Backend endpoint (if missing):**
```python
# backend/api/main.py
@app.post("/api/query")
async def execute_query(query: dict):
    """
    Execute natural language query against database
    """
    query_text = query.get('query')

    # Simple keyword-based routing for now
    # TODO: Add AI-powered query understanding in future

    if 'project' in query_text.lower():
        cursor.execute("SELECT * FROM projects LIMIT 10")
        return {"results": [dict(row) for row in cursor.fetchall()]}

    elif 'proposal' in query_text.lower():
        cursor.execute("SELECT * FROM proposals LIMIT 10")
        return {"results": [dict(row) for row in cursor.fetchall()]}

    elif 'invoice' in query_text.lower():
        cursor.execute("SELECT * FROM invoices LIMIT 10")
        return {"results": [dict(row) for row in cursor.fetchall()]}

    else:
        return {"error": "Query not understood. Try asking about projects, proposals, or invoices."}
```

### Task 5: Email Content Loading (Depends on Agent 1)

**File:** `frontend/src/components/email-content-viewer.tsx`

**Create placeholder component:**
```tsx
'use client'

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function EmailContentViewer({ emailId }: { emailId: number }) {
  const { data: email, isLoading } = useQuery({
    queryKey: ['email-content', emailId],
    queryFn: () => api.getEmailContent(emailId)
  })

  if (isLoading) {
    return <div>Loading email content...</div>
  }

  if (!email?.clean_body) {
    return (
      <Card className="border-yellow-200 bg-yellow-50">
        <CardContent className="pt-6">
          <p className="text-sm text-gray-600">
            Email content extraction in progress. This email will be processed soon.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Email Content</CardTitle>
      </CardHeader>
      <CardContent>
        {/* AI Summary */}
        {email.ai_summary && (
          <div className="mb-4 p-3 bg-blue-50 rounded">
            <div className="text-xs font-semibold text-blue-700 mb-1">
              AI Summary
            </div>
            <div className="text-sm">{email.ai_summary}</div>
          </div>
        )}

        {/* Key Points */}
        {email.key_points && (
          <div className="mb-4">
            <div className="text-xs font-semibold mb-1">Key Points</div>
            <ul className="list-disc list-inside text-sm space-y-1">
              {JSON.parse(email.key_points).map((point: string, i: number) => (
                <li key={i}>{point}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Full Body */}
        <div className="border-t pt-4">
          <div className="text-xs font-semibold mb-2">Full Content</div>
          <div className="text-sm whitespace-pre-wrap">{email.clean_body}</div>
        </div>

        {/* Category & Sentiment */}
        <div className="mt-4 pt-4 border-t flex gap-4 text-xs">
          <div>
            <span className="text-gray-600">Category:</span>{' '}
            <span className="font-medium">{email.category}</span>
          </div>
          <div>
            <span className="text-gray-600">Sentiment:</span>{' '}
            <span className="font-medium">{email.sentiment}</span>
          </div>
          {email.urgency_level && (
            <div>
              <span className="text-gray-600">Urgency:</span>{' '}
              <span className="font-medium">{email.urgency_level}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
```

### Task 6: Test All Fixes

```bash
# Test invoice aging scale
curl http://localhost:8000/api/invoices/aging

# Test active projects
curl http://localhost:8000/api/projects/active

# Test query interface
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "show me all projects"}'

# Test email content
curl http://localhost:8000/api/emails/1/content
```

---

## 📝 PHASE 5: DOCUMENTATION

Update:
- `MASTER_ARCHITECTURE.md` - Add new query endpoint
- Create `AGENT5_COMPLETION_REPORT.md`
- Document widget fixes for future reference

---

## 🤝 COORDINATION

**You need from Agent 1:**
- Email content populated (for email content viewer)

**You provide to others:**
- Polished dashboard UX
- Query interface foundation
- Widget fixes as reference for future widgets

**Potential conflicts:**
- None - mostly frontend-only fixes

---

## 🚫 WHAT NOT TO DO

- DON'T rebuild entire dashboard components
- DON'T create new backend endpoints if existing ones work
- DON'T wait for Agent 1 for non-email fixes
- DON'T over-engineer query interface (start simple)

---

**STATUS:** Ready for audit
**NEXT:** Agent creates AGENT5_AUDIT_REPORT.md
