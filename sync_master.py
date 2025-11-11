#!/usr/bin/env python3
"""
sync_master.py - FINAL VERSION with correct email columns
"""

import sqlite3
import os
from datetime import datetime

class MasterSync:
    def __init__(self, base_path):
        self.base_path = base_path
        self.master_db = os.path.join(base_path, 'bensley_master.db')
        
        self.sources = {
            'proposals': os.path.join(base_path, 'proposals.db'),
            'contracts': os.path.join(base_path, 'active_contracts.db'),
            'emails': os.path.join(base_path, 'emails.db'),
            'clients': os.path.join(base_path, 'clients.db')
        }
        
        self.conn = None
        self.cursor = None
        self.stats = {
            'projects_inserted': 0,
            'projects_updated': 0,
            'clients_synced': 0,
            'contacts_synced': 0,
            'invoices_synced': 0,
            'emails_synced': 0,
            'errors': []
        }
    
    def connect(self):
        self.conn = sqlite3.connect(self.master_db)
        self.cursor = self.conn.cursor()
        
        for name, path in self.sources.items():
            if os.path.exists(path):
                self.cursor.execute(f"ATTACH DATABASE '{path}' AS {name}_db")
                print(f"   ✅ Attached {name}.db")
            else:
                print(f"   ⚠️  {name}.db not found")
                self.stats['errors'].append(f"{name}.db not found")
    
    def sync_clients(self):
        print("\n📊 Syncing clients...")
        
        try:
            # Simple INSERT OR REPLACE
            self.cursor.execute("""
                INSERT OR REPLACE INTO clients (client_id, company_name, country, industry, notes)
                SELECT client_id, company_name, country, industry, notes
                FROM clients_db.clients
            """)
            self.stats['clients_synced'] = self.cursor.rowcount
            print(f"   ✅ Synced {self.stats['clients_synced']} clients")
            
            # Sync aliases
            self.cursor.execute("""
                INSERT OR IGNORE INTO client_aliases 
                (client_id, alias, alias_type, confidence, created_by)
                SELECT client_id, alias, alias_type, confidence, created_by
                FROM clients_db.client_aliases
            """)
            print(f"   ✅ Synced {self.cursor.rowcount} aliases")
            
            # Sync contacts
            self.cursor.execute("""
                INSERT OR REPLACE INTO contacts (contact_id, client_id, email, name, role, phone, notes)
                SELECT contact_id, client_id, email, name, role, phone, notes
                FROM clients_db.contacts
            """)
            self.stats['contacts_synced'] = self.cursor.rowcount
            print(f"   ✅ Synced {self.stats['contacts_synced']} contacts")
            
        except Exception as e:
            error_msg = f"Error syncing clients: {e}"
            print(f"   ❌ {error_msg}")
            self.stats['errors'].append(error_msg)
    
    def sync_projects_from_proposals(self):
        print("\n📋 Syncing proposals...")
        
        try:
            self.cursor.execute("""
                INSERT OR IGNORE INTO projects (
                    project_code, project_title, client_id, source_db, status,
                    country, total_fee_usd, date_created, notes, source_ref
                )
                SELECT 
                    p.project_code,
                    p.project_name,
                    c.client_id,
                    'proposals',
                    p.current_status,
                    p.country,
                    p.project_value,
                    p.date_created,
                    p.remarks,
                    'proposals.db:projects:' || p.project_code
                FROM proposals_db.projects p
                LEFT JOIN clients c ON c.company_name = p.contact_company
            """)
            
            count = self.cursor.rowcount
            self.stats['projects_inserted'] += count
            print(f"   ✅ Synced {count} proposals")
            
        except Exception as e:
            error_msg = f"Error syncing proposals: {e}"
            print(f"   ❌ {error_msg}")
            self.stats['errors'].append(error_msg)
    
    def sync_projects_from_contracts(self):
        print("\n📝 Syncing active contracts...")
        
        try:
            self.cursor.execute("""
                INSERT OR IGNORE INTO projects (
                    project_code, project_title, source_db, status, project_type,
                    total_fee_usd, contract_term_months, contract_expiry_date,
                    notes, source_ref
                )
                SELECT 
                    ac.project_code,
                    ac.project_title,
                    'contracts',
                    ac.status,
                    ac.project_type,
                    ac.total_fee_usd,
                    ac.contract_term_months,
                    ac.contract_expiry_date,
                    'Client: ' || COALESCE(ac.client_name, 'Unknown') || ' | Contact: ' || COALESCE(ac.contact_person, 'Unknown'),
                    'active_contracts.db:active_contracts:' || ac.contract_id
                FROM contracts_db.active_contracts ac
            """)
            
            count = self.cursor.rowcount
            self.stats['projects_updated'] += count
            print(f"   ✅ Synced {count} active contracts")
            
        except Exception as e:
            error_msg = f"Error syncing contracts: {e}"
            print(f"   ❌ {error_msg}")
            self.stats['errors'].append(error_msg)
    
    def sync_invoices(self):
        print("\n💰 Syncing invoices...")
        
        try:
            self.cursor.execute("""
                INSERT OR REPLACE INTO invoices (
                    project_id, invoice_number, description, 
                    invoice_amount, payment_amount, invoice_date,
                    status, source_ref
                )
                SELECT 
                    p.project_id,
                    i.invoice_number,
                    i.description,
                    i.invoice_amount,
                    i.payment_amount,
                    i.invoice_date,
                    CASE 
                        WHEN i.payment_amount >= i.invoice_amount THEN 'Paid'
                        WHEN i.payment_amount > 0 THEN 'Partial'
                        ELSE 'Unpaid'
                    END,
                    'active_contracts.db:invoices:' || i.invoice_id
                FROM contracts_db.invoices i
                JOIN projects p ON p.project_code = i.project_code
            """)
            
            self.stats['invoices_synced'] = self.cursor.rowcount
            print(f"   ✅ Synced {self.stats['invoices_synced']} invoices")
            
        except Exception as e:
            error_msg = f"Error syncing invoices: {e}"
            print(f"   ❌ {error_msg}")
            self.stats['errors'].append(error_msg)
    
    def sync_emails(self):
        print("\n✉️  Syncing emails...")
        
        try:
            # Use correct column names from emails.db
            self.cursor.execute("""
                INSERT OR IGNORE INTO emails (
                    message_id, thread_id, date, sender_email, sender_name,
                    subject, snippet, has_attachments, processed, source_ref
                )
                SELECT 
                    e.message_id,
                    e.thread_id,
                    e.date_sent,
                    e.sender_email,
                    e.sender_name,
                    e.subject,
                    SUBSTR(e.body_text, 1, 200),
                    e.has_attachments,
                    e.is_processed,
                    'emails.db:emails:' || e.email_id
                FROM emails_db.emails e
            """)
            
            self.stats['emails_synced'] = self.cursor.rowcount
            print(f"   ✅ Synced {self.stats['emails_synced']} emails")
            
        except Exception as e:
            error_msg = f"Error syncing emails: {e}"
            print(f"   ❌ {error_msg}")
            self.stats['errors'].append(error_msg)
    
    def log_sync_history(self):
        for source_name in ['proposals', 'contracts', 'emails', 'clients']:
            self.cursor.execute("""
                INSERT INTO sync_history (
                    source_db, sync_start, sync_end, 
                    records_processed, records_inserted, records_updated,
                    errors, status
                ) VALUES (?, datetime('now'), datetime('now'), 0, 0, 0, '', 'success')
            """, (f"{source_name}.db",))
    
    def run(self):
        print("="*70)
        print("SYNCING TO MASTER DATABASE")
        print("="*70)
        
        start_time = datetime.now()
        
        print("\n🔗 Connecting to databases...")
        self.connect()
        
        self.sync_clients()
        self.sync_projects_from_proposals()
        self.sync_projects_from_contracts()
        self.sync_invoices()
        self.sync_emails()
        
        self.log_sync_history()
        
        self.conn.commit()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "="*70)
        print("SYNC COMPLETE")
        print("="*70)
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"✅ Projects synced: {self.stats['projects_inserted'] + self.stats['projects_updated']}")
        print(f"✅ Clients synced: {self.stats['clients_synced']}")
        print(f"✅ Contacts synced: {self.stats['contacts_synced']}")
        print(f"✅ Invoices synced: {self.stats['invoices_synced']}")
        print(f"✅ Emails synced: {self.stats['emails_synced']}")
        
        if self.stats['errors']:
            print(f"\n⚠️  {len(self.stats['errors'])} errors:")
            for error in self.stats['errors']:
                print(f"   • {error}")
        else:
            print("\n🎉 All syncs completed successfully!")
        
        self.conn.close()

def main():
    base_path = os.path.expanduser('~/Desktop/BDS_SYSTEM/01_DATABASES')
    syncer = MasterSync(base_path)
    syncer.run()

if __name__ == '__main__':
    main()