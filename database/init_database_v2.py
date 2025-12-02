#!/usr/bin/env python3
"""
Initialize Bensley Intelligence Platform Database (v2)

Modern database initialization using canonical schema and migrations.

Usage:
    python3 database/init_database_v2.py                 # Create new database
    python3 database/init_database_v2.py --fresh          # Drop and recreate
    python3 database/init_database_v2.py --db custom.db   # Custom location
"""

import sqlite3
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class DatabaseInitializer:
    def __init__(self, db_path=None, fresh=False):
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', '~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db')

        self.db_path = Path(db_path).expanduser()
        self.fresh = fresh
        self.project_root = Path(__file__).parent.parent
        self.schema_file = self.project_root / 'database/schema/bensley_master_schema.sql'
        self.migrate_script = self.project_root / 'database/migrate.py'

    def initialize(self):
        """Initialize the database"""
        print("="*80)
        print("🏗️  INITIALIZING BENSLEY INTELLIGENCE PLATFORM DATABASE")
        print("="*80)
        print(f"Database: {self.db_path}")
        print(f"Schema: {self.schema_file}")
        print()

        # Check if database exists
        if self.db_path.exists():
            if self.fresh:
                print("⚠️  Fresh mode: Dropping existing database")
                self.db_path.unlink()
            else:
                print("❌ Database already exists!")
                print(f"   {self.db_path}")
                print("\nOptions:")
                print("  1. Use --fresh to drop and recreate")
                print("  2. Use database/migrate.py to update existing database")
                print("  3. Use different --db path")
                sys.exit(1)

        # Create directory if needed
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Verify schema file exists
        if not self.schema_file.exists():
            print(f"❌ Schema file not found: {self.schema_file}")
            print("\n   Run this first:")
            print(f"   sqlite3 ~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db \".schema\" > {self.schema_file}")
            sys.exit(1)

        print("📄 Step 1: Creating database structure from canonical schema...")
        self._apply_schema()

        print("\n📄 Step 2: Running migrations...")
        self._run_migrations()

        print("\n✅ Database initialized successfully!")
        print(f"\n   Database: {self.db_path}")
        print(f"   Tables: {self._count_tables()}")
        print(f"   Indexes: {self._count_indexes()}")
        print("\n" + "="*80)
        print("NEXT STEPS:")
        print("="*80)
        print("1. Import proposals:")
        print("   python3 backend/core/migrate_proposals.py")
        print("\n2. Import emails:")
        print("   python3 smart_email_matcher.py <database_path>")
        print("\n3. Index documents:")
        print("   python3 document_indexer.py <database_path> <files_path>")
        print("\n4. Start API:")
        print("   python3 backend/api/main.py")
        print("="*80 + "\n")

    def _apply_schema(self):
        """Apply canonical schema to new database"""
        # Read schema file
        with open(self.schema_file, 'r') as f:
            schema_sql = f.read()

        # Create database and apply schema
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Execute schema (split by semicolons)
            statements = schema_sql.split(';')
            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    cursor.execute(statement)

            conn.commit()
            print(f"   ✅ Schema applied: {len(statements)} statements")

        except Exception as e:
            print(f"   ❌ Schema failed: {e}")
            conn.close()
            if self.db_path.exists():
                self.db_path.unlink()
            sys.exit(1)

        finally:
            conn.close()

    def _run_migrations(self):
        """Run database migrations"""
        if not self.migrate_script.exists():
            print(f"   ⚠️  Migration script not found: {self.migrate_script}")
            print("   Skipping migrations")
            return

        import subprocess

        try:
            result = subprocess.run(
                ['python3', str(self.migrate_script), '--db', str(self.db_path)],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # Check if any migrations were applied
                if "pending" in result.stdout.lower():
                    print(f"   ⚠️  Some migrations pending")
                else:
                    print(f"   ✅ All migrations applied")
            else:
                print(f"   ⚠️  Migration warning: {result.stderr}")

        except Exception as e:
            print(f"   ⚠️  Could not run migrations: {e}")
            print("   You can run them manually later:")
            print(f"   python3 {self.migrate_script}")

    def _count_tables(self):
        """Count tables in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def _count_indexes(self):
        """Count indexes in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
        count = cursor.fetchone()[0]
        conn.close()
        return count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Initialize Bensley Intelligence Platform Database'
    )
    parser.add_argument(
        '--db',
        help='Database path (defaults to DATABASE_PATH from .env)'
    )
    parser.add_argument(
        '--fresh',
        action='store_true',
        help='Drop existing database and recreate (DESTRUCTIVE!)'
    )

    args = parser.parse_args()

    initializer = DatabaseInitializer(db_path=args.db, fresh=args.fresh)
    initializer.initialize()
