# Daily Frontend Audit Script

`daily_audit.js` runs a quick health-check on the dashboard codebase and appends a summary to `AI_DIALOGUE.md` so Claude always sees Codex's perspective.

## What it does
- Runs `npm run lint -- --max-warnings=0`
- Captures branch name, number of changed files, and component count
- Appends a Markdown block to `AI_DIALOGUE.md` with warnings/questions

## One-off run
```bash
cd frontend
node scripts/daily_audit.js
```

## Schedule nightly (example cron – 9:02 PM)
```bash
2 21 * * * cd /path/to/repo/frontend && node scripts/daily_audit.js >> /tmp/codex_audit.log 2>&1
```

If lint fails, the script exits with code `1` so cron logs the failure.

## Sample one-liner to install cron job
```bash
(crontab -l 2>/dev/null; echo "2 21 * * * cd /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/frontend && node scripts/daily_audit.js >> /tmp/codex_audit.log 2>&1") | crontab -
```

## Troubleshooting
- Ensure `npm install` has been run in `frontend/`.
- Script appends to `AI_DIALOGUE.md`; review git diffs regularly.
