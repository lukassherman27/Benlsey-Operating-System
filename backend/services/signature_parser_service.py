"""
Signature Parser Service - Extract contact info from email signatures

Parses email signatures to extract:
- Phone numbers (mobile, office)
- Job titles
- Company names
- LinkedIn URLs
- Location/address hints

Part of Issue #19: Contact Auto-Research
"""

import re
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from .base_service import BaseService

logger = logging.getLogger(__name__)


@dataclass
class ExtractedData:
    """Holds extracted signature data with confidence scores"""
    phone: Optional[str] = None
    phone_confidence: float = 0.0
    title: Optional[str] = None
    title_confidence: float = 0.0
    company: Optional[str] = None
    company_confidence: float = 0.0
    linkedin_url: Optional[str] = None
    linkedin_confidence: float = 0.0
    location: Optional[str] = None
    location_confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, only including non-None values"""
        result = {}
        if self.phone:
            result['phone'] = self.phone
            result['phone_confidence'] = self.phone_confidence
        if self.title:
            result['title'] = self.title
            result['title_confidence'] = self.title_confidence
        if self.company:
            result['company'] = self.company
            result['company_confidence'] = self.company_confidence
        if self.linkedin_url:
            result['linkedin_url'] = self.linkedin_url
            result['linkedin_confidence'] = self.linkedin_confidence
        if self.location:
            result['location'] = self.location
            result['location_confidence'] = self.location_confidence
        return result

    def has_data(self) -> bool:
        """Check if any data was extracted"""
        return any([self.phone, self.title, self.company, self.linkedin_url, self.location])

    def overall_confidence(self) -> float:
        """Average confidence of all extracted fields"""
        confidences = []
        if self.phone:
            confidences.append(self.phone_confidence)
        if self.title:
            confidences.append(self.title_confidence)
        if self.company:
            confidences.append(self.company_confidence)
        if self.linkedin_url:
            confidences.append(self.linkedin_confidence)
        if self.location:
            confidences.append(self.location_confidence)
        return sum(confidences) / len(confidences) if confidences else 0.0


class SignatureParserService(BaseService):
    """
    Parses email signatures to extract contact information.

    Uses a combination of:
    1. Signature block detection (heuristics)
    2. Regex patterns for structured data (phone, LinkedIn)
    3. Dictionary-based matching for job titles
    4. Position-based inference for company names
    """

    # Common signature start markers
    SIGNATURE_MARKERS = [
        r'^best\s*regards?,?$',
        r'^kind\s*regards?,?$',
        r'^regards?,?$',
        r'^sincerely,?$',
        r'^thanks?,?$',
        r'^thank\s*you,?$',
        r'^cheers,?$',
        r'^warm\s*regards?,?$',
        r'^best,?$',
        r'^cordially,?$',
        r'^respectfully,?$',
    ]

    # Patterns to detect reply/forward markers (signature ends before these)
    REPLY_MARKERS = [
        r'^>',  # Quote marker
        r'^On\s+.+wrote:?$',  # "On Mon wrote:"
        r'^From:.*<.*@.*>',  # "From: Name <email>"
        r'^Sent:',  # "Sent: Date"
        r'^-{3,}\s*Original\s*Message',  # "--- Original Message"
        r'^_{3,}',  # Underscores separator
    ]

    # Phone number patterns (international)
    PHONE_PATTERNS = [
        # Labeled phones: Tel: +1 234 567 8901
        (r'(?:Tel|Phone|T|P|M|Mobile|Office|Work|Cell)[\s.:]*([+\d\s\-\(\)]{10,25})', 0.95),
        # International format: +1-234-567-8901 or +1 234 567 8901
        (r'(\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{2,4}[\s\-]?\d{2,4}[\s\-]?\d{0,4})', 0.85),
        # US format: (123) 456-7890
        (r'\((\d{3})\)[\s\-]?(\d{3})[\s\-]?(\d{4})', 0.80),
    ]

    # LinkedIn URL pattern
    LINKEDIN_PATTERN = r'(?:https?://)?(?:www\.)?linkedin\.com/in/([\w\-]+)'

    # Common job title keywords
    JOB_TITLE_KEYWORDS = {
        # C-Suite
        'ceo', 'cfo', 'cto', 'coo', 'cmo', 'cio',
        'chief executive', 'chief financial', 'chief technology',
        'chief operating', 'chief marketing', 'chief information',
        # Directors
        'director', 'managing director', 'executive director',
        'creative director', 'art director', 'design director',
        # VPs
        'vice president', 'vp', 'svp', 'evp',
        # Managers
        'manager', 'general manager', 'project manager',
        'account manager', 'sales manager', 'marketing manager',
        'development manager', 'operations manager',
        # Heads
        'head of', 'head',
        # Leads
        'lead', 'team lead', 'tech lead',
        # Specialists
        'specialist', 'senior', 'junior', 'associate',
        # Common titles
        'architect', 'designer', 'developer', 'engineer',
        'consultant', 'advisor', 'analyst', 'coordinator',
        'executive', 'officer', 'president', 'partner',
        'founder', 'co-founder', 'owner', 'principal',
    }

    # Company name indicators (words that suggest company name follows/precedes)
    COMPANY_INDICATORS = [
        r'(?:LLC|Inc\.?|Ltd\.?|Corp\.?|Corporation|Company|Co\.?|Group|Holdings?|Partners?|Associates?|LLP|PLC|GmbH|Pte|Pvt)\b',
    ]

    # Location indicators
    LOCATION_PATTERNS = [
        # City, Country format
        (r',\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*$', 0.7),
        # Address with common elements
        (r'(\d+\s+[A-Za-z\s,]+(?:Road|Street|Ave|Avenue|Blvd|Boulevard|Lane|Drive|Way))', 0.8),
    ]

    def __init__(self, db_path: str = None):
        super().__init__(db_path)

    def extract_signature_block(self, email_body: str) -> Optional[str]:
        """
        Extract the signature block from an email body.

        For incoming emails (what we care about), the sender's signature appears
        at the TOP of the email, before any "From:" or quoted reply sections.

        Strategy:
        1. First, find where quoted replies/forwards begin
        2. Look for signature markers in the FIRST part of the email (before quotes)
        3. Extract the block between the greeting/first line and the signature marker
        """
        if not email_body:
            return None

        lines = email_body.split('\n')

        # First, find where the ORIGINAL message part ends (before quotes/forwards)
        original_end = len(lines)
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            # Look for reply/forward markers
            for pattern in self.REPLY_MARKERS:
                if re.match(pattern, line_stripped, re.IGNORECASE):
                    original_end = i
                    break
            # Also check for "From: ... <email>" patterns indicating forward
            if re.match(r'^From:\s*.*<.*@.*>', line_stripped, re.IGNORECASE):
                original_end = i
                break
            # Check for "On ... wrote:" pattern
            if re.search(r'^On\s+.+\s+wrote:', line_stripped, re.IGNORECASE):
                original_end = i
                break
            if original_end != len(lines):
                break

        # Now look at only the original message part
        original_lines = lines[:original_end]

        # Find signature marker in the original part
        signature_start = None
        for i, line in enumerate(original_lines):
            line_clean = line.strip().lower()
            for pattern in self.SIGNATURE_MARKERS:
                if re.match(pattern, line_clean, re.IGNORECASE):
                    signature_start = i + 1  # Start after the marker
                    break
            if signature_start:
                break

        # If no marker found, take the last 12 lines of the original message
        if signature_start is None:
            signature_start = max(0, len(original_lines) - 12)

        # Extract signature block
        if signature_start < len(original_lines):
            signature_lines = original_lines[signature_start:]
            # Filter out empty lines at start and end
            while signature_lines and not signature_lines[0].strip():
                signature_lines.pop(0)
            while signature_lines and not signature_lines[-1].strip():
                signature_lines.pop()
            if signature_lines:
                return '\n'.join(signature_lines)

        return None

    def extract_phone(self, text: str) -> Tuple[Optional[str], float]:
        """Extract phone number from text with confidence score."""
        if not text:
            return None, 0.0

        for pattern, confidence in self.PHONE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Clean up the phone number
                if match.lastindex and match.lastindex > 1:
                    # Multiple capture groups (like US format)
                    phone = ''.join(match.groups())
                else:
                    phone = match.group(1) if match.lastindex else match.group(0)

                # Clean and normalize
                phone = re.sub(r'[\s\-\(\)]', '', phone)
                phone = phone.strip()

                # Validate: should be 10+ digits
                digits = re.sub(r'\D', '', phone)
                if len(digits) >= 10:
                    return phone, confidence

        return None, 0.0

    def extract_linkedin(self, text: str) -> Tuple[Optional[str], float]:
        """Extract LinkedIn URL from text."""
        if not text:
            return None, 0.0

        match = re.search(self.LINKEDIN_PATTERN, text, re.IGNORECASE)
        if match:
            # Reconstruct full URL
            username = match.group(1)
            return f"https://linkedin.com/in/{username}", 0.95

        return None, 0.0

    def extract_job_title(self, signature_text: str) -> Tuple[Optional[str], float]:
        """
        Extract job title from signature.

        Strategy:
        1. Look for lines containing known job title keywords
        2. Title is usually 1-2 lines after the person's name
        3. Title line is usually shorter than 100 chars
        """
        if not signature_text:
            return None, 0.0

        lines = [l.strip() for l in signature_text.split('\n') if l.strip()]

        for i, line in enumerate(lines):
            # Skip very long lines (probably not titles)
            if len(line) > 100:
                continue

            # Skip lines that look like addresses or contact info
            if re.search(r'@|www\.|http|tel:|phone:|mobile:', line, re.IGNORECASE):
                continue

            line_lower = line.lower()

            # Check for job title keywords
            for keyword in self.JOB_TITLE_KEYWORDS:
                if keyword in line_lower:
                    # Found a title keyword
                    # Clean up the line
                    title = line.strip()
                    # Remove any trailing punctuation
                    title = re.sub(r'[,;|]+$', '', title).strip()

                    if len(title) > 5 and len(title) < 80:
                        # Higher confidence if it's early in the signature
                        confidence = 0.85 if i < 3 else 0.70
                        return title, confidence

        return None, 0.0

    def extract_company(self, signature_text: str, known_email_domain: str = None) -> Tuple[Optional[str], float]:
        """
        Extract company name from signature.

        Strategy:
        1. Look for lines with company indicators (LLC, Inc, etc.)
        2. Check email domain as fallback hint
        3. Company name often appears after title line
        """
        if not signature_text:
            return None, 0.0

        lines = [l.strip() for l in signature_text.split('\n') if l.strip()]

        for i, line in enumerate(lines):
            # Skip very long lines
            if len(line) > 150:
                continue

            # Skip contact info lines
            if re.search(r'@|tel:|phone:|mobile:|www\.|http', line, re.IGNORECASE):
                continue

            # Check for company indicators
            for indicator in self.COMPANY_INDICATORS:
                if re.search(indicator, line, re.IGNORECASE):
                    company = line.strip()
                    # Clean up
                    company = re.sub(r'^[,\-–•|]\s*', '', company)
                    company = re.sub(r'[,;|]+$', '', company).strip()

                    if len(company) > 3 and len(company) < 100:
                        return company, 0.85

        # Fallback: Try to infer from email domain
        if known_email_domain:
            # Remove common email providers
            if known_email_domain not in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']:
                # Convert domain to company name guess
                company_guess = known_email_domain.split('.')[0].title()
                if len(company_guess) > 2:
                    return company_guess, 0.50

        return None, 0.0

    def extract_location(self, signature_text: str) -> Tuple[Optional[str], float]:
        """Extract location/address hints from signature."""
        if not signature_text:
            return None, 0.0

        # Look for address-like patterns
        for pattern, confidence in self.LOCATION_PATTERNS:
            match = re.search(pattern, signature_text, re.MULTILINE)
            if match:
                location = match.group(1).strip()
                if len(location) > 3 and len(location) < 100:
                    return location, confidence

        return None, 0.0

    def parse_signature(self, email_body: str, sender_email: str = None) -> ExtractedData:
        """
        Parse an email body and extract all contact information from signature.

        Args:
            email_body: Full email body text
            sender_email: Optional sender email for domain hints

        Returns:
            ExtractedData with all extracted fields and confidence scores
        """
        result = ExtractedData()

        # Extract signature block
        signature = self.extract_signature_block(email_body)
        if not signature:
            logger.debug("No signature block found")
            return result

        # Extract email domain for hints
        email_domain = None
        if sender_email:
            match = re.search(r'@([\w\-\.]+)', sender_email)
            if match:
                email_domain = match.group(1).lower()

        # Extract each field
        result.phone, result.phone_confidence = self.extract_phone(signature)
        result.linkedin_url, result.linkedin_confidence = self.extract_linkedin(signature)
        result.title, result.title_confidence = self.extract_job_title(signature)
        result.company, result.company_confidence = self.extract_company(signature, email_domain)
        result.location, result.location_confidence = self.extract_location(signature)

        logger.debug(f"Extracted from signature: {result.to_dict()}")
        return result

    def enrich_contact_from_emails(
        self,
        contact_id: int,
        contact_email: str,
        create_suggestions: bool = True
    ) -> Dict[str, Any]:
        """
        Enrich a contact by parsing signatures from their emails.

        Args:
            contact_id: ID of the contact to enrich
            contact_email: Email address of the contact
            create_suggestions: Whether to create update_contact suggestions

        Returns:
            Dict with extraction results and any created suggestion IDs
        """
        if not contact_email:
            return {'success': False, 'error': 'No email address provided'}

        # Clean email address
        match = re.search(r'<([^>]+@[^>]+)>', contact_email)
        clean_email = match.group(1).lower() if match else contact_email.lower().strip()

        # Get emails from this contact
        emails = self.execute_query("""
            SELECT email_id, body_full, subject, date
            FROM emails
            WHERE LOWER(sender_email) LIKE ?
            AND body_full IS NOT NULL
            AND LENGTH(body_full) > 50
            ORDER BY date DESC
            LIMIT 10
        """, (f'%{clean_email}%',))

        if not emails:
            return {
                'success': False,
                'error': f'No emails with body content found for {clean_email}',
                'emails_checked': 0
            }

        # Try to extract from each email, keep best results
        best_result = ExtractedData()
        extraction_sources = []

        for email in emails:
            extracted = self.parse_signature(email['body_full'], clean_email)
            if extracted.has_data():
                # Update best result with higher-confidence extractions
                if extracted.phone_confidence > best_result.phone_confidence:
                    best_result.phone = extracted.phone
                    best_result.phone_confidence = extracted.phone_confidence
                if extracted.title_confidence > best_result.title_confidence:
                    best_result.title = extracted.title
                    best_result.title_confidence = extracted.title_confidence
                if extracted.company_confidence > best_result.company_confidence:
                    best_result.company = extracted.company
                    best_result.company_confidence = extracted.company_confidence
                if extracted.linkedin_confidence > best_result.linkedin_confidence:
                    best_result.linkedin_url = extracted.linkedin_url
                    best_result.linkedin_confidence = extracted.linkedin_confidence
                if extracted.location_confidence > best_result.location_confidence:
                    best_result.location = extracted.location
                    best_result.location_confidence = extracted.location_confidence

                extraction_sources.append({
                    'email_id': email['email_id'],
                    'subject': email['subject'],
                    'extracted': extracted.to_dict()
                })

        if not best_result.has_data():
            return {
                'success': True,
                'message': 'No data could be extracted from signatures',
                'emails_checked': len(emails),
                'extracted': {}
            }

        # Get current contact data to compare
        contact = self.execute_query(
            "SELECT * FROM contacts WHERE contact_id = ?",
            (contact_id,),
            fetch_one=True
        )

        if not contact:
            return {'success': False, 'error': f'Contact {contact_id} not found'}

        # Determine what fields need updating (only update if current value is empty)
        updates_needed = {}
        if best_result.phone and not contact.get('phone'):
            updates_needed['phone'] = {
                'value': best_result.phone,
                'confidence': best_result.phone_confidence
            }
        if best_result.title and not contact.get('role'):
            updates_needed['role'] = {
                'value': best_result.title,
                'confidence': best_result.title_confidence
            }
        if best_result.company and not contact.get('company'):
            updates_needed['company'] = {
                'value': best_result.company,
                'confidence': best_result.company_confidence
            }
        if best_result.linkedin_url and not contact.get('linkedin_url'):
            updates_needed['linkedin_url'] = {
                'value': best_result.linkedin_url,
                'confidence': best_result.linkedin_confidence
            }
        if best_result.location and not contact.get('location'):
            updates_needed['location'] = {
                'value': best_result.location,
                'confidence': best_result.location_confidence
            }

        result = {
            'success': True,
            'emails_checked': len(emails),
            'emails_with_signatures': len(extraction_sources),
            'extracted': best_result.to_dict(),
            'updates_needed': updates_needed,
            'suggestion_ids': []
        }

        # Create suggestion if updates are needed
        if updates_needed and create_suggestions:
            suggestion_id = self._create_enrichment_suggestion(
                contact_id=contact_id,
                contact_email=clean_email,
                contact_name=contact.get('name', 'Unknown'),
                updates=updates_needed,
                sources=extraction_sources[:3]  # Include top 3 sources
            )
            if suggestion_id:
                result['suggestion_ids'].append(suggestion_id)

        return result

    def _create_enrichment_suggestion(
        self,
        contact_id: int,
        contact_email: str,
        contact_name: str,
        updates: Dict[str, Any],
        sources: List[Dict]
    ) -> Optional[int]:
        """Create an update_contact suggestion for enrichment data."""

        # Calculate overall confidence
        confidences = [u['confidence'] for u in updates.values()]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Build description
        fields = list(updates.keys())
        field_str = ', '.join(fields)

        suggested_data = {
            'contact_id': contact_id,
            'contact_email': contact_email,
            'updates': {k: v['value'] for k, v in updates.items()},
            'confidences': {k: v['confidence'] for k, v in updates.items()},
            'source': 'email_signature',
            'source_emails': [s['email_id'] for s in sources]
        }

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ai_suggestions (
                        suggestion_type, priority, confidence_score,
                        source_type, source_id, source_reference,
                        title, description, suggested_action,
                        suggested_data, target_table, target_id,
                        status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', datetime('now'))
                """, (
                    'update_contact',
                    'medium' if avg_confidence >= 0.7 else 'low',
                    avg_confidence,
                    'contact',
                    contact_id,
                    f"Contact: {contact_name}",
                    f"Enrich contact: {contact_name}",
                    f"Extracted {field_str} from email signatures",
                    "Update contact fields",
                    json.dumps(suggested_data),
                    'contacts',
                    contact_id,
                ))
                conn.commit()
                suggestion_id = cursor.lastrowid
                logger.info(f"Created enrichment suggestion {suggestion_id} for contact {contact_id}")
                return suggestion_id

        except Exception as e:
            logger.error(f"Failed to create enrichment suggestion: {e}")
            return None

    def batch_enrich_contacts(
        self,
        proposal_related_first: bool = True,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Batch enrich contacts that are missing data.

        Args:
            proposal_related_first: Prioritize contacts linked to proposals
            limit: Maximum number of contacts to process

        Returns:
            Summary of enrichment results
        """
        # Get contacts needing enrichment
        if proposal_related_first:
            # Prioritize contacts linked to proposals via emails
            query = """
                SELECT DISTINCT c.contact_id, c.email, c.name, c.company, c.role, c.phone
                FROM contacts c
                JOIN emails e ON LOWER(e.sender_email) LIKE '%' || LOWER(c.email) || '%'
                JOIN email_project_links epl ON e.email_id = epl.email_id
                WHERE (c.company IS NULL OR c.company = ''
                    OR c.role IS NULL OR c.role = ''
                    OR c.phone IS NULL OR c.phone = '')
                LIMIT ?
            """
        else:
            query = """
                SELECT contact_id, email, name, company, role, phone
                FROM contacts
                WHERE (company IS NULL OR company = ''
                    OR role IS NULL OR role = ''
                    OR phone IS NULL OR phone = '')
                LIMIT ?
            """

        contacts = self.execute_query(query, (limit,))

        results = {
            'total_processed': 0,
            'enriched': 0,
            'no_data_found': 0,
            'errors': 0,
            'suggestions_created': 0,
            'details': []
        }

        for contact in contacts:
            results['total_processed'] += 1
            try:
                result = self.enrich_contact_from_emails(
                    contact_id=contact['contact_id'],
                    contact_email=contact['email'],
                    create_suggestions=True
                )

                if result.get('updates_needed'):
                    results['enriched'] += 1
                    results['suggestions_created'] += len(result.get('suggestion_ids', []))
                else:
                    results['no_data_found'] += 1

                results['details'].append({
                    'contact_id': contact['contact_id'],
                    'email': contact['email'],
                    'result': result
                })

            except Exception as e:
                results['errors'] += 1
                logger.error(f"Error enriching contact {contact['contact_id']}: {e}")

        return results


# Module-level singleton
_service = None


def get_signature_parser_service() -> SignatureParserService:
    """Get the singleton signature parser service instance"""
    global _service
    if _service is None:
        from api.dependencies import DB_PATH
        _service = SignatureParserService(db_path=DB_PATH)
    return _service
