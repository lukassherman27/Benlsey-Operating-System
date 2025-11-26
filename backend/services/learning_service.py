#!/usr/bin/env python3
"""
Learning Service - Continuous Learning from User Feedback
Analyzes user decisions and feedback to improve pattern detection accuracy
"""

import sqlite3
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import re

import os
DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')


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
