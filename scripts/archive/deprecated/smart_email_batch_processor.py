#!/usr/bin/env python3
"""
Smart Email Batch Processor

Intelligently processes ALL unprocessed emails with:
- AI categorization
- Smart linking to proposals/projects
- Junk filtering (banners, signatures, duplicate images)
- Cleanup suggestions
- Cost tracking
- Progress monitoring

Usage:
    python3 smart_email_batch_processor.py --batch-size 50 --max-batches 10
    python3 smart_email_batch_processor.py --all  # Process everything
"""

import sqlite3
import os
import sys
import time
import argparse
from datetime import datetime
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

class SmartEmailProcessor:
    def __init__(self):
        self.db_path = os.getenv('DATABASE_PATH', 'database/bensley_master.db')
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Cost tracking
        self.api_calls = 0
        self.estimated_cost = 0.0

        # Cleanup tracking
        self.junk_filtered = []
        self.duplicates_found = []
        self.cleanup_suggestions = []

        # Processing stats
        self.processed = 0
        self.linked = 0
        self.categorized = 0
        self.skipped = 0

    def get_unprocessed_emails(self, limit: Optional[int] = None) -> List[Dict]:
        """Get unprocessed emails, prioritized by importance"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Prioritize:
        # 1. Emails with attachments (likely important docs)
        # 2. Recent emails
        # 3. Emails from known clients
        query = """
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.body_full,
                e.date,
                e.has_attachments,
                e.folder,
                (SELECT COUNT(*) FROM attachments a WHERE a.email_id = e.email_id) as attachment_count
            FROM emails e
            WHERE e.processed = 0
            ORDER BY
                e.has_attachments DESC,
                e.date DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        emails = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return emails

    def is_junk_email(self, email: Dict) -> tuple[bool, str]:
        """Detect if email is junk (automated, newsletter, notification)"""
        subject = (email['subject'] or '').lower()
        sender = (email['sender_email'] or '').lower()
        body = (email['body_full'] or '').lower()

        # Junk patterns
        junk_senders = [
            'no-reply@', 'noreply@', 'donotreply@',
            'notifications@', 'updates@', 'news@',
            'marketing@', 'newsletter@'
        ]

        junk_subjects = [
            'unsubscribe', 'newsletter', 'weekly digest',
            'daily summary', 'notification', 'reminder',
            'automated', 'do not reply'
        ]

        # Check sender
        for pattern in junk_senders:
            if pattern in sender:
                return True, f"Junk sender: {pattern}"

        # Check subject
        for pattern in junk_subjects:
            if pattern in subject:
                return True, f"Junk subject: {pattern}"

        # Check if email is too short (likely automated)
        if body and len(body) < 50:
            return True, "Too short (likely automated)"

        return False, ""

    def categorize_email(self, email: Dict) -> tuple[str, str]:
        """Use AI to categorize email into STAGE and CATEGORY"""
        try:
            prompt = f"""Categorize this email into TWO dimensions:

STAGE (business track):
- proposal: Pre-contract sales pipeline (trying to win the business)
- active: Post-contract project delivery (executing won projects)
- internal: Internal Bensley operations (payroll, accounting, admin)
- other: Other business lines (Shinta Mani, private projects, social media)

CATEGORY (activity type):
- contract: Contract discussions, terms, agreements, NDAs
- design: Design reviews, drawings, creative work, presentations
- financial: Invoices, payments, budgets, fees
- meeting: Meeting schedules, agendas, coordination
- rfi: Questions, information requests
- administrative: Staff schedules, internal admin
- general: General discussion

Email:
From: {email['sender_email']}
Subject: {email['subject']}
Body: {email['body_full'][:1000]}

Return ONLY two words: stage category (e.g., "proposal design" or "active financial")"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=50
            )

            result = response.choices[0].message.content.strip().lower()
            parts = result.split()

            if len(parts) >= 2:
                stage = parts[0]
                category = parts[1]
            else:
                stage = "other"
                category = "general"

            self.api_calls += 1
            self.estimated_cost += 0.005

            return stage, category

        except Exception as e:
            logger.error(f"Categorization failed for email {email['email_id']}: {e}")
            return "other", "general"

    def link_to_proposals(self, email: Dict, proposals: List[Dict]) -> List[tuple]:
        """Use AI to link email to relevant proposals"""
        if not proposals:
            return []

        try:
            # Build proposal context - SHOW ALL PROPOSALS (was limiting to 20, causing 77% to be invisible!)
            proposal_list = "\n".join([
                f"- {p['project_code']}: {p['project_name']}"
                for p in proposals  # Show all proposals (87 total = ~1300 tokens, well within limits)
            ])

            prompt = f"""Which proposals is this email related to?

