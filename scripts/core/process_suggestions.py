#!/usr/bin/env python3
"""
Process Suggestions - Comprehensive AI Suggestions Processing

Handles BOTH tables:
1. ai_suggestions_queue - Simple queue for new_contact and project_alias
2. ai_suggestions - Main suggestions table with multiple types

Processing rules:
- Auto-approve new_contact with confidence > 0.85
- Auto-approve project_alias matching existing project patterns
- Auto-approve deadline_detected with confidence > 0.85
- Group remaining suggestions by confidence for human review
- Record training feedback for all decisions

Usage:
    python scripts/core/process_suggestions.py --dry-run
    python scripts/core/process_suggestions.py --process
    python scripts/core/process_suggestions.py --report
"""

import json
import sqlite3
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class SuggestionProcessor:
    # Confidence thresholds for auto-approval
    HIGH_CONFIDENCE_THRESHOLD = 0.85
    MEDIUM_CONFIDENCE_THRESHOLD = 0.70

    def __init__(self, db_path: str = "database/bensley_master.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.stats = {
            # Queue stats
            'queue_contacts_added': 0,
            'queue_contacts_duplicate': 0,
            'queue_contacts_rejected': 0,
            'queue_aliases_added': 0,
            'queue_aliases_rejected': 0,
            # Main table stats
            'main_auto_approved': 0,
            'main_need_review': 0,
            'main_duplicates_found': 0,
            # Feedback
            'feedback_recorded': 0
        }

    # =========================================================================
    # QUEUE PROCESSING (ai_suggestions_queue)
    # =========================================================================

    def get_queue_pending(self, field_name: str = None) -> List[sqlite3.Row]:
        """Get pending items from ai_suggestions_queue."""
        cursor = self.conn.cursor()
        if field_name:
            cursor.execute("""
                SELECT * FROM ai_suggestions_queue
                WHERE status = 'pending' AND field_name = ?
            """, (field_name,))
        else:
            cursor.execute("SELECT * FROM ai_suggestions_queue WHERE status = 'pending'")
        return cursor.fetchall()

    def contact_exists(self, email: str) -> bool:
        """Check if contact email already exists."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM contacts WHERE LOWER(email) = LOWER(?)", (email,))
        return cursor.fetchone() is not None

    def project_exists(self, project_code: str) -> bool:
        """Check if project code exists in proposals or projects."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 1 FROM proposals WHERE project_code = ?
            UNION
            SELECT 1 FROM projects WHERE project_code = ?
        """, (project_code, project_code))
        return cursor.fetchone() is not None

    def add_contact(self, name: str, email: str, company: str = None, source: str = "ai_suggestion") -> int:
        """Add a new contact to the database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO contacts (name, email, notes)
            VALUES (?, ?, ?)
        """, (name, email, f"Company: {company}. Source: {source}" if company else f"Source: {source}"))
        self.conn.commit()
        return cursor.lastrowid

    def add_project_alias(self, alias: str, project_code: str) -> Optional[int]:
        """Add a project alias as a learned pattern."""
        cursor = self.conn.cursor()

        # Check if alias already exists for this project
        cursor.execute("""
            SELECT pattern_id FROM learned_patterns
            WHERE pattern_name = ?
            AND json_extract(condition, '$.project_code') = ?
        """, (alias, project_code))
        if cursor.fetchone():
            return None  # Already exists

        cursor.execute("""
            INSERT INTO learned_patterns
            (pattern_name, pattern_type, condition, action, confidence_score, is_active, created_at, updated_at)
            VALUES (?, 'entity_pattern', ?, ?, 0.8, 1, datetime('now'), datetime('now'))
        """, (
            alias,
            json.dumps({"alias": alias, "project_code": project_code}),
            json.dumps({"link_to_project": project_code, "type": "project_alias"})
        ))
        self.conn.commit()
        return cursor.lastrowid

    def update_queue_status(self, suggestion_id: int, status: str):
        """Update queue suggestion status."""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        if status in ('approved', 'rejected'):
            cursor.execute("""
                UPDATE ai_suggestions_queue
                SET status = ?, reviewed_at = ?
                WHERE suggestion_id = ?
            """, (status, now, suggestion_id))
        else:  # applied
            cursor.execute("""
                UPDATE ai_suggestions_queue
                SET status = ?, applied_at = ?
                WHERE suggestion_id = ?
            """, (status, now, suggestion_id))
        self.conn.commit()

    def process_queue_contacts(self, dry_run: bool = True) -> int:
        """Process new_contact suggestions from queue."""
        suggestions = self.get_queue_pending('new_contact')
        processed = 0

        for s in suggestions:
            try:
                data = json.loads(s['suggested_value'])
                name = data.get('name', '').strip()
                email = data.get('email', '').strip().lower()
                company = data.get('company')
                project_code = data.get('related_project')
                confidence = s['confidence'] or 0

                if not email or '@' not in email:
                    print(f"  REJECT (invalid email): {name}")
                    if not dry_run:
                        self.update_queue_status(s['suggestion_id'], 'rejected')
                        self.record_feedback('new_contact_queue', email, 'invalid_email', False, project_code)
                    self.stats['queue_contacts_rejected'] += 1
                    continue

                if self.contact_exists(email):
                    print(f"  REJECT (duplicate): {name} <{email}>")
                    if not dry_run:
                        self.update_queue_status(s['suggestion_id'], 'rejected')
                        self.record_feedback('new_contact_queue', email, 'duplicate', False, project_code)
                    self.stats['queue_contacts_duplicate'] += 1
                    continue

                # Auto-approve if high confidence, otherwise needs review
                if confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
                    print(f"  AUTO-APPROVE (conf={confidence:.2f}): {name} <{email}>")
                    if not dry_run:
                        self.add_contact(name, email, company, source="auto_approved")
                        self.update_queue_status(s['suggestion_id'], 'applied')
                        self.record_feedback('new_contact_queue', '', email, True, project_code)
                    self.stats['queue_contacts_added'] += 1
                else:
                    print(f"  NEEDS REVIEW (conf={confidence:.2f}): {name} <{email}>")
                    self.stats['main_need_review'] += 1

                processed += 1

            except (json.JSONDecodeError, KeyError) as e:
                print(f"  ERROR parsing {s['suggestion_id']}: {e}")
                if not dry_run:
                    self.update_queue_status(s['suggestion_id'], 'rejected')
                self.stats['queue_contacts_rejected'] += 1

        return processed

    def process_queue_aliases(self, dry_run: bool = True) -> int:
        """Process project_alias suggestions from queue."""
        suggestions = self.get_queue_pending('project_alias')
        processed = 0

        for s in suggestions:
            try:
                data = json.loads(s['suggested_value'])
                alias = data.get('alias', '').strip()
                project_code = data.get('project_code', '').strip()
                confidence = s['confidence'] or 0

                if not project_code:
                    print(f"  REJECT (no project): '{alias}'")
                    if not dry_run:
                        self.update_queue_status(s['suggestion_id'], 'rejected')
                    self.stats['queue_aliases_rejected'] += 1
                    continue

                if len(alias) < 5:
                    print(f"  REJECT (too short): '{alias}'")
                    if not dry_run:
                        self.update_queue_status(s['suggestion_id'], 'rejected')
                    self.stats['queue_aliases_rejected'] += 1
                    continue

                # Verify project exists
                if not self.project_exists(project_code):
                    print(f"  REJECT (project not found): '{alias}' -> {project_code}")
                    if not dry_run:
                        self.update_queue_status(s['suggestion_id'], 'rejected')
                    self.stats['queue_aliases_rejected'] += 1
                    continue

                print(f"  ADD ALIAS: '{alias}' -> {project_code}")
                if not dry_run:
                    result = self.add_project_alias(alias, project_code)
                    if result:
                        self.update_queue_status(s['suggestion_id'], 'applied')
                        self.record_feedback('project_alias_queue', '', f"{alias} -> {project_code}", True, project_code)
                        self.stats['queue_aliases_added'] += 1
                    else:
                        self.update_queue_status(s['suggestion_id'], 'rejected')  # Duplicate
                        self.stats['queue_aliases_rejected'] += 1
                else:
                    self.stats['queue_aliases_added'] += 1

                processed += 1

            except (json.JSONDecodeError, KeyError) as e:
                print(f"  ERROR parsing {s['suggestion_id']}: {e}")
                if not dry_run:
                    self.update_queue_status(s['suggestion_id'], 'rejected')
                self.stats['queue_aliases_rejected'] += 1

        return processed

    # =========================================================================
    # MAIN TABLE PROCESSING (ai_suggestions)
    # =========================================================================

    def get_main_pending(self, suggestion_type: str = None) -> List[sqlite3.Row]:
        """Get pending items from ai_suggestions."""
        cursor = self.conn.cursor()
        if suggestion_type:
            cursor.execute("""
                SELECT * FROM ai_suggestions
                WHERE status = 'pending' AND suggestion_type = ?
                ORDER BY confidence_score DESC
            """, (suggestion_type,))
        else:
            cursor.execute("""
                SELECT * FROM ai_suggestions
                WHERE status = 'pending'
                ORDER BY suggestion_type, confidence_score DESC
            """)
        return cursor.fetchall()

    def update_main_status(self, suggestion_id: int, status: str, reviewed_by: str = "suggestion_processor"):
        """Update main suggestion status."""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE ai_suggestions
            SET status = ?, reviewed_by = ?, reviewed_at = ?
            WHERE suggestion_id = ?
        """, (status, reviewed_by, now, suggestion_id))
        self.conn.commit()

    def find_duplicate_suggestions(self) -> List[Tuple[int, int]]:
        """Find duplicate suggestions based on source_id and suggestion_type."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                a.suggestion_id as keep_id,
                b.suggestion_id as remove_id
            FROM ai_suggestions a
            JOIN ai_suggestions b ON
                a.source_id = b.source_id
                AND a.suggestion_type = b.suggestion_type
                AND a.suggestion_id < b.suggestion_id
            WHERE a.status = 'pending' AND b.status = 'pending'
        """)
        return cursor.fetchall()

    def remove_duplicates(self, dry_run: bool = True) -> int:
        """Mark duplicate suggestions as rejected."""
        duplicates = self.find_duplicate_suggestions()

        if not duplicates:
            print("  No duplicate suggestions found")
            return 0

        print(f"  Found {len(duplicates)} duplicate suggestions")

        if not dry_run:
            for keep_id, remove_id in duplicates:
                self.update_main_status(remove_id, 'rejected', 'deduplication')
                self.stats['main_duplicates_found'] += 1
        else:
            self.stats['main_duplicates_found'] = len(duplicates)

        return len(duplicates)

    def process_main_suggestions(self, dry_run: bool = True) -> Dict[str, int]:
        """Process main ai_suggestions table by type."""
        stats = {}

        # Get breakdown by type
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT suggestion_type, COUNT(*) as cnt, AVG(confidence_score) as avg_conf
            FROM ai_suggestions
            WHERE status = 'pending'
            GROUP BY suggestion_type
            ORDER BY cnt DESC
        """)
        type_breakdown = cursor.fetchall()

        print("\n  PENDING BY TYPE:")
        for row in type_breakdown:
            print(f"    {row['suggestion_type']}: {row['cnt']} (avg conf: {row['avg_conf']:.2f})")

        # Count high confidence that could be auto-approved
        cursor.execute("""
            SELECT suggestion_type, COUNT(*) as cnt
            FROM ai_suggestions
            WHERE status = 'pending' AND confidence_score >= ?
            GROUP BY suggestion_type
        """, (self.HIGH_CONFIDENCE_THRESHOLD,))
        high_conf = cursor.fetchall()

        if high_conf:
            print(f"\n  HIGH CONFIDENCE (>= {self.HIGH_CONFIDENCE_THRESHOLD}) CANDIDATES:")
            for row in high_conf:
                print(f"    {row['suggestion_type']}: {row['cnt']} could be auto-approved")
                stats[f"{row['suggestion_type']}_auto_approve"] = row['cnt']
        else:
            print(f"\n  No suggestions with confidence >= {self.HIGH_CONFIDENCE_THRESHOLD}")

        # Group by confidence bands for human review
        cursor.execute("""
            SELECT
                suggestion_type,
                CASE
                    WHEN confidence_score >= 0.85 THEN 'high'
                    WHEN confidence_score >= 0.70 THEN 'medium'
                    ELSE 'low'
                END as conf_band,
                COUNT(*) as cnt
            FROM ai_suggestions
            WHERE status = 'pending'
            GROUP BY suggestion_type, conf_band
            ORDER BY suggestion_type, conf_band DESC
        """)
        bands = cursor.fetchall()

        print("\n  CONFIDENCE BANDS FOR REVIEW:")
        current_type = None
        for row in bands:
            if row['suggestion_type'] != current_type:
                current_type = row['suggestion_type']
                print(f"\n    {current_type}:")
            print(f"      {row['conf_band']}: {row['cnt']}")

        return stats

    # =========================================================================
    # FEEDBACK RECORDING
    # =========================================================================

    def record_feedback(self, feature_name: str, original_value: str,
                       correction_value: str, helpful: bool, project_code: str = None):
        """Record decision in training_data_feedback."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO training_data_feedback
            (user_id, feature_name, original_value, correction_value, helpful,
             project_code, source, notes)
            VALUES ('suggestion_processor', ?, ?, ?, ?, ?, 'automated',
                    'Auto-processed by process_suggestions.py')
        """, (feature_name, original_value, correction_value, helpful, project_code))
        self.conn.commit()
        self.stats['feedback_recorded'] += 1

    # =========================================================================
    # REPORTING
    # =========================================================================

    def generate_report(self) -> Dict:
        """Generate comprehensive status report."""
        cursor = self.conn.cursor()

        report = {
            'timestamp': datetime.now().isoformat(),
            'queue': {},
            'main': {},
            'recommendations': []
        }

        # Queue status
        cursor.execute("""
            SELECT status, data_table, field_name, COUNT(*) as cnt
            FROM ai_suggestions_queue
            GROUP BY status, data_table, field_name
        """)
        queue_status = cursor.fetchall()
        report['queue']['breakdown'] = [dict(r) for r in queue_status]

        cursor.execute("SELECT COUNT(*) FROM ai_suggestions_queue WHERE status = 'pending'")
        report['queue']['pending'] = cursor.fetchone()[0]

        # Main table status
        cursor.execute("""
            SELECT suggestion_type, status, COUNT(*) as cnt
            FROM ai_suggestions
            GROUP BY suggestion_type, status
        """)
        main_status = cursor.fetchall()
        report['main']['breakdown'] = [dict(r) for r in main_status]

        cursor.execute("SELECT COUNT(*) FROM ai_suggestions WHERE status = 'pending'")
        report['main']['pending'] = cursor.fetchone()[0]

        # Recommendations
        cursor.execute("""
            SELECT COUNT(*) FROM ai_suggestions
            WHERE status = 'pending' AND confidence_score >= 0.85
        """)
        high_conf_count = cursor.fetchone()[0]
        if high_conf_count > 0:
            report['recommendations'].append(
                f"{high_conf_count} high-confidence suggestions could be auto-approved"
            )

        # Check for duplicates
        dups = self.find_duplicate_suggestions()
        if dups:
            report['recommendations'].append(
                f"{len(dups)} duplicate suggestions should be cleaned up"
            )

        return report

    def print_summary(self):
        """Print processing summary."""
        print("\n" + "="*70)
        print("PROCESSING SUMMARY")
        print("="*70)
        print("\nQUEUE (ai_suggestions_queue):")
        print(f"  Contacts added:      {self.stats['queue_contacts_added']}")
        print(f"  Contacts duplicate:  {self.stats['queue_contacts_duplicate']}")
        print(f"  Contacts rejected:   {self.stats['queue_contacts_rejected']}")
        print(f"  Aliases added:       {self.stats['queue_aliases_added']}")
        print(f"  Aliases rejected:    {self.stats['queue_aliases_rejected']}")
        print("\nMAIN TABLE (ai_suggestions):")
        print(f"  Auto-approved:       {self.stats['main_auto_approved']}")
        print(f"  Need review:         {self.stats['main_need_review']}")
        print(f"  Duplicates found:    {self.stats['main_duplicates_found']}")
        print("\nFEEDBACK:")
        print(f"  Records created:     {self.stats['feedback_recorded']}")
        print("="*70)

    def close(self):
        self.conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='Process AI suggestions from both queue and main tables',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/core/process_suggestions.py --report
  python scripts/core/process_suggestions.py --dry-run
  python scripts/core/process_suggestions.py --process --dedupe
        """
    )
    parser.add_argument('--report', action='store_true',
                       help='Generate status report only (no processing)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without applying')
    parser.add_argument('--process', action='store_true',
                       help='Actually process and apply changes')
    parser.add_argument('--dedupe', action='store_true',
                       help='Remove duplicate suggestions')
    parser.add_argument('--queue-only', action='store_true',
                       help='Only process ai_suggestions_queue')
    parser.add_argument('--main-only', action='store_true',
                       help='Only analyze ai_suggestions (no auto-processing)')
    parser.add_argument('--db', default='database/bensley_master.db',
                       help='Database path')

    args = parser.parse_args()

    if not any([args.report, args.dry_run, args.process]):
        print("ERROR: Must specify --report, --dry-run, or --process")
        parser.print_help()
        sys.exit(1)

    processor = SuggestionProcessor(args.db)

    try:
        if args.report:
            print("\n" + "="*70)
            print("SUGGESTIONS STATUS REPORT")
            print("="*70)
            report = processor.generate_report()

            print(f"\nGenerated: {report['timestamp']}")

            print(f"\nQUEUE PENDING: {report['queue']['pending']}")
            if report['queue']['breakdown']:
                for item in report['queue']['breakdown']:
                    if item['status'] == 'pending':
                        print(f"  {item['data_table']}/{item['field_name']}: {item['cnt']}")

            print(f"\nMAIN TABLE PENDING: {report['main']['pending']}")
            pending_types = {}
            for item in report['main']['breakdown']:
                if item['status'] == 'pending':
                    pending_types[item['suggestion_type']] = item['cnt']
            for stype, cnt in sorted(pending_types.items(), key=lambda x: -x[1]):
                print(f"  {stype}: {cnt}")

            if report['recommendations']:
                print("\nRECOMMENDATIONS:")
                for rec in report['recommendations']:
                    print(f"  - {rec}")

            print("\n" + "="*70)
            return

        dry_run = args.dry_run or not args.process

        if dry_run:
            print("\n*** DRY RUN MODE - No changes will be made ***")
        else:
            print("\n*** PROCESSING MODE - Changes will be applied ***")

        # Process queue
        if not args.main_only:
            print("\n" + "="*70)
            print("PROCESSING AI_SUGGESTIONS_QUEUE")
            print("="*70)

            print("\n[New Contacts]")
            processor.process_queue_contacts(dry_run=dry_run)

            print("\n[Project Aliases]")
            processor.process_queue_aliases(dry_run=dry_run)

        # Analyze/process main table
        if not args.queue_only:
            print("\n" + "="*70)
            print("ANALYZING AI_SUGGESTIONS (Main Table)")
            print("="*70)

            if args.dedupe:
                print("\n[Deduplication]")
                processor.remove_duplicates(dry_run=dry_run)

            processor.process_main_suggestions(dry_run=dry_run)

        processor.print_summary()

    finally:
        processor.close()


if __name__ == '__main__':
    main()
