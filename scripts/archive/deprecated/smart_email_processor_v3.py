#!/usr/bin/env python3
"""
Smart Email Processor V3 - Contact-First + Learning System

IMPROVEMENTS OVER V2:
1. Contact-first matching: Check sender against contact database FIRST
2. Participant extraction: Extract names/aliases from emails to improve contact database
3. AI as fallback only: Only use AI when sender unknown
4. Duplicate prevention: No more duplicate links
5. Learning system: Gets smarter with each email processed
"""
import sqlite3, os, sys, time, argparse, re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

class SmartEmailProcessorV3:
    def __init__(self):
        self.db_path = os.getenv('DATABASE_PATH', 'database/bensley_master.db')
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.api_calls = 0
        self.estimated_cost = 0.0
        self.processed = 0
        self.linked = 0
        self.contact_matched = 0
        self.ai_matched = 0
        self.suggestions = []  # Store learning suggestions

    def load_proposals_with_contacts(self) -> List[Dict]:
        """Load proposals WITH contact information"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT proposal_id, project_code, project_name,
                   contact_person, contact_email, client_company
            FROM proposals
            ORDER BY proposal_id
        """)
        proposals = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return proposals

    def extract_email_address(self, sender: str) -> str:
        """Extract email address from sender field"""
        if '<' in sender and '>' in sender:
            match = re.search(r'<(.+?)>', sender)
            return match.group(1).lower() if match else sender.lower()
        return sender.lower().strip()

    def match_by_contact(self, email: Dict, proposals: List[Dict]) -> Optional[Tuple[int, float]]:
        """STEP 1: Try to match by sender contact FIRST"""
        sender_email = self.extract_email_address(email['sender_email'])
        sender_name = email['sender_email'].split('<')[0].strip(' "') if '<' in email['sender_email'] else ''

        # Check against all proposal contacts
        for p in proposals:
            # Match by email
            if p['contact_email'] and sender_email in p['contact_email'].lower():
                logger.info(f"  ✓ Contact match: {sender_email} → {p['project_code']}")
                return (p['proposal_id'], 0.95)

            # Match by name
            if p['contact_person'] and sender_name:
                contact_names = [n.strip() for n in p['contact_person'].split(',')]
                for contact in contact_names:
                    # Check if sender name contains contact name or vice versa
                    if contact.lower() in sender_name.lower() or sender_name.lower() in contact.lower():
                        logger.info(f"  ✓ Contact name match: {sender_name} → {p['project_code']}")
                        return (p['proposal_id'], 0.90)

        return None

    def extract_participants(self, email: Dict, linked_proposal: Optional[Dict]) -> Dict:
        """STEP 2: Extract participants and context from email for learning"""
        try:
            proposal_context = ""
            if linked_proposal:
                proposal_context = f"\nThis email was linked to: {linked_proposal['project_code']} - {linked_proposal['project_name']}"

            prompt = f"""Extract information from this email to improve our contact database:

Email:
From: {email['sender_email']}
Subject: {email['subject']}
Body: {email['body_full'][:1000] if email['body_full'] else ''}{proposal_context}

Extract and return as JSON:
{{
  "people": ["name1 (role/email if mentioned)", "name2", ...],
  "project_aliases": ["nickname or alternate name for project", ...],
  "locations": ["specific location mentions", ...],
  "companies": ["company names mentioned", ...]
}}

Only extract if clearly mentioned. Return empty arrays if nothing found."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=300
            )

            result = response.choices[0].message.content.strip()
            self.api_calls += 1
            self.estimated_cost += 0.005

            import json
            try:
                extracted = json.loads(result)
                return extracted
            except:
                return {"people": [], "project_aliases": [], "locations": [], "companies": []}

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {"people": [], "project_aliases": [], "locations": [], "companies": []}

    def link_with_ai_fallback(self, email: Dict, proposals: List[Dict]) -> List[tuple]:
        """STEP 3: Use AI as fallback ONLY for unknown senders"""
        try:
            proposal_list = "\n".join([
                f"- {p['project_code']}: {p['project_name']} | Contact: {p['contact_person'] or 'N/A'}"
                for p in proposals
            ])

            prompt = f"""Match this email to proposal(s). BE EXTREMELY STRICT.

Email:
From: {email['sender_email']}
Subject: {email['subject']}
Body: {email['body_full'][:800] if email['body_full'] else ''}

Proposals:
{proposal_list}

CRITICAL RULES - FOLLOW EXACTLY:
1. ONLY link if you see SPECIFIC evidence:
   - Exact project name mentioned
   - Project code mentioned (BK-XXX)
   - Unique location/detail that matches ONE project

2. DO NOT link if email just mentions:
   - A region (India, Bali, China)
   - A general category (wellness, resort)
   - No specific details

3. When in DOUBT → return "NONE"
4. Default to ZERO links, not multiple

