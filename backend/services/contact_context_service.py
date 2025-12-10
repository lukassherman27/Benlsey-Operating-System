"""
Contact Context Service - Intelligent Context Learning from User Feedback

This service:
1. Extracts rich context from user notes using OpenAI
2. Stores structured contact context for future use
3. Provides context lookup for email handling decisions

Example:
    User writes: "Suresh is a kitchen consultant who works on many projects"
    System extracts: {
        "role": "kitchen consultant",
        "relationship_type": "contractor",
        "is_multi_project": true,
        "is_client": false
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


# Prompt template for context extraction
CONTEXT_EXTRACTION_PROMPT = """You are a contact context extractor for a design studio's project management system.

Given the user's note about a contact, extract structured information.

User's note: {user_note}

Extract the following fields (only include fields you can confidently determine):

1. role: The person's job role or function (e.g., "kitchen consultant", "project manager", "IT support")
2. relationship_type: One of: "client", "client_team", "vendor", "contractor", "internal", "external", "unknown"
3. is_client: true if this is a client or client's team member, false if explicitly not a client, null if unclear
4. is_multi_project: true if they work on multiple projects, false if single project, null if unclear
5. is_decision_maker: true if they can approve/sign off, false otherwise, null if unclear
6. email_handling_preference: One of:
   - "link_to_project": Always link their emails to a specific project
   - "categorize_only": Just categorize, don't suggest project links
   - "suggest_multiple": Their emails may relate to multiple projects
   - "ignore": Don't process (spam, automated emails)
   - "default": Use normal handling
7. default_category: Suggested email category (e.g., "External", "Internal", "Vendor")
8. default_subcategory: More specific category (e.g., "Kitchen", "IT", "Landscape")
9. company_type: Type of organization (e.g., "design firm", "hotel chain", "supplier")

Respond with ONLY a JSON object. Include only fields you can determine with reasonable confidence.
If you cannot determine a field, omit it entirely.

Example input: "John is our internal IT guy"
Example output: {{"role": "IT support", "relationship_type": "internal", "is_client": false, "default_category": "Internal", "default_subcategory": "IT"}}

Example input: "She's from Four Seasons, the client contact for the Bangkok project"
Example output: {{"role": "client contact", "relationship_type": "client", "is_client": true, "is_multi_project": false, "email_handling_preference": "link_to_project", "company_type": "hotel chain"}}

Example input: "Suresh is a kitchen consultant that works on many projects, not really a client"
Example output: {{"role": "kitchen consultant", "relationship_type": "contractor", "is_client": false, "is_multi_project": true, "email_handling_preference": "categorize_only", "default_category": "External", "default_subcategory": "Kitchen"}}

Now extract from the user's note:"""


