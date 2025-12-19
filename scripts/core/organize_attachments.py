#!/usr/bin/env python3
"""
Organize Email Attachments by Project

This script organizes email attachments into a structured folder hierarchy:
/files/attachments/{year}/{project_code}/{document_type}/

It:
1. Queries attachments that have proposal links (to get project_code)
2. Creates the folder structure
3. Copies files to the organized location (preserves originals)
4. Updates the database with organized_path

Usage:
    python organize_attachments.py --stats      # Show stats only
    python organize_attachments.py --dry-run    # Preview changes
    python organize_attachments.py --organize   # Actually organize files
"""

import os
import sys
import sqlite3
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Configuration
DB_PATH = os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "database" / "bensley_master.db"))
ATTACHMENTS_BASE = PROJECT_ROOT / "files" / "attachments"

# Document type mapping (from document_type field or inferred from extension)
DOCUMENT_TYPE_MAP = {
    # From document_type field
    "contract": "contracts",
    "proposal": "proposals",
    "drawing": "drawings",
    "specification": "specifications",
    "report": "reports",
    "presentation": "presentations",
    "invoice": "invoices",
    "agreement": "contracts",
    # Inferred from extension
    ".pdf": "documents",
    ".doc": "documents",
    ".docx": "documents",
    ".dwg": "drawings",
    ".dxf": "drawings",
    ".dwf": "drawings",
    ".ppt": "presentations",
    ".pptx": "presentations",
    ".xls": "spreadsheets",
    ".xlsx": "spreadsheets",
    ".jpg": "images",
    ".jpeg": "images",
    ".png": "images",
    ".tif": "images",
    ".tiff": "images",
    ".gif": "images",
    ".zip": "archives",
    ".rar": "archives",
    ".7z": "archives",
}

DEFAULT_DOC_TYPE = "other"


def get_db_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_document_folder(attachment: dict) -> str:
    """Determine the document type folder for an attachment."""
    # First try the document_type field
    doc_type = attachment.get("document_type")
    if doc_type and doc_type.lower() in DOCUMENT_TYPE_MAP:
        return DOCUMENT_TYPE_MAP[doc_type.lower()]

    # Fall back to extension
    filename = attachment.get("filename", "")
    ext = Path(filename).suffix.lower()
    return DOCUMENT_TYPE_MAP.get(ext, DEFAULT_DOC_TYPE)


def get_year_from_email(attachment: dict) -> str:
    """Extract year from email date or fall back to current year."""
    email_date = attachment.get("email_date")
    if email_date:
        try:
            # Try parsing various date formats
            for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                try:
                    dt = datetime.strptime(email_date[:19], fmt)
                    return str(dt.year)
                except ValueError:
                    continue
        except Exception:
            pass
    return str(datetime.now().year)


def sanitize_project_code(project_code: str) -> str:
    """Sanitize project code for use as folder name."""
    # Replace problematic characters
    sanitized = project_code.replace("/", "-").replace("\\", "-").replace(":", "-")
    sanitized = sanitized.replace("*", "").replace("?", "").replace('"', "")
    sanitized = sanitized.replace("<", "").replace(">", "").replace("|", "")
    return sanitized.strip()


def show_stats():
    """Show statistics about attachments and organization status."""
    conn = get_db_connection()
    cursor = conn.cursor()

    print("=" * 70)
    print("ATTACHMENT ORGANIZATION STATS")
    print("=" * 70)
    print()

    # Total attachments
    cursor.execute("SELECT COUNT(*) FROM email_attachments")
    total = cursor.fetchone()[0]

    # Already organized
    cursor.execute("SELECT COUNT(*) FROM email_attachments WHERE organized_path IS NOT NULL")
    organized = cursor.fetchone()[0]

    # With proposal links
    cursor.execute("SELECT COUNT(*) FROM email_attachments WHERE proposal_id IS NOT NULL")
    with_proposal = cursor.fetchone()[0]

    # With project_code
    cursor.execute("SELECT COUNT(*) FROM email_attachments WHERE project_code IS NOT NULL AND project_code != ''")
    with_project = cursor.fetchone()[0]

    # Organizable (has proposal link with project_code)
    cursor.execute("""
        SELECT COUNT(*)
        FROM email_attachments ea
        JOIN proposals p ON ea.proposal_id = p.proposal_id
        WHERE ea.organized_path IS NULL
        AND p.project_code IS NOT NULL AND p.project_code != ''
    """)
    organizable = cursor.fetchone()[0]

    # Source file exists
    cursor.execute("""
        SELECT ea.attachment_id, ea.filepath
        FROM email_attachments ea
        JOIN proposals p ON ea.proposal_id = p.proposal_id
        WHERE ea.organized_path IS NULL
        AND p.project_code IS NOT NULL AND p.project_code != ''
        LIMIT 10
    """)
    sample = cursor.fetchall()
    existing_files = sum(1 for row in sample if Path(row["filepath"]).exists())

    print(f"Total attachments:           {total:,}")
    print(f"Already organized:           {organized:,}")
    print(f"With proposal link:          {with_proposal:,}")
    print(f"With project_code:           {with_project:,}")
    print(f"Organizable (not organized): {organizable:,}")
    print()

    if sample:
        print(f"Sample file check (10): {existing_files}/10 files exist")

    # Top projects by attachment count
    print()
    print("-" * 70)
    print("TOP PROJECTS BY ATTACHMENT COUNT:")
    print("-" * 70)
    cursor.execute("""
        SELECT p.project_code, p.project_name, COUNT(*) as count
        FROM email_attachments ea
        JOIN proposals p ON ea.proposal_id = p.proposal_id
        WHERE p.project_code IS NOT NULL AND p.project_code != ''
        GROUP BY p.project_code
        ORDER BY count DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        name = (row["project_name"] or "")[:40]
        print(f"  {row['project_code']:15} {name:40} {row['count']:5}")

    # Document types
    print()
    print("-" * 70)
    print("DOCUMENT TYPES:")
    print("-" * 70)
    cursor.execute("""
        SELECT document_type, COUNT(*) as count
        FROM email_attachments
        WHERE document_type IS NOT NULL AND document_type != ''
        GROUP BY document_type
        ORDER BY count DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row['document_type']:20} {row['count']:5}")

    conn.close()


