#!/usr/bin/env python3
"""
AI Training Mode - Pure Learning (NO Database Modifications)
Teach the model about your business without changing production data
NOW WITH: Custom category creation and feedback loop
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
    "c": "CREATE_NEW",  # New option
    "0": "other"
}

SUBCATEGORIES = {
    "proposal": ["initial", "follow_up", "revision", "won", "lost"],
    "meeting": ["scheduled", "recap", "notes", "action_items"],
    "contract": ["draft", "signed", "amendment", "sow"],
    "project_update": ["progress", "milestone", "delay", "completion"],
    "design": ["concept", "review", "revision", "final"],
    "rfi": ["client_question", "vendor_question", "clarification"],
    "general": ["question", "info", "introduction", "thank_you", "urgent"],
}

def ensure_feedback_table():
    """Create table for category suggestions and system improvements"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_feedback (
            feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
            feedback_type TEXT,
            suggestion TEXT,
            reasoning TEXT,
            example_email_id INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            reviewed_at TEXT,
            implemented BOOLEAN DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

def suggest_new_category(category_name, subcategories, reasoning, email_id=None):
    """Save suggestion for new category to be reviewed"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    suggestion_data = {
        "category": category_name,
        "subcategories": subcategories,
        "reasoning": reasoning
    }

    cursor.execute("""
        INSERT INTO system_feedback
        (feedback_type, suggestion, reasoning, example_email_id, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        "new_category",
        json.dumps(suggestion_data),
        reasoning,
        email_id,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()
    print(f"\n✓ Category suggestion saved for review: '{category_name}'")
    print(f"  This will be reviewed and potentially added to the system.")

def get_custom_categories():
    """Get any custom categories user has created in this session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT suggestion FROM system_feedback
        WHERE feedback_type = 'new_category'
        AND status = 'pending'
    """)

    categories = []
    for row in cursor.fetchall():
        try:
            data = json.loads(row[0])
            categories.append(data['category'])
        except:
            pass

    conn.close()
    return categories

def get_emails_for_training(limit=50):
    """Get random emails for training (all emails, not just uncategorized)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            e.email_id,
            e.subject,
            e.sender_email,
            e.date,
            e.body_preview,
            e.body_full,
            e.has_attachments,
            ec.category,
            ec.subcategory,
            ec.importance_score,
            ec.ai_summary,
            e.folder
        FROM emails e
        LEFT JOIN email_content ec ON e.email_id = ec.email_id
        ORDER BY RANDOM()
        LIMIT ?
    """, (limit,))

    results = cursor.fetchall()
    conn.close()
    return results

def get_email_attachments(email_id):
    """Get attachment filenames for an email"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT filename, filesize, mime_type
        FROM email_attachments
        WHERE email_id = ?
    """, (email_id,))

    attachments = cursor.fetchall()
    conn.close()
    return attachments

