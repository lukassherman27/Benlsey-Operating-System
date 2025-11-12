#!/usr/bin/env python3
"""
pattern_learner.py

Analyzes existing emails to learn patterns for auto-linking
Builds intelligence from your historical email data
"""

import sqlite3
import os
import re
from collections import defaultdict, Counter

class PatternLearner:
    def __init__(self):
        self.master_db = os.path.expanduser('~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db')
        self.conn = sqlite3.connect(self.master_db)
        self.cursor = self.conn.cursor()
        
        self.patterns = {
            'sender_to_project': defaultdict(Counter),  # email -> project codes
            'domain_to_project': defaultdict(Counter),  # domain -> project codes
            'keyword_to_project': defaultdict(Counter), # keyword -> project codes
            'sender_to_client': defaultdict(set),       # email -> client names
        }
    
    def extract_project_codes(self, text):
        """Extract project codes from text (e.g., BK-057, 25 BK-001)"""
        if not text:
            return []
        
        # Pattern: optional year prefix + BK- + digits
        matches = re.findall(r'\b(?:\d{2}\s+)?BK-\d{3}\b', text, re.IGNORECASE)
        return [m.strip().upper() for m in matches]
    
    def extract_keywords(self, text, min_length=4):
        """Extract meaningful keywords from text"""
        if not text:
            return []
        
        # Remove common words
        stop_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have', 'been', 'will'}
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{' + str(min_length) + r',}\b', text.lower())
        return [w for w in words if w not in stop_words]
    
    def learn_from_existing_emails(self):
        """Analyze existing emails to learn patterns"""
        print("\n🧠 Learning patterns from existing emails...")
        
        # Get all emails with their content
        self.cursor.execute("""
            SELECT 
                email_id,
                sender_email,
                subject,
                snippet
            FROM emails
            WHERE sender_email NOT LIKE '%bensley.com%'
              AND sender_email NOT LIKE '%bensley.co.id%'
        """)
        
        emails_analyzed = 0
        project_codes_found = 0
        
        for email_id, sender_email, subject, snippet in self.cursor.fetchall():
            if not sender_email:
                continue
            
            emails_analyzed += 1
            domain = sender_email.split('@')[1] if '@' in sender_email else None
            
            # Combine subject and snippet
            text = f"{subject or ''} {snippet or ''}"
            
            # Extract project codes mentioned in email
            project_codes = self.extract_project_codes(text)
            
            if project_codes:
                project_codes_found += len(project_codes)
                
                for code in project_codes:
                    # Learn sender -> project pattern
                    self.patterns['sender_to_project'][sender_email][code] += 1
                    
                    # Learn domain -> project pattern
                    if domain:
                        self.patterns['domain_to_project'][domain][code] += 1
                    
                    # Extract keywords from this email
                    keywords = self.extract_keywords(text)
                    for keyword in keywords[:10]:  # Top 10 keywords
                        self.patterns['keyword_to_project'][keyword][code] += 1
        
        print(f"   ✅ Analyzed {emails_analyzed} client emails")
        print(f"   ✅ Found {project_codes_found} project code mentions")
        
        return emails_analyzed, project_codes_found
    
    def learn_client_associations(self):
        """Learn which email senders belong to which clients"""
        print("\n🏢 Learning sender→client associations...")
        
        # Get contacts and their clients
        self.cursor.execute("""
            SELECT 
                co.email,
                c.company_name,
                c.client_id
            FROM contacts co
            JOIN clients c ON co.client_id = c.client_id
        """)
        
        associations_learned = 0
        
        for email, company_name, client_id in self.cursor.fetchall():
            self.patterns['sender_to_client'][email].add(company_name)
            associations_learned += 1
        
        print(f"   ✅ Learned {associations_learned} sender→client associations")
        
        return associations_learned
    
    def save_patterns_to_db(self):
        """Save learned patterns to database for fast lookup"""
        print("\n💾 Saving patterns to database...")
        
        # Create patterns table if it doesn't exist
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_patterns (
                pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT,
                pattern_key TEXT,
                pattern_value TEXT,
                confidence REAL,
                occurrences INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(pattern_type, pattern_key, pattern_value)
            )
        """)
        
        patterns_saved = 0
        
        # Save sender -> project patterns
        for sender, projects in self.patterns['sender_to_project'].items():
            for project_code, count in projects.items():
                confidence = min(count / 10.0, 0.99)  # Max confidence 0.99
                
                self.cursor.execute("""
                    INSERT OR REPLACE INTO learned_patterns 
                    (pattern_type, pattern_key, pattern_value, confidence, occurrences)
                    VALUES (?, ?, ?, ?, ?)
                """, ('sender_to_project', sender, project_code, confidence, count))
                patterns_saved += 1
        
        # Save domain -> project patterns
        for domain, projects in self.patterns['domain_to_project'].items():
            for project_code, count in projects.items():
                confidence = min(count / 15.0, 0.95)  # Domain patterns slightly less confident
                
                self.cursor.execute("""
                    INSERT OR REPLACE INTO learned_patterns 
                    (pattern_type, pattern_key, pattern_value, confidence, occurrences)
                    VALUES (?, ?, ?, ?, ?)
                """, ('domain_to_project', domain, project_code, confidence, count))
                patterns_saved += 1
        
        # Save keyword -> project patterns (only strong ones)
        for keyword, projects in self.patterns['keyword_to_project'].items():
            for project_code, count in projects.items():
                if count >= 3:  # Only keywords mentioned 3+ times
                    confidence = min(count / 20.0, 0.85)  # Keywords less confident
                    
                    self.cursor.execute("""
                        INSERT OR REPLACE INTO learned_patterns 
                        (pattern_type, pattern_key, pattern_value, confidence, occurrences)
                        VALUES (?, ?, ?, ?, ?)
                    """, ('keyword_to_project', keyword, project_code, confidence, count))
                    patterns_saved += 1
        
        self.conn.commit()
        
        print(f"   ✅ Saved {patterns_saved} patterns")
        
        return patterns_saved
    
    def show_top_patterns(self):
        """Display the strongest patterns learned"""
        print("\n" + "="*70)
        print("TOP LEARNED PATTERNS")
        print("="*70)
        
        # Top sender patterns
        print("\n📧 Strongest sender→project patterns:")
        self.cursor.execute("""
            SELECT pattern_key, pattern_value, confidence, occurrences
            FROM learned_patterns
            WHERE pattern_type = 'sender_to_project'
            ORDER BY confidence DESC, occurrences DESC
            LIMIT 10
        """)
        
        for sender, project, conf, count in self.cursor.fetchall():
            print(f"   {sender[:35]:35} → {project}  (conf: {conf:.2f}, seen: {count}x)")
        
        # Top domain patterns
        print("\n🌐 Strongest domain→project patterns:")
        self.cursor.execute("""
            SELECT pattern_key, pattern_value, confidence, occurrences
            FROM learned_patterns
            WHERE pattern_type = 'domain_to_project'
            ORDER BY confidence DESC, occurrences DESC
            LIMIT 10
        """)
        
        for domain, project, conf, count in self.cursor.fetchall():
            print(f"   @{domain[:35]:34} → {project}  (conf: {conf:.2f}, seen: {count}x)")
        
        # Top keyword patterns
        print("\n🔑 Strongest keyword→project patterns:")
        self.cursor.execute("""
            SELECT pattern_key, pattern_value, confidence, occurrences
            FROM learned_patterns
            WHERE pattern_type = 'keyword_to_project'
            ORDER BY confidence DESC, occurrences DESC
            LIMIT 10
        """)
        
        for keyword, project, conf, count in self.cursor.fetchall():
            print(f"   '{keyword}' → {project}  (conf: {conf:.2f}, seen: {count}x)")
    
    def run(self):
        """Main learning process"""
        print("="*70)
        print("PATTERN LEARNING FROM HISTORICAL EMAILS")
        print("="*70)
        
        # Learn from emails
        emails_analyzed, codes_found = self.learn_from_existing_emails()
        
        # Learn client associations
        associations = self.learn_client_associations()
        
        # Save to database
        patterns_saved = self.save_patterns_to_db()
        
        # Show results
        self.show_top_patterns()
        
        print("\n" + "="*70)
        print("LEARNING COMPLETE")
        print("="*70)
        print(f"✅ Analyzed {emails_analyzed} emails")
        print(f"✅ Found {codes_found} project mentions")
        print(f"✅ Saved {patterns_saved} patterns")
        print("\n💡 These patterns will be used for automatic email linking!")
        
        self.conn.close()

def main():
    learner = PatternLearner()
    learner.run()

if __name__ == '__main__':
    main()
