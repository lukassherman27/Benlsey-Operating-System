# Weekly Proposal Report System - Plan

**Issue:** #291
**Branch:** `feat/weekly-proposal-report-291`
**Date:** 2025-12-31

## Research Summary

### What Already Existed
Significant work was already done on this system:
1. `WeeklyReportService` - comprehensive service with all required metrics
2. `/api/weekly-report` endpoint - returns full report data
3. `generate_weekly_proposal_report.py` - PDF generation script
4. `weekly_proposal_reports` table - stores historical reports

### Roadmap 1.3 Requirements vs Current State

| Requirement | Status | Notes |
|-------------|--------|-------|
| Scheduled script (Monday 7am) | Not implemented | Infrastructure needed |
| New proposals sent last week | Done | In WeeklyReportService |
| Proposals won/lost | Done | In WeeklyReportService |
| Stale proposals (14+ days) | Done | In WeeklyReportService |
| Total pipeline value | Done | In WeeklyReportService |
| Win rate trends | Done | In WeeklyReportService |
| Email report to Bill | Not implemented | Needs email service |
| Archive reports for history | Partially done | Table exists, enhance columns |

## Approach Chosen

Rather than rebuild from scratch, I extended the existing system:

1. **Enhanced `weekly_proposal_reports` table** - Added columns for all metrics:
   - `report_data` (JSON) - Full report data
   - `win_rate` - Win rate at time of report
   - `stale_count` - Number of stale proposals
   - `new_this_week`, `won_this_week`, `lost_this_week` - Weekly metrics

2. **Created `/api/reports/weekly-proposals` endpoint** - As requested in task:
   - `GET /api/reports/weekly-proposals` - List historical reports
   - `GET /api/reports/weekly-proposals/latest` - Get most recent
   - `GET /api/reports/weekly-proposals/{id}` - Get specific report
   - `POST /api/reports/weekly-proposals/generate` - Generate and archive new report
   - `GET /api/reports/weekly-proposals/preview/html` - HTML preview

## What I Did NOT Do

1. **Email sending** - Not in scope for this task. Would need:
   - SMTP configuration
   - Email template system
   - Scheduling (cron/launchd)

2. **PDF generation in API** - The existing `generate_weekly_proposal_report.py`
   handles PDF. API returns JSON and HTML.

3. **Dashboard UI changes** - Task said "DO NOT modify frontend"

## Files Changed

1. `backend/api/routers/reports.py` - NEW - Reports API router
2. `backend/api/main.py` - Added reports router import
3. `database/bensley_master.db` - Added columns to weekly_proposal_reports

## Testing

Report generation verified:
- Period: 2025-12-29 to 2025-12-31
- Total pipeline: $84,261,000
- Win rate: 42.9%
- Stale proposals: 10
- Top opportunity: 25 BK-037 - La Vie Wellness Resort ($4M)
