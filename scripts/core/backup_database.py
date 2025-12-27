#!/usr/bin/env python3
"""
Database Backup Script

Creates timestamped SQLite database backups and maintains retention policy.
Designed to run via LaunchAgent for automated daily backups.

Usage:
    python backup_database.py           # Create backup
    python backup_database.py --verify  # Verify latest backup integrity
    python backup_database.py --list    # List existing backups
"""

import os
import sys
import shutil
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Configuration
SCRIPT_DIR = Path(__file__).parent.parent.parent
DATABASE_PATH = SCRIPT_DIR / "database" / "bensley_master.db"
BACKUP_DIR = SCRIPT_DIR / "backups"
RETENTION_DAYS = 7

def get_backup_filename() -> str:
    """Generate timestamped backup filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"bensley_{timestamp}.db"

def create_backup() -> Path:
    """
    Create a backup of the SQLite database.

    Uses SQLite's backup API for consistency (not just file copy).
    Returns the path to the created backup.
    """
    if not DATABASE_PATH.exists():
        print(f"ERROR: Database not found at {DATABASE_PATH}")
        sys.exit(1)

    # Ensure backup directory exists
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    backup_filename = get_backup_filename()
    backup_path = BACKUP_DIR / backup_filename

    print(f"Creating backup: {backup_filename}")
    print(f"  Source: {DATABASE_PATH}")
    print(f"  Size: {DATABASE_PATH.stat().st_size / (1024*1024):.1f} MB")

    try:
        # Use SQLite backup API for a consistent backup
        source_conn = sqlite3.connect(DATABASE_PATH)
        backup_conn = sqlite3.connect(backup_path)

        source_conn.backup(backup_conn)

        source_conn.close()
        backup_conn.close()

        backup_size = backup_path.stat().st_size / (1024*1024)
        print(f"  Backup created: {backup_size:.1f} MB")

        return backup_path

    except Exception as e:
        print(f"ERROR: Backup failed - {e}")
        if backup_path.exists():
            backup_path.unlink()
        sys.exit(1)

def verify_backup(backup_path: Path) -> bool:
    """
    Verify backup integrity by running integrity check and basic queries.
    Returns True if backup is valid.
    """
    print(f"Verifying backup: {backup_path.name}")

    try:
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()

        # Integrity check
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        if result[0] != "ok":
            print(f"  FAILED: Integrity check returned {result[0]}")
            return False
        print("  Integrity check: OK")

        # Count tables
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        print(f"  Tables: {table_count}")

        # Verify key tables exist
        key_tables = ['emails', 'proposals', 'projects', 'contacts']
        for table in key_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} rows")

        conn.close()
        print("  Verification: PASSED")
        return True

    except Exception as e:
        print(f"  FAILED: {e}")
        return False

def cleanup_old_backups():
    """Remove backups older than retention period."""
    if not BACKUP_DIR.exists():
        return

    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    removed_count = 0

    for backup_file in BACKUP_DIR.glob("bensley_*.db"):
        try:
            # Parse timestamp from filename: bensley_YYYYMMDD_HHMMSS.db
            filename = backup_file.stem
            timestamp_str = filename.replace("bensley_", "")
            backup_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

            if backup_date < cutoff:
                backup_file.unlink()
                removed_count += 1
                print(f"  Removed old backup: {backup_file.name}")

        except (ValueError, OSError) as e:
            # Skip files that don't match the pattern
            continue

    if removed_count > 0:
        print(f"Cleaned up {removed_count} old backup(s)")

def list_backups():
    """List all existing backups with their sizes and dates."""
    if not BACKUP_DIR.exists():
        print("No backups directory found.")
        return

    backups = sorted(BACKUP_DIR.glob("bensley_*.db"), reverse=True)

    if not backups:
        print("No backups found.")
        return

    print(f"\nExisting backups ({len(backups)} total):\n")
    print(f"{'Filename':<35} {'Size':<12} {'Age'}")
    print("-" * 60)

    for backup in backups:
        size_mb = backup.stat().st_size / (1024*1024)
        mod_time = datetime.fromtimestamp(backup.stat().st_mtime)
        age = datetime.now() - mod_time

        if age.days > 0:
            age_str = f"{age.days} days ago"
        elif age.seconds > 3600:
            age_str = f"{age.seconds // 3600} hours ago"
        else:
            age_str = f"{age.seconds // 60} minutes ago"

        print(f"{backup.name:<35} {size_mb:>8.1f} MB   {age_str}")

def main():
    parser = argparse.ArgumentParser(description="BDS Database Backup")
    parser.add_argument('--verify', action='store_true', help="Verify latest backup")
    parser.add_argument('--list', action='store_true', help="List existing backups")
    parser.add_argument('--no-cleanup', action='store_true', help="Skip cleanup of old backups")

    args = parser.parse_args()

    if args.list:
        list_backups()
        return

    if args.verify:
        backups = sorted(BACKUP_DIR.glob("bensley_*.db"), reverse=True)
        if not backups:
            print("No backups to verify.")
            sys.exit(1)

        latest = backups[0]
        if verify_backup(latest):
            sys.exit(0)
        else:
            sys.exit(1)

    # Default: create backup
    print(f"\n{'='*50}")
    print(f"BDS Database Backup - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    backup_path = create_backup()

    # Verify the new backup
    if not verify_backup(backup_path):
        print("\nWARNING: Backup verification failed!")
        sys.exit(1)

    # Cleanup old backups
    if not args.no_cleanup:
        print(f"\nCleaning up backups older than {RETENTION_DAYS} days...")
        cleanup_old_backups()

    print(f"\nBackup complete: {backup_path.name}")

if __name__ == "__main__":
    main()
