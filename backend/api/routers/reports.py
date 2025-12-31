"""
Reports API - Historical report storage and retrieval (#291)

Endpoints:
- GET /api/reports/weekly-proposals - List archived weekly reports
- GET /api/reports/weekly-proposals/latest - Get latest report
- GET /api/reports/weekly-proposals/{report_id} - Get specific report
- POST /api/reports/weekly-proposals/generate - Generate and archive new report
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing import Optional
from datetime import datetime
import json
import sys

from pathlib import Path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from api.dependencies import DB_PATH
from services.weekly_report_service import WeeklyReportService

router = APIRouter(prefix="/api/reports", tags=["reports"])

report_service = WeeklyReportService(DB_PATH)


@router.get("/weekly-proposals")
async def list_weekly_reports(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List archived weekly proposal reports.

    Returns paginated list of historical reports with summary metrics.
    """
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get total count
    cursor.execute("SELECT COUNT(*) FROM weekly_proposal_reports")
    total = cursor.fetchone()[0]

    # Get reports
    cursor.execute("""
        SELECT
            report_id,
            report_date,
            week_ending,
            proposals_count,
            total_pipeline_value,
            win_rate,
            stale_count,
            new_this_week,
            won_this_week,
            lost_this_week,
            created_at
        FROM weekly_proposal_reports
        ORDER BY report_date DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))

    reports = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "reports": reports
    }


@router.get("/weekly-proposals/latest")
async def get_latest_report():
    """
    Get the most recent weekly report with full data.

    Returns complete report including all metrics and HTML preview.
    """
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM weekly_proposal_reports
        ORDER BY report_date DESC, created_at DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="No reports found")

    report = dict(row)

    # Parse stored JSON if available
    if report.get('report_data'):
        try:
            report['data'] = json.loads(report['report_data'])
        except json.JSONDecodeError:
            report['data'] = None

    return report


@router.get("/weekly-proposals/{report_id}")
async def get_report_by_id(report_id: int):
    """
    Get a specific weekly report by ID.
    """
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM weekly_proposal_reports
        WHERE report_id = ?
    """, (report_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    report = dict(row)

    if report.get('report_data'):
        try:
            report['data'] = json.loads(report['report_data'])
        except json.JSONDecodeError:
            report['data'] = None

    return report


@router.post("/weekly-proposals/generate")
async def generate_and_archive_report(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Generate a new weekly report and archive it.

    This creates a report for the specified period (or last week by default),
    stores it in the database for history, and returns the full report.
    """
    import sqlite3

    # Generate report using existing service
    report = report_service.generate_report(start_date, end_date)

    # Extract key metrics for columns
    period = report.get('period', {})
    week_review = report.get('week_in_review', {})
    pipeline = report.get('pipeline_outlook', {})
    attention = report.get('attention_required', {})

    # Store in database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO weekly_proposal_reports (
            report_date,
            week_ending,
            pdf_path,
            proposals_count,
            total_pipeline_value,
            win_rate,
            stale_count,
            new_this_week,
            won_this_week,
            lost_this_week,
            report_data,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        period.get('end', datetime.now().strftime('%Y-%m-%d')),
        period.get('end', datetime.now().strftime('%Y-%m-%d')),
        '',  # No PDF path for API-generated reports
        pipeline.get('proposal_count', 0),
        pipeline.get('total_pipeline', 0),
        pipeline.get('win_rate', {}).get('current', 0),
        attention.get('stale_count', 0),
        week_review.get('new_proposals', {}).get('count', 0),
        week_review.get('won', {}).get('count', 0),
        week_review.get('lost', {}).get('count', 0),
        json.dumps(report),
        datetime.now().isoformat()
    ))

    report_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "report_id": report_id,
        "message": "Report generated and archived successfully",
        "report": report
    }


@router.get("/weekly-proposals/preview/html", response_class=HTMLResponse)
async def get_html_preview(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get HTML preview of the weekly report (for email or display).
    """
    html = report_service.generate_html_report(start_date, end_date)
    return HTMLResponse(content=html)
