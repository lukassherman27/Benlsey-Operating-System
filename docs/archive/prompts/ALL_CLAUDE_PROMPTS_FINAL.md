# 🚀 ALL CLAUDE PROMPTS - PHASE 1.5 FINAL

**Created:** November 25, 2025
**Database:** OneDrive (81MB) - `/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/bensley_master.db`
**Status:** Ready to copy/paste to each Claude

---

## ⚠️ CRITICAL: Database Path

**ALL CLAUDES:** Use OneDrive database ONLY. Never reference desktop.

```bash
WORKING_DIR="/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System"
DATABASE="${WORKING_DIR}/database/bensley_master.db"
```

---

# 🔧 CLAUDE 1 - Backend API Fixes (CRITICAL - P0)

## Your Mission

Fix **BROKEN BACKEND APIs** causing dashboard to show incorrect data.

**Investigation found:**
- `/api/briefing/daily` - SQL error: "no such column: proposal_id"
- `/api/dashboard/decision-tiles` - SQL error: "no such column: contact_person"
- Dashboard querying wrong tables (proposals instead of projects)
- Active projects shows 3 instead of 49

**Working Directory:**
```bash
cd /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System
```

---

## Your Tasks (Backend Only - NO Frontend)

### Task 1: Fix /api/briefing/daily Endpoint

**File:** `backend/api/main.py`
**Lines:** 306-417

**Current Broken Query:**
```python
cursor.execute("""
    SELECT proposal_id, project_code, project_title, status,
           health_score, days_since_contact, last_contact_date,
           next_action, outstanding_usd, total_fee_usd
    FROM projects
    WHERE is_active_project = 1
    ORDER BY health_score ASC NULLS LAST
""")
```

**Problems:**
1. ❌ `proposal_id` column doesn't exist → Should be `project_id`
2. ❌ `outstanding_usd` column doesn't exist → Remove or calculate
3. ❌ `next_action` column doesn't exist → Use `notes` instead

**Fix:**
```python
cursor.execute("""
    SELECT
        project_id,
        project_code,
        project_title,
        status,
        health_score,
        days_since_contact,
        last_contact_date,
        notes as next_action,
        total_fee_usd
    FROM projects
    WHERE is_active_project = 1
    ORDER BY health_score ASC NULLS LAST
""")
```

**Then update the row processing** (lines 328-345):
```python
for row in cursor.fetchall():
    row_dict = dict(row)
    projects.append({
        "project_id": row_dict.get("project_id"),  # Changed from proposal_id
        "code": row_dict.get("project_code"),
        "name": row_dict.get("project_title"),
        "status": row_dict.get("status"),
        "health": row_dict.get("health_score"),
        "days_since_contact": row_dict.get("days_since_contact") or 0,
        "last_contact": row_dict.get("last_contact_date"),
        "next_action": row_dict.get("next_action"),
        # Remove outstanding field or calculate it
    })
```

---

### Task 2: Fix /api/dashboard/decision-tiles Endpoint

**File:** `backend/api/main.py`
**Lines:** 2697-2866 (specifically around line 2709)

**Current Broken Query:**
```python
cursor.execute("""
    SELECT project_code, project_title, contact_person, days_since_contact, next_action
    FROM projects
    WHERE days_since_contact >= 14
    AND is_active_project = 0 AND status = 'proposal'
    ORDER BY days_since_contact DESC
    LIMIT 10
""")
```

**Problems:**
1. ❌ `contact_person` column doesn't exist
2. ❌ `next_action` column doesn't exist

**Fix:**
```python
cursor.execute("""
    SELECT
        project_code,
        project_title,
        team_lead as contact_person,
        days_since_contact,
        notes as next_action
    FROM projects
    WHERE days_since_contact >= 14
    AND is_active_project = 0
    AND status = 'proposal'
    ORDER BY days_since_contact DESC
    LIMIT 10
""")
```

**Or if team_lead doesn't exist, remove contact_person:**
```python
cursor.execute("""
    SELECT
        project_code,
        project_title,
        days_since_contact,
        notes as next_action
    FROM projects
    WHERE days_since_contact >= 14
    AND is_active_project = 0
    AND status = 'proposal'
    ORDER BY days_since_contact DESC
    LIMIT 10
""")
```

---

### Task 3: Fix Dashboard Stats (Active Projects Count)

**File:** `backend/services/proposal_service.py`
**Lines:** 350-400

**Current Wrong Query:**
```python
# This queries proposals table (only 7 active)
stats['active_projects'] = count_proposals("is_active_project = 1")
```