def get_active_projects():
    """Get list of ALL proposals for linking (now in proposals table after swap)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Query the proposals table to get ALL 114 proposals
    cursor.execute("""
        SELECT project_id, project_code, project_title,
               COALESCE(country, '') as country
        FROM proposals
        ORDER BY project_code
    """)
    projects = cursor.fetchall()
    conn.close()
    return projects

def display_email_for_training(email_data, projects):
    """Display email with all context for training"""
    email_id, subject, sender, date, preview, body_full, has_attachments, ai_cat, ai_sub, ai_score, ai_summary, folder = email_data

    print("\n" + "="*80)
    print(f"EMAIL ID: {email_id}")
    print(f"FROM: {sender}")
    print(f"DATE: {date}")
    print(f"FOLDER: {folder}")
    print(f"SUBJECT: {subject}")
    print("-"*80)

    # Show full body (or as much as we have)
    if body_full:
        body_text = body_full[:2000]  # Show up to 2000 chars
        if len(body_full) > 2000:
            print(f"BODY (showing first 2000 chars of {len(body_full)}):")
            print(body_text + "\n...[truncated]...")
        else:
            print(f"BODY:")
            print(body_text)
    elif preview:
        print(f"PREVIEW (no full body):\n{preview}")
    else:
        print("BODY: (no content available)")

    # Show attachments
    if has_attachments:
        attachments = get_email_attachments(email_id)
        if attachments:
            print(f"\n📎 ATTACHMENTS ({len(attachments)}):")
            for filename, filesize, mime_type in attachments:
                size_kb = filesize / 1024 if filesize else 0
                print(f"   • {filename} ({size_kb:.1f} KB, {mime_type})")

    if ai_summary:
        print(f"\nAI SUMMARY: {ai_summary}")

    print("-"*80)

    if ai_cat:
        print(f"AI SUGGESTED: {ai_cat}/{ai_sub or 'none'} (confidence: {ai_score:.0%})")
    else:
        print("AI SUGGESTED: (not categorized)")

    print("="*80)

    # Show relevant projects if subject mentions them
    if subject:
        mentioned_projects = []
        for proj_id, code, name, client in projects:
            if code and code.upper() in subject.upper():
                mentioned_projects.append((proj_id, code, name, client))

        if mentioned_projects:
            print("\n📋 DETECTED PROJECTS IN SUBJECT:")
            for proj_id, code, name, client in mentioned_projects:
                print(f"   [{proj_id}] {code}: {name} ({client})")

def save_training_example(email_id, category, subcategory, notes, project_id=None, relationships=None):
    """
    Save training example WITHOUT modifying email_content table
    Pure training mode - only adds to training_data
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get email details
    cursor.execute("""
        SELECT e.subject, e.body_preview, e.sender_email, e.folder
        FROM emails e
        WHERE e.email_id = ?
    """, (email_id,))

    result = cursor.fetchone()
    if not result:
        print("Error: Email not found")
        conn.close()
        return

    subject, body, sender, folder = result

    # Create training example
    input_data = {
        "email_id": email_id,
        "subject": subject,
        "sender": sender,
        "preview": body[:500] if body else "",
        "folder": folder
    }

    output_data = {
        "category": category,
        "subcategory": subcategory,
        "notes": notes,
        "project_id": project_id,
        "relationships": relationships or []
    }

    # Save to training_data ONLY (no modifications to email_content)
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
        f"Human training: {notes}",
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()
    print(f"✓ Training example saved (database unchanged)")

