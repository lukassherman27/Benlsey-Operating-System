# Bill's Dashboard Feedback - November 25, 2025

**Tester:** Bill Bensley
**Testing Time:** ~30 minutes
**Dashboard URL:** http://localhost:3002
**Overall Assessment:** Good foundation, critical issues with data accuracy and structure

---

## 🚨 CRITICAL ISSUES (BLOCKING)

### 1. **KPI Values Wrong** (Priority: URGENT)
**Problem:**
- Active Proposals shows: **0** (should show actual count)
- Outstanding Invoices shows: **$0** (contradicts widget below showing $4.87M)

**Root Cause:** Backend KPI endpoint not implemented or returning wrong data

**Fix:**
- Implement proper KPI calculations
- Verify database queries

---

### 2. **Proposals Status Update Broken** (Priority: URGENT)
**Problem:**
- When changing proposal status and clicking "Save Changes"
- Error: `no such column updated_BY`

**Root Cause:** Database schema mismatch (column name is `updated_by` not `updated_BY`)

**Fix:**
```sql
-- Check proposals table schema
.schema proposals

-- If column doesn't exist, add it:
ALTER TABLE proposals ADD COLUMN updated_by TEXT DEFAULT 'bill';
ALTER TABLE proposals ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;
```

---

### 3. **Project Names Not Showing** (Priority: URGENT)
**Problem:**
- Multiple locations show project CODE but not project NAME:
  - Proposals tracker: "Project Name" column empty
  - Top 5 contracts: Shows "25-BK-018" but not actual project name
  - Recently paid invoices: Shows "Unknown Project"

**Root Cause:** Frontend not fetching `project_name` or join query missing

**Fix:**
- Check if `projects` table has `project_name` or `name` column
- Update all API endpoints to include project name in responses
- Update frontend to display `project.name` not just `project.code`

---

## 🎯 OVERVIEW DASHBOARD (/  page)

### KPI Cards - Complete Restructure Needed

**Current (Wrong):**
```
[Active Revenue: $X] [Active Projects: 49] [Active Proposals: 0] [Outstanding: $0]
```

**Required (Correct):**
```
[Total Remaining Contract Value] [Active Projects & Proposals] [Total Invoiced (Year)] [Unpaid Invoices]
```

#### NEW KPI #1: Total Remaining Contract Value
**Definition:** All signed contracts minus what's been invoiced
**Formula:**
```sql
SELECT
    SUM(CAST(total_contract_value AS REAL)) -
    SUM(CAST(total_invoiced AS REAL)) AS remaining_value
FROM projects
WHERE status = 'active'
```

**Example:**
- Total contracts: $100M
- Already invoiced: $50M
- **Remaining: $50M** ← This is what we show

#### NEW KPI #2: Active Projects & Proposals
**Option A:** Combined widget showing both counts
```
Active Projects: 49
Active Proposals: 12
```

**Option B:** Separate "Proposals Overview" widget (see below)

#### NEW KPI #3: Total Invoiced (Year)
**Definition:** Total revenue received this year
**Formula:**
```sql
SELECT SUM(CAST(invoice_amount AS REAL))
FROM invoices
WHERE paid_date IS NOT NULL
AND strftime('%Y', paid_date) = strftime('%Y', 'now')
```

**Future:** Add toggle for Quarter/Month

#### NEW KPI #4: Unpaid Invoices
**Definition:** Outstanding invoice amount
**Formula:**
```sql
SELECT SUM(CAST(invoice_amount AS REAL))
FROM invoices
WHERE paid_date IS NULL OR paid_date = ''
```

---

### NEW WIDGET: Proposals Overview

**Replaces or complements "Active Proposals" KPI**

**Content:**
```
Proposals Overview
├── Total Quantity: 87 (for the year)
├── Proposals Sent: 42
├── In Drafting: 18
├── First Contact: 12
└── Needs Follow-up: 15
```

**Backend Query:**
```sql
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
    SUM(CASE WHEN status = 'drafting' THEN 1 ELSE 0 END) as drafting,
    SUM(CASE WHEN status = 'first_contact' THEN 1 ELSE 0 END) as first_contact,
    SUM(CASE WHEN status = 'follow_up' THEN 1 ELSE 0 END) as needs_followup
FROM proposals
WHERE strftime('%Y', created_date) = strftime('%Y', 'now')
```

