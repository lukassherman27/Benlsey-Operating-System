#!/usr/bin/env python3
"""
Bensley Intelligence Platform - FastAPI Backend (v2)

Modernized API using service layer for clean data access.

Start with: uvicorn backend.api.main_v2:app --reload --port 8000
Access docs at: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.services.proposal_service import ProposalService
from backend.services.email_service import EmailService
from backend.services.document_service import DocumentService
from backend.services.query_service import QueryService

# Initialize FastAPI app
app = FastAPI(
    title="Bensley Intelligence API",
    description="AI-powered operations platform for Bensley Design Studios",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",  # Vite default
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services (lazy loaded)
_proposal_service = None
_email_service = None
_document_service = None
_query_service = None

def get_proposal_service():
    global _proposal_service
    if _proposal_service is None:
        _proposal_service = ProposalService()
    return _proposal_service

def get_email_service():
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service

def get_document_service():
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service

def get_query_service():
    global _query_service
    if _query_service is None:
        _query_service = QueryService()
    return _query_service


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class QueryRequest(BaseModel):
    question: str

class ProposalUpdate(BaseModel):
    status: Optional[str] = None

class EmailCategoryUpdate(BaseModel):
    category: str
    subcategory: Optional[str] = None
    feedback: Optional[str] = None


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Bensley Intelligence Platform API v2",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "proposals": "/api/proposals",
            "emails": "/api/emails",
            "documents": "/api/documents",
            "query": "/api/query",
            "analytics": "/api/analytics/dashboard"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        proposal_svc = get_proposal_service()
        stats = proposal_svc.get_dashboard_stats()

        return {
            "status": "healthy",
            "database": "connected",
            "services": "operational",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# ============================================================================
# PROPOSAL ENDPOINTS
# ============================================================================

@app.get("/api/proposals")
async def get_proposals(
    status: Optional[str] = Query(None, description="Filter by status"),
    is_active: Optional[bool] = Query(None, description="Filter active projects"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    sort_by: str = Query("health_score", description="Sort field"),
    sort_order: str = Query("ASC", regex="^(ASC|DESC)$", description="Sort order")
):
    """
    Get all proposals with filtering, pagination, and sorting

    **Filters:**
    - status: Filter by proposal status
    - is_active: Filter active projects only

    **Pagination:**
    - page: Page number (default: 1)
    - per_page: Results per page (default: 20, max: 100)

    **Sorting:**
    - sort_by: Column to sort by (default: health_score)
    - sort_order: ASC or DESC (default: ASC)
    """
    try:
        proposal_svc = get_proposal_service()
        result = proposal_svc.get_all_proposals(
            status=status,
            is_active_project=is_active,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/proposals/stats")
async def get_proposal_stats():
    """Get proposal dashboard statistics"""
    try:
        proposal_svc = get_proposal_service()
        return proposal_svc.get_dashboard_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/proposals/unhealthy")
async def get_unhealthy_proposals(
    threshold: float = Query(50.0, ge=0, le=100, description="Health score threshold")
):
    """Get proposals with health score below threshold"""
    try:
        proposal_svc = get_proposal_service()
        return proposal_svc.get_unhealthy_proposals(threshold)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/proposals/{project_code}")
async def get_proposal(project_code: str):
    """Get proposal by project code"""
    try:
        proposal_svc = get_proposal_service()
        proposal = proposal_svc.get_proposal_by_code(project_code)

        if not proposal:
            raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")

        return proposal
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/proposals/{project_code}/timeline")
async def get_proposal_timeline(project_code: str):
    """Get complete timeline for a proposal (emails + documents)"""
    try:
        proposal_svc = get_proposal_service()
        timeline = proposal_svc.get_proposal_timeline(project_code)

        if not timeline:
            raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")

        return timeline
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/proposals/{project_code}/health")
async def get_proposal_health(project_code: str):
    """Get health metrics and recommendations for a proposal"""
    try:
        proposal_svc = get_proposal_service()
        health = proposal_svc.get_proposal_health(project_code)

        if not health:
            raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")

        return health
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/proposals/search")
async def search_proposals(q: str = Query(..., min_length=1, description="Search query")):
    """Search proposals by name or code"""
    try:
        proposal_svc = get_proposal_service()
        return proposal_svc.search_proposals(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/proposals/{project_code}")
async def update_proposal(project_code: str, update: ProposalUpdate):
    """Update proposal (currently supports status only)"""
    try:
        proposal_svc = get_proposal_service()

        if update.status:
            success = proposal_svc.update_proposal_status(project_code, update.status)
            if not success:
                raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")

        # Return updated proposal
        return proposal_svc.get_proposal_by_code(project_code)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EMAIL ENDPOINTS
# ============================================================================

@app.get("/api/emails")
async def get_emails(
    q: Optional[str] = Query(None, description="Search by subject or sender"),
    category: Optional[str] = Query(None, description="Filter by category"),
    proposal_id: Optional[int] = Query(None, description="Filter by proposal ID"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("date", description="Sort field (date, sender_email, subject)"),
    sort_order: str = Query("DESC", regex="^(ASC|DESC)$", description="Sort order")
):
    """
    Get all emails with search, filtering, pagination, and sorting

    **Search:**
    - q: Search in subject and sender fields

    **Filters:**
    - category: Filter by email category
    - proposal_id: Filter by linked proposal

    **Sorting:**
    - sort_by: Field to sort by (default: date)
    - sort_order: ASC or DESC (default: DESC for most recent first)
    """
    try:
        email_svc = get_email_service()
        return email_svc.get_all_emails(
            search_query=q,
            category=category,
            proposal_id=proposal_id,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/emails/{email_id}")
async def get_email(email_id: int):
    """Get email by ID with full content"""
    try:
        email_svc = get_email_service()
        email = email_svc.get_email_by_id(email_id)

        if not email:
            raise HTTPException(status_code=404, detail=f"Email {email_id} not found")

        return email
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/emails/categories")
async def get_email_categories():
    """Get count of emails by category"""
    try:
        email_svc = get_email_service()
        return email_svc.get_categorized_count()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/emails/categories/list")
async def get_email_categories_list():
    """
    Get list of all email categories with metadata

    Returns structured list for dynamic dropdowns with:
    - value: Category identifier
    - label: Display name
    - count: Number of emails in this category
    """
    try:
        email_svc = get_email_service()
        return email_svc.get_categories_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/emails/categories/{category}")
async def get_emails_by_category(
    category: str,
    limit: int = Query(50, ge=1, le=200)
):
    """Get emails by category"""
    try:
        email_svc = get_email_service()
        return email_svc.get_emails_by_category(category, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/emails/search")
async def search_emails(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Search emails by subject or sender"""
    try:
        email_svc = get_email_service()
        return email_svc.search_emails(q, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/emails/stats")
async def get_email_stats():
    """Get email statistics"""
    try:
        email_svc = get_email_service()
        return email_svc.get_email_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/emails/{email_id}/category")
async def update_email_category(
    email_id: int,
    payload: EmailCategoryUpdate
):
    """Update email category with human feedback"""
    try:
        email_svc = get_email_service()
        updated = email_svc.update_email_category(
            email_id=email_id,
            new_category=payload.category,
            subcategory=payload.subcategory,
            feedback=payload.feedback
        )

        if not updated:
            raise HTTPException(status_code=404, detail=f"Email {email_id} not found")

        return {
            "message": "Email category updated",
            "data": updated
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DOCUMENT ENDPOINTS
# ============================================================================

@app.get("/api/documents")
async def get_documents(
    q: Optional[str] = Query(None, description="Search by filename"),
    document_type: Optional[str] = Query(None),
    proposal_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """
    Get all documents with search, filtering, and pagination

    **Search:**
    - q: Search in filename field

    **Filters:**
    - document_type: Filter by document type
    - proposal_id: Filter by linked proposal
    """
    try:
        doc_svc = get_document_service()
        return doc_svc.get_all_documents(
            search_query=q,
            document_type=document_type,
            proposal_id=proposal_id,
            page=page,
            per_page=per_page
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{document_id}")
async def get_document(document_id: int):
    """Get document by ID"""
    try:
        doc_svc = get_document_service()
        doc = doc_svc.get_document_by_id(document_id)

        if not doc:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

        return doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/search")
async def search_documents(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Search documents by filename"""
    try:
        doc_svc = get_document_service()
        return doc_svc.search_documents(q, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/types")
async def get_document_types():
    """Get all document types with counts"""
    try:
        doc_svc = get_document_service()
        return doc_svc.get_document_types()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/stats")
async def get_document_stats():
    """Get document statistics"""
    try:
        doc_svc = get_document_service()
        return doc_svc.get_document_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# QUERY ENDPOINTS (Natural Language)
# ============================================================================

@app.post("/api/query")
async def execute_query(request: QueryRequest):
    """Execute a natural language query"""
    try:
        query_svc = get_query_service()
        return query_svc.query(request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/query/suggestions")
async def get_query_suggestions():
    """Get example query suggestions"""
    try:
        query_svc = get_query_service()
        return {
            "suggestions": query_svc.get_query_suggestions(),
            "types": query_svc.get_supported_query_types()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ANALYTICS & DASHBOARD ENDPOINTS
# ============================================================================

@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics():
    """Get complete dashboard analytics (all stats combined)"""
    try:
        proposal_svc = get_proposal_service()
        email_svc = get_email_service()
        doc_svc = get_document_service()

        return {
            "proposals": proposal_svc.get_dashboard_stats(),
            "emails": email_svc.get_email_stats(),
            "documents": doc_svc.get_document_stats(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
