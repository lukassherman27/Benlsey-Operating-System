#!/usr/bin/env python3
"""
Comprehensive Database Audit and Migration Plan
Compare Desktop vs OneDrive databases and create migration strategy
"""

import sqlite3
import os
from datetime import datetime

DESKTOP_DB = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
ONEDRIVE_DB = "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/bensley_master.db"

def get_db_stats(db_path, name):
    """Get comprehensive stats from a database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    stats = {
        'name': name,
        'path': db_path,
        'size_mb': os.path.getsize(db_path) / (1024 * 1024),
        'modified': datetime.fromtimestamp(os.path.getmtime(db_path)).strftime('%Y-%m-%d %H:%M:%S')
    }

    # Get table counts
    tables = ['emails', 'projects', 'proposals', 'invoices', 'clients', 'contract_phases']
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        except:
            stats[table] = 0

    # Get sample recent emails
    try:
        cursor.execute("SELECT MAX(date_normalized) FROM emails WHERE date_normalized IS NOT NULL")
        stats['latest_email'] = cursor.fetchone()[0] or 'N/A'
    except:
        try:
            cursor.execute("SELECT MAX(date) FROM emails")
            stats['latest_email'] = cursor.fetchone()[0] or 'N/A'
        except:
            stats['latest_email'] = 'N/A'

    # Get sample recent invoices
    try:
        cursor.execute("SELECT MAX(invoice_number) FROM invoices")
        stats['latest_invoice'] = cursor.fetchone()[0] or 'N/A'
    except:
        stats['latest_invoice'] = 'N/A'

    # Check if date_normalized column exists
    try:
        cursor.execute("SELECT date_normalized FROM emails LIMIT 1")
        stats['has_date_normalized'] = True
    except:
        stats['has_date_normalized'] = False

    conn.close()
    return stats

def compare_data_quality(desktop_stats, onedrive_stats):
    """Determine which database has better data quality"""

    score_desktop = 0
    score_onedrive = 0
    reasons = []

    # More recent modification
    if desktop_stats['modified'] > onedrive_stats['modified']:
        score_desktop += 1
        reasons.append(f"✅ Desktop: More recent ({desktop_stats['modified']})")
    else:
        score_onedrive += 1
        reasons.append(f"✅ OneDrive: More recent ({onedrive_stats['modified']})")

    # More emails
    if desktop_stats['emails'] > onedrive_stats['emails']:
        score_desktop += 1
        reasons.append(f"✅ Desktop: More emails ({desktop_stats['emails']} vs {onedrive_stats['emails']})")
    else:
        score_onedrive += 1
        reasons.append(f"✅ OneDrive: More emails ({onedrive_stats['emails']} vs {desktop_stats['emails']})")

    # More projects
    if desktop_stats['projects'] > onedrive_stats['projects']:
        score_desktop += 2  # Projects are important
        reasons.append(f"✅ Desktop: More projects ({desktop_stats['projects']} vs {onedrive_stats['projects']})")
    else:
        score_onedrive += 2
        reasons.append(f"✅ OneDrive: More projects ({onedrive_stats['projects']} vs {desktop_stats['projects']})")

    # More invoices
    if desktop_stats['invoices'] > onedrive_stats['invoices']:
        score_desktop += 3  # Invoices are critical
        reasons.append(f"✅ Desktop: More invoices ({desktop_stats['invoices']} vs {onedrive_stats['invoices']})")
    else:
        score_onedrive += 3
        reasons.append(f"✅ OneDrive: More invoices ({onedrive_stats['invoices']} vs {desktop_stats['invoices']})")

    # Has date_normalized (newer schema)
    if desktop_stats['has_date_normalized'] and not onedrive_stats['has_date_normalized']:
        score_desktop += 1
        reasons.append(f"✅ Desktop: Has date_normalized column (newer schema)")
    elif onedrive_stats['has_date_normalized'] and not desktop_stats['has_date_normalized']:
        score_onedrive += 1
        reasons.append(f"✅ OneDrive: Has date_normalized column (newer schema)")

    return score_desktop, score_onedrive, reasons

def main():
    print("="*120)
    print("DATABASE AUDIT & MIGRATION ANALYSIS")
    print("="*120)

    print("\n[1/4] Getting Desktop database stats...")
    desktop_stats = get_db_stats(DESKTOP_DB, "Desktop")

    print("[2/4] Getting OneDrive database stats...")
    onedrive_stats = get_db_stats(ONEDRIVE_DB, "OneDrive")

    print("\n[3/4] Comparison:")
    print("\n" + "="*120)
    print(f"{'Metric':<30} {'Desktop':<40} {'OneDrive':<40}")
    print("="*120)

    print(f"{'File Size':<30} {desktop_stats['size_mb']:>10.2f} MB {'':<29} {onedrive_stats['size_mb']:>10.2f} MB")
    print(f"{'Last Modified':<30} {desktop_stats['modified']:<40} {onedrive_stats['modified']:<40}")
    print(f"{'Latest Email':<30} {str(desktop_stats['latest_email']):<40} {str(onedrive_stats['latest_email']):<40}")
    print(f"{'Latest Invoice':<30} {str(desktop_stats['latest_invoice']):<40} {str(onedrive_stats['latest_invoice']):<40}")
    print(f"{'Has date_normalized':<30} {str(desktop_stats['has_date_normalized']):<40} {str(onedrive_stats['has_date_normalized']):<40}")
    print("-"*120)
    print(f"{'Emails':<30} {desktop_stats['emails']:>10} {'':<29} {onedrive_stats['emails']:>10}")
    print(f"{'Projects':<30} {desktop_stats['projects']:>10} {'':<29} {onedrive_stats['projects']:>10}")
    print(f"{'Proposals':<30} {desktop_stats['proposals']:>10} {'':<29} {onedrive_stats['proposals']:>10}")
    print(f"{'Invoices':<30} {desktop_stats['invoices']:>10} {'':<29} {onedrive_stats['invoices']:>10}")
    print(f"{'Clients':<30} {desktop_stats['clients']:>10} {'':<29} {onedrive_stats['clients']:>10}")
    print(f"{'Contract Phases':<30} {desktop_stats['contract_phases']:>10} {'':<29} {onedrive_stats['contract_phases']:>10}")
    print("="*120)

    print("\n[4/4] Data Quality Analysis:")
    score_desktop, score_onedrive, reasons = compare_data_quality(desktop_stats, onedrive_stats)

    print("\n" + "="*120)
    print("QUALITY SCORE")
    print("="*120)
    print(f"Desktop Score: {score_desktop}")
    print(f"OneDrive Score: {score_onedrive}")
    print("\nReasons:")
    for reason in reasons:
        print(f"  {reason}")

    print("\n" + "="*120)
    print("RECOMMENDATION")
    print("="*120)

    if score_desktop > score_onedrive:
        print("🎯 RECOMMENDATION: Use DESKTOP database as master")
        print("\nWhy:")
        print(f"  • Desktop has {desktop_stats['invoices']} invoices vs OneDrive's {onedrive_stats['invoices']}")
        print(f"  • Desktop has {desktop_stats['projects']} projects vs OneDrive's {onedrive_stats['projects']}")
        print("\nMigration Plan:")
        print("  1. Backup current OneDrive database")
        print("  2. Copy Desktop database to OneDrive location")
        print("  3. Migrate the EMAILS from OneDrive → Desktop (OneDrive has more)")
        print("  4. Update .env to point to correct location")
        print("  5. Verify all data")
    else:
        print("🎯 RECOMMENDATION: Use ONEDRIVE database as master")
        print("\nWhy:")
        print(f"  • OneDrive has {onedrive_stats['emails']} emails vs Desktop's {desktop_stats['emails']}")
        print(f"  • OneDrive was modified more recently ({onedrive_stats['modified']})")
        if onedrive_stats['has_date_normalized']:
            print(f"  • OneDrive has newer schema (date_normalized column)")
        print("\nMigration Plan:")
        print("  1. Backup current Desktop database")
        print("  2. Migrate INVOICES from Desktop → OneDrive (Desktop has more)")
        print("  3. Migrate PROJECTS from Desktop → OneDrive (Desktop has more)")
        print("  4. Update .env to confirm OneDrive location")
        print("  5. Delete/archive Desktop database")
        print("  6. Verify all data")

    print("\n" + "="*120)
    print("NEXT STEPS")
    print("="*120)
    print("1. Review this analysis")
    print("2. Decide which database to use as master")
    print("3. I'll create a migration script to merge the data")
    print("="*120)

if __name__ == '__main__':
    main()
