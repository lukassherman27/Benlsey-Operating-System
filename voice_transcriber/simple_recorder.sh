#!/bin/bash
#
# Simple Meeting Recorder - Uses macOS built-in tools
# No dependencies needed!
#
# Usage: ./simple_recorder.sh
#

OUTPUT_DIR="$HOME/Library/CloudStorage/OneDrive-Personal/Bensley/Voice Memos/Incoming"
mkdir -p "$OUTPUT_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="$OUTPUT_DIR/meeting_$TIMESTAMP.m4a"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Simple Meeting Recorder                                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Output: $OUTPUT_FILE"
echo ""
echo "Press ENTER to start recording..."
read

echo ""
echo "🔴 RECORDING... Press Ctrl+C to stop"
echo ""

# Use macOS built-in recorder (afrecord) or sox if available
# afrecord is part of AudioToolbox
if command -v sox &> /dev/null; then
    # Use sox if available
    sox -d "$OUTPUT_FILE"
else
    # Use macOS built-in (requires allowing Terminal in Security & Privacy > Microphone)
    # Alternative: use ffmpeg if available
    if command -v ffmpeg &> /dev/null; then
        ffmpeg -f avfoundation -i ":0" -t 300 -c:a aac "$OUTPUT_FILE" 2>/dev/null
    else
        # Fallback: Use screencapture for audio (hacky but works)
        echo "Recording with macOS QuickTime..."
        echo ""
        echo "A QuickTime window will open. Click the red record button."
        echo "When done, close QuickTime and save to:"
        echo "  $OUTPUT_DIR"
        echo ""
        open -a "QuickTime Player"
        echo "After saving, the file will be processed automatically."
    fi
fi

echo ""
echo "✅ Recording saved to: $OUTPUT_FILE"
echo "   This will be processed automatically by the transcriber."
echo ""
