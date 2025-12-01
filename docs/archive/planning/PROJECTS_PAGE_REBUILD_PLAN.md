# Projects Page Rebuild Plan - HANDOFF DOCUMENT

## Session Context
Date: 2025-11-20
Status: Ready for rebuild in fresh session
Context Usage: 127K/200K (need fresh context for full rebuild + testing)

---

## CRITICAL: What User Wants (Based on Excel Screenshot)

User showed Excel example at `/Users/lukassherman/Desktop/Screenshot 2568-11-20 at 1.35.37 PM.png`

### Desired Hierarchy Structure:
```
PROJECT (click to expand)
  └─ DISCIPLINE (Landscape - $100K contract fee)
       ├─ Summary Row: [TOTAL PAID | TOTAL OUTSTANDING | TOTAL REMAINING]
       ├─ Phase: Mobilization ($15,000)
       │   └─ Invoice #, Invoice Date, Payment Amt, Payment Date, Outstanding Amt
       ├─ Phase: Concept Design ($25,000)
       │   └─ Invoice details...
       ├─ Phase: Concept Design (50%) ($12,500)  ← PARTIAL INVOICING!
       │   └─ Invoice #, Invoice Date, Payment Amt, Payment Date, Outstanding
       ├─ Phase: Concept Design (50%) ($12,500)
       │   └─ Invoice details...
       ├─ Phase: Design Development ($30,000)
       │   └─ Invoice details...
       ├─ Phase: Design Development (50%) ($15,000)
       │   └─ Invoice details...
       etc.
```

### Key Requirements:
1. **DISCIPLINE COMES FIRST** under project (not nested after other levels)
2. **Discipline summary** shows contract fee + 3 totals: PAID, OUTSTANDING, REMAINING
3. **Phases** show phase fee amount and % if partial (e.g., "Concept Design (50%) - $12,500")
4. **Invoice rows** show ALL fields:
   - Invoice Number
   - Invoice Date
   - Payment Amount
   - Payment Date
   - Outstanding Amount

---

## Current State (BROKEN)

### File: `frontend/src/app/(dashboard)/projects/page.tsx`
- **Top widgets**: 4 summary cards showing blank/useless data (Active Projects, Outstanding Invoices, Upcoming Deadlines, Unanswered RFIs)
- **Table structure**: WRONG hierarchy - shows Project → (expand) → Discipline → Phase → Invoice
- **User wants**: Project → (expand) → **Discipline-level summary** → Phase → Invoice

### File: `frontend/src/app/(dashboard)/page.tsx` (Overview/Dashboard)
- Has the 6 metric cards + 4 insight widgets
- Should be SIMPLE (just 6 metrics)
- The 4 insight widgets should move to **Projects page**

---

## Data Issues Found & Fixed

### Problem 1: Stale Project Summaries (FIXED ✓)
**Issue**: `projects` table had wrong `paid_to_date_usd` and `outstanding_usd` values
- Qinhu showed: paid=$0, outstanding=$893,750 (WRONG)
- Actually: paid=$243,750, outstanding=$650,000 (from invoice detail)

**Root Cause**:
- Invoice `status` field not maintained (invoices with `payment_amount > 0` still had `status='outstanding'`)
- Triggers from migration 023 looked for `status='paid'` but didn't find them

**Fix Applied**:
```sql
-- Recalculated all 50 active projects based on actual payment_amount
UPDATE projects
SET
  paid_to_date_usd = (SELECT COALESCE(SUM(payment_amount), 0) FROM invoices WHERE invoices.project_code = projects.project_code),
  outstanding_usd = (SELECT COALESCE(SUM(invoice_amount - COALESCE(payment_amount, 0)), 0) FROM invoices WHERE invoices.project_code = projects.project_code)
WHERE is_active_project = 1;
```