**Problem:** Queries `proposals` table instead of `projects` table

**Fix - Option 1 (Quick):** Add separate method
```python
def get_dashboard_stats(self):
    """Get dashboard statistics"""
    # ... existing code ...

    # FIX: Query projects table not proposals
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM projects
        WHERE is_active_project = 1
    """)
    stats['active_projects'] = cursor.fetchone()[0]

    # Keep existing proposal stats
    stats['total_proposals'] = count_proposals(None)  # 87 total
    stats['active_proposals'] = count_proposals("is_active_project = 1")  # 7 active

    conn.close()
    return stats
```

**Fix - Option 2 (Better):** Create ProjectService
```python
# Create new file: backend/services/project_service.py

class ProjectService(BaseService):
    def get_active_count(self):
        """Get count of active projects"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM projects
            WHERE is_active_project = 1
        """)
        count = cursor.fetchone()[0]
        conn.close()
        return count
```

Then update `backend/api/main.py` line 420-437:
```python
@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    """Get dashboard statistics"""
    proposal_service = ProposalService(DB_PATH)
    project_service = ProjectService(DB_PATH)  # NEW

    stats = proposal_service.get_dashboard_stats()
    stats['active_projects'] = project_service.get_active_count()  # CORRECT COUNT (49)

    return stats
```

---

### Task 4: Fix Days in Current Status Calculation

**File:** `backend/services/proposal_tracker_service.py`

**Current Issue:** `days_in_current_status` is stored as INTEGER but never updated

**Fix - Convert to Computed Field:**

Update all SELECT queries to calculate on-the-fly:
```python
# Find all queries with days_in_current_status (lines 26, 62, 149)
# Change from:
cursor.execute("""
    SELECT project_code, days_in_current_status
    FROM proposal_tracker
""")

# To:
cursor.execute("""
    SELECT
        project_code,
        CAST(JULIANDAY('now') - JULIANDAY(status_changed_date) AS INTEGER) as days_in_current_status
    FROM proposal_tracker
""")
```

**Alternative Fix - Add Daily Update Job:**

Create file: `backend/jobs/update_proposal_days.py`
```python
"""Daily job to update days_in_current_status for all proposals"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "database" / "bensley_master.db"

def update_days_in_status():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE proposal_tracker
        SET days_in_current_status = CAST(
            JULIANDAY('now') - JULIANDAY(status_changed_date) AS INTEGER
        )
        WHERE status_changed_date IS NOT NULL
    """)

    conn.commit()
    rows_updated = cursor.rowcount
    conn.close()

    print(f"Updated {rows_updated} proposals")

if __name__ == "__main__":
    update_days_in_status()
```

Add to crontab:
```bash
# Run daily at 1 AM
0 1 * * * cd /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System && python3 backend/jobs/update_proposal_days.py
```

---

## Testing

### Test 1: Briefing Daily
```bash
cd /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System

# Restart backend
cd backend
pkill -f uvicorn
uvicorn api.main:app --reload --port 8000 &

# Test endpoint
curl http://localhost:8000/api/briefing/daily | jq
# Should return actual data, no SQL errors

# Verify active projects count
curl http://localhost:8000/api/briefing/daily | jq '.metrics.active_projects'
# Should show 49, not 3
```

### Test 2: Decision Tiles
```bash
curl http://localhost:8000/api/dashboard/decision-tiles | jq
# Should return data, no "contact_person" error
```

### Test 3: Dashboard Stats
```bash
curl http://localhost:8000/api/dashboard/stats | jq '.active_projects'
# Should show 49
```

### Test 4: Days Calculation
```bash
sqlite3 database/bensley_master.db "
SELECT
    project_code,
    status_changed_date,
    CAST(JULIANDAY('now') - JULIANDAY(status_changed_date) AS INTEGER) as computed_days,
    days_in_current_status as stored_days
FROM proposal_tracker
LIMIT 5
"
# Computed_days should be realistic, stored_days might be 0
```

---

## Report Back With

✅ **Screenshots:**
1. curl output of `/api/briefing/daily` showing actual data (not fallback)
2. Dashboard showing 49 active projects (not 3)

✅ **SQL verification:**
```bash
# Show active project count from projects table
sqlite3 database/bensley_master.db "SELECT COUNT(*) FROM projects WHERE is_active_project = 1"
# Should show 49
```

✅ **Confirm:**
- No more SQL errors in API responses
- Dashboard stats showing correct counts
- Days in status calculating properly

---

**Timeline:** 2-3 hours
**Priority:** 🔴 P0 CRITICAL - Blocking all dashboard functionality