Examples:
- "Mumbai High-End Club proposal" → BK-047 ONLY
- "Le Parque Ahmedabad update" → BK-028 ONLY
- "India project introduction" → NONE (too vague)
- "Discussing multiple India projects" → NONE (no specific match)

Return ONLY project codes comma-separated, or "NONE"."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100
            )

            result = response.choices[0].message.content.strip()
            self.api_calls += 1
            self.estimated_cost += 0.01

            if result == "NONE" or not result:
                return []

            # Parse and match
            codes = [code.strip() for code in result.split(',')]
            links = []
            for code in codes:
                for p in proposals:
                    if p['project_code'] == code:
                        links.append((p['proposal_id'], 0.75))  # Lower confidence for AI
                        break

            return links

        except Exception as e:
            logger.error(f"AI linking failed: {e}")
            return []

    def assign_master_folder(self, email: Dict, stage: str, category: str) -> Optional[str]:
        """Assign to master folders like 'Master Scheduling'"""
        subject = (email['subject'] or '').lower()

        if 'schedule' in subject or 'shedule' in subject:
            return 'Master Scheduling'

        return None

    def categorize_and_assign_folder(self, email: Dict) -> Tuple[str, str, Optional[str]]:
        """Returns (stage, category, folder)"""
        try:
            prompt = f"""Categorize this email into TWO dimensions:

STAGE (business track):
- proposal: Pre-contract sales (trying to win business, even if it's Shinta Mani brand)
- active: Post-contract delivery (executing won projects)
- internal: Internal Bensley operations (payroll, accounting, internal admin)
- other: Other business (Bill's private projects, social media)

CATEGORY (activity type):
- contract: NDAs, agreements, legal
- design: Design reviews, drawings
- financial: Invoices, payments, budgets
- meeting: Meetings, scheduling, coordination
- administrative: Staff schedules, internal admin
- general: General discussion

Email:
From: {email['sender_email']}
Subject: {email['subject']}
Body: {email['body_full'][:1000] if email['body_full'] else ''}

IMPORTANT: If email mentions "Shinta Mani" BUT Bensley is designing it, it's still "proposal" stage!

Return ONLY two words: stage category"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=50
            )

            result = response.choices[0].message.content.strip().lower()
            parts = result.split()
            stage = parts[0] if len(parts) >= 1 else "other"
            category = parts[1] if len(parts) >= 2 else "general"

            self.api_calls += 1
            self.estimated_cost += 0.005

            folder = self.assign_master_folder(email, stage, category)

            return stage, category, folder

        except Exception as e:
            logger.error(f"Categorization failed: {e}")
            return "other", "general", None

    def process_batch(self, emails: List[Dict], proposals: List[Dict]) -> Dict:
        """Process batch with V3 logic"""
        batch_stats = {
            'processed': 0,
            'categorized': 0,
            'linked': 0,
            'contact_matched': 0,
            'ai_matched': 0,
            'junk_filtered': 0,
            'errors': 0
        }

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for email in emails:
            try:
                # Categorize with folder assignment
                stage, category, folder = self.categorize_and_assign_folder(email)
                logger.info(f"Email {email['email_id']}: {stage}/{category}" + (f" → {folder}" if folder else ""))
                batch_stats['categorized'] += 1

                # STEP 1: Try contact-first matching
                contact_match = self.match_by_contact(email, proposals)

                links = []
                linked_proposal = None

                if contact_match:
                    links = [contact_match]
                    batch_stats['contact_matched'] += 1
                    self.contact_matched += 1

                    # Get the proposal details for extraction
                    for p in proposals:
                        if p['proposal_id'] == contact_match[0]:
                            linked_proposal = p
                            break
                else:
                    # STEP 3: Use AI as fallback
                    links = self.link_with_ai_fallback(email, proposals)
                    if links:
                        batch_stats['ai_matched'] += 1
                        self.ai_matched += 1

                # STEP 2: Extract participants for learning
                if links:
                    extracted = self.extract_participants(email, linked_proposal)
                    if any(extracted.values()):
                        self.suggestions.append({
                            'email_id': email['email_id'],
                            'project_code': linked_proposal['project_code'] if linked_proposal else 'Unknown',
                            'extracted': extracted
                        })

                # Insert links with duplicate prevention
                if links:
                    for proposal_id, confidence in links:
                        cursor.execute("""
                            INSERT OR IGNORE INTO email_proposal_links
                            (email_id, proposal_id, confidence_score, auto_linked, created_at)
                            VALUES (?, ?, ?, 1, datetime('now'))
                        """, (email['email_id'], proposal_id, confidence))
                    batch_stats['linked'] += 1
                    logger.info(f"  → Linked to {len(links)} proposals")

                # Update with stage, category, AND folder
                cursor.execute("""
                    UPDATE emails
                    SET processed = 1, stage = ?, category = ?, collection = ?
                    WHERE email_id = ?
                """, (stage, category, folder, email['email_id']))

                batch_stats['processed'] += 1

            except Exception as e:
                logger.error(f"Error processing {email['email_id']}: {e}")
                batch_stats['errors'] += 1

        conn.commit()
        conn.close()
        return batch_stats

    def get_unprocessed_emails(self, limit: Optional[int] = None) -> List[Dict]:
        """Get unprocessed emails"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT email_id, subject, sender_email, body_full, date, has_attachments, folder
            FROM emails
            WHERE processed = 0
            ORDER BY has_attachments DESC, date DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        emails = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return emails

    def save_suggestions(self):
        """Save learning suggestions to file"""
        if not self.suggestions:
            return

        with open('email_learning_suggestions.txt', 'w') as f:
            f.write("=== EMAIL LEARNING SUGGESTIONS ===\n\n")
            f.write("Add these contacts/aliases to improve future matching:\n\n")

            for i, sugg in enumerate(self.suggestions[:50], 1):  # Show first 50
                f.write(f"{i}. Email #{sugg['email_id']} → {sugg['project_code']}\n")
                if sugg['extracted']['people']:
                    f.write(f"   People: {', '.join(sugg['extracted']['people'])}\n")
                if sugg['extracted']['project_aliases']:
                    f.write(f"   Aliases: {', '.join(sugg['extracted']['project_aliases'])}\n")
                if sugg['extracted']['locations']:
                    f.write(f"   Locations: {', '.join(sugg['extracted']['locations'])}\n")
                if sugg['extracted']['companies']:
                    f.write(f"   Companies: {', '.join(sugg['extracted']['companies'])}\n")
                f.write("\n")

            if len(self.suggestions) > 50:
                f.write(f"... and {len(self.suggestions) - 50} more suggestions\n")

        logger.info("Saved learning suggestions to email_learning_suggestions.txt")

