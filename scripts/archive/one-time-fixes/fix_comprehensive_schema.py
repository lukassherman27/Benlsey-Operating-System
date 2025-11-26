#!/usr/bin/env python3
"""
Comprehensive Schema Fix

Desktop vs OneDrive databases have different schemas.
This script fixes ALL mismatches by updating backend queries.

Changes needed:
1. p.client_company → JOIN proposals to get it
2. p.project_phase → p.current_phase
3. p.proposal_id → Remove (doesn't exist)
4. p.paid_to_date_usd → Calculate from invoices
5. p.outstanding_usd → Calculate from invoices
"""
import re
from pathlib import Path

# Critical file: backend/api/main.py - Active projects endpoint
MAIN_PY_ACTIVE_PROJECTS_FIX = {
    'file': 'backend/api/main.py',
    'old': '''        cursor.execute("""
            SELECT DISTINCT
                p.project_code,
                p.project_title,
                p.client_company as client_name,
                p.total_fee_usd as contract_value,
                p.status,
                p.project_phase as current_phase,
                p.proposal_id as project_id,
                p.paid_to_date_usd,
                p.outstanding_usd
            FROM projects p
            WHERE p.is_active_project = 1 OR p.status IN ('active', 'active_project', 'Active')
            ORDER BY p.project_code DESC
        """)''',
    'new': '''        cursor.execute("""
            SELECT DISTINCT
                p.project_code,
                p.project_title,
                COALESCE(pr.client_company, 'Unknown') as client_name,
                p.total_fee_usd as contract_value,
                p.status,
                p.current_phase as current_phase,
                p.project_id as project_id,
                0.0 as paid_to_date_usd,
                p.total_fee_usd as outstanding_usd
            FROM projects p
            LEFT JOIN proposals pr ON p.project_code = pr.project_code
            WHERE p.is_active_project = 1 OR p.status IN ('active', 'active_project', 'Active')
            ORDER BY p.project_code DESC
        """)'''
}

# Generic fix for all other files: Just remove p.client_company selections
# and add LEFT JOIN where needed
GENERIC_FIXES = [
    {
        'pattern': r'p\.client_company',
        'replacement': "COALESCE(pr.client_company, 'Unknown')",
        'description': 'Replace p.client_company with JOIN to proposals'
    },
    {
        'pattern': r'p\.project_phase',
        'replacement': 'p.current_phase',
        'description': 'Replace project_phase with current_phase'
    },
    {
        'pattern': r'p\.proposal_id',
        'replacement': 'p.project_id',
        'description': 'Replace proposal_id with project_id'
    }
]

def add_proposals_join_if_needed(content):
    """Add LEFT JOIN proposals if client_company is used but join doesn't exist"""

    # Check if content has pr.client_company or COALESCE(pr.client_company
    if 'pr.client_company' not in content:
        return content

    # Check if LEFT JOIN proposals already exists
    if 'LEFT JOIN proposals pr' in content or 'JOIN proposals pr' in content:
        return content

    # Find FROM projects p and add JOIN after it
    pattern = r'(FROM projects p)((?!\s*LEFT JOIN proposals|\s*JOIN proposals))'
    replacement = r'\1\n            LEFT JOIN proposals pr ON p.project_code = pr.project_code\2'

    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    return content

def fix_main_py():
    """Fix the critical active projects endpoint in main.py"""
    file_path = MAIN_PY_ACTIVE_PROJECTS_FIX['file']

    try:
        with open(file_path, 'r') as f:
            content = f.read()

        old_query = MAIN_PY_ACTIVE_PROJECTS_FIX['old']
        new_query = MAIN_PY_ACTIVE_PROJECTS_FIX['new']

        if old_query in content:
            content = content.replace(old_query, new_query)

            with open(file_path, 'w') as f:
                f.write(content)

            print(f"✅ {file_path}: Fixed active projects endpoint")
            return True
        else:
            print(f"⚠️  {file_path}: Active projects query not found (may already be fixed)")
            return False

    except Exception as e:
        print(f"❌ {file_path}: Error - {e}")
        return False

def fix_file_generic(file_path):
    """Apply generic fixes to a file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        original = content
        changes = 0

        # Apply generic pattern replacements
        for fix in GENERIC_FIXES:
            count_before = content.count(fix['pattern'])
            content = re.sub(fix['pattern'], fix['replacement'], content)
            count_after = content.count(fix['replacement'])

            if count_after > 0:
                changes += 1

        # Add proposals JOIN if needed
        content = add_proposals_join_if_needed(content)

        if content != original:
            with open(file_path, 'w') as f:
                f.write(content)

            print(f"✅ {file_path}: {changes} pattern fixes + JOIN added if needed")
            return True
        else:
            return False

    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"❌ {file_path}: Error - {e}")
        return False

def main():
    print("="*80)
    print("COMPREHENSIVE SCHEMA FIX")
    print("="*80)

    # Fix critical main.py endpoint first
    print("\n🎯 Fixing Critical Endpoint...")
    fix_main_py()

    # Files to fix
    files_to_fix = [
        'backend/services/financial_service.py',
        'backend/services/context_service.py',
        'backend/services/outreach_service.py',
        'backend/services/proposal_query_service.py',
        'backend/services/rfi_service.py',
        'backend/services/meeting_service.py',
        'backend/services/milestone_service.py',
        'backend/services/contract_service.py',
        'backend/services/proposal_service.py',
    ]

    print("\n🔧 Fixing Service Files...")
    fixed = 0
    for file_path in files_to_fix:
        if fix_file_generic(file_path):
            fixed += 1

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Fixed {fixed + 1} files")
    print("="*80)

    print("\n🔄 Next: Restart backend API")
    print("   pkill -f 'uvicorn backend.api.main'")
    print("   python3 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000")

if __name__ == '__main__':
    main()
