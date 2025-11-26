# Contributing Guidelines

Standards for adding files and making changes to the Bensley Operations Platform.

## Core Principles

1. **Clean data is sacred** - No junk in database, no unused files
2. **Always test** - Never assume code works
3. **Archive, don't delete** - Preserve git history
4. **No hardcoding** - Use parameters and environment variables

## File Organization

### Where to Put New Files

| File Type | Location | Notes |
|-----------|----------|-------|
| Backend services | `backend/services/` | Core business logic |
| API endpoints | `backend/api/` | FastAPI routes |
| Active scripts | `scripts/core/` | Regularly used scripts |
| One-time scripts | `scripts/` → `scripts/archive/` after use | Move after running |
| Tests | `tests/` | Mirror source structure |
| Documentation | `docs/[category]/` | See docs/README.md |
| Data exports | `exports/` | Temporary, gitignored |

### What Stays at Root

Only these files belong at project root:
- `README.md`, `CLAUDE.md`, `CONTRIBUTING.md`
- `2_MONTH_MVP_PLAN.md`, `DATABASE_MIGRATION_SUMMARY.md`
- `requirements.txt`, `Dockerfile`, `docker-compose.yml`
- Config files (`.env`, `.gitignore`, etc.)

## Naming Conventions

### Python Scripts

```
[verb]_[noun]_[qualifier].py
```

| Prefix | Use For | Example |
|--------|---------|---------|
| `import_` | Data imports | `import_proposals.py` |
| `export_` | Data exports | `export_weekly_report.py` |
| `audit_` | Data auditing | `audit_invoice_links.py` |
| `fix_` | One-time fixes | `fix_schema_mismatch.py` |
| `generate_` | Report generation | `generate_weekly_report.py` |
| `sync_` | Synchronization | `sync_database.py` |
| `test_` | Test files | `test_email_service.py` |

**Never use:**
- Project names in filenames (`fix_wynn_marjan.py` ❌)
- Version suffixes (`script_v2.py` ❌) - use git branches instead
- Vague names (`do_stuff.py` ❌)

### Markdown Documents

```
CATEGORY_DESCRIPTION.md
```

Examples:
- `SESSION_SUMMARY_2025-11-24.md`
- `DEPLOYMENT_GUIDE.md`
- `PHASE_1_COMPLETE.md`

### Database Migrations

```
NNN_description.sql
```

Example: `013_add_proposal_tracking.sql`

## Database Standards

### Always Use Environment Variable

```python
import os
db_path = os.getenv('DATABASE_PATH', 'database/bensley_master.db')
```

### Provenance Tracking

Every import must track:
- `source_type` - Where data came from
- `source_reference` - Specific file/email/etc
- `created_by` - Script or user that created it

### Validation Before Insert

```python
# Always validate before inserting
if not data.get('project_code'):
    raise ValueError("Missing required field: project_code")
```

## Archiving

### When to Archive

Move to `archive/` when:
- Script is superseded by newer version
- One-time fix has been applied
- Feature development is complete
- Session/report is older than 2 weeks

### How to Archive

```bash
# Scripts
mv scripts/old_script.py scripts/archive/deprecated/

# Docs
mv docs/OLD_DOC.md docs/archive/
```

## Code Review Checklist

Before committing:
- [ ] No hardcoded database paths
- [ ] No project-specific hardcoding
- [ ] File is in correct directory
- [ ] Follows naming conventions
- [ ] Has been tested
- [ ] Provenance tracking included (for imports)

## Questions?

See `CLAUDE.md` for AI assistant context and `docs/guides/` for detailed guides.
