#!/usr/bin/env python3
"""
Suggestion Queue Processor

Processes the ai_suggestions_queue:
- new_contact: Adds new contacts to contacts table
- project_alias: Adds aliases to learned_patterns for email matching

Records all decisions in training_data_feedback for AI training.
"""

import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path


class SuggestionProcessor:
    def __init__(self, db_path: str = "database/bensley_master.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.stats = {
            'contacts_added': 0,
            'contacts_duplicates': 0,
            'contacts_invalid': 0,
            'aliases_added': 0,
            'aliases_skipped': 0,
            'feedback_recorded': 0
        }

    def get_pending_suggestions(self, field_name: str = None) -> list:
        """Get all pending suggestions, optionally filtered by type."""
        cursor = self.conn.cursor()
        if field_name:
            cursor.execute("""
                SELECT * FROM ai_suggestions_queue
                WHERE status = 'pending' AND field_name = ?
            """, (field_name,))
        else:
            cursor.execute("""
                SELECT * FROM ai_suggestions_queue WHERE status = 'pending'
            """)
        return cursor.fetchall()

    def contact_exists(self, email: str) -> bool:
        """Check if contact email already exists."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM contacts WHERE email = ?", (email,))
        return cursor.fetchone() is not None

    def add_contact(self, name: str, email: str, company: str = None) -> int:
        """Add a new contact to the database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO contacts (name, email, notes)
            VALUES (?, ?, ?)
        """, (name, email, f"Company: {company}" if company else None))
        self.conn.commit()
        return cursor.lastrowid

    def add_project_alias(self, alias: str, project_code: str) -> int:
        """Add a project alias as a learned pattern."""
        cursor = self.conn.cursor()

        # Check if this alias already exists
        cursor.execute("""
            SELECT pattern_id FROM learned_patterns
            WHERE pattern_name = ? AND json_extract(condition, '$.project_code') = ?
        """, (alias, project_code))
        existing = cursor.fetchone()
        if existing:
            return existing[0]

        # Insert new pattern
        cursor.execute("""
            INSERT INTO learned_patterns
            (pattern_name, pattern_type, condition, action, confidence_score, is_active)
            VALUES (?, 'entity_pattern', ?, ?, 0.8, 1)
        """, (
            alias,
            json.dumps({"alias": alias, "project_code": project_code}),
            json.dumps({"link_to_project": project_code, "type": "project_alias"})
        ))
        self.conn.commit()
        return cursor.lastrowid

    def update_suggestion_status(self, suggestion_id: int, status: str):
        """Update suggestion status (approved, rejected, applied)."""
        cursor = self.conn.cursor()
        timestamp_field = 'reviewed_at' if status in ('approved', 'rejected') else 'applied_at'
        cursor.execute(f"""
            UPDATE ai_suggestions_queue
            SET status = ?, {timestamp_field} = datetime('now')
            WHERE suggestion_id = ?
        """, (status, suggestion_id))
        self.conn.commit()

    def record_feedback(self, feature_name: str, original_value: str,
                        correction_value: str, helpful: bool, project_code: str = None):
        """Record decision in training_data_feedback for AI training."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO training_data_feedback
            (user_id, feature_name, original_value, correction_value, helpful,
             project_code, source, notes)
            VALUES ('suggestion_processor', ?, ?, ?, ?, ?, 'automated',
                    'Auto-processed from suggestions queue')
        """, (feature_name, original_value, correction_value, helpful, project_code))
        self.conn.commit()
        self.stats['feedback_recorded'] += 1

    def process_contact_suggestions(self, dry_run: bool = False):
        """Process all pending new_contact suggestions."""
        print("\n" + "="*60)
        print("PROCESSING NEW_CONTACT SUGGESTIONS")
        print("="*60)

        suggestions = self.get_pending_suggestions('new_contact')
        print(f"Found {len(suggestions)} pending contact suggestions")

        for suggestion in suggestions:
            try:
                data = json.loads(suggestion['suggested_value'])
                name = data.get('name', '')
                email = data.get('email', '')
                company = data.get('company')
                project_code = data.get('related_project')

                if not email or '@' not in email:
                    print(f"  SKIP (invalid): {name} - no valid email")
                    if not dry_run:
                        self.update_suggestion_status(suggestion['suggestion_id'], 'rejected')
                    self.stats['contacts_invalid'] += 1
                    continue

                if self.contact_exists(email):
                    print(f"  SKIP (exists): {name} <{email}>")
                    if not dry_run:
                        self.update_suggestion_status(suggestion['suggestion_id'], 'rejected')
                        self.record_feedback('new_contact', email, 'duplicate', False, project_code)
                    self.stats['contacts_duplicates'] += 1
                else:
                    print(f"  ADD: {name} <{email}> ({company or 'no company'})")
                    if not dry_run:
                        self.add_contact(name, email, company)
                        self.update_suggestion_status(suggestion['suggestion_id'], 'applied')
                        self.record_feedback('new_contact', '', email, True, project_code)
                    self.stats['contacts_added'] += 1

            except json.JSONDecodeError as e:
                print(f"  ERROR parsing suggestion {suggestion['suggestion_id']}: {e}")
                if not dry_run:
                    self.update_suggestion_status(suggestion['suggestion_id'], 'rejected')
                self.stats['contacts_invalid'] += 1

    def process_alias_suggestions(self, dry_run: bool = False):
        """Process all pending project_alias suggestions."""
        print("\n" + "="*60)
        print("PROCESSING PROJECT_ALIAS SUGGESTIONS")
        print("="*60)

        suggestions = self.get_pending_suggestions('project_alias')
        print(f"Found {len(suggestions)} pending alias suggestions")

        for suggestion in suggestions:
            try:
                data = json.loads(suggestion['suggested_value'])
                alias = data.get('alias', '')
                project_code = data.get('project_code')

                # Skip if no project code (can't link to anything)
                if not project_code:
                    print(f"  SKIP (no project): '{alias}'")
                    if not dry_run:
                        self.update_suggestion_status(suggestion['suggestion_id'], 'rejected')
                    self.stats['aliases_skipped'] += 1
                    continue

                # Skip very short aliases (likely noise)
                if len(alias) < 5:
                    print(f"  SKIP (too short): '{alias}'")
                    if not dry_run:
                        self.update_suggestion_status(suggestion['suggestion_id'], 'rejected')
                    self.stats['aliases_skipped'] += 1
                    continue

                print(f"  ADD: '{alias}' → {project_code}")
                if not dry_run:
                    self.add_project_alias(alias, project_code)
                    self.update_suggestion_status(suggestion['suggestion_id'], 'applied')
                    self.record_feedback('project_alias', '', f"{alias} → {project_code}", True, project_code)
                self.stats['aliases_added'] += 1

            except json.JSONDecodeError as e:
                print(f"  ERROR parsing suggestion {suggestion['suggestion_id']}: {e}")
                if not dry_run:
                    self.update_suggestion_status(suggestion['suggestion_id'], 'rejected')
                self.stats['aliases_skipped'] += 1

    def print_summary(self):
        """Print processing summary."""
        print("\n" + "="*60)
        print("PROCESSING SUMMARY")
        print("="*60)
        print(f"Contacts added:     {self.stats['contacts_added']}")
        print(f"Contacts duplicate: {self.stats['contacts_duplicates']}")
        print(f"Contacts invalid:   {self.stats['contacts_invalid']}")
        print(f"Aliases added:      {self.stats['aliases_added']}")
        print(f"Aliases skipped:    {self.stats['aliases_skipped']}")
        print(f"Feedback recorded:  {self.stats['feedback_recorded']}")
        print("="*60)

    def close(self):
        self.conn.close()


def main():
    parser = argparse.ArgumentParser(description='Process AI suggestions queue')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without applying')
    parser.add_argument('--contacts-only', action='store_true',
                        help='Only process contact suggestions')
    parser.add_argument('--aliases-only', action='store_true',
                        help='Only process alias suggestions')
    parser.add_argument('--db', default='database/bensley_master.db',
                        help='Database path')

    args = parser.parse_args()

    if args.dry_run:
        print("\n*** DRY RUN MODE - No changes will be made ***\n")

    processor = SuggestionProcessor(args.db)

    try:
        if not args.aliases_only:
            processor.process_contact_suggestions(dry_run=args.dry_run)

        if not args.contacts_only:
            processor.process_alias_suggestions(dry_run=args.dry_run)

        processor.print_summary()

    finally:
        processor.close()


if __name__ == '__main__':
    main()
