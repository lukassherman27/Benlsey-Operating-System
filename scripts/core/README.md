# Core Scripts

Active, production-ready scripts that are regularly used.

## Current Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `smart_email_brain.py` | Email intelligence and categorization | Main email processing |
| `query_brain.py` | Natural language query system | Query interface backend |
| `rfi_detector.py` | RFI detection in emails | Email processing pipeline |
| `import_step1_proposals.py` | Import proposals from Excel | Data import pipeline |
| `import_step2_fee_breakdown.py` | Import fee breakdowns | Data import pipeline |
| `import_step3_contracts.py` | Import contract data | Data import pipeline |
| `import_all_data.py` | Orchestrator for full import | Master import script |
| `populate_email_content.py` | Index email content | Email setup |
| `generate_weekly_proposal_report.py` | Weekly proposal report | Scheduled reports |
| `proposal_tracker_weekly_email.py` | Weekly email for proposal tracking | Scheduled reports |
| `daily_accountability_system.py` | Daily tracking and accountability | Daily automation |
| `quickstart.py` | Initial system setup | One-time setup |

## Rules for This Folder

1. **Only active scripts** - If not used regularly, move to `maintenance/` or `archive/`
2. **Well-tested** - Scripts here should be reliable and tested
3. **No hardcoded paths** - Use `os.getenv('DATABASE_PATH', 'database/bensley_master.db')`
4. **Document usage** - Update this README when adding scripts
