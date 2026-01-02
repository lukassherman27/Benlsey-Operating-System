# Monday Morning Report Setup

Automated weekly proposal report email sent every Monday at 7am.

## What It Does

Every Monday morning, the system:
1. Generates a beautiful HTML report with pipeline stats
2. Emails it to the configured recipient
3. Saves a backup HTML file in `reports/`
4. Archives the report data in the database

## Quick Start

### 1. Add to .env

Uses the same Bensley mail server as email sync:

```bash
# In your project .env file:
SMTP_HOST=tmail.bensley.com
SMTP_PORT=465
SMTP_USER=lukas@bensley.com
SMTP_PASSWORD=your_password_here
REPORT_EMAIL_TO=lukas@bensley.com
```

### 2. Test Email Sending

```bash
# Send a test email
python scripts/core/send_monday_report.py --test

# Generate report without sending (dry run)
python scripts/core/send_monday_report.py --dry-run

# Send the actual report
python scripts/core/send_monday_report.py
```

### 3. Install the Schedule

```bash
# Copy plist to LaunchAgents
cp launchd/com.bensley.monday-report.plist ~/Library/LaunchAgents/

# Load the scheduled job
launchctl load ~/Library/LaunchAgents/com.bensley.monday-report.plist

# Verify it's loaded
launchctl list | grep bensley
```

## Manual Testing

```bash
# Trigger the scheduled job manually
launchctl start com.bensley.monday-report

# Check output logs
cat /tmp/bensley-monday-report.out.log
cat /tmp/bensley-monday-report.err.log
```

## Troubleshooting

### "SMTP not configured" Error

Make sure your `.env` file has:
- `SMTP_USER` - Your Bensley email address
- `SMTP_PASSWORD` - Your email password

### "Authentication failed" Error

Verify your email credentials are correct - same as you use for email sync.

### Email Not Received

1. Check spam folder
2. Verify `REPORT_EMAIL_TO` is correct
3. Check `/tmp/bensley-monday-report.err.log` for errors

### Schedule Not Running

```bash
# Check if job is loaded
launchctl list | grep bensley

# If not loaded, reload it
launchctl load ~/Library/LaunchAgents/com.bensley.monday-report.plist

# Check for plist errors
plutil ~/Library/LaunchAgents/com.bensley.monday-report.plist
```

## Uninstall

```bash
# Stop and unload the job
launchctl unload ~/Library/LaunchAgents/com.bensley.monday-report.plist

# Remove the plist file
rm ~/Library/LaunchAgents/com.bensley.monday-report.plist
```

## Files

| File | Purpose |
|------|---------|
| `scripts/core/send_monday_report.py` | Main script |
| `backend/services/email_sender.py` | SMTP email service |
| `launchd/com.bensley.monday-report.plist` | Schedule configuration |
| `reports/` | Backup HTML files |
| `/tmp/bensley-monday-report.*.log` | Execution logs |

## Related

- [Roadmap Section 1.3](./roadmap.md) - Weekly Proposal Report feature
- Issue: #301
