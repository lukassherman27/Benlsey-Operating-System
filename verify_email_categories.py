#!/usr/bin/env python3
"""
Manual Email Category Verification
Reviews AI categorizations and collects human feedback for training data
"""
import sqlite3
from pathlib import Path
import sys

class CategoryVerifier:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        self.stats = {
            'reviewed': 0,
            'correct': 0,
            'corrected': 0,
            'skipped': 0
        }

        self.categories = [
            'contract', 'invoice', 'design', 'rfi',
            'schedule', 'meeting', 'general'
        ]

    def get_unverified_emails(self, limit=None):
        """Get emails that haven't been human-verified yet"""
        query = """
            SELECT
                ec.content_id,
                ec.email_id,
                ec.category as ai_category,
                ec.ai_summary,
                ec.importance_score,
                e.subject,
                e.sender_email,
                e.date,
                e.body_preview,
                p.project_code,
                p.project_name,
                p.is_active_project
            FROM email_content ec
            JOIN emails e ON ec.email_id = e.email_id
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            JOIN proposals p ON epl.proposal_id = p.proposal_id
            LEFT JOIN training_data td ON (
                td.task_type = 'categorize_email'
                AND td.input_data LIKE '%' || e.subject || '%'
                AND td.human_verified = 1
            )
            WHERE td.data_id IS NULL
            ORDER BY ec.importance_score DESC, e.date DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        self.cursor.execute(query)
        return self.cursor.fetchall()

    def display_email(self, email):
        """Display email details for review"""
        print("\n" + "="*80)
        print(f"📧 EMAIL REVIEW")
        print("="*80)

        project_type = "🟢 ACTIVE PROJECT" if email['is_active_project'] else "🔵 PROPOSAL"
        print(f"\nProject: {email['project_code']} - {email['project_name'][:50]}")
        print(f"Status:  {project_type}")
        print(f"\nFrom:    {email['sender_email']}")
        print(f"Date:    {email['date']}")
        print(f"Subject: {email['subject']}")
        print(f"\nBody Preview:")
        print("-" * 80)
        print(email['body_preview'][:400])
        if len(email['body_preview']) > 400:
            print("... (truncated)")
        print("-" * 80)

        print(f"\n🤖 AI CATEGORIZATION:")
        print(f"   Category:   {email['ai_category']}")
        print(f"   Importance: {email['importance_score']*100:.0f}%")
        print(f"   Summary:    {email['ai_summary']}")

    def verify_category(self, email):
        """Get user verification of category"""
        print(f"\n📋 CATEGORY OPTIONS:")
        for i, cat in enumerate(self.categories, 1):
            marker = "✓" if cat == email['ai_category'] else " "
            print(f"  {i}. [{marker}] {cat}")

        print(f"\nAI chose: '{email['ai_category']}'")
        print("\nIs this correct?")
        print("  y = Yes, correct")
        print("  n = No, I'll enter the correct category")
        print("  1-7 = Select correct category number")
        print("  s = Skip this email")
        print("  q = Quit and save progress")

        while True:
            response = input("\nYour choice: ").strip().lower()

            if response == 'q':
                return 'quit', None

            if response == 's':
                self.stats['skipped'] += 1
                return 'skip', None

            if response == 'y':
                self.stats['correct'] += 1
                return 'correct', email['ai_category']

            if response == 'n':
                print("\nEnter correct category:")
                for i, cat in enumerate(self.categories, 1):
                    print(f"  {i}. {cat}")
                correct_cat = input("Category name or number: ").strip().lower()

                # Handle number input
                if correct_cat.isdigit():
                    idx = int(correct_cat) - 1
                    if 0 <= idx < len(self.categories):
                        correct_cat = self.categories[idx]
                    else:
                        print("Invalid number. Try again.")
                        continue

                if correct_cat in self.categories:
                    self.stats['corrected'] += 1
                    return 'corrected', correct_cat
                else:
                    print(f"Invalid category. Must be one of: {', '.join(self.categories)}")
                    continue

            # Handle direct number selection
            if response.isdigit():
                idx = int(response) - 1
                if 0 <= idx < len(self.categories):
                    selected = self.categories[idx]
                    if selected == email['ai_category']:
                        self.stats['correct'] += 1
                        return 'correct', email['ai_category']
                    else:
                        self.stats['corrected'] += 1
                        return 'corrected', selected
                else:
                    print("Invalid number. Try again.")
                    continue

            print("Invalid input. Try again.")

    def save_verification(self, email, human_category):
        """Save human verification to training_data"""
        # Find the corresponding training_data entry
        self.cursor.execute("""
            SELECT data_id FROM training_data
            WHERE task_type = 'categorize_email'
              AND input_data LIKE '%' || ? || '%'
            ORDER BY created_at DESC
            LIMIT 1
        """, (email['subject'],))

        result = self.cursor.fetchone()

        if result:
            # Update existing training data
            self.cursor.execute("""
                UPDATE training_data
                SET human_verified = 1,
                    feedback = ?
                WHERE data_id = ?
            """, (human_category, result['data_id']))
        else:
            # Create new training data entry
            self.cursor.execute("""
                INSERT INTO training_data
                (task_type, input_data, output_data, model_used,
                 confidence, human_verified, feedback)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                'categorize_email',
                f"Subject: {email['subject']}\nBody: {email['body_preview'][:500]}",
                email['ai_category'],
                'gpt-3.5-turbo',
                0.8,
                1,
                human_category
            ))

        self.conn.commit()
        self.stats['reviewed'] += 1

    def run_verification(self, limit=50):
        """Run interactive verification session"""
        print("="*80)
        print("📋 EMAIL CATEGORY VERIFICATION")
        print("="*80)
        print(f"Database: {self.db_path}")

        emails = self.get_unverified_emails(limit)

        if not emails:
            print("\n✓ All emails have been verified!")
            print("  Run email processor again to get new emails to verify.")
            return

        print(f"\nFound {len(emails)} unverified emails")
        print(f"Reviewing up to {limit} emails")
        print("\nPress Ctrl+C anytime to quit and save progress")

        try:
            for i, email in enumerate(emails, 1):
                print(f"\n\n{'='*80}")
                print(f"EMAIL {i}/{len(emails)}")
                print(f"{'='*80}")

                self.display_email(email)
                action, category = self.verify_category(email)

                if action == 'quit':
                    print("\n🛑 Quitting...")
                    break

                if action == 'skip':
                    print("⏭️  Skipped")
                    continue

                # Save verification
                self.save_verification(email, category)

                if action == 'correct':
                    print("✅ Confirmed correct!")
                elif action == 'corrected':
                    print(f"✏️  Corrected: {email['ai_category']} → {category}")

        except KeyboardInterrupt:
            print("\n\n🛑 Interrupted by user")

        self.print_summary()
        self.conn.close()

    def print_summary(self):
        """Print verification summary"""
        print("\n" + "="*80)
        print("📊 VERIFICATION SUMMARY")
        print("="*80)

        print(f"\nEmails reviewed:    {self.stats['reviewed']}")
        print(f"  ✅ Correct:       {self.stats['correct']}")
        print(f"  ✏️  Corrected:     {self.stats['corrected']}")
        print(f"  ⏭️  Skipped:       {self.stats['skipped']}")

        if self.stats['reviewed'] > 0:
            accuracy = self.stats['correct'] / self.stats['reviewed'] * 100
            print(f"\n🎯 AI Accuracy: {accuracy:.1f}%")

        # Show training data progress
        self.cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN human_verified = 1 THEN 1 ELSE 0 END) as verified
            FROM training_data
            WHERE task_type = 'categorize_email'
        """)

        row = self.cursor.fetchone()
        if row:
            print(f"\n📚 Training Data Progress:")
            print(f"   Total AI calls:      {row['total']}")
            print(f"   Human verified:      {row['verified']}")
            print(f"   Ready for training:  {row['verified']} / 1000 (need 1000+ for distillation)")

        print("\n" + "="*80)

def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else "database/bensley_master.db"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    if not Path(db_path).exists():
        print(f"✗ Database not found: {db_path}")
        return

    verifier = CategoryVerifier(db_path)
    verifier.run_verification(limit)

if __name__ == "__main__":
    main()
