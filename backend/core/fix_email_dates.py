#!/usr/bin/env python3
"""
fix_email_dates.py

Fixes email date formats by converting text dates to proper ISO format
Runs on both emails.db and bensley_master.db
"""

import sqlite3
from pathlib import Path
from email.utils import parsedate_to_datetime
from datetime import datetime

class DateFixer:
    def __init__(self):
        self.emails_db = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/emails.db"
        self.master_db = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
    
    def parse_email_date(self, date_string):
        """Parse various email date formats to ISO format"""
        if not date_string:
            return None
        
        try:
            # Try parsing as email date format
            dt = parsedate_to_datetime(date_string)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
        
        try:
            # Try as ISO format already
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
        
        # If all fails, return None
        return None
    
    def fix_emails_db(self):
        """Fix dates in emails.db"""
        print("\n🔧 Fixing dates in emails.db...")
        
        conn = sqlite3.connect(self.emails_db)
        cursor = conn.cursor()
        
        # Get all emails with text dates
        cursor.execute("""
            SELECT email_id, date_sent
            FROM emails
            WHERE date_sent IS NOT NULL
        """)
        
        emails = cursor.fetchall()
        fixed_count = 0
        
        for email_id, date_sent in emails:
            # Parse to ISO format
            iso_date = self.parse_email_date(date_sent)
            
            if iso_date and iso_date != date_sent:
                cursor.execute("""
                    UPDATE emails 
                    SET date_sent = ?
                    WHERE email_id = ?
                """, (iso_date, email_id))
                fixed_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ Fixed {fixed_count} dates in emails.db")
        return fixed_count
    
    def fix_master_db(self):
        """Fix dates in bensley_master.db"""
        print("\n🔧 Fixing dates in bensley_master.db...")
        
        conn = sqlite3.connect(self.master_db)
        cursor = conn.cursor()
        
        # Get all emails with text dates
        cursor.execute("""
            SELECT email_id, date
            FROM emails
            WHERE date IS NOT NULL
        """)
        
        emails = cursor.fetchall()
        fixed_count = 0
        
        for email_id, date_val in emails:
            # Parse to ISO format
            iso_date = self.parse_email_date(date_val)
            
            if iso_date and iso_date != date_val:
                cursor.execute("""
                    UPDATE emails 
                    SET date = ?
                    WHERE email_id = ?
                """, (iso_date, email_id))
                fixed_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ Fixed {fixed_count} dates in bensley_master.db")
        return fixed_count
    
    def verify_fixes(self):
        """Verify dates are now sortable"""
        print("\n✅ Verifying date fixes...")
        
        conn = sqlite3.connect(self.master_db)
        cursor = conn.cursor()
        
        # Get most recent emails (should now sort correctly)
        cursor.execute("""
            SELECT sender_email, subject, date
            FROM emails
            ORDER BY date DESC
            LIMIT 5
        """)
        
        print("\n📧 Most recent emails (by date):")
        print("-"*70)
        for sender, subject, date in cursor.fetchall():
            print(f"{date}: {subject[:50]}")
        
        conn.close()
    
    def run(self):
        """Main fixing process"""
        print("="*70)
        print("EMAIL DATE FIXER")
        print("="*70)
        print("\nConverting text dates to ISO format for proper sorting...")
        
        # Fix both databases
        emails_fixed = self.fix_emails_db()
        master_fixed = self.fix_master_db()
        
        # Verify
        self.verify_fixes()
        
        print("\n" + "="*70)
        print("DATE FIXING COMPLETE")
        print("="*70)
        print(f"✅ Fixed {emails_fixed} dates in emails.db")
        print(f"✅ Fixed {master_fixed} dates in bensley_master.db")
        print("\n💡 Dates are now properly sortable!")

def main():
    fixer = DateFixer()
    fixer.run()

if __name__ == '__main__':
    main()
