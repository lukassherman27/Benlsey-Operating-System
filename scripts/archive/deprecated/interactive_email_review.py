#!/usr/bin/env python3
"""
Interactive Email Review & Intelligence Builder

After automated processing, this tool helps you:
1. Review AI categorizations and provide feedback
2. Link emails to projects (suggests based on content)
3. Get database improvement suggestions
4. Identify patterns and optimization opportunities
5. Build training data for smarter AI

This is your chance to TEACH the system about your business!
"""

import sqlite3
import re
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

class InteractiveEmailReview:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.reviewed_count = 0
        self.corrections_made = 0

    def find_project_suggestions(self, email_text: str) -> List[Dict]:
        """Suggest project links based on email content"""
        suggestions = []

        # Find BK-XXX codes
        project_codes = re.findall(r'BK-\d{3}', email_text, re.IGNORECASE)

        for code in set(project_codes):
            # Look up project details
            self.cursor.execute("""
                SELECT project_code, project_name, client_name, status
                FROM projects
                WHERE project_code = ?
            """, (code.upper(),))

            project = self.cursor.fetchone()
            if project:
                suggestions.append({
                    'code': project['project_code'],
                    'name': project['project_name'],
                    'client': project['client_name'],
                    'status': project['status'],
                    'confidence': 'high',
                    'reason': f'Found "{code}" in email'
                })

        # Also search by project/client name mentions
        self.cursor.execute("SELECT project_code, project_name, client_name FROM projects")
        for project in self.cursor.fetchall():
            if project['project_name'] and project['project_name'].lower() in email_text.lower():
                if not any(s['code'] == project['project_code'] for s in suggestions):
                    suggestions.append({
                        'code': project['project_code'],
                        'name': project['project_name'],
                        'client': project['client_name'],
                        'confidence': 'medium',
                        'reason': f'Project name "{project["project_name"]}" mentioned'
                    })

        return suggestions

    def get_emails_needing_review(self, limit=50):
        """Get emails that need human review"""
        self.cursor.execute("""
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.date,
                e.snippet,
                e.body_full,
                e.category,
                e.project_code
            FROM emails e
            WHERE e.category IS NULL
               OR e.category = 'general'
               OR e.project_code IS NULL
            ORDER BY e.date DESC
            LIMIT ?
        """, (limit,))

        return self.cursor.fetchall()

    def show_email_for_review(self, email):
        """Display email with AI suggestions"""
        print("\n" + "=" * 100)
        print(f"📧 Email #{email['email_id']}")
        print("=" * 100)
        print(f"From:    {email['sender_email']}")
        print(f"Date:    {email['date']}")
        print(f"Subject: {email['subject']}")
        print(f"\nSnippet: {email['snippet'][:200]}...")

        print(f"\n🤖 AI Categorization: {email['category'] or 'None'}")
        print(f"🔗 Linked Project:    {email['project_code'] or 'None'}")

        # Suggest project links
        full_text = f"{email['subject']} {email['snippet']}"
        suggestions = self.find_project_suggestions(full_text)

        if suggestions:
            print(f"\n💡 PROJECT LINK SUGGESTIONS:")
            for i, sug in enumerate(suggestions, 1):
                print(f"   {i}. {sug['code']} - {sug['name']} ({sug['client']})")
                print(f"      Confidence: {sug['confidence']} - {sug['reason']}")

        print("=" * 100)

    def review_workflow(self):
        """Main interactive review workflow"""
        print("\n" + "🧠 BENSLEY INTELLIGENCE BUILDER ".center(100, "="))
        print("\nThis tool helps you teach the system about your business.")
        print("Review AI suggestions and provide corrections.\n")

        emails = self.get_emails_needing_review()
        total = len(emails)

        print(f"Found {total} emails needing review.\n")

        for i, email in enumerate(emails, 1):
            self.show_email_for_review(email)

            print(f"\n[{i}/{total}] What would you like to do?")
            print("  c - Categorize email")
            print("  p - Link to project")
            print("  b - Both (category + project)")
            print("  v - View full email body")
            print("  s - Skip to next")
            print("  q - Quit and save progress")

            choice = input("\nChoice: ").strip().lower()

            if choice == 'q':
                break
            elif choice == 's':
                continue
            elif choice == 'v':
                print(f"\n--- Full Email Body ---\n{email['body_full']}\n")
                input("Press Enter to continue...")
                continue
            elif choice in ['c', 'b']:
                self.categorize_email(email)

            if choice in ['p', 'b']:
                self.link_to_project(email)

            self.reviewed_count += 1

        self.show_summary()

    def categorize_email(self, email):
        """Interactive categorization"""
        print("\nCategories:")
        categories = [
            "proposal", "rfi", "invoice", "contract",
            "project_update", "meeting", "schedule",
            "design", "financial", "general"
        ]

        for i, cat in enumerate(categories, 1):
            print(f"  {i}. {cat}")

        choice = input("\nSelect category (1-10): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(categories):
            category = categories[int(choice) - 1]

            self.cursor.execute("""
                UPDATE emails
                SET category = ?,
                    processed = 1,
                    last_modified = CURRENT_TIMESTAMP
                WHERE email_id = ?
            """, (category, email['email_id']))

            self.corrections_made += 1
            print(f"✅ Categorized as: {category}")

    def link_to_project(self, email):
        """Interactive project linking"""
        full_text = f"{email['subject']} {email['snippet']}"
        suggestions = self.find_project_suggestions(full_text)

        if suggestions:
            print("\nSuggested projects:")
            for i, sug in enumerate(suggestions, 1):
                print(f"  {i}. {sug['code']} - {sug['name']}")

            print("  0. Enter different project code")
            print("  s. Skip")

            choice = input("\nSelect project: ").strip()

            if choice == 's':
                return
            elif choice == '0':
                code = input("Enter project code (BK-XXX): ").strip().upper()
            elif choice.isdigit() and 1 <= int(choice) <= len(suggestions):
                code = suggestions[int(choice) - 1]['code']
            else:
                return

            self.cursor.execute("""
                UPDATE emails
                SET project_code = ?,
                    last_modified = CURRENT_TIMESTAMP
                WHERE email_id = ?
            """, (code, email['email_id']))

            self.corrections_made += 1
            print(f"✅ Linked to project: {code}")

    def show_summary(self):
        """Show review session summary"""
        self.conn.commit()

        print("\n" + "=" * 100)
        print("📊 REVIEW SESSION SUMMARY")
        print("=" * 100)
        print(f"Emails reviewed:    {self.reviewed_count}")
        print(f"Corrections made:   {self.corrections_made}")
        print(f"\n✅ All changes saved to database")
        print("=" * 100)

        # Show database improvement suggestions
        self.show_improvement_suggestions()

    def show_improvement_suggestions(self):
        """Analyze patterns and suggest database improvements"""
        print("\n💡 DATABASE IMPROVEMENT SUGGESTIONS:")
        print("=" * 100)

        # Check for emails missing categories
        self.cursor.execute("SELECT COUNT(*) FROM emails WHERE category IS NULL")
        uncategorized = self.cursor.fetchone()[0]
        if uncategorized > 0:
            print(f"⚠️  {uncategorized} emails still need categorization")
            print(f"   → Run this tool again to continue reviewing")

        # Check for emails not linked to projects
        self.cursor.execute("""
            SELECT COUNT(*) FROM emails
            WHERE project_code IS NULL
            AND (subject LIKE '%BK-%' OR snippet LIKE '%BK-%')
        """)
        unlinked = self.cursor.fetchone()[0]
        if unlinked > 0:
            print(f"⚠️  {unlinked} emails mention project codes but aren't linked")
            print(f"   → Run smart_email_matcher.py to auto-link")

        # Check for missing indexes
        print(f"\n✅ Suggested database optimizations:")
        print(f"   → Add index on emails.category for faster filtering")
        print(f"   → Add index on emails.project_code for faster project queries")
        print(f"   → Add full-text search index on email bodies")

        print("=" * 100)

    def close(self):
        self.conn.close()


def main():
    reviewer = InteractiveEmailReview()
    try:
        reviewer.review_workflow()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    finally:
        reviewer.close()


if __name__ == "__main__":
    main()
