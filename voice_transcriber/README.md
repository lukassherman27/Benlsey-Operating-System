# Voice Memo Transcriber

Automatic transcription and AI summarization for meeting recordings.

## How It Works

```
Bill clicks "Record" on his Mac
    ↓
Records the meeting
    ↓
Clicks "Stop"
    ↓
Saves to shared OneDrive folder (automatic)
    ↓
Lukas's system detects new file
    ↓
Transcribes (Whisper) + Summarizes (Claude)
    ↓
Links to project + saves to database
    ↓
Email notification sent
```

**Bill's experience:** Click record, talk, click stop. That's it. Transcript + summary appears automatically.

## Features

- **One-Click Recording:** Simple menu bar app - click to record, click to stop
- **Auto-Sync:** Recordings save to shared OneDrive folder, sync automatically
- **Whisper Transcription:** Accurate speech-to-text via OpenAI API
- **Claude Summaries:** Key points, action items, meeting type detection
- **Project Matching:** Auto-detects which BDS project is being discussed
- **Email Delivery:** Sends transcript + summary to configured recipients
- **Database Storage:** Saves to BDS database for future reference

## System Overview

There are **two components**:

| Component | Runs On | Purpose |
|-----------|---------|---------|
| **Meeting Recorder** | Bill's Mac | Records audio, saves to OneDrive |
| **Transcriber** | Lukas's Mac | Watches folder, transcribes, processes |

## Installation

### For Bill (Recording)

1. Get the `voice_transcriber` folder from Lukas
2. Run the installer:
   ```bash
   cd voice_transcriber
   ./install_recorder.sh
   ```
3. Look for 🎙️ in menu bar
4. Click to start/stop recording

That's it! Recordings sync automatically.

### For Lukas (Processing)

#### Prerequisites
1. **Python 3.11+**
2. **API Keys:**
   - OpenAI API key ([platform.openai.com](https://platform.openai.com/api-keys))
   - Anthropic API key ([console.anthropic.com](https://console.anthropic.com/))

### Quick Install

```bash
# 1. Navigate to the installer
cd /path/to/voice_transcriber

# 2. Make installer executable
chmod +x install.sh

# 3. Run installer
./install.sh

# 4. Edit config with API keys
open ~/VoiceTranscriber/config.py

# 5. Start the service
launchctl load ~/Library/LaunchAgents/com.bensley.voice-transcriber.plist
```

## Configuration

Edit `~/VoiceTranscriber/config.py`:

```python
# Required
OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."

# Optional: Email notifications
EMAIL_SENDER = "bill@bensley.com"
EMAIL_PASSWORD = "app-password"  # Gmail app password, not regular password
EMAIL_RECIPIENTS = ["lukas@bensley.com"]
```

## Commands

```bash
# Check status
python3 ~/VoiceTranscriber/transcriber.py --status

# Process once (don't run continuously)
python3 ~/VoiceTranscriber/transcriber.py --once

# Test with specific file
python3 ~/VoiceTranscriber/transcriber.py --test /path/to/audio.m4a

# Start service (runs on boot)
launchctl load ~/Library/LaunchAgents/com.bensley.voice-transcriber.plist

# Stop service
launchctl unload ~/Library/LaunchAgents/com.bensley.voice-transcriber.plist

# View logs
tail -f ~/VoiceTranscriber/transcriber.log
```

## Output

Transcripts are saved to:
- **Email:** Sent to configured recipients
- **Local files:** `~/Documents/Meeting Transcripts/`
- **BDS Database:** `meeting_transcripts` table

## Cost

- **Whisper:** ~$0.006/minute of audio (~$0.36/hour)
- **Claude:** ~$0.01-0.05 per summary
- **Total:** A 1-hour meeting costs roughly $0.50-1.00

## Troubleshooting

### "Voice Memos folder not found"
Make sure iCloud Drive is enabled and Voice Memos sync is on:
- iPhone: Settings → [Your Name] → iCloud → Voice Memos → On
- Mac: System Preferences → Apple ID → iCloud Drive → Options → Voice Memos

### "API Key not set"
Edit `~/VoiceTranscriber/config.py` and add your API keys.

### Service not starting
```bash
# Check if running
launchctl list | grep voice-transcriber

# View errors
cat ~/VoiceTranscriber/stderr.log
```

### Files not processing
- Wait 60 seconds after recording (prevents processing incomplete syncs)
- Check `~/VoiceTranscriber/processed_files.json` for already-processed files
