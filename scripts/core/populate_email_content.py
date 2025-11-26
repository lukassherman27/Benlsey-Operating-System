#!/usr/bin/env python3
"""
Email Content Populator - Fills email_content table with rich AI analysis

RLHF-Style Workflow:
1. Process batch of 100 emails
2. Review with user
3. Refine prompts based on feedback
4. Continue with remaining batches

Usage:
    python3 populate_email_content.py --batch-size 100 --review
    python3 populate_email_content.py --batch-size 100 --continue
"""
import sqlite3
import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Database path - use environment variable or default
DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')

class EmailContentPopulator:
    def __init__(self, review_mode: bool = False):
        self.db_path = DB_PATH
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.review_mode = review_mode
        self.api_calls = 0
        self.estimated_cost = 0.0
        self.processed = 0
        self.errors = 0
        self.feedback_log = []  # Store for RLHF review

    def get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_emails_needing_content(self, limit: int = 100) -> List[Dict]:
        """
        Get emails that don't have email_content records yet.
        Prioritize emails WITH body_full content.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT e.email_id, e.subject, e.sender_email, e.recipient_emails,
                   e.body_full, e.date, e.has_attachments, e.folder,
                   e.stage, e.category
            FROM emails e
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE ec.content_id IS NULL
              AND e.body_full IS NOT NULL
              AND LENGTH(e.body_full) > 50
            ORDER BY e.date DESC
            LIMIT ?
        """, (limit,))

        emails = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return emails

    def analyze_email_content(self, email: Dict) -> Dict:
        """
        Rich AI analysis of email content.
        Returns structured data for email_content table.
        """
        body = email.get('body_full', '')[:3000]  # Limit for API
        subject = email.get('subject', '')
        sender = email.get('sender_email', '')

        prompt = f"""Analyze this business email and extract structured information.

EMAIL:
From: {sender}
Subject: {subject}
Body:
{body}

ANALYSIS REQUIRED (respond in JSON):
{{
    "clean_body": "Email body with signatures/banners removed (keep substance)",
    "quoted_text": "Any quoted/forwarded text (empty string if none)",
    "category": "contract|design|financial|meeting|rfi|administrative|general",
    "subcategory": "More specific type (e.g., 'fee_discussion', 'schedule_update', 'nda_request')",
    "key_points": ["bullet point 1", "bullet point 2", ...],
    "entities": {{
        "amounts": ["$X", "THB Y", ...],
        "dates": ["Dec 15", "next Friday", ...],
        "people": ["John Smith", "Ms. Lee", ...],
        "companies": ["Marriott", "AECOM", ...],
        "projects": ["Wynn Marjan", "Art Deco", ...]
    }},
    "sentiment": "positive|neutral|concerned|urgent|frustrated",
    "importance_score": 0.0-1.0,
    "ai_summary": "One sentence summary of the email's main point",
    "urgency_level": "low|medium|high|critical",
    "action_required": true/false,
    "action_items": ["specific action needed", ...]
}}

GUIDELINES:
- importance_score: 0.9+ for contracts/deadlines, 0.7+ for design/financial, 0.3-0.5 for general
- urgency: "critical" only if explicit deadline within days
- action_required: true if someone needs to DO something
- Be concise in key_points (max 5 bullets)
- clean_body: Remove "Sent from iPhone", signatures, banners, but keep all business content

Return ONLY valid JSON, no markdown."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1500
            )

            result = response.choices[0].message.content.strip()
            self.api_calls += 1
            self.estimated_cost += 0.02  # Approximate cost per call

            # Parse JSON response
            # Handle potential markdown code blocks
            if result.startswith('```'):
                result = result.split('```')[1]
                if result.startswith('json'):
                    result = result[4:]

            analysis = json.loads(result)
            return analysis

        except json.JSONDecodeError as e:
            print(f"  JSON parse error: {e}")
            return self._default_analysis()
        except Exception as e:
            print(f"  API error: {e}")
            return self._default_analysis()

    def _default_analysis(self) -> Dict:
        """Return default analysis when AI fails"""
        return {
            "clean_body": "",
            "quoted_text": "",
            "category": "general",
            "subcategory": "",
            "key_points": [],
            "entities": {"amounts": [], "dates": [], "people": [], "companies": [], "projects": []},
            "sentiment": "neutral",
            "importance_score": 0.5,
            "ai_summary": "Analysis failed",
            "urgency_level": "low",
            "action_required": False,
            "action_items": []
        }

    def store_email_content(self, email_id: int, analysis: Dict) -> bool:
        """Store analysis results in email_content table"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO email_content (
                    email_id, clean_body, quoted_text, category, subcategory,
                    key_points, entities, sentiment, importance_score,
                    ai_summary, urgency_level, action_required, processing_model
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email_id,
                analysis.get('clean_body', ''),
                analysis.get('quoted_text', ''),
                analysis.get('category', 'general'),
                analysis.get('subcategory', ''),
                json.dumps(analysis.get('key_points', [])),
                json.dumps(analysis.get('entities', {})),
                analysis.get('sentiment', 'neutral'),
                analysis.get('importance_score', 0.5),
                analysis.get('ai_summary', ''),
                analysis.get('urgency_level', 'low'),
                1 if analysis.get('action_required', False) else 0,
                'gpt-4o-mini'
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"  DB error: {e}")
            conn.close()
            return False

    def process_batch(self, emails: List[Dict]) -> Dict:
        """Process a batch of emails"""
        stats = {
            'processed': 0,
            'errors': 0,
            'high_importance': 0,
            'action_required': 0
        }

        for i, email in enumerate(emails, 1):
            print(f"\n[{i}/{len(emails)}] Email {email['email_id']}: {email['subject'][:50]}...")

            # Analyze
            analysis = self.analyze_email_content(email)

            # Store
            if self.store_email_content(email['email_id'], analysis):
                stats['processed'] += 1
                self.processed += 1

                # Track interesting stats
                if analysis.get('importance_score', 0) >= 0.8:
                    stats['high_importance'] += 1
                if analysis.get('action_required'):
                    stats['action_required'] += 1

                # In review mode, log for feedback
                if self.review_mode:
                    self.feedback_log.append({
                        'email_id': email['email_id'],
                        'subject': email['subject'],
                        'sender': email['sender_email'],
                        'analysis': analysis
                    })

                print(f"  Category: {analysis.get('category')}/{analysis.get('subcategory')}")
                print(f"  Importance: {analysis.get('importance_score'):.2f} | Urgency: {analysis.get('urgency_level')}")
                print(f"  Summary: {analysis.get('ai_summary', '')[:80]}...")
            else:
                stats['errors'] += 1
                self.errors += 1

            # Rate limiting
            time.sleep(0.5)

        return stats

    def save_review_file(self):
        """Save processed emails for human review"""
        if not self.feedback_log:
            return

        filename = f"email_content_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(self.feedback_log, f, indent=2)

        print(f"\n📝 Review file saved: {filename}")

        # Also create human-readable summary
        summary_file = filename.replace('.json', '_summary.txt')
        with open(summary_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("EMAIL CONTENT ANALYSIS - REVIEW SUMMARY\n")
            f.write("=" * 80 + "\n\n")

            for item in self.feedback_log:
                f.write(f"Email ID: {item['email_id']}\n")
                f.write(f"Subject: {item['subject']}\n")
                f.write(f"From: {item['sender']}\n")
                f.write(f"Category: {item['analysis'].get('category')}/{item['analysis'].get('subcategory')}\n")
                f.write(f"Importance: {item['analysis'].get('importance_score'):.2f}\n")
                f.write(f"Urgency: {item['analysis'].get('urgency_level')}\n")
                f.write(f"Action Required: {'YES' if item['analysis'].get('action_required') else 'No'}\n")
                f.write(f"Summary: {item['analysis'].get('ai_summary')}\n")
                f.write(f"Key Points:\n")
                for point in item['analysis'].get('key_points', []):
                    f.write(f"  - {point}\n")
                f.write("\n" + "-" * 80 + "\n\n")

        print(f"📋 Human-readable summary: {summary_file}")

    def show_statistics(self):
        """Show current email_content statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM email_content")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT category, COUNT(*) FROM email_content GROUP BY category ORDER BY COUNT(*) DESC")
        categories = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM email_content WHERE action_required = 1")
        action_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM email_content WHERE importance_score >= 0.8")
        high_importance = cursor.fetchone()[0]

        conn.close()

        print("\n📊 EMAIL_CONTENT TABLE STATISTICS")
        print("=" * 50)
        print(f"Total records: {total}")
        print(f"Action required: {action_count}")
        print(f"High importance (0.8+): {high_importance}")
        print("\nBy category:")
        for cat, count in categories:
            print(f"  {cat}: {count}")


def main():
    parser = argparse.ArgumentParser(description='Populate email_content table')
    parser.add_argument('--batch-size', type=int, default=100, help='Number of emails to process')
    parser.add_argument('--review', action='store_true', help='Enable review mode (saves output for feedback)')
    parser.add_argument('--stats', action='store_true', help='Show current statistics only')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without doing it')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()

    print("=" * 80)
    print("EMAIL CONTENT POPULATOR - RLHF Style")
    print("=" * 80)
    print(f"Database: {DB_PATH}")

    populator = EmailContentPopulator(review_mode=args.review)

    if args.stats:
        populator.show_statistics()
        return

    # Get emails needing processing
    emails = populator.get_emails_needing_content(args.batch_size)
    print(f"\n📧 Found {len(emails)} emails needing content analysis")

    if not emails:
        print("No emails to process!")
        populator.show_statistics()
        return

    if args.dry_run:
        print("\n🔍 DRY RUN - Would process these emails:")
        for i, email in enumerate(emails[:10], 1):
            print(f"  {i}. [{email['email_id']}] {email['subject'][:60]}")
        if len(emails) > 10:
            print(f"  ... and {len(emails) - 10} more")
        return

    # Estimate cost
    estimated_cost = len(emails) * 0.02
    print(f"💰 Estimated cost: ${estimated_cost:.2f}")

    if args.review:
        print("\n📝 REVIEW MODE: Results will be saved for feedback")

    # Confirm
    if not args.yes:
        confirm = input("\nProceed? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Cancelled")
            return

    # Process
    print("\n🚀 Starting processing...")
    start_time = time.time()

    stats = populator.process_batch(emails)

    elapsed = time.time() - start_time

    # Summary
    print("\n" + "=" * 80)
    print("✅ BATCH COMPLETE")
    print("=" * 80)
    print(f"Processed: {stats['processed']}")
    print(f"Errors: {stats['errors']}")
    print(f"High importance emails: {stats['high_importance']}")
    print(f"Action required: {stats['action_required']}")
    print(f"Time: {elapsed/60:.1f} minutes")
    print(f"Cost: ${populator.estimated_cost:.2f}")

    # Save review file if in review mode
    if args.review:
        populator.save_review_file()
        print("\n👉 NEXT STEP: Review the output files, provide feedback, then run:")
        print("   python3 populate_email_content.py --batch-size 100")

    # Show updated statistics
    populator.show_statistics()


if __name__ == '__main__':
    main()
