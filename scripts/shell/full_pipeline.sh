#!/bin/bash
# FULL INTELLIGENCE PIPELINE
# Import → Categorize → Index → Learn

echo "================================================================================"
echo "🧠 BENSLEY INTELLIGENCE PIPELINE - FULL RUN"
echo "================================================================================"

# 1. Import emails
echo ""
echo "1️⃣  IMPORTING EMAILS (500 most recent)..."
echo "   This will take 5-10 minutes..."
# (Already running in background)

# Wait a bit for import to start
sleep 10

# 2. Smart email matching & categorization
echo ""
echo "2️⃣  SMART EMAIL MATCHING & CATEGORIZATION..."
echo "   Analyzing email content..."
echo "   Linking to projects..."
echo "   Categorizing by type (RFI, Invoice, Proposal, etc.)..."
python3 smart_email_matcher.py &
MATCHER_PID=$!

# 3. Document indexing
echo ""
echo "3️⃣  DOCUMENT INDEXING..."
echo "   Indexing PDF attachments..."
echo "   Extracting text from documents..."
echo "   Building searchable index..."
python3 document_indexer.py &
INDEXER_PID=$!

# 4. Wait for processes
echo ""
echo "⏳ Waiting for all processes to complete..."
wait $MATCHER_PID
echo "   ✅ Email matching complete"
wait $INDEXER_PID
echo "   ✅ Document indexing complete"

# 5. Training data export
echo ""
echo "4️⃣  EXPORTING TRAINING DATA..."
python3 export_training_data.py

# 6. Final stats
echo ""
echo "================================================================================"
echo "📊 PIPELINE COMPLETE - STATS"
echo "================================================================================"

sqlite3 database/bensley_master.db << 'SQL'
SELECT
    'Emails' as type,
    COUNT(*) as count
FROM emails
UNION ALL
SELECT
    'Documents',
    COUNT(*)
FROM documents
UNION ALL
SELECT
    'Proposals',
    COUNT(*)
FROM proposals
UNION ALL
SELECT
    'Projects',
    COUNT(*)
FROM projects;
SQL

echo ""
echo "================================================================================"
echo "✅ READY FOR QUERIES!"
echo "================================================================================"
echo ""
echo "Try:"
echo "  python3 bensley_brain.py 'show me emails about BK-070'"
echo "  python3 bensley_brain.py 'which proposals need follow-up?'"
echo "  python3 bensley_brain.py 'find documents about Bali project'"
echo ""
echo "================================================================================"
