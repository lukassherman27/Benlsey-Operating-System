"""
Email Orchestrator - Coordinates existing email services

This is a THIN WRAPPER that calls existing services:
- AILearningService: Suggestion generation
- EmailCategoryService: Email categorization
- EmailIntelligenceService: Timeline, validation queue

Does NOT duplicate functionality - just coordinates.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

from .base_service import BaseService
from .ai_learning_service import AILearningService
from .email_category_service import EmailCategoryService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailOrchestrator(BaseService):
    """
    Orchestrator that coordinates existing email services.

    Usage:
        orchestrator = EmailOrchestrator()
        result = orchestrator.process_new_emails(limit=100)
    """

    def __init__(self, db_path: str = None):
        super().__init__(db_path)
        self.ai_learning = AILearningService(db_path)
        self.category_service = EmailCategoryService(db_path)

    def process_new_emails(self, limit: int = 100, hours: int = 24) -> Dict[str, Any]:
        """
        Full email processing pipeline.

        1. Categorize uncategorized emails (uses EmailCategoryService.batch_categorize)
        2. Generate suggestions (uses AILearningService.process_recent_emails_for_suggestions)

        NEVER auto-applies anything - all changes go through suggestion approval.

        Args:
            limit: Max emails to process
            hours: Look back period for suggestion generation

        Returns:
            Combined stats from both operations
        """
        result = {
            "success": True,
            "categorization": {},
            "suggestions": {},
            "errors": []
        }

        # Step 1: Categorize uncategorized emails
        try:
            cat_result = self.category_service.batch_categorize(limit=limit)
            result["categorization"] = cat_result
        except Exception as e:
            logger.error(f"Categorization error: {e}")
            result["errors"].append(f"Categorization: {str(e)}")
            result["categorization"] = {"error": str(e)}

        # Step 2: Generate suggestions for recent emails
        try:
            sugg_result = self.ai_learning.process_recent_emails_for_suggestions(
                hours=hours,
                limit=limit
            )
            result["suggestions"] = sugg_result
        except Exception as e:
            logger.error(f"Suggestion generation error: {e}")
            result["errors"].append(f"Suggestions: {str(e)}")
            result["suggestions"] = {"error": str(e)}

        return result

    def get_daily_summary(self, date_str: str = None) -> Dict[str, Any]:
        """
        Get daily import/processing summary.

        Aggregates stats from database tables.

        Args:
            date_str: Optional date string (YYYY-MM-DD), defaults to today

        Returns:
            Summary with import stats, categorization counts, suggestions created
        """
        if date_str is None:
            date_str = date.today().isoformat()

        # Imported today
        imported = self.execute_query("""
            SELECT COUNT(*) as count
            FROM emails
            WHERE DATE(created_at) = ?
        """, (date_str,), fetch_one=True)

        # Categorized today (via email_content)
        categorized = self.execute_query("""
            SELECT COUNT(*) as count
            FROM email_content
            WHERE DATE(created_at) = ?
            AND category IS NOT NULL AND category != ''
        """, (date_str,), fetch_one=True)

        # Uncategorized (in bucket, not reviewed)
        uncategorized = self.execute_query("""
            SELECT COUNT(*) as count
            FROM uncategorized_emails
            WHERE DATE(created_at) = ?
            AND reviewed = 0
        """, (date_str,), fetch_one=True)

        # Suggestions created today
        suggestions_created = self.execute_query("""
            SELECT COUNT(*) as count
            FROM ai_suggestions
            WHERE DATE(created_at) = ?
        """, (date_str,), fetch_one=True)

        # Category breakdown for today
        by_category = self.execute_query("""
            SELECT
                category,
                COUNT(*) as count
            FROM email_content
            WHERE DATE(created_at) = ?
            AND category IS NOT NULL AND category != ''
            GROUP BY category
            ORDER BY count DESC
        """, (date_str,))

        category_dict = {row['category']: row['count'] for row in by_category}

        # Get pending suggestions count
        pending_suggestions = self.execute_query("""
            SELECT COUNT(*) as count
            FROM ai_suggestions
            WHERE status = 'pending'
        """, fetch_one=True)

        return {
            "date": date_str,
            "imported": imported['count'] if imported else 0,
            "categorized": categorized['count'] if categorized else 0,
            "uncategorized": uncategorized['count'] if uncategorized else 0,
            "suggestions_created": suggestions_created['count'] if suggestions_created else 0,
            "pending_suggestions": pending_suggestions['count'] if pending_suggestions else 0,
            "by_category": category_dict
        }

    def get_import_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive import statistics.

        Returns:
            Stats for daily, weekly, and total imports with trends
        """
        today = date.today()
        week_ago = today - timedelta(days=7)

        # Today's stats
        today_stats = self.get_daily_summary(today.isoformat())

        # This week's totals
        week_imported = self.execute_query("""
            SELECT COUNT(*) as count
            FROM emails
            WHERE DATE(created_at) >= ?
        """, (week_ago.isoformat(),), fetch_one=True)

        week_categorized = self.execute_query("""
            SELECT COUNT(*) as count
            FROM email_content
            WHERE DATE(created_at) >= ?
            AND category IS NOT NULL AND category != ''
        """, (week_ago.isoformat(),), fetch_one=True)

        week_suggestions = self.execute_query("""
            SELECT COUNT(*) as count
            FROM ai_suggestions
            WHERE DATE(created_at) >= ?
        """, (week_ago.isoformat(),), fetch_one=True)

        # Total stats
        total_emails = self.count_rows('emails')
        total_categorized = self.execute_query("""
            SELECT COUNT(*) as count
            FROM email_content
            WHERE category IS NOT NULL AND category != ''
        """, fetch_one=True)

        total_suggestions = self.execute_query("""
            SELECT COUNT(*) as count
            FROM ai_suggestions
        """, fetch_one=True)

        pending_suggestions = self.execute_query("""
            SELECT COUNT(*) as count
            FROM ai_suggestions
            WHERE status = 'pending'
        """, fetch_one=True)

        # Daily trend (last 7 days)
        daily_trend = self.execute_query("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as imported
            FROM emails
            WHERE DATE(created_at) >= ?
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        """, (week_ago.isoformat(),))

        return {
            "success": True,
            "today": today_stats,
            "this_week": {
                "imported": week_imported['count'] if week_imported else 0,
                "categorized": week_categorized['count'] if week_categorized else 0,
                "suggestions": week_suggestions['count'] if week_suggestions else 0
            },
            "totals": {
                "emails": total_emails,
                "categorized": total_categorized['count'] if total_categorized else 0,
                "suggestions": total_suggestions['count'] if total_suggestions else 0,
                "pending_suggestions": pending_suggestions['count'] if pending_suggestions else 0
            },
            "daily_trend": [dict(row) for row in daily_trend]
        }

    def get_suggestions_grouped(self, status: str = 'pending') -> Dict[str, Any]:
        """
        Get suggestions grouped by project_code.

        Args:
            status: Filter by status (default 'pending')

        Returns:
            Dict with groups (by project) and ungrouped suggestions
        """
        # Get all suggestions with the given status
        suggestions = self.execute_query("""
            SELECT
                s.*,
                p.project_name,
                p.client_company
            FROM ai_suggestions s
            LEFT JOIN proposals p ON s.project_code = p.project_code
            WHERE s.status = ?
            ORDER BY s.priority DESC, s.confidence_score DESC, s.created_at DESC
        """, (status,))

        # Group by project_code
        groups = {}
        ungrouped = []

        for suggestion in suggestions:
            suggestion = dict(suggestion)
            project_code = suggestion.get('project_code')

            if project_code:
                if project_code not in groups:
                    groups[project_code] = {
                        "project_code": project_code,
                        "project_name": suggestion.get('project_name'),
                        "client_company": suggestion.get('client_company'),
                        "suggestion_count": 0,
                        "suggestions": []
                    }
                groups[project_code]["suggestion_count"] += 1
                groups[project_code]["suggestions"].append(suggestion)
            else:
                ungrouped.append(suggestion)

        # Sort groups by suggestion count
        sorted_groups = sorted(
            groups.values(),
            key=lambda x: x['suggestion_count'],
            reverse=True
        )

        return {
            "success": True,
            "groups": sorted_groups,
            "ungrouped": ungrouped,
            "total": len(suggestions)
        }
