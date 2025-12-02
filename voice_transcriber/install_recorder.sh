#!/bin/bash
#
# Meeting Recorder - One-Click Installer for Bill's Mac
#
# This installs the meeting recorder menu bar app.
# Records meetings and saves to shared OneDrive folder.
#
# Usage: ./install_recorder.sh
#

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Meeting Recorder - Installation                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INSTALL_DIR="$HOME/MeetingRecorder"
LAUNCHAGENT_DIR="$HOME/Library/LaunchAgents"
PLIST_NAME="com.bensley.meeting-recorder.plist"

# Check Python
echo "Checking Python 3..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    echo "   Download from: https://www.python.org/downloads/"
    exit 1
fi
PYTHON_PATH=$(which python3)
echo "✅ Found: $PYTHON_PATH"

# Create install directory
echo ""
echo "Installing to: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# Copy recorder script
cp "$SCRIPT_DIR/meeting_recorder.py" "$INSTALL_DIR/"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install --upgrade pyaudio rumps --quiet 2>/dev/null || {
    echo "⚠️  Some dependencies may need manual install"
    echo "   Run: pip3 install pyaudio rumps"
}

# Create recordings folder
# TODO: Update this path once Bensley OneDrive is set up
RECORDINGS_FOLDER="$HOME/Library/CloudStorage/OneDrive-Personal/Bensley/Voice Memos/Incoming"
mkdir -p "$RECORDINGS_FOLDER"
echo "✅ Recordings folder: $RECORDINGS_FOLDER"

# Create LaunchAgent for auto-start (optional)
echo ""
read -p "Auto-start recorder on login? (y/n): " AUTO_START

if [[ "$AUTO_START" == "y" || "$AUTO_START" == "Y" ]]; then
    mkdir -p "$LAUNCHAGENT_DIR"

    cat > "$LAUNCHAGENT_DIR/$PLIST_NAME" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.bensley.meeting-recorder</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$INSTALL_DIR/meeting_recorder.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
EOF

    echo "✅ Will auto-start on login"
fi

# Create desktop shortcut
echo ""
read -p "Create Desktop shortcut? (y/n): " DESKTOP_SHORTCUT

if [[ "$DESKTOP_SHORTCUT" == "y" || "$DESKTOP_SHORTCUT" == "Y" ]]; then
    # Create a simple app launcher
    SHORTCUT="$HOME/Desktop/Meeting Recorder.command"
    cat > "$SHORTCUT" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
python3 meeting_recorder.py &
disown
exit
EOF
    chmod +x "$SHORTCUT"
    echo "✅ Created: ~/Desktop/Meeting Recorder.command"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Installation Complete!                                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "To start recording:"
echo ""
echo "  1. Run:  python3 $INSTALL_DIR/meeting_recorder.py"
echo "  2. Look for 🎙️ in your menu bar"
echo "  3. Click to start/stop recording"
echo ""
echo "Recordings save to:"
echo "  $RECORDINGS_FOLDER"
echo ""
echo "These will sync automatically to Lukas's system!"
echo ""

# Offer to start now
read -p "Start Meeting Recorder now? (y/n): " START_NOW

if [[ "$START_NOW" == "y" || "$START_NOW" == "Y" ]]; then
    echo ""
    echo "Starting Meeting Recorder..."
    python3 "$INSTALL_DIR/meeting_recorder.py" &
    disown
    echo "✅ Look for 🎙️ in your menu bar!"
fi

echo ""
echo "Done!"
echo ""