def main():
    parser = argparse.ArgumentParser(description='Smart Email Processor V3')
    parser.add_argument('--batch-size', type=int, default=50)
    parser.add_argument('--max-batches', type=int, default=None)
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args()

    print("=" * 80)
    print("SMART EMAIL PROCESSOR V3 - CONTACT-FIRST + LEARNING")
    print("=" * 80)

    processor = SmartEmailProcessorV3()

    # Load proposals WITH contacts
    proposals = processor.load_proposals_with_contacts()
    logger.info(f"Loaded {len(proposals)} proposals with contacts")
    print(f"\n📊 Loaded {len(proposals)} proposals (with contact info)")

    # Get emails
    emails = processor.get_unprocessed_emails()
    print(f"📧 Found {len(emails)} unprocessed emails")

    if args.all:
        max_emails = len(emails)
    elif args.max_batches:
        max_emails = args.batch_size * args.max_batches
    else:
        max_emails = args.batch_size

    emails_to_process = emails[:max_emails]
    print(f"🎯 Will process: {len(emails_to_process)} emails")
    print(f"💰 Estimated cost: ${len(emails_to_process) * 0.02:.2f}")

    if not args.all and len(emails_to_process) > 100:
        confirm = input("\nContinue? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Cancelled")
            return

    # Process
    start_time = time.time()
    num_batches = (len(emails_to_process) + args.batch_size - 1) // args.batch_size

    for i in range(num_batches):
        batch_start = i * args.batch_size
        batch_end = min(batch_start + args.batch_size, len(emails_to_process))
        batch = emails_to_process[batch_start:batch_end]

        print(f"\n📦 Batch {i+1}/{num_batches} ({batch_start+1}-{batch_end}/{len(emails_to_process)})")

        batch_stats = processor.process_batch(batch, proposals)
        processor.processed += batch_stats['processed']
        processor.linked += batch_stats['linked']

        print(f"   ✅ Processed: {batch_stats['processed']}")
        print(f"   🔗 Linked: {batch_stats['linked']}")
        print(f"   👤 Contact-matched: {batch_stats['contact_matched']}")
        print(f"   🤖 AI-matched: {batch_stats['ai_matched']}")
        print(f"   💰 Cost so far: ${processor.estimated_cost:.2f}")

        if i < num_batches - 1:
            time.sleep(2)

    elapsed = time.time() - start_time

    # Save learning suggestions
    processor.save_suggestions()

    print(f"\n✅ COMPLETE! Processed {processor.processed} emails in {elapsed/60:.1f} min")
    print(f"📊 Contact-matched: {processor.contact_matched} ({processor.contact_matched/processor.processed*100:.1f}%)")
    print(f"🤖 AI-matched: {processor.ai_matched} ({processor.ai_matched/processor.processed*100:.1f}%)")
    print(f"💡 Learning suggestions: {len(processor.suggestions)}")
    print(f"💰 Total cost: ${processor.estimated_cost:.2f}\n")

if __name__ == '__main__':
    main()