---

# 📊 CLAUDE 2 - Invoice Aging Widget + RLHF

## Your Mission

Create **Invoice Aging Breakdown Widget** + continue RLHF work

**Working Directory:**
```bash
cd /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System
```

---

## Part 1: Invoice Aging Breakdown (NEW)

### What Bill Wants:
> "Outstanding invoices widget should have aging summary, more graphic, with actual value separated by days: 0-10 days, 10-30 days, 30-90 days, 90+ days. Bar chart of each outstanding invoice part."

### Backend Endpoint

**File:** `backend/api/main.py`

Add new endpoint:
```python
@app.get("/api/invoices/aging")
def get_invoice_aging():
    """Get invoice aging breakdown for outstanding invoices"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            invoice_number,
            invoice_date,
            invoice_amount,
            COALESCE(payment_amount, 0) as payment_amount,
            (invoice_amount - COALESCE(payment_amount, 0)) as outstanding,
            CAST(JULIANDAY('now') - JULIANDAY(invoice_date) AS INTEGER) as days_outstanding,
            project_code,
            status
        FROM invoices
        WHERE status NOT IN ('paid', 'cancelled')
        AND (invoice_amount - COALESCE(payment_amount, 0)) > 0
        ORDER BY invoice_date ASC
    """)

    invoices = [dict(row) for row in cursor.fetchall()]

    # Calculate aging buckets
    aging = {
        "0-10": {"count": 0, "amount": 0, "invoices": []},
        "10-30": {"count": 0, "amount": 0, "invoices": []},
        "30-90": {"count": 0, "amount": 0, "invoices": []},
        "90+": {"count": 0, "amount": 0, "invoices": []}
    }

    for inv in invoices:
        days = inv['days_outstanding']
        outstanding = inv['outstanding']

        if days <= 10:
            bucket = "0-10"
        elif days <= 30:
            bucket = "10-30"
        elif days <= 90:
            bucket = "30-90"
        else:
            bucket = "90+"

        aging[bucket]['count'] += 1
        aging[bucket]['amount'] += outstanding
        aging[bucket]['invoices'].append({
            "invoice_number": inv['invoice_number'],
            "project_code": inv['project_code'],
            "outstanding": outstanding,
            "days_outstanding": days
        })

    conn.close()

    return {
        "success": True,
        "aging": aging,
        "total_outstanding": sum(bucket['amount'] for bucket in aging.values()),
        "total_invoices": sum(bucket['count'] for bucket in aging.values())
    }
```

### Frontend Component

**File:** `frontend/src/components/dashboard/invoice-aging-widget.tsx`

```typescript
"use client"

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { DollarSign, TrendingUp, AlertTriangle } from 'lucide-react'

export function InvoiceAgingWidget() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['invoice-aging'],
    queryFn: () => api.get('/api/invoices/aging'),
    refetchInterval: 5 * 60 * 1000 // Refresh every 5 minutes
  })

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Invoice Aging</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Loading aging data...</p>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Invoice Aging</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">Error loading aging data</p>
        </CardContent>
      </Card>
    )
  }

  const aging = data?.aging || {}
  const totalOutstanding = data?.total_outstanding || 0
  const totalInvoices = data?.total_invoices || 0

  // Prepare data for bar chart
  const chartData = [
    {
      bucket: '0-10 days',
      amount: aging['0-10']?.amount || 0,
      count: aging['0-10']?.count || 0,
      color: '#22c55e' // green
    },
    {
      bucket: '10-30 days',
      amount: aging['10-30']?.amount || 0,
      count: aging['10-30']?.count || 0,
      color: '#eab308' // yellow
    },
    {
      bucket: '30-90 days',
      amount: aging['30-90']?.amount || 0,
      count: aging['30-90']?.count || 0,
      color: '#f97316' // orange
    },
    {
      bucket: '90+ days',
      amount: aging['90+']?.amount || 0,
      count: aging['90+']?.count || 0,
      color: '#ef4444' // red
    }
  ]

  // Flag if too many invoices are aging
  const oldInvoices = (aging['30-90']?.count || 0) + (aging['90+']?.count || 0)
  const isAging = oldInvoices > totalInvoices * 0.3 // More than 30% old

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-5 w-5" />
            Invoice Aging
          </CardTitle>
          {isAging && (
            <Badge variant="destructive" className="gap-1">
              <AlertTriangle className="h-3 w-3" />
              Aging
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Total Outstanding</p>
            <p className="text-2xl font-bold">
              ${(totalOutstanding / 1000000).toFixed(2)}M
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Total Invoices</p>
            <p className="text-2xl font-bold">{totalInvoices}</p>
          </div>
        </div>

        {/* Bar Chart */}
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="bucket"
              tick={{ fontSize: 12 }}
              angle={-15}
              textAnchor="end"
              height={60}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `$${(value / 1000000).toFixed(1)}M`}
            />
            <Tooltip
              formatter={(value: number) => [`$${value.toLocaleString()}`, 'Amount']}
              labelFormatter={(label) => `Aging: ${label}`}
            />
            <Bar dataKey="amount" radius={[8, 8, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        {/* Breakdown Table */}
        <div className="space-y-2">
          {chartData.map((bucket, i) => (
            <div
              key={i}
              className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50"
              style={{ borderLeft: `4px solid ${bucket.color}` }}
            >
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{bucket.bucket}</span>
                <Badge variant="outline" className="text-xs">
                  {bucket.count} invoices
                </Badge>
              </div>
              <span className="text-sm font-semibold">
                ${(bucket.amount / 1000000).toFixed(2)}M
              </span>
            </div>
          ))}
        </div>

        {/* Warning for 90+ days */}
        {aging['90+']?.count > 0 && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 text-red-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-900">
                  {aging['90+'].count} invoice{aging['90+'].count > 1 ? 's' : ''} overdue 90+ days
                </p>
                <p className="text-xs text-red-700 mt-1">
                  Total: ${(aging['90+'].amount / 1000000).toFixed(2)}M - Follow up required
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
```

