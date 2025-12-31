"""
Documents Router - Document management and search

Endpoints:
    GET /api/documents - List all documents
    GET /api/documents/search - Search documents
    GET /api/documents/stats - Document statistics
    GET /api/documents/types - Document types
    GET /api/documents/recent - Recent documents
    GET /api/documents/{document_id} - Get document by ID
    GET /api/documents/by-project/{project_code} - Get project documents
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from api.services import document_service
from api.helpers import list_response, item_response

router = APIRouter(prefix="/api", tags=["documents"])


# ============================================================================
# LIST ENDPOINTS
# ============================================================================

@router.get("/documents")
async def get_all_documents(
    project_code: Optional[str] = Query(None, description="Filter by project code"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    limit: int = Query(100, ge=1, le=500)
):
    """Get all documents with optional filtering"""
    try:
        documents = document_service.get_all_documents(
            project_code=project_code,
            document_type=document_type,
            limit=limit
        )
        return list_response(documents, len(documents))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/documents/search")
async def search_documents(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100)
):
    """Search documents by content or metadata"""
    try:
        results = document_service.search_documents(query=q, limit=limit)
        response = list_response(results, len(results))
        response["results"] = results  # Backward compat
        response["query"] = q  # Backward compat
        response["count"] = len(results)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/documents/stats")
async def get_document_stats():
    """Get document statistics"""
    try:
        stats = document_service.get_document_stats()
        return item_response(stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/documents/types")
async def get_document_types():
    """Get available document types"""
    try:
        types = document_service.get_document_types()
        response = list_response(types, len(types))
        response["types"] = types  # Backward compat
        response["count"] = len(types)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/documents/recent")
async def get_recent_documents(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(20, ge=1, le=100)
):
    """Get recently added/modified documents"""
    try:
        documents = document_service.get_recent_documents(days=days, limit=limit)
        return list_response(documents, len(documents))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/documents/{document_id}")
async def get_document_by_id(document_id: int):
    """Get a specific document by ID"""
    try:
        document = document_service.get_document_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
        return item_response(document)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/documents/by-project/{project_code}")
async def get_documents_by_project(project_code: str):
    """Get all documents for a specific project"""
    try:
        documents = document_service.get_documents_for_proposal(project_code)
        response = list_response(documents, len(documents))
        response["project_code"] = project_code  # Backward compat
        response["documents"] = documents  # Backward compat
        response["count"] = len(documents)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")
