#!/usr/bin/env python3
"""
Email Content Processor - Claude-Powered Version

Uses Claude (Anthropic) instead of OpenAI for:
- Better categorization
- Better entity extraction
- More reliable
- What you're already using!
"""

import sqlite3
import json
import re
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Try to import Anthropic
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  Anthropic not available - install with: pip install anthropic")


class EmailContentProcessorClaude:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Claude/Anthropic setup
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if self.anthropic_key and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=self.anthropic_key)
            self.ai_enabled = True
            print("✓ Claude (Anthropic) enabled")
        else:
            self.ai_enabled = False
            print("⚠️  Claude disabled (no API key or module)")

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

    def detect_signature(self, body):
        """Detect where signature starts"""
        # Common signature markers
        sig_markers = [
            r'\n\s*--+\s*\n',                    # -- separator
            r'\n\s*Sent from',                   # "Sent from my iPhone"
            r'\n\s*Best regards?\s*,?\s*\n',     # Best regards
            r'\n\s*Sincerely\s*,?\s*\n',        # Sincerely
            r'\n\s*Thanks?\s*,?\s*\n',          # Thanks
            r'\n\s*Cheers?\s*,?\s*\n',          # Cheers
            r'\nBill Bensley\n',                 # Bensley staff
            r'\nBrian.*Sherman\n',
            r'\n.*@bensley\.com\n',              # Email addresses
            r'\nwww\.bensley\.com',              # Website
        ]

        # Find earliest signature marker
        sig_start = len(body)
        for pattern in sig_markers:
            match = re.search(pattern, body, re.IGNORECASE)
            if match and match.start() < sig_start:
                sig_start = match.start()

        # Also remove common Bensley footer patterns
        bensley_footer = re.search(r'Bensley Design Studios?.*?Bangkok.*Thailand', body, re.IGNORECASE | re.DOTALL)
        if bensley_footer and bensley_footer.start() < sig_start:
            sig_start = bensley_footer.start()

        return sig_start

    def clean_email_body(self, body):
        """Remove signature and junk from email body"""
        if not body:
            return "", ""

        # Detect signature
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
                p.proposal_id,
                p.project_code,
                p.project_name,
                p.status,
                p.is_active_project
            FROM email_proposal_links epl
            JOIN proposals p ON epl.proposal_id = p.proposal_id
            WHERE epl.email_id = ?
            LIMIT 1
        """, (email_id,))

        row = self.cursor.fetchone()
        if row:
            return dict(row)
        return None

    def categorize_email_ai(self, subject, body, email_id=None):
        """Categorize email using Claude AI"""
        if not self.ai_enabled:
            return "general", 0.5

        # Get proposal context
        proposal_context = None
        if email_id:
            proposal_context = self.get_proposal_context(email_id)

        # Build context info
        context = ""
        if proposal_context:
            status = "ACTIVE PROJECT" if proposal_context.get('is_active_project', 0) else "PROPOSAL"
            context = f"""
Project: {proposal_context.get('project_name', 'Unknown')}
Code: {proposal_context.get('project_code', 'N/A')}
Status: {status} ({"post-contract" if proposal_context.get('is_active_project', 0) else "pre-contract"})
"""

        prompt = f"""Categorize this Bensley Design Studios email into ONE category:
{context}
Categories:

- contract: ONLY for formal legal documents (NDAs, MOUs, signed contracts, amendments)
  * Negotiating terms, discussing contract language
  * NOT for general proposal discussions

- invoice: ONLY for payment-related emails (invoices, receipts, bills)
  * Only applies to ACTIVE PROJECTS with signed contracts

- design: ONLY for ACTIVE PROJECTS with formal design work
  * Submitting drawings/plans for approval
  * Design reviews, revisions, technical feedback
  * NEVER use for proposals - exploratory design talk is "general"

- rfi: ONLY for ACTIVE PROJECTS in construction phase
  * Formal requests for information
  * Technical clarifications during construction
  * NEVER use for proposals