### Update Dashboard Page

**File:** `frontend/src/app/(dashboard)/page.tsx`

Replace the existing outstanding invoices widget with:
```typescript
import { InvoiceAgingWidget } from '@/components/dashboard/invoice-aging-widget'

// In your dashboard layout:
<InvoiceAgingWidget />
```

---

## Part 2: Continue RLHF Work (Already Assigned)

Your previous RLHF feedback system work is GOOD. Keep:
- Contextual feedback dialog
- Issue type categorization
- Training data logging

**No changes needed** - just ensure it integrates with the new invoice aging widget (add feedback buttons).

---

## Testing

```bash
# Test aging endpoint
curl http://localhost:8000/api/invoices/aging | jq

# Should show structure like:
{
  "success": true,
  "aging": {
    "0-10": {"count": 5, "amount": 500000, "invoices": [...]},
    "10-30": {"count": 10, "amount": 1200000, "invoices": [...]},
    "30-90": {"count": 15, "amount": 2000000, "invoices": [...]},
    "90+": {"count": 20, "amount": 730973.75, "invoices": [...]}
  },
  "total_outstanding": 4430973.75,
  "total_invoices": 50
}
```

**Open dashboard:** http://localhost:3002
- Verify invoice aging widget shows bar chart
- Verify colors: green (0-10), yellow (10-30), orange (30-90), red (90+)
- Verify 90+ days shows warning banner
- Verify total outstanding matches

---

## Report Back With

✅ **Screenshots:**
1. Invoice Aging Widget with bar chart
2. Breakdown showing all 4 buckets
3. Warning banner for 90+ days invoices

✅ **API verification:**
```bash
curl http://localhost:8000/api/invoices/aging | jq '.aging'
```

✅ **Confirm:**
- Colors correct (green → yellow → orange → red)
- Total outstanding matches actual database
- Warning shows if 90+ days invoices exist

---

**Timeline:** 3-4 hours (2h aging + 1-2h RLHF polish)
**Priority:** 🟡 HIGH - Critical visibility for collections

---

# 🏗️ CLAUDE 3 - Hierarchical Project View + Fix Build

## Your Mission

Fix build error + complete hierarchical project breakdown

**Working Directory:**
```bash
cd /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System
```

---

## Part 1: Fix Build Error (URGENT)

### Problem:
```
Module not found: Can't resolve collapsible, badge, progress
```

### Root Cause:
- `collapsible.tsx` component doesn't exist
- `@radix-ui/react-collapsible` package not installed

### Fix Step 1: Install Package
```bash
cd /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/frontend

npm install @radix-ui/react-collapsible
```

### Fix Step 2: Create Collapsible Component

**File:** `frontend/src/components/ui/collapsible.tsx`

Create this new file:
```typescript
"use client"

import * as React from "react"
import * as CollapsiblePrimitive from "@radix-ui/react-collapsible"

const Collapsible = CollapsiblePrimitive.Root

const CollapsibleTrigger = CollapsiblePrimitive.CollapsibleTrigger

const CollapsibleContent = CollapsiblePrimitive.CollapsibleContent

export { Collapsible, CollapsibleTrigger, CollapsibleContent }
```

