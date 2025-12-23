"""
Email Tagger Service

Comprehensive email tagging with iterative learning for Bill's complete universe.
Tags emails with multiple dimensions: category, subcategory, project, action type.

Part of Phase 2.0: Multi-Tag Categorization System
"""

import os
import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .base_service import BaseService
from .gpt_suggestion_analyzer import GPTSuggestionAnalyzer
from .context_bundler import get_context_bundler

logger = logging.getLogger(__name__)


class EmailTaggerService(BaseService):
    """
    Comprehensive email tagging with iterative learning.

    Workflow:
    1. Check patterns first (fast, no API cost)
    2. Call GPT for unknowns (with full category context)
    3. User reviews suggestions
    4. Learn from approvals/corrections
    5. Patterns grow over time, reducing AI needs
    """

    # Bill's Universe Categories
    CATEGORIES = {
        # Top-level categories
        'BDS': {'name': 'Design Business', 'type': 'design'},
        'INT': {'name': 'Internal Operations', 'type': 'internal'},
        'SM': {'name': 'Shinta Mani Hotels', 'type': 'shinta_mani'},
        'PERS': {'name': 'Personal', 'type': 'personal'},
        'MKT': {'name': 'Marketing/Brand', 'type': 'marketing'},
        'SKIP': {'name': 'Skip/Ignore', 'type': 'skip'},

        # Subcategories - Internal
        'INT-FIN': {'name': 'Finance', 'parent': 'INT'},
        'INT-OPS': {'name': 'IT/Systems', 'parent': 'INT'},
        'INT-HR': {'name': 'Human Resources', 'parent': 'INT'},
        'INT-LEGAL': {'name': 'Legal', 'parent': 'INT'},
        'INT-SCHED': {'name': 'Scheduling', 'parent': 'INT'},
        'INT-DAILY': {'name': 'Daily Work', 'parent': 'INT'},

        # Subcategories - Shinta Mani
        'SM-WILD': {'name': 'Shinta Mani Wild', 'parent': 'SM'},
        'SM-MUSTANG': {'name': 'Shinta Mani Mustang', 'parent': 'SM'},
        'SM-ANGKOR': {'name': 'Shinta Mani Angkor', 'parent': 'SM'},
        'SM-FOUNDATION': {'name': 'Shinta Mani Foundation', 'parent': 'SM'},

        # Subcategories - Personal
        'PERS-ART': {'name': 'Gallery/Art', 'parent': 'PERS'},
        'PERS-INVEST': {'name': 'Investments', 'parent': 'PERS'},
        'PERS-FAMILY': {'name': 'Family', 'parent': 'PERS'},
        'PERS-PRESS': {'name': 'Press/Speaking', 'parent': 'PERS'},

        # Subcategories - Marketing
        'MKT-SOCIAL': {'name': 'Social Media', 'parent': 'MKT'},
        'MKT-PRESS': {'name': 'Press Coverage', 'parent': 'MKT'},
        'MKT-WEB': {'name': 'Website', 'parent': 'MKT'},

        # Subcategories - Skip
        'SKIP-SPAM': {'name': 'Spam', 'parent': 'SKIP'},
        'SKIP-AUTO': {'name': 'Automated', 'parent': 'SKIP'},
        'SKIP-DUP': {'name': 'Duplicate', 'parent': 'SKIP'},
    }

    def __init__(self, db_path: str = None):
        super().__init__(db_path)
        self.bundler = get_context_bundler(db_path)
        self._gpt_analyzer = None

    @property
    def gpt_analyzer(self) -> GPTSuggestionAnalyzer:
        """Lazy-load GPT analyzer"""
        if self._gpt_analyzer is None:
            self._gpt_analyzer = GPTSuggestionAnalyzer()
        return self._gpt_analyzer

    def tag_batch(
        self,
        email_ids: List[int] = None,
        batch_size: int = 20,
        use_ai: bool = True,
        uncategorized_only: bool = True
    ) -> Dict[str, Any]:
        """
        Tag a batch of emails, using patterns first, then AI.

        Args:
            email_ids: Specific email IDs to process (optional)
            batch_size: Number of emails to process if no IDs given
            use_ai: Whether to call GPT for unknowns
            uncategorized_only: Only process emails without primary_category

        Returns:
            Dict with results breakdown
        """
        # Get emails to process
        if email_ids:
            emails = self._get_emails_by_ids(email_ids)
        else:
            emails = self._get_uncategorized_emails(batch_size) if uncategorized_only else self._get_recent_emails(batch_size)

        if not emails:
            return {
                'total': 0,
                'pattern_matched': [],
                'ai_analyzed': [],
                'needs_review': [],
                'message': 'No emails to process'
            }

        results = {
            'total': len(emails),
            'pattern_matched': [],
            'ai_analyzed': [],
            'needs_review': [],
            'errors': []
        }

        # Load patterns once for the batch
        category_patterns = self._load_category_patterns()

        for email in emails:
            try:
                # Step 1: Try pattern matching first
                pattern_result = self._match_patterns(email, category_patterns)

                if pattern_result and pattern_result.get('confidence', 0) >= 0.75:
                    results['pattern_matched'].append({
                        'email_id': email['email_id'],
                        'subject': email.get('subject', ''),
                        'sender': email.get('sender_email', ''),
                        'tags': pattern_result,
                        'source': 'pattern'
                    })
                elif use_ai:
                    # Step 2: Call GPT for analysis
                    ai_result = self._analyze_with_gpt(email)
                    if ai_result.get('success'):
                        results['ai_analyzed'].append({
                            'email_id': email['email_id'],
                            'subject': email.get('subject', ''),
                            'sender': email.get('sender_email', ''),
                            'tags': ai_result.get('analysis', {}),
                            'source': 'ai'
                        })
                    else:
                        results['needs_review'].append({
                            'email_id': email['email_id'],
                            'subject': email.get('subject', ''),
                            'error': ai_result.get('error', 'Unknown error')
                        })
                else:
                    results['needs_review'].append({
                        'email_id': email['email_id'],
                        'subject': email.get('subject', ''),
                        'reason': 'No pattern match, AI disabled'
                    })

            except Exception as e:
                logger.error(f"Error processing email {email.get('email_id')}: {e}")
                results['errors'].append({
                    'email_id': email.get('email_id'),
                    'error': str(e)
                })

        return results

    def get_review_batch(self, batch_size: int = 20) -> List[Dict[str, Any]]:
        """
        Get a batch of emails ready for review.
        Returns full context for Claude-in-the-loop review.
        """
        emails = self._get_uncategorized_emails(batch_size)
        category_patterns = self._load_category_patterns()

        review_items = []

        for email in emails:
            # Try pattern match first
            pattern_result = self._match_patterns(email, category_patterns)

            # Get thread context
            thread_context = self._get_thread_context(email)

            # Get existing project links
            project_links = self._get_existing_links(email['email_id'])

            item = {
                'email_id': email['email_id'],
                'date': email.get('date', ''),
                'sender': email.get('sender_email', ''),
                'sender_name': email.get('sender_name', ''),
                'recipients': email.get('recipient_emails', ''),
                'subject': email.get('subject', ''),
                'body_preview': (email.get('body_full') or email.get('body_preview') or '')[:500],
                'folder': email.get('folder', 'INBOX'),

                # Pattern match result (if any)
                'pattern_match': pattern_result,

                # Thread context
                'thread_email_count': thread_context.get('email_count', 1),
                'thread_has_project_link': bool(thread_context.get('existing_project_links')),
                'thread_project': thread_context.get('existing_project_links', []),

                # Existing links
                'existing_project_links': project_links,

                # Current classification (if any)
                'current_category': email.get('primary_category'),
                'current_type': email.get('email_type'),
            }

            review_items.append(item)

        return review_items

    def apply_tags(
        self,
        email_id: int,
        primary_category: str,
        subcategory: str = None,
        project_code: str = None,
        action_type: str = None,
        source: str = 'user'
    ) -> Dict[str, Any]:
        """
        Apply tags to an email and learn from it.

        Args:
            email_id: Email to tag
            primary_category: Main category (BDS, INT, SM, PERS, MKT, SKIP)
            subcategory: Subcategory (INT-FIN, SM-WILD, etc.)
            project_code: Project/proposal code (for BDS emails)
            action_type: Action type (invoice, scheduling, etc.)
            source: Who applied tags (user, ai, pattern)

        Returns:
            Dict with success status and created tags
        """
        try:
            now = datetime.now().isoformat()
            tags_created = []

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Clear existing category tags for this email (keep other tag types)
                cursor.execute("""
                    DELETE FROM email_tags
                    WHERE email_id = ?
                    AND tag_type IN ('category', 'primary', 'secondary', 'project', 'action')
                """, (email_id,))

                # Add primary category tag (using existing schema: tag, tag_type, confidence, created_by)
                cursor.execute("""
                    INSERT OR REPLACE INTO email_tags (email_id, tag, tag_type, confidence, created_by)
                    VALUES (?, ?, 'category', ?, ?)
                """, (email_id, primary_category, 0.9 if source == 'user' else 0.7, source))
                tags_created.append({'type': 'category', 'tag': primary_category})

                # Add subcategory tag if provided
                if subcategory:
                    cursor.execute("""
                        INSERT OR REPLACE INTO email_tags (email_id, tag, tag_type, confidence, created_by)
                        VALUES (?, ?, 'category', ?, ?)
                    """, (email_id, subcategory, 0.9 if source == 'user' else 0.7, source))
                    tags_created.append({'type': 'category', 'tag': subcategory})

                # Add project link tag if provided
                if project_code:
                    cursor.execute("""
                        INSERT OR REPLACE INTO email_tags (email_id, tag, tag_type, confidence, created_by)
                        VALUES (?, ?, 'project_mention', ?, ?)
                    """, (email_id, project_code, 0.9 if source == 'user' else 0.7, source))
                    tags_created.append({'type': 'project_mention', 'tag': project_code})

                # Add action type tag if provided
                if action_type:
                    cursor.execute("""
                        INSERT OR REPLACE INTO email_tags (email_id, tag, tag_type, confidence, created_by)
                        VALUES (?, ?, 'topic', ?, ?)
                    """, (email_id, action_type, 0.9 if source == 'user' else 0.7, source))
                    tags_created.append({'type': 'topic', 'tag': action_type})

                # Update emails table with primary category
                cursor.execute("""
                    UPDATE emails
                    SET primary_category = ?,
                        is_categorized = 1,
                        categorized_at = ?,
                        categorized_by = ?
                    WHERE email_id = ?
                """, (primary_category, now, source, email_id))

                conn.commit()

            # Learn from user tags
            if source == 'user':
                self._learn_from_tags(email_id, primary_category, subcategory, project_code)

            return {
                'success': True,
                'email_id': email_id,
                'tags_created': tags_created,
                'source': source
            }

        except Exception as e:
            logger.error(f"Error applying tags to email {email_id}: {e}")
            return {
                'success': False,
                'email_id': email_id,
                'error': str(e)
            }

    def apply_batch_tags(self, tag_decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply tags to multiple emails at once.

        Args:
            tag_decisions: List of dicts with email_id, primary_category, subcategory, etc.

        Returns:
            Summary of results
        """
        results = {
            'total': len(tag_decisions),
            'success': 0,
            'failed': 0,
            'errors': []
        }

        for decision in tag_decisions:
            result = self.apply_tags(
                email_id=decision['email_id'],
                primary_category=decision['primary_category'],
                subcategory=decision.get('subcategory'),
                project_code=decision.get('project_code'),
                action_type=decision.get('action_type'),
                source=decision.get('source', 'user')
            )

            if result.get('success'):
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(result)

        return results

    def _get_emails_by_ids(self, email_ids: List[int]) -> List[Dict[str, Any]]:
        """Get emails by specific IDs"""
        placeholders = ','.join('?' * len(email_ids))
        return self.execute_query(f"""
            SELECT email_id, message_id, thread_id, date, sender_email, sender_name,
                   recipient_emails, subject, body_preview, body_full, folder,
                   primary_category, email_type, is_project_related
            FROM emails
            WHERE email_id IN ({placeholders})
            ORDER BY date DESC
        """, tuple(email_ids))

    def _get_uncategorized_emails(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get emails without primary_category"""
        return self.execute_query("""
            SELECT email_id, message_id, thread_id, date, sender_email, sender_name,
                   recipient_emails, subject, body_preview, body_full, folder,
                   primary_category, email_type, is_project_related
            FROM emails
            WHERE (primary_category IS NULL OR is_categorized = 0)
            ORDER BY date DESC
            LIMIT ?
        """, (limit,))

    def _get_recent_emails(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent emails"""
        return self.execute_query("""
            SELECT email_id, message_id, thread_id, date, sender_email, sender_name,
                   recipient_emails, subject, body_preview, body_full, folder,
                   primary_category, email_type, is_project_related
            FROM emails
            ORDER BY date DESC
            LIMIT ?
        """, (limit,))

    def _load_category_patterns(self) -> List[Dict[str, Any]]:
        """Load active category patterns"""
        return self.execute_query("""
            SELECT pattern_id, pattern_type, pattern_key, pattern_key_normalized,
                   category_code, confidence
            FROM category_patterns
            WHERE is_active = 1
            ORDER BY confidence DESC
        """)

    def _match_patterns(
        self,
        email: Dict[str, Any],
        patterns: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Match email against category patterns.

        Returns highest-confidence match or None.
        """
        sender = (email.get('sender_email') or '').lower()
        subject = (email.get('subject') or '').lower()
        body = (email.get('body_full') or email.get('body_preview') or '').lower()

        # Extract domain from sender
        domain = ''
        if '@' in sender:
            domain = '@' + sender.split('@')[1]

        best_match = None
        best_confidence = 0

        for pattern in patterns:
            pattern_type = pattern.get('pattern_type', '')
            pattern_key = (pattern.get('pattern_key_normalized') or pattern.get('pattern_key', '')).lower()
            confidence = pattern.get('confidence', 0.5)

            matched = False

            if pattern_type == 'sender' and pattern_key == sender:
                matched = True
            elif pattern_type == 'domain' and pattern_key == domain:
                matched = True
            elif pattern_type == 'keyword':
                if pattern_key in subject or pattern_key in body:
                    matched = True
            elif pattern_type == 'subject' and pattern_key in subject:
                matched = True

            if matched and confidence > best_confidence:
                best_match = {
                    'primary_category': self._get_parent_category(pattern['category_code']),
                    'subcategory': pattern['category_code'],
                    'confidence': confidence,
                    'matched_pattern': pattern_key,
                    'pattern_type': pattern_type,
                    'pattern_id': pattern.get('pattern_id')
                }
                best_confidence = confidence

        # Increment pattern usage counter if we found a match
        if best_match and best_match.get('pattern_id'):
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE category_patterns
                        SET times_matched = times_matched + 1,
                            last_matched_at = datetime('now')
                        WHERE pattern_id = ?
                    """, [best_match['pattern_id']])
                    conn.commit()
            except Exception as e:
                logger.warning(f"Failed to increment pattern counter: {e}")

        return best_match

    def _get_parent_category(self, category_code: str) -> str:
        """Get the parent category for a subcategory"""
        if category_code in self.CATEGORIES:
            cat_info = self.CATEGORIES[category_code]
            if 'parent' in cat_info:
                return cat_info['parent']
        return category_code

    def _analyze_with_gpt(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze email with GPT using full category context"""
        context_prompt = self._build_category_context()
        return self.gpt_analyzer.analyze_email(email, context_prompt)

    def _build_category_context(self) -> str:
        """Build context prompt including all categories"""
        # Start with standard business context
        base_context = self.bundler.format_for_prompt()

        # Add category-specific instructions
        category_context = """

## COMPLETE CATEGORY TAXONOMY

When analyzing, classify into Bill's complete universe:

### Design Business (BDS)
- Link to specific proposal/project codes: 25 BK-033, 24 BK-019, etc.
- These are DESIGN projects Bensley is working on

### Internal Operations (INT-*)
- INT-FIN: Finance (taxes, accounting, invoices, payments)
- INT-OPS: IT/Systems (email setup, software, BOS, NaviWorld)
- INT-HR: Human Resources (hiring, policies)
- INT-LEGAL: Legal (contracts for Bensley itself, IP)
- INT-SCHED: Scheduling (PM scheduling, site visits)
- INT-DAILY: Daily work (team updates, progress)

### Shinta Mani Hotels (SM-*) - Bill OWNS these hotels
- SM-WILD: Shinta Mani Wild operations
- SM-MUSTANG: Shinta Mani Mustang operations
- SM-ANGKOR: Shinta Mani Angkor operations
- SM-FOUNDATION: Shinta Mani Foundation charity

### Personal (PERS-*)
- PERS-ART: Bill's art gallery, paintings, exhibitions
- PERS-INVEST: Land sales, investments, property deals
- PERS-FAMILY: Personal family matters
- PERS-PRESS: Interviews, speaking engagements

### Marketing (MKT-*)
- MKT-SOCIAL: Instagram, content, engagement
- MKT-PRESS: Press coverage, articles, awards
- MKT-WEB: Website analytics, updates

### Skip (SKIP-*)
- SKIP-SPAM: Marketing spam (Unanet, Pipedrive, newsletters)
- SKIP-AUTO: System notifications we don't need
- SKIP-DUP: Already processed

## YOUR TASK

Return multi-tag categorization:
{
  "primary_category": "BDS" | "INT" | "SM" | "PERS" | "MKT" | "SKIP",
  "subcategory": "INT-FIN" | "SM-WILD" | etc. (or null),
  "project_link": "25 BK-033" | null (only for BDS emails),
  "action_type": "invoice" | "contract" | "scheduling" | "status_update" | "report" | null,
  "direction": "internal_to_internal" | "internal_to_external" | "external_to_internal",
  "confidence": 0.0-1.0,
  "reasoning": "Why I categorized this way"
}
"""
        return base_context + category_context

    def _get_thread_context(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """Get thread context for an email"""
        thread_id = email.get('thread_id')
        if not thread_id:
            return {'email_count': 1}

        thread_emails = self.execute_query("""
            SELECT email_id, sender_email, subject, date
            FROM emails
            WHERE thread_id = ?
            ORDER BY date
        """, (thread_id,))

        # Check for existing project links in thread
        project_links = self.execute_query("""
            SELECT DISTINCT p.project_code, p.project_name
            FROM email_proposal_links epl
            JOIN proposals p ON epl.proposal_id = p.proposal_id
            JOIN emails e ON epl.email_id = e.email_id
            WHERE e.thread_id = ?
        """, (thread_id,))

        return {
            'email_count': len(thread_emails),
            'existing_project_links': project_links
        }

    def _get_existing_links(self, email_id: int) -> List[Dict[str, Any]]:
        """Get existing project links for an email"""
        return self.execute_query("""
            SELECT p.project_code, p.project_name, epl.confidence_score
            FROM email_proposal_links epl
            JOIN proposals p ON epl.proposal_id = p.proposal_id
            WHERE epl.email_id = ?
        """, (email_id,))

    def _learn_from_tags(
        self,
        email_id: int,
        primary_category: str,
        subcategory: str = None,
        project_code: str = None
    ):
        """Learn patterns from user-applied tags"""
        email = self._get_emails_by_ids([email_id])
        if not email:
            return

        email = email[0]
        sender = (email.get('sender_email') or '').lower()
        category_to_learn = subcategory or primary_category

        # Skip internal senders for pattern learning
        if '@bensley.com' in sender or '@bensleydesign.com' in sender:
            return

        # Extract domain
        if '@' in sender:
            domain = '@' + sender.split('@')[1]

            # Create domain pattern (if not a generic domain)
            if domain not in ['@gmail.com', '@yahoo.com', '@hotmail.com', '@outlook.com']:
                self._create_category_pattern(
                    pattern_type='domain',
                    pattern_key=domain,
                    category_code=category_to_learn,
                    confidence=0.7,
                    email_id=email_id
                )

        # Create sender pattern (always)
        self._create_category_pattern(
            pattern_type='sender',
            pattern_key=sender,
            category_code=category_to_learn,
            confidence=0.8,
            email_id=email_id
        )

    def _create_category_pattern(
        self,
        pattern_type: str,
        pattern_key: str,
        category_code: str,
        confidence: float,
        email_id: int = None
    ):
        """Create or update a category pattern"""
        try:
            normalized = pattern_key.lower().strip()

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Try to update existing pattern
                cursor.execute("""
                    UPDATE category_patterns
                    SET times_confirmed = times_confirmed + 1,
                        confidence = MIN(confidence + 0.05, 0.95),
                        last_matched_at = datetime('now')
                    WHERE pattern_type = ?
                      AND pattern_key_normalized = ?
                      AND category_code = ?
                """, (pattern_type, normalized, category_code))

                if cursor.rowcount == 0:
                    # Create new pattern
                    cursor.execute("""
                        INSERT OR IGNORE INTO category_patterns
                        (pattern_type, pattern_key, pattern_key_normalized, category_code,
                         confidence, created_from_email_id, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, 'user')
                    """, (pattern_type, pattern_key, normalized, category_code,
                          confidence, email_id))

                conn.commit()

        except Exception as e:
            logger.error(f"Error creating category pattern: {e}")

    def get_category_stats(self) -> Dict[str, Any]:
        """Get statistics about categorization progress"""
        stats = {}

        # Total emails
        result = self.execute_query("SELECT COUNT(*) as count FROM emails")
        stats['total_emails'] = result[0]['count'] if result else 0

        # Categorized emails
        result = self.execute_query(
            "SELECT COUNT(*) as count FROM emails WHERE is_categorized = 1"
        )
        stats['categorized_emails'] = result[0]['count'] if result else 0

        # By category
        result = self.execute_query("""
            SELECT primary_category, COUNT(*) as count
            FROM emails
            WHERE primary_category IS NOT NULL
            GROUP BY primary_category
            ORDER BY count DESC
        """)
        stats['by_category'] = {r['primary_category']: r['count'] for r in result}

        # Pattern count
        result = self.execute_query(
            "SELECT COUNT(*) as count FROM category_patterns WHERE is_active = 1"
        )
        stats['active_patterns'] = result[0]['count'] if result else 0

        return stats
