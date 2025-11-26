# URGENT FIXES - Bill's Testing Feedback

**Created:** November 25, 2025
**Priority:** BLOCKING - Fix before next Bill demo
**Time Estimate:** 4-6 hours total

---

## 🚨 CRITICAL BUGS (Must Fix Immediately)

### 1. KPI Values Wrong ❌
**Problem:**
- Active Proposals shows: 0 (wrong)
- Outstanding Invoices shows: $0 (wrong, should be $4.87M)

**Who:** Claude 5 (Dashboard) + Backend
**Time:** 30 min
**Status:** ⏳ URGENT

---

### 2. Proposal Status Update Broken ❌
**Problem:**
- Error: "no such column updated_BY" when saving proposal status
- Typo: Should be `updated_by` (lowercase) not `updated_BY`

**Database Check:** ✅ Column exists as `updated_by`
**Who:** Claude 4 (Proposals)
**Time:** 15 min
**Status:** ⏳ URGENT

---

### 3. Project Names Not Showing ❌
**Problem:**
- Proposals table: "Project Name" column empty
- Recently Paid: Shows "Unknown Project"
- Top 5 Contracts: Only shows code, not name

**Who:** Claude 4 (Proposals) + Claude 3 (Projects)
**Time:** 30 min
**Status:** ⏳ URGENT

---

### 4. Email Category Corrections Page "looks really, really bad" ❌
**Problems:**
- Only shows "general" category (should show all 9)
- Notes field "super tiny"
- Email titles overflow/"formatting is ass"
- No email preview
- Can't open emails

**Who:** Claude 1 (Emails)
**Time:** 2 hours
**Status:** ⏳ URGENT

---

## 📊 DATABASE VERIFICATION

### Proposals Table
```sql
-- ✅ updated_by column EXISTS (lowercase)
CREATE TABLE proposals (
    ...
    updated_by TEXT,
    ...
)
```

**Fix:** Change frontend/backend from `updated_BY` → `updated_by`

### Project Fee Breakdown
```sql
-- ✅ Table EXISTS as project_fee_breakdown
-- ✅ Has 372 rows across 35 projects
CREATE TABLE project_fee_breakdown (
    project_code TEXT,
    discipline TEXT,  -- Landscape, Interior, Architecture
    phase TEXT,       -- mobilization, concept, schematic, dd, cd, ca
    phase_fee_usd REAL,
    invoice_id TEXT,
    ...
)
```

**Ready for:** Hierarchical breakdown implementation

---

## 🎯 PRIORITY MATRIX

### URGENT (Today - Blocking)
1. ✅ Fix KPI calculations (Claude 5 + Backend)
2. ✅ Fix proposal status update (Claude 4)
3. ✅ Fix project names (Claude 4 + Claude 3)
4. ✅ Fix email corrections page (Claude 1)

### HIGH (This Week - Core Functionality)
5. ⏳ Implement hierarchical project breakdown (Claude 3)
6. ⏳ Restructure KPIs (Claude 5 + Backend)
7. ⏳ Fix recent emails widget (Claude 1)

### MEDIUM (Next Sprint - UX)
8. ⏳ Add trend indicators (+8.2%)
9. ⏳ Add project/invoice toggle
10. ⏳ Make proposal numbers bigger
11. ⏳ Over-time aging tracking

---

## 📋 DETAILED FIX INSTRUCTIONS

### Fix #1: KPI Calculations (Claude 5 + Backend)

**Backend:** Add proper KPI endpoint
```python
@app.get("/api/dashboard/kpis")
def get_dashboard_kpis():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Active Proposals (NOT 0!)
    cursor.execute("""
        SELECT COUNT(*) FROM proposals
        WHERE status IN ('active', 'sent', 'follow_up', 'drafting')
    """)
    active_proposals = cursor.fetchone()[0]

    # Outstanding Invoices (NOT $0!)
    cursor.execute("""
        SELECT SUM(CAST(invoice_amount AS REAL))
        FROM invoices
        WHERE paid_date IS NULL OR paid_date = ''
    """)
    outstanding = cursor.fetchone()[0] or 0

    # ... other KPIs

    return {
        "active_proposals": active_proposals,
        "outstanding_invoices": round(outstanding, 2),
        ...
    }
```

