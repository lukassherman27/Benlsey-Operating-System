#!/usr/bin/env python3
"""
email_monitor_daemon.py

Continuous background monitoring of emails
Auto-syncs, processes, and learns every 15 minutes
"""

import subprocess
import time
import os
from datetime import datetime
from pathlib import Path

# Paths
BDS_DIR = Path.home() / "Desktop" / "BDS_SYSTEM"
SCRIPTS_DIR = BDS_DIR / "02_SCRIPTS" / "ACTIVE"
LOG_FILE = BDS_DIR / "monitor.log"

CHECK_INTERVAL = 900  # 15 minutes in seconds

def log(message):
    """Log message to file and console"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    
    print(log_message)
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_message + "\n")

def run_script(script_name):
    """Run a script and return success status"""
    script_path = SCRIPTS_DIR / script_name
    
    try:
        result = subprocess.run(
            ['python3', str(script_path)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        return result.returncode == 0, result.stdout
    except subprocess.TimeoutExpired:
        log(f"   ⚠️  {script_name} timed out")
        return False, ""
    except Exception as e:
        log(f"   ❌ {script_name} error: {e}")
        return False, ""

def sync_and_process():
    """Run the complete sync and process pipeline"""
    log("🔄 Starting sync cycle...")
    
    # Step 1: Sync from Tmail
    log("   📧 Syncing from Tmail...")
    success, output = run_script('sync_tmail.py')
    
    if success:
        # Extract new email count from output
        if 'Added' in output:
            for line in output.split('\n'):
                if 'Added' in line and 'new emails' in line:
                    log(f"   {line.strip()}")
        else:
            log("   ✅ No new emails")
    else:
        log("   ⚠️  Tmail sync had issues")
        return False
    
    # Step 2: Sync to master database
    log("   💾 Syncing to master database...")
    success, output = run_script('sync_master.py')
    
    if not success:
        log("   ⚠️  Master sync had issues")
        return False
    
    # Step 3: Process emails through intelligence
    log("   🧠 Processing through intelligence...")
    success, output = run_script('email_processor.py')
    
    if success:
        # Extract processing stats
        if 'Processed' in output:
            for line in output.split('\n'):
                if 'Processed' in line or 'Added' in line or 'Created' in line:
                    log(f"   {line.strip()}")
    else:
        log("   ⚠️  Processing had issues")
        return False
    
    log("✅ Sync cycle complete")
    return True

def main():
    """Main daemon loop"""
    log("="*70)
    log("EMAIL MONITORING DAEMON STARTED")
    log("="*70)
    log(f"Check interval: {CHECK_INTERVAL // 60} minutes")
    log(f"Log file: {LOG_FILE}")
    log(f"Press Ctrl+C to stop")
    log("="*70)
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            log(f"\n{'='*70}")
            log(f"CYCLE {cycle_count}")
            log(f"{'='*70}")
            
            # Run sync and process
            sync_and_process()
            
            # Wait for next cycle
            log(f"\n💤 Sleeping for {CHECK_INTERVAL // 60} minutes...")
            log(f"Next check at: {datetime.fromtimestamp(time.time() + CHECK_INTERVAL).strftime('%H:%M:%S')}")
            
            time.sleep(CHECK_INTERVAL)
    
    except KeyboardInterrupt:
        log("\n" + "="*70)
        log("DAEMON STOPPED BY USER")
        log("="*70)
        log(f"Total cycles completed: {cycle_count}")
    
    except Exception as e:
        log(f"\n❌ FATAL ERROR: {e}")
        import traceback
        log(traceback.format_exc())

if __name__ == '__main__':
    main()