---

### Recent Emails Widget - BROKEN

**Problem:**
- Shows 3 "super fucking old emails"
- Dates are wrong
- Bill questions: "not really sure why that's on the dashboard"

**Options:**
1. **Fix it:** Show last 10 emails from today/this week sorted by date DESC
2. **Remove it:** If not useful, remove from overview
3. **Replace it:** With something more useful (recent payments, upcoming milestones)

**Fix (if keeping):**
```sql
SELECT * FROM emails
WHERE date_received >= date('now', '-7 days')
ORDER BY date_received DESC
LIMIT 10
```

---

### Trend Analysis - USER LOVES THIS! ⭐

**Quote:** "I really like the little top right of the widget where it has like the +8.2%. Having that kind of trend analysis is quite good."

**Action:** Add trend indicators to ALL widgets where applicable:
- Total Remaining Contract Value: +/- % vs last month
- Unpaid Invoices: +/- % vs last month (red if increasing!)
- Proposals: +/- % vs last month
- Revenue: +/- % vs last quarter

**Formula:**
```python
trend_percent = ((current_value - previous_value) / previous_value) * 100
```

---

## 📊 PROPOSALS PAGE (/tracker)

### Data Issues

#### 1. "Total Proposals" Label Wrong
**Current:** "Total Proposals" (implies active only)
**Required:** "Total Proposals (2025)" or "Total Proposals This Year"
**Value:** Should show 87 (all proposals for the year, not just active)

#### 2. Pipeline Value - Verify Active Only
**Requirement:** Make sure this ONLY includes active proposals, NOT canceled/on-hold

**Query Check:**
```sql
SELECT SUM(CAST(proposal_value AS REAL))
FROM proposals
WHERE status IN ('active', 'sent', 'follow_up', 'drafting', 'first_contact')
AND status NOT IN ('canceled', 'on_hold', 'won', 'lost')
```

#### 3. "Needs Follow-up" - Add Project Names
**Current:** Just shows count
**Improvement:** List project names since there's space

**Example:**
```
Needs Follow-up: 5
• Mumbai Clubhouse
• Tel Aviv High-Rise
• Bali Resort Extension
• ...
```

---

### Proposal Status Widget Improvements

#### Make Numbers BIGGER
**Current:** Small text for values
**Required:**
- Move labels to TOP
- Make NUMBERS much bigger (48px+)
- Make proposal VALUES ($ millions) MUCH bigger

**Before:**
```
Proposal Sent: 15 | $4.2M
```

**After:**
```
PROPOSAL SENT
    15
  $4.2M  ← Much bigger
```

#### Color Coding Updates
**Current:** Has colors for different statuses
**Changes Needed:**
- Change "On Hold" → "Canceled"
- Make "Canceled" **RED** (indicates done/dead)
- Keep other colors as-is

---

### Critical Bugs

#### Bug #1: Project Name Not Showing
**Everywhere in proposals table, project_name column is empty**

**Check:**
1. Does `proposals` table have `project_name` column?
2. Is it populated?
3. Is frontend displaying it?

**Quick Fix:**
```sql
-- If column exists but empty, populate from projects table
UPDATE proposals
SET project_name = (
    SELECT name FROM projects
    WHERE projects.code = proposals.project_code
)
WHERE project_name IS NULL OR project_name = '';
```

#### Bug #2: Status Update Error
**Error:** `no such column updated_BY` (capital BY)

**Fix:** Change query to use `updated_by` (lowercase)

```python
# In proposal_tracker_service.py or wherever update happens
cursor.execute("""
    UPDATE proposals
    SET status = ?, updated_by = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
""", (new_status, user_id, proposal_id))
```

---

### Future Feature Request

**Proposal Document Access:**
- Click on proposal → see latest proposal PDF/document
- Link to actual proposal file
- Integration with `/proposals` folder

**Implementation:** Phase 2 (after current fixes)

---

## 🏗️ ACTIVE PROJECTS PAGE - MAJOR RESTRUCTURE NEEDED

