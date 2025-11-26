#!/usr/bin/env python3
"""
Invoice Import Script - From CSV (Codex Parser Output)

Imports invoices from Codex's CSV parser output with full validation and audit trail.

Usage:
    python import_invoices_from_csv.py --csv reports/invoice_export.csv --pdf "/Users/lukassherman/Desktop/Project Status as of 10 Nov 25 (Updated).pdf"

CSV Expected Columns:
    project_code, project_name, invoice_number, invoice_date, invoice_amount,
    payment_date, payment_amount, phase, discipline, component_label,
    description, percentage, pdf_page, needs_review, suggested_parent_code
"""

import sqlite3
import csv
import argparse
from datetime import datetime
from typing import Dict, List, Tuple
import json

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


class InvoiceImporter:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.source_doc_id = None
        self.stats = {
            'total_rows': 0,
            'imported': 0,
            'skipped_duplicates': 0,
            'skipped_invalid': 0,
            'flagged_for_review': 0,
            'warnings': [],
            'errors': []
        }

    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def register_source_pdf(self, pdf_path: str, document_date: str) -> int:
        """Register the source PDF in documents table"""
        cursor = self.conn.cursor()

        # Check if already registered
        cursor.execute("""
            SELECT document_id FROM documents
            WHERE file_path = ? AND document_type = 'finance_report'
        """, (pdf_path,))
        existing = cursor.fetchone()

        if existing:
            print(f"✓ Source PDF already registered (document_id: {existing[0]})")
            return existing[0]

        # Generate new document_id
        cursor.execute("SELECT MAX(document_id) FROM documents")
        max_id = cursor.fetchone()[0] or 0
        document_id = max_id + 1

        # Extract filename
        file_name = pdf_path.split('/')[-1]

        # Insert document record
        cursor.execute("""
            INSERT INTO documents (
                document_id, project_code, document_type, file_path,
                file_name, file_type, document_date, status, created_date
            ) VALUES (?, NULL, 'finance_report', ?, ?, 'pdf', ?, 'current', ?)
        """, (document_id, pdf_path, file_name, document_date, datetime.now().isoformat()))

        self.conn.commit()
        print(f"✓ Registered source PDF (document_id: {document_id})")
        return document_id

    def validate_project_exists(self, project_code: str) -> bool:
        """Check if project exists in database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM projects WHERE project_code = ?", (project_code,))
        return cursor.fetchone() is not None

    def check_duplicate_invoice(self, invoice_number: str) -> bool:
        """Check if invoice number already exists"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM invoices WHERE invoice_number = ?", (invoice_number,))
        return cursor.fetchone() is not None

    def validate_row(self, row: Dict) -> Tuple[bool, List[str]]:
        """Validate a single CSV row"""
        errors = []

        # Required fields
        if not row.get('project_code'):
            errors.append("Missing project_code")
        if not row.get('invoice_number'):
            errors.append("Missing invoice_number")
        if not row.get('invoice_amount'):
            errors.append("Missing invoice_amount")

        # Project exists
        if row.get('project_code') and not self.validate_project_exists(row['project_code']):
            errors.append(f"Project {row['project_code']} not found in database")

        # Invoice amount is positive
        try:
            amount = float(row.get('invoice_amount', 0))
            if amount <= 0:
                errors.append(f"Invalid invoice_amount: {amount}")
        except (ValueError, TypeError):
            errors.append(f"Invalid invoice_amount format: {row.get('invoice_amount')}")

        # Valid dates
        if row.get('invoice_date'):
            try:
                datetime.fromisoformat(row['invoice_date'])
            except ValueError:
                errors.append(f"Invalid invoice_date format: {row['invoice_date']}")

        if row.get('payment_date'):
            try:
                datetime.fromisoformat(row['payment_date'])
            except ValueError:
                errors.append(f"Invalid payment_date format: {row['payment_date']}")

        return len(errors) == 0, errors

    def import_row(self, row: Dict, row_number: int) -> bool:
        """Import a single invoice row"""
        cursor = self.conn.cursor()

        # Check for duplicate
        if self.check_duplicate_invoice(row['invoice_number']):
            self.stats['skipped_duplicates'] += 1
            warning = f"Row {row_number}: Duplicate invoice {row['invoice_number']} - SKIPPED"
            print(f"⚠️  {warning}")
            self.stats['warnings'].append(warning)
            return False

        # Validate row
        valid, errors = self.validate_row(row)
        if not valid:
            self.stats['skipped_invalid'] += 1
            error_msg = f"Row {row_number}: Validation failed - {', '.join(errors)}"
            print(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return False

        # Flag for review if needed
        if row.get('needs_review') in ('true', 'True', '1', 1, True):
            self.stats['flagged_for_review'] += 1
            print(f"🚩 Row {row_number}: Flagged for review - {row.get('component_label', 'Complex case')}")

        # Generate invoice_id
        cursor.execute("SELECT MAX(invoice_id) FROM invoices")
        max_id = cursor.fetchone()[0] or 0
        invoice_id = max_id + 1

        # Calculate due_date (30 days default if not provided)
        due_date = row.get('due_date')
        if not due_date and row.get('invoice_date'):
            try:
                invoice_dt = datetime.fromisoformat(row['invoice_date'])
                from datetime import timedelta
                due_dt = invoice_dt + timedelta(days=30)
                due_date = due_dt.date().isoformat()
            except:
                due_date = None

        # Determine status
        status = 'paid' if row.get('payment_date') else 'outstanding'

        # Insert invoice
        cursor.execute("""
            INSERT INTO invoices (
                invoice_id, invoice_number, invoice_date, due_date,
                invoice_amount, payment_date, payment_amount, status,
                project_code, phase, discipline, description,
                source_document_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_id,
            row['invoice_number'],
            row.get('invoice_date'),
            due_date,
            float(row['invoice_amount']),
            row.get('payment_date'),
            float(row['payment_amount']) if row.get('payment_amount') else None,
            status,
            row['project_code'],
            row.get('phase'),
            row.get('discipline'),
            row.get('description'),
            self.source_doc_id,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

        self.stats['imported'] += 1

        # Show progress every 10 rows
        if self.stats['imported'] % 10 == 0:
            print(f"  ... {self.stats['imported']} invoices imported")

        return True

    def import_csv(self, csv_path: str) -> Dict:
        """Import all invoices from CSV"""
        print(f"\n📄 Reading CSV: {csv_path}")

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.stats['total_rows'] = len(rows)
        print(f"✓ Found {len(rows)} rows")

        print("\n🔄 Importing invoices...")
        for idx, row in enumerate(rows, 1):
            self.import_row(row, idx)

        self.conn.commit()
        return self.stats

    def print_summary(self):
        """Print import summary"""
        print("\n" + "="*80)
        print("IMPORT SUMMARY")
        print("="*80)
        print(f"Total rows:           {self.stats['total_rows']}")
        print(f"✅ Imported:          {self.stats['imported']}")
        print(f"⚠️  Duplicates skipped: {self.stats['skipped_duplicates']}")
        print(f"❌ Invalid rows:      {self.stats['skipped_invalid']}")
        print(f"🚩 Flagged for review: {self.stats['flagged_for_review']}")

        if self.stats['warnings']:
            print(f"\n⚠️  Warnings ({len(self.stats['warnings'])}):")
            for warning in self.stats['warnings'][:10]:  # Show first 10
                print(f"   {warning}")
            if len(self.stats['warnings']) > 10:
                print(f"   ... and {len(self.stats['warnings']) - 10} more")

        if self.stats['errors']:
            print(f"\n❌ Errors ({len(self.stats['errors'])}):")
            for error in self.stats['errors'][:10]:  # Show first 10
                print(f"   {error}")
            if len(self.stats['errors']) > 10:
                print(f"   ... and {len(self.stats['errors']) - 10} more")

        print("="*80)

    def save_log(self, log_path: str):
        """Save import log to JSON file"""
        log_data = {
            'import_timestamp': datetime.now().isoformat(),
            'source_document_id': self.source_doc_id,
            'statistics': self.stats
        }

        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)

        print(f"\n💾 Log saved to: {log_path}")


def main():
    parser = argparse.ArgumentParser(description='Import invoices from CSV')
    parser.add_argument('--csv', required=True, help='Path to CSV file from Codex parser')
    parser.add_argument('--pdf', required=True, help='Path to source PDF file')
    parser.add_argument('--pdf-date', default=None, help='PDF document date (YYYY-MM-DD, defaults to today)')
    parser.add_argument('--log', default='reports/invoice_import_log.json', help='Path to save import log')
    parser.add_argument('--dry-run', action='store_true', help='Validate only, do not import')

    args = parser.parse_args()

    # Default PDF date to today if not provided
    pdf_date = args.pdf_date or datetime.now().date().isoformat()

    print("="*80)
    print("INVOICE IMPORT - FROM CSV")
    print("="*80)
    print(f"CSV:        {args.csv}")
    print(f"Source PDF: {args.pdf}")
    print(f"PDF Date:   {pdf_date}")
    print(f"Database:   {DB_PATH}")

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No data will be imported")

    # Initialize importer
    importer = InvoiceImporter(DB_PATH)
    importer.connect()

    try:
        # Register source PDF
        importer.source_doc_id = importer.register_source_pdf(args.pdf, pdf_date)

        if not args.dry_run:
            # Import CSV
            importer.import_csv(args.csv)
        else:
            # Dry run - just validate
            print("\n🔍 Validating CSV (dry run)...")
            with open(args.csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader, 1):
                    valid, errors = importer.validate_row(row)
                    if not valid:
                        print(f"❌ Row {idx}: {', '.join(errors)}")
                    elif row.get('needs_review') in ('true', 'True', '1', 1, True):
                        print(f"🚩 Row {idx}: Flagged for review")

        # Print summary
        importer.print_summary()

        if not args.dry_run:
            # Save log
            importer.save_log(args.log)

    finally:
        importer.close()

    print("\n✅ Import complete!")


if __name__ == "__main__":
    main()