### Problem 2: Garbage Payment Dates (FIXED ✓)
**Issue**: 2 invoices had future dates
- I24-017: payment_date = 2028-03-01 (should be 2024-03-01)
- I25-066: payment_date = 2057-10-22 (should be 2025-10-22)

**Fix Applied**:
```sql
UPDATE invoices SET payment_date = '2024-03-01' WHERE invoice_id = 252554;
UPDATE invoices SET payment_date = '2025-10-22' WHERE invoice_id = 252613;
```

### Problem 3: Wrong Page for Dashboard (PARTIALLY FIXED)
**Issue**: Built financial dashboard on Overview page when user wanted it on Projects page
**What's wrong**:
- Overview page (`/app/(dashboard)/page.tsx`) has 6 metrics + 4 widgets
- Projects page has blank/useless top widgets
**What's needed**:
- Overview: Keep simple with just 6 metric cards
- Projects: Replace top 4 cards with the 4 insight widgets:
  1. Recent Payments (last 5)
  2. Projects by Outstanding (top 5)
  3. Oldest Unpaid Invoices (top 5 by days outstanding)
  4. Projects by Remaining Value (top 5)

---

## Backend APIs (ALL WORKING ✓)

### Database: `~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db`

### Verified Working Endpoints:
```bash
# All return real data after fixes
GET /api/finance/dashboard-metrics
GET /api/finance/recent-payments
GET /api/finance/projects-by-outstanding
GET /api/finance/oldest-unpaid-invoices
GET /api/finance/projects-by-remaining
GET /api/projects/active
GET /api/invoices/by-project/{project_code}
GET /api/projects/{project_code}/fee-breakdown
```

### Example Data Verification (Qinhu - 24 BK-029):
```
Contract: $3,250,000
Invoiced: $893,750
Paid: $243,750
Outstanding: $650,000
Remaining: $2,356,250

Breakdown:
- Mobilization: 3 invoices, $487,500 invoiced, $243,750 paid, $243,750 outstanding
- Concept Design: 3 invoices, $406,250 invoiced, $0 paid, $406,250 outstanding
```

---

## Files That Need Changes

### 1. `frontend/src/app/(dashboard)/projects/page.tsx` (MAJOR REBUILD)

**Current structure (Lines 155-191 - Top Summary Cards):**
```tsx
<SummaryCard icon={<FileText />} label="Active Projects" value={totalActiveProjects} />
<SummaryCard icon={<DollarSign />} label="Outstanding Invoices" value={formatCurrency(totalOutstandingAmount)} />
<SummaryCard icon={<Calendar />} label="Upcoming Deadlines" value={upcomingDeadlinesCount} />
<SummaryCard icon={<MessageSquare />} label="Unanswered RFIs" value={unansweredRfisCount} />
```

**Replace with 4 insight widgets (similar to financial-dashboard.tsx):**
```tsx
// Import from financial-dashboard.tsx or recreate here
<RecentPaymentsWidget />
<ProjectsByOutstandingWidget />
<OldestUnpaidInvoicesWidget />
<ProjectsByRemainingWidget />
```

**Current table structure (Lines 372-426 - ProjectRow component starts line 432):**
```tsx
{activeProjects.map((project) => (
  <ProjectRow
    project={project}
    isExpanded={expandedProjects.has(project.project_code)}
    expandedDisciplines={expandedDisciplines}
    onToggle={() => toggleProject(project.project_code)}
    onToggleDiscipline={(discipline) => toggleDiscipline(project.project_code, discipline)}
  />
))}
```

**Current ProjectRow logic (Lines 432-878):**
1. Shows project-level summary (Total Fee, Outstanding, Remaining)
2. When expanded, shows:
   - Groups invoices by discipline (Architecture, Interior, Landscape)
   - For each discipline: shows total invoiced, paid, outstanding
   - Expands to show phases within discipline
   - Expands to show individual invoices

**PROBLEM**: Structure is correct but presentation is wrong!

