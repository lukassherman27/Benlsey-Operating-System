#!/bin/bash
#
# Bensley Operations Platform - Database Backup Script
#
# Creates a timestamped backup of the SQLite database.
# Intended to run via cron daily.
#
# Usage:
#   bash scripts/deploy/backup-db.sh
#
# Cron setup (daily at 2 AM):
#   crontab -e
#   0 2 * * * /home/bensley/bensley-operating-system/scripts/deploy/backup-db.sh
#

set -e

# Configuration
PROJECT_DIR="${PROJECT_DIR:-/home/bensley/bensley-operating-system}"
BACKUP_DIR="${BACKUP_DIR:-/home/bensley/backups}"
DB_PATH="$PROJECT_DIR/database/bensley_master.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=14  # Keep backups for 14 days

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Check database exists
if [ ! -f "$DB_PATH" ]; then
    echo "[ERROR] Database not found: $DB_PATH"
    exit 1
fi

# Create backup using SQLite online backup (safe for active database)
BACKUP_FILE="$BACKUP_DIR/bensley_master_$TIMESTAMP.db"

sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"

if [ -f "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "[BACKUP] Created: $BACKUP_FILE ($SIZE)"
else
    echo "[ERROR] Backup failed"
    exit 1
fi

# Compress backup (optional, saves space)
gzip "$BACKUP_FILE"
echo "[BACKUP] Compressed: ${BACKUP_FILE}.gz"

# Clean up old backups
find "$BACKUP_DIR" -name "bensley_master_*.db.gz" -mtime +$KEEP_DAYS -delete
echo "[BACKUP] Cleaned up backups older than $KEEP_DAYS days"

# Summary
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "bensley_master_*.db.gz" | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "[BACKUP] Complete. $BACKUP_COUNT backups, total size: $TOTAL_SIZE"
