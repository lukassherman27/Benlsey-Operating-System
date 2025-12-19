#!/usr/bin/env python3
"""
File Organizer for Bensley Intelligence Platform

Helps organize existing project files into the new folder structure.

This tool:
1. Scans a source folder for documents
2. Identifies project codes in filenames
3. Suggests where each file should go
4. Optionally moves or copies files to correct locations

Usage:
    python backend/services/file_organizer.py --scan /path/to/old/projects
    python backend/services/file_organizer.py --scan /path/to/old/projects --move
    python backend/services/file_organizer.py --scan /path/to/old/projects --dry-run
"""

import os
import sys
import re
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class FileOrganizer:
    def __init__(self, source_path, target_path=None, dry_run=False, move=False):
        self.source_path = Path(source_path)
        self.target_path = Path(target_path) if target_path else Path("data")
        self.dry_run = dry_run
        self.move = move  # If False, copy instead
        self.stats = {
            'scanned': 0,
            'matched': 0,
            'unmatched': 0,
            'moved': 0,
            'errors': 0
        }

        # File type mappings
        self.file_type_map = {
            'contract': '01_CONTRACT',
            'agreement': '01_CONTRACT',
            'invoice': '02_INVOICING/invoices_sent',
            'payment': '02_INVOICING/payment_receipts',
            'receipt': '02_INVOICING/payment_receipts',
            'drawing': '03_DESIGN/architecture/current',
            'dwg': '03_DESIGN/architecture/current',
            'design': '03_DESIGN/architecture/current',
            'architecture': '03_DESIGN/architecture/current',
            'interior': '03_DESIGN/interiors',
            'landscape': '03_DESIGN/landscape',
            'schedule': '04_SCHEDULING/forward_schedule',
            'report': '04_SCHEDULING/daily_reports/by_date',
            'email': '05_CORRESPONDENCE/client_emails',
            'correspondence': '05_CORRESPONDENCE/client_emails',
            'submission': '06_SUBMISSIONS',
            'rfi': '07_RFIS',
            'meeting': '08_MEETINGS',
            'minutes': '08_MEETINGS',
            'photo': '09_PHOTOS',
            'image': '09_PHOTOS',
        }

        # Project code patterns
        self.project_code_patterns = [
            r'BK-\d{3,4}',  # BK-001, BK-0001
            r'BK\d{3,4}',   # BK001, BK0001
        ]

    def extract_project_code(self, filename):
        """Try to extract project code from filename"""
        for pattern in self.project_code_patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                code = match.group(0).upper()
                # Normalize to BK-XXX format
                if not '-' in code:
                    code = f"BK-{code[2:]}"
                return code
        return None

    def guess_file_type(self, filename):
        """Guess what type of file this is based on filename"""
        filename_lower = filename.lower()

        # Check file extensions first
        if filename_lower.endswith(('.pdf', '.doc', '.docx')):
            if 'contract' in filename_lower or 'agreement' in filename_lower:
                return '01_CONTRACT'
            elif 'invoice' in filename_lower:
                return '02_INVOICING/invoices_sent'
            elif 'payment' in filename_lower or 'receipt' in filename_lower:
                return '02_INVOICING/payment_receipts'
            elif 'meeting' in filename_lower or 'minutes' in filename_lower:
                return '08_MEETINGS'
            elif 'rfi' in filename_lower:
                return '07_RFIS'

        elif filename_lower.endswith(('.dwg', '.dxf', '.cad')):
            return '03_DESIGN/architecture/current'

        elif filename_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
            return '09_PHOTOS'

        elif filename_lower.endswith(('.xls', '.xlsx', '.csv')):
            if 'schedule' in filename_lower:
                return '04_SCHEDULING/forward_schedule'
            elif 'invoice' in filename_lower:
                return '02_INVOICING/invoices_sent'

        # Check keywords in filename
        for keyword, folder in self.file_type_map.items():
            if keyword in filename_lower:
                return folder

        return None

    def find_project_folder(self, project_code):
        """Find the project folder for a given project code"""
        # Search in all status folders
        status_folders = [
            '03_PROPOSALS',
            '04_ACTIVE_PROJECTS',
            '05_LEGAL_DISPUTES',
            '06_ARCHIVE'
        ]

        for status_folder in status_folders:
            folder_path = self.target_path / status_folder
            if folder_path.exists():
                for project_folder in folder_path.iterdir():
                    if project_folder.is_dir() and project_code in project_folder.name:
                        return project_folder

        return None

    def scan_files(self):
        """Scan source directory and categorize files"""
        print(f"\n📂 Scanning: {self.source_path}")
        print("-" * 70)

        categorized = defaultdict(list)
        uncategorized = []

        # Walk through all files
        for root, dirs, files in os.walk(self.source_path):
            for filename in files:
                # Skip hidden files and system files
                if filename.startswith('.') or filename.startswith('~'):
                    continue

                self.stats['scanned'] += 1
                file_path = Path(root) / filename

                # Try to extract project code
                project_code = self.extract_project_code(filename)

                # Try to guess file type
                file_type = self.guess_file_type(filename)

                if project_code and file_type:
                    categorized[project_code].append({
                        'path': file_path,
                        'filename': filename,
                        'type': file_type,
                        'size': file_path.stat().st_size
                    })
                    self.stats['matched'] += 1
                else:
                    uncategorized.append({
                        'path': file_path,
                        'filename': filename,
                        'project_code': project_code,
                        'type': file_type,
                        'size': file_path.stat().st_size
                    })
                    self.stats['unmatched'] += 1

        return categorized, uncategorized

    def format_size(self, size):
        """Format file size for display"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def organize_files(self, categorized):
        """Organize files into project folders"""
        print(f"\n📋 Organization Plan")
        print("=" * 70)

        if not categorized:
            print("   No files matched to projects")
            return

        # Show plan for each project
        for project_code, files in sorted(categorized.items()):
            project_folder = self.find_project_folder(project_code)

            if not project_folder:
                print(f"\n⚠️  {project_code} - Project folder not found!")
                print(f"   Files: {len(files)}")
                print(f"   Create project first with: python backend/services/project_creator.py")
                continue

            print(f"\n✅ {project_code} → {project_folder.name}")
            print(f"   Files to organize: {len(files)}")

            # Group by type
            by_type = defaultdict(list)
            for file_info in files:
                by_type[file_info['type']].append(file_info)

            for file_type, type_files in sorted(by_type.items()):
                print(f"   📁 {file_type}/")
                for file_info in type_files:
                    size_str = self.format_size(file_info['size'])
                    print(f"      - {file_info['filename']} ({size_str})")

            # Actually move/copy files if not dry run
            if not self.dry_run:
                action = "Moving" if self.move else "Copying"
                print(f"\n   {action} files...")

                for file_info in files:
                    try:
                        target_dir = project_folder / file_info['type']
                        target_dir.mkdir(parents=True, exist_ok=True)
                        target_file = target_dir / file_info['filename']

                        if self.move:
                            shutil.move(str(file_info['path']), str(target_file))
                        else:
                            shutil.copy2(str(file_info['path']), str(target_file))

                        self.stats['moved'] += 1
                    except Exception as e:
                        print(f"      ❌ Error with {file_info['filename']}: {e}")
                        self.stats['errors'] += 1

                print(f"   ✅ Complete")

    def show_uncategorized(self, uncategorized):
        """Show files that couldn't be automatically categorized"""
        if not uncategorized:
            return

        print(f"\n⚠️  Uncategorized Files ({len(uncategorized)})")
        print("=" * 70)
        print("These files need manual review:\n")

        for file_info in uncategorized[:20]:  # Show first 20
            print(f"   {file_info['filename']}")
            if file_info['project_code']:
                print(f"      Project: {file_info['project_code']} (folder not found)")
            if file_info['type']:
                print(f"      Type: {file_info['type']} (no project code)")
            print()

        if len(uncategorized) > 20:
            print(f"   ... and {len(uncategorized) - 20} more")

    def print_summary(self):
        """Print summary statistics"""
        print(f"\n{'='*70}")
        print("Summary")
        print(f"{'='*70}")
        print(f"Total files scanned: {self.stats['scanned']}")
        print(f"✅ Matched to projects: {self.stats['matched']}")
        print(f"⚠️  Unmatched: {self.stats['unmatched']}")

        if not self.dry_run:
            action = "moved" if self.move else "copied"
            print(f"📦 Files {action}: {self.stats['moved']}")
            if self.stats['errors'] > 0:
                print(f"❌ Errors: {self.stats['errors']}")

        print(f"{'='*70}\n")

    def run(self):
        """Run the file organization process"""
        print(f"\n{'='*70}")
        print("Bensley Intelligence Platform - File Organizer")
        print(f"{'='*70}")

        if self.dry_run:
            print("\n🔍 DRY RUN MODE - No files will be moved\n")

        if not self.source_path.exists():
            print(f"\n❌ ERROR: Source path not found: {self.source_path}")
            return False

        # Scan files
        categorized, uncategorized = self.scan_files()

        # Show organization plan
        self.organize_files(categorized)

        # Show uncategorized files
        self.show_uncategorized(uncategorized)

        # Print summary
        self.print_summary()

        if self.dry_run and categorized:
            print(f"💡 To actually organize files, run again without --dry-run")
            print(f"   Add --move to move files (default is copy)")

        return True


def main():
    parser = argparse.ArgumentParser(
        description='Organize existing files into Bensley project structure'
    )
    parser.add_argument(
        '--scan', '-s',
        required=True,
        help='Path to folder to scan'
    )
    parser.add_argument(
        '--target', '-t',
        help='Target data folder (default: ./data)'
    )
    parser.add_argument(
        '--move', '-m',
        action='store_true',
        help='Move files instead of copying'
    )
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Dry run - show what would be done without making changes'
    )

    args = parser.parse_args()

    organizer = FileOrganizer(
        source_path=args.scan,
        target_path=args.target,
        dry_run=args.dry_run,
        move=args.move
    )

    success = organizer.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
