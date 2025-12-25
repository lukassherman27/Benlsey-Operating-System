#!/usr/bin/env python3
"""
Learning Service - Continuous Learning from User Feedback

Two main functions:
1. General user feedback on AI suggestions (scope, fees, etc.)
2. Pattern learning from approved email->project links

The email link pattern learning loop:
1. User approves "link email from nigel@rosewood.com to BK-070"
2. System stores pattern: sender_to_project nigel@rosewood.com -> BK-070
3. Next email from nigel@rosewood.com auto-suggests BK-070 with higher confidence
4. Pattern confidence increases with each approval
"""

import sqlite3
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import uuid
import re
import logging

import os
DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for pattern learning
PATTERN_CONFIDENCE_BOOST = 0.15
MIN_PATTERN_CONFIDENCE = 0.5
MAX_PATTERN_CONFIDENCE = 0.95


class LearningService:
    """Service for continuous learning from user feedback"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def log_user_feedback(
        self,
        project_code: str,
        question_type: str,
        ai_suggestion: Dict,
        user_correction: Dict,
        context_provided: str = None,
        confidence_before: float = 0.0
    ) -> str:
        """
        Log user feedback for a suggestion

        Args:
            project_code: Project the feedback applies to
            question_type: Type of question (scope, fee_breakdown, timeline, etc.)
            ai_suggestion: What AI suggested (JSON)
            user_correction: What user corrected to (JSON)
            context_provided: User's explanation/reasoning
            confidence_before: AI confidence before correction

        Returns:
            context_id: ID of the logged feedback
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        context_id = str(uuid.uuid4())

        # Calculate new confidence based on whether user agreed
        confidence_after = confidence_before
        agreed = self._did_user_agree(ai_suggestion, user_correction)

        if agreed:
            # User agreed - increase confidence
            confidence_after = min(0.99, confidence_before + 0.05)
        else:
            # User disagreed - decrease confidence
            confidence_after = max(0.50, confidence_before - 0.10)

        cursor.execute("""
            INSERT INTO user_context
            (context_id, project_code, question_type, ai_suggestion, user_correction,
             context_provided, confidence_before, confidence_after, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            context_id,
            project_code,
            question_type,
            json.dumps(ai_suggestion),
            json.dumps(user_correction),
            context_provided,
            confidence_before,
            confidence_after,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        # Try to extract patterns from this feedback
        self.extract_patterns_from_feedback(context_id)

        return context_id

    def _did_user_agree(self, ai_suggestion: Dict, user_correction: Dict) -> bool:
        """Check if user agreed with AI suggestion"""
        # If user correction matches AI suggestion, they agreed
        return json.dumps(ai_suggestion, sort_keys=True) == json.dumps(user_correction, sort_keys=True)

    def extract_patterns_from_feedback(self, context_id: str) -> Optional[str]:
        """
        Extract a reusable pattern from user feedback

        Analyzes the feedback to see if it can be generalized into a rule
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get the feedback
        cursor.execute("""
            SELECT * FROM user_context WHERE context_id = ?
        """, (context_id,))
        feedback = cursor.fetchone()

        if not feedback or not feedback['context_provided']:
            conn.close()
            return None

        context = feedback['context_provided']
        question_type = feedback['question_type']
        user_correction = json.loads(feedback['user_correction'])

        # Try to extract keywords and patterns from user's explanation
        pattern_id = None

        # Example: If user says "All landscape projects should have landscape scope"
        if question_type == 'scope':
            pattern_id = self._extract_scope_pattern(context, user_correction, cursor)

        # Example: If user says "Mobilization is always 20% of total fee"
        elif question_type == 'fee_breakdown':
            pattern_id = self._extract_fee_pattern(context, user_correction, cursor)

        # Mark that we extracted a pattern from this feedback
        if pattern_id:
            cursor.execute("""
                UPDATE user_context
                SET pattern_extracted = 1
                WHERE context_id = ?
            """, (context_id,))
            conn.commit()

        conn.close()
        return pattern_id

    def _extract_scope_pattern(
        self,
        context: str,
        user_correction: Dict,
        cursor
    ) -> Optional[str]:
        """Extract patterns from scope feedback"""
        # Look for keywords in user's explanation
        context_lower = context.lower()

        # Example pattern: "projects with 'villa' in name are landscape + interiors"
        if 'villa' in context_lower and 'landscape' in context_lower and 'interior' in context_lower:
            rule_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO audit_rules
                (rule_id, rule_type, rule_category, rule_label, rule_logic,
                 rule_pattern, confidence_threshold, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule_id,
                'scope_detection',
                'scope',
                'Villa projects include landscape + interiors',
                'Projects with "villa" in name typically include both landscape and interiors disciplines',
                json.dumps({
                    'name_keywords': ['villa', 'residence'],
                    'suggested_disciplines': ['landscape', 'interiors']
                }),
                0.75,
                datetime.now().isoformat()
            ))
            return rule_id

        # Add more pattern extraction logic here
        return None

    def _extract_fee_pattern(
        self,
        context: str,
        user_correction: Dict,
        cursor
    ) -> Optional[str]:
        """Extract patterns from fee breakdown feedback"""
        context_lower = context.lower()

        # Example: User says mobilization is always X%
        mobilization_match = re.search(r'mobilization.*?(\d+)%', context_lower)
        if mobilization_match:
            percentage = int(mobilization_match.group(1))

            rule_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO audit_rules
                (rule_id, rule_type, rule_category, rule_label, rule_logic,
                 rule_pattern, confidence_threshold, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule_id,
                'fee_validation',
                'financial',
                f'Mobilization is typically {percentage}% of total fee',
                f'Standard mobilization fee is {percentage}% of total contract value',
                json.dumps({
                    'phase': 'mobilization',
                    'percentage': percentage
                }),
                0.80,
                datetime.now().isoformat()
            ))
            return rule_id

        return None

    def update_pattern_accuracy(self, pattern_id: str, was_correct: bool):
        """
        Update accuracy statistics for a pattern/rule

        Args:
            pattern_id: The pattern/rule ID
            was_correct: Whether the pattern's suggestion was accepted by user
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get current rule
        cursor.execute("""
            SELECT * FROM audit_rules WHERE rule_id = ?
        """, (pattern_id,))
        rule = cursor.fetchone()

        if not rule:
            # Try suggestion_patterns table (from Phase 1)
            cursor.execute("""
                SELECT * FROM suggestion_patterns WHERE pattern_id = ?
            """, (pattern_id,))
            pattern = cursor.fetchone()

            if pattern:
                # Update suggestion_patterns
                if was_correct:
                    cursor.execute("""
                        UPDATE suggestion_patterns
                        SET approval_count = approval_count + 1
                        WHERE pattern_id = ?
                    """, (pattern_id,))
                else:
                    cursor.execute("""
                        UPDATE suggestion_patterns
                        SET rejection_count = rejection_count + 1
                        WHERE pattern_id = ?
                    """, (pattern_id,))

                # Check if we should enable auto-apply
                cursor.execute("""
                    SELECT approval_count, rejection_count
                    FROM suggestion_patterns
                    WHERE pattern_id = ?
                """, (pattern_id,))
                stats = cursor.fetchone()

                total = stats['approval_count'] + stats['rejection_count']
                accuracy = stats['approval_count'] / total if total > 0 else 0

                if accuracy > 0.90 and total > 20:
                    cursor.execute("""
                        UPDATE suggestion_patterns
                        SET auto_apply_enabled = 1
                        WHERE pattern_id = ?
                    """, (pattern_id,))

            conn.commit()
            conn.close()
            return

        # Update audit_rules
        field = 'times_confirmed' if was_correct else 'times_rejected'

        cursor.execute(f"""
            UPDATE audit_rules
            SET {field} = {field} + 1,
                times_suggested = times_suggested + 1,
                last_used_at = ?,
                updated_at = ?
            WHERE rule_id = ?
        """, (datetime.now().isoformat(), datetime.now().isoformat(), pattern_id))

        # Recalculate accuracy
        cursor.execute("""
            SELECT times_confirmed, times_rejected
            FROM audit_rules
            WHERE rule_id = ?
        """, (pattern_id,))
        stats = cursor.fetchone()

        total = stats['times_confirmed'] + stats['times_rejected']
        accuracy = stats['times_confirmed'] / total if total > 0 else 0.0

        cursor.execute("""
            UPDATE audit_rules
            SET accuracy_rate = ?
            WHERE rule_id = ?
        """, (accuracy, pattern_id))

        # Enable auto-apply if accuracy is high enough
        if accuracy > 0.95 and total > 20:
            cursor.execute("""
                UPDATE audit_rules
                SET auto_apply_enabled = 1
                WHERE rule_id = ?
            """, (pattern_id,))

        conn.commit()
        conn.close()

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get statistics on learning progress"""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        # Total feedback collected
        cursor.execute("""
            SELECT COUNT(*) as total_feedback FROM user_context
        """)
        stats['total_feedback'] = cursor.fetchone()['total_feedback']

        # Patterns extracted
        cursor.execute("""
            SELECT COUNT(*) as patterns_extracted
            FROM user_context
            WHERE pattern_extracted = 1
        """)
        stats['patterns_extracted'] = cursor.fetchone()['patterns_extracted']

        # Active rules
        cursor.execute("""
            SELECT COUNT(*) as active_rules
            FROM audit_rules
            WHERE enabled = 1
        """)
        stats['active_rules'] = cursor.fetchone()['active_rules']

        # Auto-apply rules
        cursor.execute("""
            SELECT COUNT(*) as auto_apply_rules
            FROM audit_rules
            WHERE auto_apply_enabled = 1
        """)
        stats['auto_apply_rules'] = cursor.fetchone()['auto_apply_rules']

        # Average accuracy
        cursor.execute("""
            SELECT AVG(accuracy_rate) as avg_accuracy
            FROM audit_rules
            WHERE times_suggested > 0
        """)
        result = cursor.fetchone()
        stats['avg_accuracy'] = result['avg_accuracy'] or 0.0

        # Top performing rules
        cursor.execute("""
            SELECT rule_label, accuracy_rate, times_confirmed, times_rejected
            FROM audit_rules
            WHERE times_suggested > 5
            ORDER BY accuracy_rate DESC
            LIMIT 5
        """)
        stats['top_rules'] = [dict(row) for row in cursor.fetchall()]

        # Recent feedback
        cursor.execute("""
            SELECT question_type, COUNT(*) as count
            FROM user_context
            WHERE created_at > datetime('now', '-7 days')
            GROUP BY question_type
            ORDER BY count DESC
        """)
        stats['recent_feedback_by_type'] = {
            row['question_type']: row['count']
            for row in cursor.fetchall()
        }

        conn.close()
        return stats

    def suggest_auto_apply_candidates(self) -> List[Dict[str, Any]]:
        """
        Find patterns that are performing well and could be auto-applied

        Returns:
            List of patterns that are candidates for auto-apply
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM audit_rules
            WHERE auto_apply_enabled = 0
              AND times_suggested >= 10
              AND accuracy_rate >= 0.85
            ORDER BY accuracy_rate DESC, times_confirmed DESC
            LIMIT 10
        """)

        candidates = []
        for row in cursor.fetchall():
            total = row['times_confirmed'] + row['times_rejected']
            candidates.append({
                'rule_id': row['rule_id'],
                'rule_label': row['rule_label'],
                'rule_type': row['rule_type'],
                'accuracy_rate': row['accuracy_rate'],
                'times_suggested': row['times_suggested'],
                'times_confirmed': row['times_confirmed'],
                'times_rejected': row['times_rejected'],
                'sample_size': total,
                'recommendation': (
                    'Enable auto-apply' if row['accuracy_rate'] > 0.90 and total > 15
                    else 'Monitor for a few more cases'
                )
            })

        conn.close()
        return candidates

    def enable_auto_apply_for_rule(self, rule_id: str) -> bool:
        """
        Manually enable auto-apply for a specific rule

        Returns:
            True if successful, False otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE audit_rules
            SET auto_apply_enabled = 1, updated_at = ?
            WHERE rule_id = ?
        """, (datetime.now().isoformat(), rule_id))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return success


    # =========================================================================
    # EMAIL LINK PATTERN LEARNING
    # =========================================================================
    # These methods enable the system to learn from approved email->project links

    def extract_patterns_from_email_suggestion(
        self,
        suggestion: Dict[str, Any],
        email: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract learnable patterns from an approved email_link suggestion.

        Args:
            suggestion: The approved suggestion record
            email: The email that was linked

        Returns:
            List of pattern dicts to store
        """
        patterns = []
        suggested_data = suggestion.get('suggested_data', {})

        if isinstance(suggested_data, str):
            try:
                suggested_data = json.loads(suggested_data)
            except json.JSONDecodeError:
                suggested_data = {}

        # Target info
        proposal_id = suggested_data.get('proposal_id')
        project_id = suggested_data.get('project_id')
        project_code = suggested_data.get('project_code') or suggestion.get('project_code')

        if not (proposal_id or project_id):
            return patterns

        target_type = 'proposal' if proposal_id else 'project'
        target_id = proposal_id or project_id

        # Get target name
        target_name = self._get_target_name(target_type, target_id)

        # Pattern 1: Sender email -> project (skip internal Bensley staff)
        raw_sender = email.get('sender_email')
        sender_email = self._extract_email_address(raw_sender) if raw_sender else None
        if sender_email:
            domain = self._extract_domain(sender_email)

            # NEVER create patterns for internal Bensley staff - they work on many projects
            if domain and not self._is_internal_domain(domain):
                patterns.append({
                    'pattern_type': f'sender_to_{target_type}',
                    'pattern_key': sender_email,  # Store clean email, not RFC 5322 format
                    'pattern_key_normalized': sender_email.lower().strip(),
                    'target_type': target_type,
                    'target_id': target_id,
                    'target_code': project_code,
                    'target_name': target_name,
                    'confidence': 0.75,  # Good starting confidence for sender match
                })

                # Pattern 2: Domain -> project (if corporate email, not generic)
                if not self._is_generic_domain(domain):
                    patterns.append({
                        'pattern_type': f'domain_to_{target_type}',
                        'pattern_key': domain,
                        'pattern_key_normalized': domain.lower().strip(),
                        'target_type': target_type,
                        'target_id': target_id,
                        'target_code': project_code,
                        'target_name': target_name,
                        'confidence': 0.65,  # Lower for domain (could have multiple projects)
                    })

        # Pattern 3: Sender name -> project (if available and NOT internal staff)
        # Skip name patterns for internal staff - they work on many projects
        sender_name = email.get('sender_name')
        is_internal = domain and self._is_internal_domain(domain) if sender_email else False
        if sender_name and len(sender_name) > 3 and not is_internal:
            patterns.append({
                'pattern_type': f'sender_name_to_{target_type}',
                'pattern_key': sender_name,
                'pattern_key_normalized': sender_name.lower().strip(),
                'target_type': target_type,
                'target_id': target_id,
                'target_code': project_code,
                'target_name': target_name,
                'confidence': 0.60,  # Lower confidence (names can be ambiguous)
            })

        return patterns

    def store_email_pattern(
        self,
        pattern: Dict[str, Any],
        suggestion_id: Optional[int] = None,
        email_id: Optional[int] = None
    ) -> Optional[int]:
        """
        Store a learned email pattern, updating if it already exists.

        If pattern already exists:
        - Increment times_correct
        - Boost confidence (up to max)

        Args:
            pattern: Pattern dict from extract_patterns_from_email_suggestion
            suggestion_id: ID of the suggestion that created this pattern
            email_id: ID of the email that triggered the suggestion

        Returns:
            pattern_id or None on failure
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Check if pattern already exists
        cursor.execute("""
            SELECT pattern_id, confidence, times_correct, times_used
            FROM email_learned_patterns
            WHERE pattern_type = ?
              AND pattern_key_normalized = ?
              AND target_type = ?
              AND target_id = ?
        """, (
            pattern['pattern_type'],
            pattern['pattern_key_normalized'],
            pattern['target_type'],
            pattern['target_id']
        ))
        existing = cursor.fetchone()

        if existing:
            # Pattern exists - boost it
            new_confidence = min(
                existing['confidence'] + 0.05,  # Small boost per approval
                MAX_PATTERN_CONFIDENCE
            )

            cursor.execute("""
                UPDATE email_learned_patterns
                SET confidence = ?,
                    times_correct = times_correct + 1,
                    last_used_at = datetime('now')
                WHERE pattern_id = ?
            """, (new_confidence, existing['pattern_id']))

            conn.commit()
            conn.close()

            logger.info(
                f"Boosted pattern {existing['pattern_id']}: "
                f"{pattern['pattern_key']} -> {pattern['target_code']} "
                f"(confidence: {existing['confidence']:.2f} -> {new_confidence:.2f})"
            )

            return existing['pattern_id']
        else:
            # New pattern - insert
            cursor.execute("""
                INSERT INTO email_learned_patterns (
                    pattern_type, pattern_key, pattern_key_normalized,
                    target_type, target_id, target_code, target_name,
                    confidence, times_correct,
                    created_from_suggestion_id, created_from_email_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (
                pattern['pattern_type'],
                pattern['pattern_key'],
                pattern['pattern_key_normalized'],
                pattern['target_type'],
                pattern['target_id'],
                pattern['target_code'],
                pattern['target_name'],
                pattern['confidence'],
                suggestion_id,
                email_id
            ))

            pattern_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.info(
                f"Created pattern {pattern_id}: {pattern['pattern_type']} "
                f"{pattern['pattern_key']} -> {pattern['target_code']} "
                f"(confidence: {pattern['confidence']:.2f})"
            )

            return pattern_id

    def on_email_link_approved(
        self,
        suggestion: Dict[str, Any],
        suggestion_id: int,
        user_notes: str = None
    ) -> List[int]:
        """
        Called when an email_link suggestion is approved.
        Extracts and stores patterns for future learning.
        Logs learning event for analytics.

        Args:
            suggestion: The approved suggestion record
            suggestion_id: ID of the suggestion
            user_notes: Optional notes from the user

        Returns:
            List of created/updated pattern IDs
        """
        suggestion_type = suggestion.get('suggestion_type')
        if suggestion_type != 'email_link':
            return []

        # Get the email that was linked
        suggested_data = suggestion.get('suggested_data', {})
        if isinstance(suggested_data, str):
            try:
                suggested_data = json.loads(suggested_data)
            except json.JSONDecodeError:
                return []

        email_id = suggested_data.get('email_id')
        if not email_id:
            return []

        conn = self._get_connection()
        cursor = conn.cursor()

        # UPDATE EXISTING PATTERN FEEDBACK if a pattern was used to generate this suggestion
        pattern_matched = suggested_data.get('pattern_matched')
        if pattern_matched:
            cursor.execute("""
                UPDATE email_learned_patterns
                SET times_correct = times_correct + 1,
                    confidence = MIN(confidence + 0.02, 0.99),
                    last_used_at = datetime('now')
                WHERE pattern_id = ?
            """, (pattern_matched,))
            logger.info(f"Updated times_correct for pattern {pattern_matched} (suggestion {suggestion_id} approved)")
        cursor.execute("""
            SELECT email_id, sender_email, sender_name, subject
            FROM emails
            WHERE email_id = ?
        """, (email_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return []

        email = dict(row)

        # Extract patterns
        patterns = self.extract_patterns_from_email_suggestion(suggestion, email)

        # Store each pattern and log events
        pattern_ids = []
        project_code = suggested_data.get('project_code')
        sender_email = self._extract_email_address(email.get('sender_email', ''))
        sender_domain = self._extract_domain(sender_email) if sender_email else None

        for pattern in patterns:
            pattern_id = self.store_email_pattern(pattern, suggestion_id, email_id)
            if pattern_id:
                pattern_ids.append(pattern_id)

                # Log learning event
                self._log_learning_event(
                    cursor,
                    event_type='email_link_approved',
                    email_id=email_id,
                    sender_email=sender_email,
                    sender_domain=sender_domain,
                    project_code=project_code,
                    proposal_id=suggested_data.get('proposal_id'),
                    project_id=suggested_data.get('project_id'),
                    pattern_type=pattern['pattern_type'],
                    pattern_key=pattern['pattern_key'],
                    confidence_before=suggested_data.get('gpt_confidence'),
                    confidence_after=pattern['confidence'],
                    user_notes=user_notes,
                    gpt_reasoning=suggested_data.get('gpt_reasoning'),
                )

        # Also link the contact to this project if not already
        contact_id = self._get_or_create_contact(cursor, sender_email, email.get('sender_name'))
        if contact_id and suggested_data.get('proposal_id'):
            self._link_contact_to_proposal(cursor, contact_id, suggested_data.get('proposal_id'))

        conn.commit()
        conn.close()

        return pattern_ids

    def _log_learning_event(
        self,
        cursor,
        event_type: str,
        email_id: int = None,
        sender_email: str = None,
        sender_domain: str = None,
        project_code: str = None,
        proposal_id: int = None,
        project_id: int = None,
        pattern_type: str = None,
        pattern_key: str = None,
        confidence_before: float = None,
        confidence_after: float = None,
        user_notes: str = None,
        gpt_reasoning: str = None,
        correct_project_code: str = None,
    ):
        """Log a learning event for analytics and debugging."""
        confidence_delta = None
        if confidence_before is not None and confidence_after is not None:
            confidence_delta = confidence_after - confidence_before

        cursor.execute("""
            INSERT INTO learning_events (
                event_type, email_id, sender_email, sender_domain,
                project_code, proposal_id, project_id,
                pattern_type, pattern_key,
                confidence_before, confidence_after, confidence_delta,
                user_notes, gpt_reasoning, correct_project_code
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_type, email_id, sender_email, sender_domain,
            project_code, proposal_id, project_id,
            pattern_type, pattern_key,
            confidence_before, confidence_after, confidence_delta,
            user_notes, gpt_reasoning, correct_project_code
        ))

    def _get_or_create_contact(self, cursor, email: str, name: str = None) -> Optional[int]:
        """Get or create a contact record."""
        if not email:
            return None

        cursor.execute("""
            SELECT contact_id FROM contacts WHERE email = ?
        """, (email.lower(),))
        row = cursor.fetchone()

        if row:
            return row['contact_id']

        # Only create for non-internal domains
        domain = self._extract_domain(email)
        if domain and self._is_internal_domain(domain):
            return None

        # Create new contact
        cursor.execute("""
            INSERT INTO contacts (email, name, created_at)
            VALUES (?, ?, datetime('now'))
        """, (email.lower(), name))

        return cursor.lastrowid

    def _link_contact_to_proposal(self, cursor, contact_id: int, proposal_id: int):
        """Link a contact to a proposal if not already linked."""
        cursor.execute("""
            INSERT OR IGNORE INTO project_contacts (contact_id, proposal_id, created_at)
            VALUES (?, ?, datetime('now'))
        """, (contact_id, proposal_id))

    def on_email_link_rejected(
        self,
        suggestion: Dict[str, Any],
        suggestion_id: int,
        user_notes: str = None,
        correct_project_code: str = None
    ) -> Dict[str, Any]:
        """
        Called when an email_link suggestion is rejected.
        Decreases confidence of matching patterns.
        If user provides correct_project_code, learns that instead.
        If user notes contain "spam" or "admin", creates skip pattern.
        Logs learning event for analytics.

        Args:
            suggestion: The rejected suggestion record
            suggestion_id: ID of the suggestion
            user_notes: Optional user explanation (e.g., "this is spam", "administrative email")
            correct_project_code: Optional correct project code if user is correcting

        Returns:
            Dict with learning results
        """
        suggestion_type = suggestion.get('suggestion_type')
        if suggestion_type != 'email_link':
            return {'learned': False, 'reason': 'not email_link'}

        suggested_data = suggestion.get('suggested_data', {})
        if isinstance(suggested_data, str):
            try:
                suggested_data = json.loads(suggested_data)
            except json.JSONDecodeError:
                return {'learned': False, 'reason': 'invalid suggested_data'}

        email_id = suggested_data.get('email_id')
        if not email_id:
            return {'learned': False, 'reason': 'no email_id'}

        conn = self._get_connection()
        cursor = conn.cursor()

        # UPDATE EXISTING PATTERN FEEDBACK if a pattern was used to generate this suggestion
        pattern_matched = suggested_data.get('pattern_matched')
        if pattern_matched:
            cursor.execute("""
                UPDATE email_learned_patterns
                SET times_rejected = times_rejected + 1,
                    confidence = MAX(confidence - 0.1, 0.1)
                WHERE pattern_id = ?
            """, (pattern_matched,))
            logger.info(f"Updated times_rejected for pattern {pattern_matched} (suggestion {suggestion_id} rejected)")

        cursor.execute("""
            SELECT email_id, sender_email, sender_name, subject
            FROM emails
            WHERE email_id = ?
        """, (email_id,))
        row = cursor.fetchone()

        if not row or not row['sender_email']:
            conn.close()
            return {'learned': False, 'reason': 'email not found'}

        email = dict(row)
        sender_email = self._extract_email_address(email.get('sender_email', ''))
        sender_domain = self._extract_domain(sender_email) if sender_email else None

        result = {'learned': False, 'patterns_affected': 0}

        # Penalize the wrong pattern (reduce confidence)
        cursor.execute("""
            UPDATE email_learned_patterns
            SET times_rejected = times_rejected + 1,
                confidence = MAX(confidence - 0.15, ?)
            WHERE pattern_key_normalized = ?
              AND is_active = 1
        """, (MIN_PATTERN_CONFIDENCE, sender_email))
        result['patterns_affected'] = cursor.rowcount

        # Log rejection event
        self._log_learning_event(
            cursor,
            event_type='email_link_rejected',
            email_id=email_id,
            sender_email=sender_email,
            sender_domain=sender_domain,
            project_code=suggested_data.get('project_code'),
            proposal_id=suggested_data.get('proposal_id'),
            confidence_before=suggested_data.get('gpt_confidence'),
            confidence_after=suggested_data.get('gpt_confidence', 0.5) - 0.15,
            user_notes=user_notes,
            gpt_reasoning=suggested_data.get('gpt_reasoning'),
            correct_project_code=correct_project_code,
        )

        # If user provided correct project, learn it
        if correct_project_code:
            cursor.execute("""
                SELECT proposal_id, project_name FROM proposals WHERE project_code = ?
            """, (correct_project_code,))
            correct_proposal = cursor.fetchone()

            if correct_proposal:
                # Create/boost pattern for the correct project
                cursor.execute("""
                    INSERT INTO email_learned_patterns (
                        pattern_type, pattern_key, pattern_key_normalized,
                        target_type, target_id, target_code, target_name,
                        confidence, times_correct, created_from_email_id
                    ) VALUES ('sender_to_proposal', ?, ?, 'proposal', ?, ?, ?, 0.85, 1, ?)
                    ON CONFLICT(pattern_type, pattern_key) DO UPDATE SET
                        target_id = excluded.target_id,
                        target_code = excluded.target_code,
                        target_name = excluded.target_name,
                        confidence = MIN(confidence + 0.15, ?),
                        times_correct = times_correct + 1,
                        updated_at = datetime('now')
                """, (
                    sender_email, sender_email,
                    correct_proposal['proposal_id'], correct_project_code,
                    correct_proposal['project_name'], email_id,
                    MAX_PATTERN_CONFIDENCE
                ))

                self._log_learning_event(
                    cursor,
                    event_type='pattern_created_from_correction',
                    email_id=email_id,
                    sender_email=sender_email,
                    sender_domain=sender_domain,
                    project_code=correct_project_code,
                    proposal_id=correct_proposal['proposal_id'],
                    pattern_type='sender_to_proposal',
                    pattern_key=sender_email,
                    confidence_after=0.85,
                    user_notes=user_notes,
                    correct_project_code=correct_project_code,
                )

                result['learned'] = True
                result['learned_correct_project'] = correct_project_code

        # If user notes indicate spam/admin, create skip pattern
        if user_notes:
            notes_lower = user_notes.lower()
            if any(keyword in notes_lower for keyword in ['spam', 'junk', 'newsletter', 'marketing']):
                self._create_skip_pattern(cursor, sender_domain, 'spam', email_id)
                result['learned'] = True
                result['skip_pattern_created'] = f"domain_to_skip: {sender_domain}"

            elif any(keyword in notes_lower for keyword in ['admin', 'hr', 'it', 'internal', 'ops']):
                self._create_skip_pattern(cursor, sender_domain, 'administrative', email_id)
                result['learned'] = True
                result['skip_pattern_created'] = f"domain_to_skip: {sender_domain}"

        conn.commit()
        conn.close()

        logger.info(f"Rejected link for {sender_email}, learned: {result.get('learned')}")
        return result

    def _create_skip_pattern(
        self,
        cursor,
        domain: str,
        skip_type: str,
        email_id: int
    ):
        """Create a pattern to skip emails from a domain."""
        if not domain:
            return

        cursor.execute("""
            INSERT INTO email_learned_patterns (
                pattern_type, pattern_key, pattern_key_normalized,
                target_type, target_id, target_code, target_name,
                confidence, created_from_email_id
            ) VALUES ('domain_to_skip', ?, ?, 'skip', 0, 'SKIP', ?, 0.9, ?)
            ON CONFLICT(pattern_type, pattern_key) DO UPDATE SET
                confidence = MIN(confidence + 0.1, 0.95),
                times_correct = times_correct + 1,
                updated_at = datetime('now')
        """, (domain, domain, skip_type, email_id))

    def match_patterns_for_email(
        self,
        email: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Find all learned patterns that match this email.

        Args:
            email: Email record with sender_email, sender_name, subject

        Returns:
            List of matching patterns with match scores
        """
        matches = []
        raw_sender = email.get('sender_email') or ''
        # Extract clean email from RFC 5322 format (e.g., "Name <email@domain.com>")
        sender_email = self._extract_email_address(raw_sender) or ''
        sender_name = (email.get('sender_name') or '').lower().strip()

        if not sender_email:
            return matches

        conn = self._get_connection()
        cursor = conn.cursor()

        # Match by exact sender email
        cursor.execute("""
            SELECT *
            FROM email_learned_patterns
            WHERE pattern_key_normalized = ?
              AND pattern_type IN ('sender_to_project', 'sender_to_proposal')
              AND is_active = 1
            ORDER BY confidence DESC
        """, (sender_email,))

        for row in cursor.fetchall():
            matches.append({
                **dict(row),
                'match_type': 'sender_email',
                'match_score': 1.0  # Exact match
            })

        # Match by domain
        domain = self._extract_domain(sender_email)
        if domain:
            cursor.execute("""
                SELECT *
                FROM email_learned_patterns
                WHERE pattern_key_normalized = ?
                  AND pattern_type IN ('domain_to_project', 'domain_to_proposal')
                  AND is_active = 1
                ORDER BY confidence DESC
            """, (domain.lower(),))

            for row in cursor.fetchall():
                matches.append({
                    **dict(row),
                    'match_type': 'domain',
                    'match_score': 0.8
                })

        # Match by sender name (exact)
        if sender_name and len(sender_name) > 3:
            cursor.execute("""
                SELECT *
                FROM email_learned_patterns
                WHERE pattern_key_normalized = ?
                  AND pattern_type IN ('sender_name_to_project', 'sender_name_to_proposal')
                  AND is_active = 1
                ORDER BY confidence DESC
            """, (sender_name,))

            for row in cursor.fetchall():
                matches.append({
                    **dict(row),
                    'match_type': 'sender_name',
                    'match_score': 0.7
                })

        conn.close()
        return matches

    def get_best_pattern_match_for_email(
        self,
        email: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Get the best pattern match for an email, if any.

        Returns:
            Best matching pattern with adjusted confidence, or None
        """
        matches = self.match_patterns_for_email(email)

        if not matches:
            return None

        # Score = pattern confidence * match score
        for m in matches:
            m['effective_score'] = m['confidence'] * m['match_score']

        # Return highest scoring match
        best = max(matches, key=lambda x: x['effective_score'])

        # Only return if score is meaningful
        if best['effective_score'] >= 0.5:
            return best

        return None

    def suggest_link_from_patterns(
        self,
        email: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a suggestion for an email based on learned patterns.

        Args:
            email: Email record

        Returns:
            Suggestion dict or None if no good pattern match
        """
        # Skip internal @bensley.com emails - they don't need project linking
        sender_email = email.get('sender_email', '')
        sender_lower = sender_email.lower() if sender_email else ''
        if 'bensley.com' in sender_lower or 'bensley.co.id' in sender_lower:
            return None

        best_match = self.get_best_pattern_match_for_email(email)

        if not best_match:
            return None

        # Build suggestion
        email_id = email.get('email_id')
        target_type = best_match['target_type']
        target_id = best_match['target_id']
        target_code = best_match['target_code']

        # Calculate boosted confidence
        base_confidence = best_match['effective_score']
        boosted_confidence = min(
            base_confidence + PATTERN_CONFIDENCE_BOOST,
            MAX_PATTERN_CONFIDENCE
        )

        # Build evidence string
        pattern_type = best_match['pattern_type']
        pattern_key = best_match['pattern_key']
        times_correct = best_match.get('times_correct', 0)

        evidence = (
            f"Based on {times_correct} previous approvals: "
            f"{pattern_type.replace('_', ' ')} '{pattern_key}' -> {target_code}"
        )

        suggestion_data = {
            'email_id': email_id,
            'project_code': target_code,
            'confidence_score': boosted_confidence,
            'match_method': 'learned_pattern',
            'match_reason': evidence,
            'pattern_id': best_match['pattern_id'],
        }

        if target_type == 'proposal':
            suggestion_data['proposal_id'] = target_id
        else:
            suggestion_data['project_id'] = target_id

        # Get email subject for source reference
        subject = email.get('subject', '')[:50] if email.get('subject') else 'Email'

        return {
            'suggestion_type': 'email_link',
            'title': f"Link to {target_code} (learned)",
            'description': evidence,
            'confidence_score': boosted_confidence,
            'priority': 'high' if boosted_confidence > 0.8 else 'medium',
            'source_type': 'pattern',
            'source_id': email_id,
            'source_reference': f"Email: {subject}",
            'suggested_action': 'Create email_proposal_link',
            'project_code': target_code,
            'proposal_id': target_id if target_type == 'proposal' else None,
            'suggested_data': json.dumps(suggestion_data),
            'target_table': (
                'email_proposal_links' if target_type == 'proposal'
                else 'email_project_links'
            ),
        }

    def log_pattern_usage(
        self,
        pattern_id: int,
        suggestion_id: Optional[int] = None,
        email_id: Optional[int] = None,
        action: str = 'matched',
        match_score: Optional[float] = None,
        confidence_contribution: Optional[float] = None
    ) -> None:
        """
        Log usage of a pattern for analytics.

        Args:
            pattern_id: ID of the pattern used
            suggestion_id: ID of resulting suggestion (if any)
            email_id: ID of email being processed
            action: 'matched', 'suggested', 'approved', 'rejected', 'boosted'
            match_score: How well the pattern matched
            confidence_contribution: How much confidence the pattern added
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO email_pattern_usage_log (
                pattern_id, suggestion_id, email_id,
                action, match_score, confidence_contribution
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            pattern_id, suggestion_id, email_id,
            action, match_score, confidence_contribution
        ))

        # Update times_used on the pattern
        if action in ('matched', 'suggested'):
            cursor.execute("""
                UPDATE email_learned_patterns
                SET times_used = times_used + 1,
                    last_used_at = datetime('now')
                WHERE pattern_id = ?
            """, (pattern_id,))

        conn.commit()
        conn.close()

    def get_email_pattern_stats(self) -> Dict[str, Any]:
        """
        Get statistics about learned email patterns.

        Returns:
            Dict with pattern counts, effectiveness, etc.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        stats = {}

        # Check if email_learned_patterns table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='email_learned_patterns'
        """)
        if not cursor.fetchone():
            conn.close()
            return {'error': 'email_learned_patterns table not found - run migration 051'}

        # Total patterns
        cursor.execute("SELECT COUNT(*) as cnt FROM email_learned_patterns")
        stats['total_patterns'] = cursor.fetchone()['cnt']

        cursor.execute(
            "SELECT COUNT(*) as cnt FROM email_learned_patterns WHERE is_active = 1"
        )
        stats['active_patterns'] = cursor.fetchone()['cnt']

        # By type
        cursor.execute("""
            SELECT pattern_type, COUNT(*) as count
            FROM email_learned_patterns
            WHERE is_active = 1
            GROUP BY pattern_type
            ORDER BY count DESC
        """)
        stats['by_type'] = {r['pattern_type']: r['count'] for r in cursor.fetchall()}

        # By target project
        cursor.execute("""
            SELECT target_code, COUNT(*) as pattern_count
            FROM email_learned_patterns
            WHERE is_active = 1
            GROUP BY target_code
            ORDER BY pattern_count DESC
            LIMIT 10
        """)
        stats['top_projects'] = [
            {'project': r['target_code'], 'patterns': r['pattern_count']}
            for r in cursor.fetchall()
        ]

        # Effectiveness
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(times_used) as total_uses,
                SUM(times_correct) as total_correct,
                SUM(times_rejected) as total_rejected,
                AVG(confidence) as avg_confidence
            FROM email_learned_patterns
            WHERE is_active = 1
        """)
        row = cursor.fetchone()
        stats['effectiveness'] = {
            'total': row['total'],
            'total_uses': row['total_uses'] or 0,
            'total_correct': row['total_correct'] or 0,
            'total_rejected': row['total_rejected'] or 0,
            'avg_confidence': row['avg_confidence'] or 0,
        }

        # Success rate
        if stats['effectiveness']['total_uses'] > 0:
            stats['effectiveness']['success_rate'] = (
                stats['effectiveness']['total_correct'] /
                stats['effectiveness']['total_uses']
            )
        else:
            stats['effectiveness']['success_rate'] = 0

        conn.close()
        return stats

    def get_patterns_for_project(self, project_code: str) -> List[Dict[str, Any]]:
        """
        Get all learned patterns for a specific project.

        Args:
            project_code: Project code (e.g., 'BK-070')

        Returns:
            List of patterns
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM email_learned_patterns
            WHERE target_code = ?
              AND is_active = 1
            ORDER BY confidence DESC, times_correct DESC
        """, (project_code,))

        patterns = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return patterns

    # Helper methods for email pattern learning

    def _extract_email_address(self, email_str: str) -> Optional[str]:
        """Extract clean email address from RFC 5322 format.

        Handles formats like:
        - simple@domain.com -> simple@domain.com
        - "Name" <simple@domain.com> -> simple@domain.com
        - Name <simple@domain.com> -> simple@domain.com

        Returns:
            Clean email address (lowercase) or None if not parseable
        """
        if not email_str or '@' not in email_str:
            return None

        # Extract email from RFC 5322 format if present
        match = re.search(r'<([^>]+@[^>]+)>', email_str)
        if match:
            return match.group(1).lower().strip()

        # No angle brackets, assume plain email format
        return email_str.lower().strip()

    def _extract_domain(self, email: str) -> Optional[str]:
        """Extract domain from email address, handling RFC 5322 format.

        Handles formats like:
        - simple@domain.com
        - "Name" <simple@domain.com>
        - Name <simple@domain.com>
        """
        # First extract the clean email address
        clean_email = self._extract_email_address(email)
        if not clean_email or '@' not in clean_email:
            return None

        return clean_email.split('@')[1].lower()

    def _is_internal_domain(self, domain: str) -> bool:
        """Check if domain is internal Bensley staff.

        Internal staff work across many projects, so we should NEVER
        create sender patterns for them.
        """
        internal_domains = {
            'bensley.com', 'bensleydesign.com', 'bensley.co.th',
            'bensley.id', 'bensley.co.id'
        }
        return domain.lower() in internal_domains

    def _is_generic_domain(self, domain: str) -> bool:
        """Check if domain is a generic email provider (gmail, yahoo, etc).

        Generic domains shouldn't create domain patterns because many
        unrelated people use them.
        """
        generic_domains = {
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'aol.com', 'icloud.com', 'mail.com', 'protonmail.com',
            'live.com', 'msn.com', 'ymail.com', 'googlemail.com'
        }
        return domain.lower() in generic_domains

    def _get_target_name(self, target_type: str, target_id: int) -> Optional[str]:
        """Get the name of a project or proposal"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if target_type == 'proposal':
            cursor.execute(
                "SELECT project_name FROM proposals WHERE proposal_id = ?",
                (target_id,)
            )
            row = cursor.fetchone()
            conn.close()
            return row['project_name'] if row else None
        else:
            cursor.execute(
                "SELECT project_title FROM projects WHERE project_id = ?",
                (target_id,)
            )
            row = cursor.fetchone()
            conn.close()
            return row['project_title'] if row else None


if __name__ == '__main__':
    """Test learning service"""
    service = LearningService()

    print("📊 Learning System Statistics")
    print("=" * 80)

    stats = service.get_learning_stats()

    print(f"\nTotal Feedback Collected: {stats['total_feedback']}")
    print(f"Patterns Extracted: {stats['patterns_extracted']}")
    print(f"Active Rules: {stats['active_rules']}")
    print(f"Auto-Apply Rules: {stats['auto_apply_rules']}")
    print(f"Average Accuracy: {stats['avg_accuracy']*100:.1f}%")

    if stats['top_rules']:
        print(f"\n🏆 Top Performing Rules:")
        for rule in stats['top_rules']:
            print(f"  • {rule['rule_label']}")
            print(f"    Accuracy: {rule['accuracy_rate']*100:.1f}% ({rule['times_confirmed']} confirmed, {rule['times_rejected']} rejected)")

    print("\n" + "=" * 80)

    # Check for auto-apply candidates
    candidates = service.suggest_auto_apply_candidates()
    if candidates:
        print(f"\n💡 Auto-Apply Candidates ({len(candidates)}):")
        for c in candidates:
            print(f"  • {c['rule_label']}")
            print(f"    Accuracy: {c['accuracy_rate']*100:.1f}% over {c['sample_size']} cases")
            print(f"    Recommendation: {c['recommendation']}")
        print("\n" + "=" * 80)
