#!/usr/bin/env python3
"""
Codebase Health Check Script

Runs automated checks to verify codebase organization and data quality.
Use: python scripts/core/health_check.py
"""

import os
import sqlite3
import sys
from pathlib import Path

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
CHECK = "✓"
CROSS = "✗"
WARN = "⚠"


def print_status(passed: bool, message: str, warning: bool = False):
    """Print a status line."""
    if warning:
        print(f"  {YELLOW}{WARN}{RESET} {message}")
    elif passed:
        print(f"  {GREEN}{CHECK}{RESET} {message}")
    else:
        print(f"  {RED}{CROSS}{RESET} {message}")


def get_project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent.parent


def check_file_organization(root: Path) -> tuple[int, int]:
    """Check file organization standards."""
    passed = 0
    failed = 0

    print("\n📁 File Organization")
    print("-" * 40)

    # Check no Python scripts at root
    root_py = list(root.glob("*.py"))
    if len(root_py) == 0:
        print_status(True, "No Python scripts at root")
        passed += 1
    else:
        print_status(False, f"{len(root_py)} Python scripts at root (should be 0)")
        failed += 1

    # Check no shell scripts at root
    root_sh = list(root.glob("*.sh"))
    if len(root_sh) == 0:
        print_status(True, "No shell scripts at root")
        passed += 1
    else:
        print_status(False, f"{len(root_sh)} shell scripts at root")
        failed += 1

    # Check limited markdown at root
    allowed_md = {"README.md", "CLAUDE.md", "CONTRIBUTING.md", "CHANGELOG.md", "LICENSE.md"}
    root_md = {f.name for f in root.glob("*.md")}
    extra_md = root_md - allowed_md
    if len(extra_md) == 0:
        print_status(True, f"Only {len(root_md)} allowed markdown files at root")
        passed += 1
    elif len(extra_md) <= 3:
        print_status(False, f"{len(extra_md)} extra markdown at root", warning=True)
        passed += 1  # Warning, not failure
    else:
        print_status(False, f"{len(extra_md)} unexpected markdown files at root")
        failed += 1

    # Check required directories exist
    required_dirs = [
        "backend/api",
        "backend/services",
        "frontend/src",
        "database/migrations",
        "scripts/core",
        "docs",
        "tests",
    ]
    for dir_path in required_dirs:
        if (root / dir_path).exists():
            passed += 1
        else:
            print_status(False, f"Missing directory: {dir_path}")
            failed += 1

    if failed == 0:
        print_status(True, f"All {len(required_dirs)} required directories exist")

    return passed, failed


def check_database(root: Path) -> tuple[int, int]:
    """Check database health."""
    passed = 0
    failed = 0

    print("\n🗄️  Database Health")
    print("-" * 40)

    db_path = root / "database" / "bensley_master.db"

    if not db_path.exists():
        print_status(False, "Database file not found!")
        return 0, 1

    print_status(True, f"Database exists ({db_path.stat().st_size / 1024 / 1024:.1f} MB)")
    passed += 1

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check core tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        core_tables = ["projects", "proposals", "invoices", "emails", "contacts"]
        missing_tables = [t for t in core_tables if t not in tables]

        if not missing_tables:
            print_status(True, f"All {len(core_tables)} core tables exist")
            passed += 1
        else:
            print_status(False, f"Missing tables: {missing_tables}")
            failed += 1

        # Check data counts
        counts = {}
        for table in core_tables:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cursor.fetchone()[0]

        print(f"\n  Data counts:")
        for table, count in counts.items():
            status = count > 0
            print_status(status, f"{table}: {count:,} records")
            if status:
                passed += 1
            else:
                failed += 1

        # Check for orphaned records
        cursor.execute("""
            SELECT COUNT(*) FROM invoices i
            WHERE i.project_id IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_id = i.project_id)
        """)
        orphaned = cursor.fetchone()[0]
        if orphaned == 0:
            print_status(True, "No orphaned invoice records")
            passed += 1
        else:
            print_status(False, f"{orphaned} orphaned invoices", warning=True)

        conn.close()

    except sqlite3.Error as e:
        print_status(False, f"Database error: {e}")
        failed += 1

    return passed, failed


def check_config_files(root: Path) -> tuple[int, int]:
    """Check configuration files."""
    passed = 0
    failed = 0

    print("\n⚙️  Configuration Files")
    print("-" * 40)

    required_configs = [
        ".gitignore",
        "pyproject.toml",
        "Makefile",
        "requirements.txt",
        ".env.example",
    ]

    for config in required_configs:
        if (root / config).exists():
            print_status(True, f"{config} exists")
            passed += 1
        else:
            print_status(False, f"{config} missing")
            failed += 1

    # Check .env exists (warning only)
    if (root / ".env").exists():
        print_status(True, ".env configured")
        passed += 1
    else:
        print_status(False, ".env not configured (copy from .env.example)", warning=True)

    return passed, failed


def check_services(root: Path) -> tuple[int, int]:
    """Check backend services."""
    passed = 0
    failed = 0

    print("\n🔧 Backend Services")
    print("-" * 40)

    services_dir = root / "backend" / "services"
    if not services_dir.exists():
        print_status(False, "Services directory missing!")
        return 0, 1

    service_files = list(services_dir.glob("*.py"))
    service_count = len([f for f in service_files if not f.name.startswith("_")])

    print_status(True, f"{service_count} service files")
    passed += 1

    # Check no debug files in services
    debug_files = [f.name for f in service_files if f.name.startswith(("debug_", "test_"))]
    if not debug_files:
        print_status(True, "No debug/test files in services/")
        passed += 1
    else:
        print_status(False, f"Debug files in services: {debug_files}")
        failed += 1

    # Check __init__.py exists
    if (services_dir / "__init__.py").exists():
        print_status(True, "__init__.py exists")
        passed += 1
    else:
        print_status(False, "__init__.py missing")
        failed += 1

    return passed, failed


def check_git_status(root: Path) -> tuple[int, int]:
    """Check git repository status."""
    passed = 0
    failed = 0

    print("\n📦 Git Repository")
    print("-" * 40)

    if (root / ".git").exists():
        print_status(True, "Git repository initialized")
        passed += 1
    else:
        print_status(False, "Not a git repository")
        return 0, 1

    # Check for .DS_Store files
    ds_store = list(root.rglob(".DS_Store"))
    if len(ds_store) == 0:
        print_status(True, "No .DS_Store files")
        passed += 1
    else:
        print_status(False, f"{len(ds_store)} .DS_Store files (run: make clean)", warning=True)

    return passed, failed


def main():
    """Run all health checks."""
    root = get_project_root()

    print("=" * 50)
    print("🏥 Bensley Operations Platform - Health Check")
    print("=" * 50)

    total_passed = 0
    total_failed = 0

    # Run all checks
    checks = [
        check_file_organization,
        check_database,
        check_config_files,
        check_services,
        check_git_status,
    ]

    for check in checks:
        passed, failed = check(root)
        total_passed += passed
        total_failed += failed

    # Summary
    print("\n" + "=" * 50)
    total = total_passed + total_failed
    score = (total_passed / total * 100) if total > 0 else 0

    if total_failed == 0:
        print(f"{GREEN}All {total_passed} checks passed! Score: {score:.0f}%{RESET}")
    else:
        print(f"Results: {GREEN}{total_passed} passed{RESET}, {RED}{total_failed} failed{RESET}")
        print(f"Health Score: {score:.0f}%")

    print("=" * 50)

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
