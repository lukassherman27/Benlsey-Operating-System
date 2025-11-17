# Database Migrations

Automated database schema versioning and migration system.

## Quick Start

```bash
# Show migration status
python3 database/migrate.py --status

# Apply all pending migrations
python3 database/migrate.py

# Create a new migration
python3 database/migrate.py --create "add_user_preferences"
```

## Migration Files

Migrations are numbered sequentially:
- `001_schema_migrations_ledger.sql` - Migration tracking system
- `002_business_structure.sql` - Business tables
- `003_daily_work_tracking.sql` - Work tracking
- ... and so on

## Creating a New Migration

1. **Create the migration file:**
   ```bash
   python3 database/migrate.py --create "description_of_change"
   ```

2. **Edit the generated file:**
   ```bash
   # File will be created at database/migrations/XXX_description_of_change.sql
   # Add your SQL statements
   ```

3. **Apply the migration:**
   ```bash
   python3 database/migrate.py
   ```

## Migration File Format

```sql
-- Migration XXX: Description
-- Created: YYYY-MM-DD
-- Description: Detailed explanation

-- Add your SQL here
ALTER TABLE proposals ADD COLUMN new_field TEXT;

CREATE INDEX idx_new_field ON proposals(new_field);
```

## Best Practices

1. **One logical change per migration** - Don't mix unrelated changes
2. **Make migrations idempotent** - Use `IF NOT EXISTS`, `OR IGNORE`, etc.
3. **Test migrations** - Apply to a copy of the database first
4. **Never edit applied migrations** - Create a new migration instead
5. **Document breaking changes** - Add comments explaining impacts

## Migration States

- ✅ **Applied** - Migration has been run successfully
- ⏳ **Pending** - Migration exists but hasn't been run yet

## Tracking Table

All applied migrations are tracked in `schema_migrations`:

```sql
SELECT * FROM schema_migrations ORDER BY version;
```

Columns:
- `version` - Migration number (e.g., 1, 2, 3)
- `name` - Migration name
- `applied_at` - When it was applied
- `applied_by` - Who/what applied it
- `checksum` - MD5 hash for validation
- `execution_time_ms` - How long it took

## Troubleshooting

### Migration Failed

If a migration fails:
1. Check the error message
2. Fix the SQL in the migration file
3. Manually remove it from `schema_migrations` if partially applied:
   ```sql
   DELETE FROM schema_migrations WHERE version = X;
   ```
4. Re-run the migration

### Schema Out of Sync

If you suspect the schema doesn't match migrations:
1. Export current schema:
   ```bash
   sqlite3 ~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db ".schema" > current_schema.sql
   ```
2. Compare with `database/schema/bensley_master_schema.sql`
3. Create a corrective migration if needed

## Canonical Schema

The canonical schema (reflecting all migrations) is at:
```
database/schema/bensley_master_schema.sql
```

This is the source of truth for the database structure.

## Examples

### Add a Column
```sql
-- Migration 013: Add email sent count to proposals
ALTER TABLE proposals ADD COLUMN email_count INTEGER DEFAULT 0;
```

### Create a Table
```sql
-- Migration 014: Add user preferences
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id INTEGER PRIMARY KEY,
    theme TEXT DEFAULT 'light',
    notifications_enabled INTEGER DEFAULT 1
);
```

### Add an Index
```sql
-- Migration 015: Index for faster email lookups
CREATE INDEX IF NOT EXISTS idx_emails_date_sender
    ON emails(date DESC, sender_email);
```

## Future Migrations

When creating new migrations, follow this process:
1. Create migration file with `--create`
2. Add SQL statements
3. Test on dev database
4. Apply to production
5. Update canonical schema if major change
6. Commit both migration and schema to git
