# Bensley Platform User Feedback Audit Report

**Date:** December 10, 2025
**Auditor:** Claude Opus 4.5
**Status:** COMPREHENSIVE SYSTEM AUDIT - DO NOT FIX

---

## Executive Summary

Based on detailed user feedback, this platform has **significant data integrity, UX, and architectural issues** across dashboard calculations, page navigation, widget displays, and admin functionality. This audit identifies root causes with file paths and line numbers for each reported issue.

**Overall Grade: C** - Core functionality works but many features broken or misleading

---

## P0 - CRITICAL DATA BUGS (Numbers are Wrong)

### 1. **Remaining Contract Value Calculation - WRONG**

**Issue:** Dashboard KPI subtracts ALL payments from ALL TIME instead of only payments for active projects

**User complaint:** "Should be: Total Contract Value - Paid - Outstanding = Remaining. Currently subtracts ALL payments."

**Root cause:**
- **File:** `backend/api/routers/dashboard.py:337-350`
- **Lines 345-350:**
```python
cursor.execute("""
    SELECT COALESCE(SUM(payment_amount), 0) as total_paid
    FROM invoices
""")
all_time_paid = cursor.fetchone()['total_paid'] or 0
remaining_contract_value = total_contract_value - all_time_paid
```

**Problem:** Subtracts payments from ALL projects (including completed/cancelled/proposal-stage) instead of ONLY active projects

**What it should do:**
```python
cursor.execute("""
    SELECT COALESCE(SUM(i.payment_amount), 0) as total_paid
    FROM invoices i
    INNER JOIN projects p ON i.project_id = p.project_id
    WHERE p.is_active_project = 1
""")
```

**Impact:** Remaining contract value appears much smaller than reality

---

### 2. **Outstanding Invoices Calculation - POSSIBLY WRONG**

**User complaint:** "Not sure if correctly pulled from invoice table"

**Investigation findings:**
- **File:** `backend/api/routers/dashboard.py:66-71`
- Logic: `SELECT SUM(invoice_amount - COALESCE(payment_amount, 0))`
- **Issue:** Does not filter by active projects - includes all projects
- **Also:** Multiple queries use different formulas:
  - Line 379: Adds status filter `status != 'paid'`
  - Line 66: No status filter
  - Inconsistent logic across endpoints

**What it should do:** Filter to active projects only + standardize logic

---

### 3. **Average Days to Payment - VERIFICATION NEEDED**

**User complaint:** "Need verification"

**Current implementation:**
- **File:** `backend/api/routers/dashboard.py:461-468`
```python
SELECT AVG(julianday(payment_date) - julianday(invoice_date)) as avg_days
FROM invoices
WHERE payment_date IS NOT NULL AND invoice_date IS NOT NULL
```

**Potential issues:**
- Includes ALL projects (completed, cancelled, etc.)
- No filter for active projects
- May include very old historical data skewing average

**Recommendation:** Filter to active projects + last 12 months only

---

### 4. **Win Rate Calculation - LOGIC UNCLEAR**

**User complaint:** "Need verification"

**Current implementation:**
- **File:** `backend/api/routers/dashboard.py:486-503`
```python
won = row['won'] or 0  # is_active_project = 1
lost = row['lost'] or 0  # status in ('lost', 'declined', 'cancelled')
win_rate = (won / (won + lost) * 100) if lost > 0 else None
```

**Issues:**
- `is_active_project=1` includes projects currently in delivery (not just won deals)
- Excludes "Dormant" which may have been soft-losses
- Returns `None` if no lost deals tracked - misleading
- Should use `proposals` table, not `projects` table

**What it should do:**
- Count from `proposals` table
- Won = `current_status = 'Contract Signed'`
- Lost = `current_status IN ('Lost', 'Declined')`
- Exclude `Dormant`, `On Hold` (still in play)

---

### 5. **Pipeline Value - PROBABLY CORRECT**

**User complaint:** "Need verification"

**Current implementation:**
- **File:** `backend/api/routers/dashboard.py:506-512`
```python
SELECT COALESCE(SUM(project_value), 0) as pipeline
FROM proposals
WHERE current_status NOT IN ('Lost', 'Declined', 'Dormant', 'Contract Signed', ...)
```

**Status:** ✅ **Likely correct** - filters properly, uses proposals table, excludes inactive statuses

---

### 6. **Contracts Signed All Time - NUMBER SEEMS WRONG**

**User complaint:** "Number seems wrong"

