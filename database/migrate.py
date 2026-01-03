#!/usr/bin/env python3
"""
Database Migration Runner

Automatically applies pending migrations and tracks them in schema_migrations table.

Usage:
    python3 database/migrate.py                    # Apply all pending migrations
    python3 database/migrate.py --status           # Show migration status
    python3 database/migrate.py --rollback         # Rollback last migration (if supported)
    python3 database/migrate.py --create "name"    # Create new migration file
"""

import sqlite3
import hashlib
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class MigrationRunner:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', 'database/bensley_master.db')

        self.db_path = Path(db_path).expanduser()
        self.migrations_dir = Path(__file__).parent / 'migrations'

        if not self.db_path.exists():
            print(f"❌ Database not found: {self.db_path}")
            sys.exit(1)

        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Ensure schema_migrations table exists
        self._ensure_migrations_table()

    def _ensure_migrations_table(self):
        """Ensure schema_migrations table exists"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                applied_by TEXT DEFAULT 'migrate.py',
                checksum TEXT,
                execution_time_ms INTEGER
            )
        """)
        self.conn.commit()

    def _get_applied_migrations(self):
        """Get list of applied migration versions"""
        self.cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
        return {row['version'] for row in self.cursor.fetchall()}

    def _get_migration_files(self):
        """Get all migration files"""
        if not self.migrations_dir.exists():
            return []

        migrations = []
        versions_seen = {}  # Track versions to detect duplicates

        for file in sorted(self.migrations_dir.glob('*.sql')):
            # Extract version from filename (e.g., "001_name.sql" -> 1)
            match = re.match(r'(\d+)_(.+)\.sql$', file.name)
            if match:
                version = int(match.group(1))
                name = match.group(2)

                # Check for duplicate version numbers
                if version in versions_seen:
                    print(f"⚠️  DUPLICATE VERSION {version:03d}:")
                    print(f"     - {versions_seen[version]}")
                    print(f"     - {name}")
                    # Skip duplicate, keep first one found (alphabetically)
                    continue

                versions_seen[version] = name
                migrations.append({
                    'version': version,
                    'name': name,
                    'file': file
                })

        return sorted(migrations, key=lambda x: x['version'])

    def _calculate_checksum(self, file_path):
        """Calculate MD5 checksum of migration file"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def status(self):
        """Show migration status"""
        print("="*80)
        print("📊 MIGRATION STATUS")
        print("="*80)
        print(f"Database: {self.db_path}\n")

        applied = self._get_applied_migrations()
        all_migrations = self._get_migration_files()

        if not all_migrations:
            print("❌ No migration files found")
            return

        print(f"{'Ver':<5} {'Status':<10} {'Name':<40} {'Applied':<20}")
        print("-"*80)

        for mig in all_migrations:
            version = mig['version']
            status = "✅ Applied" if version in applied else "⏳ Pending"

            # Get applied date if exists
            applied_date = ""
            if version in applied:
                self.cursor.execute(
                    "SELECT applied_at FROM schema_migrations WHERE version = ?",
                    (version,)
                )
                row = self.cursor.fetchone()
                if row:
                    applied_date = row['applied_at'][:16]  # Truncate timestamp

            print(f"{version:<5} {status:<10} {mig['name']:<40} {applied_date:<20}")

        pending_count = len([m for m in all_migrations if m['version'] not in applied])
        print("-"*80)
        print(f"\n✅ {len(applied)} applied  |  ⏳ {pending_count} pending\n")

    def apply_migration(self, migration):
        """Apply a single migration"""
        version = migration['version']
        name = migration['name']
        file_path = migration['file']

        print(f"  Applying {version:03d}_{name}...")

        # Read migration file
        with open(file_path, 'r') as f:
            sql = f.read()

        # Calculate checksum
        checksum = self._calculate_checksum(file_path)

        # Execute migration
        start_time = datetime.now()
        try:
            # Split on semicolons but be careful with compound statements
            statements = sql.split(';')
            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    self.cursor.execute(statement)

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            # Record migration
            self.cursor.execute("""
                INSERT OR REPLACE INTO schema_migrations
                (version, name, checksum, execution_time_ms, applied_by)
                VALUES (?, ?, ?, ?, ?)
            """, (version, name, checksum, execution_time, 'migrate.py'))

            self.conn.commit()
            print(f"    ✅ Success ({execution_time}ms)")
            return True

        except Exception as e:
            self.conn.rollback()
            print(f"    ❌ Failed: {e}")
            return False

    def migrate(self):
        """Apply all pending migrations"""
        print("="*80)
        print("🚀 RUNNING DATABASE MIGRATIONS")
        print("="*80)
        print(f"Database: {self.db_path}\n")

        applied = self._get_applied_migrations()
        all_migrations = self._get_migration_files()

        pending = [m for m in all_migrations if m['version'] not in applied]

        if not pending:
            print("✅ Database is up to date! No pending migrations.\n")
            return

        print(f"Found {len(pending)} pending migration(s):\n")

        for migration in pending:
            success = self.apply_migration(migration)
            if not success:
                print("\n❌ Migration failed! Stopping here.\n")
                return

        print(f"\n{'='*80}")
        print(f"✅ ALL MIGRATIONS COMPLETE ({len(pending)} applied)")
        print(f"{'='*80}\n")

    def create(self, name):
        """Create a new migration file"""
        # Get next version number
        existing = self._get_migration_files()
        next_version = max([m['version'] for m in existing], default=0) + 1

        # Sanitize name
        safe_name = re.sub(r'[^a-z0-9_]', '_', name.lower())
        filename = f"{next_version:03d}_{safe_name}.sql"
        filepath = self.migrations_dir / filename

        # Create template
        template = f"""-- Migration {next_version:03d}: {name}
-- Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}
-- Description: TODO

-- TODO: Add your migration SQL here

-- Example: Create table
-- CREATE TABLE example (
--     id INTEGER PRIMARY KEY,
--     name TEXT NOT NULL
-- );

-- Example: Add column
-- ALTER TABLE proposals ADD COLUMN new_field TEXT;

-- Example: Create index
-- CREATE INDEX idx_example ON example(name);
"""

        with open(filepath, 'w') as f:
            f.write(template)

        print(f"✅ Created migration: {filename}")
        print(f"   Edit: {filepath}")

    def __del__(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Database Migration Runner')
    parser.add_argument('--status', action='store_true', help='Show migration status')
    parser.add_argument('--create', metavar='NAME', help='Create new migration file')
    parser.add_argument('--db', help='Database path (defaults to DATABASE_PATH from .env)')

    args = parser.parse_args()

    runner = MigrationRunner(db_path=args.db)

    if args.status:
        runner.status()
    elif args.create:
        runner.create(args.create)
    else:
        runner.migrate()
