#!/usr/bin/env python3
"""
Fix Hardcoded Database Paths

Scans all Python files and replaces hardcoded Desktop paths
with environment variable lookups.

Run with --dry-run to preview changes.
"""

import os
import re
from pathlib import Path
import argparse

# Patterns to find
OLD_PATTERNS = [
    r'"/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master\.db"',
    r"'/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master\.db'",
    r'Path\.home\(\)\s*/\s*"Desktop/BDS_SYSTEM/01_DATABASES/bensley_master\.db"',
    r"Path\.home\(\)\s*/\s*'Desktop/BDS_SYSTEM/01_DATABASES/bensley_master\.db'",
    r'os\.path\.expanduser\([\'"]~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master\.db[\'"]\)',
    r'~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master\.db',
]

# New pattern (using environment variable)
NEW_DB_PATH = "os.getenv('DATABASE_PATH', 'database/bensley_master.db')"

# Directories to scan
SCAN_DIRS = [
    'backend',
    'scripts',
    'database',
    'tracking',
]

# Files to skip (archived, deprecated)
SKIP_PATTERNS = [
    '/archive/',
    '/deprecated/',
    'one-time',
    'one_time',
]


def should_skip(filepath: str) -> bool:
    """Check if file should be skipped"""
    for pattern in SKIP_PATTERNS:
        if pattern in filepath:
            return True
    return False


def fix_file(filepath: Path, dry_run: bool = True) -> tuple[bool, list[str]]:
    """
    Fix hardcoded paths in a single file.

    Returns:
        (was_modified, list of changes made)
    """
    try:
        content = filepath.read_text()
    except Exception as e:
        return False, [f"Error reading: {e}"]

    changes = []
    new_content = content

    # Check if os is imported
    has_os_import = 'import os' in content or 'from os' in content

    for pattern in OLD_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            for match in matches:
                changes.append(f"  Found: {match[:60]}...")

            # Replace
            new_content = re.sub(pattern, NEW_DB_PATH, new_content)

    if new_content != content:
        # Add os import if needed
        if not has_os_import and 'os.getenv' in new_content:
            # Find first import and add os import after
            import_match = re.search(r'^import \w+', new_content, re.MULTILINE)
            if import_match:
                insert_pos = import_match.end()
                new_content = new_content[:insert_pos] + '\nimport os' + new_content[insert_pos:]
                changes.append("  Added: import os")

        if not dry_run:
            filepath.write_text(new_content)
            changes.append("  ✓ File updated")
        else:
            changes.append("  [DRY RUN] Would update file")

        return True, changes

    return False, []


def main():
    parser = argparse.ArgumentParser(description='Fix hardcoded database paths')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Preview changes without modifying files (default)')
    parser.add_argument('--apply', action='store_true',
                        help='Actually apply the changes')
    args = parser.parse_args()

    dry_run = not args.apply

    # Find project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent

    print("=" * 60)
    print("Hardcoded Path Fixer")
    print("=" * 60)
    print(f"Project root: {project_root}")
    print(f"Mode: {'DRY RUN' if dry_run else 'APPLYING CHANGES'}")
    print()

    total_files = 0
    modified_files = 0
    skipped_files = 0

    for scan_dir in SCAN_DIRS:
        dir_path = project_root / scan_dir
        if not dir_path.exists():
            continue

        for py_file in dir_path.rglob('*.py'):
            total_files += 1
            rel_path = py_file.relative_to(project_root)

            if should_skip(str(rel_path)):
                skipped_files += 1
                continue

            was_modified, changes = fix_file(py_file, dry_run)

            if was_modified:
                modified_files += 1
                print(f"\n{rel_path}")
                for change in changes:
                    print(change)

    print()
    print("=" * 60)
    print(f"Total files scanned: {total_files}")
    print(f"Files modified: {modified_files}")
    print(f"Files skipped (archived): {skipped_files}")
    print("=" * 60)

    if dry_run and modified_files > 0:
        print()
        print("To apply changes, run:")
        print("  python scripts/maintenance/fix_hardcoded_paths.py --apply")


if __name__ == "__main__":
    main()
