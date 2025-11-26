#!/bin/bash
# Setup cron job to run Daily Accountability System at 9 PM every day

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_PATH=$(which python3)
CRON_COMMAND="0 21 * * * cd $SCRIPT_DIR && $PYTHON_PATH $SCRIPT_DIR/daily_accountability_system.py >> $SCRIPT_DIR/logs/daily_accountability.log 2>&1"

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🔧 DAILY ACCOUNTABILITY SYSTEM - CRON JOB SETUP"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "This will set up a cron job to run the Daily Accountability System"
echo "every day at 9:00 PM."
echo ""
echo "The cron job will:"
echo "  • Take a snapshot of the system state"
echo "  • Run the Daily Summary Agent"
echo "  • Run the Critical Auditor Agent"
echo "  • Generate HTML and PDF reports"
echo "  • Email the reports to lukas@bensley.com"
echo ""
echo "Cron command:"
echo "  $CRON_COMMAND"
echo ""

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Check if cron job already exists
EXISTING=$(crontab -l 2>/dev/null | grep "daily_accountability_system.py" | wc -l)

if [ "$EXISTING" -gt 0 ]; then
    echo "⚠️  WARNING: Cron job already exists!"
    echo ""
    echo "Current crontab entries for daily_accountability_system.py:"
    crontab -l 2>/dev/null | grep "daily_accountability_system.py"
    echo ""
    read -p "Do you want to replace it? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Cancelled. No changes made."
        exit 1
    fi

    # Remove old entry
    crontab -l 2>/dev/null | grep -v "daily_accountability_system.py" | crontab -
    echo "   ✅ Removed old cron job"
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

echo "✅ Cron job installed successfully!"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "📋 VERIFICATION"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Your current crontab:"
crontab -l
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "🧪 TEST THE SYSTEM"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "To test the system manually, run:"
echo "  cd $SCRIPT_DIR"
echo "  python3 daily_accountability_system.py"
echo ""
echo "Reports will be saved to:"
echo "  $SCRIPT_DIR/reports/daily/"
echo ""
echo "Logs will be saved to:"
echo "  $SCRIPT_DIR/logs/daily_accountability.log"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "📧 EMAIL CONFIGURATION"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Make sure your .env file has the correct email settings:"
echo "  EMAIL_SERVER=tmail.bensley.com"
echo "  EMAIL_PORT=587"
echo "  EMAIL_USERNAME=lukas@bensley.com"
echo "  EMAIL_PASSWORD=your_password"
echo ""
echo "If email delivery fails, reports will still be saved locally."
echo ""
echo "✅ Setup complete! The system will run automatically at 9 PM every day."
echo ""
