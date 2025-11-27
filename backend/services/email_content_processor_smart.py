#!/usr/bin/env python3
"""
Email Content Processor - SMART VERSION

Uses EITHER Claude OR OpenAI - whichever you have credits for!
Set in .env:
  ANTHROPIC_API_KEY=xxx  (for Claude)
  OR
  OPENAI_API_KEY=xxx     (for ChatGPT)

Will auto-detect and use whichever is available.
"""

import sqlite3
import json
import re
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Try both AI providers
ANTHROPIC_AVAILABLE = False
OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    pass

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    pass


class SmartEmailProcessor:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Determine which AI to use
        self.ai_provider = None
        self.client = None

        # Try Claude first
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key and ANTHROPIC_AVAILABLE:
            try:
                self.client = anthropic.Anthropic(api_key=anthropic_key)
                self.ai_provider = 'claude'
                self.ai_enabled = True
                print("✓ Using Claude (Anthropic)")
            except Exception as e:
                print(f"⚠️  Claude failed: {e}")

        # Fall back to OpenAI if Claude not available
        if not self.ai_provider:
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key and OPENAI_AVAILABLE:
                try:
                    self.client = OpenAI(api_key=openai_key)
                    self.ai_provider = 'openai'
                    self.ai_enabled = True
                    print("✓ Using OpenAI (ChatGPT)")
                except Exception as e:
                    print(f"⚠️  OpenAI failed: {e}")

        # No AI available
        if not self.ai_provider:
            self.ai_enabled = False
            print("⚠️  No AI available - add ANTHROPIC_API_KEY or OPENAI_API_KEY to .env")

        # Stats
        self.stats = {
            'processed': 0,
            'cleaned': 0,
            'categorized': 0,
            'entities_extracted': 0,
            'summaries_generated': 0,
            'training_saved': 0,
            'errors': 0
        }

        # Run migration
        self.run_migration()

    def run_migration(self):
        """Run brain intelligence migration"""
        migration_file = Path(__file__).parent.parent.parent / "database/migrations/005_brain_intelligence.sql"
        if migration_file.exists():
            print("Running brain intelligence migration...")
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
                self.conn.executescript(migration_sql)
                self.conn.commit()
            print("✓ Migration complete")

    def ai_call(self, prompt, max_tokens=100, temperature=0.3):
        """Universal AI call - works with both Claude and OpenAI"""
        if not self.ai_enabled:
            return None

        try:
            if self.ai_provider == 'claude':
                response = self.client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()

            elif self.ai_provider == 'openai':
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"  ⚠️  AI call failed: {e}")
            return None

    def detect_signature(self, body):
        """Detect where signature starts"""
        sig_markers = [
            r'\n\s*--+\s*\n', r'\n\s*Sent from', r'\n\s*Best regards?\s*,?\s*\n',
            r'\n\s*Sincerely\s*,?\s*\n', r'\n\s*Thanks?\s*,?\s*\n',
            r'\nBill Bensley\n', r'\nBrian.*Sherman\n', r'\n.*@bensley\.com\n'
        ]

        sig_start = len(body)
        for pattern in sig_markers:
            match = re.search(pattern, body, re.IGNORECASE)
            if match and match.start() < sig_start:
                sig_start = match.start()

        return sig_start

    def clean_email_body(self, body):
        """Remove signature and junk from email body"""
        if not body:
            return "", ""

        sig_start = self.detect_signature(body)
        clean_body = body[:sig_start].strip()
        quoted_text = body[sig_start:].strip()

        # Remove excessive whitespace
        clean_body = re.sub(r'\n\s*\n\s*\n+', '\n\n', clean_body)

        return clean_body, quoted_text

    def get_proposal_context(self, email_id):
        """Get proposal context for this email"""
        self.cursor.execute("""
            SELECT
                p.proposal_id, p.project_code, p.project_title,
                p.status, p.is_active_project
            FROM email_proposal_links epl
            JOIN proposals p ON epl.proposal_id = p.proposal_id
            WHERE epl.email_id = ?
            LIMIT 1
        """, (email_id,))

        row = self.cursor.fetchone()
        return dict(row) if row else None

    def categorize_email_ai(self, subject, body, email_id=None):
        """Categorize email using AI"""
        if not self.ai_enabled:
            return "general", 0.5

        proposal_context = self.get_proposal_context(email_id) if email_id else None

        context = ""
        if proposal_context:
            status = "ACTIVE PROJECT" if proposal_context.get('is_active_project', 0) else "PROPOSAL"
            context = f"""
Project: {proposal_context.get('project_title', 'Unknown')}
Code: {proposal_context.get('project_code', 'N/A')}
Status: {status}
"""

        prompt = f"""Categorize this Bensley Design Studios email into ONE category:
{context}
Categories: contract, invoice, design, rfi, schedule, meeting, general

CRITICAL RULES:
1. If PROPOSAL (not active project): Almost ALWAYS use "general"
2. If ACTIVE PROJECT: Can use design/rfi/schedule
3. When in doubt → "general"

Subject: {subject}
Body: {body[:500]}

Respond with ONLY the category name (one word).
"""

        try:
            category = self.ai_call(prompt, max_tokens=10, temperature=0.3)

            if not category:
                return "general", 0.5

            category = category.lower()

            # Validate
            valid_categories = ['contract', 'invoice', 'design', 'rfi', 'schedule', 'meeting', 'general']
            if category not in valid_categories:
                category = 'general'

            # Force proposals to use general for design/rfi/schedule
            if proposal_context and not proposal_context.get('is_active_project', 0):
                if category in ['design', 'rfi', 'schedule']:
                    category = 'general'

            confidence = 0.9 if self.ai_provider == 'claude' else 0.8
            return category, confidence

        except Exception as e:
            print(f"  ⚠️  Categorization failed: {e}")
            return "general", 0.5

    def extract_entities_ai(self, subject, body):
        """Extract key entities using AI"""
        if not self.ai_enabled:
            return {'amounts': [], 'dates': [], 'people': [], 'decisions': []}

        prompt = f"""Extract key entities from this email:

Subject: {subject}
Body: {body[:800]}

Extract:
1. Money amounts (fees, costs)
2. Important dates
3. People mentioned
4. Decisions made

Return as JSON: {{"amounts": [], "dates": [], "people": [], "decisions": []}}
"""

        try:
            response = self.ai_call(prompt, max_tokens=300, temperature=0.2)

            if not response:
                return {'amounts': [], 'dates': [], 'people': [], 'decisions': []}

            # Parse JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(response)

        except Exception as e:
            print(f"  ⚠️  Entity extraction failed: {e}")
            return {'amounts': [], 'dates': [], 'people': [], 'decisions': []}

    def score_importance_ai(self, subject, body, category):
        """Score importance using AI"""
        if not self.ai_enabled:
            return 0.5

        prompt = f"""Rate importance of this email (0.0 to 1.0):

Category: {category}
Subject: {subject}
Body: {body[:400]}

High (0.8-1.0): Contracts, large fees, critical deadlines, decisions
Medium (0.5-0.7): Updates, meetings, reviews
Low (0.0-0.4): FYI, thank you

Respond with ONLY a number between 0.0 and 1.0
"""

        try:
            response = self.ai_call(prompt, max_tokens=5, temperature=0.2)

            if not response:
                return 0.5

            score = float(response)
            return max(0.0, min(1.0, score))

        except Exception as e:
            print(f"  ⚠️  Scoring failed: {e}")
            return 0.5

    def generate_summary_ai(self, subject, body):
        """Generate concise summary using AI"""
        if not self.ai_enabled:
            return None

        prompt = f"""Summarize this email in ONE sentence (max 100 chars):

Subject: {subject}
Body: {body[:600]}

Be specific and concise.
"""

        try:
            summary = self.ai_call(prompt, max_tokens=50, temperature=0.3)

            if summary and len(summary) > 120:
                summary = summary[:117] + "..."

            return summary

        except Exception as e:
            print(f"  ⚠️  Summary failed: {e}")
            return None

    def process_email(self, email_id):
        """Process a single email"""
        # Get email
        self.cursor.execute("""
            SELECT email_id, subject, body_full, sender_email
            FROM emails
            WHERE email_id = ?
        """, (email_id,))

        email = self.cursor.fetchone()
        if not email:
            return False

        subject = email['subject'] or ""
        body = email['body_full'] or ""

        # Clean
        clean_body, quoted_text = self.clean_email_body(body)
        self.stats['cleaned'] += 1

        # Categorize
        category, conf = self.categorize_email_ai(subject, clean_body, email_id)
        self.stats['categorized'] += 1

        # Extract entities
        entities = self.extract_entities_ai(subject, clean_body)
        self.stats['entities_extracted'] += 1

        # Score importance
        importance = self.score_importance_ai(subject, clean_body, category)

        # Generate summary
        summary = self.generate_summary_ai(subject, clean_body)
        if summary:
            self.stats['summaries_generated'] += 1

        # Save to database
        try:
            model_name = "claude-sonnet-4-5" if self.ai_provider == 'claude' else "gpt-3.5-turbo"

            self.cursor.execute("""
                INSERT OR REPLACE INTO email_content
                (email_id, clean_body, quoted_text, category, key_points, entities,
                 sentiment, importance_score, ai_summary, processing_model, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email_id, clean_body, quoted_text, category, json.dumps([]),
                json.dumps(entities), "neutral", importance, summary,
                model_name, datetime.now().isoformat()
            ))

            self.conn.commit()
            self.stats['processed'] += 1
            return True

        except Exception as e:
            print(f"  ⚠️  Error saving email {email_id}: {e}")
            self.stats['errors'] += 1
            return False

    def process_all_emails(self):
        """Process all unprocessed emails"""
        self.cursor.execute("""
            SELECT e.email_id
            FROM emails e
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE ec.email_id IS NULL
            AND e.body_full IS NOT NULL
            ORDER BY e.date DESC
        """)

        email_ids = [row['email_id'] for row in self.cursor.fetchall()]

        if not email_ids:
            print("\n✓ No emails to process (all done)")
            return

        print(f"\nProcessing {len(email_ids)} emails...")

        for i, email_id in enumerate(email_ids, 1):
            if i % 5 == 0:
                print(f"  [{i}/{len(email_ids)}] Processed...")

            self.process_email(email_id)

        self.show_summary()

    def show_summary(self):
        """Show processing summary"""
        print("\n" + "="*80)
        print("✅ PROCESSING COMPLETE")
        print("="*80)

        provider_name = "Claude" if self.ai_provider == 'claude' else "OpenAI"
        print(f"\nAI Provider: {provider_name}")
        print(f"\nSummary:")
        print(f"  Emails processed:      {self.stats['processed']}")
        print(f"  ✓ Cleaned:             {self.stats['cleaned']}")
        print(f"  ✓ Categorized:         {self.stats['categorized']}")
        print(f"  ✓ Entities extracted:  {self.stats['entities_extracted']}")
        print(f"  ✓ Summaries generated: {self.stats['summaries_generated']}")
        print(f"  ⚠ Errors:              {self.stats['errors']}")

        # Show category breakdown
        self.cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM email_content
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
        """)

        print("\n📊 Email Categories:")
        for row in self.cursor.fetchall():
            print(f"   {row['category']:<15} {row['count']:>4} emails")

        print("="*80)

    def __del__(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 email_content_processor_smart.py <database_path>")
        sys.exit(1)

    db_path = sys.argv[1]

    print("="*80)
    print("🧠 BENSLEY BRAIN - SMART EMAIL PROCESSOR")
    print("="*80)
    print(f"Database: {db_path}")

    processor = SmartEmailProcessor(db_path)

    if processor.ai_enabled:
        print("\nStarting email processing...")
        processor.process_all_emails()
    else:
        print("\n⚠️  No AI enabled. Add to .env:")
        print("   ANTHROPIC_API_KEY=xxx  (for Claude)")
        print("   OR")
        print("   OPENAI_API_KEY=xxx     (for ChatGPT)")