- schedule: ONLY for ACTIVE PROJECTS
  * Construction schedules, milestone tracking
  * Daily reports, timeline updates
  * NEVER use for proposals

- meeting: Meeting invitations, agendas, meeting notes
  * For both proposals and active projects

- general: Default for most PROPOSAL correspondence
  * Exploratory discussions, ideas, concepts
  * Scope discussions, fee discussions
  * Follow-ups, check-ins, introductions
  * Design ideas/brainstorming (NOT formal design work)
  * ANY proposal correspondence that isn't contract/meeting

CRITICAL RULES:
1. If PROPOSAL (not active project): Almost ALWAYS use "general"
   - Only exceptions: contract, meeting, or invoice
   - Design talk in proposals = "general" NOT "design"
2. If ACTIVE PROJECT: Can use design/rfi/schedule for formal work
3. When in doubt for proposals → "general"

Subject: {subject}
Body: {body[:500]}

Respond with ONLY the category name (one word).
"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",  # Latest Claude
                max_tokens=10,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            category = response.content[0].text.strip().lower()

            # Validate category
            valid_categories = ['contract', 'invoice', 'design', 'rfi', 'schedule', 'meeting', 'general']
            if category not in valid_categories:
                category = 'general'

            # CRITICAL: Force proposals to use general for design/rfi/schedule
            if proposal_context and not proposal_context.get('is_active_project', 0):
                # This is a PROPOSAL (not active project)
                if category in ['design', 'rfi', 'schedule']:
                    category = 'general'  # Force to general

            # Save for training
            self.save_training_data('classify', prompt, category, 'claude-sonnet-4-5', 0.9)

            return category, 0.9

        except Exception as e:
            print(f"  ⚠️ AI categorization failed: {e}")
            return "general", 0.5

    def extract_entities_ai(self, subject, body):
        """Extract key entities using Claude AI"""
        if not self.ai_enabled:
            return {
                'amounts': [],
                'dates': [],
                'people': [],
                'decisions': []
            }

        prompt = f"""Extract key entities from this Bensley Design Studios email:

Subject: {subject}
Body: {body[:800]}

Extract:
1. Money amounts (fees, costs, budgets)
2. Important dates (deadlines, meetings)
3. People mentioned (names, titles)
4. Decisions made (approvals, rejections, choices)

Return as JSON with keys: amounts, dates, people, decisions
Each should be an array of strings.

Example:
{{"amounts": ["$50,000 design fee"], "dates": ["March 15, 2024"], "people": ["John Smith, Project Manager"], "decisions": ["Approved initial concept"]}}
"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=300,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse JSON response
            entities_text = response.content[0].text.strip()

            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', entities_text, re.DOTALL)
            if json_match:
                entities = json.loads(json_match.group())
            else:
                entities = json.loads(entities_text)

            # Save for training
            self.save_training_data('extract', prompt, json.dumps(entities), 'claude-sonnet-4-5', 0.9)

            return entities

        except Exception as e:
            print(f"  ⚠️ Entity extraction failed: {e}")
            return {
                'amounts': [],
                'dates': [],
                'people': [],
                'decisions': []
            }

    def score_importance_ai(self, subject, body, category):
        """Score importance using Claude AI"""
        if not self.ai_enabled:
            return 0.5

        prompt = f"""Rate the importance of this Bensley Design Studios email (0.0 to 1.0):

Category: {category}
Subject: {subject}
Body: {body[:400]}

High importance (0.8-1.0):
- Contracts, legal documents
- Large fees, budgets
- Critical deadlines
- Client decisions
- Project approvals/rejections

Medium importance (0.5-0.7):
- Regular updates
- Meeting requests
- Design reviews
- Schedule changes

Low importance (0.0-0.4):
- FYI messages
- Thank you emails
- General chat

