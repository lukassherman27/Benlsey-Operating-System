"""
Upload Router - File upload endpoints for OneDrive integration
Issue: #243

Endpoints:
    POST /api/upload - Upload file to OneDrive (or local fallback)
    GET /api/upload/{file_id}/download - Get download URL
    GET /api/upload/by-project/{project_code} - Get project files
    DELETE /api/upload/{file_id} - Delete file
    GET /api/upload/config - Check OneDrive configuration
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional

from api.helpers import list_response, action_response

router = APIRouter(prefix="/api/upload", tags=["upload"])

# Import onedrive service inline to avoid circular imports
_onedrive_service = None

def get_service():
    global _onedrive_service
    if _onedrive_service is None:
        from api.dependencies import DB_PATH
        from services.onedrive_service import get_onedrive_service
        _onedrive_service = get_onedrive_service(DB_PATH)
    return _onedrive_service


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    project_code: str = Form(...),
    category: str = Form(...),
    uploaded_by: str = Form(default="system"),
):
    """
    Upload a file to OneDrive (or local storage as fallback).

    Categories: Daily Work, Deliverables, Client Submissions, Proposals, Contracts, Drawings, Reference
    """
    try:
        service = get_service()
        content = await file.read()
        result = await service.upload_file(
            file_content=content,
            filename=file.filename,
            project_code=project_code,
            category=category,
            uploaded_by=uploaded_by,
        )
        return {"success": True, "message": "File uploaded successfully", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/{file_id}/download")
async def get_download_url(file_id: int):
    """Get download URL for a file."""
    try:
        service = get_service()
        result = await service.get_download_url(file_id)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get download URL: {str(e)}")


@router.get("/by-project/{project_code}")
async def get_files_by_project(project_code: str, category: Optional[str] = None):
    """Get all uploaded files for a project."""
    try:
        service = get_service()
        files = service.get_files_by_project(project_code, category)
        response = list_response(files, len(files))
        response["project_code"] = project_code
        response["files"] = files
        response["count"] = len(files)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{file_id}")
async def delete_uploaded_file(file_id: int):
    """Delete an uploaded file from storage and database."""
    try:
        service = get_service()
        success = service.delete_file(file_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")
        return action_response(True, message="File deleted")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_config():
    """Check OneDrive configuration status."""
    service = get_service()
    return {
        "success": True,
        "onedrive_configured": service.is_configured(),
        "storage_mode": "onedrive" if service.is_configured() else "local",
        "categories": service.FOLDER_CATEGORIES,
    }
