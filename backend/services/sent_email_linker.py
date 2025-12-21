"""
Sent Email Linker - Links outbound @bensley.com emails to proposals via recipients

Match hierarchy:
1. Project code in subject/body (confidence: 0.95)
2. proposals.contact_email match (confidence: 0.95)
3. contacts → project_contact_links match (confidence: 0.85)
4. Domain patterns from email_learned_patterns (confidence: 0.70)

Usage:
    from backend.services.sent_email_linker import SentEmailLinker
    linker = SentEmailLinker('database/bensley_master.db')
    result = linker.link_sent_email(email_dict)
"""

import re
import logging
from typing import Dict, List, Optional, Any
from .base_service import BaseService

logger = logging.getLogger(__name__)

# Bensley internal domains
BENSLEY_DOMAINS = frozenset([
    'bensley.com', 'bensleydesign.com', 'bensley.co.th', 'bensley.co.id'
])

# Project code pattern: 25 BK-033, 24BK-015, 25 BK 087, etc.
PROJECT_CODE_PATTERN = re.compile(r'\b(\d{2})\s*BK[-\s]?(\d{3})\b', re.IGNORECASE)


def extract_email_address(raw: str) -> Optional[str]:
    """Extract clean email from RFC 5322 format like 'Name <email@domain.com>'"""
    if not raw:
        return None
    # Try to extract from angle brackets first
    match = re.search(r'<([^>]+@[^>]+)>', raw)
    if match:
        return match.group(1).lower().strip()
    # Otherwise check if it looks like an email
    if '@' in raw:
        # Clean up any quotes or extra spaces
        clean = raw.strip().strip('"').strip("'").lower()
        return clean
    return None


def extract_domain(email: str) -> Optional[str]:
    """Extract domain from email address"""
    if not email or '@' not in email:
        return None
    return email.split('@')[1].lower()


