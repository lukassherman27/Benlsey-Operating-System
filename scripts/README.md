# Scripts Directory

This directory contains all Python scripts for the Bensley Operations Platform.

## Structure

```
scripts/
├── core/           # Active, production scripts
├── analysis/       # Data audit and analysis tools
├── imports/        # Data import utilities
├── maintenance/    # Database maintenance and utilities
├── shell/          # Shell scripts (bash)
└── archive/        # Deprecated and one-time scripts
    ├── deprecated/        # Old versions, superseded code
    ├── project-specific/  # Hardcoded project scripts (don't reuse)
    └── one-time-fixes/    # One-time data fixes (already applied)
```

## Naming Conventions

| Prefix | Purpose | Example |
|--------|---------|---------|
| `import_` | Data import scripts | `import_step1_proposals.py` |
| `export_` | Data export scripts | `export_weekly_report.py` |
| `audit_` | Data auditing | `audit_invoice_links.py` |
| `fix_` | One-time fixes (archive after use) | `fix_schema_mismatch.py` |
| `generate_` | Report generation | `generate_weekly_proposal_report.py` |
| `query_` | Query/search tools | `query_brain.py` |

## Adding New Scripts

1. **Check if it belongs in `backend/services/`** - If it's core business logic, it probably does
2. **Use appropriate prefix** - Follow naming conventions above
3. **Add to correct folder**:
   - Ongoing use → `core/` or `maintenance/`
   - One-time fix → Run it, then move to `archive/one-time-fixes/`
   - Analysis tool → `analysis/`
4. **Never hardcode project names** - Use parameters instead

## Archiving Scripts

Move scripts to `archive/` when:
- They're superseded by a newer version
- They're one-time fixes that have been applied
- They reference old database paths or deprecated APIs

Keep in archive (don't delete) to preserve git history and allow reference.
