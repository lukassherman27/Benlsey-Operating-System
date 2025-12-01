"""
Intelligence Router - AI intelligence, follow-up suggestions, and user learning

Combines:
- ProposalIntelligenceService - Proposal context and AI insights
- FollowUpAgent - Follow-up recommendations
- UserLearningService - User query patterns and suggestions

Endpoints:
    GET /api/intelligence/proposals/{project_code}/context - Full proposal context
    GET /api/intelligence/proposals/needing-attention - Proposals needing attention
    GET /api/intelligence/weekly-summary - Weekly intelligence summary
    POST /api/intelligence/proposals/{project_code}/follow-up-email - Generate follow-up
    POST /api/intelligence/proposals/{project_code}/answer - Answer question about proposal
    GET /api/intelligence/follow-ups - Get follow-up recommendations
    POST /api/intelligence/follow-ups/{proposal_id}/draft - Draft follow-up email
    POST /api/intelligence/follow-ups/run-daily - Run daily analysis
    GET /api/intelligence/learning/patterns - Get learned patterns
    GET /api/intelligence/learning/suggestions - Get AI suggestions
    POST /api/intelligence/learning/log-query - Log user query
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from api.services import (
    proposal_intelligence_service,
    follow_up_agent,
    user_learning_service
)
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api", tags=["intelligence"])


# ============================================================================
# REQUEST MODELS
# ============================================================================

class GenerateFollowUpRequest(BaseModel):
    """Request to generate follow-up email"""
    tone: str = Field("professional", description="Tone: professional, casual, urgent")
    context: Optional[str] = None


class AnswerQuestionRequest(BaseModel):
    """Request to answer a question about a proposal"""
    question: str


class DraftFollowUpRequest(BaseModel):
    """Request to draft follow-up email"""
    tone: str = "professional"
    include_summary: bool = True


class LogQueryRequest(BaseModel):
    """Request to log a user query"""
    query_text: str
    query_type: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    success: bool = True


# ============================================================================
# PROPOSAL INTELLIGENCE
# ============================================================================

@router.get("/intelligence/proposals/{project_code}/context")
async def get_proposal_context(project_code: str):
    """Get full AI-generated context for a proposal"""
    try:
        context = proposal_intelligence_service.get_proposal_context(project_code)
        if not context:
            raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")
        return item_response(context)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intelligence/proposals/needing-attention")
async def get_proposals_needing_attention():
    """Get proposals that need attention based on AI analysis"""
    try:
        proposals = proposal_intelligence_service.get_proposals_needing_attention()
        return list_response(proposals, len(proposals))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intelligence/weekly-summary")
async def get_weekly_summary():
    """Get AI-generated weekly intelligence summary"""
    try:
        summary = proposal_intelligence_service.get_weekly_summary()
        return item_response(summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/intelligence/proposals/{project_code}/follow-up-email")
async def generate_follow_up_email(project_code: str, request: GenerateFollowUpRequest):
    """Generate a follow-up email for a proposal"""
    try:
        email = proposal_intelligence_service.generate_follow_up_email(
            project_code=project_code,
            tone=request.tone,
            context=request.context
        )
        return item_response(email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/intelligence/proposals/{project_code}/answer")
async def answer_proposal_question(project_code: str, request: AnswerQuestionRequest):
    """Answer a question about a specific proposal"""
    try:
        answer = proposal_intelligence_service.answer_proposal_question(
            project_code=project_code,
            question=request.question
        )
        return item_response(answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FOLLOW-UP AGENT
# ============================================================================

@router.get("/intelligence/follow-ups")
async def get_follow_up_recommendations(
    limit: int = Query(20, ge=1, le=100),
    urgency: Optional[str] = Query(None, description="Filter by urgency: critical, high, medium, low")
):
    """Get AI follow-up recommendations"""
    try:
        proposals = follow_up_agent.get_proposals_needing_followup(
            limit=limit,
            urgency_filter=urgency
        )
        return list_response(proposals, len(proposals))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/intelligence/follow-ups/{proposal_id}/draft")
async def draft_follow_up_email(proposal_id: int, request: DraftFollowUpRequest):
    """Draft a follow-up email for a proposal"""
    try:
        draft = follow_up_agent.draft_follow_up_email(
            proposal_id=proposal_id,
            tone=request.tone,
            include_summary=request.include_summary
        )
        return item_response(draft)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/intelligence/follow-ups/run-daily")
async def run_daily_follow_up_analysis():
    """Run the daily follow-up analysis job"""
    try:
        result = follow_up_agent.run_daily_analysis()
        return action_response(True, data=result, message="Daily analysis completed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# USER LEARNING
# ============================================================================

@router.get("/intelligence/learning/patterns")
async def get_learned_patterns(user_id: str = Query("bill", description="User ID")):
    """Get patterns learned from user behavior"""
    try:
        patterns = user_learning_service.get_active_patterns(user_id=user_id)
        response = list_response(patterns, len(patterns))
        response["patterns"] = patterns  # Backward compat
        response["count"] = len(patterns)  # Backward compat
        response["user_id"] = user_id  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intelligence/learning/suggestions")
async def get_learning_suggestions(user_id: str = Query("bill", description="User ID")):
    """Get AI suggestions based on learned patterns"""
    try:
        suggestions = user_learning_service.generate_suggestions(user_id=user_id)
        response = list_response(suggestions, len(suggestions))
        response["suggestions"] = suggestions  # Backward compat
        response["count"] = len(suggestions)  # Backward compat
        response["user_id"] = user_id  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intelligence/learning/query-patterns")
async def analyze_query_patterns(
    user_id: str = Query("bill", description="User ID"),
    days: int = Query(30, ge=1, le=365)
):
    """Analyze user query patterns"""
    try:
        patterns = user_learning_service.analyze_query_patterns(user_id=user_id, days=days)
        return item_response(patterns)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/intelligence/learning/log-query")
async def log_user_query(request: LogQueryRequest):
    """Log a user query for learning"""
    try:
        user_learning_service.log_query(
            query_text=request.query_text,
            query_type=request.query_type,
            context=request.context,
            success=request.success
        )
        return action_response(True, message="Query logged")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/intelligence/learning/patterns/{pattern_id}/response")
async def record_suggestion_response(pattern_id: int, accepted: bool = Query(...)):
    """Record user response to a suggestion"""
    try:
        user_learning_service.record_suggestion_response(pattern_id=pattern_id, accepted=accepted)
        return action_response(True, message="Response recorded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
