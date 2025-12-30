"""
Story API - Proposal narrative and activity extraction endpoints.
Issue #141: AI Story Builder

Provides:
- GET /story/{proposal_id} - Get complete proposal story
- GET /story/code/{project_code} - Get story by project code
- POST /story/extract/email/{email_id} - Extract activities from email
- POST /story/extract/transcript/{transcript_id} - Extract from transcript
- POST /story/extract/batch - Process unprocessed content
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import sys

# Add backend path for imports
from pathlib import Path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from api.dependencies import DB_PATH
from services.proposal_story_service import ProposalStoryService
from services.activity_extractor import ActivityExtractor

router = APIRouter(prefix="/api/story", tags=["story"])

# Initialize services with correct DB path
story_service = ProposalStoryService(DB_PATH)
extractor = ActivityExtractor(DB_PATH)


class ExtractionResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    extracted: Optional[dict] = None
    error: Optional[str] = None


@router.get("/{proposal_id}")
async def get_proposal_story(proposal_id: int):
    """
    Get the complete story for a proposal.

    Returns:
    - proposal: Basic info
    - milestones: Key milestones in journey
    - timeline: Chronological activities
    - action_items: Pending and completed items
    - sentiment_trend: How sentiment evolved
    - highlights: Key moments
    - story_summary: Narrative summary
    """
    result = story_service.get_proposal_story(proposal_id)
    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error', 'Not found'))
    return result


@router.get("/code/{project_code}")
async def get_proposal_story_by_code(project_code: str):
    """Get story by project code (e.g., '25 BK-087')."""
    result = story_service.get_proposal_story_by_code(project_code)
    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error', 'Not found'))
    return result


@router.get("/quick/{proposal_id}")
async def get_quick_summary(proposal_id: int):
    """Get lightweight summary for hover cards."""
    result = story_service.get_proposal_quick_summary(proposal_id)
    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error', 'Not found'))
    return result


@router.post("/extract/email/{email_id}")
async def extract_from_email(email_id: int):
    """
    Extract activities and action items from a linked email.

    The email must be linked to a proposal first.
    Extracts:
    - Action items with dates and owners
    - Key decisions
    - Sentiment
    - Important dates
    """
    result = extractor.extract_from_email(email_id)
    if not result.get('success'):
        if 'not linked' in result.get('error', '').lower():
            raise HTTPException(status_code=400, detail=result.get('error'))
        raise HTTPException(status_code=404, detail=result.get('error', 'Not found'))
    return result


@router.post("/extract/transcript/{transcript_id}")
async def extract_from_transcript(transcript_id: int):
    """
    Extract activities and action items from a meeting transcript.

    The transcript must be linked to a proposal.
    """
    result = extractor.extract_from_transcript(transcript_id)
    if not result.get('success'):
        if 'not linked' in result.get('error', '').lower():
            raise HTTPException(status_code=400, detail=result.get('error'))
        raise HTTPException(status_code=404, detail=result.get('error', 'Not found'))
    return result


@router.post("/extract/batch")
async def batch_extract(
    background_tasks: BackgroundTasks,
    email_limit: int = Query(100, ge=1, le=500),
    transcript_limit: int = Query(50, ge=1, le=200),
    run_async: bool = Query(False)
):
    """
    Process unprocessed emails and transcripts.

    This finds linked content that hasn't had activities extracted
    and processes them.

    Set run_async=true to run in background (returns immediately).
    """
    if run_async:
        background_tasks.add_task(
            _run_batch_extraction,
            email_limit,
            transcript_limit
        )
        return {
            'success': True,
            'message': 'Batch extraction started in background',
            'limits': {
                'emails': email_limit,
                'transcripts': transcript_limit
            }
        }

    # Run synchronously
    return _run_batch_extraction(email_limit, transcript_limit)


def _run_batch_extraction(email_limit: int, transcript_limit: int) -> dict:
    """Run batch extraction (can be sync or async)."""
    email_result = extractor.process_unprocessed_emails(limit=email_limit)
    transcript_result = extractor.process_unprocessed_transcripts(limit=transcript_limit)

    return {
        'success': True,
        'emails': {
            'processed': email_result.get('processed', 0),
            'action_items_created': email_result.get('action_items_created', 0),
            'errors': len(email_result.get('errors', []))
        },
        'transcripts': {
            'processed': transcript_result.get('processed', 0),
            'action_items_created': transcript_result.get('action_items_created', 0),
            'errors': len(transcript_result.get('errors', []))
        }
    }


@router.get("/stats")
async def get_extraction_stats():
    """Get statistics on extraction coverage."""
    import sqlite3

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Count linked emails
    cursor.execute("SELECT COUNT(*) FROM email_proposal_links")
    linked_emails = cursor.fetchone()[0]

    # Count emails with activities
    cursor.execute("""
        SELECT COUNT(DISTINCT source_id)
        FROM proposal_activities
        WHERE source_type = 'email'
    """)
    emails_with_activities = cursor.fetchone()[0]

    # Count linked transcripts
    cursor.execute("""
        SELECT COUNT(*)
        FROM meeting_transcripts t
        LEFT JOIN proposals p ON t.detected_project_code = p.project_code
        WHERE t.proposal_id IS NOT NULL OR p.proposal_id IS NOT NULL
    """)
    linked_transcripts = cursor.fetchone()[0]

    # Count transcripts with activities
    cursor.execute("""
        SELECT COUNT(DISTINCT source_id)
        FROM proposal_activities
        WHERE source_type = 'transcript'
    """)
    transcripts_with_activities = cursor.fetchone()[0]

    # Total action items (from unified tasks table)
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE proposal_id IS NOT NULL")
    total_action_items = cursor.fetchone()[0]

    # Pending action items
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE proposal_id IS NOT NULL AND status = 'pending'")
    pending_action_items = cursor.fetchone()[0]

    conn.close()

    return {
        'emails': {
            'linked': linked_emails,
            'with_activities': emails_with_activities,
            'pending': linked_emails - emails_with_activities
        },
        'transcripts': {
            'linked': linked_transcripts,
            'with_activities': transcripts_with_activities,
            'pending': linked_transcripts - transcripts_with_activities
        },
        'action_items': {
            'total': total_action_items,
            'pending': pending_action_items,
            'completed': total_action_items - pending_action_items
        }
    }
