#!/usr/bin/env python3
"""
Smoke Test Script - Pre/Post Session Verification

Run this BEFORE and AFTER every Claude session to verify system health.

Checks:
1. Database connects
2. /api/proposals returns data
3. Frontend builds (npm run build)
4. No orphaned FK references

Usage: python scripts/core/smoke_test.py
       python scripts/core/smoke_test.py --quick  (skip frontend build)
"""

import os
import sqlite3
import subprocess
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
CHECK = "\u2713"
CROSS = "\u2717"
WARN = "\u26a0"


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


def check_database_connects(root: Path) -> tuple[bool, str]:
    """
    Check 1: Database connects and has data.
    """
    print(f"\n{BLUE}1. Database Connection{RESET}")
    print("-" * 40)

    db_path = root / "database" / "bensley_master.db"

    if not db_path.exists():
        print_status(False, f"Database not found: {db_path}")
        return False, "Database file missing"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verify we can query
        cursor.execute("SELECT COUNT(*) FROM proposals")
        proposal_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM emails")
        email_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM projects")
        project_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM contacts")
        contact_count = cursor.fetchone()[0]

        conn.close()

        print_status(True, f"Database connected ({db_path.stat().st_size / 1024 / 1024:.1f} MB)")
        print_status(True, f"Proposals: {proposal_count}")
        print_status(True, f"Emails: {email_count}")
        print_status(True, f"Projects: {project_count}")
        print_status(True, f"Contacts: {contact_count}")

        if proposal_count == 0:
            print_status(False, "No proposals in database!", warning=True)
            return False, "No proposals"

        return True, f"OK - {proposal_count} proposals, {email_count} emails"

    except sqlite3.Error as e:
        print_status(False, f"Database error: {e}")
        return False, str(e)


def check_api_proposals(root: Path) -> tuple[bool, str]:
    """
    Check 2: /api/proposals returns data.
    """
    print(f"\n{BLUE}2. API Endpoint Check{RESET}")
    print("-" * 40)

    api_url = "http://localhost:8000/api/proposals?per_page=5"

    try:
        req = urllib.request.Request(api_url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

            # Check response structure
            if isinstance(data, dict):
                items = data.get("items", data.get("data", []))
                total = data.get("total", len(items))
            else:
                items = data if isinstance(data, list) else []
                total = len(items)

            print_status(True, f"API responded: {response.status}")
            print_status(True, f"Total proposals: {total}")
            print_status(True, f"Sample returned: {len(items)} items")

            if total == 0:
                print_status(False, "API returned 0 proposals", warning=True)
                return False, "No proposals returned"

            return True, f"OK - {total} proposals"

    except urllib.error.URLError as e:
        print_status(False, f"API not reachable: {e.reason}")
        print_status(False, "Is backend running? (uvicorn api.main:app --port 8000)", warning=True)
        return False, f"API unreachable: {e.reason}"
    except json.JSONDecodeError as e:
        print_status(False, f"Invalid JSON response: {e}")
        return False, "Invalid JSON"
    except Exception as e:
        print_status(False, f"API error: {e}")
        return False, str(e)


def check_frontend_build(root: Path) -> tuple[bool, str]:
    """
    Check 3: Frontend builds without errors.
    """
    print(f"\n{BLUE}3. Frontend Build{RESET}")
    print("-" * 40)

    frontend_dir = root / "frontend"

    if not (frontend_dir / "package.json").exists():
        print_status(False, "frontend/package.json not found")
        return False, "Missing package.json"

    print_status(True, "Running npm run build (this may take 30-60s)...")

    try:
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            timeout=180  # 3 minute timeout
        )

        if result.returncode == 0:
            print_status(True, "Frontend build successful")
            return True, "Build OK"
        else:
            # Extract key error info
            stderr = result.stderr or result.stdout
            error_lines = [l for l in stderr.split("\n") if "error" in l.lower()][:5]

            print_status(False, "Frontend build failed")
            for line in error_lines:
                print(f"    {line[:100]}")

            return False, "Build failed"

    except subprocess.TimeoutExpired:
        print_status(False, "Build timed out (>3 minutes)")
        return False, "Build timeout"
    except FileNotFoundError:
        print_status(False, "npm not found - is Node.js installed?")
        return False, "npm not found"
    except Exception as e:
        print_status(False, f"Build error: {e}")
        return False, str(e)