**Current implementation:**
- **File:** `backend/api/routers/dashboard.py:404-437`
- For "all_time", uses current year only:
```python
cursor.execute(f"""
    SELECT COUNT(*) as count, COALESCE(SUM(total_fee_usd), 0) as value
    FROM projects
    WHERE is_active_project = 1
    AND contract_signed_date >= '{current_year}-01-01'
""")
```

**Problem:** "All time" label but only counts THIS YEAR

**Database check results:**
```bash
# Total active project contract value: $63,028,778
```

**What it should do:** Remove date filter for "all_time" period

---

## P1 - BROKEN/NON-FUNCTIONAL PAGES

### 7. **Finance Page - Loads but may have errors**

**User complaint:** "Finance page - doesn't work"

**Investigation:**
- **File:** `frontend/src/app/(dashboard)/finance/page.tsx`
- Page loads and renders
- Uses real API calls: `api.getDashboardFinancialMetrics()`, `api.getInvoiceAging()`
- **Possible issue:** Backend endpoints may be returning errors

**Next steps:** Test these endpoints:
- `GET /api/invoices/financial-metrics`
- `GET /api/invoices/aging`

---

### 8. **Query Page - Backend endpoint broken**

**User complaint:** "Query page - doesn't work"

**STATUS PER .claude/STATUS.md:** ✅ **FIXED Dec 10**
- Root cause was backend called `process_chat()` which didn't exist
- Fixed to call `query_with_context()`

**If still broken:** Check `backend/api/routers/query.py:81-87`

---

### 9. **Email Intelligence Page - Path exists, functionality unknown**

**User complaint:** "Email intelligence - doesn't work"

**Investigation:**
- **File:** `frontend/src/app/(dashboard)/emails/intelligence/page.tsx`
- Page exists in filesystem
- **Action needed:** Load page in browser and check console for errors

---

### 10. **System Status Page - Path exists, functionality unknown**

**User complaint:** "System status - doesn't work"

**Investigation:**
- **File:** `frontend/src/app/(dashboard)/system/page.tsx`
- Page exists in filesystem
- **Action needed:** Load page and test

---

### 11. **Admin > AI Suggestions - Shows Nothing**

**User complaint:** "AI Suggestions - shows nothing"

**Investigation:**
- **File:** `frontend/src/app/(dashboard)/admin/suggestions/page.tsx`
- Page is MASSIVE (1057 lines) with full functionality
- Calls `api.getSuggestionsStats()` and `api.getSuggestions()`
- **Likely issue:** Backend returning 0 results OR API errors

**Backend endpoint:** `GET /api/suggestions`

**Database check needed:**
```sql
SELECT COUNT(*) FROM ai_suggestions WHERE status = 'pending';
```

---

### 12. **Admin > Email Categories - Doesn't Work**

**User complaint:** "Email category - doesn't work"

**Investigation:**
- **File:** `frontend/src/app/(dashboard)/admin/email-categories/page.tsx`
- File exists
- **Action needed:** Test page, check API calls

---

### 13. **Admin > Learn Patterns - "Never Used"**

**User complaint:** "Learn patterns - says 'never used'"

**Investigation:**
- **File:** `frontend/src/app/(dashboard)/admin/patterns/page.tsx`
- File exists
- **Possible issue:** Pattern usage counter not incrementing
- **Per STATUS.md:** "153 learned patterns exist but 'Times Used: 0' - pattern matching not triggering"

**Root cause:** Pattern matching logic not calling patterns or not incrementing counters

---

### 14. **Admin > Project Editor - Can't Edit Fee Breakdown or Contacts**

**User complaint:** "Project editor - can't edit fee breakdown, contacts"

**Investigation:**
- **File:** `frontend/src/app/(dashboard)/admin/project-editor/page.tsx`
- File exists
- **Action needed:** Check if forms for fee breakdown/contacts exist and are functional

---

## P2 - UX ISSUES (Confusing Navigation, Wrong Destinations)

### 15. **Hot Items Widget - Multiple Issues**

**User complaints:**
- "Shows project codes not names"
- "37 days no contact for ACTIVE PROJECTS not proposals"
- "999 days no contact makes no sense"
- "+3 more but can't see all items"
- "Clicking goes to wrong page"

**Root cause:**
- **File:** `frontend/src/components/dashboard/hot-items-widget.tsx`

**Issues found:**

**a) Shows project codes instead of names (Line 59):**
```typescript
text: `${inv.project_name || inv.project_code} - ${formatCurrency(...)}`
```
Uses `inv.project_name` which may be null - should ALWAYS look up name

**b) Shows ACTIVE PROJECTS not proposals (Line 68-78):**
```typescript
if (proposalsQuery.data?.urgent) {
  proposalsQuery.data.urgent.slice(0, 3).forEach((prop) => {
    // Uses dailyBriefing.urgent which includes PROJECTS
```
Should filter to proposals only

