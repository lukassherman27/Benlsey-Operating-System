"""
Training Router - AI training and feedback management endpoints

Endpoints:
    GET /api/training/stats - Training statistics
    GET /api/training/unverified - Unverified training data
    GET /api/training/{training_id} - Get training record
    POST /api/training/{training_id}/verify - Verify training record
    POST /api/training/verify/bulk - Bulk verify training records
    GET /api/training/feedback/stats - Feedback statistics
    GET /api/training/feedback/corrections - Corrections for review
    GET /api/training/incorrect - Incorrect predictions
    POST /api/training/feedback - Log user feedback
    GET /api/training/feedback/recent - Recent feedback entries
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from api.dependencies import DB_PATH
from api.services import training_service, training_data_service
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api", tags=["training"])


# ============================================================================
# REQUEST MODELS
# ============================================================================

class TrainingVerification(BaseModel):
    """Request model for verifying a training record"""
    is_correct: bool = Field(..., description="Whether the AI output was correct")
    feedback: Optional[str] = Field(None, description="Optional feedback for learning")
    corrected_output: Optional[str] = Field(None, description="Correct output if AI was wrong")


class BulkVerification(BaseModel):
    """Request model for bulk verifying training records"""
    training_ids: List[int] = Field(..., description="List of training record IDs")
    is_correct: bool = Field(..., description="Mark all as correct/incorrect")
    feedback: Optional[str] = Field(None, description="Optional feedback")


class FeedbackRequest(BaseModel):
    """User feedback for RLHF training"""
    feature_type: str = Field(..., description="Type of feature: email_link, category, summary, etc.")
    feature_id: str = Field(..., description="ID of specific feature instance")
    helpful: bool = Field(..., description="Was this AI output helpful?")
    issue_type: Optional[str] = Field(None, description="Issue category if not helpful")
    feedback_text: Optional[str] = Field(None, description="REQUIRED if helpful=False")
    expected_value: Optional[str] = Field(None, description="What user expected")
    current_value: Optional[str] = Field(None, description="What system shows")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


# ============================================================================
# TRAINING STATISTICS
# ============================================================================

@router.get("/training/stats")
async def get_training_stats():
    """Get verification statistics"""
    try:
        stats = training_service.get_verification_stats()
        response = item_response(stats)
        response.update(stats)  # Backward compat - flatten at root
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")


# ============================================================================
# TRAINING DATA VERIFICATION
# ============================================================================

@router.get("/training/unverified")
async def get_unverified_training(
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    min_confidence: Optional[float] = Query(None, ge=0, le=1),
    max_confidence: Optional[float] = Query(None, ge=0, le=1),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Get unverified AI training data for human review"""
    try:
        result = training_service.get_unverified_training(
            task_type=task_type,
            min_confidence=min_confidence,
            max_confidence=max_confidence,
            page=page,
            per_page=per_page
        )
        data = result.get('data', result.get('training', []))
        total = result.get('total', len(data))
        response = list_response(data, total, page, per_page)
        response.update(result)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch training data: {str(e)}")


@router.get("/training/incorrect")
async def get_incorrect_predictions(
    task_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Get training records marked as incorrect"""
    try:
        result = training_service.get_incorrect_predictions(
            task_type=task_type,
            page=page,
            per_page=per_page
        )
        data = result.get('data', result.get('predictions', []))
        total = result.get('total', len(data))
        response = list_response(data, total, page, per_page)
        response.update(result)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch incorrect predictions: {str(e)}")


@router.get("/training/{training_id}")
async def get_training_by_id(training_id: int):
    """Get a specific training record by ID"""
    try:
        training = training_service.get_training_by_id(training_id)
        if not training:
            raise HTTPException(status_code=404, detail="Training record not found")
        return item_response(training)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch training record: {str(e)}")


@router.post("/training/{training_id}/verify")
async def verify_training(training_id: int, verification: TrainingVerification):
    """Verify a training record as correct or incorrect"""
    try:
        success = training_service.verify_training(
            training_id=training_id,
            is_correct=verification.is_correct,
            feedback=verification.feedback,
            corrected_output=verification.corrected_output
        )

        if not success:
            raise HTTPException(status_code=404, detail="Training record not found")

        updated = training_service.get_training_by_id(training_id)
        return action_response(True, data=updated, message="Training verified")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify training: {str(e)}")


@router.post("/training/verify/bulk")
async def bulk_verify_training(bulk: BulkVerification):
    """Bulk verify multiple training records at once"""
    try:
        count = training_service.bulk_verify(
            training_ids=bulk.training_ids,
            is_correct=bulk.is_correct,
            feedback=bulk.feedback
        )
        return action_response(True, data={"verified_count": count, "training_ids": bulk.training_ids}, message=f"Verified {count} records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk verify: {str(e)}")


# ============================================================================
# FEEDBACK ENDPOINTS
# ============================================================================

@router.post("/training/feedback")
async def log_user_feedback(request: FeedbackRequest):
    """Log user feedback for RLHF training"""
    try:
        result = training_data_service.log_feedback(
            feature_type=request.feature_type,
            feature_id=request.feature_id,
            helpful=request.helpful,
            issue_type=request.issue_type,
            feedback_text=request.feedback_text,
            expected_value=request.expected_value,
            current_value=request.current_value,
            context=request.context
        )
        return action_response(True, data=result, message="Feedback logged")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/training/feedback/stats")
async def get_feedback_stats(
    feature: Optional[str] = Query(None, description="Filter by feature name"),
    days: int = Query(30, ge=1, le=365, description="Days to look back")
):
    """Get feedback statistics"""
    try:
        stats = training_data_service.get_feedback_stats(feature=feature, days=days)
        response = item_response(stats)
        response.update(stats)  # Backward compat - flatten at root
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get feedback stats: {str(e)}")


@router.get("/training/feedback/corrections")
async def get_corrections_for_review(
    feature: Optional[str] = Query(None, description="Filter by feature name"),
    limit: int = Query(50, ge=1, le=200)
):
    """Get recent corrections for review"""
    try:
        corrections = training_data_service.get_corrections_for_review(
            feature=feature,
            limit=limit
        )
        response = list_response(corrections, len(corrections))
        response["corrections"] = corrections  # Backward compat
        response["count"] = len(corrections)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get corrections: {str(e)}")


@router.get("/training/feedback/recent")
async def get_recent_feedback(
    feature_type: Optional[str] = Query(None, description="Filter by feature type"),
    helpful: Optional[bool] = Query(None, description="Filter by helpful status"),
    limit: int = Query(50, description="Max number to return")
):
    """Get recent feedback entries for review"""
    try:
        feedback = training_data_service.get_recent_feedback(
            feature_type=feature_type,
            helpful=helpful,
            limit=limit
        )
        response = list_response(feedback, len(feedback))
        response["feedback"] = feedback  # Backward compat
        response["count"] = len(feedback)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
