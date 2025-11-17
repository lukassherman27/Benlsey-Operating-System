"""
Service layer for project files metadata
Handles file tracking, OneDrive integration, and version management
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date
import sqlite3


class FileService:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self):
        """Create database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_files_by_proposal(self, proposal_id: int, latest_only: bool = False) -> List[Dict[str, Any]]:
        """Get all files for a specific proposal"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                f.*,
                m.milestone_name,
                m.milestone_type
            FROM project_files f
            LEFT JOIN project_milestones m ON f.related_milestone_id = m.milestone_id
            WHERE f.proposal_id = ?
        """

        if latest_only:
            query += " AND f.is_latest_version = 1"

        query += " ORDER BY f.uploaded_date DESC"

        cursor.execute(query, (proposal_id,))

        files = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return files

    def get_file_by_id(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific file by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM project_files
            WHERE file_id = ?
        """, (file_id,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_files_by_type(self, proposal_id: int, file_type: str) -> List[Dict[str, Any]]:
        """Get files filtered by type (drawing, presentation, contract, etc.)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM project_files
            WHERE proposal_id = ? AND file_type = ?
            ORDER BY uploaded_date DESC
        """, (proposal_id, file_type))

        files = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return files

    def get_files_by_category(self, proposal_id: int, file_category: str) -> List[Dict[str, Any]]:
        """Get files filtered by category (concept, schematic, detail, final)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM project_files
            WHERE proposal_id = ? AND file_category = ?
            ORDER BY uploaded_date DESC
        """, (proposal_id, file_category))

        files = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return files

    def create_file(self, data: Dict[str, Any]) -> int:
        """Create a new file record"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO project_files (
                proposal_id,
                filename,
                file_type,
                file_category,
                file_path,
                onedrive_path,
                onedrive_url,
                file_size,
                version,
                uploaded_date,
                uploaded_by,
                description,
                tags,
                is_latest_version,
                related_milestone_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('proposal_id'),
            data.get('filename'),
            data.get('file_type'),
            data.get('file_category'),
            data.get('file_path'),
            data.get('onedrive_path'),
            data.get('onedrive_url'),
            data.get('file_size'),
            data.get('version', 'v1.0'),
            data.get('uploaded_date') or date.today().isoformat(),
            data.get('uploaded_by'),
            data.get('description'),
            data.get('tags'),
            data.get('is_latest_version', 1),
            data.get('related_milestone_id')
        ))

        file_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return file_id

    def update_file(self, file_id: int, data: Dict[str, Any]) -> bool:
        """Update an existing file record"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build dynamic update query
        update_fields = []
        values = []

        allowed_fields = [
            'filename', 'file_type', 'file_category', 'file_path',
            'onedrive_path', 'onedrive_url', 'file_size', 'version',
            'uploaded_date', 'uploaded_by', 'description', 'tags',
            'is_latest_version', 'related_milestone_id'
        ]

        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                values.append(data[field])

        if not update_fields:
            conn.close()
            return False

        values.append(file_id)
        query = f"UPDATE project_files SET {', '.join(update_fields)} WHERE file_id = ?"

        cursor.execute(query, values)
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def delete_file(self, file_id: int) -> bool:
        """Delete a file record"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM project_files WHERE file_id = ?", (file_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    def mark_as_latest_version(self, file_id: int) -> bool:
        """
        Mark a file as the latest version
        Automatically sets all other versions of same filename to is_latest_version=0
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get file details
        cursor.execute("""
            SELECT proposal_id, filename FROM project_files
            WHERE file_id = ?
        """, (file_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return False

        proposal_id = row['proposal_id']
        filename = row['filename']

        # Mark all versions as not latest
        cursor.execute("""
            UPDATE project_files
            SET is_latest_version = 0
            WHERE proposal_id = ? AND filename = ?
        """, (proposal_id, filename))

        # Mark this one as latest
        cursor.execute("""
            UPDATE project_files
            SET is_latest_version = 1
            WHERE file_id = ?
        """, (file_id,))

        conn.commit()
        conn.close()

        return True

    def get_file_versions(self, proposal_id: int, filename: str) -> List[Dict[str, Any]]:
        """Get all versions of a specific file"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM project_files
            WHERE proposal_id = ? AND filename = ?
            ORDER BY uploaded_date DESC
        """, (proposal_id, filename))

        files = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return files

    def get_workspace_summary(self, proposal_id: int) -> Dict[str, Any]:
        """
        Generate workspace summary for a proposal
        Returns file counts by type, category, and recent uploads
        """
        files = self.get_files_by_proposal(proposal_id, latest_only=True)

        summary = {
            'proposal_id': proposal_id,
            'total_files': len(files),
            'by_type': {},
            'by_category': {},
            'latest_files': [],
            'onedrive_ready': 0
        }

        for file in files:
            # Type breakdown
            file_type = file['file_type'] or 'unknown'
            summary['by_type'][file_type] = summary['by_type'].get(file_type, 0) + 1

            # Category breakdown
            file_category = file['file_category'] or 'uncategorized'
            summary['by_category'][file_category] = summary['by_category'].get(file_category, 0) + 1

            # OneDrive ready
            if file['onedrive_url']:
                summary['onedrive_ready'] += 1

        # Get 5 most recent files
        summary['latest_files'] = files[:5]

        return summary

    def search_files(self, proposal_id: int, search_term: str) -> List[Dict[str, Any]]:
        """
        Search files by filename, description, or tags
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        search_pattern = f"%{search_term}%"

        cursor.execute("""
            SELECT * FROM project_files
            WHERE proposal_id = ?
              AND (
                  filename LIKE ?
                  OR description LIKE ?
                  OR tags LIKE ?
              )
            ORDER BY uploaded_date DESC
        """, (proposal_id, search_pattern, search_pattern, search_pattern))

        files = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return files

    def get_files_by_milestone(self, milestone_id: int) -> List[Dict[str, Any]]:
        """Get all files related to a specific milestone"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM project_files
            WHERE related_milestone_id = ?
            ORDER BY uploaded_date DESC
        """, (milestone_id,))

        files = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return files

    def bulk_update_onedrive_paths(self, updates: List[Dict[str, Any]]) -> int:
        """
        Bulk update OneDrive paths for multiple files
        Each update dict should have: file_id, onedrive_path, onedrive_url
        Returns count of files updated
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        count = 0
        for update in updates:
            cursor.execute("""
                UPDATE project_files
                SET onedrive_path = ?,
                    onedrive_url = ?
                WHERE file_id = ?
            """, (
                update.get('onedrive_path'),
                update.get('onedrive_url'),
                update.get('file_id')
            ))
            if cursor.rowcount > 0:
                count += 1

        conn.commit()
        conn.close()

        return count