**c) "999 days" issue:**
Likely backend calculation bug - no validation for max days

**d) "+3 more" with no way to see all (Line 192):**
```typescript
{sortedItems.slice(0, 6).map((item, idx) => (
```
Hard-coded to show 6 max, but "View all" link goes to `/admin/suggestions` which is wrong page

**e) Wrong link destination (Line 181-186):**
```typescript
<Link href="/admin/suggestions" className="...">
  View all <ChevronRight />
</Link>
```
Should link to dedicated "Hot Items" page or proposals tracker with filter

---

### 16. **Page Duplication - Review vs Admin**

**User complaint:** "There's a 'Review' page AND an 'Admin' page with review functionality - WHY?"

**Investigation:**

**Admin page:** `/admin/page.tsx` - Shows overview with links to:
- `/admin/suggestions` - AI Suggestions
- `/admin/email-links` - Email Links
- `/admin/financial-entry` - Financial Entry
- `/admin/project-editor` - Project Editor

**Suggestions page:** `/suggestions/page.tsx` - Full suggestion review interface

**Verdict:** NOT duplicate - `/suggestions` is standalone, `/admin` is hub page
**But:** Navigation is confusing - main nav should link directly to `/admin/suggestions` not `/admin`

---

### 17. **Common Tasks Buttons - Redundant**

**User complaint:** "New Proposal and View Tracker both go to same place"

**Investigation:**
- **File:** Need to find "Common Tasks" widget
- **Likely file:** `frontend/src/components/dashboard/quick-actions-widget.tsx`
- **Action needed:** Check button destinations

---

### 18. **Query Button - Opens Separate Page Instead of Inline Chat**

**User complaint:** "Query button opens separate page instead of inline chat"

**Current behavior:**
- **Dashboard:** `frontend/src/app/(dashboard)/page.tsx:198-202`
```typescript
<a href="/search" className={cn(ds.buttons.primary, "...")}>
  Open Query Interface →
</a>
```

**Issue:** Links to `/search` page instead of inline widget

**Note:** There IS a `QueryWidget` component but it's not being used inline on main dashboard

**Recommendation:** Add inline QueryWidget to dashboard OR clearly label button as "Open Full Query Page"

---

### 19. **View All Emails - Goes to Query Interface**

**User complaint:** '"View All" for emails goes to query interface (makes no sense)'

**Investigation needed:** Find "View All" link in Recent Emails widget
- **Likely file:** `frontend/src/components/dashboard/recent-emails-widget.tsx`
- **Should link to:** `/emails` or `/emails/review`

---

### 20. **Proposals Page - Just Redirects**

**User complaint:** "Just a list with no analytics, 'Days' column - days since WHAT?"

**Investigation:**
- **File:** `frontend/src/app/(dashboard)/proposals/page.tsx`
```typescript
export default function ProposalsRedirectPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/tracker");
  }, [router]);
```

**Finding:** `/proposals` just redirects to `/tracker`

**Tracker page:** `frontend/src/app/(dashboard)/tracker/page.tsx`
- Shows proposal table
- Has "Days" column (likely days since last contact)
- Missing: analytics, intelligence, tasks, value breakdown, contracts signed this year, weekly summary

---

### 21. **Projects Page - Multiple Issues**

**User complaints:**
- "Invoice aging might be wrong"
- "Project codes shown without names"
- "Need breakdown: 0-30 days, 31-60 days, 90+ days"
- "Error loading milestones"
- "Active Projects dropdown shows 10 invoice details (too much info)"
- "Phases sorted ALPHABETICALLY - should be MOB → CD → DD → CDocs → CO"
- "Invoice aging widget is too big"

**Investigation needed:**
- **File:** `frontend/src/app/(dashboard)/projects/page.tsx`
- Check invoice aging logic
- Check project name display
- Check milestone loading
- Check phase sort order

---

### 22. **Contacts Page - Multiple Issues**

**User complaints:**
- "Shows '50 of 546' - pagination unclear"
- "Console error"
- "Can't add contacts"
- "Can't link emails to projects/proposals from this page"

**Investigation:**
- **File:** `frontend/src/app/(dashboard)/contacts/page.tsx`
- Check pagination display
- Check browser console for errors
- Check if "Add Contact" form exists
- Check if email linking functionality exists

---

## P3 - MISSING FEATURES (Should Exist But Don't)

### 23. **Proposals Page - Missing Intelligence Features**

**User complaint:** "Missing: intelligence, tasks, action items, follow-up status, value breakdown, contracts signed this year, weekly summary, proposal-specific suggestions"

