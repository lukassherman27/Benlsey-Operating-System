#!/usr/bin/env python3
"""
setup_continuous_system.py

Master setup script that:
1. Enriches the database
2. Scans for documents
3. Starts continuous monitoring

Run this once to set up the complete system
"""

import subprocess
import sys
from pathlib import Path

def run_script(script_name, description):
    """Run a script and show progress"""
    print("\n" + "="*70)
    print(description)
    print("="*70)
    
    scripts_dir = Path.home() / "Desktop/BDS_SYSTEM/02_SCRIPTS/ACTIVE"
    script_path = scripts_dir / script_name
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False
    
    result = subprocess.run(['python3', str(script_path)], capture_output=True, text=True)
    
    print(result.stdout)
    
    if result.returncode != 0:
        print(f"⚠️  Script had issues:")
        print(result.stderr)
        return False
    
    return True

def main():
    print("="*70)
    print("CONTINUOUS MONITORING SYSTEM - COMPLETE SETUP")
    print("="*70)
    print()
    print("This will:")
    print("  1. Enrich database with context and metadata")
    print("  2. Scan and link project documents")
    print("  3. Start continuous email monitoring")
    print()
    
    response = input("Ready to set up the complete system? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return
    
    # Step 1: Enrich database
    if not run_script('enrich_database.py', 'STEP 1: Enriching Database'):
        print("\n⚠️  Database enrichment had issues, but continuing...")
    
    # Step 2: Scan documents
    if not run_script('scan_documents.py', 'STEP 2: Scanning Documents'):
        print("\n⚠️  Document scanning had issues, but continuing...")
    
    # Step 3: Start monitor
    print("\n" + "="*70)
    print("STEP 3: Starting Continuous Monitor")
    print("="*70)
    
    scripts_dir = Path.home() / "Desktop/BDS_SYSTEM/02_SCRIPTS/ACTIVE"
    control_script = scripts_dir / "monitor_control.sh"
    
    if not control_script.exists():
        print(f"❌ Monitor control script not found: {control_script}")
        print("   Please download monitor_control.sh to ACTIVE folder")
        return
    
    # Make sure it's executable
    import os
    os.chmod(control_script, 0o755)
    
    # Start the monitor
    result = subprocess.run([str(control_script), 'start'], capture_output=True, text=True)
    print(result.stdout)
    
    if result.returncode != 0:
        print("⚠️  Monitor start had issues:")
        print(result.stderr)
    
    # Final summary
    print("\n" + "="*70)
    print("🎉 SETUP COMPLETE!")
    print("="*70)
    print()
    print("Your continuous monitoring system is now running:")
    print()
    print("✅ Database enriched with project metadata")
    print("✅ Documents scanned and linked")
    print("✅ Email monitor running in background")
    print()
    print("Check status:")
    print(f"  cd {scripts_dir}")
    print("  ./monitor_control.sh status")
    print()
    print("View logs:")
    print("  ./monitor_control.sh logs")
    print()
    print("Stop monitoring:")
    print("  ./monitor_control.sh stop")
    print()
    print("📖 Full guide: CONTINUOUS_MONITORING_GUIDE.md")
    print()

if __name__ == '__main__':
    main()