### Fix Step 3: Verify Imports

**File:** `frontend/src/components/projects/project-hierarchy-tree.tsx`

Ensure imports are correct:
```typescript
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
```

### Test Build:
```bash
cd frontend
npm run build

# Should succeed with no errors
```

---

## Part 2: Complete Hierarchical Project View

Continue with your previous task (already well-scoped in previous prompt).

**Key Requirements from Investigation:**
- Data exists in `project_fee_breakdown` table (372 records)
- Shows: Project → Discipline → Phase → Invoices
- Example project 25 BK-002 has 15 phase records
- Must show: Landscape, Architecture, Interior disciplines
- Must show: Mobilization, Concept, DD, CD, CA phases

**No changes to your previous prompt needed** - just fix the build first, then continue.

---

## Testing

```bash
# 1. Test build
cd /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/frontend
npm run build

# 2. Start dev server
npm run dev

# 3. Open project page
# http://localhost:3002/projects/25-BK-002

# Should show hierarchical tree WITHOUT build errors
```

---

## Report Back With

✅ **Build success:**
```bash
npm run build
# Copy/paste output showing "Compiled successfully"
```

✅ **Screenshots:**
1. Hierarchical tree (collapsed view)
2. Expanded view showing phases + invoices
3. Progress bars for each phase

✅ **Confirm:**
- No build errors
- Collapsible component works
- Tree shows all 3 levels (discipline → phase → invoice)

---

**Timeline:** 2-3 hours (30min build fix + 2h hierarchy)
**Priority:** 🔴 P0 - Blocking build

---

# 📋 CLAUDE 4 - Proposals Dashboard + Inline Editing

## Your Mission

Fix proposals page + add inline editing for ALL fields

**Working Directory:**
```bash
cd /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System
```

---

## Investigation Findings

**Current Issues:**
1. Status update fails with constraint error
2. Showing 37 proposals (should be 87 total, 47 active)
3. Days in status not updating
4. No inline editing for dates, fees, etc.
5. No discipline/phase breakdown shown

**Database Tables:**
- `proposals` table: 87 records (master data)
- `proposal_tracker` table: 37 records (active tracking)
- `project_fee_breakdown` table: Phase breakdowns (for signed contracts only)

---

## Part 1: Fix Status Constraint Error

### Problem:
User trying to set status to "active" → ERROR

### Valid Statuses:
```
'First Contact'  (Title Case)
'Drafting'
'Proposal Sent'
'On Hold'
'Archived'
'Contract Signed'
```

### Fix Frontend Dropdown

**File:** `frontend/src/app/(dashboard)/tracker/page.tsx`

Update status dropdown to ONLY show valid values:
```typescript
const VALID_STATUSES = [
  'First Contact',
  'Drafting',
  'Proposal Sent',
  'On Hold',
  'Archived',
  'Contract Signed'
] as const

// In your status select component:
<Select value={proposal.current_status} onValueChange={(value) => handleStatusChange(proposal.project_code, value)}>
  <SelectTrigger>
    <SelectValue placeholder="Select status" />
  </SelectTrigger>
  <SelectContent>
    {VALID_STATUSES.map(status => (
      <SelectItem key={status} value={status}>
        {status}
      </SelectItem>
    ))}
  </SelectContent>
</Select>
```

---

## Part 2: Fix Total Proposals Display

### Show All Counts:
```typescript
// API call to get comprehensive stats
const { data: stats } = useQuery({
  queryKey: ['proposal-stats'],
  queryFn: () => api.get('/api/proposals/stats')
})

// Display breakdown:
<div className="grid grid-cols-4 gap-4">
  <Card>
    <CardHeader>
      <CardTitle className="text-sm">Total Proposals</CardTitle>
    </CardHeader>
    <CardContent>
      <p className="text-2xl font-bold">{stats?.total || 87}</p>
      <p className="text-xs text-muted-foreground">All time</p>
    </CardContent>
  </Card>

  <Card>
    <CardHeader>
      <CardTitle className="text-sm">Active Pipeline</CardTitle>
    </CardHeader>
    <CardContent>
      <p className="text-2xl font-bold">{stats?.active || 47}</p>
      <p className="text-xs text-muted-foreground">In progress</p>
    </CardContent>
  </Card>

  <Card>
    <CardHeader>
      <CardTitle className="text-sm">Contracts Signed (2025)</CardTitle>
    </CardHeader>
    <CardContent>
      <p className="text-2xl font-bold">{stats?.signed_2025 || 0}</p>
      <p className="text-xs text-muted-foreground">${(stats?.signed_value_2025 / 1000000).toFixed(1)}M</p>
    </CardContent>
  </Card>

  <Card>
    <CardHeader>
      <CardTitle className="text-sm">Total Sent (2025)</CardTitle>
    </CardHeader>
    <CardContent>
      <p className="text-2xl font-bold">{stats?.sent_2025 || 0}</p>
      <p className="text-xs text-muted-foreground">${(stats?.sent_value_2025 / 1000000).toFixed(1)}M value</p>
    </CardContent>
  </Card>
</div>
```