def organize_attachments(dry_run: bool = True):
    """Organize attachments into project folders."""
    conn = get_db_connection()
    cursor = conn.cursor()

    mode = "DRY RUN" if dry_run else "ORGANIZING"
    print("=" * 70)
    print(f"ORGANIZING ATTACHMENTS ({mode})")
    print("=" * 70)
    print()

    # Get all organizable attachments
    cursor.execute("""
        SELECT
            ea.attachment_id,
            ea.filename,
            ea.filepath,
            ea.document_type,
            p.project_code,
            p.project_name,
            e.date as email_date
        FROM email_attachments ea
        JOIN proposals p ON ea.proposal_id = p.proposal_id
        LEFT JOIN emails e ON ea.email_id = e.email_id
        WHERE ea.organized_path IS NULL
        AND p.project_code IS NOT NULL AND p.project_code != ''
        ORDER BY p.project_code, ea.filename
    """)

    attachments = cursor.fetchall()
    print(f"Found {len(attachments)} attachments to organize")
    print()

    organized_count = 0
    skipped_count = 0
    error_count = 0

    for att in attachments:
        try:
            source_path = Path(att["filepath"])

            # Skip if source doesn't exist
            if not source_path.exists():
                skipped_count += 1
                continue

            # Build destination path
            year = get_year_from_email(dict(att))
            project_folder = sanitize_project_code(att["project_code"])
            doc_folder = get_document_folder(dict(att))

            dest_dir = ATTACHMENTS_BASE / year / project_folder / doc_folder
            dest_path = dest_dir / att["filename"]

            # Handle duplicate filenames
            if dest_path.exists():
                stem = dest_path.stem
                suffix = dest_path.suffix
                counter = 1
                while dest_path.exists():
                    dest_path = dest_dir / f"{stem}_{counter}{suffix}"
                    counter += 1

            if dry_run:
                print(f"Would copy: {att['project_code']}/{doc_folder}/{att['filename']}")
            else:
                # Create directory if needed
                dest_dir.mkdir(parents=True, exist_ok=True)

                # Copy file (preserve original)
                shutil.copy2(source_path, dest_path)

                # Update database
                cursor.execute("""
                    UPDATE email_attachments
                    SET organized_path = ?,
                        project_code = ?,
                        organized_at = ?,
                        organized_by = 'organize_attachments.py'
                    WHERE attachment_id = ?
                """, [str(dest_path), att["project_code"], datetime.now().isoformat(), att["attachment_id"]])

                print(f"Organized: {att['project_code']}/{doc_folder}/{att['filename']}")

            organized_count += 1

        except Exception as e:
            error_count += 1
            print(f"ERROR processing {att['filename']}: {e}")

    if not dry_run:
        conn.commit()

    conn.close()

    print()
    print("-" * 70)
    print(f"SUMMARY:")
    print(f"  Organized: {organized_count}")
    print(f"  Skipped (file not found): {skipped_count}")
    print(f"  Errors: {error_count}")

    if dry_run:
        print()
        print("This was a dry run. Use --organize to actually move files.")


def main():
    parser = argparse.ArgumentParser(description="Organize email attachments by project")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without making them")
    parser.add_argument("--organize", action="store_true", help="Actually organize files")

    args = parser.parse_args()

    if not any([args.stats, args.dry_run, args.organize]):
        parser.print_help()
        return

    if args.stats:
        show_stats()
    elif args.dry_run:
        organize_attachments(dry_run=True)
    elif args.organize:
        response = input("This will copy files to organized folders. Continue? (y/N): ")
        if response.lower() == "y":
            organize_attachments(dry_run=False)
        else:
            print("Cancelled.")


if __name__ == "__main__":
    main()
