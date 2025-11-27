# Agent 2: Active Projects & Invoice Linking Fixes

## Your Mission
You are responsible for fixing the invoice linking system, breakdown calculations, and active projects display.

## Context
- **Codebase**: Bensley Design Studio Operations Platform
- **Backend**: FastAPI (Python) at `backend/api/main.py`
- **Frontend**: Next.js 15 at `frontend/src/`
- **Database**: SQLite at `database/bensley_master.db`

## Current State & Problems

### CRITICAL BUG: 0% Invoiced Everywhere
**File**: `backend/api/main.py` lines 5726-5727
**The Bug**:
```python
# HARDCODED TO ZERO!
0.0 as paid_to_date_usd,
p.total_fee_usd as outstanding_usd
```

**Result**: All active projects show 0% invoiced, $0 paid, even though we just achieved 100% invoice-to-breakdown linking (253/253 invoices).

### Problem 1: Breakdown Totals Not Updating
**Issue**: When invoices are linked to breakdown_id, the `project_fee_breakdown` table totals don't update automatically.

**Current Schema**:
```sql
CREATE TABLE project_fee_breakdown (
    breakdown_id TEXT PRIMARY KEY,
    project_code TEXT NOT NULL,
    phase TEXT NOT NULL,
    phase_fee_usd REAL,
    total_invoiced REAL DEFAULT 0,      -- ❌ ALL ARE 0
    percentage_invoiced REAL DEFAULT 0,  -- ❌ ALL ARE 0
    total_paid REAL DEFAULT 0,          -- ❌ ALL ARE 0
    percentage_paid REAL DEFAULT 0,     -- ❌ ALL ARE 0
    ...
)
```

**Invoices Schema**:
```sql
CREATE TABLE invoices (
    invoice_id INTEGER PRIMARY KEY,
    project_id INTEGER,
    breakdown_id TEXT,  -- ✅ 253/253 invoices now have this
    invoice_amount REAL,
    payment_amount REAL,
    status TEXT,
    ...
)
```

### Problem 2: Wrong Invoice Display Structure
**Issue**: Invoices show in flat list instead of grouped by phase

**Current**: All invoices listed under project
**Expected**:
```
Project XYZ
├─ Architectural
│  ├─ Mobilization
│  │  └─ Invoice I24-001 ($50k)
│  ├─ Concept Design
│  │  └─ Invoice I24-015 ($100k)
│  ├─ Design Development
│  │  └─ Invoice I24-030 ($150k)
│  └─ Construction Documents
│     └─ Invoice I24-050 ($200k)
```

### Problem 3: Display Issues
- Shows project codes instead of project names
- Invoice numbers too large in display
- No color coding for invoicing progress

## Your Tasks

### Task 1: Fix CRITICAL BUG (0% Invoiced)
1. Open `backend/api/main.py` line 5708 (`/api/projects/active` endpoint)
2. Remove hardcoded `0.0 as paid_to_date_usd`
3. Calculate actual paid/invoiced from invoices table:
```python
SELECT
    p.project_id,
    p.project_code,
    p.project_title,  -- ✅ Use this instead of code
    p.total_fee_usd,
    COALESCE(SUM(i.invoice_amount), 0) as total_invoiced,
    COALESCE(SUM(i.payment_amount), 0) as paid_to_date_usd,
    (p.total_fee_usd - COALESCE(SUM(i.payment_amount), 0)) as outstanding_usd,
    (COALESCE(SUM(i.invoice_amount), 0) / p.total_fee_usd * 100) as percentage_invoiced
FROM projects p
LEFT JOIN invoices i ON p.project_id = i.project_id
WHERE p.is_active_project = 1
GROUP BY p.project_id
```

4. Test with active projects

### Task 2: Create Breakdown Sync Mechanism
1. Create script `sync_breakdown_totals.py`:
   - For each breakdown_id, SUM invoice_amount and payment_amount
   - Update project_fee_breakdown.total_invoiced, total_paid
   - Calculate percentage_invoiced, percentage_paid
2. Run on all 253 invoices
3. Verify totals match

4. Add database trigger (or service method) to auto-update:
```sql
CREATE TRIGGER update_breakdown_totals
AFTER INSERT OR UPDATE ON invoices
WHEN NEW.breakdown_id IS NOT NULL
BEGIN
    UPDATE project_fee_breakdown
    SET
        total_invoiced = (SELECT COALESCE(SUM(invoice_amount), 0) FROM invoices WHERE breakdown_id = NEW.breakdown_id),
        total_paid = (SELECT COALESCE(SUM(payment_amount), 0) FROM invoices WHERE breakdown_id = NEW.breakdown_id),
        percentage_invoiced = (total_invoiced / phase_fee_usd * 100),
        percentage_paid = (total_paid / phase_fee_usd * 100)
    WHERE breakdown_id = NEW.breakdown_id;
END;
```

### Task 3: Fix Invoice Dropdown Structure
1. Edit `frontend/src/components/dashboard/active-projects-tab.tsx`
2. Restructure data to group by:
   - Discipline (Architectural, Landscape, Interior)
   - Phase (in ORDER: Mobilization → Concept Design → Design Development → Construction Documents → Construction Observation)
   - Invoices under each phase
3. Show totals at phase level:
   - Phase fee
   - Total invoiced
   - Percentage invoiced (with progress bar)
   - Invoices remaining
4. Add color coding:
   - Red: <50% invoiced
   - Yellow: 50-80% invoiced
   - Green: >80% invoiced

### Task 4: Fix Display Issues
1. Show project_title instead of project_code everywhere
2. Reduce invoice_number font size
3. Add project name to all invoice displays
4. Fix column widths

### Task 5: Update Financial Service
1. Edit `backend/services/financial_service.py`
2. Update these methods:
   - `get_project_financial_detail()` - use actual invoice data
   - `get_project_hierarchy()` - group by discipline/phase/scope
3. Test calculations

### Task 6: Verify Database Links
1. Run query to verify all 253 invoices have valid breakdown_id
2. Check for orphaned breakdown_ids (exist in invoices but not in project_fee_breakdown)
3. Fix any broken links

## Expected Deliverables

1. **Fixed API endpoint** showing correct invoiced percentages
2. **sync_breakdown_totals.py script** with auto-update trigger
3. **Updated active-projects-tab.tsx** with hierarchical invoice display
4. **Fixed financial_service.py** calculations
5. **Database integrity report** showing all links valid
6. **Color-coded UI** showing invoicing progress

## Success Criteria

- ✅ Active projects show correct % invoiced (not 0%)
- ✅ Project names displayed instead of codes
- ✅ Invoices grouped by phase in correct order
- ✅ Color coding shows invoicing progress
- ✅ Breakdown totals auto-update when invoices added
- ✅ All 253 invoices linked to valid breakdowns

## Testing Checklist

- [ ] View active projects dashboard - see real percentages
- [ ] Expand project - see invoices grouped by phase
- [ ] Check "Wynn Marjan" (22 BK-095) - should show 100% invoiced
- [ ] Check "Capella Ubud" (24 BK-021) - should show partial invoicing
- [ ] Add new invoice - verify breakdown totals update automatically

## Notes
- We just achieved 100% invoice linking (253/253 invoices)
- Coordinate with Agent 3 for dashboard widget fixes
- Test thoroughly - this is critical for financial tracking
