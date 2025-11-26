#!/usr/bin/env python3
"""
Re-link the 18 proposal emails that were missed due to 20-proposal limit bug
"""
import sqlite3
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def relink_emails():
    db_path = os.getenv('DATABASE_PATH', 'database/bensley_master.db')
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all proposals
    cursor.execute("SELECT proposal_id, project_code, project_name FROM proposals ORDER BY proposal_id")
    proposals = [dict(row) for row in cursor.fetchall()]
    print(f"Loaded {len(proposals)} proposals")
    
    # Get unlinked proposal emails
    cursor.execute("""
        SELECT email_id, subject, sender_email, body_full
        FROM emails
        WHERE processed = 1 
          AND category = 'proposal'
          AND email_id NOT IN (SELECT email_id FROM email_proposal_links)
    """)
    emails = [dict(row) for row in cursor.fetchall()]
    print(f"Found {len(emails)} unlinked proposal emails\n")
    
    # Re-link each one
    total_links = 0
    for email in emails:
        # Build full proposal list (ALL 87!)
        proposal_list = "\n".join([
            f"- {p['project_code']}: {p['project_name']}"
            for p in proposals
        ])
        
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
                # Parse project codes
                codes = [code.strip() for code in result.split(',')]
                
                # Insert links
                for code in codes:
                    for p in proposals:
                        if p['project_code'] == code:
                            cursor.execute("""
                                INSERT OR IGNORE INTO email_proposal_links
                                (email_id, proposal_id, confidence_score, auto_linked, created_at)
                                VALUES (?, ?, ?, 1, datetime('now'))
                            """, (email['email_id'], p['proposal_id'], 0.8))
                            total_links += 1
                            print(f"✓ Email {email['email_id']} → {code}: {p['project_name'][:50]}")
                            break
            else:
                print(f"✗ Email {email['email_id']}: No matches")
                
        except Exception as e:
            print(f"ERROR on email {email['email_id']}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Added {total_links} new links")

if __name__ == '__main__':
    relink_emails()
