#!/usr/bin/env python3
"""
Re-link ALL processed emails (not just 'proposal' category) to proposals
Because ANY email mentioning a proposal should be linked, regardless of category!
"""
import sqlite3
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def relink_all():
    db_path = os.getenv('DATABASE_PATH', 'database/bensley_master.db')
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all proposals
    cursor.execute("SELECT proposal_id, project_code, project_name FROM proposals ORDER BY proposal_id")
    proposals = [dict(row) for row in cursor.fetchall()]
    print(f"Loaded {len(proposals)} proposals\n")
    
    # Get ALL processed emails that have 0 or few links
    cursor.execute("""
        SELECT e.email_id, e.category, e.subject, e.sender_email, e.body_full,
               (SELECT COUNT(*) FROM email_proposal_links epl WHERE epl.email_id = e.email_id) as current_links
        FROM emails e
        WHERE e.processed = 1 
          AND e.category != 'junk'
          AND e.category != 'administrative'
        ORDER BY current_links ASC, e.email_id DESC
    """)
    emails = [dict(row) for row in cursor.fetchall()]
    print(f"Checking {len(emails)} emails for proposal mentions...\n")
    
    # Build full proposal list (ALL 87!)
    proposal_list = "\n".join([
        f"- {p['project_code']}: {p['project_name']}"
        for p in proposals
    ])
    
    total_new_links = 0
    emails_updated = 0
    
    for i, email in enumerate(emails):
        if i % 50 == 0:
            print(f"Progress: {i}/{len(emails)}")
        
        prompt = f"""Which proposals is this email related to?

Email:
From: {email['sender_email']}
Subject: {email['subject']}
Body: {email['body_full'][:800] if email['body_full'] else ''}

Proposals:
{proposal_list}

Return ONLY the project codes (e.g. BK-033, BK-008) as a comma-separated list.
If not related to any, return "NONE"."""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=100
            )
            
            result = response.choices[0].message.content.strip()
            
            if result != "NONE" and result:
                codes = [code.strip() for code in result.split(',')]
                
                links_added = 0
                for code in codes:
                    for p in proposals:
                        if p['project_code'] == code:
                            cursor.execute("""
                                INSERT OR IGNORE INTO email_proposal_links
                                (email_id, proposal_id, confidence_score, auto_linked, created_at)
                                VALUES (?, ?, ?, 1, datetime('now'))
                            """, (email['email_id'], p['proposal_id'], 0.8))
                            
                            if cursor.rowcount > 0:
                                links_added += 1
                                total_new_links += 1
                                print(f"  + Email {email['email_id']} [{email['category']}] → {code}: {p['project_name'][:40]}")
                            break
                
                if links_added > 0:
                    emails_updated += 1
                    
        except Exception as e:
            print(f"ERROR on email {email['email_id']}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Added {total_new_links} new links across {emails_updated} emails")

if __name__ == '__main__':
    relink_all()