def check_orphaned_fk(root: Path) -> tuple[bool, str]:
    """
    Check 4: No orphaned foreign key references.
    """
    print(f"\n{BLUE}4. Foreign Key Integrity{RESET}")
    print("-" * 40)

    db_path = root / "database" / "bensley_master.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        orphans = []

        # Check email_proposal_links -> emails
        cursor.execute("""
            SELECT COUNT(*) FROM email_proposal_links epl
            WHERE NOT EXISTS (SELECT 1 FROM emails e WHERE e.email_id = epl.email_id)
        """)
        count = cursor.fetchone()[0]
        if count > 0:
            orphans.append(f"email_proposal_links -> emails: {count}")

        # Check email_proposal_links -> proposals
        cursor.execute("""
            SELECT COUNT(*) FROM email_proposal_links epl
            WHERE NOT EXISTS (SELECT 1 FROM proposals p WHERE p.proposal_id = epl.proposal_id)
        """)
        count = cursor.fetchone()[0]
        if count > 0:
            orphans.append(f"email_proposal_links -> proposals: {count}")

        # Check email_project_links -> emails
        cursor.execute("""
            SELECT COUNT(*) FROM email_project_links epl
            WHERE NOT EXISTS (SELECT 1 FROM emails e WHERE e.email_id = epl.email_id)
        """)
        count = cursor.fetchone()[0]
        if count > 0:
            orphans.append(f"email_project_links -> emails: {count}")

        # Check email_project_links -> projects
        cursor.execute("""
            SELECT COUNT(*) FROM email_project_links epl
            WHERE NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_id = epl.project_id)
        """)
        count = cursor.fetchone()[0]
        if count > 0:
            orphans.append(f"email_project_links -> projects: {count}")

        # Check invoices -> projects
        cursor.execute("""
            SELECT COUNT(*) FROM invoices i
            WHERE i.project_id IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_id = i.project_id)
        """)
        count = cursor.fetchone()[0]
        if count > 0:
            orphans.append(f"invoices -> projects: {count}")

        # Check email_attachments -> emails
        cursor.execute("""
            SELECT COUNT(*) FROM email_attachments ea
            WHERE NOT EXISTS (SELECT 1 FROM emails e WHERE e.email_id = ea.email_id)
        """)
        count = cursor.fetchone()[0]
        if count > 0:
            orphans.append(f"email_attachments -> emails: {count}")

        # Check project_contact_links -> contacts
        cursor.execute("""
            SELECT COUNT(*) FROM project_contact_links pcl
            WHERE NOT EXISTS (SELECT 1 FROM contacts c WHERE c.contact_id = pcl.contact_id)
        """)
        count = cursor.fetchone()[0]
        if count > 0:
            orphans.append(f"project_contact_links -> contacts: {count}")

        # Check project_contact_links -> projects
        cursor.execute("""
            SELECT COUNT(*) FROM project_contact_links pcl
            WHERE pcl.project_code IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_code = pcl.project_code)
        """)
        count = cursor.fetchone()[0]
        if count > 0:
            orphans.append(f"project_contact_links -> projects: {count}")

        conn.close()

        if not orphans:
            print_status(True, "No orphaned FK references found")
            print_status(True, "Checked: email_proposal_links, email_project_links")
            print_status(True, "Checked: invoices, email_attachments, project_contact_links")
            return True, "No orphans"
        else:
            for orphan in orphans:
                print_status(False, f"Orphaned: {orphan}")
            return False, f"{len(orphans)} orphan issues"

    except sqlite3.Error as e:
        print_status(False, f"Database error: {e}")
        return False, str(e)


def main():
    """Run smoke tests."""
    quick_mode = "--quick" in sys.argv

    root = get_project_root()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("=" * 50)
    print(f"  SMOKE TEST - {timestamp}")
    print("=" * 50)

    if quick_mode:
        print(f"{YELLOW}Quick mode: skipping frontend build{RESET}")

    results = []

    # 1. Database connects
    passed, msg = check_database_connects(root)
    results.append(("Database", passed, msg))

    # 2. API check
    passed, msg = check_api_proposals(root)
    results.append(("API", passed, msg))

    # 3. Frontend build (unless --quick)
    if quick_mode:
        results.append(("Frontend", True, "Skipped (--quick)"))
        print(f"\n{BLUE}3. Frontend Build{RESET}")
        print("-" * 40)
        print_status(True, "Skipped in quick mode", warning=True)
    else:
        passed, msg = check_frontend_build(root)
        results.append(("Frontend", passed, msg))

    # 4. FK integrity
    passed, msg = check_orphaned_fk(root)
    results.append(("FK Integrity", passed, msg))

    # Summary
    print("\n" + "=" * 50)
    print("  SUMMARY")
    print("=" * 50)

    all_passed = all(r[1] for r in results)

    for name, passed, msg in results:
        status = f"{GREEN}{CHECK}{RESET}" if passed else f"{RED}{CROSS}{RESET}"
        print(f"  {status} {name}: {msg}")

    print("-" * 50)

    if all_passed:
        print(f"{GREEN}ALL CHECKS PASSED{RESET}")
        print("Safe to proceed with session.")
    else:
        failed = [r[0] for r in results if not r[1]]
        print(f"{RED}FAILED: {', '.join(failed)}{RESET}")
        print("Fix issues before proceeding.")

    print("=" * 50)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