**What needs to change:**
- When project expands, show **DISCIPLINE ROWS FIRST** with prominent styling
- Each discipline row should show:
  - Discipline name (Architecture/Interior/Landscape)
  - Contract fee for discipline (from fee_breakdowns)
  - **3-column summary**: TOTAL PAID | TOTAL OUTSTANDING | TOTAL REMAINING
- When discipline expands, show **PHASE ROWS**
  - Phase name + fee amount
  - If multiple invoices for same phase with different amounts, show as "Phase (50%)" format
- When phase expands, show **INVOICE DETAIL ROWS**
  - Table-style row with columns: Invoice #, Invoice Date, Payment Amount, Payment Date, Outstanding Amount

### 2. `frontend/src/app/(dashboard)/page.tsx` (SIMPLIFY)

**Current (Lines 1-20):**
```tsx
import FinancialDashboard from "@/components/dashboard/financial-dashboard";

export default function Page() {
  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight">Financial Overview</h1>
        <p className="text-slate-600 mt-1">
          Real-time financial metrics and project status across all active contracts
        </p>
      </div>
      <FinancialDashboard />
    </div>
  );
}
```

**Change to:**
- Remove `<FinancialDashboard />` (or keep ONLY the 6 metric cards, remove 4 widgets)
- Keep it simple - just show high-level financial metrics

---

## Implementation Plan

### Phase 1: Fix Top Widgets on Projects Page
- [ ] Replace 4 useless summary cards with insight widgets
- [ ] Import or recreate widget components from financial-dashboard.tsx
- [ ] Test each widget loads real data:
  - Recent Payments: Should show 5 payments with dates
  - Projects by Outstanding: Should show top 5 (Dang Thai Mai $1.4M, Qinhu $650K, etc.)
  - Oldest Unpaid: Should show 926 days outstanding invoices
  - Projects by Remaining: Should show 30 Residence Villas $3.95M, etc.

### Phase 2: Restructure Project Table Hierarchy
- [ ] Update ProjectRow component to show discipline-level summary FIRST when expanded
- [ ] Style discipline row prominently with 3-column layout:
  ```
  [Discipline Name - $XXX contract] | [PAID: $XXX] | [OUTSTANDING: $XXX] | [REMAINING: $XXX]
  ```
- [ ] Make discipline row expandable to show phases

### Phase 3: Fix Phase Display
- [ ] Group phases properly (handle partial invoicing)
- [ ] Display phase name + fee amount
- [ ] For partials, show "Phase Name (50%) - $amount"
- [ ] Make phase row expandable to show invoices

### Phase 4: Fix Invoice Detail Rows
- [ ] When phase expanded, show individual invoice rows
- [ ] Column layout:
  ```
  [Invoice #] | [Invoice Date] | [Payment Amount] | [Payment Date] | [Outstanding Amount]
  ```
- [ ] Use actual data fields:
  - `invoice.invoice_number`
  - `invoice.invoice_date`
  - `invoice.payment_amount`
  - `invoice.payment_date`
  - `(invoice.invoice_amount - invoice.payment_amount)` for outstanding

### Phase 5: Testing & Verification
- [ ] Pick 3 test projects with different characteristics:
  - Qinhu (24 BK-029): Has partials, mix of paid/unpaid
  - Dang Thai Mai (24 BK-074): High outstanding
  - One with full payment history
- [ ] For each project, manually verify:
  - Discipline totals match database queries
  - Phase fees match `project_fee_breakdown` table
  - Invoice details match `invoices` table
  - All calculations (paid, outstanding, remaining) are correct
- [ ] Check widget data matches:
  - Recent Payments: Verify dates are correct (not 2057!)
  - Outstanding amounts: Verify $650K for Qinhu (not $893K)
  - Oldest unpaid: Verify days calculation correct
  - Remaining values: Verify uninvoiced amounts correct

---

## Known Issues to Watch For

