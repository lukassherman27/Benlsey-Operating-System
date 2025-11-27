#!/bin/bash
#
# Voice Memo Transcriber - Installer
# Run this on Bill's Mac to set up automatic transcription
#
# Usage: ./install.sh
#

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Voice Memo Transcriber - Installation                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INSTALL_DIR="$HOME/VoiceTranscriber"
LAUNCHAGENT_DIR="$HOME/Library/LaunchAgents"
PLIST_NAME="com.bensley.voice-transcriber.plist"

echo "This will install the Voice Memo Transcriber to: $INSTALL_DIR"
echo ""

# Check for Python 3
echo "Checking Python 3..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    echo "   Please install Python 3 first:"
    echo "   1. Go to https://www.python.org/downloads/"
    echo "   2. Download and install Python 3.11+"
    exit 1
fi
PYTHON_PATH=$(which python3)
echo "✅ Found Python 3 at: $PYTHON_PATH"

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "   Version: $PYTHON_VERSION"

# Create installation directory
echo ""
echo "Creating installation directory..."
mkdir -p "$INSTALL_DIR"

# Copy files
echo "Copying files..."
cp "$SCRIPT_DIR/transcriber.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/config.py" "$INSTALL_DIR/"

# Create output directory
echo "Creating output directories..."
mkdir -p "$HOME/Documents/Meeting Transcripts"

# Install Python dependencies
echo ""
echo "Installing Python packages..."
pip3 install --upgrade openai anthropic --quiet

# Create LaunchAgent directory if needed
mkdir -p "$LAUNCHAGENT_DIR"

# Create LaunchAgent plist with correct paths
echo "Setting up auto-start..."
cat > "$LAUNCHAGENT_DIR/$PLIST_NAME" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.bensley.voice-transcriber</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$INSTALL_DIR/transcriber.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$INSTALL_DIR/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$INSTALL_DIR/stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
EOF

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     IMPORTANT: Configuration Required                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Before starting, you MUST configure the API keys."
echo ""
echo "1. Open the config file:"
echo "   open $INSTALL_DIR/config.py"
echo ""
echo "2. Add your API keys:"
echo "   - OPENAI_API_KEY = \"sk-...\"     (from platform.openai.com)"
echo "   - ANTHROPIC_API_KEY = \"sk-...\"  (from console.anthropic.com)"
echo ""
echo "3. (Optional) Configure email settings for notifications"
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Starting the Service                                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "After configuring, start the service with:"
echo ""
echo "   launchctl load $LAUNCHAGENT_DIR/$PLIST_NAME"
echo ""
echo "To stop the service:"
echo ""
echo "   launchctl unload $LAUNCHAGENT_DIR/$PLIST_NAME"
echo ""
echo "To check status:"
echo ""
echo "   python3 $INSTALL_DIR/transcriber.py --status"
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Installation Complete!                                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Files installed to: $INSTALL_DIR"
echo "Transcripts will be saved to: $HOME/Documents/Meeting Transcripts"
echo ""
echo "Once configured, the service will automatically transcribe"
echo "any new Voice Memos that sync from Bill's iPhone."
echo ""
