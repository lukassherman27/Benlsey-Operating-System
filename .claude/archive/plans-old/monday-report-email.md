# Monday Morning Report Email - Implementation Plan

## Summary

Automate sending the weekly proposal report to Bill every Monday at 7am.

**What exists:**
- `WeeklyReportService.generate_html_report()` - Complete HTML email generation
- `/api/reports/weekly-proposals/preview/html` - API endpoint for HTML report
- Beautiful HTML report with pipeline stats, attention items, top opportunities

**What needs to be built:**
- Email sending capability
- Script to generate + send the report
- macOS scheduling (launchd plist)

---

## 1. Email Delivery Method: Gmail SMTP with App Password

**Why Gmail SMTP (not SendGrid):**
- Single email per week = very low volume
- Free (no subscription needed)
- Python smtplib is built-in (no external dependencies)
- Sufficient deliverability for internal business reports
- SendGrid ($19.95/mo) is overkill for 4 emails/month

**Configuration (.env):**
```env
# Email Configuration for Monday Report
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx  # Gmail App Password (16 chars)
REPORT_EMAIL_TO=bill@bensley.com
REPORT_EMAIL_FROM=reports@bensley.com  # Display name, sends via SMTP_USER
```

**Setup required:**
1. Create Gmail App Password: Google Account → Security → 2-Step Verification → App Passwords
2. Generate password with "Mail" / "Other (Bensley Reports)"
3. Store 16-character password in .env

---

## 2. Scheduling Method: launchd plist

**Why launchd (not cron):**
- macOS native scheduling system
- Catches up on missed runs if computer was asleep
- Better logging and error handling
- Persistent across reboots

**Schedule:** Monday 7:00 AM local time

**Plist file:** `~/Library/LaunchAgents/com.bensley.monday-report.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.bensley.monday-report</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/scripts/core/send_monday_report.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>1</integer>  <!-- Monday -->
        <key>Hour</key>
        <integer>7</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/bensley-monday-report.out.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/bensley-monday-report.err.log</string>
    <key>WorkingDirectory</key>
    <string>/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
```

**Install commands:**
```bash
# Copy plist to LaunchAgents
cp launchd/com.bensley.monday-report.plist ~/Library/LaunchAgents/

# Load the agent
launchctl load ~/Library/LaunchAgents/com.bensley.monday-report.plist

# Verify it's loaded
launchctl list | grep bensley

# Manual test run
launchctl start com.bensley.monday-report
```

---

## 3. Files to Create

### 3.1 `backend/services/email_sender.py`
Simple SMTP email sender service:
- Send HTML emails via Gmail SMTP
- SSL connection (port 465)
- Load credentials from .env
- Logging for success/failure

### 3.2 `scripts/core/send_monday_report.py`
Main script that:
1. Generates HTML report using WeeklyReportService
2. Sends via email_sender
3. Archives the report in database
4. Logs the outcome
5. Saves HTML backup to file (fallback)

### 3.3 `launchd/com.bensley.monday-report.plist`
The scheduling plist (in repo for version control)

### 3.4 Update `.env.example`
Add email configuration variables

---

## 4. Fallback Behavior

If email fails:
1. Log the error with full traceback
2. Save HTML report to `reports/weekly-report-{date}.html`
3. Exit with non-zero code (launchd will log this)
4. Manual check: `cat /tmp/bensley-monday-report.err.log`

---

## 5. Testing Approach

**Test without waiting for Monday:**

```bash
# 1. Test email sending directly
python3 -c "from backend.services.email_sender import send_email; send_email('test@email.com', 'Test', '<h1>Hello</h1>')"

# 2. Test full script (dry run)
python3 scripts/core/send_monday_report.py --dry-run

# 3. Test full script (actually send)
python3 scripts/core/send_monday_report.py

# 4. Manual launchctl trigger
launchctl start com.bensley.monday-report

# 5. Check logs
cat /tmp/bensley-monday-report.out.log
cat /tmp/bensley-monday-report.err.log
```

---

## 6. Deliverables Summary

| File | Purpose |
|------|---------|
| `backend/services/email_sender.py` | SMTP email sending service |
| `scripts/core/send_monday_report.py` | Main script (generate + send) |
| `launchd/com.bensley.monday-report.plist` | macOS scheduling |
| `.env.example` update | Document required env vars |
| `docs/MONDAY_REPORT_SETUP.md` | Setup instructions |

---

## 7. Success Criteria

- [ ] Script sends HTML email with full weekly report
- [ ] Email arrives in Bill's inbox (not spam)
- [ ] launchd plist schedules for Monday 7am
- [ ] Credentials stored securely in .env (not committed)
- [ ] Logs show send status
- [ ] Fallback saves HTML to file if email fails
- [ ] Setup instructions are clear for non-technical user

---

## Questions for Approval

1. **Gmail account to use:** Which Gmail account should send the reports? (or should we use a service like SendGrid?)

2. **Bill's email:** Confirm `bill@bensley.com` is correct recipient

3. **Backup recipients:** Should anyone else receive the report (CC)?

4. **Send time:** Monday 7am OK, or different time?
