# Monday Morning Report Setup

Automated weekly proposal report email sent every Monday at 7am.

## What It Does

Every Monday morning, the system:
1. Generates a beautiful HTML report with pipeline stats
2. Emails it to the configured recipient
3. Saves a backup HTML file in `reports/`
4. Archives the report data in the database

## Quick Start

### 1. Configure Gmail App Password

You need a Gmail account with 2-Step Verification enabled.

1. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
2. Select "Mail" and "Other (Bensley Reports)"
3. Copy the 16-character password

### 2. Add to .env

```bash
# In your project .env file:
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx
REPORT_EMAIL_TO=lukas@bensley.com
```

### 3. Test Email Sending

```bash
# Send a test email
python scripts/core/send_monday_report.py --test

# Generate report without sending (dry run)
python scripts/core/send_monday_report.py --dry-run

# Send the actual report
python scripts/core/send_monday_report.py
```

### 4. Install the Schedule

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
- `SMTP_USER` - Your Gmail address
- `SMTP_PASSWORD` - The 16-character App Password (not your regular password!)

### "Authentication failed" Error

1. Verify 2-Step Verification is enabled on your Google account
2. Generate a new App Password
3. Make sure you're using the App Password, not your Google password

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