### Backend Endpoint:

**File:** `backend/api/main.py`

Add comprehensive stats endpoint:
```python
@app.get("/api/proposals/stats")
def get_proposal_comprehensive_stats():
    """Get comprehensive proposal statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total proposals (all time, all statuses)
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(project_value), 0) FROM proposals")
    total_row = cursor.fetchone()
    total_count = total_row[0]
    total_value = total_row[1]

    # Active proposals (not lost/cancelled)
    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(project_value), 0)
        FROM proposals
        WHERE status NOT IN ('lost', 'cancelled', 'archived')
    """)
    active_row = cursor.fetchone()
    active_count = active_row[0]
    active_value = active_row[1]

    # Contracts signed in 2025
    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(project_value), 0)
        FROM proposals
        WHERE status = 'won'
        AND contract_signed_date >= '2025-01-01'
    """)
    signed_2025_row = cursor.fetchone()
    signed_2025_count = signed_2025_row[0]
    signed_2025_value = signed_2025_row[1]

    # Proposals sent in 2025 (total value sent, regardless of status)
    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(project_value), 0)
        FROM proposals
        WHERE proposal_sent_date >= '2025-01-01'
    """)
    sent_2025_row = cursor.fetchone()
    sent_2025_count = sent_2025_row[0]
    sent_2025_value = sent_2025_row[1]

    conn.close()

    return {
        "total": total_count,
        "total_value": total_value,
        "active": active_count,
        "active_value": active_value,
        "signed_2025": signed_2025_count,
        "signed_value_2025": signed_2025_value,
        "sent_2025": sent_2025_count,
        "sent_value_2025": sent_2025_value
    }
```

---

## Part 3: Inline Editing for All Fields

### Editable Fields:
- ✏️ First Contact Date
- ✏️ Drafting Date (if not in proposal_tracker, join with proposals)
- ✏️ Proposal Sent Date
- ✏️ Contract Signed Date (when status = 'Contract Signed')
- ✏️ Project Value
- ✏️ Current Remark
- ✏️ Waiting On
- ✏️ Next Steps

### Create Inline Edit Component

**File:** `frontend/src/components/proposals/inline-edit-field.tsx`

```typescript
"use client"

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Check, X, Edit2 } from 'lucide-react'
import { toast } from 'sonner'

interface InlineEditFieldProps {
  proposalCode: string
  field: string
  value: string | number | null
  type?: 'text' | 'date' | 'number' | 'textarea'
  label: string
}

export function InlineEditField({
  proposalCode,
  field,
  value,
  type = 'text',
  label
}: InlineEditFieldProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState(value || '')

  const queryClient = useQueryClient()

  const updateMutation = useMutation({
    mutationFn: (newValue: string | number) =>
      api.patch(`/api/proposals/${proposalCode}`, {
        [field]: newValue,
        updated_by: 'bill'
      }),
    onSuccess: () => {
      toast.success(`${label} updated`)
      queryClient.invalidateQueries({ queryKey: ['proposals'] })
      setIsEditing(false)
    },
    onError: () => {
      toast.error(`Failed to update ${label}`)
    }
  })

  const handleSave = () => {
    if (editValue !== value) {
      updateMutation.mutate(editValue)
    } else {
      setIsEditing(false)
    }
  }

  const handleCancel = () => {
    setEditValue(value || '')
    setIsEditing(false)
  }

  if (!isEditing) {
    return (
      <div className="group flex items-center gap-2">
        <span className="text-sm">
          {type === 'date' && value
            ? new Date(value).toLocaleDateString()
            : value || 'Not set'}
        </span>
        <Button
          variant="ghost"
          size="sm"
          className="opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={() => setIsEditing(true)}
        >
          <Edit2 className="h-3 w-3" />
        </Button>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2">
      {type === 'textarea' ? (
        <Textarea
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          rows={3}
          className="flex-1"
        />
      ) : (
        <Input
          type={type}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          className="flex-1"
        />
      )}
      <Button
        size="sm"
        variant="ghost"
        onClick={handleSave}
        disabled={updateMutation.isPending}
      >
        <Check className="h-4 w-4 text-green-600" />
      </Button>
      <Button
        size="sm"
        variant="ghost"
        onClick={handleCancel}
        disabled={updateMutation.isPending}
      >
        <X className="h-4 w-4 text-red-600" />
      </Button>
    </div>
  )
}
```

