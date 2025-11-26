# Maintenance Scripts

Scripts for database maintenance, fixes, and upkeep.

## Purpose

These scripts:
- Fix data inconsistencies
- Run one-time corrections
- Perform maintenance tasks

## ⚠️ Caution

These scripts may modify data. Always:
1. Create a backup first: `make db-backup`
2. Test on sample data if possible
3. Review changes before committing

## Common Tasks

- `fix_*.py` - Data correction scripts
- `sync_*.py` - Synchronization scripts
- `backfill_*.py` - Fill in missing data

## After Running

1. Verify changes with analysis scripts
2. Update relevant documentation
3. Consider if script should be archived