class SentEmailLinker(BaseService):
    """Service for linking sent emails to proposals via recipient matching"""

    def __init__(self, db_path: str = None):
        super().__init__(db_path)

    def is_sent_email(self, email: Dict) -> bool:
        """Check if email is FROM a bensley domain"""
        sender = extract_email_address(email.get('sender_email', ''))
        if not sender:
            return False
        domain = extract_domain(sender)
        return domain in BENSLEY_DOMAINS if domain else False

    def extract_recipients(self, email: Dict) -> List[str]:
        """
        Extract all external recipient emails from To, CC fields.
        Skips internal @bensley.com recipients.
        """
        recipients = []

        # Check recipient_emails field (may be comma-separated or JSON)
        raw_recipients = email.get('recipient_emails', '') or ''

        # Split by comma and clean each
        for part in raw_recipients.split(','):
            addr = extract_email_address(part.strip())
            if addr and '@' in addr:
                domain = extract_domain(addr)
                # Skip internal recipients
                if domain and domain not in BENSLEY_DOMAINS:
                    recipients.append(addr)

        return list(set(recipients))

    def normalize_project_code(self, raw: str) -> str:
        """Normalize project code to standard format: '25 BK-033'"""
        match = PROJECT_CODE_PATTERN.search(raw)
        if match:
            year = match.group(1)
            num = match.group(2)
            return f"{year} BK-{num}"
        return raw

    def match_by_project_code(self, email: Dict) -> Optional[Dict]:
        """
        Priority 1: Find project code in subject or body.
        Returns match with 0.95 confidence.
        """
        subject = email.get('subject', '') or ''
        body = (email.get('body_full', '') or '')[:2000]  # First 2000 chars
        text = f"{subject} {body}"

        matches = PROJECT_CODE_PATTERN.findall(text)

        for match in matches:
            year, num = match
            project_code = f"{year} BK-{num}"

            proposal = self.execute_query("""
                SELECT proposal_id, project_code, project_name
                FROM proposals WHERE project_code = ?
            """, (project_code,), fetch_one=True)

            if proposal:
                return {
                    'target_type': 'proposal',
                    'target_id': proposal['proposal_id'],
                    'target_code': proposal['project_code'],
                    'target_name': proposal['project_name'],
                    'confidence': 0.95,
                    'match_type': 'project_code_in_sent',
                    'reason': f"Project code {project_code} found in sent email"
                }

        return None

    def match_by_recipient(self, recipients: List[str]) -> Optional[Dict]:
        """
        Priority 2-3: Match recipient to proposal via contact_email or contacts table.
        """
        for recipient in recipients:
            # Check proposals.contact_email first (highest confidence)
            proposal = self.execute_query("""
                SELECT proposal_id, project_code, project_name
                FROM proposals
                WHERE LOWER(TRIM(contact_email)) = ?
            """, (recipient,), fetch_one=True)

            if proposal:
                return {
                    'target_type': 'proposal',
                    'target_id': proposal['proposal_id'],
                    'target_code': proposal['project_code'],
                    'target_name': proposal['project_name'],
                    'confidence': 0.95,
                    'match_type': 'recipient_contact_email',
                    'reason': f"Recipient {recipient} matches proposal contact"
                }

            # Check contacts table with project_contact_links
            contact_match = self.execute_query("""
                SELECT p.proposal_id, p.project_code, p.project_name,
                       c.name as contact_name, pcl.role
                FROM contacts c
                JOIN project_contact_links pcl ON c.contact_id = pcl.contact_id
                JOIN proposals p ON pcl.project_code = p.project_code
                WHERE LOWER(TRIM(c.email)) = ?
                ORDER BY pcl.confidence_score DESC
                LIMIT 1
            """, (recipient,), fetch_one=True)

            if contact_match:
                return {
                    'target_type': 'proposal',
                    'target_id': contact_match['proposal_id'],
                    'target_code': contact_match['project_code'],
                    'target_name': contact_match['project_name'],
                    'confidence': 0.85,
                    'match_type': 'recipient_contact_link',
                    'reason': f"Recipient {recipient} ({contact_match['contact_name']}) linked to proposal"
                }

        return None

    def match_by_domain_pattern(self, recipients: List[str]) -> Optional[Dict]:
        """
        Priority 4: Check domain patterns from learned patterns.
        Returns match with confidence from pattern (typically 0.70).
        """
        for recipient in recipients:
            domain = extract_domain(recipient)
            if not domain:
                continue

            pattern = self.execute_query("""
                SELECT target_id, target_code, target_name, confidence
                FROM email_learned_patterns
                WHERE pattern_type = 'domain_to_proposal'
                AND pattern_key_normalized = ?
                AND is_active = 1
                ORDER BY confidence DESC
                LIMIT 1
            """, (domain,), fetch_one=True)

            if pattern:
                return {
                    'target_type': 'proposal',
                    'target_id': pattern['target_id'],
                    'target_code': pattern['target_code'],
                    'target_name': pattern['target_name'],
                    'confidence': min(0.70, pattern['confidence'] or 0.70),
                    'match_type': 'recipient_domain_pattern',
                    'reason': f"Recipient domain @{domain} matches learned pattern"
                }

        return None

    def match_by_recipient_map_view(self, recipients: List[str]) -> Optional[Dict]:
        """
        Use the v_recipient_proposal_map view for consolidated lookup.
        """
        for recipient in recipients:
            match = self.execute_query("""
                SELECT proposal_id, project_code, project_name, source, confidence
                FROM v_recipient_proposal_map
                WHERE recipient_email = ?
                ORDER BY confidence DESC
                LIMIT 1
            """, (recipient,), fetch_one=True)

            if match:
                return {
                    'target_type': 'proposal',
                    'target_id': match['proposal_id'],
                    'target_code': match['project_code'],
                    'target_name': match['project_name'],
                    'confidence': match['confidence'],
                    'match_type': f'recipient_map_{match["source"]}',
                    'reason': f"Recipient {recipient} found in {match['source']}"
                }

        return None

    def link_sent_email(self, email: Dict) -> Dict:
        """
        Main entry point: Link a sent email to a proposal.

        Args:
            email: Dict with email_id, sender_email, recipient_emails, subject, body_full

        Returns:
            Dict with linked status, match details, or needs_review/needs_gpt status
        """
        email_id = email.get('email_id')

        # Verify this is a sent email
        if not self.is_sent_email(email):
            return {
                'linked': False,
                'method': 'not_sent_email',
                'email_id': email_id
            }

        # Extract external recipients
        recipients = self.extract_recipients(email)
        if not recipients:
            return {
                'linked': False,
                'method': 'no_external_recipients',
                'email_id': email_id,
                'reason': 'No external recipients found (internal-only email)'
            }

        # Priority 1: Project code in subject/body
        match = self.match_by_project_code(email)
        if match and match['confidence'] >= 0.90:
            return {'linked': True, 'email_id': email_id, **match}

        # Priority 2-3: Recipient matches (contact_email, contacts table)
        recipient_match = self.match_by_recipient(recipients)
        if recipient_match:
            return {'linked': True, 'email_id': email_id, **recipient_match}

        # Alternative: Use consolidated view
        view_match = self.match_by_recipient_map_view(recipients)
        if view_match:
            return {'linked': True, 'email_id': email_id, **view_match}

        # Priority 4: Domain patterns
        domain_match = self.match_by_domain_pattern(recipients)
        if domain_match:
            # Domain matches are lower confidence - suggest for review
            return {
                'linked': False,
                'method': 'needs_review',
                'email_id': email_id,
                'suggested_match': domain_match,
                'recipients': recipients
            }

        # No match found
        return {
            'linked': False,
            'method': 'no_match',
            'email_id': email_id,
            'recipients': recipients,
            'reason': 'No recipient pattern match found'
        }

    def apply_link(self, email_id: int, proposal_id: int,
                   confidence: float, match_method: str, reason: str = None) -> bool:
        """Apply a link between email and proposal"""
        try:
            self.execute_update("""
                INSERT OR IGNORE INTO email_proposal_links
                (email_id, proposal_id, confidence_score, match_method, match_reason, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (email_id, proposal_id, confidence, match_method, reason))
            return True
        except Exception as e:
            logger.error(f"Failed to apply link: {e}")
            return False

    def learn_from_approval(self, email_id: int, proposal_id: int) -> Dict:
        """
        When a sent email link is approved, learn the recipient pattern.
        Creates sender_to_proposal pattern for future emails from this sender.
        """
        email = self.execute_query("""
            SELECT recipient_emails FROM emails WHERE email_id = ?
        """, (email_id,), fetch_one=True)

        if not email:
            return {'success': False, 'error': 'Email not found'}

        proposal = self.execute_query("""
            SELECT proposal_id, project_code, project_name FROM proposals WHERE proposal_id = ?
        """, (proposal_id,), fetch_one=True)

        if not proposal:
            return {'success': False, 'error': 'Proposal not found'}

        recipients = self.extract_recipients(dict(email))
        patterns_created = []

        for recipient in recipients:
            # Create sender_to_proposal pattern for this recipient
            # So future emails FROM this contact will also link
            self.execute_update("""
                INSERT INTO email_learned_patterns
                (pattern_type, pattern_key, pattern_key_normalized, target_type,
                 target_id, target_code, target_name, confidence,
                 notes, is_active, created_at)
                VALUES ('sender_to_proposal', ?, ?, 'proposal', ?, ?, ?, 0.90,
                        'Learned from sent email approval', 1, datetime('now'))
                ON CONFLICT(pattern_type, pattern_key_normalized, target_type, target_id)
                DO UPDATE SET
                    confidence = MIN(confidence + 0.05, 0.98),
                    times_correct = times_correct + 1,
                    updated_at = datetime('now')
            """, (recipient, recipient, proposal_id,
                  proposal['project_code'], proposal['project_name']))
            patterns_created.append(f"sender_to_proposal: {recipient}")

        return {
            'success': True,
            'patterns_created': patterns_created,
            'message': f"Learned {len(patterns_created)} recipient patterns"
        }

    def process_unlinked_sent_emails(self, days_back: int = 30, limit: int = 200) -> Dict:
        """
        Process sent emails that haven't been linked yet.

        Returns summary of auto-linked, needs_review, and unmatched.
        """
        # Get unlinked sent emails
        emails = self.execute_query("""
            SELECT e.email_id, e.sender_email, e.recipient_emails,
                   e.subject, e.body_full, e.date, e.thread_id
            FROM emails e
            WHERE (e.email_direction IN ('sent', 'SENT', 'OUTBOUND', 'internal_to_external')
                   OR e.sender_email LIKE '%@bensley.com%')
            AND COALESCE(e.date, e.date_normalized) >= date('now', '-' || ? || ' days')
            AND NOT EXISTS (
                SELECT 1 FROM email_proposal_links epl WHERE epl.email_id = e.email_id
            )
            ORDER BY e.date DESC
            LIMIT ?
        """, (days_back, limit))

        results = {
            'total': len(emails),
            'auto_linked': 0,
            'needs_review': 0,
            'no_match': 0,
            'no_external_recipients': 0,
            'linked_emails': [],
            'review_emails': []
        }

        for email in emails:
            email_dict = dict(email)
            result = self.link_sent_email(email_dict)

            if result.get('linked'):
                # Apply the link
                success = self.apply_link(
                    email_dict['email_id'],
                    result['target_id'],
                    result['confidence'],
                    result['match_type'],
                    result.get('reason')
                )
                if success:
                    results['auto_linked'] += 1
                    results['linked_emails'].append({
                        'email_id': email_dict['email_id'],
                        'subject': email_dict.get('subject', '')[:50],
                        'project_code': result['target_code'],
                        'confidence': result['confidence']
                    })
            elif result.get('method') == 'needs_review':
                results['needs_review'] += 1
                results['review_emails'].append({
                    'email_id': email_dict['email_id'],
                    'subject': email_dict.get('subject', '')[:50],
                    'recipients': result.get('recipients', []),
                    'suggested': result.get('suggested_match')
                })
            elif result.get('method') == 'no_external_recipients':
                results['no_external_recipients'] += 1
            else:
                results['no_match'] += 1

        return results


# Singleton instance for easy import
_sent_linker_instance = None

def get_sent_linker(db_path: str = None) -> SentEmailLinker:
    """Get or create singleton SentEmailLinker instance"""
    global _sent_linker_instance
    if _sent_linker_instance is None or db_path:
        _sent_linker_instance = SentEmailLinker(db_path)
    return _sent_linker_instance