### Current Structure (WRONG - Flat List)
```
Project 25-BK-018
├── Invoice #1 | Date | Amount | Outstanding
├── Invoice #2 | Date | Amount | Outstanding
├── Invoice #3 | Date | Amount | Outstanding
...
```

### Required Structure (Hierarchical - 3 Levels)

```
📁 Project 25-BK-018: Mumbai Clubhouse
   ├── Total Fee: $2,500,000
   ├── Total Invoiced: $1,200,000
   ├── Outstanding: $450,000
   ├── Remaining: $1,300,000
   └── Status: Active

   📂 [DROPDOWN 1] Disciplines
   ├─┬─ Landscape
   │ ├── Total Fee: $800,000
   │ ├── Invoiced: $400,000
   │ ├── Outstanding: $150,000
   │ └── Remaining: $400,000
   │
   │ └─┬─ [DROPDOWN 2] Phases
   │   ├─┬─ Mobilization ($50,000)
   │   │ ├── Invoice #001 | $25,000 | Paid ✓
   │   │ └── Invoice #002 | $25,000 | Paid ✓
   │   │
   │   ├─┬─ Concept Design ($200,000)
   │   │ ├── Invoice #003 | $100,000 | Paid ✓ (50% invoiced)
   │   │ └── [Not yet invoiced] | $100,000 | Pending
   │   │
   │   ├─┬─ Design Development ($250,000)
   │   │ ├── Invoice #004 | $125,000 | Outstanding (30 days)
   │   │ └── [Not yet invoiced] | $125,000 | Pending
   │   │
   │   ├─── Construction Drawings ($250,000) [Not started]
   │   └─── Construction Observation ($50,000) [Not started]
   │
   ├─┬─ Interior
   │ ├── Total Fee: $1,200,000
   │ ├── Invoiced: $600,000
   │ ├── Outstanding: $200,000
   │ └── Remaining: $600,000
   │ └─┬─ [Phases - same structure as above]
   │
   └─┬─ Architecture
     ├── Total Fee: $500,000
     └── [Same structure...]
```

### Data Source

**This data ALREADY EXISTS in database!**

Table: `contract_fee_breakdown`

**Schema (verify):**
```sql
.schema contract_fee_breakdown

-- Expected columns:
-- project_code
-- discipline (Landscape, Interior, Architecture)
-- phase (Mobilization, Concept Design, etc.)
-- phase_fee
-- phase_percentage (optional)
```

### Implementation Requirements

#### Frontend Component Structure
```typescript
<ProjectAccordion project={project}>
  <ProjectSummary
    totalFee={project.total_fee}
    invoiced={project.total_invoiced}
    outstanding={project.outstanding}
    remaining={project.remaining}
  />

  <DisciplineAccordion> {/* 1st level dropdown */}
    {project.disciplines.map(discipline => (
      <DisciplineSection discipline={discipline}>
        <DisciplineSummary {...discipline} />

        <PhaseAccordion> {/* 2nd level dropdown */}
          {discipline.phases.map(phase => (
            <PhaseSection phase={phase}>
              <PhaseSummary fee={phase.fee} />
              <InvoiceList invoices={phase.invoices} />
              {phase.uninvoiced > 0 && (
                <PendingAmount amount={phase.uninvoiced} />
              )}
            </PhaseSection>
          ))}
        </PhaseAccordion>
      </DisciplineSection>
    ))}
  </DisciplineAccordion>
</ProjectAccordion>
```

#### Backend API Needed

**New Endpoint:** `GET /api/projects/{code}/fee-breakdown`

