#!/usr/bin/env python3
"""
Manual Document Classifier & Training Data Generator

Review imported attachments and correct classifications.
All corrections are saved to training_data table for model fine-tuning.
"""

import sqlite3
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Document types
DOCUMENT_TYPES = {
    '1': ('bensley_contract', 'Bensley Contract (we send to clients)'),
    '2': ('external_contract', 'External Contract (clients send to us)'),
    '3': ('proposal', 'Proposal / Quotation'),
    '4': ('invoice', 'Invoice / Receipt'),
    '5': ('design_document', 'Design Document (drawings, plans, renderings)'),
    '6': ('presentation', 'Presentation (PPT, Keynote)'),
    '7': ('financial', 'Financial Document'),
    '8': ('correspondence', 'General Correspondence'),
    '9': ('other', 'Other'),
    's': (None, 'Skip this document'),
}


def show_document(attachment):
    """Display document information"""
    print("\n" + "=" * 80)
    print(f"📄 File: {attachment['filename']}")
    print(f"   Current Classification: {attachment['document_type']}")
    print(f"   Size: {attachment['filesize']:,} bytes")
    print(f"   MIME Type: {attachment['mime_type']}")
    print(f"   Date: {attachment['created_at']}")
    print(f"   Path: {attachment['filepath']}")

    # Show email context
    print(f"\n📧 Email Context:")
    print(f"   Subject: {attachment['email_subject']}")
    print(f"   From: {attachment['sender_email']}")
    print(f"   Date: {attachment['email_date']}")

    if attachment['project_code']:
        print(f"   Project: {attachment['project_code']} - {attachment['project_name']}")

    print("=" * 80)


def get_user_classification():
    """Get classification from user"""
    print("\n📝 Document Type:")
    for key, (doc_type, description) in DOCUMENT_TYPES.items():
        print(f"   {key}. {description}")

    while True:
        choice = input("\nEnter number (or 's' to skip, 'q' to quit): ").strip().lower()

        if choice == 'q':
            return 'quit', None

        if choice in DOCUMENT_TYPES:
            doc_type, description = DOCUMENT_TYPES[choice]
            if doc_type is None:
                return 'skip', None

            # For contracts, ask if it's incoming or outgoing
            direction = None
            if 'contract' in doc_type:
                print("\n📬 Contract Direction:")
                print("   1. Outgoing (we sent to client)")
                print("   2. Incoming (client sent to us)")
                dir_choice = input("Enter 1 or 2: ").strip()
                direction = 'outgoing' if dir_choice == '1' else 'incoming'

            # Ask if signed/executed
            is_signed = None
            if 'contract' in doc_type:
                signed_choice = input("Is it signed? (y/n): ").strip().lower()
                is_signed = 1 if signed_choice == 'y' else 0

            # Get feedback/notes
            feedback = input("Any notes about this document? (optional): ").strip()

            return doc_type, {
                'direction': direction,
                'is_signed': is_signed,
                'feedback': feedback
            }

        print("Invalid choice, please try again.")


def save_training_data(conn, attachment, correct_type, metadata):
    """Save correction to training_data table"""
    cursor = conn.cursor()

    # Create input representation for training
    input_data = (
        f"Filename: {attachment['filename']}\n"
        f"MIME Type: {attachment['mime_type']}\n"
        f"Size: {attachment['filesize']} bytes\n"
        f"Email Subject: {attachment['email_subject']}\n"
        f"Sender: {attachment['sender_email']}"
    )

    # Create output representation
    output_data = correct_type
    if metadata.get('direction'):
        output_data += f" (direction: {metadata['direction']})"

    # Insert into training_data
    cursor.execute("""
        INSERT INTO training_data (
            task_type,
            input_data,
            output_data,
            model_used,
            confidence,
            human_verified,
            feedback
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        'classify_attachment',
        input_data,
        output_data,
        'human_supervision',
        1.0,
        1,
        metadata.get('feedback', '')
    ))

    conn.commit()
    print("   ✅ Training data saved!")


def update_attachment(conn, attachment_id, correct_type, metadata):
    """Update attachment with correct classification"""
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE email_attachments
        SET document_type = ?,
            contract_direction = ?,
            is_signed = ?
        WHERE attachment_id = ?
    """, (
        correct_type,
        metadata.get('direction'),
        metadata.get('is_signed'),
        attachment_id
    ))

    conn.commit()
    print("   ✅ Document classification updated!")


def main():
    print("=" * 80)
    print("MANUAL DOCUMENT CLASSIFIER & TRAINING DATA GENERATOR")
    print("=" * 80)
    print("\nReview and correct document classifications.")
    print("All corrections will be saved as training data for model fine-tuning.\n")

    db_path = os.getenv('DATABASE_PATH')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all attachments that need review
    # Start with most recent
    cursor.execute("""
        SELECT
            a.attachment_id,
            a.filename,
            a.filepath,
            a.filesize,
            a.mime_type,
            a.document_type,
            a.contract_direction,
            a.is_signed,
            a.created_at,
            e.email_id,
            e.subject AS email_subject,
            e.sender_email,
            e.date AS email_date,
            p.project_code,
            p.project_name
        FROM email_attachments a
        JOIN emails e ON a.email_id = e.email_id
        LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
        LEFT JOIN proposals p ON epl.proposal_id = p.proposal_id
        ORDER BY a.created_at DESC
    """)

    attachments = cursor.fetchall()
    total = len(attachments)

    print(f"Found {total} documents to review.\n")

    reviewed = 0
    corrected = 0
    skipped = 0

    for idx, attachment in enumerate(attachments, 1):
        show_document(attachment)

        print(f"\n[{idx}/{total}]")

        doc_type, metadata = get_user_classification()

        if doc_type == 'quit':
            print("\n👋 Quitting...")
            break

        if doc_type == 'skip':
            skipped += 1
            continue

        # Save to training data
        save_training_data(conn, attachment, doc_type, metadata)

        # Update attachment if classification changed
        if doc_type != attachment['document_type']:
            update_attachment(conn, attachment['attachment_id'], doc_type, metadata)
            corrected += 1

        reviewed += 1

    conn.close()

    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Total documents: {total}")
    print(f"Reviewed: {reviewed}")
    print(f"Corrected: {corrected}")
    print(f"Skipped: {skipped}")
    print(f"\n✅ Training data saved to database!")
    print(f"   Use this data to fine-tune a local classification model.")
    print("\n")


if __name__ == '__main__':
    main()
