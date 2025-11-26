#!/usr/bin/env python3
"""
Re-tag ALL emails with new category patterns.

This script adds 6 new critical categories needed for the intelligence layer:
- contract-changes
- fee-adjustments
- scope-changes
- payment-terms
- rfis
- meeting-notes

Existing tags are preserved; only new tags are added.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from core.email_processor import EmailProcessor

def main():
    print("=" * 80)
    print("RE-TAG EMAILS WITH NEW CATEGORIES")
    print("=" * 80)
    print("\nAdding 6 new critical categories for Intelligence Layer:")
    print("  1. contract-changes - Detect contract modifications")
    print("  2. fee-adjustments - Track pricing/budget changes")
    print("  3. scope-changes - Monitor scope additions/removals")
    print("  4. payment-terms - Payment schedule discussions")
    print("  5. rfis - Requests for information")
    print("  6. meeting-notes - Decisions from meetings")
    print("\n" + "=" * 80)

    # Create processor
    processor = EmailProcessor()

    # Re-tag all emails
    processor.retag_all_emails_with_new_categories()

    # Show summary
    processor.show_processing_summary()

    print("\n✅ Re-tagging complete!")
    print("\n" + "=" * 80)

    processor.conn.close()

if __name__ == '__main__':
    main()
