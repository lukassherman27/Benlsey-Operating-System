# Bensley Project Lifecycle & Data Model

## The Lifecycle

```
1. PROPOSAL STAGE (proposals table)
   ↓
2. CONTRACT SIGNED (moves to projects table)
   ↓
3. ACTIVE PROJECT (projects table)
   ├── Contract Phases (contract_phases table)
   ├── Invoices (invoices table)
   ├── Addendums/Extensions (proposals table with addendum flag)
   └── Completion

4. ONGOING CHANGES (dynamic)
   - Addendums (new proposals linked to active project)
   - Extensions (modify timeline)
   - Revisions (change scope/fees)
```

## Current Problem

**TWO SEPARATE TABLES** that don't link properly:
- `proposals` (87 records) - sales pipeline
- `projects` (46 records) - active signed projects

**Invoices reference `projects.project_id` NOT `proposals.proposal_id`**

**Missing Links:**
- No field in `projects` table pointing back to original `proposal_id`
- No way to track: "Proposal BK-017 became Project 115075"
- Invoice codes (I24-017) don't match project IDs (115075)

## The Fix

### 1. Add Link Between Proposals & Projects

```sql
-- Add proposal_id reference to projects table
ALTER TABLE projects ADD COLUMN proposal_id INTEGER;
ALTER TABLE projects ADD COLUMN original_proposal_code TEXT;

-- Add project_id reference to proposals table
ALTER TABLE proposals ADD COLUMN active_project_id INTEGER;
```

### 2. Fix Invoice Linking Logic

**Current:** Invoices use sequential project_id (3600, 3601, 115075, etc.)
**Problem:** Invoice numbers use project code (I24-017 = BK-017)

**Solution:** Match invoices by extracting project code from invoice number

```sql
-- Example: I24-017 → BK-017 → Find project with code '25 BK-017' or 'BK-017'
```

### 3. Proposal → Project Relationship Types

| Type | Description | Example |
|------|-------------|---------|
| **Original Contract** | Initial proposal that won | BK-017 proposal → 25 BK-017 project |
| **Addendum** | Extension/addition to existing project | BK-017-A1 → adds to 25 BK-017 |
| **Revision** | Updated proposal (supersedes old) | BK-008 cancelled → BK-017 replaces it |
| **Maintenance** | Ongoing annual contracts | BK-012 → yearly renewals |

## Data Model Rules

### When a Proposal Becomes a Project:

1. **proposals.status** = 'won'
2. **proposals.contract_signed_date** = date signed
3. **proposals.active_project_id** = created project_id
4. **New record in projects table:**
   - `project_id` = auto-increment (e.g., 115075)
   - `project_code` = from proposal (e.g., '25 BK-017')
   - `proposal_id` = link back to original proposal
   - `status` = 'Active'

### When Invoices Are Created:

1. Extract project code from invoice number (I24-017 → 017)
2. Find matching project by code (BK-017 or 25 BK-017)
3. Link to `projects.project_id` (NOT proposal_id!)

### When Addendums Happen:

1. Create new proposal record with:
   - New proposal_id
   - `parent_proposal_id` = original proposal
   - `active_project_id` = links to same project
   - `status` = 'addendum'
2. Update project fees/scope as needed

## Current State Analysis

### Proposals Table (87 records)
- Mix of active proposals, won contracts, cancelled
- Some won contracts have NO corresponding project record
- Some are addendums to existing projects

### Projects Table (46 records)
- Active signed projects only
- Uses different project codes than proposals (e.g., "23 BK-088" vs "BK-088")
- No back-link to original proposal

### Invoices Table (253 records)
- **ALL** reference projects.project_id
- Invoice numbers encode project code (I24-017 = project 017)
- Many mislinked due to ID mismatch

## Next Steps

1. ✅ Audit proposals vs projects to find matches
2. ✅ Fix invoice links by matching invoice codes to project codes
3. ✅ Add proposal_id ↔ project_id bidirectional links
4. ✅ Handle special cases (addendums, revisions, maintenance)
5. ✅ Update all tools/APIs to understand full lifecycle
