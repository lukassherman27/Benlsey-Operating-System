"""
Service layer for manual overrides management
Handles CRUD operations for Bill's manual instructions
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import sqlite3
import json


class OverrideService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self):
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_override(self, data: Dict[str, Any]) -> int:
        """
        Create a new manual override

        Args:
            data: Dict with keys: proposal_id, project_code, scope, instruction,
                  author, source, urgency, tags

        Returns:
            override_id of created record
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Convert tags list to JSON string if provided
        tags_json = None
        if data.get('tags'):
            tags_json = json.dumps(data['tags'])

        cursor.execute("""
            INSERT INTO manual_overrides (
                proposal_id,
                project_code,
                scope,
                instruction,
                author,
                source,
                urgency,
                status,
                tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('proposal_id'),
            data.get('project_code'),
            data.get('scope', 'general'),
            data.get('instruction'),
            data.get('author', 'bill'),
            data.get('source', 'dashboard_context_modal'),
            data.get('urgency', 'informational'),
            data.get('status', 'active'),
            tags_json
        ))

        override_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return override_id

    def get_overrides(
        self,
        project_code: Optional[str] = None,
        status: Optional[str] = None,
        scope: Optional[str] = None,
        author: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Get filtered list of overrides with pagination

        Returns dict with 'data' and 'pagination' keys
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build WHERE clause
        where_clauses = []
        params = []

        if project_code:
            where_clauses.append("project_code = ?")
            params.append(project_code)

        if status:
            where_clauses.append("status = ?")
            params.append(status)

        if scope:
            where_clauses.append("scope = ?")
            params.append(scope)

        if author:
            where_clauses.append("author = ?")
            params.append(author)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        # Get total count
        cursor.execute(f"SELECT COUNT(*) FROM manual_overrides {where_sql}", params)
        total = cursor.fetchone()[0]

        # Get paginated results
        offset = (page - 1) * per_page
        query_params = params + [per_page, offset]

        cursor.execute(f"""
            SELECT
                override_id,
                proposal_id,
                project_code,
                scope,
                instruction,
                author,
                source,
                urgency,
                status,
                applied_by,
                applied_at,
                tags,
                created_at,
                updated_at
            FROM manual_overrides
            {where_sql}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, query_params)

        overrides = []
        for row in cursor.fetchall():
            override_dict = dict(row)
            # Parse tags JSON if present
            if override_dict.get('tags'):
                try:
                    override_dict['tags'] = json.loads(override_dict['tags'])
                except:
                    override_dict['tags'] = []
            else:
                override_dict['tags'] = []
            overrides.append(override_dict)

        conn.close()

        total_pages = (total + per_page - 1) // per_page

        return {
            "data": overrides,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages
            }
        }

    def get_override_by_id(self, override_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific override by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM manual_overrides
            WHERE override_id = ?
        """, (override_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        override_dict = dict(row)
        if override_dict.get('tags'):
            try:
                override_dict['tags'] = json.loads(override_dict['tags'])
            except:
                override_dict['tags'] = []

        return override_dict

    def update_override(self, override_id: int, data: Dict[str, Any]) -> bool:
        """
        Update an existing override

        Allowed fields: status, applied_by, applied_at, instruction, urgency, tags
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        update_fields = []
        values = []

        allowed_fields = ['status', 'applied_by', 'applied_at', 'instruction', 'urgency', 'scope']

        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                values.append(data[field])

        # Handle tags separately (needs JSON encoding)
        if 'tags' in data:
            update_fields.append("tags = ?")
            values.append(json.dumps(data['tags']))

        if not update_fields:
            conn.close()
            return False

        values.append(override_id)
        query = f"UPDATE manual_overrides SET {', '.join(update_fields)} WHERE override_id = ?"

        cursor.execute(query, values)
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def mark_as_applied(self, override_id: int, applied_by: str) -> bool:
        """Mark an override as applied"""
        return self.update_override(override_id, {
            'status': 'applied',
            'applied_by': applied_by,
            'applied_at': datetime.now().isoformat()
        })

    def archive_override(self, override_id: int) -> bool:
        """Archive an override"""
        return self.update_override(override_id, {'status': 'archived'})

    def delete_override(self, override_id: int) -> bool:
        """Delete an override (soft delete - archives instead)"""
        return self.archive_override(override_id)

    def get_active_overrides_for_proposal(self, project_code: str) -> List[Dict[str, Any]]:
        """Get all active overrides for a specific proposal"""
        result = self.get_overrides(
            project_code=project_code,
            status='active',
            per_page=100
        )
        return result['data']
