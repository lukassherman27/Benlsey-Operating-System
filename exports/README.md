# Exports Directory

Temporary data exports (CSV, Excel, JSON).

## Purpose

This folder holds data exports that are:
- Generated for analysis or sharing
- Temporary snapshots of database state
- Not tracked in git (see .gitignore)

## Naming Convention

Include date in filename for clarity:
```
YYYY-MM-DD_description.csv
```

Examples:
- `2025-11-26_all_proposals.csv`
- `2025-11-26_invoice_aging_report.xlsx`

## Current Exports

These files are gitignored - they exist locally but aren't tracked:
- `ACTIVE_PROJECTS_FULL_DATA.csv`
- `ALL_PROPOSALS_FULL_DATA.csv`
- `ALL_INVOICES_FULL_DATA.csv`
- etc.

## Cleanup

Periodically delete old exports (older than 30 days) to save space.
These can always be regenerated from the database.
