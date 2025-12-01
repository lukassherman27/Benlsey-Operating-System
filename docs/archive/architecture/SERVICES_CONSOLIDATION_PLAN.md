# Backend Services Consolidation Plan

**Current:** 39 service files
**Target:** ~20 service files
**Status:** Planning (not yet implemented)

## Overview

The `backend/services/` directory has grown organically and now contains overlapping functionality. This document outlines a consolidation plan.

## Current Service Groups

### Email Services (6 files → 2 files)

| Current | Proposed | Notes |
|---------|----------|-------|
| `email_service.py` | **Keep** | Core email operations |
| `email_importer.py` | Merge into `email_service.py` | Import functionality |
| `email_content_processor.py` | **Keep as `email_processor.py`** | Main processor |
| `email_content_processor_claude.py` | Merge into processor | Claude-specific logic |
| `email_content_processor_smart.py` | Merge into processor | Smart processing logic |
| `email_intelligence_service.py` | Merge into `email_service.py` | Intelligence features |

### Proposal Services (4 files → 2 files)

| Current | Proposed | Notes |
|---------|----------|-------|
| `proposal_service.py` | **Keep** | Core proposal operations |
| `proposal_query_service.py` | Merge into `proposal_service.py` | Query functionality |
| `proposal_tracker_service.py` | Merge into `proposal_service.py` | Tracking features |
| `query_service.py` | **Keep** | General query interface |

### Training/Learning (3 files → 1 file)

| Current | Proposed | Notes |
|---------|----------|-------|
| `learning_service.py` | Merge all → `training_service.py` | ML features |
| `training_data_service.py` | Merge | Data management |
| `training_service.py` | **Keep** | Unified training |

### File Services (2 files → 1 file)

| Current | Proposed | Notes |
|---------|----------|-------|
| `file_service.py` | **Keep** | File operations |
| `file_organizer.py` | Merge into `file_service.py` | Organization logic |

### Schedule Services (4 files → 2 files)

| Current | Proposed | Notes |
|---------|----------|-------|
| `schedule_email_parser.py` | Merge → `schedule_service.py` | Email parsing |
| `schedule_emailer.py` | Merge | Email sending |
| `schedule_pdf_generator.py` | Merge → `schedule_pdf_service.py` | PDF generation |
| `schedule_pdf_parser.py` | Merge | PDF parsing |

### Files to Remove/Move

| File | Action | Reason |
|------|--------|--------|
| `debug_pdf_table.py` | Move to `scripts/maintenance/` | Debug script, not a service |
| `test_services.py` | Move to `tests/` | Test file, not a service |

## Proposed Final Structure

```
backend/services/
├── __init__.py
├── base_service.py           # Base class
├── admin_service.py          # Admin operations
├── contract_service.py       # Contract management
├── context_service.py        # Context management
├── deliverables_service.py   # Deliverables tracking
├── document_service.py       # Document management
├── email_service.py          # Email operations (consolidated)
├── email_processor.py        # Email content processing (consolidated)
├── excel_importer.py         # Excel import
├── file_service.py           # File operations (consolidated)
├── financial_service.py      # Financial operations
├── intelligence_service.py   # AI/ML intelligence
├── invoice_service.py        # Invoice management
├── meeting_service.py        # Meeting management
├── milestone_service.py      # Milestone tracking
├── outreach_service.py       # Outreach operations
├── override_service.py       # Manual overrides
├── project_creator.py        # Project creation
├── proposal_service.py       # Proposal operations (consolidated)
├── query_service.py          # Query interface
├── rfi_service.py           # RFI management
├── schedule_service.py       # Schedule operations (consolidated)
├── schedule_pdf_service.py   # Schedule PDF (consolidated)
└── training_service.py       # Training/ML (consolidated)
```

**Result:** 39 files → 24 files (38% reduction)

## Implementation Notes

### Before Consolidating

1. **Check imports** - Search codebase for all imports of each service
2. **Check API routes** - Ensure routes still work after consolidation
3. **Run tests** - Ensure tests pass before and after
4. **Backup** - Create backup before major changes

### Consolidation Pattern

```python
# When merging service_b into service_a:

# 1. Move functions from service_b to service_a
# 2. Update imports in service_a
# 3. Search/replace imports across codebase:
#    from backend.services.service_b import X
#    → from backend.services.service_a import X
# 4. Delete service_b.py
# 5. Run tests
```

## Priority Order

1. **Low risk:** Move debug/test files out of services/
2. **Medium risk:** Consolidate training services (less used)
3. **Medium risk:** Consolidate file services
4. **Higher risk:** Consolidate email services (heavily used)
5. **Higher risk:** Consolidate proposal services (heavily used)

## Dependencies to Check

Before consolidating, run:
```bash
# Find all imports of a service
grep -r "from backend.services.email_importer" backend/ scripts/
grep -r "import email_importer" backend/ scripts/
```

---

**Status:** This is a planning document. Actual consolidation should be done carefully with testing.
