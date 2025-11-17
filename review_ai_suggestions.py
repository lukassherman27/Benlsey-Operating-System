#!/usr/bin/env python3
"""
Interactive AI Suggestion Review Tool

Review AI categorizations and provide feedback to build training data.
"""

import sqlite3
import json
from datetime import datetime

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


class AIReviewer:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        self.reviewed = 0
        self.approved = 0
        self.rejected = 0
        self.modified = 0

    def get_pending_suggestions(self):
        """Get all pending AI suggestions"""
        self.cursor.execute("""
            SELECT * FROM ai_suggestions_queue
            WHERE status = 'pending'
            AND suggestion_type = 'email_categorization'
            ORDER BY created_at DESC
        """)
        return self.cursor.fetchall()

    def get_email_context(self, email_id):
        """Get the email for context"""
        self.cursor.execute("""
            SELECT * FROM emails WHERE email_id = ?
        """, (email_id,))
        return self.cursor.fetchone()

    def show_suggestion(self, suggestion):
        """Display a suggestion with email context"""
        proposed_fix = json.loads(suggestion['proposed_fix'])
        evidence = json.loads(suggestion['evidence'])

        # Get email
        email = self.get_email_context(proposed_fix['email_id'])

        print("\n" + "=" * 100)
        print(f"📧 SUGGESTION #{self.reviewed + 1}")
        print("=" * 100)

        # Email context
        print(f"\n📨 Email:")
        print(f"   From: {email['sender_email']}")
        print(f"   Subject: {email['subject']}")
        print(f"   Date: {email['date']}")
        print(f"\n   Preview: {email['snippet'][:200] if email['snippet'] else 'No preview available'}...")

        # AI's suggestion
        print(f"\n🤖 AI Analysis:")
        print(f"   Suggested Category: {proposed_fix['suggested_category']}")
        print(f"   Confidence: {suggestion['confidence'] * 100:.0f}%")
        print(f"   Reasoning: {proposed_fix.get('ai_reasoning', 'N/A')}")

        if proposed_fix.get('is_new_category'):
            print(f"\n   ⚠️  NEW CATEGORY SUGGESTION!")
            print(f"   Why new: {proposed_fix.get('new_category_reason', 'N/A')}")

        # Entities found
        entities = proposed_fix.get('entities', {})
        if any(entities.values()):
            print(f"\n   📋 Entities Detected:")
            if entities.get('project_codes'):
                print(f"      Projects: {', '.join(entities['project_codes'])}")
            if entities.get('clients'):
                print(f"      Clients: {', '.join(entities['clients'])}")
            if entities.get('amounts'):
                print(f"      Amounts: {', '.join(map(str, entities['amounts']))}")

        print("\n" + "=" * 100)

        return proposed_fix, email

    def review_suggestion(self, suggestion):
        """Interactive review of one suggestion"""
        proposed_fix, email = self.show_suggestion(suggestion)

        print("\nWhat do you want to do?")
        print("  1. ✅ Approve - AI is correct")
        print("  2. ❌ Reject - AI is wrong, I'll provide correct category")
        print("  3. ➕ New Category - Create a new category")
        print("  4. 📝 Modify - Similar but needs tweaking")
        print("  5. ⏭️  Skip - Review later")
        print("  6. 🛑 Quit - Stop reviewing")

        choice = input("\nYour choice (1-6): ").strip()

        if choice == '1':
            self.approve_suggestion(suggestion, proposed_fix, email)
        elif choice == '2':
            self.reject_suggestion(suggestion, proposed_fix, email)
        elif choice == '3':
            self.create_new_category(suggestion, proposed_fix, email)
        elif choice == '4':
            self.modify_suggestion(suggestion, proposed_fix, email)
        elif choice == '5':
            print("⏭️  Skipped")
        elif choice == '6':
            return False
        else:
            print("Invalid choice, skipping...")

        return True

    def approve_suggestion(self, suggestion, proposed_fix, email):
        """User approves AI's suggestion"""
        category = proposed_fix['suggested_category']

        # Update email
        self.cursor.execute("""
            UPDATE emails
            SET category = ?, importance_score = ?
            WHERE email_id = ?
        """, (category, proposed_fix.get('importance', 50), proposed_fix['email_id']))

        # Mark suggestion as approved
        self.cursor.execute("""
            UPDATE ai_suggestions_queue
            SET status = 'approved'
            WHERE id = ?
        """, (suggestion['id'],))

        # Log to training data
        snippet_text = email['snippet'][:100] if email['snippet'] else 'No preview'
        self.log_training_data(
            source_type='email',
            source_ref=proposed_fix['email_id'],
            source_text=f"{email['subject']} | {snippet_text}",
            ai_suggestion=category,
            ai_reasoning=proposed_fix.get('ai_reasoning', ''),
            ai_confidence=suggestion['confidence'],
            human_correction=category,  # Same as suggestion (approved)
            correction_reason='approved',
            model_used='gpt-4o'
        )

        self.conn.commit()
        self.approved += 1
        print(f"\n✅ Approved! Email categorized as '{category}'")

    def reject_suggestion(self, suggestion, proposed_fix, email):
        """User rejects and provides correct category"""
        print(f"\n❌ AI suggested: {proposed_fix['suggested_category']}")
        print("\nWhat's the CORRECT category?")

        # Show existing categories
        self.cursor.execute("SELECT DISTINCT category FROM emails WHERE category IS NOT NULL")
        existing = [row['category'] for row in self.cursor.fetchall()]
        if existing:
            print(f"\n   Existing categories: {', '.join(existing[:10])}")

        correct_category = input("\nCorrect category: ").strip()
        reason = input("Why is this the correct category? ").strip()

        if not correct_category:
            print("Skipping...")
            return

        # Update email
        self.cursor.execute("""
            UPDATE emails
            SET category = ?
            WHERE email_id = ?
        """, (correct_category, proposed_fix['email_id']))

        # Mark suggestion as rejected
        self.cursor.execute("""
            UPDATE ai_suggestions_queue
            SET status = 'rejected'
            WHERE id = ?
        """, (suggestion['id'],))

        # Log to training data (IMPORTANT - AI learns from this!)
        snippet_text = email['snippet'][:100] if email['snippet'] else 'No preview'
        self.log_training_data(
            source_type='email',
            source_ref=proposed_fix['email_id'],
            source_text=f"{email['subject']} | {snippet_text}",
            ai_suggestion=proposed_fix['suggested_category'],
            ai_reasoning=proposed_fix.get('ai_reasoning', ''),
            ai_confidence=suggestion['confidence'],
            human_correction=correct_category,
            correction_reason=reason,
            model_used='gpt-4o'
        )

        self.conn.commit()
        self.rejected += 1
        print(f"\n✅ Corrected to '{correct_category}' - AI will learn from this!")

    def create_new_category(self, suggestion, proposed_fix, email):
        """User creates a brand new category"""
        print("\n➕ Creating new category")
        new_category = input("New category name: ").strip()
        reason = input("What makes this a new category? ").strip()

        if not new_category:
            print("Skipping...")
            return

        # Update email
        self.cursor.execute("""
            UPDATE emails
            SET category = ?
            WHERE email_id = ?
        """, (new_category, proposed_fix['email_id']))

        # Mark suggestion
        self.cursor.execute("""
            UPDATE ai_suggestions_queue
            SET status = 'rejected'
            WHERE id = ?
        """, (suggestion['id'],))

        # Log to training data
        snippet_text = email['snippet'][:100] if email['snippet'] else 'No preview'
        self.log_training_data(
            source_type='email',
            source_ref=proposed_fix['email_id'],
            source_text=f"{email['subject']} | {snippet_text}",
            ai_suggestion=proposed_fix['suggested_category'],
            ai_reasoning=proposed_fix.get('ai_reasoning', ''),
            ai_confidence=suggestion['confidence'],
            human_correction=new_category,
            correction_reason=f"NEW CATEGORY: {reason}",
            model_used='gpt-4o'
        )

        self.conn.commit()
        self.modified += 1
        print(f"\n✅ Created new category '{new_category}' - AI will learn this pattern!")

    def modify_suggestion(self, suggestion, proposed_fix, email):
        """User modifies the suggestion"""
        print(f"\n📝 AI suggested: {proposed_fix['suggested_category']}")
        modified = input("What should it be instead? ").strip()
        reason = input("Why this change? ").strip()

        if not modified:
            print("Skipping...")
            return

        # Update email
        self.cursor.execute("""
            UPDATE emails
            SET category = ?
            WHERE email_id = ?
        """, (modified, proposed_fix['email_id']))

        # Mark suggestion
        self.cursor.execute("""
            UPDATE ai_suggestions_queue
            SET status = 'approved'  # Modified but generally correct
            WHERE id = ?
        """, (suggestion['id'],))

        # Log to training data
        snippet_text = email['snippet'][:100] if email['snippet'] else 'No preview'
        self.log_training_data(
            source_type='email',
            source_ref=proposed_fix['email_id'],
            source_text=f"{email['subject']} | {snippet_text}",
            ai_suggestion=proposed_fix['suggested_category'],
            ai_reasoning=proposed_fix.get('ai_reasoning', ''),
            ai_confidence=suggestion['confidence'],
            human_correction=modified,
            correction_reason=f"MODIFIED: {reason}",
            model_used='gpt-4o'
        )

        self.conn.commit()
        self.modified += 1
        print(f"\n✅ Modified to '{modified}' - AI will learn the nuance!")

    def log_training_data(self, **kwargs):
        """Log feedback to training_data table (using existing schema)"""
        # Map to existing schema
        input_data = json.dumps({
            'source_type': kwargs['source_type'],
            'source_ref': kwargs['source_ref'],
            'source_text': kwargs['source_text'],
            'ai_reasoning': kwargs['ai_reasoning']
        })

        output_data = json.dumps({
            'ai_suggestion': kwargs['ai_suggestion'],
            'human_correction': kwargs['human_correction']
        })

        is_approved = kwargs['ai_suggestion'] == kwargs['human_correction']

        self.cursor.execute("""
            INSERT INTO training_data (
                task_type, input_data, output_data,
                model_used, confidence, human_verified,
                feedback, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            'email_categorization',
            input_data,
            output_data,
            kwargs['model_used'],
            kwargs['ai_confidence'],
            1 if is_approved else 0,
            kwargs['correction_reason']
        ))

    def run_review_session(self):
        """Main review loop"""
        print("\n" + "=" * 100)
        print("🧠 AI SUGGESTION REVIEW SESSION")
        print("=" * 100)
        print("\nYou're teaching the AI about your business!")
        print("Your feedback becomes training data for smarter automation.\n")

        suggestions = self.get_pending_suggestions()
        total = len(suggestions)

        if total == 0:
            print("No pending suggestions to review!")
            return

        print(f"Found {total} suggestions to review.\n")

        for suggestion in suggestions:
            if not self.review_suggestion(suggestion):
                break
            self.reviewed += 1

        # Summary
        print("\n" + "=" * 100)
        print("📊 REVIEW SESSION SUMMARY")
        print("=" * 100)
        print(f"   Reviewed: {self.reviewed}")
        print(f"   ✅ Approved: {self.approved}")
        print(f"   ❌ Rejected: {self.rejected}")
        print(f"   📝 Modified: {self.modified}")
        print(f"\n   Training examples created: {self.approved + self.rejected + self.modified}")
        print("=" * 100)

        # Show training progress
        self.cursor.execute("SELECT COUNT(*) FROM training_data")
        total_training = self.cursor.fetchone()[0]
        print(f"\n📚 Total training examples: {total_training}")

        if total_training >= 100:
            print("🎉 You have 100+ examples! Ready to fine-tune local model!")
        else:
            print(f"   {100 - total_training} more examples until local model training")

    def close(self):
        self.conn.close()


def main():
    reviewer = AIReviewer()
    try:
        reviewer.run_review_session()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    finally:
        reviewer.close()


if __name__ == "__main__":
    main()
