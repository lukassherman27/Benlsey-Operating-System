#!/usr/bin/env python3
"""
change_tracker.py

Tracks changes to critical context files over time
Monitors: master plans, status docs, database, migrations
"""

import os
import json
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
import subprocess

class ChangeTracker:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.tracking_file = self.project_root / 'tracking' / 'change_history.json'
        self.db_path = Path(os.path.expanduser('~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db'))

        # Files to track
        self.tracked_files = [
            'BENSLEY_BRAIN_MASTER_PLAN.md',
            'WHERE_WE_ARE_NOW.md',
            'DATABASE_SETUP.md',
            'CRITICAL_FIXES_SUMMARY.md',
            'IMPLEMENTATION_STATUS.md',
            'README.md',
            '.env'
        ]

        # Load history
        self.history = self._load_history()

    def _load_history(self):
        """Load change history from JSON"""
        if self.tracking_file.exists():
            with open(self.tracking_file, 'r') as f:
                return json.load(f)
        return {'snapshots': [], 'decisions': []}

    def _save_history(self):
        """Save change history to JSON"""
        self.tracking_file.parent.mkdir(exist_ok=True)
        with open(self.tracking_file, 'w') as f:
            json.dump(self.history, indent=2, fp=f)

    def _file_hash(self, filepath):
        """Get MD5 hash of file content"""
        if not filepath.exists():
            return None
        return hashlib.md5(filepath.read_bytes()).hexdigest()

    def _get_git_info(self):
        """Get recent git commits from today"""
        try:
            result = subprocess.run(
                ['git', 'log', '--since=midnight', '--oneline', '--no-decorate'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            commits = result.stdout.strip().split('\n') if result.stdout.strip() else []

            # Get files changed today
            files_result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD@{midnight}..HEAD'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            files_changed = files_result.stdout.strip().split('\n') if files_result.stdout.strip() else []

            return {
                'commits_today': len(commits),
                'commit_messages': commits[:10],  # Last 10
                'files_changed': files_changed
            }
        except Exception as e:
            return {'error': str(e)}

    def _get_database_stats(self):
        """Get current database statistics"""
        if not self.db_path.exists():
            return {'error': 'Database not found'}

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Count tables
        tables = ['proposals', 'emails', 'email_content', 'documents',
                  'contacts', 'contacts_only', 'email_proposal_links']

        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            except:
                stats[table] = 0

        # Get database size
        stats['db_size_mb'] = self.db_path.stat().st_size / (1024 * 1024)

        # Count migrations
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM schema_migrations")
            stats['migrations_applied'] = cursor.fetchone()[0]
        else:
            # Count migration files
            migrations_dir = self.project_root / 'database' / 'migrations'
            if migrations_dir.exists():
                stats['migrations_applied'] = len(list(migrations_dir.glob('*.sql')))

        # Count indexes
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
        stats['indexes'] = cursor.fetchone()[0]

        conn.close()
        return stats

    def take_snapshot(self, reason="Daily snapshot"):
        """Take a snapshot of current state"""
        print(f"\n📸 Taking snapshot: {reason}")

        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'reason': reason,
            'files': {},
            'database': self._get_database_stats(),
            'git': self._get_git_info()
        }

        # Track each file
        for filename in self.tracked_files:
            filepath = self.project_root / filename
            if filepath.exists():
                snapshot['files'][filename] = {
                    'hash': self._file_hash(filepath),
                    'size': filepath.stat().st_size,
                    'modified': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()
                }

        self.history['snapshots'].append(snapshot)
        self._save_history()

        print(f"   ✅ Snapshot saved")
        return snapshot

    def log_decision(self, decision, rationale, alternatives=None):
        """Log a major decision with rationale"""
        decision_entry = {
            'timestamp': datetime.now().isoformat(),
            'decision': decision,
            'rationale': rationale,
            'alternatives_considered': alternatives or [],
            'context': {
                'database_stats': self._get_database_stats(),
                'recent_commits': self._get_git_info()['commit_messages'][:3]
            }
        }

        self.history['decisions'].append(decision_entry)
        self._save_history()

        print(f"✅ Decision logged: {decision}")

    def get_changes_since_last_snapshot(self):
        """Compare current state to last snapshot"""
        if not self.history['snapshots']:
            return {'message': 'No previous snapshots to compare'}

        last = self.history['snapshots'][-1]
        current_db = self._get_database_stats()

        changes = {
            'time_since_last': (datetime.now() - datetime.fromisoformat(last['timestamp'])).total_seconds() / 3600,
            'database_changes': {},
            'files_changed': [],
            'git_activity': self._get_git_info()
        }

        # Database changes
        for key, value in current_db.items():
            if key in last['database']:
                diff = value - last['database'][key] if isinstance(value, (int, float)) else None
                if diff and diff != 0:
                    changes['database_changes'][key] = {
                        'before': last['database'][key],
                        'after': value,
                        'change': diff
                    }

        # File changes
        for filename in self.tracked_files:
            filepath = self.project_root / filename
            if filepath.exists():
                current_hash = self._file_hash(filepath)
                if filename in last['files']:
                    if current_hash != last['files'][filename]['hash']:
                        changes['files_changed'].append(filename)

        return changes

    def get_summary(self, days=7):
        """Get summary of changes over last N days"""
        cutoff = datetime.now().timestamp() - (days * 24 * 3600)
        recent_snapshots = [
            s for s in self.history['snapshots']
            if datetime.fromisoformat(s['timestamp']).timestamp() > cutoff
        ]

        recent_decisions = [
            d for d in self.history['decisions']
            if datetime.fromisoformat(d['timestamp']).timestamp() > cutoff
        ]

        return {
            'period_days': days,
            'snapshots_taken': len(recent_snapshots),
            'decisions_made': len(recent_decisions),
            'snapshots': recent_snapshots,
            'decisions': recent_decisions
        }

if __name__ == '__main__':
    tracker = ChangeTracker()

    # Take snapshot
    snapshot = tracker.take_snapshot("Manual test snapshot")

    # Show changes since last
    print("\n📊 Changes since last snapshot:")
    changes = tracker.get_changes_since_last_snapshot()
    print(json.dumps(changes, indent=2))
