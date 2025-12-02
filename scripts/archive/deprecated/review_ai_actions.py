#!/usr/bin/env python3
"""
AI ACTIONS REVIEW & FEEDBACK

Review what the AI did and provide feedback so it learns.

When AI fucks up:
1. You see what it did
2. You correct it: "This should be X, not Y"
3. You add context: "Because this project is in construction phase"
4. AI logs this as training data
5. AI gets smarter over time
"""

import sqlite3
import json
from datetime import datetime

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


class AIActionsReviewer:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        self.reviewed = 0
        self.correct = 0
        self.corrected = 0
        self.context_added = 0

    def get_recent_actions(self, limit=20):
        """Get recent AI actions from emails that were processed"""
        self.cursor.execute("""
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.category,
                e.date,
                e.snippet,
                e.body_full
            FROM emails e
            WHERE e.category IS NOT NULL
            AND (length(e.body_full) > 50 OR length(e.snippet) > 50)
            ORDER BY e.created_at DESC
            LIMIT ?
        """, (limit,))

        return self.cursor.fetchall()

    def show_action(self, email):
        """Show what AI did with this email"""
        print("\n" + "=" * 100)
        print(f"📧 EMAIL #{self.reviewed + 1}")
        print("=" * 100)

        print(f"\n📨 Email:")
        print(f"   From: {email['sender_email']}")
        print(f"   Subject: {email['subject']}")
        print(f"   Date: {email['date']}")

        # Show full body or snippet
        body = email['body_full'] or email['snippet'] or 'No content'
        if body and len(body) > 500:
            print(f"\n   Body (first 500 chars):\n   {body[:500]}...")
            print(f"\n   [... {len(body) - 500} more characters ...]")
        else:
            print(f"\n   Body:\n   {body}")

        print(f"\n🤖 AI Action:")
        print(f"   Categorized as: {email['category']}")

        # Check if project was updated
        self.cursor.execute("""
            SELECT project_code FROM email_project_links
            WHERE email_id = ?
        """, (email['email_id'],))

        projects = self.cursor.fetchall()
        if projects:
            print(f"   Linked to projects: {', '.join([p['project_code'] for p in projects])}")

        # Check if RFI was created
        self.cursor.execute("""
            SELECT rfi_id, subject FROM rfis
            WHERE extracted_from_email_id = ?
        """, (email['email_id'],))

        rfis = self.cursor.fetchall()
        if rfis:
            print(f"   Created RFI: {rfis[0]['subject']}")

        print("\n" + "=" * 100)

    def review_action(self, email):
        """Interactive review of AI action"""
        self.show_action(email)

        print("\nWas the AI correct?")
        print("  1. ✅ Correct - AI did the right thing")
        print("  2. ❌ Wrong - Provide correction")
        print("  3. 💡 Add Context - AI was right but add learning context")
        print("  4. ⏭️  Skip - Review later")
        print("  5. 🛑 Quit - Stop reviewing")

        choice = input("\nYour choice (1-5): ").strip()

        if choice == '1':
            self.mark_correct(email)
        elif choice == '2':
            self.provide_correction(email)
        elif choice == '3':
            self.add_context(email)
        elif choice == '4':
            print("⏭️  Skipped")
        elif choice == '5':
            return False
        else:
            print("Invalid choice, skipping...")

        return True

    def mark_correct(self, email):
        """AI was correct - log as positive training example"""
        print("\n✅ Marking as correct...")

        reason = input("Optional: Why is this correct? (or press Enter to skip): ").strip()

        self.log_training_data(
            source_type='email',
            source_ref=email['email_id'],
            source_text=f"{email['subject']} | {email['snippet'][:100] if email['snippet'] else 'No preview'}",
            ai_suggestion=email['category'],
            ai_reasoning='Auto-applied by smart_email_system',
            ai_confidence=0.85,
            human_correction=email['category'],  # Same as AI
            correction_reason=f"CORRECT: {reason}" if reason else "CORRECT",
            model_used='gpt-4o'
        )

        self.correct += 1
        print("✅ Logged as training example")

    def provide_correction(self, email):
        """AI was wrong - provide correction and context"""
        print(f"\n❌ AI categorized as: {email['category']}")
        print("What should it be?")

        correct_category = input("\nCorrect category: ").strip()
        if not correct_category:
            print("Skipping...")
            return

        reason = input("Why is this the correct category? ").strip()
        context = input("Additional context (what made this tricky?): ").strip()

        # Update the email
        self.cursor.execute("""
            UPDATE emails SET category = ? WHERE email_id = ?
        """, (correct_category, email['email_id']))

        # Log to training data
        self.log_training_data(
            source_type='email',
            source_ref=email['email_id'],
            source_text=f"{email['subject']} | {email['snippet'][:100] if email['snippet'] else 'No preview'}",
            ai_suggestion=email['category'],
            ai_reasoning='Auto-applied by smart_email_system',
            ai_confidence=0.85,
            human_correction=correct_category,
            correction_reason=f"CORRECTED: {reason}. Context: {context}" if context else f"CORRECTED: {reason}",
            model_used='gpt-4o'
        )

        self.conn.commit()
        self.corrected += 1
        print(f"\n✅ Corrected to '{correct_category}' and logged for learning")

    def add_context(self, email):
        """AI was correct but add learning context"""
        print(f"\n💡 Adding learning context for: {email['category']}")

        context = input("\nWhat context should AI learn from this? ").strip()
        if not context:
            print("Skipping...")
            return

        patterns = input("What patterns/signals indicate this category? ").strip()

        # Log to training data with context
        self.log_training_data(
            source_type='email',
            source_ref=email['email_id'],
            source_text=f"{email['subject']} | {email['snippet'][:100] if email['snippet'] else 'No preview'}",
            ai_suggestion=email['category'],
            ai_reasoning='Auto-applied by smart_email_system',
            ai_confidence=0.85,
            human_correction=email['category'],
            correction_reason=f"CONTEXT: {context}. Patterns: {patterns}",
            model_used='gpt-4o'
        )

        self.conn.commit()
        self.context_added += 1
        print("✅ Context added for learning")

    def log_training_data(self, **kwargs):
        """Log feedback to training_data table"""
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
        print("🧠 AI ACTIONS REVIEW - FEEDBACK LOOP")
        print("=" * 100)
        print("\nReview what AI did and teach it when it fucks up!\n")

        actions = self.get_recent_actions(limit=20)
        total = len(actions)

        if total == 0:
            print("No recent AI actions to review!")
            return

        print(f"Found {total} recent AI actions to review.\n")

        for action in actions:
            if not self.review_action(action):
                break
            self.reviewed += 1

        # Summary
        print("\n" + "=" * 100)
        print("📊 REVIEW SESSION SUMMARY")
        print("=" * 100)
        print(f"   Reviewed: {self.reviewed}")
        print(f"   ✅ Correct: {self.correct}")
        print(f"   ❌ Corrected: {self.corrected}")
        print(f"   💡 Context Added: {self.context_added}")
        print(f"\n   Training examples created: {self.correct + self.corrected + self.context_added}")
        print("=" * 100)

        # Show total training data
        self.cursor.execute("SELECT COUNT(*) FROM training_data")
        total_training = self.cursor.fetchone()[0]
        print(f"\n📚 Total training examples: {total_training}")

        if total_training >= 100:
            print("🎉 You have 100+ examples! Ready for rule generation and local model training!")
        else:
            print(f"   {100 - total_training} more examples until ready for advanced features")

    def close(self):
        self.conn.close()


def main():
    reviewer = AIActionsReviewer()
    try:
        reviewer.run_review_session()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    finally:
        reviewer.close()


if __name__ == "__main__":
    main()