### Use in Proposal Detail View

**File:** `frontend/src/app/(dashboard)/tracker/[projectCode]/page.tsx`

```typescript
import { InlineEditField } from '@/components/proposals/inline-edit-field'

// In your proposal detail view:
<div className="space-y-4">
  <div>
    <Label>First Contact Date</Label>
    <InlineEditField
      proposalCode={projectCode}
      field="first_contact_date"
      value={proposal.first_contact_date}
      type="date"
      label="First Contact Date"
    />
  </div>

  <div>
    <Label>Proposal Sent Date</Label>
    <InlineEditField
      proposalCode={projectCode}
      field="proposal_sent_date"
      value={proposal.proposal_sent_date}
      type="date"
      label="Proposal Sent Date"
    />
  </div>

  <div>
    <Label>Project Value</Label>
    <InlineEditField
      proposalCode={projectCode}
      field="project_value"
      value={proposal.project_value}
      type="number"
      label="Project Value"
    />
  </div>

  <div>
    <Label>Current Remark</Label>
    <InlineEditField
      proposalCode={projectCode}
      field="current_remark"
      value={proposal.current_remark}
      type="textarea"
      label="Current Remark"
    />
  </div>

  <div>
    <Label>Waiting On</Label>
    <InlineEditField
      proposalCode={projectCode}
      field="waiting_on"
      value={proposal.waiting_on}
      type="text"
      label="Waiting On"
    />
  </div>

  <div>
    <Label>Next Steps</Label>
    <InlineEditField
      proposalCode={projectCode}
      field="next_steps"
      value={proposal.next_steps}
      type="textarea"
      label="Next Steps"
    />
  </div>
</div>
```

### Backend Update Endpoint

**File:** `backend/api/main.py`

Ensure PATCH endpoint accepts all fields:
```python
@app.patch("/api/proposals/{project_code}")
def update_proposal(project_code: str, updates: dict):
    """Update proposal fields"""

    allowed_fields = {
        'first_contact_date',
        'drafting_date',  # Add if missing
        'proposal_sent_date',
        'contract_signed_date',
        'project_value',
        'current_status',
        'current_remark',
        'waiting_on',
        'next_steps',
        'updated_by'
    }

    # Filter to allowed fields
    clean_updates = {k: v for k, v in updates.items() if k in allowed_fields}

    if not clean_updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Build SET clause
    set_parts = []
    values = []
    for field, value in clean_updates.items():
        set_parts.append(f"{field} = ?")
        values.append(value)

    values.append(project_code)

    # Update proposal_tracker
    sql = f"""
        UPDATE proposal_tracker
        SET {', '.join(set_parts)}, updated_at = datetime('now')
        WHERE project_code = ?
    """

    cursor.execute(sql, values)
    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Proposal not found")

    conn.close()

    return {"success": True, "message": "Proposal updated"}
```

---

## Part 4: Show Discipline Breakdown

For proposals that became projects, join with `proposals` table to show disciplines:

```typescript
// In proposal detail view:
const { data: disciplines } = useQuery({
  queryKey: ['proposal-disciplines', projectCode],
  queryFn: () => api.get(`/api/proposals/${projectCode}/disciplines`)
})

// Display:
<div className="flex gap-2">
  {disciplines?.is_landscape && <Badge variant="secondary">Landscape</Badge>}
  {disciplines?.is_architect && <Badge variant="secondary">Architecture</Badge>}
  {disciplines?.is_interior && <Badge variant="secondary">Interior</Badge>}
</div>
```

### Backend:
```python
@app.get("/api/proposals/{project_code}/disciplines")
def get_proposal_disciplines(project_code: str):
    """Get discipline flags for proposal"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT is_landscape, is_architect, is_interior
        FROM proposals
        WHERE project_code = ?
    """, (project_code,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Proposal not found")

    return dict(row)
```

---

## Testing

```bash
# Test stats endpoint
curl http://localhost:8000/api/proposals/stats | jq

# Test update endpoint
curl -X PATCH http://localhost:8000/api/proposals/25-BK-018 \
  -H "Content-Type: application/json" \
  -d '{"project_value": 2500000, "updated_by": "bill"}'

# Verify in database
sqlite3 database/bensley_master.db "SELECT project_code, project_value, updated_at FROM proposal_tracker WHERE project_code = '25-BK-018'"
```

