"""
Service layer for training data management
Handles AI decision verification and feedback collection
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import sqlite3
import json


class TrainingService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self):
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_unverified_training(
        self,
        task_type: Optional[str] = None,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Get unverified training data with filtering and pagination

        Args:
            task_type: Filter by task type (classify, extract, summarize)
            min_confidence: Minimum confidence score
            max_confidence: Maximum confidence score
            page: Page number
            per_page: Items per page

        Returns:
            Dict with 'data' and 'pagination' keys
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build WHERE clause
        where_clauses = ["human_verified = 0"]
        params = []

        if task_type:
            where_clauses.append("task_type = ?")
            params.append(task_type)

        if min_confidence is not None:
            where_clauses.append("confidence >= ?")
            params.append(min_confidence)

        if max_confidence is not None:
            where_clauses.append("confidence <= ?")
            params.append(max_confidence)

        where_sql = f"WHERE {' AND '.join(where_clauses)}"

        # Get total count
        cursor.execute(f"SELECT COUNT(*) FROM training_data {where_sql}", params)
        total = cursor.fetchone()[0]

        # Get paginated results
        offset = (page - 1) * per_page
        query_params = params + [per_page, offset]

        cursor.execute(f"""
            SELECT
                training_id,
                task_type,
                input_data,
                output_data,
                model_used,
                confidence,
                human_verified,
                feedback,
                created_at
            FROM training_data
            {where_sql}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, query_params)

        training_records = []
        for row in cursor.fetchall():
            training_records.append(dict(row))

        conn.close()

        total_pages = (total + per_page - 1) // per_page

        return {
            "data": training_records,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages
            }
        }

    def get_training_by_id(self, training_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific training record by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM training_data
            WHERE training_id = ?
        """, (training_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return dict(row)

    def verify_training(
        self,
        training_id: int,
        is_correct: bool,
        feedback: Optional[str] = None,
        corrected_output: Optional[str] = None
    ) -> bool:
        """
        Verify a training record as correct or incorrect

        Args:
            training_id: ID of training record
            is_correct: Whether the AI output was correct
            feedback: Optional feedback explaining why it's wrong
            corrected_output: If incorrect, the correct output

        Returns:
            Success status
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build feedback JSON
        feedback_data = {
            "is_correct": is_correct,
            "feedback": feedback,
            "corrected_output": corrected_output,
            "verified_at": datetime.now().isoformat()
        }

        cursor.execute("""
            UPDATE training_data
            SET human_verified = 1,
                feedback = ?
            WHERE training_id = ?
        """, (json.dumps(feedback_data), training_id))

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def get_verification_stats(self) -> Dict[str, Any]:
        """Get overall verification statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Overall stats
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(human_verified) as verified,
                COUNT(*) - SUM(human_verified) as unverified
            FROM training_data
        """)
        overall = dict(cursor.fetchone())

        # Stats by task type
        cursor.execute("""
            SELECT
                task_type,
                COUNT(*) as total,
                SUM(human_verified) as verified,
                COUNT(*) - SUM(human_verified) as unverified,
                AVG(confidence) as avg_confidence
            FROM training_data
            GROUP BY task_type
        """)
        by_task_type = [dict(row) for row in cursor.fetchall()]

        # Stats by confidence ranges
        cursor.execute("""
            SELECT
                CASE
                    WHEN confidence >= 0.9 THEN 'high (0.9+)'
                    WHEN confidence >= 0.7 THEN 'medium (0.7-0.9)'
                    ELSE 'low (<0.7)'
                END as confidence_range,
                COUNT(*) as total,
                SUM(human_verified) as verified,
                COUNT(*) - SUM(human_verified) as unverified
            FROM training_data
            GROUP BY confidence_range
            ORDER BY MIN(confidence) DESC
        """)
        by_confidence = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            "overall": overall,
            "by_task_type": by_task_type,
            "by_confidence": by_confidence
        }

    def get_incorrect_predictions(
        self,
        task_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Get training records that were marked as incorrect
        Useful for understanding AI mistakes and improving prompts
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        where_clauses = ["human_verified = 1", "feedback IS NOT NULL"]
        params = []

        if task_type:
            where_clauses.append("task_type = ?")
            params.append(task_type)

        where_sql = f"WHERE {' AND '.join(where_clauses)}"

        # Get total count
        cursor.execute(f"SELECT COUNT(*) FROM training_data {where_sql}", params)
        total = cursor.fetchone()[0]

        # Get paginated results
        offset = (page - 1) * per_page
        query_params = params + [per_page, offset]

        cursor.execute(f"""
            SELECT
                training_id,
                task_type,
                input_data,
                output_data,
                model_used,
                confidence,
                feedback,
                created_at
            FROM training_data
            {where_sql}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, query_params)

        records = []
        for row in cursor.fetchall():
            record = dict(row)
            # Parse feedback JSON
            if record.get('feedback'):
                try:
                    record['feedback'] = json.loads(record['feedback'])
                except (json.JSONDecodeError, TypeError):
                    pass
            records.append(record)

        conn.close()

        total_pages = (total + per_page - 1) // per_page

        return {
            "data": records,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages
            }
        }

    def bulk_verify(
        self,
        training_ids: List[int],
        is_correct: bool,
        feedback: Optional[str] = None
    ) -> int:
        """
        Bulk verify multiple training records at once

        Returns:
            Number of records updated
        """
        if not training_ids:
            return 0

        conn = self._get_connection()
        cursor = conn.cursor()

        feedback_data = {
            "is_correct": is_correct,
            "feedback": feedback,
            "verified_at": datetime.now().isoformat()
        }

        placeholders = ','.join('?' * len(training_ids))
        cursor.execute(f"""
            UPDATE training_data
            SET human_verified = 1,
                feedback = ?
            WHERE training_id IN ({placeholders})
        """, [json.dumps(feedback_data)] + training_ids)

        conn.commit()
        count = cursor.rowcount
        conn.close()

        return count