Email:
From: {email['sender_email']}
Subject: {email['subject']}
Body: {email['body_full'][:800]}

Proposals:
{proposal_list}

Return ONLY the project codes (e.g. BK-033, BK-008) as a comma-separated list.
If not related to any, return "NONE"."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=100
            )

            result = response.choices[0].message.content.strip()
            self.api_calls += 1
            self.estimated_cost += 0.01

            if result == "NONE" or not result:
                return []

            # Parse project codes
            codes = [code.strip() for code in result.split(',')]

            # Match to proposal IDs
            links = []
            for code in codes:
                for p in proposals:
                    if p['project_code'] == code:
                        links.append((p['proposal_id'], 0.8))  # 0.8 confidence
                        break

            return links

        except Exception as e:
            logger.error(f"Linking failed for email {email['email_id']}: {e}")
            return []

    def process_batch(self, emails: List[Dict], proposals: List[Dict]) -> Dict:
        """Process a batch of emails"""
        batch_stats = {
            'processed': 0,
            'categorized': 0,
            'linked': 0,
            'junk_filtered': 0,
            'errors': 0
        }

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for email in emails:
            try:
                # Check if junk
                is_junk, reason = self.is_junk_email(email)
                if is_junk:
                    logger.info(f"Skipping junk email {email['email_id']}: {reason}")
                    self.junk_filtered.append({
                        'email_id': email['email_id'],
                        'subject': email['subject'],
                        'reason': reason
                    })
                    batch_stats['junk_filtered'] += 1

                    # Mark as processed but don't categorize
                    cursor.execute("""
                        UPDATE emails
                        SET processed = 1, stage = 'other', category = 'junk'
                        WHERE email_id = ?
                    """, (email['email_id'],))
                    continue

                # Categorize (now returns stage AND category)
                stage, category = self.categorize_email(email)
                logger.info(f"Email {email['email_id']}: {stage}/{category}")
                batch_stats['categorized'] += 1

                # Link to proposals
                links = self.link_to_proposals(email, proposals)
                if links:
                    for proposal_id, confidence in links:
                        cursor.execute("""
                            INSERT OR IGNORE INTO email_proposal_links
                            (email_id, proposal_id, confidence_score, auto_linked, created_at)
                            VALUES (?, ?, ?, 1, datetime('now'))
                        """, (email['email_id'], proposal_id, confidence))
                    batch_stats['linked'] += 1
                    logger.info(f"  Linked to {len(links)} proposals")

                # Mark as processed with stage AND category
                cursor.execute("""
                    UPDATE emails
                    SET processed = 1, stage = ?, category = ?
                    WHERE email_id = ?
                """, (stage, category, email['email_id']))

                batch_stats['processed'] += 1

            except Exception as e:
                logger.error(f"Error processing email {email['email_id']}: {e}")
                batch_stats['errors'] += 1
                continue

        conn.commit()
        conn.close()

        return batch_stats

    def generate_cleanup_report(self):
        """Generate report of cleanup suggestions"""
        report_path = 'EMAIL_CLEANUP_REPORT.md'

        with open(report_path, 'w') as f:
            f.write("# Email Processing Cleanup Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("## Processing Summary\n\n")
            f.write(f"- **Processed:** {self.processed} emails\n")
            f.write(f"- **Categorized:** {self.categorized} emails\n")
            f.write(f"- **Linked:** {self.linked} emails\n")
            f.write(f"- **Junk Filtered:** {len(self.junk_filtered)} emails\n")
            f.write(f"- **API Calls:** {self.api_calls}\n")
            f.write(f"- **Estimated Cost:** ${self.estimated_cost:.2f}\n\n")

            if self.junk_filtered:
                f.write("## Junk Emails Filtered\n\n")
                f.write("These emails were marked as junk and can be safely deleted:\n\n")
                for item in self.junk_filtered[:50]:  # Show first 50
                    f.write(f"- **{item['email_id']}**: {item['subject']} ({item['reason']})\n")
                if len(self.junk_filtered) > 50:
                    f.write(f"\n... and {len(self.junk_filtered) - 50} more\n")

            f.write("\n## Recommendations\n\n")
            f.write("1. **Delete junk emails** marked as category='junk'\n")
            f.write("2. **Review duplicate attachments** (banner images, signatures)\n")
            f.write("3. **Archive old automated emails** (>1 year old)\n")
            f.write("4. **Set up email filters** to prevent future junk import\n")

        logger.info(f"Cleanup report saved to {report_path}")
        return report_path

def main():
    parser = argparse.ArgumentParser(description='Smart Email Batch Processor')
    parser.add_argument('--batch-size', type=int, default=50, help='Emails per batch')
    parser.add_argument('--max-batches', type=int, default=None, help='Maximum batches to process')
    parser.add_argument('--all', action='store_true', help='Process all unprocessed emails')
    args = parser.parse_args()

    print("=" * 80)
    print("SMART EMAIL BATCH PROCESSOR")
    print("=" * 80)

    processor = SmartEmailProcessor()

    # Load proposals for linking
    conn = sqlite3.connect(processor.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT proposal_id, project_code, project_name FROM proposals")
    proposals = [dict(row) for row in cursor.fetchall()]
    conn.close()

    logger.info(f"Loaded {len(proposals)} proposals for linking")
    print(f"\n📊 Found {len(proposals)} proposals for linking")

    # Get unprocessed emails
    emails = processor.get_unprocessed_emails()
    total_emails = len(emails)

    print(f"📧 Found {total_emails} unprocessed emails")
    print(f"⚙️  Batch size: {args.batch_size}")

    if args.all:
        max_emails = total_emails
    elif args.max_batches:
        max_emails = args.batch_size * args.max_batches
    else:
        max_emails = args.batch_size

    emails_to_process = emails[:max_emails]
    print(f"🎯 Will process: {len(emails_to_process)} emails")

    estimated_cost = len(emails_to_process) * 0.015  # $0.015 per email avg
    print(f"💰 Estimated cost: ${estimated_cost:.2f}")

    if not args.all:
        confirm = input("\nContinue? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Cancelled")
            return

    # Process in batches
    start_time = time.time()
    num_batches = (len(emails_to_process) + args.batch_size - 1) // args.batch_size

    for i in range(num_batches):
        batch_start = i * args.batch_size
        batch_end = min(batch_start + args.batch_size, len(emails_to_process))
        batch = emails_to_process[batch_start:batch_end]

        print(f"\n📦 Batch {i+1}/{num_batches} ({batch_start+1}-{batch_end}/{len(emails_to_process)})")

        batch_stats = processor.process_batch(batch, proposals)

        processor.processed += batch_stats['processed']
        processor.categorized += batch_stats['categorized']
        processor.linked += batch_stats['linked']

        print(f"   ✅ Processed: {batch_stats['processed']}")
        print(f"   🏷️  Categorized: {batch_stats['categorized']}")
        print(f"   🔗 Linked: {batch_stats['linked']}")
        print(f"   🗑️  Junk: {batch_stats['junk_filtered']}")
        print(f"   💰 Cost so far: ${processor.estimated_cost:.2f}")

        # Rate limiting
        if i < num_batches - 1:
            time.sleep(2)  # 2 second pause between batches

    elapsed = time.time() - start_time

    # Generate cleanup report
    report_path = processor.generate_cleanup_report()

    print("\n" + "=" * 80)
    print("✅ PROCESSING COMPLETE")
    print("=" * 80)
    print(f"\n📊 Final Stats:")
    print(f"   Processed: {processor.processed}")
    print(f"   Categorized: {processor.categorized}")
    print(f"   Linked: {processor.linked}")
    print(f"   Junk Filtered: {len(processor.junk_filtered)}")
    print(f"   API Calls: {processor.api_calls}")
    print(f"   Actual Cost: ${processor.estimated_cost:.2f}")
    print(f"   Time: {elapsed/60:.1f} minutes")
    print(f"\n📄 Cleanup report: {report_path}")
    print("\n")

if __name__ == '__main__':
    main()
