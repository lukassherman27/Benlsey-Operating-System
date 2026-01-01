"""
Email Category Service

Handles email categorization with:
- Rule-based auto-categorization
- Uncategorized email tracking
- AI-suggested categories
- Learning from user feedback
"""

import re
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from .base_service import BaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailCategoryService(BaseService):
    """Service for email categorization operations"""

    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all email categories with stats"""
        sql = """
            SELECT
                ec.category_id,
                ec.name,
                ec.description,
                ec.is_system,
                ec.parent_category_id,
                ec.display_order,
                ec.color,
                ec.icon,
                ec.created_at,
                ec.created_by,
                parent.name as parent_name,
                (SELECT COUNT(*) FROM email_category_rules WHERE category_id = ec.category_id AND is_active = 1) as rule_count,
                (SELECT COALESCE(SUM(hit_count), 0) FROM email_category_rules WHERE category_id = ec.category_id) as total_hits
            FROM email_categories ec
            LEFT JOIN email_categories parent ON ec.parent_category_id = parent.category_id
            ORDER BY ec.display_order, ec.name
        """
        return self.execute_query(sql)

    def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Get a single category by ID"""
        sql = """
            SELECT * FROM email_categories WHERE category_id = ?
        """
        return self.execute_query(sql, (category_id,), fetch_one=True)

    def get_category_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a single category by name"""
        sql = """
            SELECT * FROM email_categories WHERE name = ?
        """
        return self.execute_query(sql, (name,), fetch_one=True)

    def create_category(
        self,
        name: str,
        description: Optional[str] = None,
        parent_category_id: Optional[int] = None,
        created_by: str = 'user'
    ) -> Dict[str, Any]:
        """
        Create a new email category

        Args:
            name: Category name (unique)
            description: Human-readable description
            parent_category_id: Parent category for hierarchy
            created_by: 'user', 'ai_suggested', 'system'

        Returns:
            Created category dict
        """
        sql = """
            INSERT INTO email_categories (name, description, parent_category_id, created_by)
            VALUES (?, ?, ?, ?)
        """
        self.execute_update(sql, (name, description, parent_category_id, created_by))

        return self.get_category_by_name(name)

    def categorize_email(self, email_id: int) -> Dict[str, Any]:
        """
        Attempt to categorize an email using rules

        Applies rules in priority order. If no rules match, adds to uncategorized bucket.

        Args:
            email_id: Email ID to categorize

        Returns:
            Dict with category_id, category_name, confidence, matched_rule_id (or uncategorized info)
        """
        # Get email data
        email_sql = """
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.body_full,
                e.recipient_emails
            FROM emails e
            WHERE e.email_id = ?
        """
        email = self.execute_query(email_sql, (email_id,), fetch_one=True)

        if not email:
            return {"error": f"Email {email_id} not found"}

        # Get active rules ordered by priority
        rules_sql = """
            SELECT
                r.rule_id,
                r.category_id,
                r.rule_type,
                r.pattern,
                r.is_regex,
                r.confidence,
                r.priority,
                c.name as category_name
            FROM email_category_rules r
            JOIN email_categories c ON r.category_id = c.category_id
            WHERE r.is_active = 1
            ORDER BY r.priority DESC, r.confidence DESC
        """
        rules = self.execute_query(rules_sql)

        # Try each rule
        for rule in rules:
            matched = self._check_rule_match(email, rule)
            if matched:
                # Update rule hit count
                self._update_rule_hit(rule['rule_id'])

                # Update email_content category
                self._update_email_category(email_id, rule['category_name'])

                return {
                    "email_id": email_id,
                    "categorized": True,
                    "category_id": rule['category_id'],
                    "category_name": rule['category_name'],
                    "confidence": rule['confidence'],
                    "matched_rule_id": rule['rule_id'],
                    "rule_type": rule['rule_type']
                }

        # No rules matched - add to uncategorized
        return self._add_to_uncategorized(email_id)

    def _check_rule_match(self, email: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """Check if an email matches a rule"""
        pattern = rule['pattern']
        is_regex = rule['is_regex']
        rule_type = rule['rule_type']

        # Get the field to check
        field_value = None
        if rule_type == 'sender_email':
            field_value = email.get('sender_email', '')
        elif rule_type == 'sender_domain':
            sender = email.get('sender_email', '')
            field_value = '@' + sender.split('@')[-1] if '@' in sender else ''
        elif rule_type == 'subject_pattern':
            field_value = email.get('subject', '')
        elif rule_type == 'body_pattern':
            field_value = email.get('body_full', '')
        elif rule_type == 'recipient_pattern':
            field_value = email.get('recipient_emails', '')

        if not field_value:
            return False

        # Check match
        try:
            if is_regex:
                return bool(re.search(pattern, field_value, re.IGNORECASE))
            else:
                # LIKE-style match for exact patterns
                return pattern.lower() in field_value.lower()
        except re.error:
            logger.warning(f"Invalid regex pattern in rule {rule['rule_id']}: {pattern}")
            return False

    def _update_rule_hit(self, rule_id: int):
        """Update rule hit count and last hit timestamp"""
        sql = """
            UPDATE email_category_rules
            SET hit_count = hit_count + 1, last_hit_at = ?
            WHERE rule_id = ?
        """
        self.execute_update(sql, (datetime.now().isoformat(), rule_id))

    def _update_email_category(self, email_id: int, category_name: str):
        """Update email_content category for an email"""
        # Check if email_content row exists
        check_sql = "SELECT content_id FROM email_content WHERE email_id = ?"
        existing = self.execute_query(check_sql, (email_id,), fetch_one=True)

        if existing:
            update_sql = "UPDATE email_content SET category = ? WHERE email_id = ?"
            self.execute_update(update_sql, (category_name, email_id))
        else:
            insert_sql = """
                INSERT INTO email_content (email_id, category, importance_score)
                VALUES (?, ?, 0.5)
            """
            self.execute_update(insert_sql, (email_id, category_name))

    def _add_to_uncategorized(self, email_id: int) -> Dict[str, Any]:
        """Add email to uncategorized bucket"""
        # Check if already in uncategorized
        check_sql = "SELECT id FROM uncategorized_emails WHERE email_id = ?"
        existing = self.execute_query(check_sql, (email_id,), fetch_one=True)

        if existing:
            return {
                "email_id": email_id,
                "categorized": False,
                "uncategorized_id": existing['id'],
                "message": "Already in uncategorized bucket"
            }

        # Add to uncategorized
        insert_sql = """
            INSERT INTO uncategorized_emails (email_id)
            VALUES (?)
        """
        self.execute_update(insert_sql, (email_id,))

        return {
            "email_id": email_id,
            "categorized": False,
            "message": "Added to uncategorized bucket for review"
        }

    def suggest_category(self, email_id: int) -> Dict[str, Any]:
        """
        AI-suggest a category for an uncategorized email

        This method analyzes email content and suggests a category.
        The suggestion is stored for human review.

        Args:
            email_id: Email ID to suggest category for

        Returns:
            Dict with suggested category and reasoning
        """
        # Get email data
        email_sql = """
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.body_full,
                e.snippet,
                ec.clean_body
            FROM emails e
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE e.email_id = ?
        """
        email = self.execute_query(email_sql, (email_id,), fetch_one=True)

        if not email:
            return {"error": f"Email {email_id} not found"}

        # Simple heuristic-based suggestion (can be enhanced with AI later)
        suggested = self._heuristic_suggest(email)

        # Update uncategorized_emails with suggestion
        if suggested['category_id']:
            update_sql = """
                UPDATE uncategorized_emails
                SET suggested_category_id = ?,
                    suggested_category_reason = ?,
                    confidence_score = ?
                WHERE email_id = ?
            """
            self.execute_update(update_sql, (
                suggested['category_id'],
                suggested['reason'],
                suggested['confidence'],
                email_id
            ))

        return {
            "email_id": email_id,
            "suggested_category_id": suggested['category_id'],
            "suggested_category_name": suggested['category_name'],
            "confidence": suggested['confidence'],
            "reason": suggested['reason']
        }

    def _heuristic_suggest(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simple heuristic-based category suggestion

        This can be enhanced with OpenAI API calls later.
        """
        subject = (email.get('subject') or '').lower()
        sender = (email.get('sender_email') or '').lower()
        body = (email.get('body_full') or email.get('clean_body') or email.get('snippet') or '').lower()

        # Check for various signals
        categories_confidence = []

        # Internal
        if 'bensley' in sender:
            categories_confidence.append(('internal_scheduling', 0.6, 'Sender is from Bensley'))

        # Financial signals
        if any(word in subject or word in body for word in ['invoice', 'payment', 'fee', 'billing', 'quote']):
            categories_confidence.append(('project_financial', 0.8, 'Contains financial keywords'))

        # Contract signals
        if any(word in subject or word in body for word in ['contract', 'agreement', 'proposal', 'terms']):
            categories_confidence.append(('project_contracts', 0.8, 'Contains contract keywords'))

        # Design signals
        if any(word in subject or word in body for word in ['design', 'concept', 'schematic', 'drawing', 'render']):
            categories_confidence.append(('project_design', 0.7, 'Contains design keywords'))

        # Meeting signals
        if any(word in subject or word in body for word in ['meeting', 'calendar', 'invite', 'zoom', 'teams']):
            categories_confidence.append(('internal_scheduling', 0.75, 'Contains meeting keywords'))

        # Automated signals
        if any(word in sender for word in ['noreply', 'no-reply', 'notifications', 'system']):
            categories_confidence.append(('automated_notification', 0.9, 'Sender appears automated'))

        if not categories_confidence:
            return {
                "category_id": None,
                "category_name": None,
                "confidence": 0,
                "reason": "No clear signals found"
            }

        # Get highest confidence suggestion
        best = max(categories_confidence, key=lambda x: x[1])
        category = self.get_category_by_name(best[0])

        return {
            "category_id": category['category_id'] if category else None,
            "category_name": best[0],
            "confidence": best[1],
            "reason": best[2]
        }

    def add_rule(
        self,
        category_id: int,
        rule_type: str,
        pattern: str,
        is_regex: bool = False,
        confidence: float = 0.8,
        priority: int = 50,
        learned_from: str = 'manual'
    ) -> Dict[str, Any]:
        """
        Add a new categorization rule

        Args:
            category_id: Category to assign when rule matches
            rule_type: One of 'sender_domain', 'sender_email', 'subject_pattern', 'body_pattern', 'recipient_pattern'
            pattern: Pattern to match (regex or substring)
            is_regex: True if pattern is a regex
            confidence: Confidence score (0-1)
            priority: Rule priority (higher = checked first)
            learned_from: 'manual', 'ai_analysis', 'user_feedback'

        Returns:
            Created rule dict
        """
        valid_types = ['sender_domain', 'sender_email', 'subject_pattern', 'body_pattern', 'recipient_pattern']
        if rule_type not in valid_types:
            raise ValueError(f"Invalid rule_type: {rule_type}. Must be one of {valid_types}")

        # Validate regex if applicable
        if is_regex:
            try:
                re.compile(pattern)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}")

        sql = """
            INSERT INTO email_category_rules
            (category_id, rule_type, pattern, is_regex, confidence, priority, learned_from)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.execute_update(sql, (category_id, rule_type, pattern, int(is_regex), confidence, priority, learned_from))

        # Get the created rule
        get_sql = """
            SELECT * FROM email_category_rules
            WHERE category_id = ? AND rule_type = ? AND pattern = ?
            ORDER BY rule_id DESC LIMIT 1
        """
        return self.execute_query(get_sql, (category_id, rule_type, pattern), fetch_one=True)

    def get_uncategorized(self, limit: int = 50, include_suggested: bool = True) -> List[Dict[str, Any]]:
        """
        Get uncategorized emails for review

        Args:
            limit: Max number to return
            include_suggested: Include emails with AI suggestions

        Returns:
            List of uncategorized emails with metadata
        """
        sql = """
            SELECT
                ue.id,
                ue.email_id,
                ue.suggested_category_id,
                ue.suggested_category_reason,
                ue.confidence_score,
                ue.created_at,
                e.subject,
                e.sender_email,
                e.date,
                e.snippet,
                ec.name as suggested_category_name
            FROM uncategorized_emails ue
            JOIN emails e ON ue.email_id = e.email_id
            LEFT JOIN email_categories ec ON ue.suggested_category_id = ec.category_id
            WHERE ue.reviewed = 0
        """

        if not include_suggested:
            sql += " AND ue.suggested_category_id IS NULL"

        sql += " ORDER BY ue.created_at DESC LIMIT ?"

        return self.execute_query(sql, (limit,))

    def approve_category_suggestion(
        self,
        email_id: int,
        category_id: int,
        create_rule: bool = False,
        rule_type: Optional[str] = None,
        rule_pattern: Optional[str] = None,
        reviewed_by: str = 'user'
    ) -> Dict[str, Any]:
        """
        Approve a category for an uncategorized email

        Removes from uncategorized bucket, updates email_content,
        and optionally creates a new rule for future categorization.

        Args:
            email_id: Email ID
            category_id: Approved category ID
            create_rule: If True, create a rule from this decision
            rule_type: Type of rule to create
            rule_pattern: Pattern for the rule
            reviewed_by: Who reviewed this

        Returns:
            Result dict
        """
        # Get category info
        category = self.get_category_by_id(category_id)
        if not category:
            return {"error": f"Category {category_id} not found"}

        # Update uncategorized_emails as reviewed
        update_sql = """
            UPDATE uncategorized_emails
            SET reviewed = 1,
                reviewed_by = ?,
                reviewed_at = ?,
                final_category_id = ?
            WHERE email_id = ?
        """
        self.execute_update(update_sql, (reviewed_by, datetime.now().isoformat(), category_id, email_id))

        # Update email_content with the category
        self._update_email_category(email_id, category['name'])

        # Record in history
        history_sql = """
            INSERT INTO email_category_history
            (email_id, new_category_id, changed_by, change_reason)
            VALUES (?, ?, ?, ?)
        """
        self.execute_update(history_sql, (email_id, category_id, 'user', 'Manual categorization from uncategorized bucket'))

        # Optionally create a rule
        rule_created = None
        if create_rule and rule_type and rule_pattern:
            try:
                rule_created = self.add_rule(
                    category_id=category_id,
                    rule_type=rule_type,
                    pattern=rule_pattern,
                    learned_from='user_feedback'
                )
            except ValueError as e:
                logger.warning(f"Failed to create rule: {e}")

        return {
            "email_id": email_id,
            "category_id": category_id,
            "category_name": category['name'],
            "reviewed": True,
            "rule_created": rule_created
        }

    def get_rules_for_category(self, category_id: int) -> List[Dict[str, Any]]:
        """Get all rules for a category"""
        sql = """
            SELECT * FROM email_category_rules
            WHERE category_id = ?
            ORDER BY priority DESC, confidence DESC
        """
        return self.execute_query(sql, (category_id,))

    def disable_rule(self, rule_id: int) -> bool:
        """Disable a categorization rule"""
        sql = "UPDATE email_category_rules SET is_active = 0 WHERE rule_id = ?"
        rows = self.execute_update(sql, (rule_id,))
        return rows > 0

    def enable_rule(self, rule_id: int) -> bool:
        """Enable a categorization rule"""
        sql = "UPDATE email_category_rules SET is_active = 1 WHERE rule_id = ?"
        rows = self.execute_update(sql, (rule_id,))
        return rows > 0

    def get_category_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all categories"""
        sql = """
            SELECT * FROM v_email_category_stats
            ORDER BY email_count DESC
        """
        return self.execute_query(sql)

    def batch_categorize(self, email_ids: Optional[List[int]] = None, limit: int = 100) -> Dict[str, Any]:
        """
        Categorize multiple emails at once

        Args:
            email_ids: Specific email IDs to categorize (or None for uncategorized)
            limit: Max emails to process

        Returns:
            Summary of categorization results
        """
        if email_ids is None:
            # Get emails that haven't been categorized yet
            # Also exclude emails already in uncategorized bucket
            sql = """
                SELECT e.email_id
                FROM emails e
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
                WHERE (ec.category IS NULL OR ec.category = '')
                AND e.email_id NOT IN (SELECT email_id FROM uncategorized_emails)
                LIMIT ?
            """
            rows = self.execute_query(sql, (limit,))
            email_ids = [row['email_id'] for row in rows]

        results = {
            "processed": 0,
            "categorized": 0,
            "uncategorized": 0,
            "errors": 0,
            "categories": {}
        }

        for email_id in email_ids:
            try:
                result = self.categorize_email(email_id)
                results["processed"] += 1

                if result.get("categorized"):
                    results["categorized"] += 1
                    cat_name = result.get("category_name", "unknown")
                    results["categories"][cat_name] = results["categories"].get(cat_name, 0) + 1
                else:
                    results["uncategorized"] += 1
            except Exception as e:
                logger.error(f"Error categorizing email {email_id}: {e}")
                results["errors"] += 1

        return results
