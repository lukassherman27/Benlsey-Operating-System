#!/usr/bin/env python3
"""
Continuous Email Processor
Runs smart_email_brain.py in a loop until all emails are processed
"""
import subprocess
import sqlite3
import os
import time
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BRAIN_SCRIPT = os.path.join(SCRIPT_DIR, 'smart_email_brain.py')
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

def get_remaining_count():
    """Count emails not yet processed"""
    conn = sqlite3.connect(os.path.join(PROJECT_ROOT, DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM emails
        WHERE email_id NOT IN (SELECT email_id FROM email_content)
        AND body_full IS NOT NULL
        AND LENGTH(body_full) > 10
    """)
    remaining = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM email_content")
    processed = cursor.fetchone()[0]

    conn.close()
    return remaining, processed

def run_batch(batch_size=100):
    """Run one batch of processing"""
    os.chdir(PROJECT_ROOT)
    result = subprocess.run(
        ['python3', BRAIN_SCRIPT, '--batch-size', str(batch_size), '--yes'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def main():
    print("=" * 60)
    print("CONTINUOUS EMAIL PROCESSOR")
    print("=" * 60)

    batch_size = 100
    pause_between_batches = 2  # seconds

    while True:
        remaining, processed = get_remaining_count()

        if remaining == 0:
            print(f"\n All {processed} emails processed!")
            break

        print(f"\n[{processed} processed / {remaining} remaining]")
        print(f"Running batch of {batch_size}...")

        success = run_batch(batch_size)

        if not success:
            print("Batch failed, waiting 10s before retry...")
            time.sleep(10)
        else:
            # Check progress
            new_remaining, new_processed = get_remaining_count()
            batch_processed = new_processed - processed
            print(f"Batch complete: +{batch_processed} emails")

            if batch_processed == 0:
                print("No progress made - possible issue. Waiting 30s...")
                time.sleep(30)
            else:
                time.sleep(pause_between_batches)

if __name__ == "__main__":
    main()
