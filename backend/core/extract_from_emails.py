#!/usr/bin/env python3
"""
extract_from_emails.py

Extracts structured data from linked emails:
- RFIs (request for information)
- Action items (tasks, assignments)
- Status changes
- Deadlines and dates

Updated: Oct 24, 2025 - Works with current email_project_links structure
"""

import sqlite3
import re
from pathlib import Path
from datetime import datetime, timedelta

class EmailExtractor:
    def __init__(self):
        self.master_db = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
        self.conn = sqlite3.connect(self.master_db)
        self.cursor = self.conn.cursor()
        
        # Patterns for extraction
        self.rfi_patterns = [
            r'\bRFI[\s-]?#?(\d+)',
            r'\bRequest for Information[\s-]?#?(\d+)',
            r'\b(RFI|rfi)[\s:]+([\w\s\-,]+?)(?:\s*-\s*Due:?\s*(.+?))?$'
        ]
        
        self.date_patterns = [
            r'due\s+(?:date\s+)?(?:by\s+)?([A-Za-z]+\s+\d+)',
            r'deadline\s+(?:is\s+)?([A-Za-z]+\s+\d+)',
            r'by\s+([A-Za-z]+\s+\d+)',
            r'(\d{1,2}/\d{1,2}/\d{2,4})',
            r'([A-Za-z]+\s+\d+,?\s+\d{4})'
        ]
        
        self.action_keywords = [
            'please send', 'please provide', 'please submit',
            'need', 'require', 'must', 'should',
            'can you', 'could you', 'would you',
            'awaiting', 'waiting for', 'need to'
        ]
        
        self.phase_keywords = {
            'concept': ['concept', 'conceptual', 'preliminary'],
            'schematic': ['schematic', 'sd phase', 'sd submittal'],
            'DD': ['design development', 'dd phase', 'dd submittal', 'detailed design'],
            'CD': ['construction documents', 'cd phase', 'cd submittal', 'working drawings'],
            'construction': ['construction', 'building', 'contractor']
        }
        
        self.stats = {
            'emails_processed': 0,
            'rfis_found': 0,
            'actions_found': 0,
            'dates_found': 0,
            'status_changes': 0
        }
    
    def extract_rfi_from_subject(self, subject):
        """Extract RFI number and details from subject line"""
        if not subject:
            return None
        
        subject_lower = subject.lower()
        
        # Check if it's an RFI
        if 'rfi' not in subject_lower:
            return None
        
        rfi_data = {}
        
        # Extract RFI number
        for pattern in self.rfi_patterns:
            match = re.search(pattern, subject, re.IGNORECASE)
            if match:
                if len(match.groups()) >= 1:
                    rfi_data['rfi_number'] = match.group(1)
                break
        
        # Rest of subject is the RFI subject
        rfi_cleaned = re.sub(r'\bRFI[\s-]?#?\d+\s*[-:]?\s*', '', subject, flags=re.IGNORECASE)
        rfi_data['subject'] = rfi_cleaned.strip()
        
        return rfi_data if rfi_data else None
    
    def extract_dates(self, text):
        """Extract dates from text"""
        if not text:
            return []
        
        dates = []
        
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1)
                parsed = self.parse_date_string(date_str)
                if parsed:
                    dates.append(parsed)
        
        return dates
    
    def parse_date_string(self, date_str):
        """Try to parse various date formats"""
        formats = [
            '%B %d',
            '%b %d',
            '%m/%d/%Y',
            '%m/%d/%y',
            '%B %d, %Y',
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                if parsed.year == 1900:
                    parsed = parsed.replace(year=datetime.now().year)
                return parsed.date()
            except:
                continue
        
        return None
    
    def extract_action_items(self, text, sender_email):
        """Extract potential action items from text"""
        if not text:
            return []
        
        actions = []
        sentences = text.split('.')
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            for keyword in self.action_keywords:
                if keyword in sentence_lower:
                    action = sentence.strip()
                    dates = self.extract_dates(sentence)
                    due_date = dates[0] if dates else None
                    
                    actions.append({
                        'description': action[:200],
                        'due_date': due_date,
                        'assigned_by': sender_email
                    })
                    break
        
        return actions
    
    def detect_phase_change(self, text):
        """Detect project phase mentions"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        for phase, keywords in self.phase_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return phase
        
        return None
    
    def process_linked_emails(self):
        """Process all emails linked to projects"""
        print("="*70)
        print("EXTRACTING DATA FROM LINKED EMAILS")
        print("="*70)
        
        # Get all linked emails with project info
        self.cursor.execute("""
            SELECT 
                e.email_id,
                e.message_id,
                e.subject,
                e.snippet,
                e.sender_email,
                e.date,
                epl.project_id,
                epl.project_code,
                p.project_title
            FROM email_project_links epl
            JOIN emails e ON epl.email_id = e.email_id
            LEFT JOIN projects p ON epl.project_id = p.project_id
            WHERE epl.project_code IS NOT NULL
            ORDER BY e.date DESC
        """)
        
        emails = self.cursor.fetchall()
        print(f"\n📧 Processing {len(emails)} linked emails...")
        
        if not emails:
            print("\n⚠️  No linked emails found!")
            print("   Make sure email_project_links has project_code populated.")
            return
        
        for row in emails:
            email_id, message_id, subject, snippet, sender, date, project_id, project_code, project_title = row
            
            text = f"{subject or ''} {snippet or ''}"
            self.stats['emails_processed'] += 1
            
            # Extract RFIs
            rfi_data = self.extract_rfi_from_subject(subject)
            if rfi_data:
                dates = self.extract_dates(snippet or '')
                due_date = dates[0] if dates else None
                
                try:
                    self.cursor.execute("""
                        INSERT OR IGNORE INTO rfis 
                        (project_id, project_code, rfi_number, subject, date_sent, date_due, 
                         sender_email, status, extracted_from_email_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?)
                    """, (project_id, project_code, rfi_data.get('rfi_number'), 
                          rfi_data.get('subject'), date, due_date, sender, email_id))
                    
                    if self.cursor.rowcount > 0:
                        self.stats['rfis_found'] += 1
                except Exception as e:
                    pass
            
            # Extract action items
            actions = self.extract_action_items(text, sender)
            for action in actions:
                try:
                    self.cursor.execute("""
                        INSERT INTO action_items_tracking 
                        (project_id, project_code, description, assigned_by, due_date, 
                         status, source_email_id)
                        VALUES (?, ?, ?, ?, ?, 'pending', ?)
                    """, (project_id, project_code, action['description'], 
                          action['assigned_by'], action['due_date'], email_id))
                    
                    self.stats['actions_found'] += 1
                except:
                    pass
            
            # Detect phase changes
            phase = self.detect_phase_change(text)
            if phase:
                try:
                    self.cursor.execute("""
                        INSERT INTO project_status_tracking 
                        (project_id, project_code, status_date, phase, current_activity,
                         extracted_from_email, source_email_id)
                        VALUES (?, ?, ?, ?, ?, 1, ?)
                    """, (project_id, project_code, date, phase, subject, email_id))
                    
                    self.stats['status_changes'] += 1
                except:
                    pass
            
            # Log communication
            try:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO communication_log
                    (project_id, project_code, comm_date, comm_type, subject,
                     participants, email_id)
                    VALUES (?, ?, ?, 'email', ?, ?, ?)
                """, (project_id, project_code, date, subject, sender, email_id))
            except:
                pass
        
        self.conn.commit()
        
        # Show summary
        print("\n" + "="*70)
        print("EXTRACTION COMPLETE")
        print("="*70)
        print(f"\n✅ Emails processed: {self.stats['emails_processed']}")
        print(f"✅ RFIs found: {self.stats['rfis_found']}")
        print(f"✅ Action items found: {self.stats['actions_found']}")
        print(f"✅ Phase changes detected: {self.stats['status_changes']}")
        
        # Show some examples
        if self.stats['rfis_found'] > 0:
            print("\n📋 Sample RFIs extracted:")
            self.cursor.execute("""
                SELECT 
                    r.project_code,
                    r.rfi_number,
                    r.subject,
                    r.date_due
                FROM rfis r
                ORDER BY r.date_sent DESC
                LIMIT 5
            """)
            
            for code, num, subj, due in self.cursor.fetchall():
                due_str = due if due else 'No due date'
                print(f"   {code} - RFI {num}: {subj[:40]} (Due: {due_str})")
        
        if self.stats['actions_found'] > 0:
            print("\n✅ Sample Action Items:")
            self.cursor.execute("""
                SELECT 
                    a.project_code,
                    a.description,
                    a.due_date
                FROM action_items_tracking a
                ORDER BY a.created_at DESC
                LIMIT 5
            """)
            
            for code, desc, due in self.cursor.fetchall():
                due_str = due if due else 'TBD'
                print(f"   {code}: {desc[:50]} (Due: {due_str})")
        
        self.conn.close()
        
        print("\n✅ Data ready for reporting!")
        print("\nNext: Run python3 project_reports.py")

def main():
    extractor = EmailExtractor()
    extractor.process_linked_emails()

if __name__ == '__main__':
    main()
