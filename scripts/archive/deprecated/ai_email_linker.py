#!/usr/bin/env python3
"""
AI Email-to-Project Linker

Links emails to projects using:
1. Contact recognition (who sent it)
2. Project name matching (fuzzy matching on project names, client names)
3. AI context analysis (what is this email about?)

Example:
- Email from: john@soudah.sa
- Subject: "Re: Hotel design for the resort"
- Body mentions: "the Soudah project", "mountain resort"
→ AI links to project: 25 BK-017 (Soudah Mountain Resort)
"""

import sqlite3
import os
from typing import List, Dict, Optional, Any
from pathlib import Path
from openai import OpenAI
import json
from difflib import SequenceMatcher

# Configuration
DB_PATH = Path(__file__).parent / "database" / "bensley_master.db"


class AIEmailLinker:
    """AI-powered email to project linker"""

    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

        # Initialize OpenAI client
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        self.client = OpenAI(api_key=api_key)

        # Load projects for matching
        self.projects = self.load_projects()
        self.contact_project_map = self.load_contact_project_mapping()

    def load_projects(self) -> List[Dict[str, Any]]:
        """Load all projects from database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                project_code,
                project_name,
                client_company,
                contact_email,
                status
            FROM proposals
            WHERE project_name IS NOT NULL
        """)

        projects = []
        for row in cursor.fetchall():
            projects.append({
                'project_code': row['project_code'],
                'project_name': row['project_name'] or '',
                'client_company': row['client_company'] or '',
                'contact_email': row['contact_email'] or '',
                'status': row['status']
            })

        print(f"✓ Loaded {len(projects)} projects")
        return projects

    def load_contact_project_mapping(self) -> Dict[str, List[str]]:
        """Build map of email addresses to project codes"""
        cursor = self.conn.cursor()

        # Get existing links from email_project_links
        cursor.execute("""
            SELECT DISTINCT
                e.sender_email,
                epl.project_code
            FROM emails e
            INNER JOIN email_project_links epl ON e.email_id = epl.email_id
            WHERE e.sender_email IS NOT NULL
            AND epl.project_code IS NOT NULL
        """)

        contact_map = {}
        for row in cursor.fetchall():
            email = row['sender_email'].lower().strip()
            project_code = row['project_code']

            if email not in contact_map:
                contact_map[email] = []
            if project_code not in contact_map[email]:
                contact_map[email].append(project_code)

        # Also get from proposals.contact_email
        cursor.execute("""
            SELECT DISTINCT contact_email, project_code
            FROM proposals
            WHERE contact_email IS NOT NULL
        """)

        for row in cursor.fetchall():
            email = row['contact_email'].lower().strip()
            project_code = row['project_code']

            if email not in contact_map:
                contact_map[email] = []
            if project_code not in contact_map[email]:
                contact_map[email].append(project_code)

        print(f"✓ Loaded {len(contact_map)} contact-project mappings")
        return contact_map

    def fuzzy_match_project(self, text: str, threshold: float = 0.6) -> List[Dict[str, Any]]:
        """Fuzzy match text against project names and client names"""
        text_lower = text.lower().strip()
        matches = []

        for project in self.projects:
            # Check project name similarity
            project_name_lower = project['project_name'].lower()
            name_similarity = SequenceMatcher(None, text_lower, project_name_lower).ratio()

            # Check if text contains project name keywords
            project_keywords = [word for word in project_name_lower.split() if len(word) > 3]
            keyword_matches = sum(1 for kw in project_keywords if kw in text_lower)
            keyword_score = keyword_matches / max(len(project_keywords), 1)

            # Check client company similarity
            client_lower = project['client_company'].lower()
            client_similarity = SequenceMatcher(None, text_lower, client_lower).ratio()

            # Combined score
            best_score = max(name_similarity, keyword_score, client_similarity)

            if best_score >= threshold:
                matches.append({
                    'project_code': project['project_code'],
                    'project_name': project['project_name'],
                    'score': best_score,
                    'match_type': 'name' if name_similarity == best_score else 'client' if client_similarity == best_score else 'keyword'
                })

        # Sort by score
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches

    def link_email_using_ai(self, email_id: int, verbose: bool = True) -> Optional[Dict[str, Any]]:
        """Use AI to determine which project this email is about"""

        # Get email
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                email_id,
                subject,
                sender_email,
                sender_name,
                date,
                body_full,
                snippet
            FROM emails
            WHERE email_id = ?
        """, (email_id,))

        email = cursor.fetchone()
        if not email:
            return None

        email_dict = dict(email)

        # Check if already linked
        cursor.execute("""
            SELECT project_code FROM email_project_links WHERE email_id = ?
        """, (email_id,))
        existing_link = cursor.fetchone()
        if existing_link:
            if verbose:
                print(f"   ⚠️  Already linked to {existing_link['project_code']}")
            return None

        # Step 1: Check if sender is known contact
        sender_email = email_dict['sender_email']
        if sender_email:
            sender_lower = sender_email.lower().strip()
            if sender_lower in self.contact_project_map:
                known_projects = self.contact_project_map[sender_lower]
                if len(known_projects) == 1:
                    # Only one project for this contact - high confidence link
                    return {
                        'project_code': known_projects[0],
                        'confidence': 0.95,
                        'method': 'contact_known',
                        'evidence': f"Sender {sender_email} is known contact for this project"
                    }

        # Step 2: Fuzzy match on subject + body
        search_text = f"{email_dict['subject']} {email_dict['body_full'][:1000] if email_dict['body_full'] else email_dict['snippet']}"
        fuzzy_matches = self.fuzzy_match_project(search_text, threshold=0.6)

        # Step 3: Use AI to analyze and pick best match
        if fuzzy_matches:
            # Build context for AI
            projects_context = "\n".join([
                f"- {m['project_code']}: {m['project_name']} (match score: {m['score']:.2f})"
                for m in fuzzy_matches[:5]  # Top 5 matches
            ])

            body_preview = email_dict['body_full'][:1500] if email_dict['body_full'] else email_dict['snippet']

            prompt = f"""You are linking an email to a project.

