#!/usr/bin/env python3
"""
Manual Training Feedback Tool
Allows human verification and correction of AI categorizations
Builds high-quality training data for local model
"""

import sqlite3
import sys
import json
from datetime import datetime

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

# Category options
CATEGORIES = {
    "1": "proposal",
    "2": "meeting",
    "3": "contract",
    "4": "project_update",
    "5": "schedule",
    "6": "design",
    "7": "rfi",
    "8": "invoice",
    "9": "general",
    "0": "other"
}

SUBCATEGORIES = {
    "proposal": ["initial", "follow_up", "revision", "won", "lost"],
    "meeting": ["scheduled", "recap", "notes", "action_items"],
    "contract": ["draft", "signed", "amendment", "sow"],
    "project_update": ["progress", "milestone", "delay", "completion"],
    "general": ["question", "info", "introduction", "thank_you", "urgent"],
}

def get_uncategorized_or_low_confidence():
    """Get emails that need human review"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            e.email_id,
            e.subject,
            e.sender_email,
            e.date,
            e.body_preview,
            ec.category,
            ec.subcategory,
            ec.importance_score,
            ec.ai_summary
        FROM emails e
        LEFT JOIN email_content ec ON e.email_id = ec.email_id
        WHERE ec.category IS NULL
           OR ec.importance_score < 0.6
           OR ec.category = 'general'
        ORDER BY e.date DESC
        LIMIT 50
    """)

    results = cursor.fetchall()
    conn.close()
    return results

def get_business_context():
    """Get business context for the AI to learn from"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get active projects
    cursor.execute("""
        SELECT project_code, project_name, client_name
        FROM proposals
        WHERE is_active_project = 1
        ORDER BY project_code
    """)
    projects = [{"code": r[0], "name": r[1], "client": r[2]} for r in cursor.fetchall()]

    # Get common email patterns
    cursor.execute("""
        SELECT category, subcategory, COUNT(*) as count
        FROM email_content
        WHERE category IS NOT NULL
        GROUP BY category, subcategory
        ORDER BY count DESC
        LIMIT 20
    """)
    patterns = [{"category": r[0], "subcategory": r[1], "count": r[2]} for r in cursor.fetchall()]

    conn.close()

    return {
        "active_projects": projects,
        "common_patterns": patterns,
        "company_name": "Bensley Design Studios",
        "business_type": "Luxury hospitality design",
        "key_people": ["Bill Bensley", "Brian", "Lukas"]
    }

def display_email(email_data):
    """Display email for review"""
    email_id, subject, sender, date, preview, category, subcategory, confidence, summary = email_data

    print("\n" + "="*80)
    print(f"EMAIL ID: {email_id}")
    print(f"FROM: {sender}")
    print(f"DATE: {date}")
    print(f"SUBJECT: {subject}")
    print("-"*80)
    print(f"PREVIEW:\n{preview[:300]}...")
    if summary:
        print(f"\nAI SUMMARY: {summary}")
    print("-"*80)
    if category:
        print(f"CURRENT: {category}/{subcategory or 'none'} (confidence: {confidence:.0%})")
    else:
        print("CURRENT: Uncategorized")
    print("="*80)

def save_human_feedback(email_id, category, subcategory, notes, correct_ai=False):
    """Save human verification to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Update email_content with human-verified category
    cursor.execute("""
        UPDATE email_content
        SET category = ?,
            subcategory = ?,
            importance_score = 1.0
        WHERE email_id = ?
    """, (category, subcategory, email_id))

    # Get email details for training data
    cursor.execute("""
        SELECT e.subject, e.body_preview, e.sender_email
        FROM emails e
        WHERE e.email_id = ?
    """, (email_id,))

    subject, body, sender = cursor.fetchone()

    # Create training example
    input_data = {
        "subject": subject,
        "sender": sender,
        "preview": body[:500]
    }

    output_data = {
        "category": category,
        "subcategory": subcategory,
        "notes": notes
    }

    # Save to training_data
    cursor.execute("""
        INSERT INTO training_data
        (task_type, input_data, output_data, model_used, confidence, human_verified, feedback, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "classify",
        json.dumps(input_data),
        json.dumps(output_data),
        "human",
        1.0,
        1,
        f"{'Corrected AI' if correct_ai else 'Human verified'}: {notes}",
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()
    print(f"✓ Saved and added to training data")

def main():
    print("="*80)
    print("BENSLEY INTELLIGENCE - MANUAL TRAINING FEEDBACK")
    print("="*80)
    print("\nThis tool helps you verify AI categorizations and build training data")
    print("for your local model.\n")

    # Load business context
    context = get_business_context()
    print(f"Loaded context: {len(context['active_projects'])} active projects")

    # Get emails to review
    emails = get_uncategorized_or_low_confidence()

    if not emails:
        print("\n✓ All emails are categorized with high confidence!")
        print("No manual review needed at this time.")
        return

    print(f"\nFound {len(emails)} emails needing review\n")

    reviewed = 0
    for email_data in emails:
        display_email(email_data)

        print("\nCATEGORIES:")
        for key, cat in CATEGORIES.items():
            print(f"  [{key}] {cat}")

        print("\nOPTIONS:")
        print("  [s] Skip this email")
        print("  [q] Quit and save")
        print("  [c] Add context/notes")

        choice = input("\nSelect category (or s/q/c): ").strip().lower()

        if choice == 'q':
            break
        elif choice == 's':
            continue
        elif choice == 'c':
            notes = input("Add notes about this email: ")
            print(f"Note saved: {notes}")
            continue
        elif choice not in CATEGORIES:
            print("Invalid choice, skipping...")
            continue

        category = CATEGORIES[choice]

        # Get subcategory
        if category in SUBCATEGORIES:
            print(f"\nSUBCATEGORIES for {category}:")
            subs = SUBCATEGORIES[category]
            for i, sub in enumerate(subs, 1):
                print(f"  [{i}] {sub}")
            print("  [0] None/Skip")

            sub_choice = input("Select subcategory: ").strip()
            if sub_choice == '0' or not sub_choice:
                subcategory = None
            elif sub_choice.isdigit() and 1 <= int(sub_choice) <= len(subs):
                subcategory = subs[int(sub_choice) - 1]
            else:
                subcategory = None
        else:
            subcategory = None

        # Get notes
        notes = input("Any notes about this categorization? (optional): ").strip()

        # Check if correcting AI
        correct_ai = email_data[5] is not None

        # Save
        save_human_feedback(email_data[0], category, subcategory, notes, correct_ai)
        reviewed += 1

        print(f"\n[{reviewed}/{len(emails)}] reviewed")

    print("\n" + "="*80)
    print(f"SESSION COMPLETE: {reviewed} emails verified")
    print("="*80)
    print("\nYour feedback has been saved to the training database.")
    print("This will improve the AI's accuracy for future emails.\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStopped by user. Progress saved.")
        sys.exit(0)
