"""
Context-Aware Suggestion Service

Main orchestration service for GPT-powered suggestion generation.
Coordinates context building, GPT analysis, and suggestion writing.

Part of Phase 2.0: Context-Aware AI Suggestions
"""

import os
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .base_service import BaseService
from .context_bundler import ContextBundler, get_context_bundler
from .gpt_suggestion_analyzer import GPTSuggestionAnalyzer, GPTUsageTracker
from .suggestion_writer import SuggestionWriter
from .thread_context_service import ThreadContextService, get_thread_context_service

logger = logging.getLogger(__name__)


class ContextAwareSuggestionService(BaseService):
    """
    Orchestrates context-aware suggestion generation.

    Flow:
    1. Load context bundle (cached)
    2. Format context for GPT prompt
    3. Analyze emails with GPT
    4. Write suggestions to database
    5. Track usage for cost monitoring
    """

    def __init__(self, db_path: str = None):
        super().__init__(db_path)

        # Initialize sub-services
        self.bundler = get_context_bundler(db_path)
        self.writer = SuggestionWriter(db_path)
        self.thread_service = get_thread_context_service(db_path)

        # Analyzer is initialized lazily (requires API key)
        self._analyzer: Optional[GPTSuggestionAnalyzer] = None

    @property
    def analyzer(self) -> GPTSuggestionAnalyzer:
        """Lazy initialization of GPT analyzer"""
        if self._analyzer is None:
            self._analyzer = GPTSuggestionAnalyzer()
        return self._analyzer

    def is_enabled(self) -> bool:
        """Check if context-aware suggestions are enabled"""
        # Check environment variable first
        env_enabled = os.environ.get("USE_CONTEXT_AWARE_SUGGESTIONS", "").lower() == "true"
        if env_enabled:
            return True

        # Check database config
        try:
            config = self.execute_query("""
                SELECT config_value FROM ai_config
                WHERE config_key = 'use_context_aware_suggestions'
            """, fetch_one=True)
            if config:
                return config.get("config_value", "").lower() == "true"
        except Exception:
            pass

        return False

    def set_enabled(self, enabled: bool, updated_by: str = "system"):
        """Enable or disable context-aware suggestions"""
        try:
            self.execute_update("""
                UPDATE ai_config
                SET config_value = ?, updated_at = datetime('now'), updated_by = ?
                WHERE config_key = 'use_context_aware_suggestions'
            """, ("true" if enabled else "false", updated_by))
            logger.info(f"Context-aware suggestions {'enabled' if enabled else 'disabled'} by {updated_by}")
        except Exception as e:
            logger.error(f"Failed to update config: {e}")
            raise

    def generate_suggestions_for_email(self, email_id: int) -> Dict[str, Any]:
        """
        Generate suggestions for a single email using context-aware analysis.

        Args:
            email_id: ID of email to analyze

        Returns:
            Dict with results including suggestions created and usage stats
        """
        # Load email data
        email = self._load_email(email_id)
        if not email:
            return {"success": False, "error": f"Email {email_id} not found"}

        # Check if already processed
        existing = self.execute_query("""
            SELECT suggestion_id FROM ai_suggestions
            WHERE source_type = 'email' AND source_id = ?
            AND suggested_data LIKE '%"match_type": "context_aware"%'
        """, (email_id,))
        if existing:
            return {
                "success": True,
                "skipped": True,
                "reason": "Already processed with context-aware",
            }

        # Get context and analyze
        context_prompt = self.bundler.format_for_prompt()
        result = self.analyzer.analyze_email(email, context_prompt)

        if not result.get("success"):
            return {
                "success": False,
                "error": result.get("error"),
                "email_id": email_id,
            }

        # Write suggestions
        analysis = result.get("analysis", {})
        suggestion_ids = self.writer.write_suggestions_from_analysis(
            email_id, analysis, email
        )

        # Log usage
        self._log_usage(result, [email_id])

        return {
            "success": True,
            "email_id": email_id,
            "suggestions_created": len(suggestion_ids),
            "suggestion_ids": suggestion_ids,
            "usage": result.get("usage"),
        }

    def generate_suggestions_batch(
        self,
        email_ids: List[int] = None,
        limit: int = 100,
        hours_back: int = 24,
    ) -> Dict[str, Any]:
        """
        Generate suggestions for multiple emails in batch.

        Args:
            email_ids: Specific email IDs to process, or None for recent unprocessed
            limit: Maximum emails to process
            hours_back: If email_ids not provided, look back this many hours

        Returns:
            Dict with batch results
        """
        start_time = datetime.now()

        # Get emails to process
        if email_ids is None:
            email_ids = self._get_unprocessed_emails(limit, hours_back)

        if not email_ids:
            return {
                "success": True,
                "message": "No emails to process",
                "emails_processed": 0,
            }

        # Load emails
        emails = [self._load_email(eid) for eid in email_ids]
        emails = [e for e in emails if e is not None]

        if not emails:
            return {
                "success": True,
                "message": "No valid emails found",
                "emails_processed": 0,
            }

        # Get context (cached)
        context_prompt = self.bundler.format_for_prompt()

        # Analyze batch
        results = self.analyzer.analyze_batch(emails, context_prompt)

        # Process results
        total_suggestions = 0
        successful = 0
        failed = 0
        total_cost = 0.0

        for i, result in enumerate(results):
            if result.get("success"):
                analysis = result.get("analysis", {})
                email_id = emails[i].get("email_id")
                suggestions = self.writer.write_suggestions_from_analysis(
                    email_id, analysis, emails[i]
                )
                total_suggestions += len(suggestions)
                successful += 1
                if result.get("usage"):
                    total_cost += result["usage"].get("estimated_cost_usd", 0)
            else:
                failed += 1

        # Log batch usage
        batch_usage = {
            "input_tokens": sum(r.get("usage", {}).get("input_tokens", 0) for r in results if r.get("success")),
            "output_tokens": sum(r.get("usage", {}).get("output_tokens", 0) for r in results if r.get("success")),
            "estimated_cost_usd": total_cost,
            "processing_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
        }

        self._log_batch_usage(batch_usage, [e.get("email_id") for e in emails])

        return {
            "success": True,
            "emails_processed": len(emails),
            "successful": successful,
            "failed": failed,
            "suggestions_created": total_suggestions,
            "cost_usd": round(total_cost, 4),
            "processing_time_seconds": round((datetime.now() - start_time).total_seconds(), 2),
        }

    def _load_email(self, email_id: int) -> Optional[Dict[str, Any]]:
        """Load email data for analysis, including thread context"""
        email = self.execute_query("""
            SELECT
                e.email_id, e.subject, e.sender_email, e.recipient_emails,
                e.body_full, e.body_preview as body, e.date, e.folder,
                e.thread_id,
                ec.category, ec.ai_summary, ec.entities,
                ec.linked_project_code, ec.urgency_level
            FROM emails e
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE e.email_id = ?
        """, (email_id,), fetch_one=True)

        if not email:
            return None

        # Load thread context if thread_id exists
        thread_context = self._load_thread_context(email.get("thread_id"), email_id)
        if thread_context:
            email["thread_context"] = thread_context

        return email

    def _load_thread_context(self, thread_id: str, current_email_id: int) -> Optional[Dict[str, Any]]:
        """
        Load context from other emails in the same thread using ThreadContextService.

        This helps GPT understand:
        - Who else is involved in this conversation
        - What project this thread is about (if already linked)
        - The conversation history
        - Conversation state (waiting for us or them)
        """
        if not thread_id:
            return None

        # Use the dedicated thread context service
        full_context = self.thread_service.get_thread_context(current_email_id)

        if not full_context:
            return None

        # Format for GPT consumption (keep backward compatible structure)
        thread_info = full_context.get("thread_info", {})
        participants_data = full_context.get("participants", {})
        existing_links = full_context.get("existing_links", [])
        thread_emails = full_context.get("emails", [])
        conversation_state = full_context.get("conversation_state", {})

        # Extract participant emails
        all_participants = []
        for p in participants_data.get("internal", []):
            all_participants.append(p.get("email"))
        for p in participants_data.get("external", []):
            all_participants.append(p.get("email"))

        return {
            "thread_id": thread_id,
            "email_count": thread_info.get("total_emails", 1),
            "participants": all_participants,
            "emails": thread_emails,
            "existing_project_links": existing_links if existing_links else None,
            # New fields from enhanced service
            "conversation_state": conversation_state,
            "thread_starter": participants_data.get("thread_starter"),
            "external_participants": [p.get("email") for p in participants_data.get("external", [])],
        }

    def _get_unprocessed_emails(self, limit: int, hours_back: int) -> List[int]:
        """Get emails that haven't been processed with context-aware analysis"""
        emails = self.execute_query("""
            SELECT e.email_id
            FROM emails e
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE e.date >= datetime('now', '-' || ? || ' hours')
            AND NOT EXISTS (
                SELECT 1 FROM ai_suggestions s
                WHERE s.source_type = 'email'
                AND s.source_id = e.email_id
                AND s.suggested_data LIKE '%"match_type": "context_aware"%'
            )
            ORDER BY e.date DESC
            LIMIT ?
        """, (hours_back, limit))

        return [e["email_id"] for e in emails]

    def _log_usage(self, result: Dict[str, Any], email_ids: List[int]):
        """Log single request usage to database"""
        usage = result.get("usage", {})
        try:
            with self.get_connection() as conn:
                tracker = GPTUsageTracker(conn)
                tracker.log_usage(
                    request_type="suggestion_analysis",
                    model=usage.get("model", "gpt-4o-mini"),
                    input_tokens=usage.get("input_tokens", 0),
                    output_tokens=usage.get("output_tokens", 0),
                    estimated_cost=usage.get("estimated_cost_usd", 0),
                    email_ids=email_ids,
                    processing_time_ms=usage.get("processing_time_ms", 0),
                    success=result.get("success", False),
                    error_message=result.get("error"),
                )
        except Exception as e:
            logger.error(f"Failed to log usage: {e}")

    def _log_batch_usage(self, usage: Dict[str, Any], email_ids: List[int]):
        """Log batch usage to database"""
        try:
            with self.get_connection() as conn:
                tracker = GPTUsageTracker(conn)
                tracker.log_usage(
                    request_type="batch_suggestion_analysis",
                    model="gpt-4o-mini",
                    input_tokens=usage.get("input_tokens", 0),
                    output_tokens=usage.get("output_tokens", 0),
                    estimated_cost=usage.get("estimated_cost_usd", 0),
                    email_ids=email_ids,
                    processing_time_ms=usage.get("processing_time_ms", 0),
                    success=True,
                )
        except Exception as e:
            logger.error(f"Failed to log batch usage: {e}")

    def get_usage_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get usage statistics for the past N days"""
        stats = self.execute_query("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as requests,
                SUM(input_tokens) as input_tokens,
                SUM(output_tokens) as output_tokens,
                SUM(estimated_cost_usd) as cost_usd,
                SUM(batch_size) as emails_processed
            FROM gpt_usage_log
            WHERE created_at >= datetime('now', '-' || ? || ' days')
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, (days,))

        total_cost = sum(s.get("cost_usd", 0) or 0 for s in stats)
        total_emails = sum(s.get("emails_processed", 0) or 0 for s in stats)
        total_requests = sum(s.get("requests", 0) or 0 for s in stats)

        return {
            "daily_stats": stats,
            "total_cost_usd": round(total_cost, 4),
            "total_emails_processed": total_emails,
            "total_requests": total_requests,
            "avg_cost_per_email": round(total_cost / total_emails, 6) if total_emails > 0 else 0,
        }

    def get_context_stats(self) -> Dict[str, Any]:
        """Get statistics about the current context bundle"""
        return self.bundler.get_stats()

    def refresh_context(self) -> Dict[str, Any]:
        """Force refresh the context bundle cache"""
        bundle = self.bundler.get_bundle(force_refresh=True)
        return {
            "success": True,
            "estimated_tokens": bundle.get("estimated_tokens"),
            "proposal_count": len(bundle.get("active_proposals", [])),
            "pattern_count": len(bundle.get("learned_patterns", [])),
        }


# Singleton instance
_service_instance: Optional[ContextAwareSuggestionService] = None


def get_context_aware_service(db_path: str = None) -> ContextAwareSuggestionService:
    """Get or create the singleton service instance"""
    global _service_instance

    if _service_instance is None:
        _service_instance = ContextAwareSuggestionService(db_path)

    return _service_instance