class ContactContextService(BaseService):
    """Service for extracting and managing rich contact context"""

    def __init__(self, db_path: str = None):
        super().__init__(db_path)
        api_key = os.environ.get('OPENAI_API_KEY')
        self.ai_enabled = bool(api_key)
        if self.ai_enabled:
            self.client = OpenAI(api_key=api_key)

    # =========================================================================
    # CONTEXT EXTRACTION
    # =========================================================================

    def extract_context_from_notes(
        self,
        user_note: str,
        contact_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract structured context from user's free-form notes using OpenAI.

        Args:
            user_note: The user's note about the contact (e.g., "Suresh is a kitchen consultant")
            contact_email: Optional email address of the contact

        Returns:
            Dict with extracted fields: role, relationship_type, is_client, etc.
        """
        if not user_note or not user_note.strip():
            return {}

        # First try regex patterns for common cases (fast, no API call)
        quick_extract = self._quick_extract_patterns(user_note)
        if quick_extract.get('high_confidence'):
            logger.info(f"Quick extraction succeeded: {quick_extract}")
            return quick_extract

        # Use OpenAI for complex extraction
        if not self.ai_enabled:
            logger.warning("OpenAI not configured, using basic extraction only")
            return quick_extract

        try:
            prompt = CONTEXT_EXTRACTION_PROMPT.format(user_note=user_note)

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You extract contact context information. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )

            content = response.choices[0].message.content.strip()

            # Clean up response - sometimes GPT adds markdown code blocks
            if content.startswith("```"):
                content = re.sub(r'^```(?:json)?\n?', '', content)
                content = re.sub(r'\n?```$', '', content)

            extracted = json.loads(content)

            # Validate and clean the response
            cleaned = self._validate_extracted_context(extracted)

            # Merge with quick extraction (quick extract provides defaults)
            result = {**quick_extract, **cleaned}

            # Remove the internal high_confidence flag
            result.pop('high_confidence', None)

            logger.info(f"AI extracted context: {result}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            return quick_extract
        except Exception as e:
            logger.error(f"Context extraction failed: {e}")
            return quick_extract

    def _quick_extract_patterns(self, user_note: str) -> Dict[str, Any]:
        """
        Quick pattern-based extraction for common phrases.
        Faster than API call, good for obvious cases.
        """
        result = {}
        note_lower = user_note.lower().strip()

        # Multi-project patterns
        multi_project_patterns = [
            r'(many|multiple|several|various)\s+project',
            r'works?\s+(on|across)\s+(many|multiple|several)',
            r'not\s+(just\s+)?(one|single|this)\s+project'
        ]
        for pattern in multi_project_patterns:
            if re.search(pattern, note_lower):
                result['is_multi_project'] = True
                break

        # Single project patterns
        single_project_patterns = [
            r'(only|just)\s+(this|one|single)\s+project',
            r'(for|on)\s+(this|the)\s+project\s+only'
        ]
        for pattern in single_project_patterns:
            if re.search(pattern, note_lower):
                result['is_multi_project'] = False
                break

        # Not a client patterns
        not_client_patterns = [
            r'not\s+(a\s+)?client',
            r'isn\'?t\s+(a\s+)?client',
            r'(vendor|supplier|contractor|consultant)',
        ]
        for pattern in not_client_patterns:
            if re.search(pattern, note_lower):
                result['is_client'] = False
                break

        # Client patterns
        client_patterns = [
            r'(the|a)\s+client',
            r'client\'?s?\s+(contact|team|representative)',
            r'from\s+(the\s+)?client'
        ]
        for pattern in client_patterns:
            if re.search(pattern, note_lower):
                result['is_client'] = True
                result['relationship_type'] = 'client'
                break

        # Internal patterns
        if re.search(r'(our|internal|in-house|bensley)', note_lower):
            result['relationship_type'] = 'internal'
            result['is_client'] = False

        # Vendor/contractor patterns
        if re.search(r'(vendor|supplier)', note_lower):
            result['relationship_type'] = 'vendor'
            result['is_client'] = False

        if re.search(r'(consultant|contractor|freelance)', note_lower):
            result['relationship_type'] = 'contractor'
            result['is_client'] = False

        # Role extraction
        role_patterns = [
            (r'(kitchen|landscape|interior|architect)\s+(consultant|designer|specialist)', r'\1 \2'),
            (r'(project|account|sales)\s+manager', r'\1 manager'),
            (r'(IT|tech|technical)\s+(support|guy|person|specialist)', r'IT support'),
            (r'(our|the)\s+(.+?)\s+(guy|person|contact)', r'\2'),
        ]
        for pattern, replacement in role_patterns:
            match = re.search(pattern, note_lower)
            if match:
                result['role'] = match.expand(replacement).strip()
                break

        # Mark high confidence if we got significant extraction
        if len(result) >= 2:
            result['high_confidence'] = True

        return result

    def _validate_extracted_context(self, extracted: Dict) -> Dict:
        """Validate and clean extracted context fields"""
        valid = {}

        # Validate role
        if extracted.get('role'):
            role = str(extracted['role']).strip()
            if len(role) > 2 and len(role) < 100:
                valid['role'] = role

        # Validate relationship_type
        valid_relationships = {'client', 'client_team', 'vendor', 'contractor', 'internal', 'external', 'unknown'}
        if extracted.get('relationship_type') in valid_relationships:
            valid['relationship_type'] = extracted['relationship_type']

        # Validate booleans
        for field in ['is_client', 'is_multi_project', 'is_decision_maker']:
            if field in extracted and extracted[field] is not None:
                valid[field] = bool(extracted[field])

        # Validate email_handling_preference
        valid_preferences = {'link_to_project', 'categorize_only', 'suggest_multiple', 'ignore', 'default'}
        if extracted.get('email_handling_preference') in valid_preferences:
            valid['email_handling_preference'] = extracted['email_handling_preference']

        # Validate categories
        if extracted.get('default_category'):
            cat = str(extracted['default_category']).strip()
            if len(cat) > 1 and len(cat) < 50:
                valid['default_category'] = cat

        if extracted.get('default_subcategory'):
            subcat = str(extracted['default_subcategory']).strip()
            if len(subcat) > 1 and len(subcat) < 50:
                valid['default_subcategory'] = subcat

        if extracted.get('company_type'):
            ctype = str(extracted['company_type']).strip()
            if len(ctype) > 1 and len(ctype) < 100:
                valid['company_type'] = ctype

        return valid

    # =========================================================================
    # CONTEXT STORAGE
    # =========================================================================

    def store_contact_context(
        self,
        email: str,
        context: Dict[str, Any],
        learned_from: str = 'user_correction',
        source_suggestion_id: Optional[int] = None,
        source_email_id: Optional[int] = None,
        original_notes: Optional[str] = None
    ) -> Optional[int]:
        """
        Store or update contact context in the database.

        Args:
            email: Contact's email address
            context: Extracted context dict
            learned_from: How we learned this context
            source_suggestion_id: Suggestion that triggered learning
            source_email_id: Email that provided context
            original_notes: User's original notes

        Returns:
            context_id or None on failure
        """
        if not email or not context:
            return None

        email = email.lower().strip()

        # Check if context exists
        existing = self.execute_query(
            "SELECT context_id FROM contact_context WHERE email = ?",
            [email]
        )

        with self.get_connection() as conn:
            cursor = conn.cursor()

            if existing:
                # Update existing context
                context_id = existing[0]['context_id']
                previous_context = self.get_contact_context(email)

                # Build update query dynamically
                updates = []
                params = []

                if context.get('role'):
                    updates.append("role = ?")
                    params.append(context['role'])

                if context.get('relationship_type'):
                    updates.append("relationship_type = ?")
                    params.append(context['relationship_type'])

                if 'is_client' in context:
                    updates.append("is_client = ?")
                    params.append(1 if context['is_client'] else 0 if context['is_client'] is False else None)

                if 'is_multi_project' in context:
                    updates.append("is_multi_project = ?")
                    params.append(1 if context['is_multi_project'] else 0 if context['is_multi_project'] is False else None)

                if 'is_decision_maker' in context:
                    updates.append("is_decision_maker = ?")
                    params.append(1 if context['is_decision_maker'] else 0 if context['is_decision_maker'] is False else None)

                if context.get('email_handling_preference'):
                    updates.append("email_handling_preference = ?")
                    params.append(context['email_handling_preference'])

                if context.get('default_category'):
                    updates.append("default_category = ?")
                    params.append(context['default_category'])

                if context.get('default_subcategory'):
                    updates.append("default_subcategory = ?")
                    params.append(context['default_subcategory'])

                if context.get('company_type'):
                    updates.append("company_type = ?")
                    params.append(context['company_type'])

                if original_notes:
                    updates.append("context_notes = COALESCE(context_notes || '\\n' || ?, ?)")
                    params.extend([original_notes, original_notes])
                    updates.append("structured_notes = ?")
                    params.append(json.dumps(context))

                # Boost confidence on update
                updates.append("confidence = MIN(0.95, confidence + 0.1)")
                updates.append("times_validated = times_validated + 1")

                if updates:
                    params.append(email)
                    cursor.execute(f"""
                        UPDATE contact_context
                        SET {', '.join(updates)}
                        WHERE email = ?
                    """, params)

                # Log history
                cursor.execute("""
                    INSERT INTO contact_context_history (
                        context_id, email, change_type, previous_values, new_values,
                        change_reason, source_suggestion_id, source_email_id
                    ) VALUES (?, ?, 'updated', ?, ?, ?, ?, ?)
                """, (
                    context_id, email, json.dumps(previous_context), json.dumps(context),
                    original_notes, source_suggestion_id, source_email_id
                ))

                conn.commit()
                logger.info(f"Updated contact context for {email}: {context}")
                return context_id

            else:
                # Insert new context
                cursor.execute("""
                    INSERT INTO contact_context (
                        email, role, relationship_type,
                        is_client, is_multi_project, is_decision_maker,
                        email_handling_preference, default_category, default_subcategory,
                        company_type, context_notes, structured_notes,
                        learned_from, learned_from_suggestion_id, learned_from_email_id,
                        confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    email,
                    context.get('role'),
                    context.get('relationship_type', 'unknown'),
                    1 if context.get('is_client') else 0 if context.get('is_client') is False else None,
                    1 if context.get('is_multi_project') else 0 if context.get('is_multi_project') is False else None,
                    1 if context.get('is_decision_maker') else 0 if context.get('is_decision_maker') is False else None,
                    context.get('email_handling_preference', 'default'),
                    context.get('default_category'),
                    context.get('default_subcategory'),
                    context.get('company_type'),
                    original_notes,
                    json.dumps(context) if context else None,
                    learned_from,
                    source_suggestion_id,
                    source_email_id,
                    0.7  # Initial confidence
                ))

                context_id = cursor.lastrowid

                # Log history
                cursor.execute("""
                    INSERT INTO contact_context_history (
                        context_id, email, change_type, new_values,
                        change_reason, source_suggestion_id, source_email_id
                    ) VALUES (?, ?, 'created', ?, ?, ?, ?)
                """, (
                    context_id, email, json.dumps(context),
                    original_notes, source_suggestion_id, source_email_id
                ))

                conn.commit()
                logger.info(f"Created contact context for {email}: {context}")
                return context_id

    # =========================================================================
    # CONTEXT RETRIEVAL
    # =========================================================================

    def get_contact_context(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get stored context for a contact.

        Args:
            email: Contact's email address

        Returns:
            Context dict or None if not found
        """
        if not email:
            return None

        email = email.lower().strip()

        result = self.execute_query("""
            SELECT
                cc.*,
                c.name as contact_name
            FROM contact_context cc
            LEFT JOIN contacts c ON cc.contact_id = c.contact_id
            WHERE cc.email = ?
        """, [email])

        if result:
            context = dict(result[0])
            # Convert booleans
            for field in ['is_client', 'is_multi_project', 'is_decision_maker']:
                if context.get(field) is not None:
                    context[field] = bool(context[field])
            return context

        return None

    def get_context_by_sender(self, sender_email: str) -> Optional[Dict[str, Any]]:
        """
        Get context for an email sender, handling various email formats.

        Handles:
        - "John Smith <john@example.com>"
        - "john@example.com"
        - Partial matches

        Args:
            sender_email: The sender string from an email

        Returns:
            Context dict or None
        """
        if not sender_email:
            return None

        # Extract email from "Name <email>" format
        email_match = re.search(r'<([^>]+)>', sender_email)
        clean_email = email_match.group(1) if email_match else sender_email
        clean_email = clean_email.lower().strip()

        # Try exact match first
        context = self.get_contact_context(clean_email)
        if context:
            return context

        # Try partial match on domain
        domain = clean_email.split('@')[-1] if '@' in clean_email else None
        if domain:
            result = self.execute_query("""
                SELECT * FROM contact_context
                WHERE email LIKE ?
                AND confidence > 0.5
                ORDER BY confidence DESC
                LIMIT 1
            """, [f"%@{domain}"])

            if result:
                context = dict(result[0])
                # Mark as partial match
                context['_match_type'] = 'domain'
                return context

        return None

    def should_skip_project_linking(self, sender_email: str) -> bool:
        """
        Check if emails from this sender should skip project linking.

        Returns True if:
        - Contact is multi-project
        - Contact's email_handling_preference is 'categorize_only'
        - Contact is internal (not project-related)

        Args:
            sender_email: Email sender

        Returns:
            True if should skip project linking
        """
        context = self.get_context_by_sender(sender_email)
        if not context:
            return False

        # Skip if multi-project
        if context.get('is_multi_project'):
            return True

        # Skip if handling preference says so
        if context.get('email_handling_preference') == 'categorize_only':
            return True

        # Skip if internal
        if context.get('relationship_type') == 'internal':
            return True

        return False

    def get_email_category_for_contact(self, sender_email: str) -> Optional[Dict[str, str]]:
        """
        Get the suggested email category for a contact.

        Args:
            sender_email: Email sender

        Returns:
            Dict with 'category' and 'subcategory' or None
        """
        context = self.get_context_by_sender(sender_email)
        if not context:
            return None

        result = {}
        if context.get('default_category'):
            result['category'] = context['default_category']
        if context.get('default_subcategory'):
            result['subcategory'] = context['default_subcategory']

        # Derive category from relationship if not explicitly set
        if not result.get('category') and context.get('relationship_type'):
            category_map = {
                'client': 'Client',
                'client_team': 'Client',
                'vendor': 'External',
                'contractor': 'External',
                'internal': 'Internal',
                'external': 'External'
            }
            result['category'] = category_map.get(context['relationship_type'])

        return result if result else None

    def get_display_info_for_contact(self, sender_email: str) -> Optional[Dict[str, str]]:
        """
        Get display info for a contact (for UI enhancement).

        Args:
            sender_email: Email sender

        Returns:
            Dict with 'role', 'relationship', 'display_label' or None
        """
        context = self.get_context_by_sender(sender_email)
        if not context:
            return None

        result = {}

        if context.get('role'):
            result['role'] = context['role']

        if context.get('relationship_type') and context['relationship_type'] != 'unknown':
            result['relationship'] = context['relationship_type']

        # Build display label like "Kitchen Consultant" or "Internal - IT"
        if context.get('role'):
            result['display_label'] = context['role'].title()
        elif context.get('relationship_type') != 'unknown':
            label_parts = [context['relationship_type'].title()]
            if context.get('default_subcategory'):
                label_parts.append(context['default_subcategory'])
            result['display_label'] = ' - '.join(label_parts)

        if context.get('is_multi_project'):
            result['badge'] = 'Multi-Project'

        return result if result else None

    # =========================================================================
    # LEARNING FROM FEEDBACK
    # =========================================================================

    def learn_from_suggestion_feedback(
        self,
        suggestion_id: int,
        user_notes: str,
        sender_email: str,
        source_email_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Learn contact context from user feedback on a suggestion.

        This is the main entry point called when a user approves/rejects
        a suggestion and provides notes.

        Args:
            suggestion_id: The suggestion being reviewed
            user_notes: User's notes/explanation
            sender_email: Email address of the contact
            source_email_id: The email that triggered the suggestion

        Returns:
            Dict with extracted context and context_id
        """
        if not user_notes or not sender_email:
            return {'success': False, 'error': 'Missing notes or email'}

        # Extract context from notes
        extracted = self.extract_context_from_notes(user_notes, sender_email)

        if not extracted:
            return {
                'success': False,
                'error': 'Could not extract context from notes',
                'notes': user_notes
            }

        # Store the context
        context_id = self.store_contact_context(
            email=sender_email,
            context=extracted,
            learned_from='user_correction',
            source_suggestion_id=suggestion_id,
            source_email_id=source_email_id,
            original_notes=user_notes
        )

        return {
            'success': True,
            'context_id': context_id,
            'extracted': extracted,
            'email': sender_email
        }

    # =========================================================================
    # BULK OPERATIONS
    # =========================================================================

    def get_multi_project_contacts(self) -> List[Dict[str, Any]]:
        """Get all contacts marked as multi-project"""
        results = self.execute_query("""
            SELECT
                cc.email,
                cc.role,
                cc.company,
                cc.context_notes,
                cc.confidence,
                c.name as contact_name
            FROM contact_context cc
            LEFT JOIN contacts c ON cc.contact_id = c.contact_id
            WHERE cc.is_multi_project = 1
            ORDER BY cc.confidence DESC
        """, [])

        return [dict(r) for r in results]

    def get_context_stats(self) -> Dict[str, Any]:
        """Get statistics about stored contact context"""
        stats = {}

        # Total contacts with context
        result = self.execute_query(
            "SELECT COUNT(*) as count FROM contact_context", []
        )
        stats['total_contacts'] = result[0]['count'] if result else 0

        # By relationship type
        result = self.execute_query("""
            SELECT relationship_type, COUNT(*) as count
            FROM contact_context
            GROUP BY relationship_type
        """, [])
        stats['by_relationship'] = {r['relationship_type']: r['count'] for r in result}

        # Multi-project contacts
        result = self.execute_query(
            "SELECT COUNT(*) as count FROM contact_context WHERE is_multi_project = 1", []
        )
        stats['multi_project_contacts'] = result[0]['count'] if result else 0

        # By learned_from source
        result = self.execute_query("""
            SELECT learned_from, COUNT(*) as count
            FROM contact_context
            WHERE learned_from IS NOT NULL
            GROUP BY learned_from
        """, [])
        stats['by_source'] = {r['learned_from']: r['count'] for r in result}

        # Average confidence
        result = self.execute_query(
            "SELECT AVG(confidence) as avg FROM contact_context", []
        )
        stats['avg_confidence'] = round(result[0]['avg'] or 0, 3)

        return stats


# Module-level singleton
_service = None


def get_contact_context_service() -> ContactContextService:
    """Get the singleton contact context service instance"""
    global _service
    if _service is None:
        # Use the same DB path as other services
        from api.dependencies import DB_PATH
        _service = ContactContextService(db_path=DB_PATH)
    return _service
