#!/usr/bin/env python3
"""
Intelligence Service - AI Suggestion Management
Handles AI-generated database suggestions, decisions, and pattern learning

Updated: 2025-11-26 - Fixed to match actual database schema
"""

import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Use correct database path - OneDrive master database
DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')


class IntelligenceService:
    """Service for managing AI suggestions and decisions"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_suggestions(
        self,
        status: str = "pending",
        data_table: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get suggestions filtered by status and table

        Args:
            status: pending, approved, rejected, applied
            data_table: filter by table name (projects, proposals, etc)
            limit: max results to return

        Returns:
            Dict with 'group' and 'items' list

        Schema: ai_suggestions_queue has columns:
            suggestion_id, data_table, record_id, field_name,
            current_value, suggested_value, confidence, reasoning,
            evidence, status, created_at, reviewed_at, applied_at
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                suggestion_id,
                data_table,
                record_id,
                field_name,
                current_value,
                suggested_value,
                confidence,
                reasoning,
                evidence,
                status,
                created_at,
                reviewed_at,
                applied_at
            FROM ai_suggestions_queue
            WHERE status = ?
        """
        params = [status]

        if data_table:
            query += " AND data_table = ?"
            params.append(data_table)

        query += " ORDER BY confidence DESC, created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        suggestions = []

        for row in cursor.fetchall():
            # Parse evidence if it's JSON
            evidence = row['evidence']
            if evidence:
                try:
                    evidence = json.loads(evidence)
                except:
                    pass  # Keep as string if not valid JSON

            suggestion = {
                'id': row['suggestion_id'],
                'suggestion_id': row['suggestion_id'],
                'data_table': row['data_table'],
                'record_id': row['record_id'],
                'field_name': row['field_name'],
                'current_value': row['current_value'],
                'suggested_value': row['suggested_value'],
                'confidence': row['confidence'],
                'reasoning': row['reasoning'],
                'evidence': evidence,
                'status': row['status'],
                'created_at': row['created_at'],
                'reviewed_at': row['reviewed_at'],
                'applied_at': row['applied_at']
            }

            # Try to get related record info based on data_table
            if row['data_table'] == 'projects' and row['record_id']:
                cursor.execute("""
                    SELECT project_code, project_title
                    FROM projects WHERE project_id = ?
                    LIMIT 1
                """, (row['record_id'],))
                project = cursor.fetchone()
                if project:
                    suggestion['project_code'] = project['project_code']
                    suggestion['project_title'] = project['project_title']

            elif row['data_table'] == 'proposals' and row['record_id']:
                cursor.execute("""
                    SELECT proposal_code, project_name
                    FROM proposals WHERE proposal_id = ?
                    LIMIT 1
                """, (row['record_id'],))
                proposal = cursor.fetchone()
                if proposal:
                    suggestion['proposal_code'] = proposal['proposal_code']
                    suggestion['project_name'] = proposal['project_name']

            suggestions.append(suggestion)

        conn.close()

        return {
            'group': data_table or 'all',
            'items': suggestions,
            'count': len(suggestions)
        }

    def get_patterns(self) -> Dict[str, Any]:
        """Get all learned patterns with statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                pattern_id,
                pattern_name,
                pattern_type,
                condition,
                action,
                confidence_score,
                evidence_count,
                is_active,
                created_at,
                updated_at
            FROM learned_patterns
            WHERE is_active = 1
            ORDER BY confidence_score DESC, evidence_count DESC
        """)

        patterns = []
        for row in cursor.fetchall():
            # Parse JSON fields
            condition = row['condition']
            action = row['action']
            try:
                condition = json.loads(condition) if condition else {}
            except:
                pass
            try:
                action = json.loads(action) if action else {}
            except:
                pass

            pattern = {
                'pattern_id': row['pattern_id'],
                'pattern_name': row['pattern_name'],
                'pattern_type': row['pattern_type'],
                'condition': condition,
                'action': action,
                'confidence_score': row['confidence_score'],
                'evidence_count': row['evidence_count'],
                'is_active': bool(row['is_active']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
            patterns.append(pattern)

        conn.close()
        return {'patterns': patterns, 'count': len(patterns)}

    def apply_decision(
        self,
        suggestion_id: int,
        decision: str,
        reason: Optional[str] = None,
        apply_now: bool = True,
        dry_run: bool = False,
        decision_by: str = "user"
    ) -> Dict[str, Any]:
        """
        Apply a decision to a suggestion

        Args:
            suggestion_id: ID of the suggestion
            decision: approved, rejected
            reason: optional reason for decision
            apply_now: whether to apply changes to database immediately
            dry_run: preview changes without applying
            decision_by: who made the decision
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if dry_run:
            # Preview mode - get suggestion details
            cursor.execute("""
                SELECT * FROM ai_suggestions_queue WHERE suggestion_id = ?
            """, (suggestion_id,))
            suggestion = cursor.fetchone()

            if not suggestion:
                conn.close()
                return {'error': 'Suggestion not found', 'preview': [], 'applied': False}

            conn.close()
            return {
                'would_update': 1,
                'preview': [{
                    'table': suggestion['data_table'],
                    'record_id': suggestion['record_id'],
                    'field': suggestion['field_name'],
                    'from': suggestion['current_value'],
                    'to': suggestion['suggested_value']
                }],
                'applied': False
            }

        # Get suggestion
        cursor.execute("SELECT * FROM ai_suggestions_queue WHERE suggestion_id = ?", (suggestion_id,))
        suggestion = cursor.fetchone()

        if not suggestion:
            conn.close()
            return {'error': 'Suggestion not found', 'updated': 0}

        results = {
            'updated': 0,
            'applied': [],
            'errors': []
        }

        now = datetime.now().isoformat()

        if decision == 'approved':
            if apply_now:
                # Apply the change to the target table
                try:
                    data_table = suggestion['data_table']
                    record_id = suggestion['record_id']
                    field_name = suggestion['field_name']
                    new_value = suggestion['suggested_value']

                    # Determine primary key column based on table
                    pk_column = 'id'
                    if data_table == 'projects':
                        pk_column = 'project_id'
                    elif data_table == 'proposals':
                        pk_column = 'proposal_id'
                    elif data_table == 'emails':
                        pk_column = 'email_id'
                    elif data_table == 'invoices':
                        pk_column = 'invoice_id'

                    cursor.execute(f"""
                        UPDATE {data_table}
                        SET {field_name} = ?
                        WHERE {pk_column} = ?
                    """, (new_value, record_id))

                    results['applied'].append({
                        'table': data_table,
                        'record_id': record_id,
                        'field': field_name,
                        'new_value': new_value
                    })

                except Exception as e:
                    results['errors'].append({
                        'suggestion_id': suggestion_id,
                        'error': str(e)
                    })

            # Update suggestion status
            cursor.execute("""
                UPDATE ai_suggestions_queue
                SET status = 'approved', reviewed_at = ?, applied_at = ?
                WHERE suggestion_id = ?
            """, (now, now if apply_now else None, suggestion_id))

            results['updated'] += 1

            # Log to training_data for future learning
            cursor.execute("""
                INSERT INTO training_data
                (task_type, input_data, output_data, model_used, confidence, human_verified, feedback, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'suggestion_approval',
                json.dumps({
                    'table': suggestion['data_table'],
                    'field': suggestion['field_name'],
                    'current': suggestion['current_value']
                }),
                json.dumps({'approved_value': suggestion['suggested_value']}),
                'intelligence_service_v2',
                suggestion['confidence'],
                1,
                reason or 'User approved suggestion',
                now
            ))

        elif decision == 'rejected':
            cursor.execute("""
                UPDATE ai_suggestions_queue
                SET status = 'rejected', reviewed_at = ?
                WHERE suggestion_id = ?
            """, (now, suggestion_id))
            results['updated'] += 1

            # Log rejection for learning
            cursor.execute("""
                INSERT INTO training_data
                (task_type, input_data, output_data, model_used, confidence, human_verified, feedback, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'suggestion_rejection',
                json.dumps({
                    'table': suggestion['data_table'],
                    'field': suggestion['field_name'],
                    'current': suggestion['current_value'],
                    'suggested': suggestion['suggested_value']
                }),
                json.dumps({'rejected': True}),
                'intelligence_service_v2',
                suggestion['confidence'],
                1,
                reason or 'User rejected suggestion',
                now
            ))

        conn.commit()
        conn.close()

        return results

    def get_decisions(self, limit: int = 50) -> Dict[str, Any]:
        """Get recent suggestion decisions for audit trail"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get recently reviewed suggestions
        cursor.execute("""
            SELECT
                suggestion_id,
                data_table,
                record_id,
                field_name,
                current_value,
                suggested_value,
                status,
                reviewed_at,
                applied_at
            FROM ai_suggestions_queue
            WHERE status IN ('approved', 'rejected')
            ORDER BY reviewed_at DESC
            LIMIT ?
        """, (limit,))

        decisions = []
        for row in cursor.fetchall():
            decisions.append({
                'suggestion_id': row['suggestion_id'],
                'data_table': row['data_table'],
                'record_id': row['record_id'],
                'field_name': row['field_name'],
                'current_value': row['current_value'],
                'suggested_value': row['suggested_value'],
                'decision': row['status'],
                'reviewed_at': row['reviewed_at'],
                'applied': row['applied_at'] is not None
            })

        conn.close()

        return {
            'decisions': decisions,
            'count': len(decisions)
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get overall suggestion statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Count by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM ai_suggestions_queue
            GROUP BY status
        """)

        status_counts = {}
        for row in cursor.fetchall():
            status_counts[row['status']] = row['count']

        # Count by table
        cursor.execute("""
            SELECT data_table, COUNT(*) as count
            FROM ai_suggestions_queue
            WHERE status = 'pending'
            GROUP BY data_table
        """)

        table_counts = {}
        for row in cursor.fetchall():
            table_counts[row['data_table']] = row['count']

        # Average confidence
        cursor.execute("""
            SELECT AVG(confidence) as avg_confidence
            FROM ai_suggestions_queue
            WHERE status = 'pending'
        """)
        avg_conf = cursor.fetchone()['avg_confidence'] or 0

        conn.close()

        return {
            'by_status': status_counts,
            'pending_by_table': table_counts,
            'average_confidence': round(avg_conf, 2),
            'total_pending': status_counts.get('pending', 0),
            'total_approved': status_counts.get('approved', 0),
            'total_rejected': status_counts.get('rejected', 0)
        }

    def export_training_data(self, format: str = 'ndjson', limit: int = 1000) -> str:
        """Export training data for LLM fine-tuning"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM training_data
            WHERE human_verified = 1
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

        if format == 'ndjson':
            lines = []
            for row in cursor.fetchall():
                try:
                    line = json.dumps({
                        'task_type': row['task_type'],
                        'input': json.loads(row['input_data']) if row['input_data'] else {},
                        'output': json.loads(row['output_data']) if row['output_data'] else {},
                        'confidence': row['confidence'],
                        'feedback': row['feedback'],
                        'created_at': row['created_at']
                    })
                    lines.append(line)
                except:
                    continue

            conn.close()
            return '\n'.join(lines)

        conn.close()
        return ''


# Singleton instance
intelligence_service = IntelligenceService()
