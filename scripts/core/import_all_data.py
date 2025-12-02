#!/usr/bin/env python3
"""
MASTER IMPORT SCRIPT
Runs all 3 import steps in sequence:
1. Import proposal overview (87 proposals for analytics)
2. Import fee breakdown & invoices from Excel
3. Import signed contract PDFs using Claude API

Run this to import everything at once.
"""

import subprocess
import sys
from pathlib import Path

WORKING_DIR = Path("/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System")

STEPS = [
    {
        "number": 1,
        "name": "Import Proposals",
        "script": "import_step1_proposals.py",
        "description": "Import 87 proposals from Excel for analytics"
    },
    {
        "number": 2,
        "name": "Import Fee Breakdown & Invoices",
        "script": "import_step2_fee_breakdown.py",
        "description": "Import 345 fee/invoice records from Excel"
    },
    {
        "number": 3,
        "name": "Import Contract PDFs",
        "script": "import_step3_contracts.py",
        "description": "Extract & import 8 signed contracts using OpenAI API"
    }
]


def run_step(step):
    """Run a single import step"""
    print("\n" + "="*80)
    print(f"STEP {step['number']}: {step['name']}")
    print("="*80)
    print(f"{step['description']}")
    print(f"\nRunning: {step['script']}")

    script_path = WORKING_DIR / step['script']

    if not script_path.exists():
        print(f"\n❌ ERROR: Script not found: {script_path}")
        return False

    # Run the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(WORKING_DIR),
        capture_output=False
    )

    if result.returncode != 0:
        print(f"\n❌ Step {step['number']} failed with error code: {result.returncode}")
        return False

    print(f"\n✅ Step {step['number']} completed successfully")
    return True


def main():
    print("\n" + "="*80)
    print("MASTER DATA IMPORT")
    print("="*80)
    print("\nThis will run all 3 import steps in sequence:")
    for step in STEPS:
        print(f"\n  STEP {step['number']}: {step['name']}")
        print(f"    → {step['description']}")

    print("\n" + "="*80)
    print("IMPORTANT:")
    print("  • Proposals stay in proposals table for analytics")
    print("  • Signed proposals become active projects")
    print("  • Step 3 uses OpenAI API (~$1-2 cost with GPT-4)")
    print("="*80)

    response = input("\nRun all 3 steps? (y/n): ")
    if response.lower() != 'y':
        print("\nAborted.")
        print("\nYou can run steps individually:")
        for step in STEPS:
            print(f"  python3 {step['script']}")
        return

    # Run each step
    for step in STEPS:
        success = run_step(step)
        if not success:
            print(f"\n❌ Import failed at Step {step['number']}")
            print("Fix the error and run remaining steps manually:")
            for remaining_step in STEPS:
                if remaining_step['number'] > step['number']:
                    print(f"  python3 {remaining_step['script']}")
            sys.exit(1)

        # Ask before continuing to next step
        if step['number'] < len(STEPS):
            response = input(f"\nContinue to Step {step['number'] + 1}? (y/n): ")
            if response.lower() != 'y':
                print("\nStopped. Run remaining steps manually:")
                for remaining_step in STEPS:
                    if remaining_step['number'] > step['number']:
                        print(f"  python3 {remaining_step['script']}")
                return

    # All steps complete
    print("\n" + "="*80)
    print("ALL IMPORTS COMPLETE!")
    print("="*80)
    print("\n✅ Successfully imported:")
    print("   • 87 proposals for analytics")
    print("   • 345 fee breakdown & invoice records")
    print("   • 8 signed contracts ($13.025M total value)")
    print("\n📊 Analytics Available:")
    print("   • Conversion rate: 8/87 = 9.2% win rate")
    print("   • Total proposal value vs signed value")
    print("   • Pipeline by discipline, country, status")
    print("\n🎯 Next Steps:")
    print("   • Check frontend dashboard for data")
    print("   • Verify invoice displays (Claude 2 fixes)")
    print("   • Run analytics queries on proposals table")


if __name__ == "__main__":
    main()