**Frontend:** Use API instead of hardcoded
```typescript
const { data: kpis } = useQuery(
  ['dashboard-kpis'],
  () => api.get('/api/dashboard/kpis')
)
```

---

### Fix #2: Proposal Status Update (Claude 4)

**Find and fix:** Search for `updated_BY` and change to `updated_by`

**Likely location:** `backend/services/proposal_tracker_service.py`

```python
# WRONG:
cursor.execute("""
    UPDATE proposals SET status = ?, updated_BY = ?  -- WRONG CASE
    WHERE project_code = ?
""", (status, user_id, code))

# CORRECT:
cursor.execute("""
    UPDATE proposals SET status = ?, updated_by = ?  -- correct lowercase
    WHERE project_code = ?
""", (status, user_id, code))
```

---

### Fix #3: Project Names (Claude 4 + Claude 3)

**Problem:** API returns `project_code` but not `project_name`

**Backend Fix:** Add JOIN to get project name

```python
# proposals endpoint
cursor.execute("""
    SELECT
        p.*,
        proj.name as project_name  -- ADD THIS
    FROM proposals p
    LEFT JOIN projects proj ON p.project_code = proj.code
""")
```

**Frontend Fix:** Display name
```typescript
<TableCell>{proposal.project_name || proposal.project_code}</TableCell>
```

---

### Fix #4: Email Corrections Page (Claude 1)

**Issues to fix:**
1. Category dropdown only shows "general"
2. Notes field too small
3. Email titles overflow
4. No preview modal

**Quick Fixes:**

```typescript
// 1. Fix categories
const CATEGORIES = [
  'contract', 'invoice', 'proposal', 'design_document',
  'correspondence', 'internal', 'financial', 'rfi', 'presentation'
]

// 2. Fix notes field
<Textarea className="min-h-[120px]" />  // Was too small

// 3. Fix title overflow
<div className="truncate max-w-md">{email.subject}</div>

// 4. Add preview
<Button onClick={() => setPreviewEmail(email)}>Preview</Button>
<EmailPreviewModal email={previewEmail} />
```

---

## 🎯 BILL'S FEEDBACK HIGHLIGHTS

### What Bill LOVES ⭐
- Trend indicators (+8.2%) - "quite good"
- Invoice aging color coding - "fucking sick"
- Data validation page - "looks fucking fantastic"
- Overall design - "Super cool. Super clean. Nice."

### What Bill HATES ❌
- Email corrections page - "looks really, really bad"
- Wrong data (0s everywhere) - Breaks trust
- Missing project names - Makes dashboard unusable
- "ass" formatting - Unprofessional

---

## 📁 FILES CREATED

1. **BILL_FEEDBACK_NOVEMBER_25.md** (28KB) - Complete feedback documentation
2. **THIS FILE** - Urgent fixes summary

---

## ⏱️ TIME ESTIMATES

| Fix | Owner | Time | Difficulty |
|-----|-------|------|------------|
| KPI calculations | Claude 5 + Backend | 30min | Easy |
| Status update bug | Claude 4 | 15min | Trivial |
| Project names | Claude 4 | 30min | Easy |
| Email corrections | Claude 1 | 2h | Medium |
| **TOTAL URGENT** | | **3-4h** | |

---

## 🚀 ACTION PLAN

### Step 1: Send prompts to Claudes (5 min)
- Claude 5: Fix KPI calculations
- Claude 4: Fix status bug + project names
- Claude 1: Fix email corrections page

### Step 2: Backend KPI endpoint (30 min)
- Add `/api/dashboard/kpis` with real calculations
- Test: `curl http://localhost:8000/api/dashboard/kpis`

### Step 3: Test fixes (30 min)
- Verify KPIs show real numbers
- Test proposal status update works
- Check project names appear
- Verify email corrections page usable

### Step 4: Demo to Bill (when ready)
- Show fixed KPIs
- Show working proposal updates
- Show proper project names
- (Email page might still need polish)

---

**Next File:** Individual prompts for each Claude →
