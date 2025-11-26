#!/usr/bin/env python3
"""
Email Content Processor - The Bensley Brain

Processes emails to extract intelligence:
- Strips signatures/banners
- Categorizes emails
- Extracts entities (fees, dates, decisions)
- Scores importance
- Generates summaries
- Saves training data for future distillation
"""

import sqlite3
import json
import re
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI not available - install with: pip install openai")


class EmailContentProcessor:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # OpenAI setup
        self.openai_key = os.getenv('OPENAI_API_KEY')
        if self.openai_key and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=self.openai_key)
            self.ai_enabled = True
            print("✓ OpenAI enabled")
        else:
            self.ai_enabled = False
            print("⚠️  OpenAI disabled (no API key or module)")

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
        """Remove signatures, banners, and extract quoted text"""
        if not body:
            return "", ""

        # Detect signature
        sig_start = self.detect_signature(body)
        clean_body = body[:sig_start].strip()

        # Extract quoted text (lines starting with >)
        quoted_lines = []
        content_lines = []

        for line in clean_body.split('\n'):
            if line.strip().startswith('>'):
                quoted_lines.append(line)
            else:
                content_lines.append(line)

        clean_body = '\n'.join(content_lines).strip()
        quoted_text = '\n'.join(quoted_lines).strip()

        return clean_body, quoted_text

    def categorize_email_ai(self, subject, body, proposal_context=None):
        """Use AI to categorize email with proposal/project context"""
        if not self.ai_enabled:
            return "general", 0.5

        # Build context string
        context = ""
        if proposal_context:
            is_active = proposal_context.get('is_active_project', 0)
            project_title = proposal_context.get('project_title', '')
            status = proposal_context.get('status', 'proposal')

            if is_active:
                context = f"""
PROJECT CONTEXT: This is an ACTIVE PROJECT (contract signed) - {project_title}
Status: {status}
"""
            else:
                context = f"""
PROJECT CONTEXT: This is a PROPOSAL (not yet won) - {project_title}
Status: {status} (pre-contract)
"""

        prompt = f"""Categorize this Bensley Design Studios email into ONE category:
{context}
Categories:

- proposal: Initial project proposals, fee proposals, scope discussions
  * Discussing fees, budgets, pricing
  * Sharing initial concepts, design ideas
  * Proposal submissions, RFPs, quote requests
  * Scope negotiations (what will be included)
  * ONLY for PROPOSALS (not active projects)

- project_update: Status updates on ongoing work
  * Progress reports, milestone completions
  * Project status emails ("here's where we are")
  * Updates on next steps
  * Can be for proposals OR active projects

- contract: Formal legal documents (NDAs, MOUs, signed contracts, amendments)
  * Negotiating contract terms and language
  * Signing, reviewing legal agreements
  * Contract amendments, extensions
  * For both proposals AND active projects

- invoice: Payment-related emails (invoices, receipts, bills)
  * Sending/receiving invoices
  * Payment confirmations, receipts
  * ONLY applies to ACTIVE PROJECTS with signed contracts

- design: ONLY for ACTIVE PROJECTS with formal design work
  * Submitting drawings/plans for approval
  * Design reviews, revisions, technical feedback
  * Formal design deliverables
  * NEVER use for proposal design ideas (use "proposal" instead)

- rfi: ONLY for ACTIVE PROJECTS - formal requests for information
  * Technical clarifications during construction/design phase
  * Formal RFI documents
  * Questions requiring official responses
  * NEVER use for proposals (use "proposal" for questions)

- schedule: ONLY for ACTIVE PROJECTS
  * Construction schedules, milestone tracking
  * Daily reports, timeline updates
  * Gantt charts, critical path discussions
  * NEVER use for proposal timelines (use "proposal")

- meeting: Meeting invitations, agendas, meeting notes
  * Calendar invites, Zoom links
  * Meeting summaries, action items
  * For both proposals AND active projects

- general: Miscellaneous correspondence
  * Thank you emails, introductions
  * Administrative matters
  * Emails that don't fit other categories
  * When genuinely unsure

CRITICAL RULES:
1. If discussing FEES or SCOPE → "proposal" (not "general")
2. If PROGRESS UPDATE or STATUS → "project_update" (not "general")
3. If ACTIVE PROJECT + formal RFI → "rfi"
4. If ACTIVE PROJECT + design deliverables → "design"
5. If PROPOSAL + design ideas → "proposal" (NOT "design")
6. When in doubt between proposal/project_update/general → choose proposal or project_update

Subject: {subject}
Body: {body[:500]}

Respond with ONLY the category name (one word).
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=10
            )

            category = response.choices[0].message.content.strip().lower()

            # Validate category
            valid_categories = ['contract', 'invoice', 'design', 'rfi', 'schedule', 'meeting', 'general', 'proposal', 'project_update']
            if category not in valid_categories:
                category = 'general'

            # CRITICAL: Validate context-specific categories
            if proposal_context and not proposal_context.get('is_active_project', 0):
                # This is a PROPOSAL (not active project)
                # Force design/rfi/schedule to proposal category (design ideas, questions, timelines in proposals)
                if category in ['design', 'rfi', 'schedule']:
                    category = 'proposal'  # Force to proposal
                # Invoice doesn't make sense for proposals
                if category == 'invoice':
                    category = 'proposal'

            # Save for distillation
            self.save_training_data('classify', prompt, category, 'gpt-3.5-turbo', 0.8)

            return category, 0.8

        except Exception as e:
            print(f"  ⚠️ AI categorization failed: {e}")
            return "general", 0.5

    def extract_entities_ai(self, subject, body):
        """Extract key entities using AI"""
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
3. Key people mentioned (clients, staff)
4. Decisions made or questions asked

Respond in JSON format:
{{
    "amounts": ["$2.5M fee", "$500k budget"],
    "dates": ["Oct 18 deadline", "Nov 1 meeting"],
    "people": ["Joe (client)", "Brian"],
    "decisions": ["Reduced scope to phase 1-2", "Fee agreed at $2.2M"]
}}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300,
                response_format={"type": "json_object"}
            )

            entities = json.loads(response.choices[0].message.content)

            # Save for distillation
            self.save_training_data('extract', prompt, json.dumps(entities), 'gpt-3.5-turbo', 0.7)

            return entities

        except Exception as e:
            print(f"  ⚠️ Entity extraction failed: {e}")
            return {'amounts': [], 'dates': [], 'people': [], 'decisions': []}

    def generate_summary_ai(self, subject, body, category):
        """Generate one-sentence summary"""
        if not self.ai_enabled:
            return f"{category.title()}: {subject[:50]}"

        prompt = f"""Summarize this {category} email in ONE sentence (max 15 words):

