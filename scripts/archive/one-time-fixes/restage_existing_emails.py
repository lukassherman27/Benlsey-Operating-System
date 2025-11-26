#!/usr/bin/env python3
"""
Re-stage the 296 existing processed emails to add stage field
"""
import sqlite3
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def restage_emails():
    db_path = os.getenv('DATABASE_PATH', 'database/bensley_master.db')
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all processed emails without stage
    cursor.execute("""
        SELECT email_id, category, subject, sender_email, body_full
        FROM emails
        WHERE processed = 1 AND (stage IS NULL OR stage = '')
        ORDER BY email_id DESC
    """)
    emails = [dict(row) for row in cursor.fetchall()]
    print(f"Found {len(emails)} emails to re-stage\n")
    
    api_calls = 0
    updated = 0
    
    for i, email in enumerate(emails):
        if i % 50 == 0:
            print(f"Progress: {i}/{len(emails)}")
        
        prompt = f"""Determine the business STAGE for this email:

STAGES:
- proposal: Pre-contract sales pipeline (trying to win the business)
- active: Post-contract project delivery (executing won projects)
- internal: Internal Bensley operations (payroll, accounting, admin)
- other: Other business lines (Shinta Mani, private projects, social media)

Email:
From: {email['sender_email']}
Subject: {email['subject']}
Body: {email['body_full'][:800] if email['body_full'] else ''}
Current category: {email['category']}

Return ONLY one word: the stage name."""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=20
            )
            
            stage = response.choices[0].message.content.strip().lower()
            api_calls += 1
            
            # Validate stage
            if stage not in ['proposal', 'active', 'internal', 'other']:
                stage = 'other'
            
            # Update email
            cursor.execute("""
                UPDATE emails
                SET stage = ?
                WHERE email_id = ?
            """, (stage, email['email_id']))
            updated += 1
            
            if i % 10 == 0:
                conn.commit()
                
        except Exception as e:
            print(f"ERROR on email {email['email_id']}: {e}")
    
    conn.commit()
    conn.close()
    
    cost = api_calls * 0.0025  # $0.0025 per call for staging
    print(f"\n✅ Re-staged {updated} emails")
    print(f"💰 API calls: {api_calls}, Cost: ${cost:.2f}")

if __name__ == '__main__':
    restage_emails()
