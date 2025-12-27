#!/usr/bin/env python3
"""
Database Restore Script

Restores SQLite database from a backup file.
Includes safety checks and verification.

Usage:
    python restore_database.py                    # Interactive: select from available backups
    python restore_database.py backup_file.db    # Restore specific backup
    python restore_database.py --latest          # Restore latest backup
"""

import os
import sys
import shutil
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

# Configuration
SCRIPT_DIR = Path(__file__).parent.parent.parent
DATABASE_PATH = SCRIPT_DIR / "database" / "bensley_master.db"
BACKUP_DIR = SCRIPT_DIR / "backups"

def verify_backup(backup_path: Path) -> bool:
    """Verify backup integrity before restore."""
    print(f"Verifying backup: {backup_path.name}")

    try:
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()

        # Integrity check
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        if result[0] != "ok":
            print(f"  FAILED: Integrity check - {result[0]}")
            return False

        # Check for key tables
        key_tables = ['emails', 'proposals', 'projects']
        for table in key_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count} rows")
            except sqlite3.OperationalError:
                print(f"  WARNING: Table '{table}' not found")

        conn.close()
        return True

    except Exception as e:
        print(f"  FAILED: {e}")
        return False

def list_backups() -> list:
    """List available backups, newest first."""
    if not BACKUP_DIR.exists():
        return []

    backups = sorted(BACKUP_DIR.glob("bensley_*.db"), reverse=True)
    return backups

def display_backups(backups: list):
    """Display list of backups for selection."""
    print(f"\nAvailable backups:\n")
    print(f"  # {'Filename':<35} {'Size':<12} {'Age'}")
    print("  " + "-" * 60)

    for i, backup in enumerate(backups, 1):
        size_mb = backup.stat().st_size / (1024*1024)
        mod_time = datetime.fromtimestamp(backup.stat().st_mtime)
        age = datetime.now() - mod_time

        if age.days > 0:
            age_str = f"{age.days} days ago"
        elif age.seconds > 3600:
            age_str = f"{age.seconds // 3600} hours ago"
        else:
            age_str = f"{age.seconds // 60} min ago"

        print(f"  {i} {backup.name:<35} {size_mb:>8.1f} MB   {age_str}")

def create_pre_restore_backup():
    """Create a backup of current database before restore."""
    if not DATABASE_PATH.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pre_restore_path = BACKUP_DIR / f"pre_restore_{timestamp}.db"

    print(f"Creating pre-restore backup: {pre_restore_path.name}")
    shutil.copy2(DATABASE_PATH, pre_restore_path)
    return pre_restore_path

def restore_database(backup_path: Path, skip_confirmation: bool = False) -> bool:
    """
    Restore database from backup.

    Returns True if successful.
    """
    if not backup_path.exists():
        print(f"ERROR: Backup file not found: {backup_path}")
        return False

    print(f"\n{'='*50}")
    print(f"DATABASE RESTORE")
    print(f"{'='*50}")
    print(f"\nBackup: {backup_path.name}")
    print(f"Size: {backup_path.stat().st_size / (1024*1024):.1f} MB")
    print(f"Target: {DATABASE_PATH}")

    # Verify backup first
    if not verify_backup(backup_path):
        print("\nERROR: Backup verification failed. Aborting restore.")
        return False

    # Confirmation
    if not skip_confirmation:
        if DATABASE_PATH.exists():
            current_size = DATABASE_PATH.stat().st_size / (1024*1024)
            print(f"\nWARNING: This will replace the current database ({current_size:.1f} MB)")

        response = input("\nProceed with restore? (type 'yes' to confirm): ")
        if response.lower() != 'yes':
            print("Restore cancelled.")
            return False

    # Create pre-restore backup
    if DATABASE_PATH.exists():
        pre_restore = create_pre_restore_backup()
        if pre_restore:
            print(f"Pre-restore backup saved: {pre_restore.name}")

    # Perform restore
    print("\nRestoring database...")
    try:
        # Use SQLite backup API for consistency
        source_conn = sqlite3.connect(backup_path)
        target_conn = sqlite3.connect(DATABASE_PATH)

        source_conn.backup(target_conn)

        source_conn.close()
        target_conn.close()

        print("Restore complete!")

        # Verify restored database
        print("\nVerifying restored database...")
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        if result[0] == "ok":
            print("  Integrity check: PASSED")
        else:
            print(f"  WARNING: Integrity check - {result[0]}")

        conn.close()
        return True

    except Exception as e:
        print(f"ERROR: Restore failed - {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="BDS Database Restore")
    parser.add_argument('backup', nargs='?', help="Backup file to restore")
    parser.add_argument('--latest', action='store_true', help="Restore latest backup")
    parser.add_argument('-y', '--yes', action='store_true', help="Skip confirmation prompt")

    args = parser.parse_args()

    backups = list_backups()

    if not backups:
        print("No backups found in backup directory.")
        sys.exit(1)

    if args.latest:
        backup_path = backups[0]
    elif args.backup:
        # Check if it's a path or just a filename
        if os.path.exists(args.backup):
            backup_path = Path(args.backup)
        else:
            backup_path = BACKUP_DIR / args.backup
            if not backup_path.exists():
                print(f"ERROR: Backup not found: {args.backup}")
                sys.exit(1)
    else:
        # Interactive selection
        display_backups(backups)

        try:
            choice = input("\nEnter backup number to restore (or 'q' to quit): ")
            if choice.lower() == 'q':
                print("Cancelled.")
                sys.exit(0)

            index = int(choice) - 1
            if 0 <= index < len(backups):
                backup_path = backups[index]
            else:
                print("Invalid selection.")
                sys.exit(1)

        except (ValueError, KeyboardInterrupt):
            print("\nCancelled.")
            sys.exit(0)

    # Perform restore
    success = restore_database(backup_path, skip_confirmation=args.yes)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
