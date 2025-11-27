# Analysis Scripts

Scripts for auditing, analyzing, and inspecting data.

## Purpose

These scripts are used for:
- Database audits and data quality checks
- System analysis and reporting
- Investigation and debugging

## Scripts

Analysis scripts typically:
- Read-only (don't modify data)
- Generate reports or output
- Help understand data state

## Usage

```bash
python scripts/analysis/audit_invoice_links.py
python scripts/analysis/complete_database_audit.py
```

## Output

Most scripts output to:
- Console for quick checks
- `reports/` directory for detailed reports
- `exports/` directory for CSV exports
