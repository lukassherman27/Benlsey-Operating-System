"""
Batch Suggestion Service - Groups email suggestions by sender for efficient review

Confidence Tiers:
- AUTO_APPROVE (>0.90): High confidence, can be auto-applied
- BATCH_REVIEW (0.70-0.90): Group by sender, review as batch
- INDIVIDUAL (0.50-0.70): Needs individual review
- LOG_ONLY (<0.50): Too low confidence, log for reference only

This service replaces per-email suggestions with grouped batches.
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from .base_service import BaseService

logger = logging.getLogger(__name__)

# Confidence tier thresholds
TIER_AUTO_APPROVE = 0.90
TIER_BATCH_REVIEW = 0.70
TIER_INDIVIDUAL = 0.50

# Internal domains to skip
INTERNAL_DOMAINS = {'bensley.com', 'bensley.co.id', 'bensleydesign.com'}


class BatchSuggestionService(BaseService):
    """Service for creating and managing batched email suggestions"""

    def __init__(self, db_path: str = None):
        super().__init__(db_path)

    def _extract_email_address(self, sender: str) -> Optional[str]:
        """Extract clean email from RFC 5322 format"""
        if not sender:
            return None
        match = re.search(r'<([^>]+@[^>]+)>', sender)
        if match:
            return match.group(1).lower().strip()
        if '@' in sender:
            return sender.lower().strip()
        return None

    def _extract_domain(self, email: str) -> Optional[str]:
        """Extract domain from email address"""
        if not email or '@' not in email:
            return None
        return email.split('@')[1].lower()

    def _is_internal(self, email: str) -> bool:
        """Check if email is from internal domain"""
        domain = self._extract_domain(email)
        return domain in INTERNAL_DOMAINS if domain else False

    def _should_skip_domain(self, domain: str) -> Optional[str]:
        """Check if domain should be skipped (spam, newsletter, SaaS notifications)"""
        if not domain:
            return None
        result = self.execute_query("""
            SELECT pattern_id, target_code, target_name
            FROM email_learned_patterns
            WHERE pattern_key_normalized = ?
            AND pattern_type = 'domain_to_skip'
            AND is_active = 1
            LIMIT 1
        """, [domain.lower()])
        if result:
            row = dict(result[0])
            self._increment_pattern_usage(row['pattern_id'])
            return row['target_name']  # Return reason for skipping
        return None

    def _get_confidence_tier(self, confidence: float) -> str:
        """Determine confidence tier from score"""
        if confidence >= TIER_AUTO_APPROVE:
            return 'auto_approve'
        elif confidence >= TIER_BATCH_REVIEW:
            return 'batch_review'
        elif confidence >= TIER_INDIVIDUAL:
            return 'individual'
        else:
            return 'log_only'

    def process_emails_for_batches(
        self,
        hours: int = 24,
        limit: int = 500
    ) -> Dict[str, Any]:
        """
        Process recent emails and create batched suggestions.

        Instead of creating one suggestion per email, groups emails by sender
        and creates batch suggestions for efficient review.
        """
        results = {
            'emails_processed': 0,
            'batches_created': 0,
            'auto_approved': 0,
            'batch_review': 0,
            'individual': 0,
            'low_confidence_logged': 0,
            'skipped_internal': 0
        }

        # Get unprocessed emails with content
        # Use COALESCE to handle both date and date_normalized for compatibility
        emails = self.execute_query("""
            SELECT
                e.email_id, e.sender_email, e.subject,
                COALESCE(e.date, e.date_normalized) as date,
                ec.category, ec.linked_project_code
            FROM emails e
            JOIN email_content ec ON e.email_id = ec.email_id
            WHERE COALESCE(e.date, e.date_normalized) >= datetime('now', '-' || ? || ' hours')
            AND e.email_id NOT IN (
                SELECT email_id FROM batch_emails
            )
            AND e.email_id NOT IN (
                SELECT email_id FROM low_confidence_log
            )
            AND ec.linked_project_code IS NULL
            ORDER BY COALESCE(e.date, e.date_normalized) DESC
            LIMIT ?
        """, [hours, limit])

        if not emails:
            return results

        # Group emails by sender
        sender_groups: Dict[str, List[Dict]] = {}
        for email in emails:
            email = dict(email)
            sender = self._extract_email_address(email.get('sender_email', ''))

            if not sender:
                continue

            # Skip internal emails
            if self._is_internal(sender):
                results['skipped_internal'] += 1
                continue

            if sender not in sender_groups:
                sender_groups[sender] = []
            sender_groups[sender].append(email)

        results['emails_processed'] = sum(len(g) for g in sender_groups.values())

        # Process each sender group
        for sender, emails_in_group in sender_groups.items():
            batch_result = self._process_sender_group(sender, emails_in_group)

            if batch_result:
                tier = batch_result.get('tier')
                if tier == 'auto_approve':
                    results['auto_approved'] += 1
                elif tier == 'batch_review':
                    results['batch_review'] += 1
                elif tier == 'individual':
                    results['individual'] += len(emails_in_group)
                elif tier == 'log_only':
                    results['low_confidence_logged'] += len(emails_in_group)
                elif tier == 'skipped':
                    results['skipped_spam'] = results.get('skipped_spam', 0) + len(emails_in_group)

                if tier in ('auto_approve', 'batch_review', 'individual'):
                    results['batches_created'] += 1

        return results

    def _process_sender_group(
        self,
        sender: str,
        emails: List[Dict]
    ) -> Optional[Dict]:
        """
        Process a group of emails from the same sender.

        Finds the best project match and creates appropriate suggestion.
        """
        if not emails:
            return None

        # Check if this domain should be skipped (spam, SaaS notifications, etc.)
        domain = self._extract_domain(sender)
        skip_reason = self._should_skip_domain(domain)
        if skip_reason:
            logger.debug(f"Skipping {domain}: {skip_reason}")
            return {'tier': 'skipped', 'reason': skip_reason}

        # Get best project match for this sender
        match_result = self._find_best_project_match(sender, emails)

        if not match_result:
            # Log as low confidence if we can't find a match
            self._log_low_confidence_emails(emails, None, 0.0, "No project match found")
            return {'tier': 'log_only'}

        project_code = match_result['project_code']
        project_name = match_result['project_name']
        proposal_id = match_result.get('proposal_id')
        confidence = match_result['confidence']
        signals = match_result.get('signals', [])

        tier = self._get_confidence_tier(confidence)

        if tier == 'log_only':
            self._log_low_confidence_emails(
                emails, project_code, confidence,
                f"Low confidence: {', '.join(signals)}"
            )
            return {'tier': 'log_only'}

        # Create batch suggestion
        batch_id = self._create_batch(
            grouping_key=f"sender:{sender}",
            grouping_type='sender',
            project_code=project_code,
            project_name=project_name,
            proposal_id=proposal_id,
            confidence=confidence,
            tier=tier,
            emails=emails,
            signals=signals
        )

        # Auto-approve if high confidence
        if tier == 'auto_approve':
            self._auto_approve_batch(batch_id)

        return {
            'tier': tier,
            'batch_id': batch_id,
            'project_code': project_code,
            'confidence': confidence
        }

    def _find_best_project_match(
        self,
        sender: str,
        emails: List[Dict]
    ) -> Optional[Dict]:
        """
        Find the best project match for a sender's emails.

        Uses multiple signals:
        1. Learned patterns (sender/domain)
        2. Project code in subject
        3. Project name mentions
        """
        signals = []
        confidence = 0.0
        best_match = None

        # Check learned patterns first
        pattern_match = self._check_learned_patterns(sender)
        if pattern_match:
            signals.append(f"learned_pattern:{pattern_match['pattern_type']}")
            confidence = max(confidence, pattern_match['confidence'])
            best_match = pattern_match

        # Check for project codes in subjects
        for email in emails:
            subject = email.get('subject', '') or ''
            code_match = re.search(r'\b(\d{2}\s*BK[-\s]?\d{3})\b', subject, re.IGNORECASE)
            if code_match:
                code = self._normalize_project_code(code_match.group(1))
                project = self._get_proposal_by_code(code)
                if project:
                    signals.append(f"subject_code:{code}")
                    # Project code in subject is very strong signal
                    code_confidence = 0.95
                    if code_confidence > confidence:
                        confidence = code_confidence
                        best_match = {
                            'project_code': code,
                            'project_name': project['project_name'],
                            'proposal_id': project['proposal_id'],
                            'confidence': code_confidence
                        }

        # Check domain patterns
        domain = self._extract_domain(sender)
        if domain and not best_match:
            domain_match = self._check_domain_pattern(domain)
            if domain_match:
                signals.append(f"domain_pattern:{domain}")
                if domain_match['confidence'] > confidence:
                    confidence = domain_match['confidence']
                    best_match = domain_match

        if best_match:
            best_match['signals'] = signals
            best_match['confidence'] = confidence

        return best_match

    def _check_learned_patterns(self, sender: str) -> Optional[Dict]:
        """Check for learned sender patterns"""
        result = self.execute_query("""
            SELECT
                pattern_id, target_code, target_name, target_id, target_type,
                confidence, pattern_type
            FROM email_learned_patterns
            WHERE pattern_key_normalized = ?
            AND is_active = 1
            AND target_type = 'proposal'
            ORDER BY confidence DESC, times_correct DESC
            LIMIT 1
        """, [sender.lower()])

        if result:
            row = dict(result[0])
            # Increment times_used for analytics
            self._increment_pattern_usage(row['pattern_id'])
            return {
                'project_code': row['target_code'],
                'project_name': row['target_name'],
                'proposal_id': row['target_id'],
                'confidence': row['confidence'],
                'pattern_type': row['pattern_type'],
                'pattern_id': row['pattern_id']
            }
        return None

    def _check_domain_pattern(self, domain: str) -> Optional[Dict]:
        """Check for learned domain patterns"""
        result = self.execute_query("""
            SELECT
                pattern_id, target_code, target_name, target_id,
                confidence, pattern_type
            FROM email_learned_patterns
            WHERE pattern_key_normalized = ?
            AND pattern_type LIKE 'domain_%'
            AND is_active = 1
            AND target_type = 'proposal'
            ORDER BY confidence DESC
            LIMIT 1
        """, [domain.lower()])

        if result:
            row = dict(result[0])
            # Increment times_used for analytics
            self._increment_pattern_usage(row['pattern_id'])
            return {
                'project_code': row['target_code'],
                'project_name': row['target_name'],
                'proposal_id': row['target_id'],
                'confidence': row['confidence'],
                'pattern_type': row['pattern_type'],
                'pattern_id': row['pattern_id']
            }
        return None

    def _increment_pattern_usage(self, pattern_id: int):
        """Increment times_used counter for pattern analytics"""
        try:
            self.execute_update("""
                UPDATE email_learned_patterns
                SET times_used = times_used + 1,
                    last_used_at = datetime('now')
                WHERE pattern_id = ?
            """, [pattern_id])
        except Exception as e:
            logger.warning(f"Failed to increment pattern usage: {e}")

    def _normalize_project_code(self, code: str) -> str:
        """Normalize project code format"""
        normalized = re.sub(r'[\s-]+', ' ', code.upper()).strip()
        return re.sub(r'(\d{2})\s*BK\s*(\d{3})', r'\1 BK-\2', normalized)

    def _get_proposal_by_code(self, code: str) -> Optional[Dict]:
        """Get proposal details by project code"""
        result = self.execute_query("""
            SELECT proposal_id, project_code, project_name
            FROM proposals
            WHERE project_code = ?
        """, [code])
        return dict(result[0]) if result else None

    def _create_batch(
        self,
        grouping_key: str,
        grouping_type: str,
        project_code: str,
        project_name: str,
        proposal_id: int,
        confidence: float,
        tier: str,
        emails: List[Dict],
        signals: List[str]
    ) -> int:
        """Create a batch suggestion with associated emails"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Create batch
            cursor.execute("""
                INSERT INTO suggestion_batches (
                    grouping_key, grouping_type, suggested_project_code,
                    suggested_project_name, proposal_id, confidence_score,
                    confidence_tier, email_count, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (
                grouping_key, grouping_type, project_code,
                project_name, proposal_id, confidence,
                tier, len(emails)
            ))
            batch_id = cursor.lastrowid

            # Add emails to batch
            for email in emails:
                cursor.execute("""
                    INSERT INTO batch_emails (
                        batch_id, email_id, individual_confidence, match_signals
                    ) VALUES (?, ?, ?, ?)
                """, (
                    batch_id,
                    email['email_id'],
                    confidence,
                    json.dumps(signals)
                ))

            conn.commit()
            return batch_id

    def _log_low_confidence_emails(
        self,
        emails: List[Dict],
        best_guess: Optional[str],
        confidence: float,
        reason: str
    ):
        """Log emails that are too low confidence for suggestions"""
        # Get project name if we have a guess
        project_name = None
        if best_guess:
            project = self._get_proposal_by_code(best_guess)
            if project:
                project_name = project['project_name']

        with self.get_connection() as conn:
            cursor = conn.cursor()
            for email in emails:
                cursor.execute("""
                    INSERT OR IGNORE INTO low_confidence_log (
                        email_id, best_guess_project, best_guess_name,
                        confidence, reason
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    email['email_id'],
                    best_guess,
                    project_name,
                    confidence,
                    reason
                ))
            conn.commit()

    def _auto_approve_batch(self, batch_id: int):
        """Auto-approve a high-confidence batch and apply links"""
        batch = self.execute_query("""
            SELECT * FROM suggestion_batches WHERE batch_id = ?
        """, [batch_id])

        if not batch:
            return

        batch = dict(batch[0])
        proposal_id = batch['proposal_id']

        if not proposal_id:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get emails in batch
            emails = self.execute_query("""
                SELECT email_id FROM batch_emails WHERE batch_id = ?
            """, [batch_id])

            # Create links
            for email in emails:
                cursor.execute("""
                    INSERT OR IGNORE INTO email_proposal_links (
                        email_id, proposal_id, confidence_score,
                        match_method, created_at
                    ) VALUES (?, ?, ?, 'auto_batch', datetime('now'))
                """, (
                    email['email_id'],
                    proposal_id,
                    batch['confidence_score']
                ))

            # Update batch status
            cursor.execute("""
                UPDATE suggestion_batches
                SET status = 'approved',
                    reviewed_by = 'auto_approve',
                    reviewed_at = datetime('now')
                WHERE batch_id = ?
            """, [batch_id])

            # Update batch_emails status
            cursor.execute("""
                UPDATE batch_emails
                SET status = 'approved'
                WHERE batch_id = ?
            """, [batch_id])

            conn.commit()

            logger.info(
                f"Auto-approved batch {batch_id}: {len(emails)} emails "
                f"linked to {batch['suggested_project_code']}"
            )

    # =========================================================================
    # BATCH REVIEW METHODS
    # =========================================================================

    def get_pending_batches(self, tier: str = None) -> List[Dict]:
        """Get pending batches for review"""
        query = """
            SELECT
                b.*,
                GROUP_CONCAT(be.email_id) as email_ids
            FROM suggestion_batches b
            LEFT JOIN batch_emails be ON b.batch_id = be.batch_id
            WHERE b.status = 'pending'
        """
        params = []

        if tier:
            query += " AND b.confidence_tier = ?"
            params.append(tier)

        query += " GROUP BY b.batch_id ORDER BY b.confidence_score DESC"

        results = self.execute_query(query, params)
        return [dict(r) for r in results]

    def approve_batch(self, batch_id: int, reviewed_by: str = 'user') -> Dict:
        """Approve a batch and create email-proposal links"""
        batch = self.execute_query("""
            SELECT * FROM suggestion_batches WHERE batch_id = ?
        """, [batch_id])

        if not batch:
            return {'success': False, 'error': 'Batch not found'}

        batch = dict(batch[0])
        proposal_id = batch['proposal_id']

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get emails
            emails = self.execute_query("""
                SELECT email_id FROM batch_emails WHERE batch_id = ?
            """, [batch_id])

            links_created = 0
            for email in emails:
                cursor.execute("""
                    INSERT OR IGNORE INTO email_proposal_links (
                        email_id, proposal_id, confidence_score,
                        match_method, created_at
                    ) VALUES (?, ?, ?, 'batch_approved', datetime('now'))
                """, (email['email_id'], proposal_id, batch['confidence_score']))
                links_created += cursor.rowcount

            # Update batch
            cursor.execute("""
                UPDATE suggestion_batches
                SET status = 'approved',
                    reviewed_by = ?,
                    reviewed_at = datetime('now')
                WHERE batch_id = ?
            """, (reviewed_by, batch_id))

            cursor.execute("""
                UPDATE batch_emails SET status = 'approved' WHERE batch_id = ?
            """, [batch_id])

            conn.commit()

        # Learn patterns from approval
        self._learn_from_batch_approval(batch)

        return {
            'success': True,
            'batch_id': batch_id,
            'links_created': links_created
        }

    def reject_batch(
        self,
        batch_id: int,
        reviewed_by: str = 'user',
        reason: str = None
    ) -> Dict:
        """Reject a batch"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE suggestion_batches
                SET status = 'rejected',
                    reviewed_by = ?,
                    reviewed_at = datetime('now'),
                    review_notes = ?
                WHERE batch_id = ?
            """, (reviewed_by, reason, batch_id))

            cursor.execute("""
                UPDATE batch_emails SET status = 'rejected' WHERE batch_id = ?
            """, [batch_id])

            conn.commit()

        return {'success': True, 'batch_id': batch_id}

    def _learn_from_batch_approval(self, batch: Dict):
        """Learn patterns from an approved batch"""
        grouping_key = batch.get('grouping_key', '')
        project_code = batch['suggested_project_code']
        proposal_id = batch['proposal_id']
        project_name = batch['suggested_project_name']

        if not grouping_key.startswith('sender:'):
            return

        sender = grouping_key.replace('sender:', '')
        domain = self._extract_domain(sender)

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Boost or create sender pattern
            cursor.execute("""
                INSERT INTO email_learned_patterns (
                    pattern_type, pattern_key, pattern_key_normalized,
                    target_type, target_id, target_code, target_name,
                    confidence, times_correct, notes
                ) VALUES (
                    'sender_to_proposal', ?, ?, 'proposal', ?, ?, ?, 0.85, 1,
                    'Learned from batch approval'
                )
                ON CONFLICT(pattern_type, pattern_key_normalized, target_type, target_id)
                DO UPDATE SET
                    confidence = MIN(confidence + 0.05, 0.98),
                    times_correct = times_correct + 1,
                    last_used_at = datetime('now')
            """, (sender, sender.lower(), proposal_id, project_code, project_name))

            # Create domain pattern if corporate domain
            if domain and domain not in INTERNAL_DOMAINS:
                generic_domains = {'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com'}
                if domain not in generic_domains:
                    cursor.execute("""
                        INSERT INTO email_learned_patterns (
                            pattern_type, pattern_key, pattern_key_normalized,
                            target_type, target_id, target_code, target_name,
                            confidence, times_correct, notes
                        ) VALUES (
                            'domain_to_proposal', ?, ?, 'proposal', ?, ?, ?, 0.70, 1,
                            'Learned from batch approval'
                        )
                        ON CONFLICT(pattern_type, pattern_key_normalized, target_type, target_id)
                        DO UPDATE SET
                            confidence = MIN(confidence + 0.03, 0.90),
                            times_correct = times_correct + 1,
                            last_used_at = datetime('now')
                    """, (domain, domain.lower(), proposal_id, project_code, project_name))

            conn.commit()

    def get_batch_stats(self) -> Dict[str, Any]:
        """Get statistics about batch suggestions"""
        stats = {}

        # Batch counts by status
        status_counts = self.execute_query("""
            SELECT status, COUNT(*) as count, SUM(email_count) as emails
            FROM suggestion_batches
            GROUP BY status
        """, [])
        stats['by_status'] = {r['status']: {'batches': r['count'], 'emails': r['emails']}
                             for r in status_counts}

        # Tier distribution
        tier_counts = self.execute_query("""
            SELECT confidence_tier, COUNT(*) as count
            FROM suggestion_batches
            WHERE status = 'pending'
            GROUP BY confidence_tier
        """, [])
        stats['pending_by_tier'] = {r['confidence_tier']: r['count'] for r in tier_counts}

        # Low confidence log
        low_conf = self.execute_query("""
            SELECT COUNT(*) as total, SUM(reviewed) as reviewed
            FROM low_confidence_log
        """, [])
        if low_conf:
            stats['low_confidence'] = {
                'total': low_conf[0]['total'],
                'reviewed': low_conf[0]['reviewed'] or 0
            }

        return stats


def get_batch_service(db_path: str = None) -> BatchSuggestionService:
    """Get batch suggestion service instance"""
    return BatchSuggestionService(db_path)