**Open tracker:** http://localhost:3002/tracker
- Change status → Should succeed (no constraint error)
- Edit fields inline → Should save to database
- See total proposals: 87
- See active proposals: 47
- See discipline badges

---

## Report Back With

✅ **Screenshots:**
1. Proposal tracker with all 4 stat cards (87 total, 47 active, etc.)
2. Status dropdown showing ONLY valid statuses
3. Inline editing in action (before/after edit)
4. Proposal detail with discipline badges

✅ **Database verification:**
```bash
# Show inline edit saved
sqlite3 database/bensley_master.db "SELECT project_code, project_value, current_remark, updated_at FROM proposal_tracker WHERE project_code = '25-BK-018'"
```

✅ **Confirm:**
- Status updates work (no errors)
- All fields editable inline
- Stats show correct counts (87 total, 47 active)
- Days in status displaying correctly

---

**Timeline:** 4-5 hours
**Priority:** 🟡 HIGH - Critical for proposal management

---

# 📈 CLAUDE 5 - KPI Trend Indicators

## Your Mission

Add trend indicators to ALL KPI cards (month-over-month, quarter-over-quarter)

**Working Directory:**
```bash
cd /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System
```

---

## Context

**Investigation found:** Dashboard APIs were broken, now being fixed by Claude 1.

**Your job:** Once Claude 1 fixes the APIs, add trend indicators showing:
- ↑ +8.2% (green) if increasing
- ↓ -3.5% (red) if decreasing
- → 0.0% (gray) if stable

---

## Wait for Claude 1

**IMPORTANT:** Claude 1 is fixing `/api/briefing/daily` and `/api/dashboard/stats`.

**Wait until:**
1. Claude 1 reports back that APIs are fixed
2. Verify APIs return data without errors:
```bash
curl http://localhost:8000/api/dashboard/stats | jq
curl http://localhost:8000/api/briefing/daily | jq
```

Then proceed with your previous prompt (already well-scoped).

**No changes needed to your task** - just wait for Claude 1 to finish first.

---

## Dependencies

- ✅ Claude 1 fixes `/api/dashboard/stats`
- ✅ APIs return actual data (not fallback)
- ✅ Then you add trend indicators to KPIs

---

**Timeline:** 2-3 hours (after Claude 1 completes)
**Priority:** 🟢 MEDIUM - Can wait for Claude 1

---

# 📧 CLAUDE 6 - Email Intelligence UI

## Your Mission

Build Email Intelligence UI (validation, linking, timeline)

**Working Directory:**
```bash
cd /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System
```

---

## Your Full Prompt

**Use the complete prompt from:** `CLAUDE_6_EMAIL_INTELLIGENCE_UI_PROMPT.md`

**No changes needed** - that prompt is comprehensive and uses correct OneDrive paths.

**Key points:**
- Build 3 tabs: Email Links, Validation Queue, Project Timeline
- 6 backend API endpoints
- RLHF integration (log all corrections)
- Recent emails: Click opens popup (not navigate)
- Categorization filters

---

**Timeline:** 6-7 hours
**Priority:** 🟡 HIGH - Foundation for Phase 2 RAG

---

# 📝 COORDINATION NOTES

## Dependencies

1. **Claude 1** → Must complete FIRST (fixes broken APIs)
2. **Claude 3** → Can run IMMEDIATELY (build fix independent)
3. **Claude 2, 4, 6** → Can run IMMEDIATELY (independent work)
4. **Claude 5** → Wait for Claude 1 to finish

## No Conflicts

- **Claude 1:** Backend API files only
- **Claude 2:** New widget component + backend endpoint
- **Claude 3:** Frontend components + npm install
- **Claude 4:** Proposals page + new backend endpoint
- **Claude 5:** KPI components (uses Claude 1's fixed APIs)
- **Claude 6:** Email pages (separate feature area)

## Testing Order

1. Test Claude 1 fixes first (verify APIs work)
2. Test Claude 3 build fix (verify no errors)
3. Test Claude 2, 4, 6 in parallel
4. Test Claude 5 last (depends on Claude 1)

---

**ALL PROMPTS READY TO COPY/PASTE**

Launch order:
1. Claude 1 (CRITICAL - start first)
2. Claude 3 (CRITICAL - build blocker)
3. Claude 2, 4, 6 (parallel)
4. Claude 5 (after Claude 1 completes)