EMAIL:
From: {email_dict['sender_email']} ({email_dict['sender_name']})
Subject: {email_dict['subject']}
Body preview:
{body_preview}

POSSIBLE PROJECT MATCHES (from fuzzy matching):
{projects_context}

Based on the email content, which project is this email MOST LIKELY about?

Return ONLY a JSON object:
{{
  "project_code": "BK-XXX" or null if none match,
  "confidence": 0.0 to 1.0,
  "reasoning": "Brief explanation of why this project matches"
}}

If the email is clearly not about any of these projects, return null for project_code.
If it's generic/unclear, return null.
Only return a project if you're confident (>0.7) it's the right match.
"""

            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are an assistant that links emails to projects. Always respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0,
                    max_tokens=500
                )

                result_json = response.choices[0].message.content.strip()

                # Handle markdown code blocks
                if result_json.startswith("```"):
                    result_json = result_json.split("```")[1]
                    if result_json.startswith("json"):
                        result_json = result_json[4:]
                    result_json = result_json.strip()

                result = json.loads(result_json)

                if result.get('project_code') and result.get('confidence', 0) > 0.7:
                    return {
                        'project_code': result['project_code'],
                        'confidence': result['confidence'],
                        'method': 'ai_analysis',
                        'evidence': result['reasoning']
                    }

            except Exception as e:
                if verbose:
                    print(f"   ⚠️  AI analysis error: {e}")

        return None

    def create_link(self, email_id: int, link_info: Dict[str, Any]) -> int:
        """Create email-project link in database"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO email_project_links
            (email_id, project_code, confidence, link_method, evidence)
            VALUES (?, ?, ?, ?, ?)
        """, (
            email_id,
            link_info['project_code'],
            link_info['confidence'],
            link_info['method'],
            link_info['evidence']
        ))

        self.conn.commit()
        return cursor.lastrowid

    def process_email(self, email_id: int, verbose: bool = True) -> bool:
        """Process single email and link to project"""
        if verbose:
            print(f"\n📧 Processing email {email_id}...")

        link_info = self.link_email_using_ai(email_id, verbose=verbose)

        if link_info:
            self.create_link(email_id, link_info)
            if verbose:
                print(f"   ✅ Linked to {link_info['project_code']} (confidence: {link_info['confidence']:.0%})")
                print(f"      Method: {link_info['method']}")
                print(f"      Evidence: {link_info['evidence'][:80]}...")
            return True
        else:
            if verbose:
                print(f"   ❌ No project match found")
            return False

    def process_batch(self, email_ids: List[int], verbose: bool = True) -> Dict[str, int]:
        """Process multiple emails"""
        stats = {'linked': 0, 'no_match': 0, 'already_linked': 0, 'errors': 0}

        for email_id in email_ids:
            try:
                result = self.process_email(email_id, verbose=verbose)
                if result:
                    stats['linked'] += 1
                else:
                    stats['no_match'] += 1
            except Exception as e:
                stats['errors'] += 1
                if verbose:
                    print(f"   ⚠️  Error: {e}")

        print(f"\n✅ Processed {len(email_ids)} emails")
        print(f"   Linked: {stats['linked']}")
        print(f"   No match: {stats['no_match']}")
        print(f"   Errors: {stats['errors']}")

        return stats

    def close(self):
        """Close database connection"""
        self.conn.close()


def main():
    """CLI Interface"""
    import sys

    linker = AIEmailLinker()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 ai_email_linker.py process <email_id>")
        print("  python3 ai_email_linker.py batch <start_id> <end_id>")
        print("  python3 ai_email_linker.py unlinked <count>    # Process N unlinked emails with body content")
        print("  python3 ai_email_linker.py recent <count>      # Process N recent emails with body content")
        sys.exit(1)

    command = sys.argv[1]

    if command == "process":
        email_id = int(sys.argv[2])
        linker.process_email(email_id)

    elif command == "batch":
        start_id = int(sys.argv[2])
        end_id = int(sys.argv[3])
        email_ids = list(range(start_id, end_id + 1))
        linker.process_batch(email_ids)

    elif command == "unlinked":
        count = int(sys.argv[2])
        cursor = linker.conn.cursor()

        # Find emails with body content that aren't linked yet
        cursor.execute("""
            SELECT e.email_id
            FROM emails e
            LEFT JOIN email_project_links epl ON e.email_id = epl.email_id
            WHERE e.body_full IS NOT NULL
            AND LENGTH(e.body_full) > 100
            AND epl.email_id IS NULL
            ORDER BY e.date DESC
            LIMIT ?
        """, (count,))

        email_ids = [row[0] for row in cursor.fetchall()]
        print(f"Processing {len(email_ids)} unlinked emails with body content...")
        linker.process_batch(email_ids)

    elif command == "recent":
        count = int(sys.argv[2])
        cursor = linker.conn.cursor()

        # Process recent emails with body content
        cursor.execute("""
            SELECT email_id
            FROM emails
            WHERE body_full IS NOT NULL
            AND LENGTH(body_full) > 100
            ORDER BY date DESC
            LIMIT ?
        """, (count,))

        email_ids = [row[0] for row in cursor.fetchall()]
        print(f"Processing {len(email_ids)} recent emails with body content...")
        linker.process_batch(email_ids)

    linker.close()


if __name__ == "__main__":
    main()
