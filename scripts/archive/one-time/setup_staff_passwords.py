#!/usr/bin/env python3
"""
Set Initial Passwords for Staff Members

This script sets passwords for staff members who don't have one yet.
Useful for initial setup or after adding new staff.

Usage:
    python scripts/setup_staff_passwords.py

The script will:
1. Show all staff without passwords
2. Set a default password for each (bensley123)
3. Print login credentials

After running, staff should change their passwords on first login.
"""

import sqlite3
import bcrypt
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "bensley_master.db"
DEFAULT_PASSWORD = "bensley123"


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')


def main():
    print("=" * 60)
    print("Staff Password Setup")
    print("=" * 60)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get staff without passwords
    cursor.execute("""
        SELECT staff_id, email, first_name, last_name, password_hash
        FROM staff
        WHERE is_active = 1
        ORDER BY first_name
    """)

    staff = cursor.fetchall()

    without_password = [s for s in staff if not s["password_hash"]]
    with_password = [s for s in staff if s["password_hash"]]

    print(f"\nStaff with passwords: {len(with_password)}")
    for s in with_password:
        print(f"  - {s['email']} ({s['first_name']})")

    print(f"\nStaff WITHOUT passwords: {len(without_password)}")
    for s in without_password:
        print(f"  - {s['email']} ({s['first_name']})")

    if not without_password:
        print("\nAll staff members already have passwords set.")
        conn.close()
        return

    print(f"\n{'=' * 60}")
    print(f"Setting default password for {len(without_password)} staff members...")
    print(f"Default password: {DEFAULT_PASSWORD}")
    print(f"{'=' * 60}")

    confirm = input("\nProceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        conn.close()
        return

    password_hash = get_password_hash(DEFAULT_PASSWORD)

    for s in without_password:
        cursor.execute("""
            UPDATE staff
            SET password_hash = ?
            WHERE staff_id = ?
        """, (password_hash, s["staff_id"]))
        print(f"Set password for: {s['email']}")

    conn.commit()
    conn.close()

    print(f"\n{'=' * 60}")
    print("Done! Staff can now log in with:")
    print(f"Password: {DEFAULT_PASSWORD}")
    print("\nRemind them to change their password after first login.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
