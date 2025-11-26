#!/usr/bin/env python3
"""
Fix Schema Mismatch - Replace project_name with project_title

The database migration changed project_name → project_title
but backend code wasn't updated. This fixes ALL occurrences.
"""
import os
import re
from pathlib import Path

# Files to fix (from grep results)
FILES_TO_FIX = [
    "backend/services/financial_service.py",
    "backend/services/admin_service.py",
    "backend/api/main.py",
    "backend/services/proposal_service.py",
    "backend/services/proposal_tracker_service.py",
    "backend/services/contract_service.py",
    "backend/services/milestone_service.py",
    "backend/services/meeting_service.py",
    "backend/services/rfi_service.py",
    "backend/services/proposal_query_service.py",
    "backend/services/intelligence_service.py",
    "backend/services/comprehensive_auditor.py",
    "backend/services/schedule_pdf_generator.py",
    "backend/services/schedule_pdf_parser.py",
    "backend/services/schedule_email_parser.py",
    "backend/services/outreach_service.py",
    "backend/services/context_service.py",
    "backend/routes/contracts.py",
    "backend/services/email_content_processor.py",
    "backend/services/document_service.py",
    "backend/services/test_services.py",
    "backend/services/email_content_processor_smart.py",
    "backend/services/email_content_processor_claude.py",
    "backend/services/project_creator.py",
    "backend/services/excel_importer.py",
    "backend/core/sync_master.py",
    "backend/core/import_excel_timeline.py",
]

def fix_file(file_path):
    """Replace project_name with project_title in file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        original = content

        # Replace project_name with project_title
        # But be careful not to replace in comments about the old name
        content = content.replace('project_name', 'project_title')

        if content != original:
            with open(file_path, 'w') as f:
                f.write(content)

            changes = content.count('project_title') - original.count('project_title')
            print(f"✅ {file_path}: {changes} replacements")
            return True
        else:
            print(f"⚠️  {file_path}: No changes needed")
            return False

    except FileNotFoundError:
        print(f"❌ {file_path}: File not found")
        return False
    except Exception as e:
        print(f"❌ {file_path}: Error - {e}")
        return False

def main():
    print("="*80)
    print("FIXING SCHEMA MISMATCH: project_name → project_title")
    print("="*80)

    fixed = 0
    skipped = 0
    errors = 0

    for file_path in FILES_TO_FIX:
        result = fix_file(file_path)
        if result:
            fixed += 1
        elif result is False:
            skipped += 1
        else:
            errors += 1

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Fixed: {fixed} files")
    print(f"⚠️  Skipped: {skipped} files")
    print(f"❌ Errors: {errors} files")
    print("="*80)

    print("\n🔄 Restart backend API for changes to take effect:")
    print("   pkill -f 'uvicorn backend.api.main'")
    print("   python3 -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000")

if __name__ == '__main__':
    main()
