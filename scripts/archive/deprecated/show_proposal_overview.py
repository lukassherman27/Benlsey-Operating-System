#!/usr/bin/env python3
"""
Show overview of all proposals by status
"""
import sqlite3
import sys
from pathlib import Path

def show_overview(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print('='*80)
    print('📋 PROPOSAL STATUS OVERVIEW')
    print('='*80)

    # Lost proposals
    print('\n🔴 LOST/CANCELLED PROPOSALS:')
    print('='*80)
    cursor.execute('''
        SELECT project_code, project_name, status
        FROM proposals
        WHERE status = 'lost'
        ORDER BY project_code
    ''')
    lost = cursor.fetchall()
    for i, p in enumerate(lost[:10], 1):
        print(f"{i}. {p['project_code']}: {p['project_name'][:60]}")
    if len(lost) > 10:
        print(f'... and {len(lost) - 10} more')
    print(f'\nTotal Lost: {len(lost)}')

    # Healthy (with email data)
    print('\n\n🟢 HEALTHY PROPOSALS (WITH EMAIL ACTIVITY):')
    print('='*80)
    cursor.execute('''
        SELECT project_code, project_name, days_since_contact, health_score
        FROM proposals
        WHERE is_active_project = 0
          AND (status IS NULL OR status != 'lost')
          AND days_since_contact IS NOT NULL
        ORDER BY days_since_contact
    ''')
    healthy = cursor.fetchall()
    for p in healthy:
        days = p['days_since_contact']
        score = p['health_score'] or 50
        print(f"{p['project_code']}: {p['project_name'][:50]:50} | {days:3} days | {score:3.0f}%")
    print(f'\nTotal Healthy: {len(healthy)}')

    # Needs review (no email data)
    print('\n\n❓ NEEDS REVIEW - NO EMAIL DATA:')
    print('='*80)
    cursor.execute('''
        SELECT project_code, project_name, status
        FROM proposals
        WHERE is_active_project = 0
          AND (status IS NULL OR status != 'lost')
          AND days_since_contact IS NULL
        ORDER BY project_code
    ''')
    needs_review = cursor.fetchall()
    for i, p in enumerate(needs_review, 1):
        status = p['status'] or 'proposal'
        print(f"{i:2}. {p['project_code']}: {p['project_name'][:55]:55} [{status}]")
    print(f'\nTotal Needs Review: {len(needs_review)}')

    # Active project
    print('\n\n✅ ACTIVE PROJECTS (SIGNED CONTRACTS):')
    print('='*80)
    cursor.execute('''
        SELECT project_code, project_name, status
        FROM proposals
        WHERE is_active_project = 1
        ORDER BY project_code
    ''')
    active = cursor.fetchall()
    for p in active:
        print(f"{p['project_code']}: {p['project_name']}")
    print(f'\nTotal Active: {len(active)}')

    print('\n' + '='*80)
    print('📊 TOTAL SUMMARY')
    print('='*80)
    print(f'  🔴 Lost/Cancelled:   {len(lost)}')
    print(f'  🟢 Healthy:          {len(healthy)}')
    print(f'  ❓ Needs Review:     {len(needs_review)}')
    print(f'  ✅ Active Projects:  {len(active)}')
    print(f'  📊 Total:            {len(lost) + len(healthy) + len(needs_review) + len(active)}')
    print('='*80 + '\n')

    conn.close()

def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else "database/bensley_master.db"

    if not Path(db_path).exists():
        print(f"✗ Database not found: {db_path}")
        return

    show_overview(db_path)

if __name__ == "__main__":
    main()
