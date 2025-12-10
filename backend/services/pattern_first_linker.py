"""
Pattern-First Email Linker

NEW APPROACH (Dec 2025):
1. Check patterns FIRST (sender, domain, thread, keywords)
2. Auto-link if confident match found - NO GPT call
3. Only call GPT for truly unknown emails (~20%)
4. ONE review queue for uncertain links
5. Learning that actually prevents repeat mistakes

This replaces the overcomplicated context_aware_suggestion_service.
"""

import os
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_service import BaseService

logger = logging.getLogger(__name__)


def extract_email_address(sender: str) -> str:
    """
    Extract just the email address from sender field.
    Handles formats like:
    - "John Doe" <john@example.com>
    - john@example.com
    - John Doe <john@example.com>
    """
    if not sender:
        return ""

    # Try to extract from angle brackets
    match = re.search(r'<([^>]+@[^>]+)>', sender)
    if match:
        return match.group(1).lower().strip()

    # Try to find email directly
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', sender)
    if match:
        return match.group(0).lower().strip()

    return sender.lower().strip()


class PatternFirstLinker(BaseService):
    """
    Links emails to projects using pattern matching FIRST, GPT only when needed.

    Priority order:
    1. Thread inheritance - if other emails in thread are linked, inherit
    2. Sender exact match - sender@domain.com → project
    3. Domain match - @company.com → project
    4. Keyword match - subject/body contains keyword → project
    5. GPT analysis - only for truly unknown emails
    """

    # Internal category IDs
    INT_OPS = 2      # NaviWorld, D365, BOS, scheduling
    INT_LEGAL = 3    # Legal, NDA, contracts
    INT_FINANCE = 4  # Invoices, payments
    INT_HR = 5       # HR stuff

    def __init__(self, db_path: str = None):
        super().__init__(db_path)
        self._patterns_cache = None
        self._patterns_loaded_at = None
        self._cache_ttl_seconds = 300  # 5 min cache

    def _load_patterns(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Load all active patterns from database, with caching"""
        now = datetime.now()

        if (not force_refresh and
            self._patterns_cache and
            self._patterns_loaded_at and
            (now - self._patterns_loaded_at).seconds < self._cache_ttl_seconds):
            return self._patterns_cache

        patterns = {
            "sender_to_proposal": {},
            "sender_to_project": {},
            "sender_to_internal": {},
            "domain_to_proposal": {},
            "domain_to_project": {},
            "domain_to_internal": {},
            "keyword_to_proposal": {},
            "keyword_to_project": {},
            "keyword_to_internal": {},
        }

        rows = self.execute_query("""
            SELECT pattern_type, pattern_key, pattern_key_normalized,
                   target_type, target_id, target_code, target_name, confidence
            FROM email_learned_patterns
            WHERE is_active = 1 AND confidence >= 0.7
            ORDER BY confidence DESC
        """)

        for row in rows:
            ptype = row["pattern_type"]
            key = (row.get("pattern_key_normalized") or row["pattern_key"]).lower()

            if ptype in patterns:
                patterns[ptype][key] = {
                    "target_type": row["target_type"],
                    "target_id": row["target_id"],
                    "target_code": row["target_code"],
                    "target_name": row["target_name"],
                    "confidence": row["confidence"],
                }

        self._patterns_cache = patterns
        self._patterns_loaded_at = now

        logger.info(f"Loaded patterns: {sum(len(v) for v in patterns.values())} total")
        return patterns

    def _check_thread_inheritance(self, email: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check if other emails in this thread are already linked"""
        thread_id = email.get("thread_id")
        if not thread_id:
            return None

        # Find existing links in this thread
        links = self.execute_query("""
            SELECT DISTINCT
                COALESCE(epl.proposal_id, eprl.project_id) as target_id,
                CASE WHEN epl.proposal_id IS NOT NULL THEN 'proposal' ELSE 'project' END as target_type,
                COALESCE(p.project_code, pr.project_code) as target_code,
                COALESCE(p.project_name, pr.project_title) as target_name,
                COUNT(*) as link_count
            FROM emails e
            LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
            LEFT JOIN email_project_links eprl ON e.email_id = eprl.email_id
            LEFT JOIN proposals p ON epl.proposal_id = p.proposal_id
            LEFT JOIN projects pr ON eprl.project_id = pr.project_id
            WHERE e.thread_id = ?
            AND e.email_id != ?
            AND (epl.proposal_id IS NOT NULL OR eprl.project_id IS NOT NULL)
            GROUP BY target_id, target_type
            ORDER BY link_count DESC
            LIMIT 1
        """, (thread_id, email.get("email_id")))

        if links:
            link = links[0]
            return {
                "match_type": "thread_inheritance",
                "target_type": link["target_type"],
                "target_id": link["target_id"],
                "target_code": link["target_code"],
                "target_name": link["target_name"],
                "confidence": 0.95,
                "reason": f"Thread already linked ({link['link_count']} emails)",
            }
        return None

    def _check_sender_pattern(self, email: Dict[str, Any], patterns: Dict) -> Optional[Dict[str, Any]]:
        """Check if sender matches a known pattern"""
        raw_sender = email.get("sender_email") or ""
        sender = extract_email_address(raw_sender)
        if not sender:
            return None

        # Exact sender match
        for ptype in ["sender_to_proposal", "sender_to_project", "sender_to_internal"]:
            if sender in patterns.get(ptype, {}):
                match = patterns[ptype][sender]
                return {
                    "match_type": ptype,
                    "target_type": match["target_type"],
                    "target_id": match["target_id"],
                    "target_code": match["target_code"],
                    "target_name": match["target_name"],
                    "confidence": match["confidence"],
                    "reason": f"Sender pattern: {sender}",
                }
        return None

    def _check_domain_pattern(self, email: Dict[str, Any], patterns: Dict) -> Optional[Dict[str, Any]]:
        """Check if sender domain matches a known pattern"""
        raw_sender = email.get("sender_email") or ""
        sender = extract_email_address(raw_sender)
        if "@" not in sender:
            return None

        domain = sender.split("@")[1]

        # Skip internal domains
        if domain in ["bensley.com", "bensleydesign.com", "bensley.co.th", "bensley.co.id"]:
            return None

        for ptype in ["domain_to_proposal", "domain_to_project", "domain_to_internal"]:
            if domain in patterns.get(ptype, {}):
                match = patterns[ptype][domain]
                return {
                    "match_type": ptype,
                    "target_type": match["target_type"],
                    "target_id": match["target_id"],
                    "target_code": match["target_code"],
                    "target_name": match["target_name"],
                    "confidence": match["confidence"],
                    "reason": f"Domain pattern: @{domain}",
                }
        return None

    def _check_keyword_pattern(self, email: Dict[str, Any], patterns: Dict) -> Optional[Dict[str, Any]]:
        """Check if subject/body contains known keywords"""
        subject = (email.get("subject") or "").lower()
        body = (email.get("body_full") or email.get("body") or "")[:1000].lower()
        text = f"{subject} {body}"

        for ptype in ["keyword_to_proposal", "keyword_to_project", "keyword_to_internal"]:
            for keyword, match in patterns.get(ptype, {}).items():
                if keyword in text:
                    return {
                        "match_type": ptype,
                        "target_type": match["target_type"],
                        "target_id": match["target_id"],
                        "target_code": match["target_code"],
                        "target_name": match["target_name"],
                        "confidence": match["confidence"],
                        "reason": f"Keyword pattern: '{keyword}'",
                    }
        return None

    def _is_internal_email(self, email: Dict[str, Any]) -> bool:
        """Check if email is internal (Bensley to Bensley)"""
        raw_sender = email.get("sender_email") or ""
        sender = extract_email_address(raw_sender)
        recipients = (email.get("recipient_emails") or "").lower()

        internal_domains = ["bensley.com", "bensleydesign.com", "bensley.co.th", "bensley.co.id"]

        sender_domain = sender.split("@")[1] if "@" in sender else ""
        sender_internal = sender_domain in internal_domains

        # If sender is internal, check if ALL recipients are also internal
        if sender_internal and recipients:
            # Extract all recipient emails and check their domains
            recipient_emails = [extract_email_address(r) for r in recipients.split(",") if "@" in r]
            all_internal = all(
                (r.split("@")[1] if "@" in r else "") in internal_domains
                for r in recipient_emails
            )
            if all_internal:
                return True  # Fully internal circulation

        return False

    def _is_spam_or_noise(self, email: Dict[str, Any]) -> Optional[str]:
        """Check if email is spam/noise that should be skipped"""
        raw_sender = email.get("sender_email") or ""
        sender = extract_email_address(raw_sender)
        subject = (email.get("subject") or "").lower()
        domain = sender.split("@")[1] if "@" in sender else ""

        # Spam sender patterns (in email address)
        spam_senders = [
            "noreply@", "no-reply@", "notifications@", "newsletter@",
            "marketing@", "info@zoom", "teamzoom@", "atlassian",
            "microsoft notifications", "verification", "promo@",
            "mailer-daemon", "postmaster@"
        ]
        for pattern in spam_senders:
            if pattern in sender:
                return f"Spam sender: {pattern}"

        # Spam domains (marketing/saas tools)
        spam_domains = [
            "pipedrive.com", "monday.com", "mail.monday.com",
            "hubspot.com", "mailchimp.com", "sendgrid.net",
            "dropbox.com", "em-s.dropbox.com",
            "bqe.com", "accelo.com", "asana.com",
            "slack.com", "trello.com", "notion.so",
            "zoom.us", "e.zoom.us",
            "ghost.io",  # newsletters
            "substack.com",
            "e.atlassian.com", "id.atlassian.com",
            "email.microsoft.com",
            "ansmtp.ariba.com",  # SAP
            "pandadoc.net",  # unless it's a real signing request for a project
        ]
        for spam_domain in spam_domains:
            if domain.endswith(spam_domain):
                return f"Spam domain: {spam_domain}"

        # Spam subject patterns
        spam_subjects = [
            "unsubscribe", "verification code", "verify your",
            "password reset", "your order", "delivery notification",
            "out of office", "automatic reply", "welcome to",
            "webinar", "free trial", "schedule a demo",
        ]
        for pattern in spam_subjects:
            if pattern in subject:
                return f"Spam subject: {pattern}"

        return None

    def link_email(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Try to link a single email using pattern matching.

        Returns:
            {
                "linked": True/False,
                "method": "thread_inheritance" | "sender_pattern" | "domain_pattern" | "keyword_pattern" | "needs_gpt",
                "target_type": "proposal" | "project" | "internal" | None,
                "target_id": int | None,
                "target_code": str | None,
                "target_name": str | None,
                "confidence": float,
                "reason": str,
            }
        """
        email_id = email.get("email_id")

        # Skip spam/noise only (external marketing, newsletters, etc.)
        spam_reason = self._is_spam_or_noise(email)
        if spam_reason:
            return {
                "linked": False,
                "method": "skip_spam",
                "reason": spam_reason,
                "email_id": email_id,
            }

        # NOTE: Internal emails are NOT auto-skipped anymore.
        # - Project-related internal emails go to GPT for linking
        # - Admin internal emails (financials, proposal list) get categorized
        #   as INT-OPS, INT-FIN etc. by GPT

        # NEW: Check if this is a SENT email (from @bensley.com to external)
        # Use sent_email_linker to match via recipient instead of sender
        raw_sender = email.get("sender_email") or ""
        sender = extract_email_address(raw_sender)
        sender_domain = sender.split("@")[1] if "@" in sender else ""

        if sender_domain in ["bensley.com", "bensleydesign.com", "bensley.co.th", "bensley.co.id"]:
            # Check if there are external recipients
            recipients = (email.get("recipient_emails") or "").lower()
            has_external = any(
                r and "@" in r and r.split("@")[1] not in
                ["bensley.com", "bensleydesign.com", "bensley.co.th", "bensley.co.id"]
                for r in [extract_email_address(r.strip()) for r in recipients.split(",")]
            )

            if has_external:
                # Use sent email linker for outbound emails
                from .sent_email_linker import SentEmailLinker
                sent_linker = SentEmailLinker(self.db_path)
                sent_result = sent_linker.link_sent_email(email)

                if sent_result.get("linked"):
                    return {
                        "linked": True,
                        "method": "sent_email_recipient",
                        "email_id": email_id,
                        "target_type": sent_result.get("target_type"),
                        "target_id": sent_result.get("target_id"),
                        "target_code": sent_result.get("target_code"),
                        "target_name": sent_result.get("target_name"),
                        "confidence": sent_result.get("confidence"),
                        "reason": sent_result.get("reason"),
                        "match_type": sent_result.get("match_type"),
                    }
                elif sent_result.get("method") == "needs_review":
                    # Pass through the suggestion
                    return {
                        "linked": False,
                        "method": "sent_needs_review",
                        "email_id": email_id,
                        "suggested_match": sent_result.get("suggested_match"),
                        "recipients": sent_result.get("recipients"),
                        "reason": "Sent email - recipient domain match needs review",
                    }
                # If no_external_recipients or no_match, continue with normal flow

        patterns = self._load_patterns()

        # Priority 1: Thread inheritance
        match = self._check_thread_inheritance(email)
        if match:
            return {
                "linked": True,
                "method": "thread_inheritance",
                "email_id": email_id,
                **match,
            }

        # Priority 2: Sender exact match
        match = self._check_sender_pattern(email, patterns)
        if match:
            return {
                "linked": True,
                "method": "sender_pattern",
                "email_id": email_id,
                **match,
            }

        # Priority 3: Domain match
        match = self._check_domain_pattern(email, patterns)
        if match:
            return {
                "linked": True,
                "method": "domain_pattern",
                "email_id": email_id,
                **match,
            }

        # Priority 4: Keyword match
        match = self._check_keyword_pattern(email, patterns)
        if match:
            return {
                "linked": True,
                "method": "keyword_pattern",
                "email_id": email_id,
                **match,
            }

        # No pattern match - needs GPT
        return {
            "linked": False,
            "method": "needs_gpt",
            "reason": "No pattern match found",
            "email_id": email_id,
        }

    def apply_link(self, email_id: int, target_type: str, target_id: int,
                   confidence: float, match_type: str) -> bool:
        """Apply a link to the database"""
        try:
            if target_type == "proposal":
                self.execute_update("""
                    INSERT OR IGNORE INTO email_proposal_links
                    (email_id, proposal_id, confidence_score, match_method, created_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                """, (email_id, target_id, confidence, match_type))
            elif target_type == "project":
                self.execute_update("""
                    INSERT OR IGNORE INTO email_project_links
                    (email_id, project_id, confidence_score, match_method, created_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                """, (email_id, target_id, confidence, match_type))
            return True
        except Exception as e:
            logger.error(f"Failed to apply link: {e}")
            return False

    def learn_from_correction(self, email_id: int, correct_target_type: str,
                              correct_target_id: int, correct_target_code: str,
                              correct_target_name: str) -> Dict[str, Any]:
        """
        Learn a pattern from a user correction.
        Creates sender pattern so same mistake won't happen again.
        """
        # Get email details
        email = self.execute_query("""
            SELECT sender_email, subject FROM emails WHERE email_id = ?
        """, (email_id,), fetch_one=True)

        if not email:
            return {"success": False, "error": "Email not found"}

        sender = extract_email_address(email["sender_email"])
        domain = sender.split("@")[1] if "@" in sender else None

        patterns_created = []

        # Create sender pattern
        pattern_type = f"sender_to_{correct_target_type}"
        try:
            self.execute_update("""
                INSERT INTO email_learned_patterns
                (pattern_type, pattern_key, pattern_key_normalized, target_type,
                 target_id, target_code, target_name, confidence,
                 created_from_email_id, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0.95, ?, 'Learned from correction', datetime('now'))
                ON CONFLICT(pattern_type, pattern_key) DO UPDATE SET
                    target_id = excluded.target_id,
                    target_code = excluded.target_code,
                    target_name = excluded.target_name,
                    confidence = 0.95,
                    updated_at = datetime('now')
            """, (pattern_type, sender, sender, correct_target_type,
                  correct_target_id, correct_target_code, correct_target_name, email_id))
            patterns_created.append(f"{pattern_type}: {sender}")
        except Exception as e:
            logger.error(f"Failed to create sender pattern: {e}")

        # Invalidate cache
        self._patterns_cache = None

        return {
            "success": True,
            "patterns_created": patterns_created,
            "message": f"Learned: {sender} → {correct_target_code}",
        }

    def process_batch(self, email_ids: List[int] = None, limit: int = 100) -> Dict[str, Any]:
        """
        Process a batch of emails with pattern-first approach.

        Returns stats on:
        - How many auto-linked (no GPT needed)
        - How many need GPT analysis
        - How many skipped (spam, internal)
        """
        # Get emails
        if email_ids:
            placeholders = ",".join("?" * len(email_ids))
            emails = self.execute_query(f"""
                SELECT email_id, sender_email, recipient_emails, subject,
                       body_full, body_preview as body, date, folder, thread_id
                FROM emails WHERE email_id IN ({placeholders})
            """, tuple(email_ids))
        else:
            emails = self.execute_query("""
                SELECT email_id, sender_email, recipient_emails, subject,
                       body_full, body_preview as body, date, folder, thread_id
                FROM emails e
                WHERE NOT EXISTS (
                    SELECT 1 FROM email_proposal_links epl WHERE epl.email_id = e.email_id
                )
                AND NOT EXISTS (
                    SELECT 1 FROM email_project_links eprl WHERE eprl.email_id = e.email_id
                )
                AND date LIKE '2025-%'
                ORDER BY date ASC
                LIMIT ?
            """, (limit,))

        results = {
            "total": len(emails),
            "auto_linked": 0,
            "needs_gpt": 0,
            "skipped_spam": 0,
            "links_applied": 0,
            "needs_gpt_ids": [],
        }

        for email in emails:
            result = self.link_email(dict(email))

            if result.get("linked"):
                results["auto_linked"] += 1
                # Apply the link
                if self.apply_link(
                    email["email_id"],
                    result["target_type"],
                    result["target_id"],
                    result["confidence"],
                    result["match_type"]
                ):
                    results["links_applied"] += 1

            elif result.get("method") == "needs_gpt":
                results["needs_gpt"] += 1
                results["needs_gpt_ids"].append(email["email_id"])

            elif result.get("method") == "skip_spam":
                results["skipped_spam"] += 1

        return results

    def create_review_suggestions(self, email_ids: List[int],
                                   gpt_results: List[Dict[str, Any]]) -> int:
        """
        Create review suggestions for GPT-analyzed emails.
        ONE queue - just uncertain links that need human review.
        NOW STORES FULL CONTEXT for the reviewer.
        """
        import json
        suggestions_created = 0

        # Pre-load email data for context
        if not email_ids:
            return 0

        placeholders = ",".join("?" * len(email_ids))
        emails_data = self.execute_query(f"""
            SELECT email_id, sender_email, sender_name, recipient_emails,
                   subject, SUBSTR(body_full, 1, 500) as body_preview,
                   date, folder, email_direction, is_purely_internal
            FROM emails WHERE email_id IN ({placeholders})
        """, tuple(email_ids))

        email_map = {e["email_id"]: dict(e) for e in emails_data}

        for email_id, result in zip(email_ids, gpt_results):
            if not result.get("success"):
                continue

            analysis = result.get("analysis", {})
            links = analysis.get("email_links", [])
            classification = analysis.get("email_classification", {})

            email_data = email_map.get(email_id, {})

            for link in links:
                if link.get("confidence", 0) < 0.4:
                    continue  # Lowered threshold - human reviews everything

                # Look up proposal/project ID and name
                code = link.get("project_code")
                target_id = None
                target_type = None
                target_name = link.get("project_name")

                proposal = self.execute_query("""
                    SELECT proposal_id, project_name FROM proposals WHERE project_code = ?
                """, (code,), fetch_one=True)

                if proposal:
                    target_id = proposal["proposal_id"]
                    target_type = "proposal"
                    target_name = target_name or proposal["project_name"]
                else:
                    project = self.execute_query("""
                        SELECT project_id, project_title as project_name FROM projects WHERE project_code = ?
                    """, (code,), fetch_one=True)
                    if project:
                        target_id = project["project_id"]
                        target_type = "project"
                        target_name = target_name or project["project_name"]

                if not target_id:
                    continue

                # Build FULL context for review
                suggested_data = {
                    # Email context
                    "email_id": email_id,
                    "subject": email_data.get("subject"),
                    "sender_email": email_data.get("sender_email"),
                    "sender_name": email_data.get("sender_name"),
                    "recipients": email_data.get("recipient_emails"),
                    "date": email_data.get("date"),
                    "body_preview": email_data.get("body_preview"),
                    "email_direction": email_data.get("email_direction") or classification.get("direction"),

                    # GPT analysis
                    "project_code": code,
                    "project_name": target_name,
                    f"{target_type}_id": target_id,
                    "gpt_confidence": link.get("confidence"),
                    "gpt_reasoning": link.get("reasoning"),
                    "gpt_evidence": link.get("evidence", []),
                    "is_primary": link.get("is_primary", True),

                    # Classification context
                    "email_type": classification.get("type"),
                    "classification_reasoning": classification.get("reasoning"),
                    "is_project_related": classification.get("is_project_related"),
                }

                # Create review suggestion with full context
                self.execute_update("""
                    INSERT INTO ai_suggestions
                    (source_type, source_id, suggestion_type, title, description,
                     suggested_data, confidence_score, project_code, proposal_id,
                     status, created_at)
                    VALUES ('email', ?, 'email_link', ?, ?, ?, ?, ?, ?, 'pending', datetime('now'))
                """, (
                    email_id,
                    f"Link to {code} ({target_name})",
                    link.get("reasoning", "GPT suggested link"),
                    json.dumps(suggested_data),
                    link.get("confidence", 0.5),
                    code,
                    target_id if target_type == "proposal" else None,
                ))
                suggestions_created += 1

        return suggestions_created


# Singleton
_linker_instance = None

def get_pattern_linker(db_path: str = None) -> PatternFirstLinker:
    global _linker_instance
    if _linker_instance is None:
        _linker_instance = PatternFirstLinker(db_path)
    return _linker_instance
