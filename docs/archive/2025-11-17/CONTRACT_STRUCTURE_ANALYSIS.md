# CONTRACT STRUCTURE ANALYSIS

## Current State

### Database Tables Status
- **contract_terms**: 0 records (empty Phase 2 table)
- **project_fee_breakdown**: 0 records (empty Phase 2 table)
- **invoices**: 254 records ($29.8M total)
- **projects**: 138 records (52 active, 72 proposals, 14 archived)

### Invoice-Project Linking
- **14 out of 52** active projects have invoices linked
- **38 active projects** worth $72M have NO invoices
- Only older projects (2013-2021) have invoice data
- Newer projects (2022-2025) missing financial tracking

### Top Active Projects WITH Invoices
1. 20 BK-092 - Resort Udaipur - 17 invoices, $4M invoiced ($3.1M paid)
2. 13 BK-057 - St. Regis Jakarta - 20 invoices, $2.65M invoiced ($2.4M paid)
3. 20 BK-047 - Audley Square House - 19 invoices, $2.54M invoiced ($2M paid)
4. 20 BK-060 - St. Regis Jakarta - 10 invoices, $2.1M invoiced (fully paid)

### Top Active Projects WITHOUT Invoices (Missing $72M)
1. 24 BK-074 - Dang Thai Mai Vietnam - $4.9M
2. 23 BK-050 - Ultra Luxury Bodrum Turkey - $4.65M
3. 22 BK-013 - Tel Aviv High Rise - $4.15M
4. 25 BK-037 - India Wellness hotel - $4M
5. 25 BK-027 - 30 Residence Villas Bai Bac - $3.95M
6. 22 BK-095 - Wynn Al Marjan Island - $3.77M
7. 24 BK-029 - Qinhu Resort China - $3.25M
8. 23 BK-068 - Treasure Island Resort - $3.25M
9. 25 BK-017 - TARC Delhi - $3M
10. 23 BK-029 - Mandarin Oriental Bali - $2.9M

---

## Contract Relationship Types Identified

### 1. Additional Services Contracts
Projects that link to existing active projects with supplemental work:

**Examples:**
- **25 BK-036** → links to **22 BK-095** (Wynn Al Marjan)
  - Additional services for existing Wynn project

- **25 BK-069** → links to **Bodrum Cheval Blanc**
  - Additional services for Bodrum project

- **25 BK-093-R** → links to **23 BK-093** (Downtown Mumbai)
  - Redesign service for existing project

- **25 BK-030** → links to **23 BK-029** (Mandarin Oriental Bali)
  - Beach Club additional services ($550K)

**Database Need:**
- Parent-child project relationship
- `parent_project_code` field in projects table
- `relationship_type` field: 'additional_services', 'extension', 'amendment', 'standalone'

### 2. Contract Extensions
Contracts that extend the timeline/scope of existing contracts:

**Examples:**
- **25 BK-018** - Ritz Carlton Nanyan Bay (Extension)
  - One year extension with new company entity

- **24 BK-021** - Capella Ubud Bali (Extension)
  - Extension of existing Capella contract

- **25 BK-028** - Villa Ahmedabad (Addendum)
  - 18 month extension agreement

**Database Need:**
- `original_contract_id` in contract_terms table (already exists!)
- `contract_type` values: 'original', 'extension', 'amendment'
- `extension_months` field
- Track amendment history

### 3. Monthly Installment Contracts
Contracts paid on monthly retainer basis:

**Examples:**
- **22 BK-095-4** - Wynn Night Club (Addendum $450K)
- **22 BK-013-M** - Tel Aviv Monthly Fee
- **25 BK-026** - Four Seasons Chiang Mai Landscape Maintenance (1 trip)

**Database Need:**
- `payment_schedule` JSON field in contract_terms (already exists!)
- Fee breakdown by month/period
- Recurring invoice automation

### 4. Phase-Based Contracts
Most common: Standard architecture phases with percentage splits:

**Standard Phases (from invoices):**
- Mobilization (typically 5-10%)
- Conceptual Design (20-30%)
- Design Development (30-40%)
- Construction Documents (25-35%)
- Construction Administration (10-15%)

**Database Need:**
- project_fee_breakdown table (already designed!)
- Phase-based payment tracking
- Link invoices to specific phases

### 5. Multi-Component Contracts
Single project with multiple sub-contracts (restaurants, clubs, etc.):

**Examples:**
- **Wynn Al Marjan Island** (22 BK-095):
  - 22 BK-095-1: Indian Brasserie #473 ($831,250)
  - 22 BK-095-2: Mediterranean #477 ($831,250)
  - 22 BK-095-3: Day Club #650 ($1,662,500)
  - 22 BK-095-4: Night Club Addendum ($450,000)

