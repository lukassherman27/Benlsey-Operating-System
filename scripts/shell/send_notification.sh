#!/bin/bash
# macOS notification with report opening

REPORT_HTML="$1"
TITLE="$2"
MESSAGE="$3"

# Send macOS notification
osascript -e "display notification \"$MESSAGE\" with title \"$TITLE\" sound name \"Glass\""

# Wait a moment
sleep 1

# Auto-open the HTML report in default browser
if [ -f "$REPORT_HTML" ]; then
    open "$REPORT_HTML"
fi
