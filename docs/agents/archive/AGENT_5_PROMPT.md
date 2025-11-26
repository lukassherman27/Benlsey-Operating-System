# AGENT 5: Email Integration

**Your Mission:** Integrate email components into proposal pages and create email search page

**What You're Building:**
1. Enhance proposal page with Emails tab
2. Create global email search page
3. Test full end-to-end flow

**CRITICAL RULES:**
- ✅ Minimal code changes - mostly wiring up components
- ✅ Follow existing page structure patterns
- ✅ Test all user flows
- ❌ DO NOT break existing functionality
- ❌ DO NOT create new routing patterns

**Dependencies:** Wait for Agent 4 (needs components built)

---

## Task 5.1: Add Email Tab to Proposal Page

**File:** `frontend/src/app/(dashboard)/proposals/[projectCode]/page.tsx`

Find the Tabs component and add an Emails tab:

```tsx
import { EmailList } from "@/components/emails/email-list"

// Inside the component, add this tab:
<TabsContent value="emails">
  <Card>
    <CardHeader>
      <CardTitle>Emails</CardTitle>
      <CardDescription>
        All emails linked to this proposal ({proposalData?.project_code})
      </CardDescription>
    </CardHeader>
    <CardContent>
      <EmailList
        proposalId={proposalData?.proposal_id}
        limit={100}
      />
    </CardContent>
  </Card>
</TabsContent>

// Add the tab trigger in the TabsList:
<TabsList>
  <TabsTrigger value="overview">Overview</TabsTrigger>
  <TabsTrigger value="details">Details</TabsTrigger>
  <TabsTrigger value="emails">Emails</TabsTrigger>
  <TabsTrigger value="timeline">Timeline</TabsTrigger>
</TabsList>
```

---

## Task 5.2: Create Email Search Page

**File:** `frontend/src/app/(dashboard)/emails/page.tsx`

Create a new page for global email search:

```tsx
"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Search, Filter } from "lucide-react"
import { EmailList } from "@/components/emails/email-list"

export default function EmailsPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [category, setCategory] = useState<string | undefined>()
  const [urgency, setUrgency] = useState<string | undefined>()

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Email Search</h1>
        <p className="text-muted-foreground">Search and filter all emails</p>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Category</label>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger>
                  <SelectValue placeholder="All categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All categories</SelectItem>
                  <SelectItem value="proposal">Proposal</SelectItem>
                  <SelectItem value="contract">Contract</SelectItem>
                  <SelectItem value="financial">Financial</SelectItem>
                  <SelectItem value="rfi">RFI</SelectItem>
                  <SelectItem value="meeting">Meeting</SelectItem>
                  <SelectItem value="general">General</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Urgency</label>
              <Select value={urgency} onValueChange={setUrgency}>
                <SelectTrigger>
                  <SelectValue placeholder="All urgency levels" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All levels</SelectItem>
                  <SelectItem value="urgent">Urgent</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Search</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search subject or content..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      <Card>
        <CardHeader>
          <CardTitle>Results</CardTitle>
        </CardHeader>
        <CardContent>
          <EmailList
            limit={100}
          />
        </CardContent>
      </Card>
    </div>
  )
}
```

---

## Task 5.3: Add Email Activity Widget to Dashboard

**File:** `frontend/src/app/(dashboard)/page.tsx`

Add the EmailActivityWidget to the dashboard:

```tsx
import { EmailActivityWidget } from "@/components/emails/email-activity-widget"

// Add it to the dashboard grid:
<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
  {/* Existing widgets */}
  <QuickActionsWidget />
  <InvoiceAgingWidget />

  {/* Add this */}
  <EmailActivityWidget />
</div>
```

---

## Task 5.4: Update Navigation

**File:** `frontend/src/components/layout/app-shell.tsx`

Add Emails link to the sidebar navigation:

```tsx
{
  title: "Emails",
  href: "/emails",
  icon: Mail,
}
```

---

## Full End-to-End Testing

Test these user flows:

### Flow 1: View Proposal Emails
1. Go to http://localhost:3002/proposals/25BK033
2. Click "Emails" tab
3. Should see list of emails linked to that proposal
4. Click an email
5. Modal should open with AI summary and full content

### Flow 2: Global Email Search
1. Go to http://localhost:3002/emails
2. Search for "contract"
3. Should see filtered results
4. Filter by category "proposal"
5. Results should update
6. Click an email
7. Should see linked proposals in the modal

### Flow 3: Dashboard Email Activity
1. Go to http://localhost:3002/
2. Should see "Recent Email Activity" widget
3. Should show email count and urgent count
4. Should list 3 recent emails

### Flow 4: Email Threads
1. Find an email that's part of a thread
2. Open email detail modal
3. Should show "Part of thread with X messages"
4. (Future enhancement: click to view thread)

---

## Verification Commands

```bash
# Frontend should build without errors
cd frontend && npm run build

# Check for TypeScript errors
npm run type-check

# Start dev server
PORT=3002 npm run dev
```

---

## SUCCESS CRITERIA

- ✅ Proposal page has working Emails tab showing proposal-specific emails
- ✅ Global email search page at /emails works
- ✅ Email activity widget shows on dashboard
- ✅ Navigation includes Emails link
- ✅ All modals open and close properly
- ✅ Search and filters work
- ✅ AI insights display correctly
- ✅ No console errors
- ✅ Frontend builds successfully

**Report back:** "Agent 5 complete. Email integration tested end-to-end. All flows working."

---

## Final Integration Checklist

When complete, verify this full flow:
1. ✅ Agent 1 processed 3,334 emails with AI → email_content populated
2. ✅ Agent 1 built email threads → email_threads table populated
3. ✅ Agent 2 ran migration → indexes and views created
4. ✅ Agent 3 built APIs → curl tests pass
5. ✅ Agent 4 built components → no React errors
6. ✅ Agent 5 integrated → full user flows work

**System is complete when:** User can browse proposals, click Emails tab, see AI-analyzed emails, search globally, and view email activity on dashboard.
