"""
Proposal Detail Story Service - Extracted from /proposals/{project_code}/story endpoint

Refactored from 677 lines of inline code (#117) into a proper service layer.

Generates the complete story/timeline of a proposal including:
- Full proposal metadata with remarks, correspondence_summary
- All emails chronologically with AI summaries
- Proposal versions detected from attachments
- Events (meetings, calls) from proposal_events and meetings tables
- Action items extracted from emails and waiting_for field
- Threads (grouped emails by subject)
- Current status with calculated days_since_contact
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from .base_service import BaseService


def _redact_path(path: Optional[str]) -> Optional[str]:
    """Redact file path to filename only for security (Issue #385)."""
    if not path:
        return None
    return os.path.basename(path)

import logging
logger = logging.getLogger(__name__)


class ProposalDetailStoryService(BaseService):
    """Generate detailed proposal story with timeline, threads, and action items."""

    def get_story(self, project_code: str) -> Dict[str, Any]:
        """
        Get the complete story/timeline of a proposal.

        Args:
            project_code: The project code to fetch

        Returns:
            Complete proposal story with timeline, threads, action items, etc.

        Raises:
            ValueError: If proposal not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Get full proposal details
            proposal = self._get_proposal(cursor, project_code)
            if not proposal:
                raise ValueError(f"Proposal {project_code} not found")

            proposal_id = proposal["proposal_id"]

            # 2. Get all related data
            all_emails = self._get_emails(cursor, proposal_id)
            proposal_docs = self._get_proposal_attachments(cursor, proposal_id, project_code)
            formal_docs = self._get_formal_documents(cursor, proposal_id, project_code)
            events = self._get_events(cursor, proposal_id, project_code)
            status_history = self._get_status_history(cursor, proposal_id, project_code)

            # 3. Build derived data
            timeline = self._build_timeline(
                cursor, all_emails, proposal_docs, formal_docs, events, status_history
            )
            action_items = self._extract_action_items(proposal, all_emails)
            threads = self._group_into_threads(all_emails)
            current_status = self._calculate_current_status(proposal, all_emails)

            # Security: Redact file paths from attachments/documents (#385)
            def redact_doc_paths(docs: List[Dict]) -> List[Dict]:
                """Redact filepath fields in document lists."""
                redacted = []
                for doc in docs:
                    d = dict(doc)
                    for path_field in ['filepath', 'file_path', 'local_path']:
                        if path_field in d:
                            d[path_field] = _redact_path(d.get(path_field))
                    redacted.append(d)
                return redacted

            return {
                "success": True,
                "project_code": project_code,
                "project_name": proposal.get("project_name"),
                "client": {
                    "name": proposal.get("contact_person"),
                    "company": proposal.get("client_company"),
                    "email": proposal.get("contact_email")
                },
                "value": proposal.get("project_value"),
                "currency": proposal.get("currency") or "USD",
                "remarks": proposal.get("remarks"),
                "correspondence_summary": proposal.get("correspondence_summary"),
                "internal_notes": proposal.get("internal_notes"),
                "scope_summary": proposal.get("scope_summary"),
                "num_proposals_sent": proposal.get("num_proposals_sent"),
                "first_contact_date": proposal.get("first_contact_date"),
                "proposal_sent_date": proposal.get("proposal_sent_date"),
                "timeline": timeline,
                "proposal_versions": redact_doc_paths(formal_docs),
                "proposal_attachments": redact_doc_paths(proposal_docs),
                "events": events,
                "threads": threads,
                "action_items": action_items,
                "current_status": current_status
            }

    def _get_proposal(self, cursor, project_code: str) -> Optional[Dict]:
        """Get full proposal details from proposals table."""
        cursor.execute("""
            SELECT
                proposal_id, project_code, project_name,
                status, current_status,
                client_company, contact_person, contact_email,
                project_value, currency,
                remarks, correspondence_summary, internal_notes, scope_summary,
                waiting_for, waiting_since, ball_in_court,
                next_action, next_action_date,
                last_action, last_contact_date,
                first_contact_date, proposal_sent_date,
                num_proposals_sent,
                created_at
            FROM proposals WHERE project_code = ?
        """, (project_code,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def _get_emails(self, cursor, proposal_id: int) -> List[Dict]:
        """Get all emails linked to this proposal with AI content."""
        cursor.execute("""
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.sender_name,
                e.date,
                e.snippet,
                e.email_direction,
                ec.category,
                ec.subcategory,
                ec.ai_summary,
                ec.key_points,
                ec.action_required,
                ec.urgency_level,
                ec.sentiment
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE epl.proposal_id = ?
            ORDER BY e.date ASC
        """, (proposal_id,))
        return [dict(row) for row in cursor.fetchall()]

    def _get_proposal_attachments(self, cursor, proposal_id: int, project_code: str) -> List[Dict]:
        """Get proposal document attachments."""
        # Extract code portion for matching
        code_part = project_code.split()[1] if ' ' in project_code else project_code

        cursor.execute("""
            SELECT
                ea.attachment_id, ea.email_id, ea.filename, ea.filepath,
                ea.mime_type, ea.document_type, e.date as email_date, e.subject
            FROM email_attachments ea
            JOIN emails e ON ea.email_id = e.email_id
            WHERE ea.proposal_id = ?
            AND ea.filename LIKE '%.docx'
            AND ea.filename LIKE ?
            ORDER BY e.date ASC
        """, (proposal_id, f"%{code_part}%"))
        return [dict(row) for row in cursor.fetchall()]

    def _get_formal_documents(self, cursor, proposal_id: int, project_code: str) -> List[Dict]:
        """Get formal proposal documents from proposal_documents table."""
        cursor.execute("""
            SELECT * FROM proposal_documents
            WHERE proposal_id = ? OR project_code = ?
            ORDER BY sent_date ASC
        """, (proposal_id, project_code))
        return [dict(row) for row in cursor.fetchall()]

    def _get_events(self, cursor, proposal_id: int, project_code: str) -> List[Dict]:
        """Get events including meetings with transcript data."""
        # Get from proposal_events table
        cursor.execute("""
            SELECT * FROM proposal_events
            WHERE proposal_id = ? OR project_code = ?
            ORDER BY event_date ASC
        """, (proposal_id, project_code))
        events = [dict(row) for row in cursor.fetchall()]

        # Also get from meetings table with transcript data
        cursor.execute("""
            SELECT
                m.meeting_id,
                m.title,
                m.description,
                m.meeting_date as event_date,
                m.start_time,
                m.location,
                m.status,
                m.transcript_id,
                t.summary as transcript_summary,
                t.key_points as transcript_key_points,
                t.action_items as transcript_action_items
            FROM meetings m
            LEFT JOIN meeting_transcripts t ON m.transcript_id = t.id
            WHERE m.proposal_id = ? OR m.project_code LIKE ?
            ORDER BY m.meeting_date ASC
        """, (proposal_id, f"%{project_code}%"))

        # Merge meetings into events
        seen_dates: Dict[str, int] = {}
        for i, e in enumerate(events):
            date_key = e.get("event_date")
            if date_key:
                seen_dates[date_key] = i

        for row in cursor.fetchall():
            meeting = dict(row)
            meeting_date = meeting.get("event_date")
            meeting["completed"] = 1 if meeting.get("status") == "completed" else 0

            if meeting_date in seen_dates:
                # If meeting has transcript but existing one doesn't, replace
                if meeting.get("transcript_id"):
                    events[seen_dates[meeting_date]] = meeting
            else:
                events.append(meeting)
                if meeting_date:
                    seen_dates[meeting_date] = len(events) - 1

        return events

    def _get_status_history(self, cursor, proposal_id: int, project_code: str) -> List[Dict]:
        """Get status change history."""
        cursor.execute("""
            SELECT * FROM proposal_status_history
            WHERE proposal_id = ? OR project_code = ?
            ORDER BY status_date ASC
        """, (proposal_id, project_code))
        return [dict(row) for row in cursor.fetchall()]

    def _build_timeline(
        self,
        cursor,
        all_emails: List[Dict],
        proposal_docs: List[Dict],
        formal_docs: List[Dict],
        events: List[Dict],
        status_history: List[Dict]
    ) -> List[Dict]:
        """Build the milestone timeline from all sources."""
        timeline = []

        # Add first contact (first meaningful external email)
        first_external = self._find_first_external_email(all_emails)
        if first_external:
            timeline.append({
                "type": "first_contact",
                "date": first_external["date"],
                "title": "First Contact",
                "summary": first_external.get("subject"),
                "email_id": first_external["email_id"],
                "direction": first_external.get("email_direction")
            })

        # Add email milestones
        timeline.extend(
            self._extract_email_milestones(all_emails, first_external)
        )

        # Add proposal version attachments (external-facing only)
        for doc in proposal_docs:
            cursor.execute(
                "SELECT email_direction FROM emails WHERE email_id = ?",
                (doc["email_id"],)
            )
            email_row = cursor.fetchone()
            if email_row and email_row["email_direction"] == "internal_to_internal":
                continue  # Skip internal drafts

            timeline.append({
                "type": "proposal_version",
                "date": doc["email_date"],
                "title": f"Proposal Document: {doc['filename'][:60]}...",
                "summary": f"Sent via: {doc.get('subject')}",
                "attachment_id": doc["attachment_id"],
                "filepath": _redact_path(doc.get("filepath"))  # Security: redact full path (#385)
            })

        # Add formal documents
        for doc in formal_docs:
            fee_text = f"${doc.get('fee_amount', 0):,.0f}" if doc.get("fee_amount") else ""
            title = f"V{doc.get('version', 1)} Proposal - {fee_text}" if fee_text else f"V{doc.get('version', 1)} Proposal"
            timeline.append({
                "type": "proposal_sent",
                "date": doc.get("sent_date"),
                "title": title,
                "summary": doc.get("notes"),
                "doc_id": doc["doc_id"],
                "version": doc.get("version"),
                "fee_amount": doc.get("fee_amount"),
                "sent_to": doc.get("sent_to")
            })

        # Add events/meetings
        for event in events:
            is_completed = event.get("completed") == 1 or event.get("status") == "completed"
            is_future = False

            if event.get("event_date"):
                try:
                    event_date = datetime.strptime(event["event_date"], "%Y-%m-%d")
                    is_future = event_date.date() >= datetime.now().date() and not is_completed
                except (ValueError, TypeError):
                    pass

            timeline.append({
                "type": "meeting" if not is_future else "upcoming_meeting",
                "date": event.get("event_date"),
                "title": event.get("title"),
                "summary": event.get("transcript_summary") or event.get("description"),
                "location": event.get("location"),
                "attendees": event.get("attendees"),
                "is_confirmed": event.get("is_confirmed"),
                "completed": event.get("completed"),
                "outcome": event.get("outcome"),
                "is_future": is_future,
                "has_transcript": bool(event.get("transcript_id")),
                "transcript_summary": event.get("transcript_summary"),
                "transcript_key_points": event.get("transcript_key_points"),
                "transcript_action_items": event.get("transcript_action_items")
            })

        # Add meaningful status changes
        for sh in status_history:
            notes = sh.get("notes") or ""
            old_status = sh.get("old_status") or ""
            if "Auto-logged" in notes or not notes or not old_status or old_status == "None":
                continue
            timeline.append({
                "type": "status_change",
                "date": sh.get("status_date"),
                "title": f"Status: {old_status} → {sh.get('new_status')}",
                "summary": notes,
                "changed_by": sh.get("changed_by")
            })

        # Sort timeline by date
        timeline.sort(key=self._parse_date_for_sort)
        return timeline

    def _find_first_external_email(self, all_emails: List[Dict]) -> Optional[Dict]:
        """Find the first meaningful external email."""
        for email in all_emails:
            direction = email.get("email_direction") or ""
            if "external" not in direction and direction != "OUTBOUND":
                continue

            summary = email.get("ai_summary") or ""
            subject = email.get("subject") or ""

            # Skip garbage emails
            if "not pertain" in summary.lower() or "not related" in summary.lower():
                continue
            if not subject or subject.lower().startswith("invitation"):
                continue

            return email
        return None

    def _extract_email_milestones(
        self,
        all_emails: List[Dict],
        first_external: Optional[Dict]
    ) -> List[Dict]:
        """Extract milestone events from emails."""
        milestones = []
        seen_milestones: Set[str] = set()

        for email in all_emails:
            if email == first_external:
                continue

            subject_lower = (email.get("subject") or "").lower()
            summary_lower = (email.get("ai_summary") or "").lower()
            direction = email.get("email_direction") or ""
            is_outbound = "external" in direction or direction == "OUTBOUND"
            email_date = (email.get("date") or "")[:10]

            # Skip generic internal emails
            if "proposal list" in subject_lower or "proposal tracking" in subject_lower:
                continue

            # Determine milestone type
            milestone_type = None
            milestone_title = None

            # Proposal sent
            if is_outbound and "proposal" in subject_lower:
                milestone_type = "proposal_sent"
                milestone_title = "Proposal Sent"

            # Meeting scheduled
            elif ("meeting" in subject_lower or "zoom" in subject_lower) and \
                 any(word in summary_lower for word in ["scheduled", "confirmed", "10 am", "10am", "9 am", "9am"]):
                milestone_type = "meeting_scheduled"
                milestone_title = "Meeting Scheduled"

            # Contract discussion
            elif any(word in subject_lower for word in ["contract", "agreement", "mou"]) and \
                 not subject_lower.startswith("re:"):
                milestone_type = "contract_discussion"
                milestone_title = "Contract Discussion"

            # Client response
            elif not is_outbound and any(word in summary_lower for word in
                ["confirmed", "approved", "agreed", "accept", "proceed", "go ahead",
                 "questions about", "comments on the proposal", "feedback on"]):
                milestone_type = "client_response"
                milestone_title = "Client Response"

            if milestone_type:
                milestone_key = f"{milestone_type}:{email_date}"
                if milestone_key not in seen_milestones:
                    seen_milestones.add(milestone_key)
                    milestones.append({
                        "type": milestone_type,
                        "date": email["date"],
                        "title": milestone_title,
                        "summary": email.get("ai_summary"),
                        "email_id": email["email_id"],
                        "direction": email.get("email_direction")
                    })

        return milestones

    def _extract_action_items(self, proposal: Dict, all_emails: List[Dict]) -> List[Dict]:
        """Extract action items from proposal and emails."""
        action_items = []
        seen_email_ids: Set[int] = set()

        # From waiting_for field
        if proposal.get("waiting_for"):
            action_items.append({
                "task": proposal["waiting_for"],
                "date": proposal.get("waiting_since"),
                "source": "system",
                "priority": "high",
                "ball_in_court": proposal.get("ball_in_court")
            })

        # From next_action field
        if proposal.get("next_action"):
            action_items.append({
                "task": proposal["next_action"],
                "date": proposal.get("next_action_date"),
                "source": "system",
                "priority": "high"
            })

        # Extract client requests from recent emails
        request_type_emails = self._find_client_requests(all_emails, seen_email_ids)
        action_items.extend(
            self._create_request_action_items(request_type_emails, all_emails)
        )

        # From emails with action_required flag
        action_items.extend(
            self._extract_email_action_items(all_emails, seen_email_ids)
        )

        # Deduplicate
        return self._deduplicate_action_items(action_items)

    def _find_client_requests(
        self,
        all_emails: List[Dict],
        seen_email_ids: Set[int]
    ) -> Dict[str, List[Dict]]:
        """Find client requests in recent emails."""
        request_patterns = [
            ("contract", "Review contract terms"),
            ("clause", "Contract clause questions"),
            ("confirm", "Confirmation requested"),
            ("please send", "Document request"),
            ("can you send", "Document request"),
            ("we need", "Client request"),
            ("could you", "Client request"),
            ("approve", "Approval needed"),
            ("feedback", "Feedback/response needed"),
        ]

        request_type_emails: Dict[str, List[Dict]] = {}

        for email in reversed(all_emails[-20:]):
            email_id = email.get("email_id")
            if email_id in seen_email_ids:
                continue

            direction = email.get("email_direction") or ""
            if "internal_to_external" in direction or direction == "OUTBOUND":
                continue

            email_date = email.get("date", "")[:10]
            try:
                email_dt = datetime.strptime(email_date, "%Y-%m-%d")
                days_old = (datetime.now() - email_dt).days
                if days_old > 14:
                    continue
            except (ValueError, TypeError):
                continue

            snippet = (email.get("snippet") or "").lower()
            subject = (email.get("subject") or "").lower()

            for pattern, task_type in request_patterns:
                if pattern in snippet or pattern in subject:
                    if task_type not in request_type_emails:
                        request_type_emails[task_type] = []
                    request_type_emails[task_type].append({
                        "email_id": email_id,
                        "date": email_date,
                        "days_old": days_old,
                        "sender": self._clean_sender_name(email)
                    })
                    seen_email_ids.add(email_id)
                    break

        return request_type_emails

    def _create_request_action_items(
        self,
        request_type_emails: Dict[str, List[Dict]],
        all_emails: List[Dict]
    ) -> List[Dict]:
        """Create action items from grouped client requests."""
        action_items = []

        for task_type, emails in request_type_emails.items():
            if not emails:
                continue

            latest_request_date = max(e["date"] for e in emails)

            # Check if we already responded
            we_responded = False
            for email in all_emails:
                direction = email.get("email_direction") or ""
                if "internal_to_external" in direction or direction == "OUTBOUND":
                    email_date = (email.get("date") or "")[:10]
                    if email_date > latest_request_date:
                        we_responded = True
                        break

            if we_responded:
                continue

            min_days_old = min(e["days_old"] for e in emails)
            email_count = len(emails)

            if email_count == 1:
                task_text = f"{task_type} from {emails[0]['sender']}"
            else:
                task_text = f"{task_type} ({email_count} emails)"

            action_items.append({
                "task": task_text,
                "date": latest_request_date,
                "source": "email",
                "email_id": emails[0]["email_id"],
                "priority": "high" if min_days_old <= 3 else "medium"
            })

        return action_items

    def _extract_email_action_items(
        self,
        all_emails: List[Dict],
        seen_email_ids: Set[int]
    ) -> List[Dict]:
        """Extract action items from emails with action_required flag."""
        action_items = []

        for email in all_emails[-30:]:
            email_id = email.get("email_id")
            if email_id in seen_email_ids:
                continue

            if not email.get("action_required"):
                continue

            email_date = email.get("date", "")[:10]
            try:
                email_dt = datetime.strptime(email_date, "%Y-%m-%d")
                if (datetime.now() - email_dt).days > 14:
                    continue
            except (ValueError, TypeError):
                continue

            key_points = email.get("key_points")
            if key_points:
                try:
                    points = json.loads(key_points) if isinstance(key_points, str) else key_points
                    if isinstance(points, list):
                        seen_email_ids.add(email_id)
                        for point in points[:2]:
                            action_items.append({
                                "task": point,
                                "date": email_date,
                                "source": "email",
                                "email_id": email_id,
                                "priority": email.get("urgency_level") or "medium"
                            })
                except (json.JSONDecodeError, TypeError):
                    pass

        return action_items

    def _deduplicate_action_items(self, action_items: List[Dict]) -> List[Dict]:
        """Remove duplicate action items."""
        seen_tasks: Set[str] = set()
        unique_items = []

        for item in action_items:
            task_key = item["task"].lower().strip()
            if task_key not in seen_tasks:
                seen_tasks.add(task_key)
                unique_items.append(item)

        return unique_items

    def _group_into_threads(self, all_emails: List[Dict]) -> List[Dict]:
        """Group emails into conversation threads by subject."""
        threads: Dict[str, Dict] = {}

        for email in all_emails:
            subject = email.get("subject") or "No Subject"
            base_subject = subject

            # Strip reply/forward prefixes
            for prefix in ["Re: ", "RE: ", "Fwd: ", "FW: ", "Fw: ", "TR: ", "RE : "]:
                while base_subject.startswith(prefix):
                    base_subject = base_subject[len(prefix):]
            base_subject = base_subject.strip()

            if base_subject not in threads:
                threads[base_subject] = {
                    "emails": [],
                    "first_date": email["date"],
                    "last_date": email["date"],
                    "participants": set(),
                    "has_action": False
                }

            threads[base_subject]["emails"].append({
                "id": email["email_id"],
                "date": email["date"],
                "sender": email.get("sender_name") or email.get("sender_email"),
                "summary": email.get("ai_summary"),
                "direction": email.get("email_direction")
            })
            threads[base_subject]["last_date"] = email["date"]

            if email.get("sender_name"):
                threads[base_subject]["participants"].add(email["sender_name"])
            if email.get("action_required"):
                threads[base_subject]["has_action"] = True

        # Convert to list and sort
        thread_list = []
        for subject, data in threads.items():
            thread_list.append({
                "subject": subject,
                "email_count": len(data["emails"]),
                "emails": data["emails"],
                "first_date": data["first_date"],
                "last_date": data["last_date"],
                "participants": list(data["participants"]),
                "has_action": data["has_action"]
            })

        thread_list.sort(key=lambda x: x["last_date"] or "", reverse=True)
        return thread_list

    def _calculate_current_status(self, proposal: Dict, all_emails: List[Dict]) -> Dict:
        """Calculate current status with days since contact."""
        last_email = all_emails[-1] if all_emails else None
        last_email_date = last_email["date"] if last_email else None
        days_since_contact = None

        if last_email_date:
            try:
                date_str = str(last_email_date).replace("+07:00", "").replace("+08:00", "")[:19]
                last_dt = datetime.fromisoformat(date_str)
                days_since_contact = (datetime.now() - last_dt).days
            except (ValueError, TypeError):
                pass

        current_status = {
            "status": proposal.get("current_status") or proposal.get("status"),
            "last_contact_date": last_email_date[:10] if last_email_date else proposal.get("last_contact_date"),
            "days_since_contact": days_since_contact,
            "email_count": len(all_emails),
            "ball_in_court": proposal.get("ball_in_court"),
            "waiting_for": proposal.get("waiting_for"),
            "waiting_since": proposal.get("waiting_since"),
            "last_action": proposal.get("last_action"),
            "suggested_action": proposal.get("next_action")
        }

        # Extract suggested action from correspondence_summary if not set
        if not current_status["suggested_action"]:
            current_status["suggested_action"] = self._extract_suggested_action(
                proposal.get("correspondence_summary") or ""
            )

        return current_status

    def _extract_suggested_action(self, correspondence_summary: str) -> Optional[str]:
        """Extract suggested next action from correspondence summary."""
        patterns = [
            (r'(?:meeting|call|zoom|video call)\s+(?:on|scheduled for|set for)\s+(\w+\s*\d+(?:st|nd|rd|th)?(?:\s*,?\s*\d{4})?)', 'Meeting scheduled'),
            (r'(?:meeting|call)\s+(?:to be|needs to be)\s+(?:scheduled|arranged|set up)', 'Schedule meeting'),
            (r'waiting\s+(?:for|on)\s+(?:their|client|owner|developer)\s+(?:response|reply|feedback|approval|decision)', 'Awaiting client response'),
            (r'awaiting\s+(?:client|their)\s+(?:response|feedback|approval)', 'Awaiting client response'),
            (r'need(?:s)?\s+to\s+(?:follow up|followup|follow-up)', 'Follow up required'),
            (r'(?:will|should)\s+(?:send|submit|provide)\s+(?:revised|updated|new)\s+(?:proposal|quote|fee)', 'Send revised proposal'),
            (r'(?:contract|proposal|fee)\s+(?:under|pending)\s+(?:review|consideration)', 'Under review'),
            (r'(?:reviewing|review)\s+(?:contract|proposal|terms)', 'Under review'),
        ]

        for pattern, action_label in patterns:
            match = re.search(pattern, correspondence_summary, re.IGNORECASE)
            if match:
                if match.groups():
                    return f"{action_label}: {match.group(1)}"
                return action_label

        return None

    def _clean_sender_name(self, email_data: Dict) -> str:
        """Clean sender name from email data."""
        sender = email_data.get("sender_name") or ""

        # Remove angle brackets
        if "<" in sender:
            sender = sender.split("<")[0].strip()

        if not sender.strip():
            sender_email = email_data.get("sender_email", "") or ""
            if "<" in sender_email:
                name_part = sender_email.split("<")[0].strip()
                if name_part:
                    sender = name_part
                else:
                    email_part = sender_email.split("<")[1].rstrip(">") if "<" in sender_email else sender_email
                    sender = email_part.split("@")[0] if "@" in email_part else email_part
            else:
                sender_email = sender_email.strip().lstrip("<").rstrip(">")
                sender = sender_email.split("@")[0] if "@" in sender_email else sender_email

        sender = sender.replace("<", "").replace(">", "")
        return sender.strip() or "Unknown"

    def _parse_date_for_sort(self, item: Dict) -> datetime:
        """Parse date for timeline sorting."""
        d = item.get("date")
        if not d:
            return datetime.min
        try:
            d_str = str(d)
            if "T" in d_str or " " in d_str:
                d_str = d_str.replace("+07:00", "").replace("+08:00", "").replace("+00:00", "")[:19]
                return datetime.fromisoformat(d_str)
            return datetime.strptime(d_str[:10], "%Y-%m-%d")
        except (ValueError, TypeError):
            return datetime.min
