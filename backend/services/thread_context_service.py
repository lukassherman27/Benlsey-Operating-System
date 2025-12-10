"""
Thread Context Service

Provides thread-level intelligence for email analysis.
Groups emails by thread_id and analyzes conversations as units.

Key capabilities:
- Get full thread context for an email
- Find existing proposal/project links in a thread
- Identify thread participants and their roles
- Determine conversation state (waiting for us vs them)

Part of Phase 1.5: Email Threading (Task 10)
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_service import BaseService

logger = logging.getLogger(__name__)


class ThreadContextService(BaseService):
    """
    Service for analyzing email threads and building context.

    Used by:
    - GPT analyzer to understand conversation context
    - Suggestion service to inherit links from thread
    - Admin UI to display thread details
    """

    def get_thread_context(self, email_id: int) -> Optional[Dict[str, Any]]:
        """
        Get full thread context for a specific email.

        Args:
            email_id: The email to get context for

        Returns:
            Dict with thread info, or None if email has no thread_id
        """
        # Get the email's thread_id
        email = self.execute_query("""
            SELECT email_id, thread_id, sender_email, subject, date
            FROM emails
            WHERE email_id = ?
        """, (email_id,), fetch_one=True)

        if not email or not email.get("thread_id"):
            return None

        thread_id = email["thread_id"]

        # Build comprehensive thread context
        return {
            "thread_id": thread_id,
            "current_email_id": email_id,
            "thread_info": self._get_thread_info(thread_id, email_id),
            "existing_links": self.get_thread_links(thread_id),
            "participants": self.get_thread_participants(thread_id),
            "emails": self._get_thread_emails(thread_id, email_id),
            "conversation_state": self._analyze_conversation_state(thread_id, email_id),
        }

    def get_thread_links(self, thread_id: str) -> List[Dict[str, Any]]:
        """
        Get all proposal/project links for emails in this thread.

        Args:
            thread_id: The thread to check

        Returns:
            List of links with project codes and names
        """
        # Get proposal links
        proposal_links = self.execute_query("""
            SELECT DISTINCT
                p.project_code,
                p.project_name,
                p.status as proposal_status,
                COUNT(DISTINCT epl.email_id) as linked_email_count,
                MAX(epl.confidence_score) as max_confidence,
                'proposal' as link_type
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            JOIN proposals p ON epl.proposal_id = p.proposal_id
            WHERE e.thread_id = ?
            GROUP BY p.project_code, p.project_name, p.status
            ORDER BY linked_email_count DESC
        """, (thread_id,))

        # Get project links
        project_links = self.execute_query("""
            SELECT DISTINCT
                pr.project_code,
                pr.project_title as project_name,
                pr.status as project_status,
                COUNT(DISTINCT epl.email_id) as linked_email_count,
                MAX(epl.confidence) as max_confidence,
                'project' as link_type
            FROM emails e
            JOIN email_project_links epl ON e.email_id = epl.email_id
            JOIN projects pr ON epl.project_id = pr.project_id
            WHERE e.thread_id = ?
            GROUP BY pr.project_code, pr.project_title, pr.status
            ORDER BY linked_email_count DESC
        """, (thread_id,))

        return proposal_links + project_links

    def get_thread_participants(self, thread_id: str) -> Dict[str, Any]:
        """
        Get all participants in a thread with their roles.

        Args:
            thread_id: The thread to analyze

        Returns:
            Dict with categorized participants
        """
        # Get all senders
        senders = self.execute_query("""
            SELECT DISTINCT
                sender_email,
                sender_name,
                COUNT(*) as email_count,
                MIN(date) as first_email,
                MAX(date) as last_email
            FROM emails
            WHERE thread_id = ?
            AND sender_email IS NOT NULL
            GROUP BY sender_email, sender_name
            ORDER BY email_count DESC
        """, (thread_id,))

        # Categorize participants
        internal = []
        external = []

        bensley_domains = ['@bensley.com', '@bensleydesign.com', '@bensley.co.th', '@bensley.id']

        for sender in senders:
            email = sender.get("sender_email", "").lower()
            is_internal = any(domain in email for domain in bensley_domains)

            participant = {
                "email": sender.get("sender_email"),
                "name": sender.get("sender_name"),
                "email_count": sender.get("email_count"),
                "first_email": sender.get("first_email"),
                "last_email": sender.get("last_email"),
            }

            if is_internal:
                internal.append(participant)
            else:
                external.append(participant)

        # Get thread starter (first email sender)
        thread_starter = self.execute_query("""
            SELECT sender_email, sender_name, date
            FROM emails
            WHERE thread_id = ?
            ORDER BY date ASC
            LIMIT 1
        """, (thread_id,), fetch_one=True)

        # Get email direction stats
        direction_stats = self._get_email_direction_stats(thread_id)

        return {
            "total_participants": len(senders),
            "internal": internal,
            "external": external,
            "thread_starter": thread_starter,
            "email_directions": direction_stats,
        }

    def _get_email_direction_stats(self, thread_id: str) -> Dict[str, int]:
        """
        Analyze email directions in thread.

        Categories:
        - external_to_internal: Client emails to us (most important)
        - internal_to_external: Our responses to client
        - internal_to_internal: Internal discussion/forwarding (less relevant for linking)
        """
        bensley_domains = ['@bensley.com', '@bensleydesign.com', '@bensley.co.th', '@bensley.id']

        emails = self.execute_query("""
            SELECT sender_email, recipient_emails
            FROM emails
            WHERE thread_id = ?
        """, (thread_id,))

        stats = {
            "external_to_internal": 0,
            "internal_to_external": 0,
            "internal_to_internal": 0,
            "external_to_external": 0,  # rare, but possible
        }

        for email in emails:
            sender = (email.get("sender_email") or "").lower()
            recipients = (email.get("recipient_emails") or "").lower()

            sender_internal = any(domain in sender for domain in bensley_domains)

            # Check if ANY recipient is external
            recipient_has_external = not all(
                any(domain in part for domain in bensley_domains)
                for part in recipients.split(",") if "@" in part
            ) if recipients else False

            recipient_has_internal = any(domain in recipients for domain in bensley_domains)

            if sender_internal:
                if recipient_has_external:
                    stats["internal_to_external"] += 1
                else:
                    stats["internal_to_internal"] += 1
            else:
                if recipient_has_internal:
                    stats["external_to_internal"] += 1
                else:
                    stats["external_to_external"] += 1

        return stats

    def _get_thread_info(self, thread_id: str, current_email_id: int) -> Dict[str, Any]:
        """Get basic thread statistics"""
        stats = self.execute_query("""
            SELECT
                COUNT(*) as total_emails,
                MIN(date) as first_email_date,
                MAX(date) as last_email_date,
                COUNT(DISTINCT sender_email) as unique_senders
            FROM emails
            WHERE thread_id = ?
        """, (thread_id,), fetch_one=True)

        # Get common subject
        subject = self.execute_query("""
            SELECT subject FROM emails
            WHERE thread_id = ?
            ORDER BY date ASC
            LIMIT 1
        """, (thread_id,), fetch_one=True)

        return {
            "total_emails": stats.get("total_emails", 0) if stats else 0,
            "first_email_date": stats.get("first_email_date") if stats else None,
            "last_email_date": stats.get("last_email_date") if stats else None,
            "unique_senders": stats.get("unique_senders", 0) if stats else 0,
            "thread_subject": subject.get("subject") if subject else None,
        }

    def _get_thread_emails(
        self,
        thread_id: str,
        current_email_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get emails in thread (excluding current email).

        Returns most recent emails first, with snippets and direction info.
        """
        emails = self.execute_query("""
            SELECT
                e.email_id,
                e.sender_email,
                e.sender_name,
                e.recipient_emails,
                e.subject,
                e.date,
                substr(e.body_preview, 1, 200) as snippet,
                CASE WHEN epl.email_id IS NOT NULL THEN 1 ELSE 0 END as is_linked
            FROM emails e
            LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
            WHERE e.thread_id = ?
            AND e.email_id != ?
            ORDER BY e.date DESC
            LIMIT ?
        """, (thread_id, current_email_id, limit))

        # Add direction info to each email
        bensley_domains = ['@bensley.com', '@bensleydesign.com', '@bensley.co.th', '@bensley.id']

        for email in emails:
            sender = (email.get("sender_email") or "").lower()
            recipients = (email.get("recipient_emails") or "").lower()

            sender_internal = any(domain in sender for domain in bensley_domains)
            recipient_has_external = recipients and not all(
                any(domain in part for domain in bensley_domains)
                for part in recipients.split(",") if "@" in part
            )

            if sender_internal:
                if recipient_has_external:
                    email["direction"] = "internal_to_external"
                else:
                    email["direction"] = "internal_to_internal"
            else:
                email["direction"] = "external_to_internal"

        return emails

    def _analyze_conversation_state(
        self,
        thread_id: str,
        current_email_id: int
    ) -> Dict[str, Any]:
        """
        Analyze the state of the conversation.

        Determines:
        - Who sent the last email (us or them)?
        - Are we waiting for a response?
        - How long since last activity?
        """
        # Get the most recent email in thread
        last_email = self.execute_query("""
            SELECT email_id, sender_email, date, folder
            FROM emails
            WHERE thread_id = ?
            ORDER BY date DESC
            LIMIT 1
        """, (thread_id,), fetch_one=True)

        if not last_email:
            return {"status": "unknown"}

        sender = last_email.get("sender_email", "").lower()
        bensley_domains = ['@bensley.com', '@bensleydesign.com', '@bensley.co.th']

        is_from_us = any(domain in sender for domain in bensley_domains)

        # Calculate days since last email
        last_date_str = last_email.get("date")
        days_since_last = None
        if last_date_str:
            try:
                # Handle various date formats
                if "T" in str(last_date_str):
                    last_date = datetime.fromisoformat(str(last_date_str).replace("Z", "+00:00"))
                else:
                    last_date = datetime.strptime(str(last_date_str)[:19], "%Y-%m-%d %H:%M:%S")
                days_since_last = (datetime.now() - last_date.replace(tzinfo=None)).days
            except Exception:
                pass

        return {
            "last_email_from_us": is_from_us,
            "waiting_for": "their_response" if is_from_us else "our_response",
            "last_email_sender": last_email.get("sender_email"),
            "last_email_date": last_email.get("date"),
            "days_since_last_email": days_since_last,
            "needs_followup": days_since_last and days_since_last > 7 and is_from_us,
        }

    def get_thread_summary(self, thread_id: str) -> Dict[str, Any]:
        """
        Get a comprehensive summary of a thread.

        Used by the admin API endpoint.
        """
        thread_info = self._get_thread_info(thread_id, -1)
        participants = self.get_thread_participants(thread_id)
        links = self.get_thread_links(thread_id)
        emails = self._get_thread_emails(thread_id, -1, limit=50)
        conversation_state = self._analyze_conversation_state(thread_id, -1)

        return {
            "thread_id": thread_id,
            "info": thread_info,
            "participants": participants,
            "existing_links": links,
            "emails": emails,
            "conversation_state": conversation_state,
            "summary": {
                "total_emails": thread_info.get("total_emails", 0),
                "linked_to": [l.get("project_code") for l in links] if links else [],
                "external_participants": [p.get("email") for p in participants.get("external", [])],
                "status": conversation_state.get("waiting_for"),
            }
        }

    def suggest_link_from_thread(self, email_id: int) -> Optional[Dict[str, Any]]:
        """
        Suggest a project link based on other emails in the thread.

        If other emails in the thread are linked to a project,
        suggest linking this email to the same project.

        Returns:
            Dict with suggested project_code and confidence, or None
        """
        context = self.get_thread_context(email_id)
        if not context:
            return None

        links = context.get("existing_links", [])
        if not links:
            return None

        # Get the most common/confident link
        best_link = links[0]  # Already sorted by linked_email_count

        thread_info = context.get("thread_info", {})
        total_emails = thread_info.get("total_emails", 1)
        linked_count = best_link.get("linked_email_count", 0)

        # Calculate confidence based on how many thread emails are linked
        link_ratio = linked_count / total_emails if total_emails > 0 else 0
        base_confidence = best_link.get("max_confidence", 0.8)

        # Boost confidence if many emails in thread are linked
        if link_ratio > 0.5:
            confidence = min(0.95, base_confidence + 0.1)
        elif link_ratio > 0.25:
            confidence = base_confidence
        else:
            confidence = max(0.6, base_confidence - 0.1)

        return {
            "project_code": best_link.get("project_code"),
            "project_name": best_link.get("project_name"),
            "confidence": confidence,
            "reason": f"{linked_count} of {total_emails} emails in thread linked to this project",
            "link_type": best_link.get("link_type"),
        }


# Singleton instance
_service_instance: Optional[ThreadContextService] = None


def get_thread_context_service(db_path: str = None) -> ThreadContextService:
    """Get or create the singleton service instance"""
    global _service_instance

    if _service_instance is None:
        _service_instance = ThreadContextService(db_path)

    return _service_instance
