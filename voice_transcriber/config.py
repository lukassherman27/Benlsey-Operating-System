"""
Configuration for Voice Memo Transcriber
Edit these settings before first run.
"""
import os
from pathlib import Path

# =============================================================================
# API KEYS (Required)
# =============================================================================

# OpenAI API key for Whisper transcription
# Get one at: https://platform.openai.com/api-keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Anthropic API key for Claude summarization
# Get one at: https://console.anthropic.com/
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# =============================================================================
# EMAIL SETTINGS (Required for email notifications)
# =============================================================================

# Gmail App Password recommended (not regular password)
# See: https://support.google.com/accounts/answer/185833
EMAIL_SENDER = ""  # e.g., "bill@bensley.com"
EMAIL_PASSWORD = ""  # App password, not regular password
EMAIL_RECIPIENTS = ["lukas@bensley.com"]  # Who gets the transcripts
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# =============================================================================
# VOICE MEMOS / RECORDINGS FOLDER
# =============================================================================

# TODO: Update this once Bensley OneDrive is set up
# This is where the transcriber WATCHES for new recordings
#
# Options:
# 1. Shared OneDrive folder (recommended once Bensley M365 is set up):
#    VOICE_MEMOS_FOLDER = Path.home() / "Library/CloudStorage/OneDrive-BensleyDesignStudios/Voice Memos"
#
# 2. Personal OneDrive shared folder (current):
#    VOICE_MEMOS_FOLDER = Path.home() / "Library/CloudStorage/OneDrive-Personal/Bensley/Voice Memos/Incoming"
#
# 3. iCloud Voice Memos (if using iPhone recordings):
#    VOICE_MEMOS_FOLDER = Path.home() / "Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings"

# Current: Personal OneDrive folder
VOICE_MEMOS_FOLDER = Path.home() / "Library/CloudStorage/OneDrive-Personal/Bensley/Voice Memos/Incoming"

# Fallback to iCloud Voice Memos if OneDrive folder doesn't exist
if not VOICE_MEMOS_FOLDER.exists():
    alt_path = Path.home() / "Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings"
    if alt_path.exists():
        VOICE_MEMOS_FOLDER = alt_path

# =============================================================================
# OUTPUT SETTINGS
# =============================================================================

# Where to save transcripts locally
OUTPUT_FOLDER = Path.home() / "Documents/Meeting Transcripts"

# BDS Database path (for linking to projects)
BDS_DATABASE = Path(__file__).parent.parent / "database/bensley_master.db"

# =============================================================================
# PROCESSING SETTINGS
# =============================================================================

# How often to check for new recordings (seconds)
CHECK_INTERVAL = 30

# Minimum file age before processing (seconds)
# Prevents processing files still being synced
MIN_FILE_AGE = 60

# Whisper model to use (via API, so this is just for reference)
WHISPER_MODEL = "whisper-1"

# Claude model for summarization
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# =============================================================================
# PROJECT MATCHING
# =============================================================================

# Enable automatic project detection from transcript content
AUTO_DETECT_PROJECT = True

# Minimum confidence score for auto-linking (0-1)
PROJECT_MATCH_CONFIDENCE = 0.7
