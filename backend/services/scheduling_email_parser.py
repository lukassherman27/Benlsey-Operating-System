"""
Scheduling Email Parser - Extract scheduling data from emails using OpenAI

This service:
1. Extracts deadlines, dates, and milestones from email content
2. Identifies people mentioned and their roles
3. Detects project references and nicknames
4. Returns structured JSON for UI display and database storage

Example:
    Email: "We need the Soudah presentation by Aug 15. John is reviewing the drawings."
    System extracts: {
        "deadlines": [{"date": "2025-08-15", "context": "presentation", "project_hint": "Soudah"}],
        "people": [{"name": "John", "role": "reviewer"}],
        "project_references": ["Soudah"],
        "potential_nicknames": [{"nickname": "Soudah", "possible_projects": []}]
    }
"""

import os
import json
import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from openai import OpenAI

from .base_service import BaseService

logger = logging.getLogger(__name__)


# Prompt template for scheduling extraction
SCHEDULING_EXTRACTION_PROMPT = """You are a scheduling data extractor for a design studio's project management system.

Given an email, extract scheduling-related information.

Email Subject: {subject}
Email Body:
{body}

Extract the following (only include what you can confidently determine):

1. deadlines: List of deadlines or important dates mentioned
   Each deadline should have:
   - date: The date in YYYY-MM-DD format (estimate year based on context if not specified)
   - context: What the deadline is for (e.g., "presentation", "review", "submission")
   - project_hint: Any project name or code mentioned near this deadline
   - is_hard_deadline: true if explicitly stated as firm, false if flexible/estimated

2. people: List of people mentioned with their apparent role in the email
   Each person should have:
   - name: Person's name
   - role: Their apparent role (e.g., "reviewer", "presenter", "client contact", "responsible party")
   - action_item: Any task assigned to them

3. project_references: List of project codes (like "BK-042", "25 BK-070") or project names mentioned

4. potential_nicknames: Informal project names that might map to a project code
   Each nickname should have:
   - nickname: The informal name used (e.g., "Soudah", "Ritz Bali", "the Bangkok project")
   - context: The context where it was used

5. action_items: List of action items or tasks mentioned
   Each action item should have:
   - description: What needs to be done
   - assignee: Who should do it (if mentioned)
   - due_date: When it's due (if mentioned)
   - priority: high/medium/low (infer from urgency words)

Respond with ONLY a JSON object. Include only fields you can determine with reasonable confidence.
If you cannot extract anything meaningful, return an empty object {{}}.

Example input subject: "Soudah presentation - August deadline"
Example input body: "Hi team, just a reminder that we need to finalize the Soudah presentation for the client by August 15th. John, please make sure the 3D renderings are ready by EOD Friday. Sarah will handle the budget slides."

Example output:
{{
    "deadlines": [
        {{"date": "2025-08-15", "context": "presentation", "project_hint": "Soudah", "is_hard_deadline": true}},
        {{"date": "2025-12-06", "context": "3D renderings", "project_hint": "Soudah", "is_hard_deadline": true}}
    ],
    "people": [
        {{"name": "John", "role": "responsible party", "action_item": "3D renderings"}},
        {{"name": "Sarah", "role": "responsible party", "action_item": "budget slides"}}
    ],
    "project_references": [],
    "potential_nicknames": [
        {{"nickname": "Soudah", "context": "presentation deadline"}}
    ],
    "action_items": [
        {{"description": "Finalize presentation for client", "assignee": null, "due_date": "2025-08-15", "priority": "high"}},
        {{"description": "3D renderings ready", "assignee": "John", "due_date": "EOD Friday", "priority": "high"}},
        {{"description": "Budget slides", "assignee": "Sarah", "due_date": null, "priority": "medium"}}
    ]
}}

Now extract from this email:"""


