# Process Meeting Recording

When user says "process meeting" or runs /process-meeting:

## What This Does
Interactive workflow to transcribe a meeting recording, review it together, and send a summary email.

## Step 1: Get Recording Details

Ask user for:
1. **File path** - Where is the recording? (Check `~/Library/CloudStorage/OneDrive-Personal/Bensley/Voice Memos/Incoming` for recent files)
2. **Project code** - e.g., "25 BK-087" (optional - can detect from content)
3. **Attendees** - Who was on the call? (BENSLEY team + client names)
4. **Context** - Brief description of what this meeting was about

## Step 2: Transcribe

```bash
# Use the transcriber to just transcribe (no auto-email)
cd /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/voice_transcriber
python3 -c "
from transcriber import transcribe_audio
from pathlib import Path
transcript = transcribe_audio(Path('[FILE_PATH]'))
print(transcript)
"
```

Or if file is large, it will auto-chunk.

## Step 3: Review Transcript Together

Show the transcript to user. Ask:
- Any names that need correcting? (Whisper often mishears names)
- Any unclear sections?
- Anything to add/remove?

## Step 4: Generate Summary

With the corrected transcript + user context, generate:
- **Meeting Summary** - 3-6 paragraph narrative
- **Action Items** - Task, Owner, Deadline, Ball (us/them)
- **Key Decisions** - What was agreed
- **Next Steps** - What happens next

## Step 5: Review Summary

Show the summary to user:
- Are action items correct?
- Any missing items?
- Who should receive this email?

## Step 6: Send Email

Once approved:
- Format as HTML email
- Send to specified recipients
- Save transcript to database
- Create tasks from action items (using meeting_summary_parser)

## Quick Start

If user just says "process meeting", list recent recordings:

```bash
ls -la ~/Library/CloudStorage/OneDrive-Personal/Bensley/Voice\ Memos/Incoming/*.m4a 2>/dev/null | tail -10
```

Then ask which one to process.

## Example Interaction

```
User: process meeting

Claude: Found these recent recordings:
1. Dec 17 - Recording_001.m4a (45 min)
2. Dec 16 - Recording_002.m4a (22 min)

Which one? And tell me:
- Project code (if known)
- Who was on the call
- Brief context

User: #1, it's 25 BK-087 Pearl Resorts, call with Romain about contract revisions

Claude: Transcribing... [shows transcript]

Any corrections to names or content?

User: "Roman" should be "Romain"

Claude: Fixed. Here's the summary... [shows summary + action items]

Look good? Who should receive this?

User: Send to lukas@bensley.com and bill@bensley.com

Claude: Sent! Also created 4 tasks in the system.
```
