# Import Scripts

Scripts for importing data from external sources.

## Data Sources

- Excel spreadsheets (contracts, fee breakdowns)
- Email exports
- PDF documents (contracts, invoices)
- CSV files

## Import Standards

All import scripts must:
1. Validate data before inserting
2. Support dry-run mode
3. Track provenance (source_type, source_reference)
4. Handle duplicates gracefully
5. Log all operations

## Usage Pattern

```bash
# Dry run first
python scripts/imports/import_contracts.py --dry-run

# Then actual import
python scripts/imports/import_contracts.py
```

## See Also

- `scripts/core/import_all_data.py` - Master import pipeline
- `docs/guides/DATA_VALIDATION_WORKFLOW.md` - Validation process