def link_email_to_project(email_id, project_id):
    """Save project relationship as training data (no database modification)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get email and project details
    cursor.execute("SELECT subject FROM emails WHERE email_id = ?", (email_id,))
    subject = cursor.fetchone()[0]

    cursor.execute("SELECT project_code, project_name FROM proposals WHERE proposal_id = ?", (project_id,))
    project_code, project_name = cursor.fetchone()

    # Save as training example
    input_data = {
        "email_id": email_id,
        "subject": subject,
        "task": "link_to_project"
    }

    output_data = {
        "project_id": project_id,
        "project_code": project_code,
        "project_name": project_name,
        "reasoning": "Human linked this email to project"
    }

    cursor.execute("""
        INSERT INTO training_data
        (task_type, input_data, output_data, model_used, confidence, human_verified, feedback, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "link_to_project",
        json.dumps(input_data),
        json.dumps(output_data),
        "human",
        1.0,
        1,
        f"Linked to {project_code}",
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()
    print(f"✓ Relationship saved: Email → {project_code}")

def create_custom_category(email_id):
    """Interactive flow to create a new category"""
    print("\n" + "="*80)
    print("CREATE NEW CATEGORY")
    print("="*80)
    print("\nYou've identified a category that doesn't exist yet.")
    print("This helps improve the system for everyone!\n")

    category_name = input("Category name (e.g., 'travel', 'vendor', 'press'): ").strip().lower()

    if not category_name:
        print("Cancelled.")
        return None, None

    print(f"\nGreat! Creating category: '{category_name}'")

    # Get subcategories
    print("\nWhat subcategories should this have? (comma-separated, or leave empty)")
    print("Example: booked, quote_request, itinerary")
    subcats_input = input("> ").strip()

    subcategories = []
    if subcats_input:
        subcategories = [s.strip() for s in subcats_input.split(',')]

    # Get reasoning
    print("\nWhy is this category needed? What makes it distinct?")
    reasoning = input("> ").strip()

    # Save suggestion
    suggest_new_category(category_name, subcategories, reasoning, email_id)

    return category_name, subcategories

def main():
    print("="*80)
    print("BENSLEY INTELLIGENCE - AI TRAINING MODE v2.0")
    print("="*80)
    print("\n⚠️  PURE TRAINING MODE - NO DATABASE MODIFICATIONS")
    print("    Your feedback is saved for model training only.")
    print("    The production email database remains unchanged.")
    print("\n✨ NEW: Create custom categories on the fly!")
    print("         Your suggestions improve the entire system.\n")

    # Ensure feedback table exists
    ensure_feedback_table()

    # Load projects
    projects = get_active_projects()
    print(f"Loaded {len(projects)} active projects (for linking reference)")

    # Get emails to train on
    print("\nHow many emails do you want to train on?")
    try:
        limit = int(input("Number (10-100, default 20): ") or "20")
    except:
        limit = 20

    emails = get_emails_for_training(limit)

    if not emails:
        print("\n✗ No emails found")
        return

    print(f"\nLoaded {len(emails)} random emails from ALL folders")
    print("\nYou will teach the AI about:")
    print("  • What category each email belongs to")
    print("  • NEW CATEGORIES if existing ones don't fit")
    print("  • Which project it relates to")
    print("  • Business context and relationships")
    print("  • Why you made each decision\n")

    input("Press ENTER to start training...")

    trained = 0
    custom_categories_created = []

    for email_data in emails:
        display_email_for_training(email_data, projects)

        print("\n" + "="*80)
        print("TRAINING OPTIONS:")
        print("="*80)
        print("\nCATEGORIES:")
        for key, cat in CATEGORIES.items():
            if cat == "CREATE_NEW":
                print(f"  [{key}] ✨ Create new category")
            else:
                print(f"  [{key}] {cat}")

        # Show any custom categories created this session
        if custom_categories_created:
            print("\n  YOUR CUSTOM CATEGORIES (this session):")
            for custom_cat in custom_categories_created:
                print(f"      • {custom_cat}")

        print("\nACTIONS:")
        print("  [p] Link to project")
        print("  [n] Add detailed notes/context")
        print("  [f] General feedback about the system")
        print("  [s] Skip this email")
        print("  [q] Quit and save")

        choice = input("\nWhat should I learn? (category/action): ").strip().lower()

        if choice == 'q':
            break
        elif choice == 's':
            continue
        elif choice == 'f':
            # General system feedback
            print("\nWhat feedback do you have about the system?")
            feedback = input("> ")
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_feedback
                (feedback_type, suggestion, reasoning, created_at)
                VALUES (?, ?, ?, ?)
            """, ("general_feedback", feedback, "", datetime.now().isoformat()))
            conn.commit()
            conn.close()
            print("✓ Feedback saved for review")
            continue
        elif choice == 'n':
            notes = input("\nTeach me about this email:\n> ")
            save_training_example(email_data[0], None, None, notes)
            trained += 1
            continue
        elif choice == 'p':
            # Link to project
            print(f"\nAVAILABLE PROJECTS ({len(projects)} total):")
            print("Type to search, or enter number:")

            # Show all projects
            for i, (proj_id, code, name, country) in enumerate(projects, 1):
                print(f"  [{i}] {code}: {name} ({country or 'No location'})")

            proj_choice = input("\nWhich project? (search term or number, 0 to cancel): ").strip()

            if not proj_choice or proj_choice == '0':
                continue

            # Check if it's a search term (not a number)
            if not proj_choice.isdigit():
                # Search for matching project
                search = proj_choice.lower()
                matches = []
                for i, (proj_id, code, name, country) in enumerate(projects, 1):
                    if (search in code.lower() or
                        search in name.lower() or
                        (country and search in country.lower())):
                        matches.append((i, proj_id, code, name, country))

                if not matches:
                    print(f"No projects found matching '{proj_choice}'")
                    continue
                elif len(matches) == 1:
                    print(f"\n✓ Found: {matches[0][2]}: {matches[0][3]}")
                    link_email_to_project(email_data[0], matches[0][1])
                    trained += 1
                else:
                    print(f"\nFound {len(matches)} matches:")
                    for i, proj_id, code, name, country in matches:
                        print(f"  [{i}] {code}: {name} ({country or 'No location'})")
                    choice = input("Select number: ").strip()
                    if choice.isdigit():
                        selected_i = int(choice) - 1
                        if 0 <= selected_i < len(projects):
                            link_email_to_project(email_data[0], projects[selected_i][0])
                            trained += 1
            else:
                # Direct number selection
                proj_idx = int(proj_choice) - 1
                if 0 <= proj_idx < len(projects):
                    link_email_to_project(email_data[0], projects[proj_idx][0])
                    trained += 1
            continue
        elif choice == 'c':
            # Create new category
            category, subcategories = create_custom_category(email_data[0])
            if category:
                custom_categories_created.append(category)
                # Now categorize this email with the new category
                print(f"\nNow categorizing this email as '{category}'")
                if subcategories:
                    print("\nSubcategories:")
                    for i, sub in enumerate(subcategories, 1):
                        print(f"  [{i}] {sub}")
                    sub_choice = input("Select subcategory (number or 0 for none): ").strip()
                    if sub_choice and sub_choice != '0' and sub_choice.isdigit():
                        sub_idx = int(sub_choice) - 1
                        if 0 <= sub_idx < len(subcategories):
                            subcategory = subcategories[sub_idx]
                        else:
                            subcategory = None
                    else:
                        subcategory = None
                else:
                    subcategory = None

                notes = input("Why this category for this email? > ").strip()
                save_training_example(email_data[0], category, subcategory, notes)
                trained += 1
            continue
        elif choice not in CATEGORIES:
            print("Invalid choice, skipping...")
            continue

        category = CATEGORIES[choice]

        # Get subcategory
        subcategory = None
        if category in SUBCATEGORIES:
            print(f"\nSUBCATEGORIES for {category}:")
            subs = SUBCATEGORIES[category]
            for i, sub in enumerate(subs, 1):
                print(f"  [{i}] {sub}")
            print("  [0] None/Skip")

            sub_choice = input("Select subcategory: ").strip()
            if sub_choice and sub_choice != '0' and sub_choice.isdigit():
                sub_idx = int(sub_choice) - 1
                if 0 <= sub_idx < len(subs):
                    subcategory = subs[sub_idx]

        # Get teaching notes
        print("\n💡 WHY this category? (helps model learn your reasoning)")
        notes = input("> ").strip()

        # Check if should link to project
        print("\nDoes this relate to a project? (y/N): ", end="")
        if input().lower() == 'y':
            print(f"\nAVAILABLE PROJECTS ({len(projects)} total):")
            print("Type to search, or enter number:")

            # Show all projects
            for i, (proj_id, code, name, country) in enumerate(projects, 1):
                print(f"  [{i}] {code}: {name} ({country or 'No location'})")

            proj_choice = input("\nWhich project? (search term or number, 0 to skip): ").strip()
            project_id = None

            if proj_choice and proj_choice != '0':
                # Check if it's a search term (not a number)
                if not proj_choice.isdigit():
                    # Search for matching project
                    search = proj_choice.lower()
                    matches = []
                    for i, (proj_id, code, name, country) in enumerate(projects, 1):
                        if (search in code.lower() or
                            search in name.lower() or
                            (country and search in country.lower())):
                            matches.append((i, proj_id, code, name, country))

                    if not matches:
                        print(f"No projects found matching '{proj_choice}'")
                    elif len(matches) == 1:
                        print(f"\n✓ Found: {matches[0][2]}: {matches[0][3]}")
                        project_id = matches[0][1]
                        link_email_to_project(email_data[0], project_id)
                    else:
                        print(f"\nFound {len(matches)} matches:")
                        for i, proj_id, code, name, country in matches:
                            print(f"  [{i}] {code}: {name} ({country or 'No location'})")
                        choice = input("Select number: ").strip()
                        if choice.isdigit():
                            selected_i = int(choice) - 1
                            if 0 <= selected_i < len(projects):
                                project_id = projects[selected_i][0]
                                link_email_to_project(email_data[0], project_id)
                else:
                    # Direct number selection
                    proj_idx = int(proj_choice) - 1
                    if 0 <= proj_idx < len(projects):
                        project_id = projects[proj_idx][0]
                        link_email_to_project(email_data[0], project_id)
        else:
            project_id = None

        # Save training example
        save_training_example(email_data[0], category, subcategory, notes, project_id)
        trained += 1

        print(f"\n📊 Progress: {trained}/{len(emails)} emails trained")

    print("\n" + "="*80)
    print(f"TRAINING SESSION COMPLETE: {trained} examples added")
    print("="*80)

    if custom_categories_created:
        print(f"\n✨ NEW CATEGORIES SUGGESTED: {len(custom_categories_created)}")
        for cat in custom_categories_created:
            print(f"   • {cat}")
        print("\nRun: python3 review_feedback.py to review and implement")

    print("\nYour training data has been saved!")
    print("The production database was NOT modified.")
    print("\nNext steps:")
    print("  1. Review suggestions: python3 review_feedback.py")
    print("  2. Export training data: python3 export_training_data.py")
    print("  3. Train your model with the new examples")
    print("  4. Test improved accuracy: python3 local_model_inference.py compare")
    print("\nThe more you train, the smarter it gets!\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTraining stopped. Progress saved.")
        sys.exit(0)
