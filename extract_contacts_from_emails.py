#!/usr/bin/env python3
"""
extract_contacts_from_emails.py

Extracts contacts from emails and stores them
Does NOT try to guess clients - that's manual in Excel
Just focuses on: contact email → project patterns
"""

import sqlite3
import os
from collections import Counter

class ContactExtractor:
    def __init__(self):
        self.master_db = os.path.expanduser('~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db')
        self.conn = sqlite3.connect(self.master_db)
        self.cursor = self.conn.cursor()
        
        # Ignore internal emails
        self.ignore_domains = ['bensley.com', 'bensley.co.id']
    
    def extract_contacts_from_emails(self):
        """Extract unique external contacts from emails"""
        print("\n👥 Extracting contacts from emails...")
        
        self.cursor.execute("""
            SELECT 
                sender_email,
                sender_name,
                COUNT(*) as email_count
            FROM emails
            WHERE sender_email NOT LIKE '%bensley.com%' 
              AND sender_email NOT LIKE '%bensley.co.id%'
              AND sender_email IS NOT NULL
            GROUP BY sender_email
            ORDER BY email_count DESC
        """)
        
        contacts = self.cursor.fetchall()
        
        print(f"   ✅ Found {len(contacts)} unique external contacts")
        
        return contacts
    
    def store_contacts(self, contacts):
        """Store contacts without trying to assign clients"""
        print("\n💾 Storing contacts...")
        
        # Create a simple contacts_only table if it doesn't exist
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts_only (
                contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                email_count INTEGER DEFAULT 0,
                first_seen DATE,
                last_seen DATE,
                notes TEXT
            )
        """)
        
        contacts_added = 0
        
        for email, name, count in contacts:
            # Extract name from email if no name provided
            if not name:
                name_part = email.split('@')[0]
                name = ' '.join(word.capitalize() for word in name_part.replace('.', ' ').split())
            
            try:
                self.cursor.execute("""
                    INSERT OR REPLACE INTO contacts_only (email, name, email_count, notes)
                    VALUES (?, ?, ?, ?)
                """, (email, name, count, 'Auto-extracted from emails'))
                
                contacts_added += 1
            except Exception as e:
                print(f"   ⚠️  Error adding {email}: {e}")
        
        self.conn.commit()
        
        print(f"   ✅ Stored {contacts_added} contacts")
        
        return contacts_added
    
    def show_top_contacts(self):
        """Show the most active contacts"""
        print("\n📊 TOP CONTACTS BY EMAIL VOLUME:")
        print("-"*70)
        
        self.cursor.execute("""
            SELECT email, name, email_count
            FROM contacts_only
            ORDER BY email_count DESC
            LIMIT 15
        """)
        
        print(f"{'Email':<40} {'Name':<25} {'Emails':>5}")
        print("-"*70)
        
        for email, name, count in self.cursor.fetchall():
            email_short = email[:38] if len(email) <= 40 else email[:37] + '...'
            name_short = (name or 'Unknown')[:23]
            print(f"{email_short:<40} {name_short:<25} {count:>5}")
    
    def run(self):
        """Main extraction process"""
        print("="*70)
        print("EXTRACTING CONTACTS (NOT CLIENTS)")
        print("="*70)
        print("\nNote: This extracts contact emails only.")
        print("Client assignment is done manually via Excel.")
        
        # Extract contacts
        contacts = self.extract_contacts_from_emails()
        
        # Store them
        contacts_added = self.store_contacts(contacts)
        
        # Show summary
        self.show_top_contacts()
        
        print("\n" + "="*70)
        print("EXTRACTION COMPLETE")
        print("="*70)
        print(f"✅ Stored {contacts_added} contacts")
        print("\n💡 Next step: Run pattern_learner.py to learn contact→project patterns")
        
        self.conn.close()

def main():
    extractor = ContactExtractor()
    extractor.run()

if __name__ == '__main__':
    main()
