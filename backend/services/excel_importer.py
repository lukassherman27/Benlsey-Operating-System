#!/usr/bin/env python3
"""
Excel Project Importer for Bensley Intelligence Platform

Imports projects from Excel files into the database and creates folder structures.

Expected Excel format:
- Column A: Project Code (BK-001)
- Column B: Project Name
- Column C: Client Name (who pays)
- Column D: Operator Name (hotel brand)
- Column E: Contract Value (number)
- Column F: Status (active/proposal/completed)
- Column G: Start Date (optional)
- Column H: Completion Target (optional)

Usage:
    python backend/services/excel_importer.py --file path/to/projects.xlsx
    python backend/services/excel_importer.py --file path/to/projects.xlsx --sheet "Active Projects"
    python backend/services/excel_importer.py --file path/to/projects.xlsx --dry-run
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

try:
    import pandas as pd
    import openpyxl
except ImportError:
    print("ERROR: Missing required packages. Install with:")
    print("pip install pandas openpyxl")
    sys.exit(1)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.project_creator import ProjectCreator


class ExcelProjectImporter:
    def __init__(self, excel_path, sheet_name=None, dry_run=False):
        self.excel_path = excel_path
        self.sheet_name = sheet_name
        self.dry_run = dry_run
        self.project_creator = ProjectCreator()
        self.stats = {
            'processed': 0,
            'created': 0,
            'skipped': 0,
            'errors': 0
        }

    def read_excel(self):
        """Read Excel file and return DataFrame"""
        print(f"📖 Reading Excel file: {self.excel_path}")

        if not os.path.exists(self.excel_path):
            print(f"❌ ERROR: File not found: {self.excel_path}")
            return None

        try:
            # Read Excel file
            if self.sheet_name:
                df = pd.read_excel(self.excel_path, sheet_name=self.sheet_name)
                print(f"   Using sheet: {self.sheet_name}")
            else:
                df = pd.read_excel(self.excel_path)
                print(f"   Using first sheet")

            print(f"   Found {len(df)} rows")
            return df

        except Exception as e:
            print(f"❌ ERROR reading Excel: {e}")
            return None

    def normalize_column_names(self, df):
        """Normalize column names to handle variations"""
        # Map of possible column names to standard names
        column_mapping = {
            'project_code': ['project code', 'code', 'project_code', 'project id', 'id'],
            'project_name': ['project name', 'name', 'project_name', 'project', 'title'],
            'client': ['client', 'client name', 'client_name', 'developer', 'owner'],
            'operator': ['operator', 'operator name', 'operator_name', 'brand', 'hotel brand'],
            'contract_value': ['contract value', 'contract_value', 'value', 'amount', 'contract'],
            'status': ['status', 'project status', 'state'],
            'start_date': ['start date', 'start_date', 'start', 'began'],
            'completion_target': ['completion target', 'completion_target', 'target', 'end date', 'completion']
        }

        # Create normalized DataFrame
        normalized = {}
        df_columns_lower = [col.lower().strip() for col in df.columns]

        for standard_name, variations in column_mapping.items():
            for var in variations:
                if var in df_columns_lower:
                    original_col = df.columns[df_columns_lower.index(var)]
                    normalized[standard_name] = df[original_col]
                    break

        return pd.DataFrame(normalized)

    def validate_row(self, row, row_num):
        """Validate required fields in row"""
        errors = []

        if pd.isna(row.get('project_code')) or not str(row.get('project_code')).strip():
            errors.append(f"Missing project code")

        if pd.isna(row.get('project_name')) or not str(row.get('project_name')).strip():
            errors.append(f"Missing project name")

        if pd.isna(row.get('client')) or not str(row.get('client')).strip():
            errors.append(f"Missing client name")

        if errors:
            print(f"   ⚠️  Row {row_num}: {', '.join(errors)}")
            return False

        return True

    def import_row(self, row, row_num):
        """Import a single project row"""
        self.stats['processed'] += 1

        # Validate
        if not self.validate_row(row, row_num):
            self.stats['skipped'] += 1
            return False

        # Extract data
        project_code = str(row['project_code']).strip().upper()
        project_name = str(row['project_name']).strip()
        client_name = str(row['client']).strip()
        operator_name = str(row.get('operator', '')).strip() if pd.notna(row.get('operator')) else None

        # Parse contract value
        try:
            contract_value = float(row.get('contract_value', 0)) if pd.notna(row.get('contract_value')) else 0
        except (ValueError, TypeError):
            contract_value = 0

        # Status
        status = str(row.get('status', 'active')).strip().lower() if pd.notna(row.get('status')) else 'active'
        if status not in ['active', 'proposal', 'completed', 'on_hold']:
            status = 'active'

        # Dates
        start_date = None
        completion_target = None

        if pd.notna(row.get('start_date')):
            try:
                if isinstance(row['start_date'], datetime):
                    start_date = row['start_date'].strftime('%Y-%m-%d')
                else:
                    start_date = pd.to_datetime(row['start_date']).strftime('%Y-%m-%d')
            except:
                pass

        if pd.notna(row.get('completion_target')):
            try:
                if isinstance(row['completion_target'], datetime):
                    completion_target = row['completion_target'].strftime('%Y-%m-%d')
                else:
                    completion_target = pd.to_datetime(row['completion_target']).strftime('%Y-%m-%d')
            except:
                pass

        # Print what we're about to create
        print(f"\n   📦 Row {row_num}: {project_code} - {project_name}")
        print(f"      Client: {client_name}")
        if operator_name:
            print(f"      Operator: {operator_name}")
        if contract_value > 0:
            print(f"      Value: ${contract_value:,.2f}")
        print(f"      Status: {status}")

        if self.dry_run:
            print(f"      [DRY RUN - Would create project]")
            self.stats['created'] += 1
            return True

        # Create project
        try:
            result = self.project_creator.create_project(
                project_code=project_code,
                project_name=project_name,
                client_name=client_name,
                operator_name=operator_name,
                contract_value=contract_value,
                status=status,
                start_date=start_date,
                completion_target=completion_target
            )

            if result:
                print(f"      ✅ Created successfully")
                self.stats['created'] += 1
                return True
            else:
                print(f"      ⚠️  Already exists, skipped")
                self.stats['skipped'] += 1
                return False

        except Exception as e:
            print(f"      ❌ ERROR: {e}")
            self.stats['errors'] += 1
            return False

    def import_all(self):
        """Import all projects from Excel"""
        print(f"\n{'='*60}")
        print(f"Bensley Intelligence Platform - Excel Project Importer")
        print(f"{'='*60}\n")

        if self.dry_run:
            print("🔍 DRY RUN MODE - No changes will be made\n")

        # Read Excel
        df = self.read_excel()
        if df is None:
            return False

        # Normalize columns
        df = self.normalize_column_names(df)

        print(f"\n📊 Columns found: {', '.join(df.columns)}")

        # Check for required columns
        if 'project_code' not in df.columns:
            print(f"\n❌ ERROR: Could not find 'Project Code' column")
            print(f"   Available columns: {', '.join(df.columns)}")
            return False

        print(f"\n🚀 Starting import...\n")

        # Import each row
        for idx, row in df.iterrows():
            self.import_row(row, idx + 2)  # +2 because Excel is 1-indexed and has header

        # Print summary
        print(f"\n{'='*60}")
        print(f"Import Summary")
        print(f"{'='*60}")
        print(f"Total rows processed: {self.stats['processed']}")
        print(f"✅ Successfully created: {self.stats['created']}")
        print(f"⚠️  Skipped (already exist): {self.stats['skipped']}")
        print(f"❌ Errors: {self.stats['errors']}")
        print(f"{'='*60}\n")

        if not self.dry_run and self.stats['created'] > 0:
            print(f"✨ Import complete! Check data/04_ACTIVE_PROJECTS/ for new folders")
            print(f"💾 Database updated: {self.project_creator.data_root / 'database' / 'bensley_master.db'}")

        return True


def main():
    parser = argparse.ArgumentParser(
        description='Import projects from Excel into Bensley Intelligence Platform'
    )
    parser.add_argument(
        '--file', '-f',
        required=True,
        help='Path to Excel file'
    )
    parser.add_argument(
        '--sheet', '-s',
        help='Sheet name (default: first sheet)'
    )
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Dry run - show what would be imported without making changes'
    )

    args = parser.parse_args()

    # Create importer
    importer = ExcelProjectImporter(
        excel_path=args.file,
        sheet_name=args.sheet,
        dry_run=args.dry_run
    )

    # Run import
    success = importer.import_all()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
