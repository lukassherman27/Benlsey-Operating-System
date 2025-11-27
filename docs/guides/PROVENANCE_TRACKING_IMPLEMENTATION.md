# Data Provenance Tracking Implementation

## Overview
Implemented comprehensive data provenance tracking across the Bensley Operating System to ensure data integrity, prevent AI overwrites of manually entered data, and maintain complete audit trails.

## Purpose
- **Track data sources**: Know where every piece of data came from (manual entry, Excel import, AI parsing, email extraction)
- **Protect manual data**: Prevent automated systems from overwriting verified human entries
- **Enable auditing**: Full traceability of who created/modified what and when
- **Support verification**: Mark fields as verified/locked after manual review

## Database Schema Changes

### Migration 013: Core Provenance Columns
Added to tables: `projects`, `invoices`, `emails`, `project_metadata`

```sql
-- Provenance tracking
source_type TEXT CHECK(source_type IN ('manual', 'import', 'ai', 'email_parser'))
source_reference TEXT  -- e.g., "MASTER_CONTRACT_FEE_BREAKDOWN.xlsx:row_42"
created_by TEXT DEFAULT 'system'
updated_by TEXT

-- Field locking (for manually verified data)
locked_fields TEXT  -- JSON array: ["project_code", "total_fee_usd"]
locked_by TEXT      -- e.g., "user:bill", "seed/manual"
locked_at DATETIME
```

### Migration 020: Contract Table Provenance
Added same provenance columns to: `contract_metadata`, `contract_phases`

## Updated Import Scripts

### 1. import_proposal_tracking_dates.py
**What**: Imports historical proposal tracking dates from Proposals.xlsx calendar
**Provenance added**:
```python
source_type = 'import'
source_reference = 'Proposals.xlsx:Weekly_proposal_calendar'
updated_by = 'import_proposal_tracking_dates'
```

### 2. import_contract_fee_breakdown.py
**What**: Imports invoices from MASTER_CONTRACT_FEE_BREAKDOWN.xlsx
**Provenance added**:
```python
source_type = 'import'
source_reference = f'MASTER_CONTRACT_FEE_BREAKDOWN.xlsx:row_{idx}'
created_by = 'import_contract_fee_breakdown'
```

### 3. parse_contracts.py
**What**: AI-powered contract parsing from .docx/.pdf files
**Provenance added**:
```python
source_type = 'ai'
source_reference = f'contract_file:{filename}'
created_by = 'parse_contracts_ai'
```

## Provenance Types

| Type | Description | Example Use Case |
|------|-------------|------------------|
| `manual` | Human-entered data | User manually adds project details via UI |
| `import` | Excel/CSV import | Batch import from Proposals.xlsx |
| `ai` | AI/ML-generated | Claude parsing contract PDFs |
| `email_parser` | Email extraction | Automatically extracting data from emails |

## Data Protection Strategy

### Level 1: Source Tracking (All Data)
- Every record tracks `source_type`, `source_reference`, `created_by`
- Enables audit: "Where did this data come from?"

### Level 2: Manual Verification
- User reviews AI-suggested data
- Marks record as `confirmed_by_user = 1`
- Still allows AI updates (with logging)

### Level 3: Field Locking (Critical Data)
- Specific fields marked as locked in `locked_fields` JSON array
- Example: `["project_code", "total_fee_usd", "contract_signed_date"]`
- AI/import scripts MUST check locked fields before overwriting
- Only manual user action can unlock

## Future Implementation: Service Layer Guards

### Phase 2.6: Implement Guards (Pending)
Create guards in service layer to enforce provenance rules:

```python
def update_project(project_id, updates, source_type, user):
    """Update project with provenance enforcement"""

    # 1. Check locked fields
    locked = get_locked_fields(project_id)
    for field in updates.keys():
        if field in locked:
            raise LockedFieldError(f"{field} is locked by {locked_by}")

    # 2. Log provenance
    updates['updated_by'] = user
    updates['source_type'] = source_type

    # 3. Apply update
    db.update(project_id, updates)
```

## Verification Workflow Example

1. **AI imports invoice data** from email:
   ```python
   invoice = {
       'invoice_number': 'I25-001',
       'amount': 50000,
       'source_type': 'email_parser',
       'created_by': 'email_ai',
       'confidence': 0.85
   }
   ```

2. **User reviews and corrects**:
   - Finds amount should be $55,000 (AI misread)
   - Updates amount manually
   - System marks: `updated_by = 'user:bill'`, `source_type = 'manual'`

3. **User locks field**:
   ```python
   lock_fields(invoice_id, ['invoice_amount'], locked_by='user:bill')
   ```

4. **Future AI attempts update**:
   - Checks locked_fields: `['invoice_amount']`
   - Skips invoice_amount update
   - Only updates other fields (e.g., payment_date)
   - Logs: "Skipped locked field: invoice_amount"

## Benefits

### For Users
- **Confidence**: Manual work won't be overwritten
- **Transparency**: Always know data sources
- **Control**: Lock critical fields after verification

### For Developers
- **Debugging**: Track down data quality issues
- **Safety**: Prevent accidental overwrites
- **Compliance**: Audit trail for financial data

### For AI Systems
- **Safety rails**: Don't touch verified data
- **Feedback loop**: Learn from manual corrections
- **Confidence tracking**: Know what to ask humans about

## Status

### ✅ Completed
- Migration 013: Core provenance schema
- Migration 020: Contract table provenance
- Updated import_proposal_tracking_dates.py
- Updated import_contract_fee_breakdown.py
- Updated parse_contracts.py

### ⏳ Pending (Phase 2.6)
- Implement service layer guards
- Add provenance checks to backend services
- Create user verification UI
- Build field locking interface

## Next Steps

1. **Apply to remaining import scripts**:
   - import_proposals.py
   - import_contract_data.py
   - Any other batch import scripts

2. **Update backend services** (backend/services/*.py):
   - Add provenance parameters to all update functions
   - Implement locked field checks
   - Log all data modifications

3. **Build verification UI**:
   - Show data source in dashboard
   - Add "Verify & Lock" buttons
   - Display confidence scores for AI data
   - Allow field-level locking

4. **Create monitoring**:
   - Track which fields most often need manual correction
   - Identify low-confidence AI extractions
   - Report on data source distribution

## Example Queries

### Find all AI-generated data
```sql
SELECT * FROM invoices WHERE source_type = 'ai';
```

### Find all locked fields
```sql
SELECT project_code, locked_fields, locked_by, locked_at
FROM projects
WHERE locked_fields IS NOT NULL;
```

### Audit trail for specific invoice
```sql
SELECT invoice_number, source_type, source_reference, created_by, updated_by
FROM invoices
WHERE invoice_number = 'I25-001';
```

### Data source distribution
```sql
SELECT source_type, COUNT(*) as count
FROM projects
GROUP BY source_type;
```

---

**Last Updated**: 2025-11-19
**Implementation Status**: Phase 2.5 Complete
**Next Phase**: Service layer guards (Phase 2.6)
