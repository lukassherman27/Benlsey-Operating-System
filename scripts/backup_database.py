#!/usr/bin/env python3
"""
Database Backup Script

Creates timestamped backups of the SQLite database.
Keeps the last N backups and removes older ones.

Usage:
    python scripts/backup_database.py

Configuration:
    BACKUP_DIR: Where to store backups (default: database/backups)
    MAX_BACKUPS: Maximum backups to keep (default: 30)

Schedule with cron (daily at 2am):
    0 2 * * * cd /path/to/project && python scripts/backup_database.py

Or with launchd on macOS (see scripts/com.bensley.db-backup.plist)
"""

import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bensley_master.db"
BACKUP_DIR = PROJECT_ROOT / "database" / "backups"
MAX_BACKUPS = 30  # Keep last 30 backups


def create_backup():
    """Create a timestamped backup of the database."""
    # Create backup directory if it doesn't exist
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"bensley_master_{timestamp}.db"
    backup_path = BACKUP_DIR / backup_name

    print(f"Creating backup: {backup_name}")

    # Use SQLite's backup API for a consistent copy
    # This is safer than shutil.copy for an active database
    source = sqlite3.connect(str(DB_PATH))
    dest = sqlite3.connect(str(backup_path))

    source.backup(dest)

    source.close()
    dest.close()

    # Verify the backup
    backup_conn = sqlite3.connect(str(backup_path))
    cursor = backup_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sqlite_master")
    table_count = cursor.fetchone()[0]
    backup_conn.close()

    print(f"Backup created: {backup_path}")
    print(f"Verified: {table_count} objects in backup")

    # Get file size
    size_mb = backup_path.stat().st_size / (1024 * 1024)
    print(f"Size: {size_mb:.2f} MB")

    return backup_path


def cleanup_old_backups():
    """Remove old backups, keeping only the most recent MAX_BACKUPS."""
    if not BACKUP_DIR.exists():
        return

    # Get all backup files, sorted by modification time (newest first)
    backups = sorted(
        BACKUP_DIR.glob("bensley_master_*.db"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    if len(backups) <= MAX_BACKUPS:
        print(f"Total backups: {len(backups)} (under limit of {MAX_BACKUPS})")
        return

    # Remove old backups
    old_backups = backups[MAX_BACKUPS:]
    print(f"Removing {len(old_backups)} old backups...")

    for backup in old_backups:
        print(f"  Removing: {backup.name}")
        backup.unlink()

    print(f"Kept {MAX_BACKUPS} most recent backups")


def get_backup_stats():
    """Get statistics about existing backups."""
    if not BACKUP_DIR.exists():
        return {"count": 0, "total_size_mb": 0, "oldest": None, "newest": None}

    backups = sorted(
        BACKUP_DIR.glob("bensley_master_*.db"),
        key=lambda f: f.stat().st_mtime
    )

    if not backups:
        return {"count": 0, "total_size_mb": 0, "oldest": None, "newest": None}

    total_size = sum(f.stat().st_size for f in backups)

    return {
        "count": len(backups),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "oldest": backups[0].name,
        "newest": backups[-1].name
    }


def main():
    print("=" * 60)
    print("Database Backup")
    print("=" * 60)
    print(f"Source: {DB_PATH}")
    print(f"Destination: {BACKUP_DIR}")
    print(f"Max backups: {MAX_BACKUPS}")
    print()

    # Check source exists
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        return 1

    # Show current stats
    stats = get_backup_stats()
    print(f"Current backups: {stats['count']}")
    if stats['count'] > 0:
        print(f"Total size: {stats['total_size_mb']} MB")
        print(f"Oldest: {stats['oldest']}")
        print(f"Newest: {stats['newest']}")
    print()

    # Create backup
    try:
        backup_path = create_backup()
    except Exception as e:
        print(f"ERROR: Backup failed: {e}")
        return 1

    print()

    # Cleanup old backups
    cleanup_old_backups()

    print()
    print("=" * 60)
    print("Backup complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