class SchedulingEmailParser(BaseService):
    """Service for extracting scheduling data from emails using OpenAI"""

    def __init__(self, db_path: str = None):
        super().__init__(db_path)
        api_key = os.environ.get('OPENAI_API_KEY')
        self.ai_enabled = bool(api_key)
        if self.ai_enabled:
            self.client = OpenAI(api_key=api_key)

    def parse(self, email_body: str, subject: str = "") -> Dict[str, Any]:
        """
        Extract scheduling data from an email.

        Args:
            email_body: The full email body text
            subject: The email subject line

        Returns:
            Dict with extracted scheduling data:
            - deadlines: List of deadline objects
            - people: List of people mentioned
            - project_references: List of project codes found
            - potential_nicknames: List of informal project names
            - action_items: List of action items
        """
        if not email_body or not email_body.strip():
            return self._empty_result()

        # First try quick pattern extraction (no API call)
        quick_extract = self._quick_extract_patterns(email_body, subject)

        # If we got good data from patterns, we can skip AI
        if self._has_meaningful_data(quick_extract):
            logger.info(f"Quick extraction found data: {len(quick_extract.get('deadlines', []))} deadlines, "
                       f"{len(quick_extract.get('project_references', []))} project refs")

        # Use OpenAI for comprehensive extraction
        if not self.ai_enabled:
            logger.warning("OpenAI not configured, using basic extraction only")
            return quick_extract

        try:
            # Truncate body if too long (keep first 3000 chars to stay within context)
            truncated_body = email_body[:3000] if len(email_body) > 3000 else email_body

            prompt = SCHEDULING_EXTRACTION_PROMPT.format(
                subject=subject or "(No subject)",
                body=truncated_body
            )

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You extract scheduling and deadline information from emails. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )

            content = response.choices[0].message.content.strip()

            # Clean up response - sometimes GPT adds markdown code blocks
            if content.startswith("```"):
                content = re.sub(r'^```(?:json)?\n?', '', content)
                content = re.sub(r'\n?```$', '', content)

            extracted = json.loads(content)

            # Validate and clean the response
            cleaned = self._validate_extracted_data(extracted)

            # Merge with quick extraction (quick extract provides defaults)
            result = self._merge_extractions(quick_extract, cleaned)

            logger.info(f"AI extracted scheduling data: {len(result.get('deadlines', []))} deadlines, "
                       f"{len(result.get('people', []))} people")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            return quick_extract
        except Exception as e:
            logger.error(f"Scheduling extraction failed: {e}")
            return quick_extract

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            "deadlines": [],
            "people": [],
            "project_references": [],
            "potential_nicknames": [],
            "action_items": []
        }

    def _has_meaningful_data(self, data: Dict[str, Any]) -> bool:
        """Check if extracted data has meaningful content"""
        return (
            len(data.get('deadlines', [])) > 0 or
            len(data.get('project_references', [])) > 0 or
            len(data.get('action_items', [])) > 0
        )

    def _quick_extract_patterns(self, body: str, subject: str = "") -> Dict[str, Any]:
        """
        Quick pattern-based extraction for common cases.
        Faster than API call, good for obvious patterns.
        """
        result = self._empty_result()
        combined_text = f"{subject} {body}".lower()
        original_text = f"{subject} {body}"

        # Extract project codes (BK-XXX, XX BK-XXX patterns)
        project_patterns = [
            r'\b(\d{2}\s*BK[-\s]?\d{3})\b',  # "25 BK-070", "25BK-070"
            r'\b(BK[-\s]?\d{3})\b',           # "BK-070", "BK 070"
        ]
        for pattern in project_patterns:
            matches = re.findall(pattern, original_text, re.IGNORECASE)
            for match in matches:
                # Normalize the code
                normalized = re.sub(r'\s+', ' ', match.upper()).strip()
                if normalized not in result['project_references']:
                    result['project_references'].append(normalized)

        # Extract dates (various formats)
        date_patterns = [
            # "August 15", "Aug 15", "15 August"
            (r'(?:by\s+|on\s+|due\s+)?(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s*,?\s*(\d{4}))?', 'month_day'),
            (r'(?:by\s+|on\s+|due\s+)?(\d{1,2})(?:st|nd|rd|th)?\s+(\w+)(?:\s*,?\s*(\d{4}))?', 'day_month'),
            # "EOD Friday", "by Friday"
            (r'(?:by\s+|on\s+)?EOD\s+(\w+day)', 'eod_weekday'),
            (r'(?:by\s+|on\s+|due\s+)(\w+day)', 'weekday'),
            # ISO dates
            (r'(\d{4}-\d{2}-\d{2})', 'iso'),
            # US format: 12/15/2024
            (r'(\d{1,2}/\d{1,2}/\d{4})', 'us_date'),
        ]

        months = {
            'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
            'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
            'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'sept': 9,
            'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
        }

        for pattern, pattern_type in date_patterns:
            matches = re.finditer(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                deadline = {"context": "mentioned deadline", "is_hard_deadline": False}

                if pattern_type == 'month_day':
                    month_name, day, year = match.groups()
                    month = months.get(month_name.lower())
                    if month:
                        year = int(year) if year else datetime.now().year
                        try:
                            deadline['date'] = f"{year}-{month:02d}-{int(day):02d}"
                        except ValueError:
                            continue
                elif pattern_type == 'day_month':
                    day, month_name, year = match.groups()
                    month = months.get(month_name.lower())
                    if month:
                        year = int(year) if year else datetime.now().year
                        try:
                            deadline['date'] = f"{year}-{month:02d}-{int(day):02d}"
                        except ValueError:
                            continue
                elif pattern_type == 'iso':
                    deadline['date'] = match.group(1)
                elif pattern_type in ('eod_weekday', 'weekday'):
                    # Just note the weekday mention
                    deadline['date'] = match.group(1).capitalize()
                    deadline['is_relative'] = True

                if 'date' in deadline:
                    # Check for urgency indicators
                    context_start = max(0, match.start() - 50)
                    context_end = min(len(combined_text), match.end() + 50)
                    context = combined_text[context_start:context_end]

                    if any(word in context for word in ['deadline', 'due', 'must', 'need', 'urgent']):
                        deadline['is_hard_deadline'] = True

                    result['deadlines'].append(deadline)

        # Extract people (look for names followed by action verbs)
        # This is basic - AI does much better
        name_patterns = [
            r'([A-Z][a-z]+)\s+(?:will|is|should|can|please)\s+(\w+)',
            r'(?:please|can)\s+([A-Z][a-z]+)\s+(\w+)',
        ]
        for pattern in name_patterns:
            matches = re.finditer(pattern, original_text)
            for match in matches:
                name = match.group(1)
                if name.lower() not in ['the', 'this', 'that', 'please', 'can', 'will']:
                    result['people'].append({
                        "name": name,
                        "role": "mentioned",
                        "action_item": None
                    })

        return result

    def _validate_extracted_data(self, extracted: Dict) -> Dict[str, Any]:
        """Validate and clean extracted data from AI"""
        result = self._empty_result()

        # Validate deadlines
        if extracted.get('deadlines') and isinstance(extracted['deadlines'], list):
            for d in extracted['deadlines']:
                if isinstance(d, dict):
                    deadline = {}
                    if d.get('date'):
                        deadline['date'] = str(d['date'])
                    if d.get('context'):
                        deadline['context'] = str(d['context'])[:200]
                    if d.get('project_hint'):
                        deadline['project_hint'] = str(d['project_hint'])[:100]
                    if 'is_hard_deadline' in d:
                        deadline['is_hard_deadline'] = bool(d['is_hard_deadline'])
                    if deadline.get('date'):
                        result['deadlines'].append(deadline)

        # Validate people
        if extracted.get('people') and isinstance(extracted['people'], list):
            for p in extracted['people']:
                if isinstance(p, dict) and p.get('name'):
                    person = {'name': str(p['name'])[:100]}
                    if p.get('role'):
                        person['role'] = str(p['role'])[:100]
                    if p.get('action_item'):
                        person['action_item'] = str(p['action_item'])[:200]
                    result['people'].append(person)

        # Validate project_references
        if extracted.get('project_references') and isinstance(extracted['project_references'], list):
            for ref in extracted['project_references']:
                if isinstance(ref, str) and len(ref) < 50:
                    result['project_references'].append(ref)

        # Validate potential_nicknames
        if extracted.get('potential_nicknames') and isinstance(extracted['potential_nicknames'], list):
            for n in extracted['potential_nicknames']:
                if isinstance(n, dict) and n.get('nickname'):
                    nickname = {'nickname': str(n['nickname'])[:100]}
                    if n.get('context'):
                        nickname['context'] = str(n['context'])[:200]
                    result['potential_nicknames'].append(nickname)

        # Validate action_items
        if extracted.get('action_items') and isinstance(extracted['action_items'], list):
            for a in extracted['action_items']:
                if isinstance(a, dict) and a.get('description'):
                    action = {'description': str(a['description'])[:300]}
                    if a.get('assignee'):
                        action['assignee'] = str(a['assignee'])[:100]
                    if a.get('due_date'):
                        action['due_date'] = str(a['due_date'])[:50]
                    if a.get('priority') and a['priority'] in ('high', 'medium', 'low'):
                        action['priority'] = a['priority']
                    result['action_items'].append(action)

        return result

    def _merge_extractions(self, quick: Dict[str, Any], ai: Dict[str, Any]) -> Dict[str, Any]:
        """Merge quick extraction with AI extraction, preferring AI but keeping unique items from quick"""
        result = {
            "deadlines": ai.get('deadlines', []),
            "people": ai.get('people', []),
            "project_references": list(set(
                quick.get('project_references', []) + ai.get('project_references', [])
            )),
            "potential_nicknames": ai.get('potential_nicknames', []),
            "action_items": ai.get('action_items', [])
        }
        return result

    def get_email_content(self, email_id: int) -> Optional[Dict[str, str]]:
        """Get email content from database"""
        result = self.execute_query("""
            SELECT subject, body_full, body_preview
            FROM emails
            WHERE email_id = ?
        """, [email_id])

        if result:
            row = result[0]
            return {
                'subject': row.get('subject') or '',
                'body': row.get('body_full') or row.get('body_preview') or ''
            }
        return None

    def parse_email_by_id(self, email_id: int) -> Dict[str, Any]:
        """
        Parse scheduling data from an email by ID.

        Args:
            email_id: The email ID in the database

        Returns:
            Dict with extracted scheduling data or error
        """
        email = self.get_email_content(email_id)
        if not email:
            return {
                "success": False,
                "error": f"Email {email_id} not found"
            }

        result = self.parse(email['body'], email['subject'])
        result['success'] = True
        result['email_id'] = email_id
        return result


# Module-level singleton
_parser = None


def get_scheduling_parser() -> SchedulingEmailParser:
    """Get the singleton scheduling parser instance"""
    global _parser
    if _parser is None:
        from api.dependencies import DB_PATH
        _parser = SchedulingEmailParser(db_path=DB_PATH)
    return _parser