- **Tel Aviv High Rise** (22 BK-013):
  - 22 BK-013-I: Interior Phase 1
  - 22 BK-013-L: Landscape Phase 1
  - 22 BK-013-M: Monthly Fee

**Database Need:**
- `parent_project_code` to link components
- `component_type`: 'restaurant', 'club', 'landscape', 'interior', 'monthly'
- Aggregate total fees for parent contract

### 6. Cancelled/Archived Contracts
Signed contracts that were later cancelled:

**Examples:**
- 25 BK-023 - Sun Phu Quoc Airways (signed but cancelled)
- 25 BK-025 - APEC Downtown Project (signed but cancelled)

**Database Need:**
- `cancellation_date` field
- `cancellation_reason` text field
- `status_change_history` JSON to track lifecycle

---

## Required Database Schema Additions

### 1. Add to `projects` table:
```sql
ALTER TABLE projects ADD COLUMN parent_project_code TEXT;
ALTER TABLE projects ADD COLUMN relationship_type TEXT DEFAULT 'standalone';
  -- Values: 'standalone', 'additional_services', 'extension', 'component', 'amendment'
ALTER TABLE projects ADD COLUMN component_type TEXT;
  -- Values: 'restaurant', 'club', 'landscape', 'interior', 'spa', 'monthly_maintenance'
ALTER TABLE projects ADD COLUMN cancellation_date TEXT;
ALTER TABLE projects ADD COLUMN cancellation_reason TEXT;
ALTER TABLE projects ADD COLUMN status_change_history TEXT;
  -- JSON array tracking all status changes with dates

CREATE INDEX idx_projects_parent ON projects(parent_project_code);
CREATE INDEX idx_projects_relationship ON projects(relationship_type);
```

### 2. Populate `contract_terms` table:
For all 52 active projects, create contract_terms records with:
- Contract signed date (manual input needed)
- Total contract term months
- Fee schedule/payment milestones
- Contract type (fixed_fee, monthly, etc.)

### 3. Populate `project_fee_breakdown` table:
Based on invoice phase data, populate standard phase breakdown:
- Mobilization, Conceptual, DD, CD, CA phases
- Link existing invoices to phases
- Calculate percentages of total fee

### 4. Create new `project_relationships` table:
```sql
CREATE TABLE project_relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_project_code TEXT NOT NULL,
    child_project_code TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    -- 'additional_services', 'extension', 'component', 'amendment'
    description TEXT,
    effective_date TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_project_code) REFERENCES projects(project_code),
    FOREIGN KEY (child_project_code) REFERENCES projects(project_code)
);

CREATE INDEX idx_relationships_parent ON project_relationships(parent_project_code);
CREATE INDEX idx_relationships_child ON project_relationships(child_project_code);
```

---

## Next Steps

### Phase 1: Schema Updates (Immediate)
1. Add parent_project_code and relationship fields to projects table
2. Create project_relationships table for complex hierarchies
3. Add cancellation tracking fields

### Phase 2: Data Population (Manual + Automated)
1. Identify and link all parent-child project relationships
2. Import contract signed dates for all 52 active projects
3. Populate contract_terms with payment schedules
4. Map existing invoices to fee breakdown phases

### Phase 3: Contract Document Analysis (AI)
1. Build PDF contract parser to extract:
   - Signing dates
   - Payment schedules
   - Phase breakdowns
   - Scope of work
   - Term lengths
2. Auto-populate contract_terms table from scanned contracts
3. Validate extracted data with user confirmation

### Phase 4: Automation Services
1. Auto-generate invoices based on phase completion
2. Alert when contracts are expiring (90 days notice)
3. Track monthly installment due dates
4. Monitor parent project + additional services total fees
5. Proposal follow-up automation (user's #1 priority)

---

## Questions for User

To properly model the contract structure, please provide:

1. **Contract Document**: Sample contract showing:
   - Payment schedule structure
   - Phase definitions
   - Milestone terms
   - Extension/amendment language

2. **Parent-Child Projects**: Confirm these relationships:
   - 25 BK-036 → 22 BK-095 (Wynn)
   - 25 BK-069 → Bodrum Cheval Blanc
   - 25 BK-093-R → 23 BK-093 (Mumbai)
   - 25 BK-030 → 23 BK-029 (Mandarin Bali)

3. **Contract Dates**: For top 10 active projects ($38M), provide:
   - Contract signed dates
   - Expected start/end dates
   - Payment milestone dates

4. **Phase Standards**: Confirm typical phase breakdown:
   - Mobilization: ___%
   - Conceptual Design: ___%
   - Design Development: ___%
   - Construction Documents: ___%
   - Construction Admin: ___%

---

**Ready to implement once contract structure is confirmed!**
