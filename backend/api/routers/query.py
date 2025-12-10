"""
Query Router - Natural language query and search endpoints

Endpoints:
    POST /api/query/ask - Ask a natural language question
    GET /api/query/search - Search across all data
    GET /api/query/suggestions - Query suggestions
    POST /api/query/chat - Chat conversation
    ... and more
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel, Field

from api.services import query_service, proposal_query_service
from api.models import QueryRequest, QueryFeedbackRequest
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api", tags=["query"])


# ============================================================================
# NATURAL LANGUAGE QUERY
# ============================================================================

@router.post("/query/ask")
async def ask_query(request: QueryRequest):
    """Process a natural language query"""
    try:
        result = query_service.process_query(
            query=request.query,
            context=request.context
        )
        return item_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/ask")
async def ask_query_get(q: str = Query(..., description="Natural language query")):
    """Process a natural language query (GET method)"""
    try:
        result = query_service.process_query(query=q)
        return item_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/ask-enhanced")
async def ask_enhanced_query(request: QueryRequest):
    """Process query with enhanced AI analysis"""
    try:
        result = query_service.process_enhanced_query(
            query=request.query,
            context=request.context
        )
        return item_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/chat")
async def chat_query(request: dict):
    """Process a chat-style conversation query with conversation history"""
    try:
        question = request.get("question", "")
        conversation_history = request.get("conversation_history", [])
        use_ai = request.get("use_ai", True)

        # Format conversation history as string for the service
        conversation_context = None
        if conversation_history:
            context_parts = []
            for msg in conversation_history[-5:]:  # Use last 5 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                context_parts.append(f"{role}: {content}")
            conversation_context = "\n".join(context_parts)

        result = query_service.query_with_context(
            question=question,
            conversation_context=conversation_context,
            use_ai=use_ai
        )
        # Return raw result - frontend expects {success, results, ...} not wrapped in {data, meta}
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SEARCH
# ============================================================================

@router.get("/query/search")
async def search(
    q: str = Query(..., description="Search query"),
    type: Optional[str] = Query(None, description="Filter by type: projects, emails, contacts"),
    limit: int = Query(20, ge=1, le=100)
):
    """Search across all data. Returns standardized list response."""
    try:
        results = query_service.search(query=q, filter_type=type, limit=limit)
        response = list_response(results, len(results))
        response["results"] = results  # Backward compat
        response["query"] = q  # Backward compat
        response["count"] = len(results)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/search-communications")
async def search_communications(
    q: str = Query(..., description="Search query"),
    project_code: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100)
):
    """Search emails and communications. Returns standardized list response."""
    try:
        results = query_service.search_communications(
            query=q,
            project_code=project_code,
            limit=limit
        )
        response = list_response(results, len(results))
        response["results"] = results  # Backward compat
        response["query"] = q  # Backward compat
        response["count"] = len(results)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# QUERY HELPERS
# ============================================================================

@router.get("/query/suggestions")
async def get_query_suggestions():
    """Get suggested queries. Returns standardized list response."""
    try:
        suggestions = query_service.get_suggestions()
        response = list_response(suggestions, len(suggestions))
        response["suggestions"] = suggestions  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/examples")
async def get_query_examples():
    """Get example queries. Returns standardized list response."""
    examples = [
        "What's the status of BK-033?",
        "Show me overdue invoices",
        "Which projects need follow up?",
        "How much is outstanding for Thailand projects?",
        "Show emails about RFI",
        "What happened with Marriott last week?"
    ]
    response = list_response(examples, len(examples))
    response["examples"] = examples  # Backward compat
    return response


@router.get("/query/stats")
async def get_query_stats():
    """Get query usage statistics"""
    try:
        stats = query_service.get_stats()
        return item_response(stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/intelligent-suggestions")
async def get_intelligent_suggestions():
    """Get AI-powered query suggestions based on context. Returns standardized list response."""
    try:
        suggestions = query_service.get_intelligent_suggestions()
        response = list_response(suggestions, len(suggestions))
        response["suggestions"] = suggestions  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROJECT-SPECIFIC QUERIES
# ============================================================================

@router.get("/query/project-status/{project_search}")
async def query_project_status(project_search: str):
    """Get project status by code or name"""
    try:
        result = proposal_query_service.get_project_status(project_search)
        if not result:
            raise HTTPException(status_code=404, detail="Project not found")
        return item_response(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/context/{project_search}")
async def get_project_context(project_search: str):
    """Get full context for a project"""
    try:
        result = proposal_query_service.get_context(project_search)
        if not result:
            raise HTTPException(status_code=404, detail="Project not found")
        return item_response(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/timeline/{project_search}")
async def get_project_timeline(project_search: str):
    """Get timeline for a project. Returns standardized list response."""
    try:
        result = proposal_query_service.get_timeline(project_search)
        timeline = result if isinstance(result, list) else [result] if result else []
        response = list_response(timeline, len(timeline))
        response["timeline"] = result  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/outstanding/{project_search}")
async def get_project_outstanding(project_search: str):
    """Get outstanding amounts for a project"""
    try:
        result = proposal_query_service.get_outstanding(project_search)
        return item_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/proposal/{project_code}/status")
async def get_proposal_status(project_code: str):
    """Get proposal status details"""
    try:
        result = proposal_query_service.get_proposal_status(project_code)
        if not result:
            raise HTTPException(status_code=404, detail="Proposal not found")
        return item_response(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/proposal/{project_code}/documents")
async def get_proposal_documents(project_code: str):
    """Get documents for a proposal. Returns standardized list response."""
    try:
        result = proposal_query_service.get_documents(project_code)
        docs = result if isinstance(result, list) else [result] if result else []
        response = list_response(docs, len(docs))
        response["documents"] = result  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/proposal/{project_code}/fee")
async def get_proposal_fee(project_code: str):
    """Get fee details for a proposal"""
    try:
        result = proposal_query_service.get_fee_details(project_code)
        return item_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/proposal/{project_code}/scope")
async def get_proposal_scope(project_code: str):
    """Get scope details for a proposal"""
    try:
        result = proposal_query_service.get_scope(project_code)
        return item_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FEEDBACK
# ============================================================================

@router.post("/query/feedback")
async def submit_query_feedback(request: QueryFeedbackRequest):
    """Submit feedback on query results"""
    try:
        result = query_service.record_feedback(
            query=request.query,
            response=request.response,
            helpful=request.helpful,
            feedback=request.feedback
        )
        return action_response(True, message="Feedback recorded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
