#!/bin/bash
# DAILY AUTOMATION WORKFLOW
# Run this every morning via cron to keep proposals automated

echo "================================================================================"
echo "🌅 BENSLEY DAILY AUTOMATION - $(date '+%Y-%m-%d %H:%M')"
echo "================================================================================"

# 1. Import new emails (checks every folder)
echo ""
echo "1️⃣  Checking for new emails..."
python3 import_all_emails.py

# 2. Categorize & link emails to projects
echo ""
echo "2️⃣  Categorizing emails & linking to projects..."
python3 smart_email_matcher.py

# 3. Index new documents
echo ""
echo "3️⃣  Indexing new documents..."
python3 document_indexer.py

# 4. Generate AI suggestions
echo ""
echo "4️⃣  Generating AI suggestions..."
python3 proposal_automation_engine.py

# 5. Update proposal health scores
echo ""
echo "5️⃣  Updating proposal health scores..."
python3 proposal_health_monitor.py

# 6. Export training data (if needed)
echo ""
echo "6️⃣  Exporting training data..."
python3 export_training_data.py

echo ""
echo "================================================================================"
echo "✅ DAILY AUTOMATION COMPLETE"
echo "================================================================================"
echo ""
echo "📊 View your dashboard: http://localhost:3002"
echo "💡 Review AI suggestions: python3 review_suggestions.py"
echo "🧠 Query anything: python3 bensley_brain.py 'your question'"
echo ""
