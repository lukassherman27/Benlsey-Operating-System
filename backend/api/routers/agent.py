"""
Agent Router - AI Agent endpoints (Follow-up Agent, etc.)

Endpoints:
    GET /api/agent/follow-up/summary - Follow-up summary
    GET /api/agent/follow-up/proposals - Proposals needing follow-up
    POST /api/agent/follow-up/draft/{proposal_id} - Draft follow-up email
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sqlite3
from datetime import datetime, timedelta

from api.dependencies import DB_PATH
from api.helpers import item_response, list_response

router = APIRouter(prefix="/api", tags=["agent"])


@router.get("/agent/follow-up/summary")
async def get_follow_up_summary():
    """Get follow-up agent summary"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get proposals needing follow-up (no contact in 14+ days)
        cursor.execute("""
            SELECT
                COUNT(*) as total_active
            FROM proposals
            WHERE status = 'active'
        """)
        total_row = cursor.fetchone()
        total_active = total_row['total_active'] if total_row else 0

        # Count proposals needing follow-up
        cursor.execute("""
            SELECT
                p.proposal_id,
                p.project_code,
                p.project_name as project_title,
                p.client_company,
                p.project_value,
                p.last_contact_date,
                julianday('now') - julianday(p.last_contact_date) as days_since_contact
            FROM proposals p
            WHERE p.status = 'active'
              AND (
                  p.last_contact_date IS NULL
                  OR julianday('now') - julianday(p.last_contact_date) > 14
              )
            ORDER BY p.project_value DESC NULLS LAST
        """)

        needing_followup = [dict(row) for row in cursor.fetchall()]

        # Calculate by urgency
        by_urgency = {
            "critical": {"count": 0, "value": 0},
            "high": {"count": 0, "value": 0},
            "medium": {"count": 0, "value": 0},
            "low": {"count": 0, "value": 0},
        }

        value_at_risk = 0
        top_priority = []

        for p in needing_followup:
            days = p.get('days_since_contact') or 30
            value = p.get('project_value') or 0

            if days > 30:
                urgency = "critical"
            elif days > 21:
                urgency = "high"
            elif days > 14:
                urgency = "medium"
            else:
                urgency = "low"

            by_urgency[urgency]["count"] += 1
            by_urgency[urgency]["value"] += value
            value_at_risk += value

            if len(top_priority) < 5:
                top_priority.append({
                    "project_code": p.get('project_code'),
                    "project_name": p.get('project_title'),
                    "client": p.get('client_company'),
                    "value": value,
                    "urgency": urgency,
                    "priority_score": value * (days / 14) if days else 0
                })

        conn.close()

        return {
            "success": True,
            "total_active_proposals": total_active,
            "needing_follow_up": len(needing_followup),
            "by_urgency": by_urgency,
            "value_at_risk": value_at_risk,
            "top_priority": sorted(top_priority, key=lambda x: x.get('priority_score', 0), reverse=True),
            "overdue_actions": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/follow-up/proposals")
async def get_follow_up_proposals(
    days_threshold: int = Query(14, ge=1),
    include_analysis: bool = True,
    limit: int = Query(50, ge=1, le=200)
):
    """Get proposals needing follow-up"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                p.proposal_id,
                p.project_code,
                p.project_name,
                p.client_company,
                p.contact_person,
                p.contact_email,
                p.status,
                p.last_contact_date,
                julianday('now') - julianday(p.last_contact_date) as days_since_contact,
                p.next_action,
                p.next_action_date,
                p.project_value,
                p.win_probability,
                p.health_score
            FROM proposals p
            WHERE p.status = 'active'
              AND (
                  p.last_contact_date IS NULL
                  OR julianday('now') - julianday(p.last_contact_date) > ?
              )
            ORDER BY p.project_value DESC NULLS LAST
            LIMIT ?
        """, (days_threshold, limit))

        proposals = []
        for row in cursor.fetchall():
            p = dict(row)
            days = p.get('days_since_contact') or 30

            if days > 30:
                urgency = "critical"
            elif days > 21:
                urgency = "high"
            elif days > 14:
                urgency = "medium"
            else:
                urgency = "low"

            p['urgency'] = urgency
            p['priority_score'] = (p.get('project_value') or 0) * (days / 14) if days else 0
            proposals.append(p)

        conn.close()

        return {
            "success": True,
            "proposals": proposals,
            "count": len(proposals)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/follow-up/draft/{proposal_id}")
async def draft_follow_up_email(
    proposal_id: int,
    tone: str = Query("professional")
):
    """Draft a follow-up email for a proposal based on actual correspondence and status"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get proposal details INCLUDING current_status and proposal_sent_date
        cursor.execute("""
            SELECT
                p.project_code,
                p.project_name as project_title,
                p.client_company,
                p.contact_person,
                p.contact_email,
                p.current_status,
                p.proposal_sent_date,
                p.last_contact_date,
                p.action_needed
            FROM proposals p
            WHERE p.proposal_id = ?
        """, (proposal_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Proposal not found")

        proposal = dict(row)

        # Get recent emails for context
        cursor.execute("""
            SELECT e.subject, e.sender_email, e.date, e.snippet
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            WHERE epl.proposal_id = ?
            ORDER BY e.date DESC
            LIMIT 3
        """, (proposal_id,))
        recent_emails = [dict(r) for r in cursor.fetchall()]
        conn.close()

        contact = proposal.get('contact_person') or 'there'
        project = proposal.get('project_title') or proposal.get('project_code')
        company = proposal.get('client_company') or 'your team'
        status = proposal.get('current_status') or ''
        proposal_sent_date = proposal.get('proposal_sent_date')

        # CRITICAL: Determine the correct email type based on ACTUAL status
        if proposal_sent_date or status in ['Proposal Sent', 'Negotiation']:
            # Proposal WAS sent - can reference it
            subject = f"Following up on {project}"
            body = f"""Dear {contact},

I hope this email finds you well. I wanted to follow up on our proposal for {project}.

We remain very interested in working with {company} on this project and would welcome the opportunity to discuss any questions you may have or provide additional information.

Please let me know if there's a convenient time for a quick call to discuss the next steps.

Best regards"""
        else:
            # NO proposal sent - suggest scheduling a call
            subject = f"Regarding {project} - Next Steps"
            body = f"""Dear {contact},

I hope this message finds you well. I wanted to reach out regarding {project}.

We're very interested in exploring this opportunity with {company} and would love to schedule a call to discuss your vision and requirements in more detail.

Would you have time for a brief call this week or next? Please let me know what works best for your schedule.

Best regards"""

        # Add context about last email if available
        if recent_emails:
            last_email = recent_emails[0]
            last_subject = last_email.get('subject', '')
            # Optionally enhance the draft with context

        return {
            "success": True,
            "subject": subject,
            "body": body,
            "proposal_status": status,
            "proposal_sent": bool(proposal_sent_date)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
