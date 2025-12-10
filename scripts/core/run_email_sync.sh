#!/bin/bash
# Email Sync Wrapper Script
# This script is called by launchd to run the email sync
# It loads the .env file and runs the Python sync script

# Set the project directory (where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Log file for debugging
LOG_FILE="$PROJECT_ROOT/logs/email_sync_launcher.log"
mkdir -p "$PROJECT_ROOT/logs"

echo "========================================" >> "$LOG_FILE"
echo "Email sync started at $(date)" >> "$LOG_FILE"
echo "Project root: $PROJECT_ROOT" >> "$LOG_FILE"

# Change to project directory
cd "$PROJECT_ROOT"

# Load environment variables from .env file
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "Loading .env file" >> "$LOG_FILE"
    # Export all variables from .env
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
else
    echo "WARNING: .env file not found at $PROJECT_ROOT/.env" >> "$LOG_FILE"
fi

# Run the sync script
echo "Running email sync..." >> "$LOG_FILE"
/usr/bin/python3 "$PROJECT_ROOT/scripts/core/scheduled_email_sync.py" 2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=$?
echo "Email sync completed with exit code: $EXIT_CODE at $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

exit $EXIT_CODE