Respond with ONLY a number between 0.0 and 1.0
"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=5,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )

            score_text = response.content[0].text.strip()
            score = float(score_text)

            # Clamp to 0.0-1.0
            score = max(0.0, min(1.0, score))

            return score

        except Exception as e:
            print(f"  ⚠️ Importance scoring failed: {e}")
            return 0.5

    def generate_summary_ai(self, subject, body):
        """Generate concise summary using Claude AI"""
        if not self.ai_enabled:
            return None

        prompt = f"""Summarize this Bensley Design Studios email in ONE sentence (max 100 chars):

Subject: {subject}
Body: {body[:600]}

Focus on: what action is needed, what decision was made, or what information is shared.
Be specific and concise.
"""

        try:
            response = self.client.messages.create(
                model="claude-haiku-3-5-20250314",  # Use Haiku for speed
                max_tokens=50,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            summary = response.content[0].text.strip()

            # Truncate if too long
            if len(summary) > 120:
                summary = summary[:117] + "..."

            # Save for training
            self.save_training_data('summarize', prompt, summary, 'claude-haiku-3-5', 0.85)

            return summary

        except Exception as e:
            print(f"  ⚠️ Summary generation failed: {e}")
            return None

    def save_training_data(self, task_type, prompt, response, model, confidence):
        """Save AI interactions for future fine-tuning"""
        # Save to training_data table for future model distillation
        try:
            self.cursor.execute("""
                INSERT INTO training_data (task_type, prompt, response, model_used, confidence_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (task_type, prompt, response, model, confidence, datetime.now().isoformat()))
            self.stats['training_saved'] += 1
        except Exception as e:
            # Table might not exist yet, skip silently
            pass

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

        # Clean email body
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
            self.cursor.execute("""
                INSERT OR REPLACE INTO email_content
                (email_id, clean_body, quoted_text, category, key_points, entities,
                 sentiment, importance_score, ai_summary, processing_model, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email_id,
                clean_body,
                quoted_text,
                category,
                json.dumps([]),  # key_points (deprecated)
                json.dumps(entities),
                "neutral",  # sentiment (could add later)
                importance,
                summary,
                "claude-sonnet-4-5-20250929",
                datetime.now().isoformat()
            ))

            self.conn.commit()
            self.stats['processed'] += 1
            return True

        except Exception as e:
            print(f"  ⚠️ Error saving email {email_id}: {e}")
            self.stats['errors'] += 1
            return False

    def process_all_emails(self):
        """Process all unprocessed emails"""
        # Get unprocessed emails
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

        print("\nSummary:")
        print(f"  Emails processed:      {self.stats['processed']}")
        print(f"  ✓ Cleaned:             {self.stats['cleaned']}")
        print(f"  ✓ Categorized:         {self.stats['categorized']}")
        print(f"  ✓ Entities extracted:  {self.stats['entities_extracted']}")
        print(f"  ✓ Summaries generated: {self.stats['summaries_generated']}")
        print(f"  📚 Training data saved: {self.stats['training_saved']}")
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

        # Show most important emails
        self.cursor.execute("""
            SELECT ec.category, ec.ai_summary, ec.importance_score
            FROM email_content ec
            WHERE ec.ai_summary IS NOT NULL
            AND ec.importance_score >= 0.8
            ORDER BY ec.importance_score DESC
            LIMIT 5
        """)

        print("\n⭐ Most Important Emails:")
        for row in self.cursor.fetchall():
            score = int(row['importance_score'] * 100)
            summary = row['ai_summary'][:70]
            print(f"   [{score}%] {row['category']:<10} {summary}")

        print("="*80)

    def __del__(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 email_content_processor_claude.py <database_path>")
        sys.exit(1)

    db_path = sys.argv[1]

    print("="*80)
    print("🧠 BENSLEY BRAIN - EMAIL CONTENT PROCESSOR (CLAUDE)")
    print("="*80)
    print(f"Database: {db_path}")

    processor = EmailContentProcessorClaude(db_path)

    if processor.ai_enabled:
        print("AI Enabled: ✓ (Claude Sonnet 4.5)")
        print("\nStarting email processing...")
        processor.process_all_emails()
    else:
        print("AI Enabled: ✗")
        print("\n⚠️  Set ANTHROPIC_API_KEY in .env to enable AI processing")
        print("   Get your API key from: https://console.anthropic.com/")
