# Log Issue - Quick Issue Capture

Quick command to log issues you notice while using the system.

## Usage

Just describe what's broken or wrong:
```
/log-issue The proposals table takes 10 seconds to load
/log-issue Contact search returns wrong results
/log-issue Calendar widget shows meetings from wrong timezone
```

## What This Does

1. Creates a GitHub issue with:
   - Title from your description
   - `needs-triage` label (for later categorization)
   - Timestamp and context

2. Does NOT:
   - Require you to categorize it
   - Require you to assign priority
   - Require you to write a detailed description

The Triage Agent will organize these later.

## Instructions for Claude

When user runs `/log-issue <description>`:

1. Create GitHub issue:
```bash
gh issue create \
  --title "<user's description>" \
  --body "## Quick Issue Log

**Reported:** $(date)
**Source:** User observation

---

_This issue was quickly logged and needs triage. The Issue Triage Agent will categorize and prioritize it._" \
  --label "needs-triage"
```

2. Confirm to user: "Logged issue #XXX - will be triaged later"

3. Do NOT try to fix it immediately unless user asks
