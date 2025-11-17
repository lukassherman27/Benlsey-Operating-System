#!/bin/bash
# Database Sync Script
# Keeps BDS_SYSTEM (primary) and git repo (backup) databases in sync

PRIMARY_DB="/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
BACKUP_DB="/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/bensley_master.db"

echo "🔄 Syncing databases..."
echo ""

# Check primary exists
if [ ! -f "$PRIMARY_DB" ]; then
    echo "❌ Primary database not found: $PRIMARY_DB"
    exit 1
fi

# Get file sizes
PRIMARY_SIZE=$(du -h "$PRIMARY_DB" | cut -f1)
BACKUP_SIZE=$(du -h "$BACKUP_DB" | cut -f1 2>/dev/null || echo "N/A")

echo "Primary (BDS_SYSTEM):  $PRIMARY_SIZE"
echo "Backup (Git Repo):     $BACKUP_SIZE"
echo ""

# Copy primary to backup
cp "$PRIMARY_DB" "$BACKUP_DB"

if [ $? -eq 0 ]; then
    echo "✅ Database synced successfully!"
    echo ""

    # Show record counts
    echo "📊 Record counts:"
    sqlite3 "$PRIMARY_DB" "
        SELECT 'Proposals: ' || COUNT(*) FROM proposals;
        SELECT 'Emails: ' || COUNT(*) FROM emails;
        SELECT 'Documents: ' || COUNT(*) FROM documents;
        SELECT 'Email Content: ' || COUNT(*) FROM email_content;
    "
else
    echo "❌ Sync failed!"
    exit 1
fi
