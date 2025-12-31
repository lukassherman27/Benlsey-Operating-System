"""
Files Router - File management and workspace

Endpoints:
    GET /api/files/by-proposal/{proposal_id} - Get proposal files
    GET /api/files/by-proposal/{proposal_id}/workspace - Get workspace summary
    GET /api/files/by-proposal/{proposal_id}/by-type/{file_type} - Get files by type
    GET /api/files/by-proposal/{proposal_id}/by-category/{category} - Get files by category
    GET /api/files/by-proposal/{proposal_id}/versions/{filename} - Get file versions
    GET /api/files/by-proposal/{proposal_id}/search - Search files
    GET /api/files/by-milestone/{milestone_id} - Get milestone files
    GET /api/files/{file_id} - Get file by ID
    POST /api/files - Create file record
    PATCH /api/files/{file_id} - Update file
    PATCH /api/files/{file_id}/mark-latest - Mark as latest version
    DELETE /api/files/{file_id} - Delete file
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, Field

from api.services import file_service
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api", tags=["files"])


# ============================================================================
# REQUEST MODELS
# ============================================================================

class CreateFileRequest(BaseModel):
    """Request to create a file record"""
    proposal_id: int
    filename: str
    file_path: Optional[str] = None
    onedrive_path: Optional[str] = None
    file_type: Optional[str] = None
    file_category: Optional[str] = None
    version: int = 1
    is_latest_version: bool = True
    notes: Optional[str] = None


class UpdateFileRequest(BaseModel):
    """Request to update file"""
    filename: Optional[str] = None
    file_path: Optional[str] = None
    onedrive_path: Optional[str] = None
    file_type: Optional[str] = None
    file_category: Optional[str] = None
    notes: Optional[str] = None


class BulkUpdateOnedriveRequest(BaseModel):
    """Request to bulk update OneDrive paths"""
    updates: List[dict] = Field(..., description="List of {file_id, onedrive_path}")


# ============================================================================
# PROPOSAL FILES
# ============================================================================

@router.get("/files/by-proposal/{proposal_id}")
async def get_files_by_proposal(
    proposal_id: int,
    latest_only: bool = Query(False, description="Only return latest versions")
):
    """Get all files for a proposal"""
    try:
        files = file_service.get_files_by_proposal(proposal_id, latest_only=latest_only)
        response = list_response(files, len(files))
        response["proposal_id"] = proposal_id  # Backward compat
        response["files"] = files  # Backward compat
        response["count"] = len(files)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/files/by-proposal/{proposal_id}/workspace")
async def get_workspace_summary(proposal_id: int):
    """Get workspace summary for a proposal"""
    try:
        summary = file_service.get_workspace_summary(proposal_id)
        return item_response(summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/files/by-proposal/{proposal_id}/by-type/{file_type}")
async def get_files_by_type(proposal_id: int, file_type: str):
    """Get files of a specific type for a proposal"""
    try:
        files = file_service.get_files_by_type(proposal_id, file_type)
        response = list_response(files, len(files))
        response["proposal_id"] = proposal_id  # Backward compat
        response["file_type"] = file_type  # Backward compat
        response["files"] = files  # Backward compat
        response["count"] = len(files)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/files/by-proposal/{proposal_id}/by-category/{category}")
async def get_files_by_category(proposal_id: int, category: str):
    """Get files of a specific category for a proposal"""
    try:
        files = file_service.get_files_by_category(proposal_id, category)
        response = list_response(files, len(files))
        response["proposal_id"] = proposal_id  # Backward compat
        response["category"] = category  # Backward compat
        response["files"] = files  # Backward compat
        response["count"] = len(files)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/files/by-proposal/{proposal_id}/versions/{filename}")
async def get_file_versions(proposal_id: int, filename: str):
    """Get all versions of a file"""
    try:
        versions = file_service.get_file_versions(proposal_id, filename)
        response = list_response(versions, len(versions))
        response["proposal_id"] = proposal_id  # Backward compat
        response["filename"] = filename  # Backward compat
        response["versions"] = versions  # Backward compat
        response["count"] = len(versions)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/files/by-proposal/{proposal_id}/search")
async def search_files(
    proposal_id: int,
    q: str = Query(..., description="Search term")
):
    """Search files in a proposal"""
    try:
        files = file_service.search_files(proposal_id, q)
        response = list_response(files, len(files))
        response["proposal_id"] = proposal_id  # Backward compat
        response["query"] = q  # Backward compat
        response["files"] = files  # Backward compat
        response["count"] = len(files)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/files/by-milestone/{milestone_id}")
async def get_files_by_milestone(milestone_id: int):
    """Get files associated with a milestone"""
    try:
        files = file_service.get_files_by_milestone(milestone_id)
        response = list_response(files, len(files))
        response["milestone_id"] = milestone_id  # Backward compat
        response["files"] = files  # Backward compat
        response["count"] = len(files)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# CRUD
# ============================================================================

@router.get("/files/{file_id}")
async def get_file(file_id: int):
    """Get a specific file"""
    try:
        file = file_service.get_file_by_id(file_id)
        if not file:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")
        return item_response(file)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("/files")
async def create_file(request: CreateFileRequest):
    """Create a new file record"""
    try:
        file_id = file_service.create_file(request.dict())
        return action_response(True, data={"file_id": file_id}, message="File created")
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.patch("/files/{file_id}")
async def update_file(file_id: int, request: UpdateFileRequest):
    """Update a file record"""
    try:
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        success = file_service.update_file(file_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")
        return action_response(True, message="File updated")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.patch("/files/{file_id}/mark-latest")
async def mark_as_latest(file_id: int):
    """Mark a file as the latest version"""
    try:
        success = file_service.mark_as_latest_version(file_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")
        return action_response(True, message="Marked as latest version")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("/files/{file_id}")
async def delete_file(file_id: int):
    """Delete a file record"""
    try:
        success = file_service.delete_file(file_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")
        return action_response(True, message="File deleted")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("/files/bulk-update-onedrive")
async def bulk_update_onedrive_paths(request: BulkUpdateOnedriveRequest):
    """Bulk update OneDrive paths"""
    try:
        count = file_service.bulk_update_onedrive_paths(request.updates)
        return action_response(True, data={"updated": count}, message=f"Updated {count} files")
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# ONEDRIVE UPLOAD/DOWNLOAD (Issue #243)
# ============================================================================

from fastapi import UploadFile, File, Form
from api.services import onedrive_service


@router.post("/files/upload")
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
        content = await file.read()
        result = await onedrive_service.upload_file(
            file_content=content,
            filename=file.filename,
            project_code=project_code,
            category=category,
            uploaded_by=uploaded_by,
        )
        return {"success": True, "message": "File uploaded successfully", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/files/download/{file_id}")
async def get_download_url(file_id: int):
    """Get download URL for a file."""
    try:
        result = await onedrive_service.get_download_url(file_id)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail="An internal error occurred")
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/files/by-project/{project_code}")
async def get_files_by_project(project_code: str, category: Optional[str] = None):
    """Get all uploaded files for a project."""
    try:
        files = onedrive_service.get_files_by_project(project_code, category)
        response = list_response(files, len(files))
        response["project_code"] = project_code
        response["files"] = files
        response["count"] = len(files)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("/files/uploaded/{file_id}")
async def delete_uploaded_file(file_id: int):
    """Delete an uploaded file from storage and database."""
    try:
        success = onedrive_service.delete_file(file_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"File {file_id} not found")
        return action_response(True, message="File deleted")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/files/config")
async def get_onedrive_config():
    """Check OneDrive configuration status."""
    return {
        "success": True,
        "onedrive_configured": onedrive_service.is_configured(),
        "storage_mode": "onedrive" if onedrive_service.is_configured() else "local",
        "categories": onedrive_service.FOLDER_CATEGORIES,
    }