**Response Structure:**
```json
{
  "project_code": "25-BK-018",
  "project_name": "Mumbai Clubhouse",
  "total_fee": 2500000,
  "total_invoiced": 1200000,
  "outstanding": 450000,
  "remaining": 1300000,
  "disciplines": [
    {
      "name": "Landscape",
      "total_fee": 800000,
      "invoiced": 400000,
      "outstanding": 150000,
      "remaining": 400000,
      "phases": [
        {
          "name": "Mobilization",
          "phase_fee": 50000,
          "invoiced": 50000,
          "outstanding": 0,
          "remaining": 0,
          "invoices": [
            {
              "invoice_id": "I24-001",
              "amount": 25000,
              "date_issued": "2024-01-15",
              "paid_date": "2024-02-10",
              "status": "paid"
            },
            {
              "invoice_id": "I24-002",
              "amount": 25000,
              "date_issued": "2024-02-01",
              "paid_date": "2024-03-05",
              "status": "paid"
            }
          ]
        },
        {
          "name": "Concept Design",
          "phase_fee": 200000,
          "invoiced": 100000,
          "outstanding": 0,
          "remaining": 100000,
          "invoices": [
            {
              "invoice_id": "I24-003",
              "amount": 100000,
              "date_issued": "2024-03-01",
              "paid_date": "2024-04-15",
              "status": "paid",
              "note": "50% of phase invoiced"
            }
          ],
          "uninvoiced_amount": 100000
        },
        {
          "name": "Design Development",
          "phase_fee": 250000,
          "invoiced": 125000,
          "outstanding": 125000,
          "remaining": 125000,
          "invoices": [
            {
              "invoice_id": "I24-004",
              "amount": 125000,
              "date_issued": "2024-06-01",
              "paid_date": null,
              "status": "outstanding",
              "days_outstanding": 30
            }
          ],
          "uninvoiced_amount": 125000
        },
        {
          "name": "Construction Drawings",
          "phase_fee": 250000,
          "invoiced": 0,
          "outstanding": 0,
          "remaining": 250000,
          "invoices": [],
          "status": "not_started"
        },
        {
          "name": "Construction Observation",
          "phase_fee": 50000,
          "invoiced": 0,
          "outstanding": 0,
          "remaining": 50000,
          "invoices": [],
          "status": "not_started"
        }
      ]
    },
    {
      "name": "Interior",
      "total_fee": 1200000,
      "phases": [...]
    },
    {
      "name": "Architecture",
      "total_fee": 500000,
      "phases": [...]
    }
  ]
}
```

#### Backend Service Method

```python
# backend/services/financial_service.py or contract_service.py

def get_project_fee_breakdown(self, project_code: str) -> Dict:
    """
    Get hierarchical fee breakdown for project
    Discipline → Phase → Invoices
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get project summary
    cursor.execute("""
        SELECT
            code, name, total_fee, status
        FROM projects
        WHERE code = ?
    """, (project_code,))
    project = cursor.fetchone()

    if not project:
        return None

    # Get fee breakdown by discipline and phase
    cursor.execute("""
        SELECT
            discipline,
            phase_name,
            phase_fee,
            phase_order
        FROM contract_fee_breakdown
        WHERE project_code = ?
        ORDER BY discipline, phase_order
    """, (project_code,))
    breakdown = cursor.fetchall()

    # Get all invoices for this project
    cursor.execute("""
        SELECT
            invoice_id,
            invoice_amount,
            date_issued,
            paid_date,
            phase_name,
            discipline
        FROM invoices
        WHERE project_code = ?
        ORDER BY date_issued
    """, (project_code,))
    invoices = cursor.fetchall()

    conn.close()

    # Build hierarchical structure
    disciplines = {}
    for row in breakdown:
        disc_name = row['discipline']
        if disc_name not in disciplines:
            disciplines[disc_name] = {
                'name': disc_name,
                'total_fee': 0,
                'invoiced': 0,
                'outstanding': 0,
                'remaining': 0,
                'phases': {}
            }

        phase_name = row['phase_name']
        disciplines[disc_name]['phases'][phase_name] = {
            'name': phase_name,
            'phase_fee': row['phase_fee'],
            'invoiced': 0,
            'outstanding': 0,
            'remaining': row['phase_fee'],
            'invoices': []
        }
        disciplines[disc_name]['total_fee'] += row['phase_fee']

    # Attach invoices to phases
    for inv in invoices:
        disc_name = inv['discipline']
        phase_name = inv['phase_name']

        if disc_name in disciplines and phase_name in disciplines[disc_name]['phases']:
            phase = disciplines[disc_name]['phases'][phase_name]
            invoice_data = {
                'invoice_id': inv['invoice_id'],
                'amount': inv['invoice_amount'],
                'date_issued': inv['date_issued'],
                'paid_date': inv['paid_date'],
                'status': 'paid' if inv['paid_date'] else 'outstanding'
            }

            if inv['paid_date']:
                phase['invoiced'] += inv['invoice_amount']
                disciplines[disc_name]['invoiced'] += inv['invoice_amount']
            else:
                phase['outstanding'] += inv['invoice_amount']
                disciplines[disc_name]['outstanding'] += inv['invoice_amount']

            phase['remaining'] = phase['phase_fee'] - phase['invoiced']
            phase['invoices'].append(invoice_data)

    # Calculate discipline totals
    for disc in disciplines.values():
        disc['remaining'] = disc['total_fee'] - disc['invoiced']

    return {
        'project_code': project['code'],
        'project_name': project['name'],
        'total_fee': project['total_fee'],
        'disciplines': list(disciplines.values())
    }
```

