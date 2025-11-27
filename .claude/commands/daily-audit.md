# Daily Accountability Audit

Run the Daily Accountability System to generate a comprehensive audit report of today's progress.

## What This Does:

1. **Tracks Changes:**
   - Database changes (proposals, emails, documents)
   - File modifications
   - Git commits
   - System state

2. **Runs Two AI Agents:**
   - **Daily Summary Agent**: What changed today, alignment check
   - **Critical Auditor Agent**: Brutal honest critique of current state

3. **Generates Reports:**
   - HTML report (beautiful, interactive)
   - PDF/Text report (email-friendly)
   - Saves to `reports/daily/YYYY-MM-DD/`

4. **Sends Email:**
   - To: lukas@bensley.com
   - Subject: "Daily Accountability Report - [DATE]"
   - Includes both HTML and PDF attachments

## Instructions:

Run the daily accountability system:

```bash
cd /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System
python3 daily_accountability_system.py
```

The script will:
- Take snapshots of current state
- Analyze what changed since last run
- Generate AI-powered summaries and critiques
- Create beautiful reports
- Email them automatically

**Note:** First time running might take 2-3 minutes. Subsequent runs are faster.

## Expected Output:

You should see:
```
📊 Taking snapshot...
✓ Database snapshot complete
✓ File changes tracked
✓ Git activity logged

🤖 Running Daily Summary Agent...
✓ Summary generated

🔍 Running Critical Auditor Agent...
✓ Audit complete

📝 Generating reports...
✓ HTML report: reports/daily/2024-11-14/report.html
✓ PDF report: reports/daily/2024-11-14/report.pdf

📧 Sending email...
✓ Email sent to lukas@bensley.com

✅ Daily accountability report complete!
```

## Manual Review:

If you want to review the report before it's scheduled:
- Open: `reports/daily/YYYY-MM-DD/report.html` in browser
- Read PDF: `reports/daily/YYYY-MM-DD/report.pdf`

## Schedule for 9 PM Daily:

To set up automatic daily runs at 9 PM, add to crontab:
```bash
0 21 * * * cd /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System && /usr/bin/python3 daily_accountability_system.py
```
