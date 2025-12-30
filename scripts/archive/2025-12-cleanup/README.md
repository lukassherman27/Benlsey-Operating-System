# 2025-12 Script Cleanup Archive

Scripts archived on 2025-12-30 as part of system audit cleanup.

## Archived Scripts

| Script | Lines | Reason for Archive |
|--------|-------|-------------------|
| `backfill_proposal_activities.py` | 326 | One-time backfill script for Issue #140. Already ran to seed historical activity data. |
| `review_enrichment_suggestions.py` | 246 | Old interactive CLI for reviewing suggestions. Superseded by `/suggestions` UI in frontend. |
| `organize_attachments.py` | 344 | Utility to organize attachments by project folder. Never deployed to production. |
| `continuous_email_processor.py` | 83 | Wrapper around smart_email_brain.py. Redundant with `scheduled_email_sync.py` which runs hourly via cron. |
| `email_category_review.py` | 340 | Email category review CLI. Not integrated into main workflow. |
| `detect_waiting_for.py` | 418 | Detects "waiting for" status on proposals. Not integrated into main workflow. |

## Audit Verification

Before archiving, verified each script:
- Not in crontab (`crontab -l`)
- Not in LaunchAgents (`ls ~/Library/LaunchAgents/`)
- Not imported by any Python file (`grep -r "from scripts.core.X import"`)
- Not referenced in skill files or configs

## Scripts Still Active in scripts/core/

| Script | Schedule | Purpose |
|--------|----------|---------|
| `scheduled_email_sync.py` | Hourly (cron) | Import emails, run pattern-first linker |
| `daily_accountability_system.py` | Daily 9pm (cron) | Daily accountability system |
| `backup_database.py` | LaunchD | Database backups |

## Restoration

If needed, restore with:
```bash
git mv scripts/archive/2025-12-cleanup/SCRIPT.py scripts/core/
```

## Reference

Audit documented in: `docs/research/2025-01/SYSTEM-AUDIT-COMPREHENSIVE.md` (Section 3: Script Audit)