---

### Other Active Projects Issues

#### "Unknown Project" in Recently Paid
**Problem:** Last 3 invoices show "Unknown Project"

**Cause:** Invoices not linked to project or join missing

**Fix:**
```sql
-- Check if invoices have project_code
SELECT invoice_id, project_code FROM invoices WHERE paid_date IS NOT NULL ORDER BY paid_date DESC LIMIT 10;

-- If project_code exists but name is missing, update query to join:
SELECT
    i.invoice_id,
    i.invoice_amount,
    i.paid_date,
    p.code as project_code,
    p.name as project_name  -- THIS WAS MISSING
FROM invoices i
LEFT JOIN projects p ON i.project_code = p.code
WHERE i.paid_date IS NOT NULL
ORDER BY i.paid_date DESC
LIMIT 5;
```

#### Toggle: View by Project vs by Invoice
**Feature Request:** Switch between two views

**View 1: By Project** (grouped)
```
Project A
├── Invoice 1
└── Invoice 2

Project B
├── Invoice 3
└── Invoice 4
```

**View 2: By Invoice** (flat list, sorted by date)
```
Invoice 4 | Project B | $50K | 2025-11-20
Invoice 3 | Project B | $30K | 2025-11-15
Invoice 2 | Project A | $40K | 2025-11-10
Invoice 1 | Project A | $60K | 2025-11-05
```

---

### Aging Breakdown - Add "Over Time" Tracking

**Current:** Static snapshot (30 days, 30-90, >90)

**Required:** Show how aging changes over time

**Goal:**
- Track if outstanding invoices are increasing (bad)
- Track if aging is worsening (bad)
- Show both absolute ($) and relative (%) trends

**Example Widget:**
```
Aging Breakdown Over Time

[Line Chart]
                          Oct      Nov      Dec
< 30 days         $1.2M  $1.5M    $1.8M  ↗ (worrying)
30-90 days        $800K  $900K    $1.1M  ↗ (worrying)
> 90 days         $200K  $300K    $400K  ↗ (bad!)

Total Outstanding $2.2M  $2.7M    $3.3M  ↗ +50% (3 months)
```

**Backend:** Need monthly aging snapshots table

```sql
CREATE TABLE invoice_aging_snapshots (
    snapshot_id INTEGER PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    under_30_days REAL,
    days_30_90 REAL,
    over_90_days REAL,
    total_outstanding REAL
);

-- Insert snapshot monthly (or weekly)
INSERT INTO invoice_aging_snapshots (snapshot_date, under_30_days, days_30_90, over_90_days, total_outstanding)
SELECT
    date('now'),
    SUM(CASE WHEN aging < 30 THEN invoice_amount ELSE 0 END),
    SUM(CASE WHEN aging BETWEEN 30 AND 90 THEN invoice_amount ELSE 0 END),
    SUM(CASE WHEN aging > 90 THEN invoice_amount ELSE 0 END),
    SUM(invoice_amount)
FROM (
    SELECT
        invoice_amount,
        julianday('now') - julianday(date_issued) as aging
    FROM invoices
    WHERE paid_date IS NULL
);
```

---

## 📧 EMAIL PAGES - MAJOR ISSUES

### Email Category Corrections Page - "looks really, really bad"

**Problems:**
1. ❌ Only shows "general" category when correcting
2. ❌ Notes field is "super tiny"
3. ❌ No subcategories shown
4. ❌ Email titles formatting is "ass" - text overflows
5. ❌ No email preview available
6. ❌ Can't open the email
7. ❌ Shows linked proposal but can't see it

