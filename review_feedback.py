#!/usr/bin/env python3
"""
Review System Feedback and Implement Improvements
Reviews category suggestions and other feedback from training sessions
"""

import sqlite3
import sys
import json
from datetime import datetime

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

def get_pending_feedback():
    """Get all pending feedback from training sessions"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT feedback_id, feedback_type, suggestion, reasoning,
               example_email_id, created_at
        FROM system_feedback
        WHERE status = 'pending'
        ORDER BY created_at DESC
    """)

    feedback = cursor.fetchall()
    conn.close()
    return feedback

def mark_feedback_reviewed(feedback_id, status, implemented=False):
    """Mark feedback as reviewed"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE system_feedback
        SET status = ?,
            reviewed_at = ?,
            implemented = ?
        WHERE feedback_id = ?
    """, (status, datetime.now().isoformat(), implemented, feedback_id))

    conn.commit()
    conn.close()

def show_example_email(email_id):
    """Show the example email for context"""
    if not email_id:
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT subject, sender_email, body_preview
        FROM emails
        WHERE email_id = ?
    """, (email_id,))

    result = cursor.fetchone()
    conn.close()

    if result:
        print("\n    EXAMPLE EMAIL:")
        print(f"    Subject: {result[0]}")
        print(f"    From: {result[1]}")
        if result[2]:
            print(f"    Preview: {result[2][:200]}...")

def review_new_category(feedback_id, suggestion_json, reasoning, email_id):
    """Review suggestion for new category"""
    try:
        data = json.loads(suggestion_json)
    except:
        print("Error: Invalid suggestion data")
        return

    category = data.get('category')
    subcategories = data.get('subcategories', [])

    print(f"\n  📝 NEW CATEGORY: '{category}'")
    if subcategories:
        print(f"  Subcategories: {', '.join(subcategories)}")
    print(f"\n  Reasoning: {reasoning}")

    show_example_email(email_id)

    print("\n  This suggestion would:")
    print(f"    1. Add '{category}' to CATEGORIES in ai_training_mode.py")
    if subcategories:
        print(f"    2. Add subcategories to SUBCATEGORIES dict")
    print(f"    3. Update export_training_data.py category list")
    print(f"    4. Include in future training exports")

    print("\n  DECISION:")
    print("    [a] Approve - Add to system")
    print("    [m] Modify - Edit before adding")
    print("    [r] Reject - Not needed")
    print("    [s] Skip - Review later")

    choice = input("\n  Decision: ").strip().lower()

    if choice == 'a':
        mark_feedback_reviewed(feedback_id, 'approved', True)
        print(f"  ✓ Approved: '{category}' will be added")
        print(f"\n  TODO: Update these files manually:")
        print(f"    • ai_training_mode.py (line ~15: CATEGORIES dict)")
        print(f"    • ai_training_mode.py (line ~30: SUBCATEGORIES dict)")
        print(f"    • export_training_data.py (categorization logic)")
        return True

    elif choice == 'm':
        print("\n  Enter modified category name:")
        new_name = input("  > ").strip()
        if new_name:
            data['category'] = new_name
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE system_feedback
                SET suggestion = ?,
                    status = 'approved',
                    implemented = 1,
                    reviewed_at = ?
                WHERE feedback_id = ?
            """, (json.dumps(data), datetime.now().isoformat(), feedback_id))
            conn.commit()
            conn.close()
            print(f"  ✓ Modified and approved: '{new_name}'")
            return True

    elif choice == 'r':
        print("\n  Reason for rejection:")
        reason = input("  > ")
        mark_feedback_reviewed(feedback_id, f'rejected: {reason}', False)
        print("  ✗ Rejected")

    elif choice == 's':
        print("  ⏸ Skipped - will review later")

    return False

def review_general_feedback(feedback_id, suggestion, created_at):
    """Review general system feedback"""
    print(f"\n  💬 GENERAL FEEDBACK")
    print(f"  Date: {created_at}")
    print(f"\n  {suggestion}")

    print("\n  DECISION:")
    print("    [a] Acknowledge - Mark as reviewed")
    print("    [i] Important - Flag for action")
    print("    [s] Skip")

    choice = input("\n  Decision: ").strip().lower()

    if choice == 'a':
        mark_feedback_reviewed(feedback_id, 'acknowledged', False)
        print("  ✓ Acknowledged")

    elif choice == 'i':
        mark_feedback_reviewed(feedback_id, 'important', False)
        print("  ⭐ Flagged as important")

def main():
    print("="*80)
    print("BENSLEY INTELLIGENCE - FEEDBACK REVIEW")
    print("="*80)
    print("\nReviewing suggestions and feedback from training sessions\n")

    feedback_items = get_pending_feedback()

    if not feedback_items:
        print("✓ No pending feedback to review!")
        print("\nAll suggestions have been processed.")
        return

    print(f"Found {len(feedback_items)} items to review\n")

    categories_approved = 0
    for feedback_id, feedback_type, suggestion, reasoning, email_id, created_at in feedback_items:

        print("="*80)
        print(f"FEEDBACK #{feedback_id} - {feedback_type.upper()}")
        print(f"Created: {created_at}")
        print("="*80)

        if feedback_type == 'new_category':
            approved = review_new_category(feedback_id, suggestion, reasoning, email_id)
            if approved:
                categories_approved += 1

        elif feedback_type == 'general_feedback':
            review_general_feedback(feedback_id, suggestion, created_at)

        print()

    print("="*80)
    print("REVIEW COMPLETE")
    print("="*80)

    if categories_approved > 0:
        print(f"\n✓ {categories_approved} new categories approved")
        print("\nNEXT STEPS:")
        print("  1. Update ai_training_mode.py:")
        print("     Add approved categories to CATEGORIES dict")
        print("     Add subcategories to SUBCATEGORIES dict")
        print("\n  2. Update export_training_data.py:")
        print("     Add new categories to categorization logic")
        print("\n  3. Re-export training data:")
        print("     python3 export_training_data.py")
        print("\n  4. Test new categories:")
        print("     python3 ai_training_mode.py")

    print("\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nReview stopped.")
        sys.exit(0)
