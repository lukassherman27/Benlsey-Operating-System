"""
OneDrive Service - Microsoft Graph API integration for file storage

Environment variables required:
    MICROSOFT_CLIENT_ID - Azure AD app client ID
    MICROSOFT_CLIENT_SECRET - Azure AD app client secret
    MICROSOFT_TENANT_ID - Azure AD tenant ID
    ONEDRIVE_ROOT_FOLDER - Root folder in OneDrive (default: "Bensley Projects")

Folder structure:
    OneDrive/Bensley Projects/{project_code}/Daily Work|Deliverables|etc

Issue: #243
"""

import os
import sqlite3
import httpx
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from utils.logger import get_logger

logger = get_logger(__name__)


class OneDriveService:
    """Service for OneDrive file operations via Microsoft Graph API."""

    GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
    FOLDER_CATEGORIES = [
        "Daily Work", "Deliverables", "Client Submissions",
        "Proposals", "Contracts", "Drawings", "Reference",
    ]

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.client_id = os.getenv("MICROSOFT_CLIENT_ID")
        self.client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
        self.tenant_id = os.getenv("MICROSOFT_TENANT_ID")
        self.root_folder = os.getenv("ONEDRIVE_ROOT_FOLDER", "Bensley Projects")
        self._access_token = None
        self._token_expires = None

    def _get_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.tenant_id)

    async def _get_access_token(self) -> str:
        if not self.is_configured():
            raise ValueError("OneDrive not configured")
        if self._access_token and self._token_expires and datetime.now() < self._token_expires:
            return self._access_token

        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "https://graph.microsoft.com/.default",
                "grant_type": "client_credentials",
            })
            response.raise_for_status()
            data = response.json()

        self._access_token = data["access_token"]
        self._token_expires = datetime.now() + timedelta(seconds=data.get("expires_in", 3600) - 300)
        return self._access_token

    def _build_folder_path(self, project_code: str, category: str) -> str:
        if category not in self.FOLDER_CATEGORIES:
            category = "Reference"
        safe_project_code = project_code.replace("/", "-").replace("\\", "-")
        return f"{self.root_folder}/{safe_project_code}/{category}"

    async def upload_file(
        self, file_content: bytes, filename: str, project_code: str,
        category: str, uploaded_by: str = "system"
    ) -> Dict[str, Any]:
        if not self.is_configured():
            return await self._upload_local(file_content, filename, project_code, category, uploaded_by)

        folder_path = self._build_folder_path(project_code, category)
        try:
            token = await self._get_access_token()
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream"}
            upload_url = f"{self.GRAPH_API_BASE}/me/drive/root:/{folder_path}/{filename}:/content"

            async with httpx.AsyncClient() as client:
                response = await client.put(upload_url, headers=headers, content=file_content)
                response.raise_for_status()
                file_info = response.json()

            onedrive_path = f"{folder_path}/{filename}"
            file_id = self._store_file_metadata(
                filename=filename, project_code=project_code, category=category,
                onedrive_path=onedrive_path, onedrive_id=file_info.get("id"),
                file_size=len(file_content), uploaded_by=uploaded_by,
                download_url=file_info.get("@microsoft.graph.downloadUrl"),
            )
            return {
                "file_id": file_id, "filename": filename, "onedrive_path": onedrive_path,
                "onedrive_id": file_info.get("id"), "size": len(file_content),
            }
        except Exception as e:
            logger.error(f"OneDrive upload failed: {e}")
            return await self._upload_local(file_content, filename, project_code, category, uploaded_by)

    async def _upload_local(self, file_content: bytes, filename: str, project_code: str,
                            category: str, uploaded_by: str) -> Dict[str, Any]:
        storage_dir = Path("storage/files") / project_code.replace(" ", "_") / category.replace(" ", "_")
        storage_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        local_path = storage_dir / f"{timestamp}_{filename}"

        with open(local_path, "wb") as f:
            f.write(file_content)

        file_id = self._store_file_metadata(
            filename=filename, project_code=project_code, category=category,
            local_path=str(local_path), file_size=len(file_content), uploaded_by=uploaded_by,
        )
        return {"file_id": file_id, "filename": filename, "local_path": str(local_path), "size": len(file_content), "storage": "local"}

    def _store_file_metadata(self, filename: str, project_code: str, category: str,
                             onedrive_path: str = None, onedrive_id: str = None,
                             local_path: str = None, file_size: int = 0,
                             uploaded_by: str = "system", download_url: str = None) -> int:
        conn = self._get_db()
        cursor = conn.cursor()
        ext = Path(filename).suffix.lower().strip(".")
        file_type = self._get_file_type(ext)

        cursor.execute("""
            INSERT INTO uploaded_files (filename, project_code, category, file_type,
                onedrive_path, onedrive_id, local_path, file_size, uploaded_by, download_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (filename, project_code, category, file_type, onedrive_path, onedrive_id, local_path, file_size, uploaded_by, download_url))
        file_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return file_id

    def _get_file_type(self, ext: str) -> str:
        type_map = {"pdf": "document", "doc": "document", "docx": "document", "xls": "spreadsheet",
                    "xlsx": "spreadsheet", "dwg": "drawing", "dxf": "drawing", "jpg": "image",
                    "jpeg": "image", "png": "image", "ppt": "presentation", "pptx": "presentation"}
        return type_map.get(ext, "other")

    async def get_download_url(self, file_id: int) -> Dict[str, Any]:
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM uploaded_files WHERE file_id = ?", (file_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise ValueError(f"File {file_id} not found")

        file_data = dict(row)
        if file_data.get("local_path"):
            return {"file_id": file_id, "filename": file_data["filename"], "storage": "local", "local_path": file_data["local_path"]}

        if file_data.get("onedrive_id") and self.is_configured():
            token = await self._get_access_token()
            async with httpx.AsyncClient() as client:
                url = f"{self.GRAPH_API_BASE}/me/drive/items/{file_data['onedrive_id']}"
                response = await client.get(url, headers={"Authorization": f"Bearer {token}"})
                if response.status_code == 200:
                    item = response.json()
                    return {"file_id": file_id, "filename": file_data["filename"], "storage": "onedrive",
                            "download_url": item.get("@microsoft.graph.downloadUrl")}
        return file_data

    def get_files_by_project(self, project_code: str, category: str = None) -> List[Dict]:
        conn = self._get_db()
        cursor = conn.cursor()
        if category:
            cursor.execute("SELECT * FROM uploaded_files WHERE project_code = ? AND category = ? ORDER BY created_at DESC", (project_code, category))
        else:
            cursor.execute("SELECT * FROM uploaded_files WHERE project_code = ? ORDER BY category, created_at DESC", (project_code,))
        files = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return files

    def delete_file(self, file_id: int) -> bool:
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM uploaded_files WHERE file_id = ?", (file_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False

        file_data = dict(row)
        if file_data.get("local_path"):
            local_path = Path(file_data["local_path"])
            if local_path.exists():
                local_path.unlink()

        cursor.execute("DELETE FROM uploaded_files WHERE file_id = ?", (file_id,))
        conn.commit()
        conn.close()
        return True


_onedrive_service = None

def get_onedrive_service(db_path: str) -> OneDriveService:
    global _onedrive_service
    if _onedrive_service is None:
        _onedrive_service = OneDriveService(db_path)
    return _onedrive_service