**Quote:** "needs a lot more work"

**Fixes Needed:**

#### 1. Fix Category Dropdown
**Problem:** Only "general" available

**Fix:** Show all 9 categories
```typescript
const CATEGORIES = [
  'contract',
  'invoice',
  'proposal',
  'design_document',
  'correspondence',
  'internal',
  'financial',
  'rfi',
  'presentation'
]
```

#### 2. Fix Notes Field Size
**Current:** "super tiny"
**Fix:** Make textarea bigger (min-height: 120px)

#### 3. Add Subcategories
**If they exist in schema, show them in correction UI**

#### 4. Fix Email Title Formatting
**Problem:** Text overflows, "looks like shit"

**Fix:**
```css
.email-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 400px; /* or use flex */
}
```

#### 5. Add Email Preview
**Critical:** User can't see email content when correcting

**Solution:** Add preview panel or modal

```typescript
<EmailCorrectionRow>
  <EmailTitle onClick={() => openPreview(email)} />
  <CategoryBadge />
  <CorrectButton />
</EmailCorrectionRow>

<EmailPreviewModal email={selectedEmail}>
  <EmailHeader />
  <EmailBody />
  <EmailAttachments />
</EmailPreviewModal>
```

#### 6. Make Email Clickable
**Link to email detail view or open in modal**

#### 7. Show Linked Proposal Details
**If proposal is linked, show proposal info (name, value, status) not just code**

---

### Data Validation Page - "looks fucking fantastic" ✅

**Quote:** "looks fucking fantastic"
**Status:** Working well, approve button works
**Minor Issue:** Only 7 items, maybe needs more suggestions

---

### Email Links Manager - Purpose Unclear

**Quote:** "looks good, just don't really know what the point of it is"

**Action:**
- Add description/help text explaining purpose
- Or integrate into main email flow if redundant

---

### Overall Email Strategy

**Bill's Comment:** "I think we need to really dig into a little bit more and look into it, how we can integrate it together and add this kind of training feedback loop."

**Action Plan:**
1. Fix email category corrections page (priority)
2. Clarify purpose of email links manager
3. Better integration between email pages
4. Strengthen RLHF feedback loops
5. Consider consolidating redundant features

---

## 📊 SUMMARY - PRIORITY MATRIX

### 🚨 URGENT (Blocking for Bill's use)
1. Fix KPI wrong values (0s)
2. Fix proposal status update error (updated_BY)
3. Fix project names not showing
4. Fix email category corrections page

### 🔴 HIGH (Core functionality)
1. Implement hierarchical project fee breakdown
2. Add "Total Remaining Contract Value" KPI
3. Fix recent emails widget (or remove)
4. Restructure KPIs per Bill's requirements

### 🟡 MEDIUM (UX improvements)
1. Add trend indicators to all widgets
2. Add toggle: project vs invoice view
3. Make proposal numbers bigger
4. Add project names to "Needs Follow-up"
5. Over-time aging breakdown tracking

### 🟢 LOW (Nice to have)
1. Proposal document links
2. Better email integration
3. More validation suggestions
4. Clarify email links manager purpose

---

## 🎯 WHAT BILL LOVES ⭐

1. **Trend indicators** (+8.2%) - wants MORE of these
2. **Invoice aging color coding** - "fucking sick"
3. **Data validation page** - "looks fucking fantastic"
4. **Overall design** - "Super cool. Super clean. Nice."
5. **Invoice aging widget** - Loves the concept, wants it more interactive

---

## 📋 NEXT STEPS

### Immediate (Today):
1. Create fix prompts for all 5 Claudes
2. Fix database schema issues (updated_by column)
3. Verify contract_fee_breakdown data exists

### Short-term (This Week):
1. Implement hierarchical project breakdown
2. Fix all KPI calculations
3. Fix email corrections page
4. Add project names everywhere

### Medium-term (Next Sprint):
1. Add trend analysis to all widgets
2. Implement over-time aging tracking
3. Add view toggles
4. Better email integration

---

**Bill's Final Note:** "Other than that, it should be good."

**Translation:** Once these issues are fixed, the dashboard is production-ready for daily use.
