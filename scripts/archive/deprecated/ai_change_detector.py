#!/usr/bin/env python3
"""
AI-Powered Change Detection System

Monitors incoming emails and detects changes to project data:
- Fee changes
- Scope changes
- Timeline changes
- Client contact changes

Automatically updates database when changes are detected.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from openai import OpenAI

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


class AIChangeDetector:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Initialize OpenAI
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY required")

        self.client = OpenAI(api_key=api_key)

    def process_incoming_email(self, email_id: int):
        """Process a single email and detect any changes to project data"""

        # Get email
        email = self._get_email(email_id)
        if not email:
            return None

        # Step 1: Use AI to extract structured data from email
        extracted_data = self._extract_data_from_email(email)

        if not extracted_data or not extracted_data.get('project_code'):
            print(f"   ⚠️  No project code found in email")
            return None

        project_code = extracted_data['project_code']
        print(f"\n   📊 Found project: {project_code}")

        # Step 2: Get current project data from database
        current_project = self._get_project_data(project_code)

        if not current_project:
            print(f"   ⚠️  Project {project_code} not found in database")
            # Could suggest creating new project here
            return None

        # Step 3: Compare extracted data with database
        changes = self._detect_changes(current_project, extracted_data)

        if not changes:
            print(f"   ✅ No changes detected")
            return None

        # Step 4: Create change suggestions
        suggestion_id = self._create_change_suggestion(
            email_id,
            project_code,
            current_project,
            extracted_data,
            changes
        )

        print(f"   🔄 Detected {len(changes)} change(s):")
        for change in changes:
            print(f"      • {change['field']}: {change['old_value']} → {change['new_value']}")

        return suggestion_id

    def _extract_data_from_email(self, email: Dict) -> Optional[Dict]:
        """Use AI to extract structured data from email"""

        email_text = f"""
Subject: {email['subject']}
From: {email['sender_email']}
Date: {email['date']}

Body:
{email['body_full'] or email['snippet'] or 'No content'}
"""

        prompt = f"""You are analyzing a business email to extract project-related data.

Email:
{email_text}

