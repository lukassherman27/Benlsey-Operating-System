#!/usr/bin/env python3
"""
build_intelligence.py

Runs the complete intelligence pipeline:
1. Extract contacts from emails (NOT clients - you do that in Excel)
2. Learn patterns: which contacts email about which projects  
3. Process and auto-link emails based on patterns

This is the "one-click" setup for contact→project intelligence
"""

import os
import subprocess
import sys

def run_script(script_name, description):
    """Run a Python script and show progress"""
    print("\n" + "="*70)
    print(description)
    print("="*70)
    
    scripts_dir = os.path.expanduser('~/Desktop/BDS_SYSTEM/02_SCRIPTS')
    script_path = os.path.join(scripts_dir, script_name)
    
    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return False
    
    result = subprocess.run(['python3', script_path], capture_output=True, text=True)
    
    print(result.stdout)
    
    if result.returncode != 0:
        print(f"❌ Error:")
        print(result.stderr)
        return False
    
    return True

def main():
    print("="*70)
    print("BUILDING INTELLIGENT EMAIL SYSTEM")
    print("="*70)
    print()
    print("This will:")
    print("  1. Extract contacts from your 688 client emails")
    print("  2. Learn which contacts email about which projects")
    print("  3. Auto-link future emails based on learned patterns")
    print()
    print("Note: Client assignment is done separately (Excel).")
    print("      This focuses on contact → project patterns.")
    print()
    
    response = input("Ready to build? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    # Step 1: Extract contacts (not clients)
    if not run_script(
        'extract_contacts_from_emails.py',
        'STEP 1: Extracting contacts from emails'
    ):
        print("\n⚠️  Contact extraction had issues, but continuing...")
    
    # Step 2: Learn patterns
    if not run_script(
        'pattern_learner.py',
        'STEP 2: Learning contact→project patterns'
    ):
        print("\n❌ Pattern learning failed. Cannot continue.")
        return
    
    # Step 3: Process emails
    if not run_script(
        'email_processor.py',
        'STEP 3: Auto-linking emails to projects'
    ):
        print("\n❌ Email processing failed.")
        return
    
    # Final summary
    print("\n" + "="*70)
    print("🎉 INTELLIGENCE SYSTEM BUILT!")
    print("="*70)
    print()
    print("Your system now:")
    print("  ✅ Knows which contacts send emails")
    print("  ✅ Learned contact → project patterns")
    print("  ✅ Can auto-link emails to projects")
    print("  ✅ Auto-tags emails by category")
    print()
    print("Next steps:")
    print("  1. Review linked emails: python3 query_linked_emails.py")
    print("  2. Manage clients separately in Excel")
    print("  3. Use quick_edit.py to link projects to clients manually")
    print()

if __name__ == '__main__':
    main()
