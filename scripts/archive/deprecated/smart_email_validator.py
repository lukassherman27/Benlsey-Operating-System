#!/usr/bin/env python3
"""
Smart Email Validator - AI-Powered Data Consistency Checker

This script:
1. Reads emails and extracts structured facts using Claude
2. Compares facts against database
3. Detects inconsistencies (email says X, database says Y)
4. Creates suggestions for review/approval
5. Human reviews and approves changes

Example inconsistencies it catches:
- Email: "5 people working on Rosewood" → DB: project status = "archived"
- Email: "Updated proposal to $850K" → DB: project_value = $720K
- Email: "Project completed last week" → DB: status = "active"
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
from openai import OpenAI

# Configuration
DB_PATH = Path(__file__).parent / "database" / "bensley_master.db"


class SmartEmailValidator:
    """AI-powered email validation and data consistency checking"""

    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

        # Initialize OpenAI client
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        self.client = OpenAI(api_key=api_key)

    def extract_facts_from_email(self, email_id: int) -> Dict[str, Any]:
        """Extract structured facts from email using GPT"""

        # Get email content AND linked projects
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT e.email_id, e.subject, e.sender_email, e.date, e.body_full, e.category,
                   epl.project_code
            FROM emails e
            LEFT JOIN email_project_links epl ON e.email_id = epl.email_id
            WHERE e.email_id = ?
        """, (email_id,))

        email = cursor.fetchone()
        if not email:
            return {"error": "Email not found"}

        email_dict = dict(email)
        linked_project_code = email_dict.get('project_code')

        # Build prompt for GPT
        email_body = email_dict.get('body_full') or ''

        # If no linked project, skip extraction
        if not linked_project_code:
            return {
                "error": "Email not linked to any project",
                "email_id": email_id
            }

        prompt = f"""You are analyzing an email about project {linked_project_code} to extract factual information.

EMAIL:
From: {email_dict['sender_email']}
Date: {email_dict['date']}
Subject: {email_dict['subject']}
Body:
{email_body[:3000]}

Extract FACTS mentioned about the project (project code: {linked_project_code}):
1. Project status mentions (active, completed, archived, on-hold, etc.)
2. Team information (number of people working, who's working)
3. Financial mentions (fees, budget changes, payments)
4. Timeline mentions (deadlines, completion dates, start dates)
5. Scope changes or updates
6. Client decisions or approvals

Return ONLY a JSON object:
{{
  "project_code": "{linked_project_code}",
  "facts": [
    {{
      "field": "status",
      "value": "active",
      "confidence": 0.9,
      "evidence": "exact quote from email"
    }}
  ]
}}

If no relevant facts found, return: {{"project_code": "{linked_project_code}", "facts": []}}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a data extraction assistant. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=2000
            )

            # Parse JSON response
            facts_json = response.choices[0].message.content.strip()

            # Handle markdown code blocks
            if facts_json.startswith("```"):
                facts_json = facts_json.split("```")[1]
                if facts_json.startswith("json"):
                    facts_json = facts_json[4:]
                facts_json = facts_json.strip()

            facts = json.loads(facts_json)
            facts['email_id'] = email_id
            facts['email_date'] = email_dict['date']
            facts['linked_project_code'] = linked_project_code

            return facts

        except Exception as e:
            print(f"Error extracting facts from email {email_id}: {e}")
            return {"error": str(e), "email_id": email_id}

    def check_fact_against_database(
        self,
        project_code: str,
        field: str,
        email_value: str,
        confidence: float,
        evidence: str,
        email_id: int,
        email_date: str
    ) -> Optional[Dict[str, Any]]:
        """Compare email fact against database value, return suggestion if mismatch"""

        cursor = self.conn.cursor()

        # Map field names to database columns
        field_mapping = {
            "status": ("proposals", "status", "proposal_id"),
            "project_status": ("proposals", "status", "proposal_id"),
            "project_value": ("proposals", "project_value", "proposal_id"),
            "team_size": ("projects", "team_size", "project_id"),
            "completion_date": ("projects", "completion_date", "project_id"),
            "is_active": ("proposals", "is_active_project", "proposal_id"),
            "phase": ("proposals", "project_phase", "proposal_id"),
        }

        if field not in field_mapping:
            # Unknown field, skip
            return None

        table, column, id_column = field_mapping[field]

        # Get current database value
        query = f"""
            SELECT {id_column}, {column} as current_value, project_name, status
            FROM {table}
            WHERE project_code = ?
        """

        cursor.execute(query, (project_code,))
        db_record = cursor.fetchone()

        if not db_record:
            # Project not in database yet - skip for now
            # (In future, could suggest creating it)
            return None

        current_value = str(db_record['current_value']) if db_record['current_value'] else None
        email_value_normalized = str(email_value).lower().strip()
        current_value_normalized = current_value.lower().strip() if current_value else ""

        # Check for mismatch
        mismatch = False
        reasoning = ""

        # Status mismatch detection
        if field in ["status", "project_status"]:
            active_keywords = ["active", "working", "in progress", "ongoing"]
            completed_keywords = ["completed", "finished", "done"]
            archived_keywords = ["archived", "closed", "inactive"]

            email_indicates_active = any(kw in email_value_normalized for kw in active_keywords)
            email_indicates_completed = any(kw in email_value_normalized for kw in completed_keywords)
            email_indicates_archived = any(kw in email_value_normalized for kw in archived_keywords)

            db_is_active = "active" in current_value_normalized or "proposal" in current_value_normalized
            db_is_completed = "completed" in current_value_normalized
            db_is_archived = "archived" in current_value_normalized or "closed" in current_value_normalized

            if email_indicates_active and not db_is_active:
                mismatch = True
                reasoning = f"Email indicates project is active ('{email_value}') but database shows '{current_value}'"
            elif email_indicates_completed and not db_is_completed:
                mismatch = True
                reasoning = f"Email indicates project completed ('{email_value}') but database shows '{current_value}'"
            elif email_indicates_archived and not db_is_archived:
                mismatch = True
                reasoning = f"Email indicates project archived ('{email_value}') but database shows '{current_value}'"

        # Numeric field mismatch (project_value, team_size)
        elif field in ["project_value", "team_size"]:
            try:
                email_num = float(email_value.replace("$", "").replace(",", "").strip())
                db_num = float(current_value) if current_value else 0

                # Allow 5% variance for rounding
                if abs(email_num - db_num) > (db_num * 0.05) and abs(email_num - db_num) > 100:
                    mismatch = True
                    reasoning = f"Email mentions {field} = {email_value}, database shows {current_value}"
            except ValueError:
                pass

        # If mismatch detected, create suggestion
        if mismatch and confidence > 0.7:  # Only suggest if AI is confident
            return {
                "entity_type": "proposal" if table == "proposals" else "project",
                "entity_id": db_record[id_column],
                "project_code": project_code,
                "field_name": field,
                "current_value": current_value,
                "suggested_value": email_value,
                "evidence_source": "email",
                "evidence_id": email_id,
                "evidence_snippet": evidence[:500],
                "evidence_date": email_date,
                "confidence_score": confidence,
                "reasoning": reasoning,
                "suggested_action": f"Update {field} from '{current_value}' to '{email_value}'"
            }

        return None

    def create_suggestion(self, suggestion: Dict[str, Any]) -> int:
        """Insert suggestion into database"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO data_validation_suggestions (
                entity_type, entity_id, project_code,
                field_name, current_value, suggested_value,
                evidence_source, evidence_id, evidence_snippet, evidence_date,
                confidence_score, reasoning, suggested_action
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            suggestion['entity_type'],
            suggestion['entity_id'],
            suggestion['project_code'],
            suggestion['field_name'],
            suggestion['current_value'],
            suggestion['suggested_value'],
            suggestion['evidence_source'],
            suggestion['evidence_id'],
            suggestion['evidence_snippet'],
            suggestion['evidence_date'],
            suggestion['confidence_score'],
            suggestion['reasoning'],
            suggestion['suggested_action']
        ))

        self.conn.commit()
        return cursor.lastrowid

    def process_email(self, email_id: int, verbose: bool = True) -> List[int]:
        """Process single email and create suggestions"""
        if verbose:
            print(f"\n📧 Processing email {email_id}...")

        # Extract facts
        facts = self.extract_facts_from_email(email_id)

        if "error" in facts:
            if verbose and "not linked" not in facts['error']:
                print(f"   ⚠️  {facts['error']}")
            return []

        suggestion_ids = []
        project_code = facts.get('project_code') or facts.get('linked_project_code')

        if not project_code:
            return []

        if verbose:
            print(f"   📋 Checking project: {project_code}")

        # Check each fact
        for fact in facts.get('facts', []):
            suggestion = self.check_fact_against_database(
                project_code=project_code,
                field=fact['field'],
                email_value=fact['value'],
                confidence=fact['confidence'],
                evidence=fact['evidence'],
                email_id=email_id,
                email_date=facts['email_date']
            )

            if suggestion:
                suggestion_id = self.create_suggestion(suggestion)
                suggestion_ids.append(suggestion_id)
                if verbose:
                    print(f"   🚨 Mismatch detected: {suggestion['field_name']}")
                    print(f"      DB: {suggestion['current_value']}")
                    print(f"      Email: {suggestion['suggested_value']}")
                    print(f"      Confidence: {suggestion['confidence_score']:.0%}")

        if not suggestion_ids and verbose:
            print(f"   ✅ No inconsistencies found")

        return suggestion_ids

    def process_batch(self, email_ids: List[int], verbose: bool = True):
        """Process multiple emails"""
        total_suggestions = 0

        for email_id in email_ids:
            suggestions = self.process_email(email_id, verbose=verbose)
            total_suggestions += len(suggestions)

        print(f"\n✅ Processed {len(email_ids)} emails")
        print(f"   Generated {total_suggestions} suggestions")

        return total_suggestions

    def get_pending_suggestions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get pending suggestions for review"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                suggestion_id, entity_type, project_code,
                field_name, current_value, suggested_value,
                evidence_snippet, confidence_score, reasoning, suggested_action,
                created_at
            FROM data_validation_suggestions
            WHERE status = 'pending'
            ORDER BY confidence_score DESC, created_at DESC
            LIMIT ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    def review_suggestion(self, suggestion_id: int, action: str, notes: str = None, reviewer: str = "system"):
        """Approve or deny a suggestion"""
        if action not in ['approved', 'denied']:
            raise ValueError("Action must be 'approved' or 'denied'")

        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE data_validation_suggestions
            SET status = ?, reviewed_by = ?, reviewed_at = datetime('now'), review_notes = ?
            WHERE suggestion_id = ?
        """, (action, reviewer, notes, suggestion_id))

        self.conn.commit()
        print(f"   ✅ Suggestion {suggestion_id} {action}")

    def close(self):
        """Close database connection"""
        self.conn.close()


def main():
    """CLI Interface"""
    import sys

    validator = SmartEmailValidator()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 smart_email_validator.py process <email_id>")
        print("  python3 smart_email_validator.py batch <start_id> <end_id>")
        print("  python3 smart_email_validator.py recent <count>")
        print("  python3 smart_email_validator.py review")
        sys.exit(1)

    command = sys.argv[1]

    if command == "process":
        email_id = int(sys.argv[2])
        validator.process_email(email_id)

    elif command == "batch":
        start_id = int(sys.argv[2])
        end_id = int(sys.argv[3])
        email_ids = list(range(start_id, end_id + 1))
        validator.process_batch(email_ids)

    elif command == "recent":
        count = int(sys.argv[2])
        cursor = validator.conn.cursor()
        # Only process emails that are linked to projects
        cursor.execute("""
            SELECT DISTINCT e.email_id
            FROM emails e
            INNER JOIN email_project_links epl ON e.email_id = epl.email_id
            WHERE e.body_full IS NOT NULL AND e.body_full != ''
            ORDER BY e.date DESC
            LIMIT ?
        """, (count,))
        email_ids = [row[0] for row in cursor.fetchall()]
        print(f"Processing {len(email_ids)} most recent project-linked emails...")
        validator.process_batch(email_ids)

    elif command == "review":
        suggestions = validator.get_pending_suggestions()
        print(f"\n📋 {len(suggestions)} Pending Suggestions:\n")

        for i, sugg in enumerate(suggestions, 1):
            print(f"{i}. [{sugg['project_code']}] {sugg['field_name']}")
            print(f"   Current: {sugg['current_value']}")
            print(f"   Suggested: {sugg['suggested_value']}")
            print(f"   Confidence: {sugg['confidence_score']:.0%}")
            print(f"   Evidence: {sugg['evidence_snippet'][:100]}...")
            print(f"   Reasoning: {sugg['reasoning']}")
            print()

    validator.close()


if __name__ == "__main__":
    main()