Extract ALL structured data you can find:
1. Project code (format: BK-XXX or similar)
2. Financial data (fees, budgets, costs)
3. Timeline data (deadlines, start dates, milestones)
4. Scope data (what's being built, deliverables)
5. Client information (names, companies, contacts)
6. Status updates (active, on hold, completed)

Respond in JSON format:
{{
    "project_code": "BK-XXX or null",
    "financial": {{
        "fee": 150000,
        "currency": "USD",
        "payment_terms": "...",
        "mentioned_amounts": [...]
    }},
    "timeline": {{
        "deadline": "2025-12-31",
        "start_date": "2025-01-15",
        "milestones": ["..."]
    }},
    "scope": {{
        "description": "...",
        "deliverables": ["..."],
        "area_sqm": 5000
    }},
    "client": {{
        "name": "...",
        "company": "...",
        "contact_email": "..."
    }},
    "status": "active|on_hold|completed|null",
    "confidence": 85
}}

If you can't find a field, set it to null. Only include data explicitly mentioned.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a business intelligence assistant that extracts structured data from emails."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for accuracy
                response_format={"type": "json_object"}
            )

            data = json.loads(response.choices[0].message.content)
            return data

        except Exception as e:
            print(f"   ⚠️  AI extraction failed: {e}")
            return None

    def _get_email(self, email_id: int) -> Optional[Dict]:
        """Get email from database"""
        self.cursor.execute("""
            SELECT * FROM emails WHERE email_id = ?
        """, (email_id,))

        row = self.cursor.fetchone()
        return dict(row) if row else None

    def _get_project_data(self, project_code: str) -> Optional[Dict]:
        """Get current project data from database"""
        self.cursor.execute("""
            SELECT * FROM projects WHERE project_code = ?
        """, (project_code,))

        row = self.cursor.fetchone()
        return dict(row) if row else None

    def _detect_changes(self, current: Dict, extracted: Dict) -> List[Dict]:
        """Compare current database values with extracted email data"""
        changes = []

        # Financial changes
        if extracted.get('financial', {}).get('fee'):
            extracted_fee = extracted['financial']['fee']
            current_fee = current.get('project_value') or current.get('fee_usd')

            if current_fee and abs(extracted_fee - current_fee) > 1:  # Allow $1 difference
                changes.append({
                    'field': 'fee',
                    'old_value': f"${current_fee:,.0f}",
                    'new_value': f"${extracted_fee:,.0f}",
                    'database_field': 'project_value',
                    'update_value': extracted_fee,
                    'severity': 'high'
                })

        # Timeline changes
        if extracted.get('timeline', {}).get('deadline'):
            extracted_deadline = extracted['timeline']['deadline']
            current_deadline = current.get('deadline') or current.get('target_completion')

            if current_deadline and extracted_deadline != current_deadline:
                changes.append({
                    'field': 'deadline',
                    'old_value': current_deadline,
                    'new_value': extracted_deadline,
                    'database_field': 'deadline',
                    'update_value': extracted_deadline,
                    'severity': 'medium'
                })

        # Status changes
        if extracted.get('status'):
            extracted_status = extracted['status']
            current_status = current.get('status')

            if current_status and extracted_status != current_status:
                changes.append({
                    'field': 'status',
                    'old_value': current_status,
                    'new_value': extracted_status,
                    'database_field': 'status',
                    'update_value': extracted_status,
                    'severity': 'high'
                })

        # Scope changes
        if extracted.get('scope', {}).get('area_sqm'):
            extracted_area = extracted['scope']['area_sqm']
            current_area = current.get('area_sqm')

            if current_area and abs(extracted_area - current_area) > 10:
                changes.append({
                    'field': 'area_sqm',
                    'old_value': f"{current_area:,.0f} sqm",
                    'new_value': f"{extracted_area:,.0f} sqm",
                    'database_field': 'area_sqm',
                    'update_value': extracted_area,
                    'severity': 'medium'
                })

        # Client contact changes
        if extracted.get('client', {}).get('contact_email'):
            extracted_email = extracted['client']['contact_email']
            current_email = current.get('client_email')

            if current_email and extracted_email != current_email:
                changes.append({
                    'field': 'client_email',
                    'old_value': current_email,
                    'new_value': extracted_email,
                    'database_field': 'client_email',
                    'update_value': extracted_email,
                    'severity': 'low'
                })

        return changes

    def _create_change_suggestion(
        self,
        email_id: int,
        project_code: str,
        current: Dict,
        extracted: Dict,
        changes: List[Dict]
    ) -> str:
        """Create a suggestion in the queue for user to approve"""
        import uuid
        suggestion_id = str(uuid.uuid4())

        proposed_fix = {
            'action': 'update_project_data',
            'project_code': project_code,
            'email_id': email_id,
            'changes': changes,
            'extracted_data': extracted
        }

        evidence = {
            'email_subject': current.get('subject', 'N/A'),
            'changes_count': len(changes),
            'severity': max([c['severity'] for c in changes], key=lambda x: {'high': 3, 'medium': 2, 'low': 1}[x])
        }

        confidence = extracted.get('confidence', 50) / 100.0

        # High severity changes go to urgent bucket
        severity = 'high' if any(c['severity'] == 'high' for c in changes) else 'medium'
        bucket = 'urgent' if severity == 'high' else 'needs_attention'

        self.cursor.execute("""
            INSERT INTO ai_suggestions_queue (
                id, project_code, suggestion_type, proposed_fix, evidence,
                confidence, impact_type, impact_summary,
                severity, bucket, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
        """, (
            suggestion_id,
            project_code,
            'project_data_change',
            json.dumps(proposed_fix),
            json.dumps(evidence),
            confidence,
            'data_quality',
            f"Detected {len(changes)} change(s) to project data",
            severity,
            bucket
        ))

        self.conn.commit()
        return suggestion_id

    def auto_apply_changes(self, suggestion_id: str):
        """Auto-apply approved changes to database"""

        # Get suggestion
        self.cursor.execute("""
            SELECT * FROM ai_suggestions_queue WHERE id = ?
        """, (suggestion_id,))

        suggestion = self.cursor.fetchone()
        if not suggestion:
            return False

        proposed_fix = json.loads(suggestion['proposed_fix'])
        changes = proposed_fix['changes']
        project_code = proposed_fix['project_code']

        # Apply each change
        for change in changes:
            self.cursor.execute(f"""
                UPDATE projects
                SET {change['database_field']} = ?
                WHERE project_code = ?
            """, (change['update_value'], project_code))

        # Mark suggestion as applied
        self.cursor.execute("""
            UPDATE ai_suggestions_queue
            SET status = 'approved'
            WHERE id = ?
        """, (suggestion_id,))

        self.conn.commit()
        return True

    def process_recent_emails(self, limit=20):
        """Process recent emails for changes"""
        print("=" * 80)
        print("🔍 AI CHANGE DETECTION")
        print("=" * 80)

        # Get recent emails (last 30 days)
        self.cursor.execute("""
            SELECT email_id, subject, date
            FROM emails
            WHERE date > date('now', '-30 days')
            ORDER BY date DESC
            LIMIT ?
        """, (limit,))

        emails = self.cursor.fetchall()
        print(f"\nAnalyzing {len(emails)} recent emails for changes...\n")

        suggestions_created = 0

        for i, email in enumerate(emails, 1):
            print(f"[{i}/{len(emails)}] {email['subject'][:60]}...")

            suggestion_id = self.process_incoming_email(email['email_id'])
            if suggestion_id:
                suggestions_created += 1

        print(f"\n✅ Created {suggestions_created} change suggestions")
        return suggestions_created

    def close(self):
        self.conn.close()


def main():
    print("🤖 AI CHANGE DETECTION SYSTEM")
    print("Analyzing emails for project data changes\n")

    detector = AIChangeDetector()

    try:
        # Process recent emails
        suggestions = detector.process_recent_emails(limit=20)

        print("\n" + "=" * 80)
        print(f"✅ COMPLETE! Created {suggestions} change suggestions")
        print("=" * 80)
        print("\nReview suggestions: python3 review_changes.py")

    finally:
        detector.close()


if __name__ == "__main__":
    main()