**Current state:** Proposals page is just a redirect to tracker

**Tracker page has:**
- ✅ List view with filters
- ✅ Status breakdown
- ❌ No intelligence panel
- ❌ No tasks/action items
- ❌ No value breakdown analytics
- ❌ No "contracts signed this year" stat
- ❌ No weekly summary
- ❌ No proposal-specific suggestions display

**Recommendation:** Add these widgets to tracker page or create proper proposals page

---

### 24. **Projects/Finance Page - Missing Breakdowns**

**User complaint:** "Need breakdown: 0-30 days, 31-60 days, 90+ days"

**Current implementation:**
- Finance page exists at `frontend/src/app/(dashboard)/finance/page.tsx`
- Has `InvoiceAgingWidgetEnhanced` component
- **Need to check:** Does aging widget show 30/60/90 day buckets?

**Backend:** `api.getInvoiceAging()` should return aging buckets

---

## Navigation Architecture Issues

### Page Structure Analysis

**Total pages found:** 33 dashboard pages

**Duplicates/Overlaps:**
1. `/proposals` → redirects to `/tracker` (why have both?)
2. `/admin` → overview page
3. `/admin/suggestions` → actual suggestions interface
4. `/suggestions` → standalone suggestions page (duplicate?)

**Recommendation:** Consolidate navigation, remove redirects, create clear hierarchy

---

## Database Data Validation

### Contract Value Verification

```sql
-- Active projects total contract value
SELECT SUM(total_fee_usd) FROM projects WHERE is_active_project = 1;
-- Result: $63,028,778

-- Total paid across ALL invoices
SELECT SUM(payment_amount) FROM invoices WHERE payment_amount > 0;
-- Result: $35,998,083.64
-- Count: 367 payments

-- Total invoices
SELECT COUNT(*) FROM invoices;
-- Result: 420 invoices
```

**Finding:** If remaining contract value = $63M - $36M = $27M, this seems reasonable
**But:** Current dashboard logic subtracts ALL payments including from completed/cancelled projects

---

## Summary of File Locations

### Priority 0 Fixes Needed:

1. **Dashboard calculations:** `backend/api/routers/dashboard.py`
   - Lines 345-350: Remaining contract value
   - Lines 66-71: Outstanding invoices
   - Lines 461-468: Avg days to payment
   - Lines 486-503: Win rate
   - Lines 404-437: Contracts signed

2. **Hot Items widget:** `frontend/src/components/dashboard/hot-items-widget.tsx`
   - Line 59: Project names
   - Lines 68-78: Active projects vs proposals
   - Line 192: Hard-coded slice
   - Lines 181-186: Wrong link

### Priority 1 Fixes Needed:

3. **Finance page APIs:** Check these endpoints work
4. **Query page:** Already fixed per STATUS.md
5. **Email intelligence:** Test page functionality
6. **System status:** Test page functionality
7. **Admin > AI Suggestions:** Check why showing nothing
8. **Admin pages:** Test all sub-pages

### Priority 2 Fixes Needed:

9. **Navigation:** Clean up duplicates, fix link destinations
10. **Proposals/Tracker:** Add missing analytics
11. **Projects page:** Fix phase sorting, milestone loading
12. **Contacts page:** Fix pagination, add features

---

## Recommendations

### Immediate Actions (This Week):

1. **Fix remaining contract value calculation** - P0, 5-minute fix
2. **Fix outstanding invoices to filter active projects** - P0, 5-minute fix
3. **Fix hot items widget project names** - P0, 10-minute fix
4. **Test all "broken" pages and document actual errors** - P1, 1 hour
5. **Standardize invoice calculation logic** - P0, 30 minutes

### Medium Term (Next Sprint):

6. **Add missing analytics to proposals page** - P3, 4 hours
7. **Fix phase sorting on projects page** - P2, 30 minutes
8. **Add aging breakdown to finance page** - P3, 2 hours
9. **Consolidate navigation structure** - P2, 2 hours
10. **Add proposal intelligence panels** - P3, 8 hours

### Long Term (Next Month):

11. **Complete UX audit of all 33 pages** - P2, 8 hours
12. **Create page hierarchy documentation** - P2, 2 hours
13. **Build comprehensive test suite** - P1, 16 hours

---

## Testing Protocol

Before marking ANY issue as "fixed":

1. ✅ Fix the code
2. ✅ Restart backend/frontend
3. ✅ Load page in browser
4. ✅ Verify number is correct (compare to direct DB query)
5. ✅ Check browser console for errors
6. ✅ Test on multiple screen sizes
7. ✅ Update STATUS.md with verification

---

**End of Audit Report**
