"""
Training Data Service - Captures user feedback for RLHF training (Phase 2)

Collects feedback on:
- Query results
- Email categories
- Project health scores
- Invoice classifications
- Any AI-generated content

This data will be used for Reinforcement Learning from Human Feedback
"""

import sqlite3
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from .base_service import BaseService


class TrainingDataService(BaseService):
    """Service for collecting training data from user feedback"""

    def log_feedback(
        self,
        feature_type: str,
        feature_id: str,
        helpful: bool,
        issue_type: Optional[str] = None,
        feedback_text: Optional[str] = None,
        expected_value: Optional[str] = None,
        current_value: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log user feedback with context for RLHF training

        Args:
            feature_type: Type of feature (e.g., 'kpi_outstanding_invoices', 'email_category')
            feature_id: ID of the feature instance (e.g., 'dashboard', email_id)
            helpful: True if user found it helpful, False otherwise
            issue_type: Category of issue (if helpful=False) - comma-separated list
            feedback_text: REQUIRED explanation if helpful=False
            expected_value: What user expected to see
            current_value: What system actually shows
            context: Additional context data (will be JSON-ified)

        Returns:
            Dict with training_id and success status

        Raises:
            ValueError: If helpful=False and feedback_text is not provided
        """
        # CRITICAL: Require explanation for negative feedback
        if not helpful and not feedback_text:
            raise ValueError("feedback_text is REQUIRED when helpful=False")

        with self.get_connection() as conn:
            cursor = conn.cursor()

            context_json = json.dumps(context) if context else None

            cursor.execute("""
                INSERT INTO training_data (
                    user_id, feature_type, feature_id,
                    helpful, issue_type, feedback_text,
                    expected_value, current_value, context_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'bill',  # TODO: Get from auth context
                feature_type,
                feature_id,
                1 if helpful else 0,
                issue_type,
                feedback_text,
                expected_value,
                current_value,
                context_json,
                datetime.now().isoformat()
            ))

            training_id = cursor.lastrowid
            conn.commit()

            return {
                "success": True,
                "training_id": training_id,
                "message": "Feedback logged successfully"
            }

    def get_feedback_stats(
        self,
        feature_type: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get feedback statistics

        Args:
            feature_type: Filter by feature type (optional)
            days: Number of days to look back

        Returns:
            Stats dict with counts and percentages
        """
        sql = """
            SELECT
                feature_type,
                COUNT(*) as total,
                SUM(CASE WHEN helpful = 1 THEN 1 ELSE 0 END) as helpful_count,
                SUM(CASE WHEN helpful = 0 THEN 1 ELSE 0 END) as not_helpful_count,
                COUNT(DISTINCT user_id) as unique_users
            FROM training_data
            WHERE user_id IS NOT NULL
            AND created_at >= datetime('now', '-' || ? || ' days')
        """

        params = [days]
        if feature_type:
            sql += " AND feature_type = ?"
            params.append(feature_type)

        sql += " GROUP BY feature_type"

        results = self.execute_query(sql, tuple(params))

        return {
            "success": True,
            "stats": results,
            "period_days": days
        }

    def get_recent_feedback(
        self,
        feature_type: Optional[str] = None,
        helpful: Optional[bool] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent feedback entries for review/analysis

        Args:
            feature_type: Filter by feature type
            helpful: Filter by helpful status (True/False/None for all)
            limit: Max number to return

        Returns:
            List of feedback entries
        """
        sql = """
            SELECT
                training_id,
                user_id,
                feature_type,
                feature_id,
                helpful,
                issue_type,
                feedback_text,
                expected_value,
                current_value,
                context_json,
                created_at
            FROM training_data
            WHERE user_id IS NOT NULL
        """

        params = []

        if feature_type:
            sql += " AND feature_type = ?"
            params.append(feature_type)

        if helpful is not None:
            sql += " AND helpful = ?"
            params.append(1 if helpful else 0)

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        return self.execute_query(sql, tuple(params))