Subject: {subject}
Body: {body[:500]}

Focus on: What action, decision, or key information does this contain?
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=50
            )

            summary = response.choices[0].message.content.strip()

            # Save for distillation
            self.save_training_data('summarize', prompt, summary, 'gpt-3.5-turbo', 0.7)

            return summary

        except Exception as e:
            print(f"  ⚠️ Summary generation failed: {e}")
            return f"{category.title()}: {subject[:50]}"

    def calculate_importance(self, category, entities, body_length):
        """Calculate importance score (0-1)"""
        score = 0.5  # Base score

        # Category weights
        category_weights = {
            'contract': 0.3,
            'invoice': 0.2,
            'proposal': 0.15,
            'design': 0.15,
            'rfi': 0.15,
            'project_update': 0.1,
            'schedule': 0.1,
            'meeting': 0.1,
            'general': 0.0
        }
        score += category_weights.get(category, 0)

        # Entities boost importance
        if entities.get('amounts'):
            score += 0.1
        if entities.get('decisions'):
            score += 0.15
        if entities.get('dates'):
            score += 0.05

        # Very short emails are usually not important
        if body_length < 50:
            score -= 0.2

        return min(max(score, 0.0), 1.0)

    def save_training_data(self, task_type, input_data, output_data, model, confidence):
        """Save for future distillation"""
        try:
            self.cursor.execute("""
                INSERT INTO training_data
                (task_type, input_data, output_data, model_used, confidence)
                VALUES (?, ?, ?, ?, ?)
            """, (task_type, input_data[:2000], output_data[:1000], model, confidence))
            self.conn.commit()
            self.stats['training_saved'] += 1
        except Exception as e:
            pass  # Non-critical

    def process_email(self, email_id, subject, body, proposal_context=None):
        """Process a single email"""
        try:
            # Check if already processed
            self.cursor.execute(
                "SELECT content_id FROM email_content WHERE email_id = ?",
                (email_id,)
            )
            if self.cursor.fetchone():
                return  # Already processed

            # Clean body
            clean_body, quoted_text = self.clean_email_body(body)
            self.stats['cleaned'] += 1

            # Categorize with proposal context
            category, confidence = self.categorize_email_ai(subject, clean_body, proposal_context)
            self.stats['categorized'] += 1

            # Extract entities
            entities = self.extract_entities_ai(subject, clean_body)
            self.stats['entities_extracted'] += 1

            # Generate summary
            summary = self.generate_summary_ai(subject, clean_body, category)
            self.stats['summaries_generated'] += 1

            # Calculate importance
            importance = self.calculate_importance(category, entities, len(clean_body))

            # Save to database
            self.cursor.execute("""
                INSERT INTO email_content
                (email_id, clean_body, quoted_text, category, key_points,
                 entities, importance_score, ai_summary, processing_model)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email_id,
                clean_body,
                quoted_text,
                category,
                json.dumps(entities.get('decisions', [])),
                json.dumps(entities),
                importance,
                summary,
                'gpt-3.5-turbo' if self.ai_enabled else 'rule-based'
            ))

            self.conn.commit()
            self.stats['processed'] += 1

        except Exception as e:
            print(f"  ✗ Error processing email {email_id}: {e}")
            self.stats['errors'] += 1

    def process_all_emails(self, limit=None):
        """Process ALL emails, whether linked or not"""
        print("\n" + "="*80)
        print("🧠 BENSLEY BRAIN - EMAIL CONTENT PROCESSOR (ALL EMAILS)")
        print("="*80)
        print(f"Database: {self.db_path}")
        print(f"AI Enabled: {'✓' if self.ai_enabled else '✗'}")

        # Get ALL unprocessed emails
        query = """
            SELECT
                e.email_id,
                e.subject,
                COALESCE(e.body_full, e.body_preview) as body
            FROM emails e
            WHERE e.email_id NOT IN (SELECT email_id FROM email_content)
            ORDER BY e.date DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        self.cursor.execute(query)
        emails = self.cursor.fetchall()

        if not emails:
            print("\n✓ All emails already processed!")
            return

        print(f"\nProcessing {len(emails)} emails...")

        for i, email in enumerate(emails, 1):
            if i % 50 == 0:
                print(f"  [{i}/{len(emails)}] Processed...")

            self.process_email(
                email['email_id'],
                email['subject'],
                email['body'],
                proposal_context=None  # No context for unlinked emails
            )

        print(f"\n✅ Processing complete!")

    def process_all_linked_emails(self, limit=None):
        """Process all emails linked to proposals"""
        print("\n" + "="*80)
        print("🧠 BENSLEY BRAIN - EMAIL CONTENT PROCESSOR")
        print("="*80)
        print(f"Database: {self.db_path}")
        print(f"AI Enabled: {'✓' if self.ai_enabled else '✗'}")

        # Get linked emails with proposal context
        query = """
            SELECT DISTINCT
                e.email_id,
                e.subject,
                e.body_preview,
                p.project_title,
                p.status,
                COALESCE(p.is_active_project, 0) as is_active_project
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            JOIN proposals p ON epl.proposal_id = p.proposal_id
            WHERE e.email_id NOT IN (SELECT email_id FROM email_content)
            ORDER BY e.created_at DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        self.cursor.execute(query)
        emails = self.cursor.fetchall()

        if not emails:
            print("\n✓ All emails already processed!")
            return

        print(f"\nProcessing {len(emails)} emails...")

        for i, email in enumerate(emails, 1):
            if i % 5 == 0:
                print(f"  [{i}/{len(emails)}] Processed...")

            # Build proposal context
            proposal_context = {
                'project_title': email['project_title'],
                'status': email['status'],
                'is_active_project': email['is_active_project']
            }

            self.process_email(
                email['email_id'],
                email['subject'],
                email['body_preview'],
                proposal_context
            )

        self.print_summary()

    def print_summary(self):
        """Print processing summary"""
        print("\n" + "="*80)
        print("✅ PROCESSING COMPLETE")
        print("="*80)

        print(f"\nSummary:")
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
            GROUP BY category
            ORDER BY count DESC
        """)

        print(f"\n📊 Email Categories:")
        for row in self.cursor.fetchall():
            print(f"   {row['category']:15} {row['count']:3} emails")

        # Show high-importance emails
        self.cursor.execute("""
            SELECT e.subject, ec.category, ec.importance_score, ec.ai_summary
            FROM email_content ec
            JOIN emails e ON ec.email_id = e.email_id
            WHERE ec.importance_score > 0.7
            ORDER BY ec.importance_score DESC
            LIMIT 5
        """)

        results = self.cursor.fetchall()
        if results:
            print(f"\n⭐ Most Important Emails:")
            for row in results:
                print(f"   [{row['importance_score']:.0%}] {row['category']:10} {row['ai_summary'][:60]}")

        print("="*80)

    # =========================================================================
    # BENSLEY BRAIN INTEGRATION
    # =========================================================================

    def process_with_brain_context(self, email_id: int):
        """
        Process an email using full Bensley Brain context.

        This method uses:
        - Contact history (all emails from this sender)
        - Project context (all related emails, invoices, milestones)
        - Learned patterns (sender-project associations)
        - Thread context (previous emails in thread)

        Returns enhanced categorization and insights.
        """
        try:
            from backend.core.bensley_brain import get_brain, get_contact_context

            brain = get_brain()

            # Get email context from brain (includes sender history, thread, etc.)
            email_ctx = brain.get_email_context(email_id)
            if not email_ctx:
                print(f"  ⚠️ Email {email_id} not found")
                return None

            # Get or match project
            project_code = email_ctx.matched_project
            confidence = email_ctx.confidence

            if not project_code:
                # Use brain's intelligent matching
                project_code, confidence = brain.match_email_to_project(email_id)

            # Build rich context for categorization
            rich_context = {
                'project_title': None,
                'status': None,
                'is_active_project': 0,
                'sender_history': email_ctx.sender_history[:5],
                'thread_length': len(email_ctx.thread_context),
                'mentioned_projects': email_ctx.mentioned_projects,
            }

            # Add full project context if matched
            if project_code:
                project_ctx = brain.get_project_context(project_code)
                if project_ctx:
                    rich_context.update({
                        'project_title': project_ctx.project_title,
                        'status': project_ctx.status,
                        'is_active_project': 1 if project_ctx.is_active else 0,
                        'client_name': project_ctx.client_name,
                        'total_fee': project_ctx.total_fee,
                        'common_senders': project_ctx.common_senders,
                        'key_topics': project_ctx.key_topics,
                        'days_since_contact': project_ctx.days_since_contact,
                        'email_count': len(project_ctx.emails),
                        'invoice_count': len(project_ctx.invoices),
                        'has_meetings': len(project_ctx.meetings) > 0,
                        'has_rfis': len(project_ctx.rfis) > 0,
                    })

            # Add contact context
            if email_ctx.matched_contact:
                contact_ctx = get_contact_context(email_ctx.matched_contact)
                if contact_ctx:
                    rich_context.update({
                        'sender_name': contact_ctx.name,
                        'sender_company': contact_ctx.company,
                        'sender_role': contact_ctx.role,
                        'sender_projects': contact_ctx.projects,
                        'sender_total_emails': contact_ctx.total_emails,
                    })

            # Get email body
            self.cursor.execute("SELECT subject, body FROM emails WHERE email_id = ?", (email_id,))
            email_row = self.cursor.fetchone()
            if not email_row:
                return None

            subject = email_row['subject'] or ''
            body = email_row['body'] or ''

            # Clean body
            clean_body, quoted = self.clean_email_body(body)

            # Process with rich context
            category, cat_confidence = self.categorize_email_ai(
                subject, clean_body, rich_context
            )
            entities = self.extract_entities_ai(subject, clean_body)
            summary = self.generate_summary_ai(subject, clean_body, category)
            importance = self.calculate_importance(category, entities, len(clean_body))

            # Save results
            self.cursor.execute("""
                INSERT OR REPLACE INTO email_content
                (email_id, cleaned_body, quoted_text, category, entities,
                 ai_summary, importance_score, processed_at, confidence,
                 context_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email_id,
                clean_body,
                quoted,
                category,
                json.dumps(entities),
                summary,
                importance,
                datetime.now().isoformat(),
                max(confidence, cat_confidence),
                json.dumps({
                    'project_code': project_code,
                    'context_type': 'bensley_brain',
                    'context_fields': list(rich_context.keys())
                })
            ))
            self.conn.commit()

            return {
                'email_id': email_id,
                'project_code': project_code,
                'confidence': confidence,
                'category': category,
                'summary': summary,
                'importance': importance,
                'context_keys': list(rich_context.keys())
            }

        except ImportError:
            print("  ⚠️ Bensley Brain not available, falling back to basic processing")
            return self.process_email(email_id, email_ctx.subject, '', None)
        except Exception as e:
            print(f"  ⚠️ Brain processing error: {e}")
            self.stats['errors'] += 1
            return None

    def process_batch_with_brain(self, limit: int = None):
        """Process a batch of emails using Bensley Brain context"""
        print("\n" + "="*80)
        print("🧠 BENSLEY BRAIN EMAIL PROCESSING")
        print("="*80)

        # Get unprocessed emails
        query = """
            SELECT e.email_id, e.subject
            FROM emails e
            WHERE e.email_id NOT IN (
                SELECT email_id FROM email_content WHERE context_used LIKE '%bensley_brain%'
            )
            ORDER BY e.date DESC
        """
        if limit:
            query += f" LIMIT {limit}"

        self.cursor.execute(query)
        emails = self.cursor.fetchall()

        if not emails:
            print("\n✓ All emails already processed with Brain context!")
            return

        print(f"\nProcessing {len(emails)} emails with full context...")

        processed = 0
        for i, email in enumerate(emails, 1):
            if i % 10 == 0:
                print(f"  [{i}/{len(emails)}] Processed {processed} emails...")

            result = self.process_with_brain_context(email['email_id'])
            if result:
                processed += 1

        print(f"\n✅ Brain processing complete: {processed}/{len(emails)} emails processed")

    def close(self):
        """Close database connection"""
        self.conn.close()


def main():
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else "database/bensley_master.db"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None

    if not Path(db_path).exists():
        print(f"✗ Database not found: {db_path}")
        return

    if limit:
        print(f"📌 Processing {limit} emails (test mode)\n")

    try:
        processor = EmailContentProcessor(db_path)
        processor.process_all_emails(limit=limit)
        processor.close()
    except KeyboardInterrupt:
        print("\n\n⏸️  Interrupted - progress saved")
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
