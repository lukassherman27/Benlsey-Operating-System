#!/usr/bin/env python3
"""
email_processor.py

Intelligent email processor that:
- Auto-tags emails (invoicing, urgent, scheduling, etc.)
- Auto-links emails to projects using learned patterns
- Extracts action items
- Gets smarter over time
"""

import sqlite3
import os
import re
from datetime import datetime

class EmailProcessor:
    def __init__(self, db_path=None):
        if db_path is None:
            # Default to the database in the current project
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(project_root, 'database', 'bensley_master.db')
        self.master_db = db_path
        self.conn = sqlite3.connect(self.master_db)
        self.cursor = self.conn.cursor()
        
        # Load tag mappings for normalization
        self.load_tag_mappings()
    
    def load_tag_mappings(self):
        """Load tag normalization mappings"""
        self.cursor.execute("SELECT raw_tag, canonical_tag FROM tag_mappings")
        self.tag_map = {row[0].lower(): row[1] for row in self.cursor.fetchall()}
    
    def normalize_tag(self, raw_tag):
        """Normalize a tag using mappings"""
        return self.tag_map.get(raw_tag.lower(), raw_tag.lower())
    
    def auto_tag_email(self, email_id, subject, snippet):
        """Auto-tag an email based on content"""
        text = f"{subject or ''} {snippet or ''}".lower()
        tags_to_add = []

        # Category detection
        if any(word in text for word in ['invoice', 'billing', 'payment', 'paid', 'outstanding']):
            tags_to_add.append(('invoicing', 'category', 0.95))

        if any(word in text for word in ['urgent', 'asap', 'immediately', 'time-sensitive']):
            tags_to_add.append(('high-priority', 'priority', 0.90))

        if any(word in text for word in ['meeting', 'schedule', 'calendar', 'appointment']):
            tags_to_add.append(('scheduling', 'category', 0.90))

        if any(word in text for word in ['question', 'clarification', 'wondering', 'asking']):
            tags_to_add.append(('inquiry', 'category', 0.85))

        if any(word in text for word in ['contract', 'agreement', 'legal', 'terms']):
            tags_to_add.append(('legal', 'category', 0.90))

        if any(word in text for word in ['proposal', 'quote', 'scope', 'sow']):
            tags_to_add.append(('business-development', 'category', 0.88))

        if any(word in text for word in ['progress', 'update', 'status', 'report']):
            tags_to_add.append(('project-update', 'category', 0.85))

        # NEW CRITICAL CATEGORIES for Intelligence Layer

        # Contract Changes - detect modifications to existing contracts
        if any(phrase in text for phrase in ['revise contract', 'amend contract', 'change order',
                                                'amendment', 'modify agreement', 'contract revision']):
            tags_to_add.append(('contract-changes', 'category', 0.92))

        # Fee Adjustments - detect pricing/budget changes
        if any(phrase in text for phrase in ['reduce fee', 'increase fee', 'fee adjustment',
                                                'budget change', 'price change', 'discount',
                                                'fee reduction', 'additional cost']):
            tags_to_add.append(('fee-adjustments', 'category', 0.90))

        # Scope Changes - detect scope additions/removals
        if any(phrase in text for phrase in ['remove landscape', 'add interiors', 'expand scope',
                                                'scope change', 'additional work', 'remove from scope',
                                                'scope reduction', 'scope increase']):
            tags_to_add.append(('scope-changes', 'category', 0.88))

        # Payment Terms - detect payment schedule discussions
        if any(phrase in text for phrase in ['monthly installment', 'payment plan', 'milestone payment',
                                                'payment schedule', 'payment terms', 'installment plan',
                                                'staged payment', 'payment structure']):
            tags_to_add.append(('payment-terms', 'category', 0.87))

        # RFIs - Request for Information
        if any(word in text for word in ['rfi', 'request for information', 'clarification needed',
                                           'need clarification', 'question about', 'please clarify']):
            tags_to_add.append(('rfis', 'category', 0.93))

        # Meeting Notes - capture decisions from meetings
        if any(phrase in text for phrase in ['meeting summary', 'meeting notes', 'action items',
                                                'we agreed', 'meeting minutes', 'decisions made',
                                                'discussed in meeting', 'as discussed']):
            tags_to_add.append(('meeting-notes', 'category', 0.89))
        
        # Add tags to database
        for tag, tag_type, confidence in tags_to_add:
            self.cursor.execute("""
                INSERT OR IGNORE INTO email_tags (email_id, tag, tag_type, confidence, created_by)
                VALUES (?, ?, ?, ?, 'auto')
            """, (email_id, tag, tag_type, confidence))
        
        return len(tags_to_add)
    
    def extract_project_codes(self, text):
        """Extract project codes from text"""
        if not text:
            return []
        matches = re.findall(r'\b(?:\d{2}\s+)?BK-\d{3}\b', text, re.IGNORECASE)
        return [m.strip().upper() for m in matches]
    
    def auto_link_email_deterministic(self, email_id, sender_email, subject, snippet):
        """Link email to project using deterministic rules (fast, high confidence)"""
        links_created = 0
        text = f"{subject or ''} {snippet or ''}"
        
        # Method 1: Explicit project code in subject/body (HIGHEST CONFIDENCE)
        project_codes = self.extract_project_codes(text)
        for code in project_codes:
            # Check if project exists
            self.cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (code,))
            result = self.cursor.fetchone()
            
            if result:
                project_id = result[0]
                self.cursor.execute("""
                    INSERT OR IGNORE INTO email_project_links 
                    (email_id, project_id, confidence, link_method, evidence)
                    VALUES (?, ?, ?, ?, ?)
                """, (email_id, project_id, 0.99, 'explicit_code', f'Project code {code} found in email'))
                links_created += self.cursor.rowcount
        
        # Method 2: Learned pattern matching (sender has history with project)
        if sender_email:
            self.cursor.execute("""
                SELECT pattern_value, confidence, occurrences
                FROM learned_patterns
                WHERE pattern_type = 'sender_to_project' 
                  AND pattern_key = ?
                ORDER BY confidence DESC
                LIMIT 3
            """, (sender_email,))
            
            for project_code, confidence, occurrences in self.cursor.fetchall():
                # Get project_id
                self.cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
                result = self.cursor.fetchone()
                
                if result:
                    project_id = result[0]
                    self.cursor.execute("""
                        INSERT OR IGNORE INTO email_project_links 
                        (email_id, project_id, confidence, link_method, evidence)
                        VALUES (?, ?, ?, ?, ?)
                    """, (email_id, project_id, confidence, 'sender_pattern', 
                          f'Sender has sent {occurrences} previous emails about this project'))
                    links_created += self.cursor.rowcount
        
        # Method 3: Domain pattern matching
        if sender_email and '@' in sender_email:
            domain = sender_email.split('@')[1]
            self.cursor.execute("""
                SELECT pattern_value, confidence, occurrences
                FROM learned_patterns
                WHERE pattern_type = 'domain_to_project' 
                  AND pattern_key = ?
                ORDER BY confidence DESC
                LIMIT 2
            """, (domain,))
            
            for project_code, confidence, occurrences in self.cursor.fetchall():
                self.cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
                result = self.cursor.fetchone()
                
                if result:
                    project_id = result[0]
                    self.cursor.execute("""
                        INSERT OR IGNORE INTO email_project_links 
                        (email_id, project_id, confidence, link_method, evidence)
                        VALUES (?, ?, ?, ?, ?)
                    """, (email_id, project_id, confidence * 0.9, 'domain_pattern',
                          f'Domain {domain} associated with this project'))
                    links_created += self.cursor.rowcount
        
        return links_created
    
    def process_unprocessed_emails(self):
        """Process all emails that haven't been processed yet"""
        print("\n🔄 Processing unprocessed emails...")

        # Get unprocessed emails
        self.cursor.execute("""
            SELECT email_id, sender_email, subject, snippet
            FROM emails
            WHERE processed = 0
            ORDER BY date DESC
        """)

        emails = self.cursor.fetchall()
        total_emails = len(emails)

        if total_emails == 0:
            print("   ✅ All emails already processed!")
            return

        print(f"   Found {total_emails} unprocessed emails")

        tags_added = 0
        links_created = 0

        for i, (email_id, sender_email, subject, snippet) in enumerate(emails, 1):
            if i % 100 == 0:
                print(f"   Processing... {i}/{total_emails}")

            # Auto-tag
            tags_added += self.auto_tag_email(email_id, subject, snippet)

            # Auto-link
            links_created += self.auto_link_email_deterministic(email_id, sender_email, subject, snippet)

            # Mark as processed
            self.cursor.execute("UPDATE emails SET processed = 1 WHERE email_id = ?", (email_id,))

        self.conn.commit()

        print(f"   ✅ Processed {total_emails} emails")
        print(f"   ✅ Added {tags_added} tags")
        print(f"   ✅ Created {links_created} project links")

        return total_emails, tags_added, links_created

    def retag_all_emails_with_new_categories(self):
        """Re-tag ALL emails with new category patterns (for adding new categories)"""
        print("\n🔄 Re-tagging ALL emails with new category patterns...")
        print("   Note: Only new tags will be added, existing tags are preserved\n")

        # Get ALL emails
        self.cursor.execute("""
            SELECT email_id, subject, snippet
            FROM emails
            ORDER BY date DESC
        """)

        emails = self.cursor.fetchall()
        total_emails = len(emails)

        print(f"   Found {total_emails} total emails to re-process")

        tags_added = 0

        for i, (email_id, subject, snippet) in enumerate(emails, 1):
            if i % 100 == 0:
                print(f"   Re-tagging... {i}/{total_emails}")

            # Re-tag with potentially new categories
            tags_added += self.auto_tag_email(email_id, subject, snippet)

        self.conn.commit()

        print(f"\n   ✅ Re-processed {total_emails} emails")
        print(f"   ✅ Added {tags_added} new tags")

        return total_emails, tags_added
    
    def show_processing_summary(self):
        """Show summary of processing results"""
        print("\n" + "="*70)
        print("PROCESSING SUMMARY")
        print("="*70)
        
        # Email status
        self.cursor.execute("""
            SELECT 
                SUM(CASE WHEN processed = 1 THEN 1 ELSE 0 END) as processed,
                SUM(CASE WHEN processed = 0 THEN 1 ELSE 0 END) as unprocessed,
                COUNT(*) as total
            FROM emails
        """)
        
        processed, unprocessed, total = self.cursor.fetchone()
        print(f"\n📊 Email Processing Status:")
        print(f"   Processed: {processed}/{total} ({100*processed/total:.1f}%)")
        print(f"   Remaining: {unprocessed}")
        
        # Linking stats
        self.cursor.execute("""
            SELECT COUNT(DISTINCT email_id) as linked_emails
            FROM email_project_links
        """)
        linked = self.cursor.fetchone()[0]
        
        self.cursor.execute("""
            SELECT COUNT(*) FROM emails 
            WHERE sender_email NOT LIKE '%bensley.com%'
              AND sender_email NOT LIKE '%bensley.co.id%'
        """)
        external = self.cursor.fetchone()[0]
        
        print(f"\n🔗 Email Linking:")
        print(f"   External emails: {external}")
        print(f"   Linked to projects: {linked} ({100*linked/external:.1f}%)")
        
        # Top tags
        print(f"\n🏷️  Most common tags:")
        self.cursor.execute("""
            SELECT tag, COUNT(*) as count
            FROM email_tags
            WHERE created_by = 'auto'
            GROUP BY tag
            ORDER BY count DESC
            LIMIT 5
        """)
        
        for tag, count in self.cursor.fetchall():
            print(f"   {tag}: {count}")
        
        # Link confidence distribution
        print(f"\n📈 Link confidence distribution:")
        self.cursor.execute("""
            SELECT 
                CASE 
                    WHEN confidence >= 0.95 THEN 'Very High (≥0.95)'
                    WHEN confidence >= 0.85 THEN 'High (0.85-0.95)'
                    WHEN confidence >= 0.70 THEN 'Medium (0.70-0.85)'
                    ELSE 'Low (<0.70)'
                END as conf_level,
                COUNT(*) as count
            FROM email_project_links
            GROUP BY conf_level
            ORDER BY MIN(confidence) DESC
        """)
        
        for level, count in self.cursor.fetchall():
            print(f"   {level}: {count}")
    
    def run(self):
        """Main processing"""
        print("="*70)
        print("INTELLIGENT EMAIL PROCESSING")
        print("="*70)
        
        # Process emails
        self.process_unprocessed_emails()
        
        # Show summary
        self.show_processing_summary()
        
        print("\n✅ Processing complete!")
        
        self.conn.close()

def main():
    processor = EmailProcessor()
    processor.run()

if __name__ == '__main__':
    main()
