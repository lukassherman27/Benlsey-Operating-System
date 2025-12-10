#!/usr/bin/env python3
"""
Apply Approved Suggestions Script

Finds all suggestions with status='approved' and applies them using the
appropriate handlers, then updates status to 'applied'.

Usage:
    # Dry run - see what would be applied
    python scripts/core/apply_approved_suggestions.py --dry-run

    # Apply ONE suggestion for testing
    python scripts/core/apply_approved_suggestions.py --limit 1

    # Apply all approved suggestions
    python scripts/core/apply_approved_suggestions.py

    # Apply specific suggestion type only
    python scripts/core/apply_approved_suggestions.py --type email_link
"""

import argparse
import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.services.suggestion_handlers import HandlerRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = project_root / "database" / "bensley_master.db"


def get_approved_suggestions(conn, suggestion_type=None, limit=None):
    """Get all suggestions with status='approved' that haven't been applied."""
    cursor = conn.cursor()

    query = """
        SELECT
            suggestion_id,
            suggestion_type,
            title,
            description,
            suggested_data,
            target_table,
            project_code,
            source_type,
            source_id
        FROM ai_suggestions
        WHERE status = 'approved'
    """
    params = []

    if suggestion_type:
        query += " AND suggestion_type = ?"
        params.append(suggestion_type)

    query += " ORDER BY suggestion_id ASC"

    if limit:
        query += " LIMIT ?"
        params.append(limit)

    cursor.execute(query, params)
    columns = [desc[0] for desc in cursor.description]

    suggestions = []
    for row in cursor.fetchall():
        suggestions.append(dict(zip(columns, row)))

    return suggestions


def apply_suggestion(conn, suggestion, dry_run=False):
    """Apply a single suggestion using the handler registry."""
    suggestion_id = suggestion['suggestion_id']
    suggestion_type = suggestion['suggestion_type']

    # Parse suggested_data
    try:
        suggested_data = json.loads(suggestion.get('suggested_data') or '{}')
        # Handle malformed data (list instead of dict)
        if isinstance(suggested_data, list):
            logger.warning(f"  Malformed suggested_data (list instead of dict): {suggested_data}")
            return False, "Malformed suggested_data: expected dict, got list"
        if not isinstance(suggested_data, dict):
            logger.warning(f"  Malformed suggested_data (not a dict): {type(suggested_data)}")
            return False, f"Malformed suggested_data: expected dict, got {type(suggested_data).__name__}"
    except json.JSONDecodeError:
        logger.error(f"  Invalid JSON in suggested_data for suggestion {suggestion_id}")
        return False, "Invalid JSON in suggested_data"

    # Get the handler
    handler = HandlerRegistry.get_handler(suggestion_type, conn)

    if not handler:
        logger.warning(f"  No handler for suggestion type: {suggestion_type}")
        return False, f"No handler for type: {suggestion_type}"

    # Validate
    errors = handler.validate(suggested_data)
    if errors:
        logger.warning(f"  Validation errors: {errors}")
        return False, f"Validation errors: {errors}"

    if dry_run:
        # Preview what would happen
        preview = handler.preview(suggestion, suggested_data)
        logger.info(f"  [DRY RUN] Would: {preview.action} on {preview.table}")
        logger.info(f"  [DRY RUN] Summary: {preview.summary}")
        return True, f"Would apply: {preview.summary}"

    # Apply the changes
    result = handler.apply(suggestion, suggested_data)

    if result.success:
        # Store rollback data
        if result.rollback_data:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ai_suggestions
                SET rollback_data = ?
                WHERE suggestion_id = ?
            """, (json.dumps(result.rollback_data), suggestion_id))

        # Update status to 'applied'
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE ai_suggestions
            SET status = 'applied'
            WHERE suggestion_id = ?
        """, (suggestion_id,))
        conn.commit()

        logger.info(f"  SUCCESS: {result.message}")
        return True, result.message
    else:
        logger.error(f"  FAILED: {result.message}")
        return False, result.message


def main():
    parser = argparse.ArgumentParser(
        description="Apply approved suggestions to the database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be applied without making changes"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of suggestions to process"
    )
    parser.add_argument(
        "--type",
        dest="suggestion_type",
        help="Only process suggestions of this type"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show more details"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Connect to database
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    try:
        # Get approved suggestions
        suggestions = get_approved_suggestions(
            conn,
            suggestion_type=args.suggestion_type,
            limit=args.limit
        )

        logger.info(f"Found {len(suggestions)} approved suggestions to apply")

        if not suggestions:
            logger.info("Nothing to do!")
            return

        # Summary by type
        type_counts = {}
        for s in suggestions:
            t = s['suggestion_type']
            type_counts[t] = type_counts.get(t, 0) + 1

        logger.info("Breakdown by type:")
        for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            logger.info(f"  {t}: {count}")

        if args.dry_run:
            logger.info("\n=== DRY RUN MODE ===\n")

        # Process each suggestion
        success_count = 0
        fail_count = 0
        skip_count = 0

        for i, suggestion in enumerate(suggestions, 1):
            s_id = suggestion['suggestion_id']
            s_type = suggestion['suggestion_type']
            s_title = suggestion['title'][:60] if suggestion['title'] else 'No title'

            logger.info(f"\n[{i}/{len(suggestions)}] #{s_id} ({s_type}): {s_title}")

            try:
                success, message = apply_suggestion(conn, suggestion, dry_run=args.dry_run)

                if success:
                    success_count += 1
                else:
                    fail_count += 1

            except Exception as e:
                logger.exception(f"  Exception applying suggestion {s_id}: {e}")
                fail_count += 1

        # Final summary
        logger.info("\n" + "=" * 50)
        logger.info("SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total processed: {len(suggestions)}")
        logger.info(f"Successful: {success_count}")
        logger.info(f"Failed: {fail_count}")

        if args.dry_run:
            logger.info("\nThis was a DRY RUN. No changes were made.")
            logger.info("Run without --dry-run to apply changes.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
