#!/usr/bin/env python3
"""
Database Migration Script
=========================

Migrate from split databases to unified master database.

STRATEGY:
1. Copy Desktop DB (master with all features) → OneDrive location
2. Apply schema improvements from old OneDrive → new master
3. Migrate unique emails from old OneDrive → new master
4. Verify data integrity
5. Archive old databases

SAFETY:
- Creates backups before any changes
- Validates data at each step
- Can be re-run safely (idempotent)
"""

import sqlite3
import os
import shutil
from datetime import datetime
from typing import Dict, List, Tuple

DESKTOP_DB = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
OLD_ONEDRIVE_DB = "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/bensley_master.db"
NEW_MASTER_DB = "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/bensley_master_MIGRATED.db"
BACKUP_DIR = "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/backups"

class DatabaseMigration:
    def __init__(self):
        self.desktop_conn = None
        self.old_onedrive_conn = None
        self.new_master_conn = None

    def validate_source_databases(self) -> bool:
        """Ensure source databases exist and are valid"""
        print("\n" + "="*80)
        print("STEP 1: VALIDATING SOURCE DATABASES")
        print("="*80)

        if not os.path.exists(DESKTOP_DB):
            print(f"❌ Desktop database not found: {DESKTOP_DB}")
            return False

        if not os.path.exists(OLD_ONEDRIVE_DB):
            print(f"❌ OneDrive database not found: {OLD_ONEDRIVE_DB}")
            return False

        # Check sizes
        desktop_size = os.path.getsize(DESKTOP_DB) / (1024*1024)
        onedrive_size = os.path.getsize(OLD_ONEDRIVE_DB) / (1024*1024)

        print(f"✅ Desktop DB: {desktop_size:.1f}MB")
        print(f"✅ OneDrive DB: {onedrive_size:.1f}MB")

        return True

    def create_backup(self) -> bool:
        """Backup both source databases"""
        print("\n" + "="*80)
        print("STEP 2: CREATING BACKUPS")
        print("="*80)

        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            # Backup Desktop
            desktop_backup = f"{BACKUP_DIR}/desktop_bensley_master_{timestamp}.db"
            shutil.copy2(DESKTOP_DB, desktop_backup)
            print(f"✅ Backed up Desktop → {desktop_backup}")

            # Backup OneDrive
            onedrive_backup = f"{BACKUP_DIR}/onedrive_bensley_master_{timestamp}.db"
            shutil.copy2(OLD_ONEDRIVE_DB, onedrive_backup)
            print(f"✅ Backed up OneDrive → {onedrive_backup}")

            return True
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False

    def copy_desktop_to_master(self) -> bool:
        """Copy Desktop database to new master location"""
        print("\n" + "="*80)
        print("STEP 3: COPYING DESKTOP → NEW MASTER")
        print("="*80)

        try:
            shutil.copy2(DESKTOP_DB, NEW_MASTER_DB)
            size = os.path.getsize(NEW_MASTER_DB) / (1024*1024)
            print(f"✅ Copied Desktop database → {NEW_MASTER_DB}")
            print(f"   Size: {size:.1f}MB")
            return True
        except Exception as e:
            print(f"❌ Copy failed: {e}")
            return False

    def apply_schema_improvements(self) -> bool:
        """Apply schema improvements from OneDrive to new master"""
        print("\n" + "="*80)
        print("STEP 4: APPLYING SCHEMA IMPROVEMENTS")
        print("="*80)

        try:
            self.new_master_conn = sqlite3.connect(NEW_MASTER_DB)
            cursor = self.new_master_conn.cursor()

            # 1. Add date_normalized column to emails if not exists
            cursor.execute("PRAGMA table_info(emails)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'date_normalized' not in columns:
                print("📝 Adding date_normalized column to emails...")
                cursor.execute("ALTER TABLE emails ADD COLUMN date_normalized TEXT")
                self.new_master_conn.commit()
                print("✅ Added date_normalized column")
            else:
                print("✅ date_normalized column already exists")

            # 2. Create new tables from OneDrive if they don't exist
            self.old_onedrive_conn = sqlite3.connect(OLD_ONEDRIVE_DB)
            old_cursor = self.old_onedrive_conn.cursor()

            # Get CREATE TABLE statements for OneDrive-specific tables
            old_cursor.execute("""
                SELECT name, sql FROM sqlite_master
                WHERE type='table'
                AND name IN ('ai_observations', 'data_sources_catalog', 'contract_phases')
            """)

            for table_name, create_sql in old_cursor.fetchall():
                if create_sql:
                    # Check if table exists in new master
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                    if not cursor.fetchone():
                        print(f"📝 Creating table {table_name}...")
                        cursor.execute(create_sql)
                        self.new_master_conn.commit()
                        print(f"✅ Created {table_name}")
                    else:
                        print(f"✅ {table_name} already exists")

            return True

        except Exception as e:
            print(f"❌ Schema update failed: {e}")
            return False

    def migrate_unique_emails(self) -> Tuple[int, int]:
        """Migrate emails from OneDrive that don't exist in new master"""
        print("\n" + "="*80)
        print("STEP 5: MIGRATING UNIQUE EMAILS")
        print("="*80)

        try:
            new_cursor = self.new_master_conn.cursor()
            old_cursor = self.old_onedrive_conn.cursor()

            # Find emails in OneDrive that aren't in Desktop (by email_id)
            old_cursor.execute("SELECT email_id FROM emails")
            old_email_ids = set(row[0] for row in old_cursor.fetchall())

            new_cursor.execute("SELECT email_id FROM emails")
            new_email_ids = set(row[0] for row in new_cursor.fetchall())

            unique_to_onedrive = old_email_ids - new_email_ids

            print(f"📊 OneDrive has {len(old_email_ids)} emails")
            print(f"📊 Desktop has {len(new_email_ids)} emails")
            print(f"📊 Unique to OneDrive: {len(unique_to_onedrive)}")

            if len(unique_to_onedrive) == 0:
                print("✅ No unique emails to migrate")
                return 0, 0

            # Get column names from emails table
            old_cursor.execute("PRAGMA table_info(emails)")
            columns = [col[1] for col in old_cursor.fetchall()]

            # Filter out columns that might not exist in new master
            new_cursor.execute("PRAGMA table_info(emails)")
            new_columns = [col[1] for col in new_cursor.fetchall()]
            common_columns = [col for col in columns if col in new_columns]

            print(f"📝 Migrating {len(unique_to_onedrive)} emails...")

            migrated = 0
            failed = 0

            for email_id in unique_to_onedrive:
                try:
                    # Get email data from OneDrive
                    old_cursor.execute(f"""
                        SELECT {', '.join(common_columns)}
                        FROM emails
                        WHERE email_id = ?
                    """, (email_id,))

                    email_data = old_cursor.fetchone()

                    if email_data:
                        # Insert into new master
                        placeholders = ', '.join(['?' for _ in common_columns])
                        new_cursor.execute(f"""
                            INSERT INTO emails ({', '.join(common_columns)})
                            VALUES ({placeholders})
                        """, email_data)
                        migrated += 1

                except Exception as e:
                    print(f"⚠️  Failed to migrate email {email_id}: {e}")
                    failed += 1

            self.new_master_conn.commit()

            print(f"✅ Migrated {migrated} emails")
            if failed > 0:
                print(f"⚠️  Failed to migrate {failed} emails")

            return migrated, failed

        except Exception as e:
            print(f"❌ Email migration failed: {e}")
            return 0, 0

    def migrate_contract_phases(self) -> int:
        """Migrate contract phases from OneDrive"""
        print("\n" + "="*80)
        print("STEP 6: MIGRATING CONTRACT PHASES")
        print("="*80)

        try:
            new_cursor = self.new_master_conn.cursor()
            old_cursor = self.old_onedrive_conn.cursor()

            # Check if table exists in OneDrive
            old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contract_phases'")
            if not old_cursor.fetchone():
                print("ℹ️  No contract_phases table in OneDrive")
                return 0

            # Check if table exists in new master
            new_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contract_phases'")
            if not new_cursor.fetchone():
                print("⚠️  contract_phases table doesn't exist in master")
                return 0

            # Get all contract phases from OneDrive
            old_cursor.execute("SELECT * FROM contract_phases")
            phases = old_cursor.fetchall()

            if not phases:
                print("ℹ️  No contract phases to migrate")
                return 0

            # Get column count
            old_cursor.execute("PRAGMA table_info(contract_phases)")
            col_count = len(old_cursor.fetchall())

            migrated = 0
            for phase in phases:
                placeholders = ', '.join(['?' for _ in range(col_count)])
                new_cursor.execute(f"INSERT OR REPLACE INTO contract_phases VALUES ({placeholders})", phase)
                migrated += 1

            self.new_master_conn.commit()
            print(f"✅ Migrated {migrated} contract phases")

            return migrated

        except Exception as e:
            print(f"❌ Contract phase migration failed: {e}")
            return 0

    def verify_migration(self) -> bool:
        """Verify migration was successful"""
        print("\n" + "="*80)
        print("STEP 7: VERIFYING MIGRATION")
        print("="*80)

        try:
            new_cursor = self.new_master_conn.cursor()

            # Count emails
            new_cursor.execute("SELECT COUNT(*) FROM emails")
            email_count = new_cursor.fetchone()[0]

            # Count proposals
            new_cursor.execute("SELECT COUNT(*) FROM proposals")
            proposal_count = new_cursor.fetchone()[0]

            # Count invoices
            new_cursor.execute("SELECT COUNT(*) FROM invoices")
            invoice_count = new_cursor.fetchone()[0]

            # Count projects
            new_cursor.execute("SELECT COUNT(*) FROM projects")
            project_count = new_cursor.fetchone()[0]

            # Check for date_normalized column
            new_cursor.execute("PRAGMA table_info(emails)")
            columns = [col[1] for col in new_cursor.fetchall()]
            has_date_normalized = 'date_normalized' in columns

            print(f"📊 New Master Database Stats:")
            print(f"   Emails: {email_count}")
            print(f"   Proposals: {proposal_count}")
            print(f"   Invoices: {invoice_count}")
            print(f"   Projects: {project_count}")
            print(f"   Has date_normalized: {'✅' if has_date_normalized else '❌'}")

            # Basic validation
            if email_count < 3000:
                print(f"⚠️  Warning: Only {email_count} emails (expected ~3,300+)")
                return False

            if proposal_count < 80:
                print(f"⚠️  Warning: Only {proposal_count} proposals (expected ~87)")
                return False

            print("✅ Migration verification passed!")
            return True

        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False

    def finalize_migration(self) -> bool:
        """Replace old database with new master"""
        print("\n" + "="*80)
        print("STEP 8: FINALIZING MIGRATION")
        print("="*80)

        try:
            # Close connections
            if self.new_master_conn:
                self.new_master_conn.close()
            if self.old_onedrive_conn:
                self.old_onedrive_conn.close()

            # Move old OneDrive to backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            old_backup = f"{BACKUP_DIR}/old_onedrive_master_{timestamp}.db"
            shutil.move(OLD_ONEDRIVE_DB, old_backup)
            print(f"✅ Archived old OneDrive DB → {old_backup}")

            # Move new master to production location
            shutil.move(NEW_MASTER_DB, OLD_ONEDRIVE_DB)
            print(f"✅ New master → {OLD_ONEDRIVE_DB}")

            return True

        except Exception as e:
            print(f"❌ Finalization failed: {e}")
            return False

    def run(self):
        """Execute full migration"""
        print("\n" + "="*80)
        print("DATABASE MIGRATION STARTING")
        print("="*80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Step 1: Validate
        if not self.validate_source_databases():
            print("\n❌ MIGRATION ABORTED: Source validation failed")
            return False

        # Step 2: Backup
        if not self.create_backup():
            print("\n❌ MIGRATION ABORTED: Backup failed")
            return False

        # Step 3: Copy Desktop to new master
        if not self.copy_desktop_to_master():
            print("\n❌ MIGRATION ABORTED: Copy failed")
            return False

        # Step 4: Apply schema improvements
        if not self.apply_schema_improvements():
            print("\n❌ MIGRATION ABORTED: Schema update failed")
            return False

        # Step 5: Migrate unique emails
        migrated, failed = self.migrate_unique_emails()

        # Step 6: Migrate contract phases
        phases_migrated = self.migrate_contract_phases()

        # Step 7: Verify
        if not self.verify_migration():
            print("\n⚠️  MIGRATION WARNING: Verification failed")
            print("New database created but not moved to production")
            print(f"Review: {NEW_MASTER_DB}")
            return False

        # Step 8: Finalize
        print("\n" + "="*80)
        print("READY TO FINALIZE")
        print("="*80)
        print(f"This will:")
        print(f"  1. Archive old OneDrive DB")
        print(f"  2. Move new master to production location")
        print(f"\nAll backups are in: {BACKUP_DIR}")

        response = input("\nProceed with finalization? (yes/no): ").strip().lower()

        if response == 'yes':
            if self.finalize_migration():
                print("\n" + "="*80)
                print("✅ MIGRATION COMPLETE!")
                print("="*80)
                print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"\nBackups saved in: {BACKUP_DIR}")
                print(f"Production database: {OLD_ONEDRIVE_DB}")
                return True
            else:
                print("\n❌ FINALIZATION FAILED")
                return False
        else:
            print("\n⚠️  FINALIZATION CANCELLED")
            print(f"New database ready for review at: {NEW_MASTER_DB}")
            return False

if __name__ == '__main__':
    migration = DatabaseMigration()
    success = migration.run()
    exit(0 if success else 1)
