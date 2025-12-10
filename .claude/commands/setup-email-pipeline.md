# Email Pipeline Setup - Full Automation

You are setting up the complete email automation pipeline for Bensley Operating System.

## OVERVIEW

This session will:
1. Reject 64 stale pending suggestions
2. Run smart categorizer on 274 uncategorized emails
3. Set up daily email sync automation
4. Verify everything works

## STEP 1: Clean Up Stale Suggestions

Run this to reject the 64 old pending suggestions from Dec 3:

```bash
cd "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System"
python3 -c "
import sqlite3
conn = sqlite3.connect('database/bensley_master.db')
cursor = conn.cursor()

# Count before
cursor.execute('SELECT COUNT(*) FROM ai_suggestions WHERE status = \"pending\"')
before = cursor.fetchone()[0]
print(f'Pending suggestions before: {before}')

# Reject all pending (they are stale from Dec 3)
cursor.execute('''
    UPDATE ai_suggestions
    SET status = \"rejected\",
        rejection_reason = \"Batch rejected 2025-12-08 - stale suggestions, proposals already manually updated\"
    WHERE status = \"pending\"
''')
print(f'Rejected: {cursor.rowcount}')

conn.commit()

# Verify
cursor.execute('SELECT COUNT(*) FROM ai_suggestions WHERE status = \"pending\"')
after = cursor.fetchone()[0]
print(f'Pending suggestions after: {after}')

conn.close()
print('Done!')
"
```

Confirm this worked (should show 0 pending after), then proceed.

## STEP 2: Run Smart Categorizer

First, preview what it will do:

```bash
cd "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System"
python scripts/core/smart_categorizer.py --dry-run --limit 274
```

If that looks good, run it for real:

```bash
python scripts/core/smart_categorizer.py --limit 500
```

This will:
- Detect direction (internal/outbound/inbound)
- Assign categories (internal gets INT-OPS/FIN/MKTG/LEGAL/BILL, external gets meeting/contract/design/etc)
- Extract project codes and create links (even for internal emails!)
- Report stats

## STEP 3: Verify Results

Check the results:

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('database/bensley_master.db')
cursor = conn.cursor()

print('=== POST-CATEGORIZATION STATUS ===')
print()

# Uncategorized count
cursor.execute('SELECT COUNT(*) FROM emails WHERE category IS NULL')
print(f'Uncategorized emails: {cursor.fetchone()[0]}')

# Category breakdown
cursor.execute('SELECT category, COUNT(*) as cnt FROM emails GROUP BY category ORDER BY cnt DESC')
print()
print('Categories:')
for row in cursor.fetchall():
    print(f'  {row[0] or \"NULL\"}: {row[1]}')

# Internal links
cursor.execute('SELECT COUNT(*) FROM email_internal_links')
print(f')
print(f'Internal category links: {cursor.fetchone()[0]}')

# Project links
cursor.execute('SELECT COUNT(*) FROM email_proposal_links')
prop_links = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM email_project_links')
proj_links = cursor.fetchone()[0]
print(f'Proposal links: {prop_links}')
print(f'Project links: {proj_links}')

conn.close()
"
```

## STEP 4: Set Up Daily Email Sync

### Option A: Manual Daily Run (Simplest)

Create a simple run script:

```bash
cat > "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/run_daily_sync.sh" << 'EOF'
#!/bin/bash
cd "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System"

# Load environment
export EMAIL_USERNAME="your_email@bensley.com"
export EMAIL_PASSWORD="your_password"
export EMAIL_SERVER="tmail.bensley.com"
export EMAIL_PORT="993"

# Run sync
echo "Starting email sync at $(date)"
python scripts/core/scheduled_email_sync.py

# Run categorizer on any new uncategorized
echo "Running categorizer..."
python scripts/core/smart_categorizer.py --limit 100

echo "Done at $(date)"
EOF

chmod +x run_daily_sync.sh
```

Then run manually each morning:
```bash
./run_daily_sync.sh
```

### Option B: macOS LaunchAgent (Automatic)

Create a LaunchAgent to run every 4 hours:

```bash
cat > ~/Library/LaunchAgents/com.bensley.emailsync.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.bensley.emailsync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/run_daily_sync.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>14400</integer>
    <key>StandardOutPath</key>
    <string>/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/logs/sync.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/logs/sync_error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>EMAIL_USERNAME</key>
        <string>your_email@bensley.com</string>
        <key>EMAIL_PASSWORD</key>
        <string>your_password</string>
        <key>EMAIL_SERVER</key>
        <string>tmail.bensley.com</string>
        <key>EMAIL_PORT</key>
        <string>993</string>
    </dict>
</dict>
</plist>
EOF

# Load it
launchctl load ~/Library/LaunchAgents/com.bensley.emailsync.plist

# Check status
launchctl list | grep bensley
```

To stop it later:
```bash
launchctl unload ~/Library/LaunchAgents/com.bensley.emailsync.plist
```

## STEP 5: Test the Full Pipeline

Test that everything works end-to-end:

```bash
# 1. Check current email count
python3 -c "
import sqlite3
conn = sqlite3.connect('database/bensley_master.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM emails')
print(f'Current emails: {cursor.fetchone()[0]}')
cursor.execute('SELECT MAX(date) FROM emails')
print(f'Most recent: {cursor.fetchone()[0]}')
conn.close()
"

# 2. Run the sync (will need real credentials)
# python scripts/core/scheduled_email_sync.py --dry-run

# 3. Verify new emails came in
# python scripts/core/smart_categorizer.py --limit 50
```

## IMPORTANT: Email Credentials

The user needs to provide:
- EMAIL_USERNAME (their Bensley email)
- EMAIL_PASSWORD (their email password)

Ask them for these to complete the setup. Store in .env file:

```bash
cat > "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/.env" << 'EOF'
DATABASE_PATH=/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/bensley_master.db
EMAIL_USERNAME=your_email@bensley.com
EMAIL_PASSWORD=your_password
EMAIL_SERVER=tmail.bensley.com
EMAIL_PORT=993
EOF
```

## SUCCESS CRITERIA

After this session:
- [ ] 0 pending suggestions (all rejected)
- [ ] 0 uncategorized emails (all processed)
- [ ] Daily sync script created
- [ ] Pipeline tested and working

## TROUBLESHOOTING

If IMAP connection fails:
- Check EMAIL_SERVER is correct (tmail.bensley.com)
- Check EMAIL_PORT is 993 (SSL)
- Check credentials are correct
- Try: `python scripts/core/scheduled_email_sync.py --dry-run`

If categorizer fails:
- Check database path is correct
- Try with smaller limit: `--limit 10`
- Check for Python errors in output
