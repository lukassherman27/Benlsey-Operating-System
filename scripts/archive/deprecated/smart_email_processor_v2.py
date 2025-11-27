#!/usr/bin/env python3
"""
Smart Email Processor V2 - With Contact Matching & Master Folders

IMPROVEMENTS:
- Matches proposals by CONTACT NAMES not just project names
- Assigns MASTER FOLDERS (Master Scheduling, etc.)  
- Smarter linking - doesn't over-link to all similar projects
- Extracts contacts from email to match precisely
"""
import sqlite3, os, sys, time, argparse
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

class SmartEmailProcessorV2:
    def __init__(self):
        self.db_path = os.getenv('DATABASE_PATH', 'database/bensley_master.db')
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.api_calls = 0
        self.estimated_cost = 0.0
        self.junk_filtered = []
        self.processed = 0
        self.linked = 0
        self.categorized = 0

    def load_proposals_with_contacts(self) -> List[Dict]:
        """Load proposals WITH contact information for better matching"""
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

    def assign_master_folder(self, email: Dict, stage: str, category: str) -> Optional[str]:
        """Assign to master folders like 'Master Scheduling'"""
        subject = (email['subject'] or '').lower()
        
        # Master Scheduling folder
        if 'schedule' in subject or 'shedule' in subject:
            return 'Master Scheduling'
        
        # Add more master folders as needed
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
            
            # Assign master folder if applicable
            folder = self.assign_master_folder(email, stage, category)
            
            return stage, category, folder
            
        except Exception as e:
            logger.error(f"Categorization failed: {e}")
            return "other", "general", None

    def link_to_proposals_smart(self, email: Dict, proposals: List[Dict]) -> List[tuple]:
        """SMART linking using contact names + project context"""
        try:
            # Build proposal list WITH CONTACTS
            proposal_list = "\n".join([
                f"- {p['project_code']}: {p['project_name']} | Contact: {p['contact_person'] or 'N/A'}"
                for p in proposals
            ])
            
            prompt = f"""Match this email to the CORRECT proposal(s). BE VERY SELECTIVE - default to ONE or ZERO projects.

Email:
From: {email['sender_email']}
Subject: {email['subject']}
Body: {email['body_full'][:800] if email['body_full'] else ''}

Proposals (with contacts):
{proposal_list}

CRITICAL RULES (FOLLOW STRICTLY):
1. DEFAULT TO ZERO OR ONE PROJECT - only link to multiple if email EXPLICITLY discusses multiple projects
2. Match by CONTACT NAME FIRST (e.g., "Carlos" → BK-074, "Nigel/Sudha" → BK-037, "Vikram" → BK-073)
3. If multiple similar projects exist (multiple India/Sumba projects), pick THE SINGLE MOST SPECIFIC MATCH
4. DO NOT link to all projects in a region just because region is mentioned
5. Only link to multiple projects if: (a) email is a schedule/overview listing projects OR (b) email explicitly names multiple contacts/projects
6. When in doubt, return "NONE" - NO LINK is better than WRONG LINK

Return ONLY project codes (e.g., BK-074) comma-separated, or "NONE"."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=150
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
                        links.append((p['proposal_id'], 0.9))  # Higher confidence
                        break
            
            return links
            
        except Exception as e:
            logger.error(f"Linking failed: {e}")
            return []

    def is_junk_email(self, email: Dict) -> Tuple[bool, str]:
        """Detect junk emails"""
        subject = (email['subject'] or '').lower()
        sender = (email['sender_email'] or '').lower()
        body = (email['body_full'] or '').lower()
        
        junk_senders = ['no-reply@', 'noreply@', 'donotreply@', 'notifications@']
        junk_subjects = ['unsubscribe', 'newsletter', 'weekly digest', 'automated']
        
        for pattern in junk_senders:
            if pattern in sender:
                return True, f"Junk sender: {pattern}"
        
        for pattern in junk_subjects:
            if pattern in subject:
                return True, f"Junk subject: {pattern}"
        
        if body and len(body) < 50:
            return True, "Too short (likely automated)"
        
        return False, ""

    def process_batch(self, emails: List[Dict], proposals: List[Dict]) -> Dict:
        """Process batch with new logic"""
        batch_stats = {'processed': 0, 'categorized': 0, 'linked': 0, 'junk_filtered': 0, 'errors': 0}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for email in emails:
            try:
                # Check junk
                is_junk, reason = self.is_junk_email(email)
                if is_junk:
                    logger.info(f"Skipping junk: {email['email_id']}: {reason}")
                    cursor.execute("""
                        UPDATE emails
                        SET processed = 1, stage = 'other', category = 'junk'
                        WHERE email_id = ?
                    """, (email['email_id'],))
                    batch_stats['junk_filtered'] += 1
                    continue
                
                # Categorize with folder assignment
                stage, category, folder = self.categorize_and_assign_folder(email)
                logger.info(f"Email {email['email_id']}: {stage}/{category}" + (f" → {folder}" if folder else ""))
                batch_stats['categorized'] += 1
                
                # Smart linking with contacts
                links = self.link_to_proposals_smart(email, proposals)
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

def main():
    parser = argparse.ArgumentParser(description='Smart Email Processor V2')
    parser.add_argument('--batch-size', type=int, default=50)
    parser.add_argument('--max-batches', type=int, default=None)
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args()
    
    print("=" * 80)
    print("SMART EMAIL PROCESSOR V2 - WITH CONTACT MATCHING")
    print("=" * 80)
    
    processor = SmartEmailProcessorV2()
    
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
    print(f"💰 Estimated cost: ${len(emails_to_process) * 0.015:.2f}")
    
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
        processor.categorized += batch_stats['categorized']
        processor.linked += batch_stats['linked']
        
        print(f"   ✅ Processed: {batch_stats['processed']}")
        print(f"   🏷️  Categorized: {batch_stats['categorized']}")
        print(f"   🔗 Linked: {batch_stats['linked']}")
        print(f"   💰 Cost so far: ${processor.estimated_cost:.2f}")
        
        if i < num_batches - 1:
            time.sleep(2)
    
    elapsed = time.time() - start_time
    print(f"\n✅ COMPLETE! Processed {processor.processed} emails in {elapsed/60:.1f} min")
    print(f"💰 Total cost: ${processor.estimated_cost:.2f}\n")

if __name__ == '__main__':
    main()
