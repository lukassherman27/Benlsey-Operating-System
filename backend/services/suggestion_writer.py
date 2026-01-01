"""
Suggestion Writer Service

Maps GPT analysis output to ai_suggestions table format.
Creates properly structured suggestions ready for human review.

Part of Phase 2.0: Context-Aware AI Suggestions
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_service import BaseService

logger = logging.getLogger(__name__)


class SuggestionWriter(BaseService):
    """
    Converts GPT analysis results into ai_suggestions records.

    Handles mapping of:
    - email_links (multi-project) with classification
    - new_contact suggestions
    - status_update suggestions
    - stale_proposal suggestions
    - relationship_insight suggestions
    - conversation_state tracking
    """

    # Minimum confidence thresholds by type
    CONFIDENCE_THRESHOLDS = {
        "email_link": 0.6,
        "new_contact": 0.85,  # Raised from 0.7 - 16% approval rate was too noisy
        "status_update": 0.8,  # Higher threshold for status changes
        "stale_proposal": 0.5,  # Lower threshold for alerts
        "relationship_insight": 0.6,
        # NEW: Task/Meeting/Deliverable detection thresholds
        "action_item": 0.7,
        "meeting_detected": 0.75,
        "deadline_detected": 0.7,
        "commitment": 0.65,
    }

    # Valid email classification types
    VALID_EMAIL_TYPES = [
        "internal",
        "client_external",
        "operator_external",
        "developer_external",
        "consultant_external",
        "vendor_external",
        "spam",
        "administrative",
    ]

    def __init__(self, db_path: str = None):
        super().__init__(db_path)

    def _get_patterns_for_sender(self, sender_email: str) -> List[Dict[str, Any]]:
        """
        Look up learned patterns for a sender email.

        Checks both sender-specific patterns and domain patterns.
        Returns list of matching patterns sorted by confidence.
        """
        if not sender_email:
            return []

        # Properly extract email from RFC 5322 format like "Name" <email@domain.com>
        match = re.search(r'<([^>]+@[^>]+)>', sender_email)
        if match:
            clean_sender = match.group(1).lower().strip()
        elif '@' in sender_email:
            # Already just an email address
            clean_sender = sender_email.lower().strip()
        else:
            # No valid email found
            return []

        # Extract domain from email (without @ for flexible matching)
        domain = None
        domain_with_at = None
        if "@" in clean_sender:
            domain = clean_sender.split("@")[1]  # e.g., "bdlbali.com"
            domain_with_at = "@" + domain        # e.g., "@bdlbali.com"

        # Query for matching patterns - check both with and without @ prefix
        patterns = self.execute_query("""
            SELECT
                pattern_id, pattern_type, pattern_key_normalized,
                target_type, target_id, target_code, target_name,
                confidence, times_used, times_correct, times_rejected
            FROM email_learned_patterns
            WHERE is_active = 1
            AND confidence >= 0.6
            AND (
                (pattern_type IN ('sender_to_project', 'sender_to_proposal')
                 AND pattern_key_normalized = ?)
                OR
                (pattern_type IN ('domain_to_project', 'domain_to_proposal')
                 AND (pattern_key_normalized = ? OR pattern_key_normalized = ?))
            )
            ORDER BY confidence DESC, times_correct DESC
        """, (clean_sender, domain, domain_with_at))

        return patterns or []

    def _get_contact_context(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get contact context for an email address.

        Returns context including is_multi_project flag.
        """
        if not email:
            return None

        return self.execute_query("""
            SELECT
                context_id, email, role, relationship_type,
                is_multi_project, email_handling_preference,
                default_category, default_subcategory
            FROM contact_context
            WHERE email = ?
        """, (email,), fetch_one=True)

    def _record_pattern_usage(self, pattern_id: int, was_correct: bool = None) -> None:
        """
        Record that a pattern was used to boost a suggestion.

        Args:
            pattern_id: ID of the pattern used
            was_correct: If known, whether suggestion was approved (True) or rejected (False)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                if was_correct is None:
                    # Just record usage, don't know outcome yet
                    cursor.execute("""
                        UPDATE email_learned_patterns
                        SET times_used = times_used + 1,
                            last_used_at = datetime('now')
                        WHERE pattern_id = ?
                    """, (pattern_id,))
                elif was_correct:
                    # Pattern was correct - boost confidence
                    cursor.execute("""
                        UPDATE email_learned_patterns
                        SET times_correct = times_correct + 1,
                            confidence = CASE
                                WHEN times_correct + times_rejected >= 2 THEN
                                    CAST(times_correct + 1 AS REAL) / (times_correct + times_rejected + 2)
                                ELSE confidence
                            END
                        WHERE pattern_id = ?
                    """, (pattern_id,))
                else:
                    # Pattern was wrong - reduce confidence
                    cursor.execute("""
                        UPDATE email_learned_patterns
                        SET times_rejected = times_rejected + 1,
                            confidence = CASE
                                WHEN times_correct + times_rejected >= 2 THEN
                                    CAST(times_correct AS REAL) / (times_correct + times_rejected + 2)
                                ELSE confidence * 0.9
                            END
                        WHERE pattern_id = ?
                    """, (pattern_id,))

                conn.commit()
                logger.debug(f"Recorded pattern {pattern_id} usage (correct={was_correct})")

        except Exception as e:
            logger.error(f"Failed to record pattern usage: {e}")

    def write_suggestions_from_analysis(
        self,
        email_id: int,
        analysis: Dict[str, Any],
        email_data: Dict[str, Any] = None,
    ) -> List[int]:
        """
        Create suggestions from GPT analysis results.

        Args:
            email_id: ID of the analyzed email
            analysis: GPT analysis output (new format with email_links array)
            email_data: Original email data for reference

        Returns:
            List of created suggestion IDs
        """
        suggestion_ids = []

        # TRAINING MODE: Create review suggestion even for skipped emails
        # so user can validate what should/shouldn't be skipped
        if analysis.get("skip_reason"):
            logger.info(f"Creating review suggestion for email {email_id}: {analysis['skip_reason']}")
            # Still update email classification
            if analysis.get("email_classification"):
                self._update_email_classification(email_id, analysis["email_classification"])
            # Create a review suggestion instead of skipping entirely
            sid = self._write_email_review_suggestion(email_id, analysis, email_data)
            if sid:
                suggestion_ids.append(sid)
            return suggestion_ids

        # Process email classification first (updates emails table)
        if analysis.get("email_classification"):
            self._update_email_classification(email_id, analysis["email_classification"])

        # Process email links (NEW: array of multiple projects)
        # Track the primary project_code for use in action_required suggestions
        primary_project_code = None
        email_links = analysis.get("email_links", [])
        if email_links:
            for link_data in email_links:
                sid = self._write_email_link_suggestion(email_id, link_data, email_data)
                if sid:
                    suggestion_ids.append(sid)
                # Track primary project code (first is_primary or highest confidence)
                if link_data.get("is_primary") and not primary_project_code:
                    primary_project_code = link_data.get("project_code")
            # Fallback: use first link's project_code if no primary found
            if not primary_project_code and email_links:
                primary_project_code = email_links[0].get("project_code")
        # Backwards compatibility: handle old single email_link format
        elif analysis.get("email_link"):
            sid = self._write_email_link_suggestion(email_id, analysis["email_link"], email_data)
            if sid:
                suggestion_ids.append(sid)
            primary_project_code = analysis["email_link"].get("project_code")

        # Process conversation state (NEW: tracks waiting_for, last_action)
        # Pass primary_project_code so action_required suggestions have context
        if analysis.get("conversation_state"):
            self._process_conversation_state(email_id, analysis["conversation_state"], email_data, primary_project_code)

        if analysis.get("new_contact"):
            sid = self._write_new_contact_suggestion(email_id, analysis["new_contact"], email_data)
            if sid:
                suggestion_ids.append(sid)

        if analysis.get("status_update"):
            sid = self._write_status_update_suggestion(email_id, analysis["status_update"], email_data)
            if sid:
                suggestion_ids.append(sid)

        if analysis.get("stale_proposal"):
            sid = self._write_stale_proposal_suggestion(email_id, analysis["stale_proposal"], email_data)
            if sid:
                suggestion_ids.append(sid)

        if analysis.get("relationship_insight"):
            sid = self._write_relationship_insight_suggestion(email_id, analysis["relationship_insight"], email_data)
            if sid:
                suggestion_ids.append(sid)

        # NEW: Suggest creating a new proposal if email is about unknown project
        if analysis.get("new_proposal"):
            sid = self._write_new_proposal_suggestion(email_id, analysis["new_proposal"], email_data)
            if sid:
                suggestion_ids.append(sid)

        # ==== NEW: Task/Meeting/Deliverable/Commitment Detection ====

        # Process action items (tasks detected from email)
        action_items = analysis.get("action_items", [])
        for action_item in action_items:
            sid = self._write_action_item_suggestion(email_id, action_item, email_data, primary_project_code)
            if sid:
                suggestion_ids.append(sid)

        # Process meeting detection
        meeting_detected = analysis.get("meeting_detected")
        if meeting_detected and meeting_detected.get("detected"):
            sid = self._write_meeting_suggestion(email_id, meeting_detected, email_data, primary_project_code)
            if sid:
                suggestion_ids.append(sid)

        # Process deliverables/deadlines
        deliverables = analysis.get("deliverables", [])
        for deliverable in deliverables:
            sid = self._write_deliverable_suggestion(email_id, deliverable, email_data, primary_project_code)
            if sid:
                suggestion_ids.append(sid)

        # Process commitments (promises made by us or them)
        commitments = analysis.get("commitments", [])
        for commitment in commitments:
            sid = self._write_commitment_suggestion(email_id, commitment, email_data, primary_project_code)
            if sid:
                suggestion_ids.append(sid)

        logger.info(f"Created {len(suggestion_ids)} suggestions for email {email_id}")
        return suggestion_ids

    def _update_email_classification(
        self,
        email_id: int,
        classification: Dict[str, Any],
    ) -> None:
        """
        Update email with classification data.

        Stores email type (internal/external/client/consultant/vendor)
        and is_project_related flag directly on the email record.
        """
        email_type = classification.get("type", "")
        is_project_related = classification.get("is_project_related", False)
        confidence = classification.get("confidence", 0)

        # Validate email type
        if email_type not in self.VALID_EMAIL_TYPES:
            logger.warning(f"Invalid email type '{email_type}' for email {email_id}")
            email_type = "administrative"  # Default fallback

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Update emails table with classification
                cursor.execute("""
                    UPDATE emails SET
                        email_type = ?,
                        is_project_related = ?,
                        classification_confidence = ?,
                        classification_reasoning = ?,
                        classified_at = datetime('now')
                    WHERE email_id = ?
                """, (
                    email_type,
                    1 if is_project_related else 0,
                    confidence,
                    classification.get("reasoning", ""),
                    email_id,
                ))
                conn.commit()
                logger.debug(f"Updated email {email_id} classification: {email_type}")

        except Exception as e:
            logger.error(f"Failed to update email classification: {e}")

    def _process_conversation_state(
        self,
        email_id: int,
        state_data: Dict[str, Any],
        email_data: Dict[str, Any] = None,
        project_code: str = None,
    ) -> None:
        """
        Process conversation state and potentially create action suggestions.

        Detects actionable states like:
        - waiting_for: our_response → We need to respond
        - next_action_needed → Specific action required

        Args:
            email_id: ID of the email
            state_data: Conversation state from GPT analysis
            email_data: Original email data
            project_code: Primary project code from email_links (if any)
        """
        waiting_for = state_data.get("waiting_for")
        next_action = state_data.get("next_action_needed")

        # Create action suggestion if we need to respond
        if waiting_for == "our_response" and next_action:
            subject = email_data.get("subject", "Unknown") if email_data else "Unknown"

            suggested_data = {
                "email_id": email_id,
                "waiting_for": waiting_for,
                "last_action": state_data.get("last_action"),
                "action_needed": next_action,
            }
            # Include project_code in suggested_data if available
            if project_code:
                suggested_data["project_code"] = project_code

            self._insert_suggestion(
                suggestion_type="action_required",
                priority="high",
                confidence_score=0.85,
                source_type="email",
                source_id=email_id,
                source_reference=f"Email: {subject[:50]}",
                title=f"Action needed: {next_action[:60]}",
                description=f"We need to respond. {next_action}",
                suggested_action="Complete action",
                suggested_data=suggested_data,
                target_table="tasks",
                project_code=project_code,
            )

    def _write_email_link_suggestion(
        self,
        email_id: int,
        link_data: Dict[str, Any],
        email_data: Dict[str, Any] = None,
    ) -> Optional[int]:
        """
        Create email_link suggestion.

        Handles both old format (should_link) and new format (is_primary).
        New format comes from email_links array, always create suggestion.

        LEARNING LOOP: If sender has a learned pattern matching this project,
        boost confidence by +0.2 and record pattern usage.
        """
        # Check old format first (backwards compatibility)
        if "should_link" in link_data and not link_data.get("should_link"):
            return None

        confidence = link_data.get("confidence", 0)
        project_code = link_data.get("project_code")
        if not project_code:
            return None

        # === CONTACT CONTEXT: Check if sender is multi-project ===
        sender_email = email_data.get("sender_email", "") if email_data else ""
        sender_clean = sender_email.lower().strip().replace("<", "").replace(">", "")

        # Check if this contact is marked as multi-project (don't suggest single-project links)
        contact_ctx = self._get_contact_context(sender_clean)
        if contact_ctx and contact_ctx.get("is_multi_project"):
            logger.debug(f"Skipping single-project suggestion for multi-project contact: {sender_clean}")
            return None

        # === LEARNING LOOP: Check for matching patterns ===
        pattern_matched = None
        pattern_boost = 0.0

        patterns = self._get_patterns_for_sender(sender_email)
        for pattern in patterns:
            if pattern.get("target_code") == project_code:
                # Pattern matches GPT suggestion - BOOST confidence!
                pattern_matched = pattern
                pattern_boost = 0.2  # +20% confidence boost
                logger.info(
                    f"Pattern match! Sender {sender_email} → {project_code} "
                    f"(pattern {pattern['pattern_id']}, conf +{pattern_boost})"
                )
                # Record that this pattern was used
                self._record_pattern_usage(pattern["pattern_id"])
                break

        # Apply boost and cap at 0.99
        boosted_confidence = min(0.99, confidence + pattern_boost)

        if boosted_confidence < self.CONFIDENCE_THRESHOLDS["email_link"]:
            logger.debug(f"Email link confidence {boosted_confidence} below threshold")
            return None

        # Look up proposal_id
        proposal = self.execute_query("""
            SELECT proposal_id, project_name FROM proposals WHERE project_code = ?
        """, (project_code,), fetch_one=True)

        if not proposal:
            logger.warning(f"Project code {project_code} not found in proposals")
            return None

        # Check for duplicate suggestion
        if self.check_duplicate_suggestion(email_id, "email_link", project_code):
            logger.debug(f"Duplicate email_link suggestion for email {email_id} → {project_code}")
            return None

        subject = email_data.get("subject", "Unknown") if email_data else "Unknown"
        is_primary = link_data.get("is_primary", True)

        suggested_data = {
            "email_id": email_id,
            "proposal_id": proposal["proposal_id"],
            "project_code": project_code,
            "project_name": proposal.get("project_name") or link_data.get("project_name"),
            "match_type": "context_aware",
            "is_primary_link": is_primary,
            "gpt_reasoning": link_data.get("reasoning"),
            # NEW: Track pattern matching for learning feedback
            "pattern_matched": pattern_matched["pattern_id"] if pattern_matched else None,
            "original_confidence": confidence,
            "boosted_confidence": boosted_confidence if pattern_matched else None,
        }

        # Priority based on confidence level and pattern match
        if boosted_confidence >= 0.9:
            priority = "high"
        elif is_primary:
            priority = "medium"
        else:
            priority = "low"

        # Enhanced description when pattern matched
        if pattern_matched:
            description = (
                f"GPT + learned pattern: {link_data.get('reasoning', '')} "
                f"[Pattern #{pattern_matched['pattern_id']} boosted conf {confidence:.2f}→{boosted_confidence:.2f}]"
            )
        else:
            description = link_data.get("reasoning", f"GPT suggests linking to {project_code}")

        return self._insert_suggestion(
            suggestion_type="email_link",
            priority=priority,
            confidence_score=boosted_confidence,
            source_type="email",
            source_id=email_id,
            source_reference=f"Email: {subject[:50]}",
            title=f"Link email to {project_code}" + (" (primary)" if is_primary else " (secondary)"),
            description=description,
            suggested_action="Create email_proposal_link",
            suggested_data=suggested_data,
            target_table="email_proposal_links",
            project_code=project_code,
        )

    def _write_new_contact_suggestion(
        self,
        email_id: int,
        contact_data: Dict[str, Any],
        email_data: Dict[str, Any] = None,
    ) -> Optional[int]:
        """Create new_contact suggestion"""
        if not contact_data.get("should_create"):
            return None

        confidence = contact_data.get("confidence", 0)
        if confidence < self.CONFIDENCE_THRESHOLDS["new_contact"]:
            return None

        email_addr = contact_data.get("email")
        name = contact_data.get("name")

        if not email_addr or not name:
            return None

        # Check if contact already exists
        existing = self.execute_query("""
            SELECT contact_id FROM contacts WHERE email = ?
        """, (email_addr,), fetch_one=True)

        if existing:
            logger.debug(f"Contact {email_addr} already exists")
            return None

        subject = email_data.get("subject", "Unknown") if email_data else "Unknown"

        suggested_data = {
            "name": name,
            "email": email_addr,
            "company": contact_data.get("inferred_company"),
            "role": contact_data.get("inferred_role"),
            "source": "email_import",
            "source_email_id": email_id,
        }

        return self._insert_suggestion(
            suggestion_type="new_contact",
            priority="medium",
            confidence_score=confidence,
            source_type="email",
            source_id=email_id,
            source_reference=f"Email: {subject[:50]}",
            title=f"New contact: {name}",
            description=f"Add contact from email. Company: {contact_data.get('inferred_company', 'Unknown')}",
            suggested_action="Add to contacts table",
            suggested_data=suggested_data,
            target_table="contacts",
            project_code=None,
        )

    def _write_new_proposal_suggestion(
        self,
        email_id: int,
        proposal_data: Dict[str, Any],
        email_data: Dict[str, Any] = None,
    ) -> Optional[int]:
        """
        Create new_proposal suggestion when email appears to be about
        a project that doesn't exist in our proposals table.
        """
        if not proposal_data.get("should_create"):
            return None

        confidence = proposal_data.get("confidence", 0)
        if confidence < 0.7:  # Require high confidence for new proposals
            return None

        suggested_name = proposal_data.get("suggested_name")
        if not suggested_name:
            return None

        subject = email_data.get("subject", "Unknown") if email_data else "Unknown"
        sender_email = email_data.get("sender_email", "") if email_data else ""

        suggested_data = {
            "suggested_name": suggested_name,
            "suggested_client": proposal_data.get("suggested_client"),
            "contact_name": proposal_data.get("contact_name"),
            "contact_email": proposal_data.get("contact_email") or sender_email,
            "location": proposal_data.get("location"),
            "project_type": proposal_data.get("project_type"),
            "reasoning": proposal_data.get("reasoning"),
            "source_email_id": email_id,
        }

        return self._insert_suggestion(
            suggestion_type="new_proposal",
            priority="high",
            confidence_score=confidence,
            source_type="email",
            source_id=email_id,
            source_reference=f"Email: {subject[:50]}",
            title=f"Create proposal: {suggested_name}",
            description=f"New project inquiry from {proposal_data.get('suggested_client', 'Unknown')}. {proposal_data.get('reasoning', '')}",
            suggested_action="Create new proposal entry",
            suggested_data=suggested_data,
            target_table="proposals",
            project_code=None,  # No code yet - will be assigned on approval
        )

    # Lifecycle stage ordering (status can only move forward, not backward)
    STATUS_STAGE_ORDER = {
        'inquiry': 1,
        'proposal': 1,  # legacy alias
        'meeting_scheduled': 2,
        'nda_signed': 3,
        'proposal_prep': 4,
        'submitted': 5,
        'proposal_sent': 5,  # legacy alias
        'negotiation': 6,
        'revision_requested': 7,
        'revised': 8,
        'won': 9,
        'active_project': 10,
        # Special statuses can be set from any stage 5+
        'on_hold': 100,
        'lost': 100,
        'cancelled': 100,
    }

    def _write_status_update_suggestion(
        self,
        email_id: int,
        status_data: Dict[str, Any],
        email_data: Dict[str, Any] = None,
    ) -> Optional[int]:
        """Create proposal_status_update suggestion (NEW TYPE)

        NOTE: This suggestion type is SUPPRESSED due to low approval rate (10%).
        The logic for detecting status changes was too aggressive and created
        many false positives. Re-enable when detection logic is improved.
        """
        # SUPPRESSED: proposal_status_update has 10% approval rate (26 approved, 152 rejected)
        # Too many false positives. Uncomment when detection logic is improved.
        logger.debug("proposal_status_update suggestions are suppressed due to low approval rate")
        return None

        if not status_data.get("should_update"):
            return None

        confidence = status_data.get("confidence", 0)
        if confidence < self.CONFIDENCE_THRESHOLDS["status_update"]:
            return None

        project_code = status_data.get("project_code")
        suggested_status = status_data.get("suggested_status")

        if not project_code or not suggested_status:
            return None

        # VALIDATION: Check current status from database and prevent backward moves
        current_status = self._get_current_proposal_status(project_code)
        if current_status:
            current_stage = self.STATUS_STAGE_ORDER.get(current_status, 0)
            suggested_stage = self.STATUS_STAGE_ORDER.get(suggested_status, 0)

            # Allow special statuses (on_hold, lost, cancelled) from stage 5+
            if suggested_stage == 100:
                if current_stage < 5:  # Can only go to on_hold/lost after submitted
                    logger.info(f"Blocking backward status: {project_code} cannot go to {suggested_status} from {current_status}")
                    return None
            elif suggested_stage <= current_stage:
                # Trying to go backwards - block this
                logger.info(f"Blocking backward status: {project_code} {current_status}(stage {current_stage}) → {suggested_status}(stage {suggested_stage})")
                return None

        subject = email_data.get("subject", "Unknown") if email_data else "Unknown"

        suggested_data = {
            "project_code": project_code,
            "current_status": current_status or status_data.get("current_status"),
            "suggested_status": suggested_status,
            "reasoning": status_data.get("reasoning"),
            "source_email_id": email_id,
        }

        return self._insert_suggestion(
            suggestion_type="proposal_status_update",
            priority="high",
            confidence_score=confidence,
            source_type="email",
            source_id=email_id,
            source_reference=f"Email: {subject[:50]}",
            title=f"Update {project_code} status to '{suggested_status}'",
            description=status_data.get("reasoning", "Status change detected in email"),
            suggested_action="Update proposal status",
            suggested_data=suggested_data,
            target_table="proposals",
            project_code=project_code,
        )

    def _get_current_proposal_status(self, project_code: str) -> Optional[str]:
        """Get the current status of a proposal from the database."""
        if not project_code:
            return None

        result = self.execute_query(
            "SELECT status FROM proposals WHERE project_code = ?",
            (project_code,),
            fetch_one=True
        )
        return result.get("status") if result else None

    def _write_stale_proposal_suggestion(
        self,
        email_id: int,
        stale_data: Dict[str, Any],
        email_data: Dict[str, Any] = None,
    ) -> Optional[int]:
        """Create stale_proposal suggestion (NEW TYPE)"""
        if not stale_data.get("is_stale"):
            return None

        project_code = stale_data.get("project_code")
        days_inactive = stale_data.get("days_inactive", 0)

        if not project_code or days_inactive < 14:  # Only flag if > 2 weeks
            return None

        subject = email_data.get("subject", "Unknown") if email_data else "Unknown"

        suggested_data = {
            "project_code": project_code,
            "days_inactive": days_inactive,
            "suggested_action": stale_data.get("suggested_action", "Follow up with client"),
            "detected_from_email_id": email_id,
        }

        # Priority based on inactivity
        priority = "high" if days_inactive > 30 else "medium"

        return self._insert_suggestion(
            suggestion_type="follow_up_needed",
            priority=priority,
            confidence_score=0.8,
            source_type="email",
            source_id=email_id,
            source_reference=f"Email: {subject[:50]}",
            title=f"Follow up on {project_code} ({days_inactive} days inactive)",
            description=f"Proposal has been inactive for {days_inactive} days. {stale_data.get('suggested_action', '')}",
            suggested_action="Create follow-up task",
            suggested_data=suggested_data,
            target_table="tasks",
            project_code=project_code,
        )

    def _write_relationship_insight_suggestion(
        self,
        email_id: int,
        insight_data: Dict[str, Any],
        email_data: Dict[str, Any] = None,
    ) -> Optional[int]:
        """Create relationship_insight suggestion (NEW TYPE - informational)"""
        if not insight_data.get("has_insight"):
            return None

        contact_email = insight_data.get("contact_email")
        insight = insight_data.get("insight")

        if not contact_email or not insight:
            return None

        subject = email_data.get("subject", "Unknown") if email_data else "Unknown"

        suggested_data = {
            "contact_email": contact_email,
            "insight": insight,
            "projects_involved": insight_data.get("projects_involved", []),
            "detected_from_email_id": email_id,
        }

        return self._insert_suggestion(
            suggestion_type="info",
            priority="low",
            confidence_score=0.7,
            source_type="email",
            source_id=email_id,
            source_reference=f"Email: {subject[:50]}",
            title=f"Contact insight: {contact_email}",
            description=insight,
            suggested_action="Review contact relationships",
            suggested_data=suggested_data,
            target_table=None,  # Informational, no DB change
            project_code=None,
        )

    def _write_email_review_suggestion(
        self,
        email_id: int,
        analysis: Dict[str, Any],
        email_data: Dict[str, Any] = None,
    ) -> Optional[int]:
        """
        Create an email_review suggestion for emails GPT wanted to skip.
        This is TRAINING MODE - lets user validate what should/shouldn't be skipped.
        """
        subject = email_data.get("subject", "Unknown") if email_data else "Unknown"
        skip_reason = analysis.get("skip_reason", "Unknown reason")
        classification = analysis.get("email_classification", {})

        suggested_data = {
            "skip_reason": skip_reason,
            "classification": classification,
            "ai_recommendation": "skip",
            "source_email_id": email_id,
        }

        # Determine category from classification
        email_type = classification.get("type", "unknown")

        return self._insert_suggestion(
            suggestion_type="email_review",
            priority="low",
            confidence_score=0.5,  # Low confidence - needs human review
            source_type="email",
            source_id=email_id,
            source_reference=f"Email: {subject[:50]}",
            title=f"Review: {email_type} - {subject[:40]}",
            description=f"AI suggests skipping: {skip_reason}",
            suggested_action="Confirm skip or link to project",
            suggested_data=suggested_data,
            target_table=None,
            project_code=None,
        )

    def _insert_suggestion(
        self,
        suggestion_type: str,
        priority: str,
        confidence_score: float,
        source_type: str,
        source_id: int,
        source_reference: str,
        title: str,
        description: str,
        suggested_action: str,
        suggested_data: Dict[str, Any],
        target_table: Optional[str],
        project_code: Optional[str],
    ) -> Optional[int]:
        """Insert a suggestion into ai_suggestions table"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ai_suggestions (
                        suggestion_type, priority, confidence_score,
                        source_type, source_id, source_reference,
                        title, description, suggested_action,
                        suggested_data, target_table, project_code,
                        status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', datetime('now'))
                """, (
                    suggestion_type,
                    priority,
                    confidence_score,
                    source_type,
                    source_id,
                    source_reference,
                    title,
                    description,
                    suggested_action,
                    json.dumps(suggested_data),
                    target_table,
                    project_code,
                ))
                conn.commit()
                suggestion_id = cursor.lastrowid
                logger.debug(f"Created suggestion {suggestion_id}: {title}")
                return suggestion_id

        except Exception as e:
            logger.error(f"Failed to insert suggestion: {e}")
            return None

    def check_duplicate_suggestion(
        self,
        email_id: int,
        suggestion_type: str,
        project_code: Optional[str] = None,
    ) -> bool:
        """
        Check if a similar suggestion already exists.

        For link-type suggestions (email_link, link_review), checks across
        BOTH types to prevent duplicates from pattern linker + GPT (#316).
        """
        # Link-type suggestions should be deduplicated across types
        # Pattern linker creates 'link_review', GPT creates 'email_link'
        link_types = ("email_link", "link_review")

        if suggestion_type in link_types:
            # Check for ANY link suggestion for this email+project
            query = """
                SELECT COUNT(*) as count FROM ai_suggestions
                WHERE source_id = ?
                AND suggestion_type IN ('email_link', 'link_review')
                AND status = 'pending'
            """
            params = [email_id]

            if project_code:
                query += " AND project_code = ?"
                params.append(project_code)

            result = self.execute_query(query, tuple(params), fetch_one=True)
            return result.get("count", 0) > 0
        else:
            # Standard check for non-link suggestions
            query = """
                SELECT COUNT(*) as count FROM ai_suggestions
                WHERE source_id = ? AND suggestion_type = ?
                AND status = 'pending'
            """
            params = [email_id, suggestion_type]

            if project_code:
                query += " AND project_code = ?"
                params.append(project_code)

            result = self.execute_query(query, tuple(params), fetch_one=True)
            return result.get("count", 0) > 0

    # ==================================================================
    # NEW: Task/Meeting/Deliverable/Commitment Suggestion Methods
    # ==================================================================

    def _write_action_item_suggestion(
        self,
        email_id: int,
        action_item: Dict[str, Any],
        email_data: Dict[str, Any] = None,
        project_code: str = None,
    ) -> Optional[int]:
        """
        Create action_item suggestion from GPT-detected task in email.

        These become tasks when approved.
        """
        if not action_item.get("should_create"):
            return None

        confidence = action_item.get("confidence", 0)
        if confidence < self.CONFIDENCE_THRESHOLDS["action_item"]:
            logger.debug(f"Action item confidence {confidence} below threshold")
            return None

        task_title = action_item.get("task_title")
        if not task_title:
            return None

        # Check for duplicate
        if self.check_duplicate_suggestion(email_id, "action_item", project_code):
            logger.debug(f"Duplicate action_item suggestion for email {email_id}")
            return None

        subject = email_data.get("subject", "Unknown") if email_data else "Unknown"

        # Map assignee hint to category
        assignee_hint = action_item.get("assignee_hint", "us")
        if assignee_hint == "us":
            category = "Project" if project_code else "Admin"
        elif assignee_hint == "them":
            category = "Project"
        else:
            category = "Project"

        suggested_data = {
            "task_title": task_title,
            "task_description": action_item.get("task_description", ""),
            "assignee_hint": assignee_hint,
            "due_date_hint": action_item.get("due_date_hint"),
            "priority_hint": action_item.get("priority_hint", "medium"),
            "category": category,
            "source_email_id": email_id,
            "source_quote": action_item.get("source_quote"),
            "project_code": project_code,
        }

        # Determine priority from hint
        priority_map = {"critical": "high", "high": "high", "medium": "medium", "low": "low"}
        priority = priority_map.get(action_item.get("priority_hint", "medium"), "medium")

        return self._insert_suggestion(
            suggestion_type="action_item",
            priority=priority,
            confidence_score=confidence,
            source_type="email",
            source_id=email_id,
            source_reference=f"Email: {subject[:50]}",
            title=f"Task: {task_title[:60]}",
            description=f"Detected action item: {task_title}. {action_item.get('task_description', '')}",
            suggested_action="Create task",
            suggested_data=suggested_data,
            target_table="tasks",
            project_code=project_code,
        )

    def _write_meeting_suggestion(
        self,
        email_id: int,
        meeting_data: Dict[str, Any],
        email_data: Dict[str, Any] = None,
        project_code: str = None,
    ) -> Optional[int]:
        """
        Create meeting_detected suggestion from GPT analysis.

        These become meeting records when approved.
        """
        if not meeting_data.get("detected"):
            return None

        confidence = meeting_data.get("confidence", 0)
        if confidence < self.CONFIDENCE_THRESHOLDS["meeting_detected"]:
            logger.debug(f"Meeting confidence {confidence} below threshold")
            return None

        # Check for duplicate
        if self.check_duplicate_suggestion(email_id, "meeting_detected", project_code):
            logger.debug(f"Duplicate meeting_detected suggestion for email {email_id}")
            return None

        subject = email_data.get("subject", "Unknown") if email_data else "Unknown"
        meeting_type = meeting_data.get("meeting_type", "request")
        meeting_purpose = meeting_data.get("meeting_purpose", "Meeting")

        # Build title based on type
        if meeting_type == "confirmation":
            title = f"Meeting confirmed: {meeting_purpose[:40]}"
        elif meeting_type == "reschedule":
            title = f"Meeting reschedule: {meeting_purpose[:40]}"
        else:
            title = f"Meeting request: {meeting_purpose[:40]}"

        suggested_data = {
            "meeting_type": meeting_type,
            "meeting_purpose": meeting_purpose,
            "proposed_date": meeting_data.get("proposed_date"),
            "proposed_time": meeting_data.get("proposed_time"),
            "participants": meeting_data.get("participants", []),
            "location_hint": meeting_data.get("location_hint"),
            "source_email_id": email_id,
            "source_quote": meeting_data.get("source_quote"),
            "project_code": project_code,
        }

        # Priority based on meeting type
        if meeting_type == "confirmation":
            priority = "high"
        elif meeting_type == "reschedule":
            priority = "high"
        else:
            priority = "medium"

        return self._insert_suggestion(
            suggestion_type="meeting_detected",
            priority=priority,
            confidence_score=confidence,
            source_type="email",
            source_id=email_id,
            source_reference=f"Email: {subject[:50]}",
            title=title,
            description=f"Meeting detected in email. {meeting_data.get('source_quote', '')}",
            suggested_action="Create meeting",
            suggested_data=suggested_data,
            target_table="meetings",
            project_code=project_code,
        )

    def _write_deliverable_suggestion(
        self,
        email_id: int,
        deliverable_data: Dict[str, Any],
        email_data: Dict[str, Any] = None,
        project_code: str = None,
    ) -> Optional[int]:
        """
        Create deadline_detected suggestion from GPT analysis.

        These become deliverable records when approved.
        """
        if not deliverable_data.get("detected"):
            return None

        confidence = deliverable_data.get("confidence", 0)
        if confidence < self.CONFIDENCE_THRESHOLDS["deadline_detected"]:
            logger.debug(f"Deliverable confidence {confidence} below threshold")
            return None

        deliverable_name = deliverable_data.get("deliverable_name")
        if not deliverable_name:
            return None

        # Check for duplicate
        if self.check_duplicate_suggestion(email_id, "deadline_detected", project_code):
            logger.debug(f"Duplicate deadline_detected suggestion for email {email_id}")
            return None

        subject = email_data.get("subject", "Unknown") if email_data else "Unknown"

        suggested_data = {
            "deliverable_name": deliverable_name,
            "deliverable_type": deliverable_data.get("deliverable_type", "other"),
            "deadline_date": deliverable_data.get("deadline_date"),
            "milestone_status": deliverable_data.get("milestone_status"),
            "description": deliverable_data.get("description", ""),
            "source_email_id": email_id,
            "source_quote": deliverable_data.get("source_quote"),
            "project_code": project_code,
        }

        # Priority based on deadline proximity (if date provided)
        priority = "medium"
        deadline_date = deliverable_data.get("deadline_date")
        if deadline_date:
            try:
                from datetime import datetime
                deadline = datetime.strptime(deadline_date, "%Y-%m-%d")
                days_until = (deadline - datetime.now()).days
                if days_until <= 7:
                    priority = "high"
                elif days_until <= 30:
                    priority = "medium"
                else:
                    priority = "low"
            except (ValueError, TypeError):
                pass

        return self._insert_suggestion(
            suggestion_type="deadline_detected",
            priority=priority,
            confidence_score=confidence,
            source_type="email",
            source_id=email_id,
            source_reference=f"Email: {subject[:50]}",
            title=f"Deliverable: {deliverable_name[:50]}",
            description=f"Deadline detected: {deliverable_name}. Due: {deadline_date or 'TBD'}",
            suggested_action="Create deliverable",
            suggested_data=suggested_data,
            target_table="deliverables",
            project_code=project_code,
        )

    def _write_commitment_suggestion(
        self,
        email_id: int,
        commitment_data: Dict[str, Any],
        email_data: Dict[str, Any] = None,
        project_code: str = None,
    ) -> Optional[int]:
        """
        Create commitment suggestion from GPT analysis.

        Tracks promises made by us or by clients/partners.
        These become commitment records when approved.
        """
        if not commitment_data.get("detected"):
            return None

        confidence = commitment_data.get("confidence", 0)
        if confidence < self.CONFIDENCE_THRESHOLDS["commitment"]:
            logger.debug(f"Commitment confidence {confidence} below threshold")
            return None

        description = commitment_data.get("description")
        if not description:
            return None

        commitment_type = commitment_data.get("commitment_type", "our_commitment")
        if commitment_type not in ("our_commitment", "their_commitment"):
            commitment_type = "our_commitment"

        # Check for duplicate
        if self.check_duplicate_suggestion(email_id, "commitment", project_code):
            logger.debug(f"Duplicate commitment suggestion for email {email_id}")
            return None

        subject = email_data.get("subject", "Unknown") if email_data else "Unknown"

        suggested_data = {
            "commitment_type": commitment_type,
            "description": description,
            "committed_by": commitment_data.get("committed_by"),
            "due_date": commitment_data.get("due_date"),
            "source_email_id": email_id,
            "source_quote": commitment_data.get("source_quote"),
            "project_code": project_code,
        }

        # Title based on who made the commitment
        if commitment_type == "our_commitment":
            title = f"We promised: {description[:45]}"
            priority = "high"  # Our commitments are high priority
        else:
            title = f"They promised: {description[:45]}"
            priority = "medium"

        return self._insert_suggestion(
            suggestion_type="commitment",
            priority=priority,
            confidence_score=confidence,
            source_type="email",
            source_id=email_id,
            source_reference=f"Email: {subject[:50]}",
            title=title,
            description=f"Commitment detected: {description}",
            suggested_action="Track commitment",
            suggested_data=suggested_data,
            target_table="commitments",
            project_code=project_code,
        )
