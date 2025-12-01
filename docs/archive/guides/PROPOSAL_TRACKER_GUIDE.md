# Automated Proposal Tracker System

## Overview
This system automatically tracks all your active proposals, extracts updates from your emails, and generates weekly PDF reports for Bill.

## How It Works

### 1. Database (`proposal_tracker` table)
Stores all proposal data:
- Project code, name, value, country
- Current status (First Contact, Drafting, Proposal Sent, On Hold)
- Status history and days in each status
- Key dates (first contact, proposal sent)
- Current remarks and context
- Latest email updates

### 2. Email Intelligence (`proposal_email_intelligence.py`)
Automatically processes your emails using Claude AI to:
- Detect proposal-related content
- Extract status updates
- Identify action items and next steps
- Update proposal tracker automatically
- Track client sentiment

### 3. Weekly PDF Generator (`generate_weekly_proposal_report.py`)
Pulls from the database to create:
- Professional PDF report
- Color-coded status cells
- Summary statistics
- All formatted for Bill

## Daily Workflow

### When You Send/Receive Proposal Emails:
**The system does this automatically:**
```bash
# Run this daily or after important email batches
python3 proposal_email_intelligence.py analyze 3
```
This scans your last 3 days of emails and automatically:
- Finds proposal-related emails
- Extracts updates and context
- Updates the proposal tracker
- Tracks status changes

### When You Need to Generate Weekly Report:
```bash
# Simple one-liner
python3 generate_weekly_proposal_report.py
```

Output: `/Users/lukassherman/Desktop/Bensley Proposal Overview (November 21).pdf`

## Manual Updates

### Update a specific proposal:
```sql
UPDATE proposal_tracker
SET
    current_status = 'Proposal Sent',
    proposal_sent_date = '2024-11-21',
    current_remark = 'Sent revised proposal with new pricing',
    last_week_status = current_status,
    status_changed_date = datetime('now')
WHERE project_code = '25 BK-068';
```

### Check current status:
```bash
python3 proposal_email_intelligence.py report
```

## Database Queries

### See all active proposals:
```sql
SELECT project_code, project_name, current_status, days_in_current_status, current_remark
FROM proposal_tracker
WHERE is_active = 1
ORDER BY project_code;
```

### Get proposals needing follow-up (>14 days):
```sql
SELECT project_code, project_name, current_status, days_in_current_status
FROM proposal_tracker
WHERE is_active = 1
AND days_in_current_status > 14
AND current_status != 'On Hold'
ORDER BY days_in_current_status DESC;
```

### See email intelligence for a project:
```sql
SELECT email_subject, email_date, status_update, key_information, email_snippet
FROM proposal_email_intelligence
WHERE project_code = '25 BK-062'
ORDER BY email_date DESC;
```

## Automation Setup

### Set up weekly cron job (runs every Friday):
```bash
# Edit crontab
crontab -e

# Add this line (runs every Friday at 2 PM):
0 14 * * 5 cd /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System && /usr/local/bin/python3 generate_weekly_proposal_report.py
```

### Or create a simple weekly script:
```bash
#!/bin/bash
# weekly_proposal_update.sh

echo "Running proposal tracker weekly update..."

# Analyze last week's emails
python3 proposal_email_intelligence.py analyze 7

# Generate PDF
python3 generate_weekly_proposal_report.py

# Email to Bill (optional - add email command)
echo "Weekly proposal report generated!"
```

## Files Created

### Core System Files:
1. `/database/migrations/013_proposal_tracker_system.sql` - Database schema
2. `proposal_email_intelligence.py` - AI email processor
3. `generate_weekly_proposal_report.py` - PDF generator

### Database Tables:
- `proposal_tracker` - Main tracking table
- `proposal_email_intelligence` - Email-extracted intelligence
- `proposal_status_history` - History of all status changes
- `weekly_proposal_reports` - Log of generated reports

## Key Features

✓ **Automatic email processing** - AI reads your emails and updates tracker
✓ **Status tracking** - Knows how long each proposal has been in current status
✓ **Context preservation** - Keeps latest remarks and updates
✓ **Historical tracking** - Full history of status changes
✓ **One-command PDF generation** - Simple weekly report creation
✓ **Color-coded** - Visual status indicators (Green/Blue/Orange/Red)

## Commands Reference

```bash
# Initialize system with current data
python3 /tmp/init_proposal_tracker.py

# Analyze recent emails (default 7 days)
python3 proposal_email_intelligence.py analyze

# Analyze last 14 days
python3 proposal_email_intelligence.py analyze 14

# View current proposals
python3 proposal_email_intelligence.py report

# Generate weekly PDF
python3 generate_weekly_proposal_report.py

# Direct database access
sqlite3 /Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db
```

## Next Steps

1. **Test the email analysis** - Send yourself a test email about a proposal
2. **Set up weekly automation** - Add cron job for automatic reports
3. **Integrate with email sender** - Auto-email Bill on Fridays
4. **Add to dashboard** - Show proposals in your web interface

## Questions?

The system is now live and ready to use. Just run:
```bash
python3 generate_weekly_proposal_report.py
```

And you'll have your PDF ready to send to Bill!
