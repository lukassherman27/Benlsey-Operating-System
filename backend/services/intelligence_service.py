#!/usr/bin/env python3
"""
Intelligence Service - AI Suggestion Management
Handles AI-generated database suggestions, decisions, and pattern learning
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


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
        bucket: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get suggestions filtered by status and bucket

        Args:
            status: pending, approved, rejected, snoozed, auto_applied
            bucket: urgent, needs_attention, fyi
            limit: max results to return
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT *
            FROM ai_suggestions_queue
            WHERE status = ?
        """
        params = [status]

        if bucket:
            query += " AND bucket = ?"
            params.append(bucket)

        query += " ORDER BY severity DESC, confidence DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        suggestions = []

        for row in cursor.fetchall():
            suggestion = {
                'id': row['id'],
                'project_code': row['project_code'],
                'suggestion_type': row['suggestion_type'],
                'proposed_fix': json.loads(row['proposed_fix']),
                'evidence': json.loads(row['evidence']),
                'confidence': row['confidence'],
                'impact': {
                    'type': row['impact_type'],
                    'value_usd': row['impact_value_usd'],
                    'summary': row['impact_summary'],
                    'severity': row['severity']
                },
                'bucket': row['bucket'],
                'pattern_id': row['pattern_id'],
                'pattern_label': row['pattern_label'],
                'auto_apply_candidate': bool(row['auto_apply_candidate']),
                'status': row['status'],
                'created_at': row['created_at']
            }

            # Get project name (from unified projects table after migration 015)
            cursor.execute("""
                SELECT project_name, is_active_project FROM projects WHERE project_code = ?
                LIMIT 1
            """, (row['project_code'],))
            project = cursor.fetchone()

            if project:
                suggestion['project_name'] = project['project_name']
                suggestion['is_active_project'] = project['is_active_project']

            suggestions.append(suggestion)

        conn.close()

        return {
            'group': bucket or 'all',
            'items': suggestions
        }

    def get_patterns(self) -> Dict[str, Any]:
        """Get all patterns with statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                p.*,
                COUNT(s.id) as active_suggestions,
                SUM(s.impact_value_usd) as total_impact_usd,
                AVG(s.confidence) as avg_confidence
            FROM suggestion_patterns p
            LEFT JOIN ai_suggestions_queue s ON p.pattern_id = s.pattern_id AND s.status = 'pending'
            GROUP BY p.pattern_id
            ORDER BY active_suggestions DESC, p.approval_count DESC
        """)

        patterns = []
        for row in cursor.fetchall():
            # Get sample projects for this pattern
            cursor.execute("""
                SELECT project_code
                FROM ai_suggestions_queue
                WHERE pattern_id = ? AND status = 'pending'
                LIMIT 5
            """, (row['pattern_id'],))
            samples = [r['project_code'] for r in cursor.fetchall()]

            pattern = {
                'pattern_id': row['pattern_id'],
                'label': row['label'],
                'detection_logic': row['detection_logic'],
                'count': row['active_suggestions'],
                'impact_total_usd': row['total_impact_usd'],
                'confidence_avg': row['avg_confidence'],
                'sample_projects': samples,
                'approval_rate': (
                    row['approval_count'] / (row['approval_count'] + row['rejection_count'])
                    if (row['approval_count'] + row['rejection_count']) > 0
                    else 0.0
                ),
                'auto_apply_enabled': bool(row['auto_apply_enabled'])
            }
            patterns.append(pattern)

        conn.close()
        return {'patterns': patterns}

    def apply_decision(
        self,
        suggestion_id: str,
        decision: str,
        reason: Optional[str] = None,
        apply_now: bool = True,
        dry_run: bool = False,
        batch_ids: Optional[List[str]] = None,
        decision_by: str = "user"
    ) -> Dict[str, Any]:
        """
        Apply a decision to a suggestion

        Args:
            suggestion_id: ID of the suggestion
            decision: approved, rejected, snoozed
            reason: optional reason for reject/snooze
            apply_now: whether to apply changes to database
            dry_run: preview changes without applying
            batch_ids: additional suggestions to apply same decision
            decision_by: who made the decision
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Collect all suggestions to process
        suggestion_ids = [suggestion_id]
        if batch_ids:
            suggestion_ids.extend(batch_ids)

        if dry_run:
            # Preview mode - just count what would change
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM ai_suggestions_queue
                WHERE id IN ({})
            """.format(','.join('?' * len(suggestion_ids))), suggestion_ids)

            return {
                'would_update': cursor.fetchone()['count'],
                'preview': [],
                'conflicts': [],
                'applied': False
            }

        results = {
            'updated': 0,
            'applied': [],
            'decisions_logged': 0
        }

        for sid in suggestion_ids:
            # Get suggestion
            cursor.execute("SELECT * FROM ai_suggestions_queue WHERE id = ?", (sid,))
            suggestion = cursor.fetchone()

            if not suggestion:
                continue

            # Log decision
            decision_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO suggestion_decisions
                (decision_id, suggestion_id, project_code, suggestion_type,
                 proposed_payload, evidence_snapshot, confidence, decision,
                 decision_by, decision_reason, applied, decided_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                decision_id,
                sid,
                suggestion['project_code'],
                suggestion['suggestion_type'],
                suggestion['proposed_fix'],
                suggestion['evidence'],
                suggestion['confidence'],
                decision,
                decision_by,
                reason,
                1 if (apply_now and decision == 'approved') else 0,
                datetime.now().isoformat()
            ))

            # Apply changes if approved and apply_now=True
            if decision == 'approved' and apply_now:
                proposed_fix = json.loads(suggestion['proposed_fix'])

                # Update projects table (unified after migration 015)
                update_fields = []
                update_values = []

                for field, value in proposed_fix.items():
                    update_fields.append(f"{field} = ?")
                    update_values.append(value)

                if update_fields:
                    update_values.append(suggestion['project_code'])

                    try:
                        cursor.execute(f"""
                            UPDATE projects
                            SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                            WHERE project_code = ?
                        """, update_values)

                        results['applied'].append({
                            'project_code': suggestion['project_code'],
                            'changes': proposed_fix
                        })
                    except Exception as e:
                        results['errors'].append({
                            'project_code': suggestion['project_code'],
                            'error': str(e)
                        })

                # Update suggestion status
                cursor.execute("""
                    UPDATE ai_suggestions_queue
                    SET status = 'approved', updated_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), sid))

                # Also log to training_data
                cursor.execute("""
                    INSERT INTO training_data
                    (task_type, input_data, output_data, model_used, confidence, human_verified, feedback, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    'database_intelligence',
                    suggestion['evidence'],
                    suggestion['proposed_fix'],
                    'pattern_detector_v1',
                    suggestion['confidence'],
                    1,
                    reason or 'User approved suggestion',
                    datetime.now().isoformat()
                ))

                results['updated'] += 1

            elif decision == 'rejected':
                cursor.execute("""
                    UPDATE ai_suggestions_queue
                    SET status = 'rejected', updated_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), sid))
                results['updated'] += 1

            elif decision == 'snoozed':
                # Snooze for 7 days by default
                snooze_until = datetime.now() + timedelta(days=7)
                cursor.execute("""
                    UPDATE ai_suggestions_queue
                    SET status = 'snoozed', snooze_until = ?, updated_at = ?
                    WHERE id = ?
                """, (snooze_until.isoformat(), datetime.now().isoformat(), sid))
                results['updated'] += 1

            results['decisions_logged'] += 1

            # Update pattern statistics
            if decision in ['approved', 'rejected']:
                field = 'approval_count' if decision == 'approved' else 'rejection_count'
                cursor.execute(f"""
                    UPDATE suggestion_patterns
                    SET {field} = {field} + 1,
                        updated_at = ?
                    WHERE pattern_id = ?
                """, (datetime.now().isoformat(), suggestion['pattern_id']))

        conn.commit()
        conn.close()

        return results

    def get_decisions(self, limit: int = 50) -> Dict[str, Any]:
        """Get recent decisions for audit trail"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM suggestion_decisions
            ORDER BY decided_at DESC
            LIMIT ?
        """, (limit,))

        decisions = []
        for row in cursor.fetchall():
            decisions.append({
                'decision_id': row['decision_id'],
                'suggestion_id': row['suggestion_id'],
                'project_code': row['project_code'],
                'suggestion_type': row['suggestion_type'],
                'decision': row['decision'],
                'decided_at': row['decided_at'],
                'applied': bool(row['applied']),
                'decision_by': row['decision_by'],
                'decision_reason': row['decision_reason']
            })

        conn.close()

        return {
            'decisions': decisions,
            'export_ndjson_url': '/api/intel/training-data?format=ndjson'
        }

    def export_training_data(self, format: str = 'ndjson', limit: int = 1000) -> str:
        """Export training data for LLM fine-tuning"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM suggestion_decisions
            WHERE applied = 1
            ORDER BY decided_at DESC
            LIMIT ?
        """, (limit,))

        if format == 'ndjson':
            lines = []
            for row in cursor.fetchall():
                line = json.dumps({
                    'task_type': row['suggestion_type'],
                    'input': json.loads(row['evidence_snapshot']),
                    'output': json.loads(row['proposed_payload']),
                    'confidence': row['confidence'],
                    'human_verified': 1,
                    'decision': row['decision'],
                    'decided_at': row['decided_at']
                })
                lines.append(line)

            conn.close()
            return '\n'.join(lines)

        conn.close()
        return ''


# Import for datetime timedelta
from datetime import timedelta