1. **Partial invoicing**: Some phases have multiple invoices at different percentages (e.g., 50% + 50%)
   - Need to identify and display as separate rows: "Concept Design (50%)" twice
   - Both should link to different invoice records

2. **Discipline normalization**: The code normalizes discipline names:
   - "Architectural" → "Architecture"
   - "Interior Design" → "Interior"
   - "Landscape Architecture" → "Landscape"
   - Make sure this still works with new structure

3. **Fee breakdown source**: Contract fees come from `project_fee_breakdown` table
   - If missing, falls back to `project.total_fee_usd`
   - Make sure both work correctly

4. **Invoice status field**: Still broken in database (all "outstanding" even when paid)
   - DO NOT rely on `status` field
   - Use `payment_amount > 0` to determine if paid
   - Use `invoice_amount - payment_amount` for outstanding

5. **Payment date sorting**: After fixing bad dates, verify sorting works:
   - Should order by `payment_date DESC`
   - Latest payments should appear first

---

## Testing Commands

### Verify database data:
```bash
# Check Qinhu totals
sqlite3 ~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db \
  "SELECT * FROM v_project_financial_summary WHERE project_code = '24 BK-029';"

# Check invoice detail
sqlite3 ~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db \
  "SELECT invoice_number, phase, discipline, invoice_amount, payment_amount,
   (invoice_amount - COALESCE(payment_amount, 0)) as outstanding
   FROM invoices WHERE project_code = '24 BK-029' ORDER BY phase, discipline;"

# Check recent payments
sqlite3 ~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db \
  "SELECT invoice_number, payment_date, payment_amount FROM invoices
   WHERE payment_amount > 0 ORDER BY payment_date DESC LIMIT 10;"
```

### Test API endpoints:
```bash
# Dashboard metrics (should show $64M contract, $25M invoiced, $21M paid, $3.4M outstanding)
curl http://localhost:8000/api/finance/dashboard-metrics | python3 -m json.tool

# Recent payments (should NOT have 2057 or 2028 dates)
curl http://localhost:8000/api/finance/recent-payments | python3 -m json.tool

# Qinhu outstanding (should show $650K, not $893K)
curl http://localhost:8000/api/finance/projects-by-outstanding | python3 -m json.tool
```

### Frontend URLs:
- Overview Dashboard: http://localhost:3002
- Projects Page: http://localhost:3002/projects

---

## Success Criteria

Before marking complete, verify:
1. [ ] Projects page top shows 4 working insight widgets with real data
2. [ ] Clicking a project expands to show disciplines first
3. [ ] Each discipline shows contract fee + 3-column summary (PAID | OUTSTANDING | REMAINING)
4. [ ] Clicking discipline expands to show phases with fees
5. [ ] Phases with partial invoicing show correctly (e.g., "Concept Design (50%)")
6. [ ] Clicking phase expands to show invoice rows with all 5 columns
7. [ ] All numbers match database (spot check 3 projects)
8. [ ] No broken calculations, no $0 where there should be real numbers
9. [ ] Payment dates are correct (no 2057, 2028 garbage dates)
10. [ ] Overview page is simple (just 6 metrics, not cluttered)

---

## User's Emphasis

"**i dont want to see something that is wrong... you need to check and re check everything and figure out why something isn't working whats breaking and then fix and debug shit adjust database adjust structure etc. to make this function**"

This means:
- DO NOT say something works until you've TESTED it
- DO NOT assume calculations are correct - VERIFY against database
- DO NOT mark complete until you've checked multiple projects
- IF something is broken, DEBUG IT, don't just move on
- ADJUST database, structure, queries as needed to make it work

---

## Next Session TODO

1. Start fresh session with full context
2. Read this document
3. Rebuild Projects page with correct structure
4. Test thoroughly with multiple projects
5. Fix any issues found during testing
6. Only mark complete when user confirms it works

END OF HANDOFF DOCUMENT
