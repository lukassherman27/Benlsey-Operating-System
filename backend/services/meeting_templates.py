"""
Meeting Summary Templates

Different meeting types need different summary formats.
These templates guide Claude to generate appropriate summaries.

Created: 2025-12-26 for Issue #171
"""

from typing import Dict, List, Optional
import re


# Meeting type detection keywords
MEETING_TYPE_KEYWORDS = {
    'contract_negotiation': [
        'contract', 'terms', 'fee', 'payment', 'signing', 'mobilization',
        'agreement', 'legal', 'scope of work', 'deliverables', 'retainer'
    ],
    'site_visit': [
        'site visit', 'on site', 'walked through', 'construction', 'progress',
        'inspection', 'walkthrough', 'site conditions', 'as-built'
    ],
    'design_review': [
        'design review', 'feedback', 'comments', 'revisions', 'drawings',
        'presentation', 'scheme', 'concept', 'dd', 'cd', 'schematic'
    ],
    'concept_presentation': [
        'concept', 'presentation', 'presented', 'first look', 'initial design',
        'vision', 'mood board', 'inspiration'
    ],
    'kickoff': [
        'kickoff', 'kick-off', 'kick off', 'introduction', 'first meeting',
        'getting started', 'project start', 'onboarding'
    ],
    'proposal_discussion': [
        'proposal', 'scope', 'budget', 'timeline', 'estimate', 'quote',
        'pricing', 'phases'
    ],
    'internal': [
        'internal', 'team meeting', 'coordination', 'sync', 'standup',
        'check-in', 'weekly'
    ],
    'client_call': [
        'call', 'zoom', 'teams', 'video', 'conference', 'catch up',
        'update', 'status'
    ],
}


# Templates for each meeting type
MEETING_TEMPLATES = {
    'contract_negotiation': """
[CLIENT NAME IN CAPS]
Contract Negotiation Meeting
[PROJECT CODE] | [Project Name]

Date & Time
[Date] | [Time]

Platform
[Zoom/Teams/In-Person]

Attendees
[Name (Affiliation)] for each person

Meeting Summary:
[2-3 paragraph summary focusing on contract terms discussed, what was agreed, and what remains open]

📋 Projects Under Discussion
1. [Project Name] - [Location]
   Type: [type]
   Status: [status]
   Contract Value: [value if discussed]

📝 Contract Terms Discussed
| # | Term | Status | Notes |
|---|------|--------|-------|
| 1 | Fee Structure | [Agreed/Pending] | [Details] |
| 2 | Payment Schedule | [Agreed/Pending] | [Details] |
| 3 | Scope of Work | [Agreed/Pending] | [Details] |
| 4 | Timeline | [Agreed/Pending] | [Details] |
| 5 | Deliverables | [Agreed/Pending] | [Details] |

🔧 Legal/Administrative Notes
[Any legal considerations, insurance requirements, licensing notes]

✅ Action Items

**BENSLEY**
| Action | Owner | Deadline |
|--------|-------|----------|
| [Action] | [Person] | [Date/TBD] |

**[CLIENT]**
| Action | Deadline |
|--------|----------|
| [Action] | [Date/TBD] |

Key Decisions Made
- [Decision 1]
- [Decision 2]

Next Steps
- Immediate: [next action]
- Upon Signing: [what happens after contract signed]

---
Minutes prepared from meeting recording | [Date]
Projects: [Codes] | Client: [Name]
BENSLEY Design Studios | Bangkok, Thailand
""",

    'site_visit': """
[PROJECT NAME IN CAPS]
Site Visit Report
[PROJECT CODE] | [Location]

Date
[Date]

Location
[Site address/location]

Attendees
[Name (Affiliation)] for each person

Site Visit Summary:
[2-3 paragraph summary of what was observed, key findings, and overall site status]

📍 Site Observations

**Area 1: [Area Name]**
- Observation: [What was seen]
- Status: [Good/Concerns/Action Needed]
- Notes: [Details]

**Area 2: [Area Name]**
- Observation: [What was seen]
- Status: [Good/Concerns/Action Needed]
- Notes: [Details]

[Continue for each area visited]

⚠️ Issues Identified
| # | Issue | Location | Priority | Recommended Action |
|---|-------|----------|----------|-------------------|
| 1 | [Issue] | [Where] | [High/Med/Low] | [What to do] |

📸 Photos Referenced
[List of photo filenames or references discussed]

🔧 Technical Notes
[Construction observations, measurements, technical details]

✅ Action Items

**BENSLEY**
| Action | Owner | Deadline |
|--------|-------|----------|
| [Action] | [Person] | [Date/TBD] |

**CONTRACTOR/CLIENT**
| Action | Deadline |
|--------|----------|
| [Action] | [Date/TBD] |

Next Visit
- Scheduled: [Date if known]
- Focus Areas: [What to check next time]

---
Site visit report | [Date]
Project: [Code] | Location: [Site]
BENSLEY Design Studios | Bangkok, Thailand
""",

    'design_review': """
[PROJECT NAME IN CAPS]
Design Review Meeting
[PROJECT CODE] | [Phase: SD/DD/CD]

Date & Time
[Date] | [Time]

Platform
[Zoom/Teams/In-Person]

Attendees
[Name (Affiliation)] for each person

Review Summary:
[2-3 paragraph summary of what was presented, overall reception, and key feedback themes]

📋 Items Presented
1. [Drawing/Document Name]
   - Status: [For Review/For Approval]
   - Client Response: [Approved/Comments/Revisions Needed]

📝 Feedback by Area

**[Area/Room 1]**
| Item | Feedback | Action |
|------|----------|--------|
| [Element] | [Client comment] | [What BENSLEY will do] |

**[Area/Room 2]**
| Item | Feedback | Action |
|------|----------|--------|
| [Element] | [Client comment] | [What BENSLEY will do] |

✅ Approved Items
- [Item 1]
- [Item 2]

🔄 Revisions Requested
| # | Item | Current | Requested Change | Priority |
|---|------|---------|------------------|----------|
| 1 | [What] | [Current state] | [What client wants] | [High/Med/Low] |

✅ Action Items

**BENSLEY**
| Action | Owner | Deadline |
|--------|-------|----------|
| [Revision] | [Person] | [Date] |

**CLIENT**
| Action | Deadline |
|--------|----------|
| [Decision needed] | [Date] |

Next Review
- Date: [Scheduled date]
- Deliverables: [What will be presented]

---
Design review notes | [Date]
Project: [Code] | Phase: [SD/DD/CD]
BENSLEY Design Studios | Bangkok, Thailand
""",

    'kickoff': """
[PROJECT NAME IN CAPS]
Project Kickoff Meeting
[PROJECT CODE] | [Location]

Date & Time
[Date] | [Time]

Platform
[Zoom/Teams/In-Person]

Attendees
[Name (Affiliation/Role)] for each person

Project Overview:
[2-3 paragraph summary of the project vision, scope, and key objectives discussed]

📋 Project Scope
- **Architecture**: [Yes/No - brief scope]
- **Interior Design**: [Yes/No - brief scope]
- **Landscape**: [Yes/No - brief scope]
- **FF&E**: [Yes/No - brief scope]

👥 Team Structure

**BENSLEY Team**
| Role | Name | Responsibility |
|------|------|----------------|
| Principal | [Name] | [Oversight] |
| Project Manager | [Name] | [Day-to-day] |
| [Other] | [Name] | [Role] |

**Client Team**
| Role | Name | Contact |
|------|------|---------|
| [Role] | [Name] | [Email/Phone] |

📅 Key Milestones
| Phase | Deliverable | Target Date |
|-------|-------------|-------------|
| Concept | [What] | [When] |
| Schematic Design | [What] | [When] |
| Design Development | [What] | [When] |
| Construction Docs | [What] | [When] |

🔧 Technical Requirements
[Key technical constraints, regulations, client requirements discussed]

✅ Immediate Next Steps

**BENSLEY**
| Action | Owner | Deadline |
|--------|-------|----------|
| [Action] | [Person] | [Date] |

**CLIENT**
| Action | Deadline |
|--------|----------|
| [Info/docs to provide] | [Date] |

Communication Protocol
- Primary Contact: [Name/Email]
- Meeting Cadence: [Weekly/Bi-weekly]
- File Sharing: [Platform]

---
Kickoff meeting notes | [Date]
Project: [Code] | Client: [Name]
BENSLEY Design Studios | Bangkok, Thailand
""",

    'client_call': """
[CLIENT NAME IN CAPS]
[Meeting Type Description]
[PROJECT CODE] | [Project Name]

Date & Time
[Date] | [Time]

Platform
[Zoom/Teams/Phone]

Attendees
[Name (Affiliation)] for each person

Meeting Summary:
[2-3 paragraph executive summary focusing on outcomes and decisions]

📋 Topics Discussed
1. [Topic 1]
   - Discussion: [Summary]
   - Outcome: [Decision/Action]

2. [Topic 2]
   - Discussion: [Summary]
   - Outcome: [Decision/Action]

📝 Key Points
- [Important point 1]
- [Important point 2]
- [Important point 3]

✅ Action Items

**BENSLEY**
| Action | Owner | Deadline |
|--------|-------|----------|
| [Action] | [Person] | [Date/TBD] |

**[CLIENT]**
| Action | Deadline |
|--------|----------|
| [Action] | [Date/TBD] |

Key Decisions Made
- [Decision 1]
- [Decision 2]

Next Steps
- Immediate: [next action]
- Next Call: [when scheduled]

---
Minutes prepared from meeting recording | [Date]
Projects: [Codes] | Client: [Name]
BENSLEY Design Studios | Bangkok, Thailand
""",

    'internal': """
BENSLEY INTERNAL
[Meeting Topic]
[PROJECT CODE(s) if applicable]

Date & Time
[Date] | [Time]

Attendees
[Name (Role)] for each team member

Meeting Summary:
[Brief summary of internal discussion and decisions]

📋 Agenda Items Discussed

**1. [Topic]**
- Discussion: [Summary]
- Decision: [What was decided]
- Owner: [Who's responsible]

**2. [Topic]**
- Discussion: [Summary]
- Decision: [What was decided]
- Owner: [Who's responsible]

✅ Action Items
| Action | Owner | Deadline |
|--------|-------|----------|
| [Task] | [Person] | [Date] |

📌 Notes for Client Communication
[Any items that need to be communicated to clients]

Next Meeting
- Date: [When]
- Focus: [Topics]

---
Internal meeting notes | [Date]
BENSLEY Design Studios
""",

    'proposal_discussion': """
[CLIENT NAME IN CAPS]
Proposal Discussion
[PROJECT CODE] | [Project Name]

Date & Time
[Date] | [Time]

Platform
[Zoom/Teams/In-Person]

Attendees
[Name (Affiliation)] for each person

Discussion Summary:
[2-3 paragraph summary of proposal discussion, client questions, and responses]

📋 Proposal Overview
- **Project**: [Name and location]
- **Scope**: [Architecture/Interior/Landscape]
- **Proposed Value**: [Fee amount]
- **Timeline**: [Duration]

📝 Client Questions & Responses
| Question | BENSLEY Response |
|----------|------------------|
| [Question 1] | [Answer] |
| [Question 2] | [Answer] |

💰 Fee Discussion
| Phase | Proposed | Client Feedback |
|-------|----------|-----------------|
| [Phase 1] | [Amount] | [Accepted/Negotiating] |
| [Phase 2] | [Amount] | [Accepted/Negotiating] |

🔄 Requested Changes to Proposal
- [Change 1]
- [Change 2]

✅ Action Items

**BENSLEY**
| Action | Owner | Deadline |
|--------|-------|----------|
| [Revise proposal] | [Person] | [Date] |

**CLIENT**
| Action | Deadline |
|--------|----------|
| [Decision] | [Date] |

Next Steps
- [What happens next]

---
Proposal discussion notes | [Date]
Project: [Code] | Client: [Name]
BENSLEY Design Studios | Bangkok, Thailand
""",
}


def detect_meeting_type(transcript: str, title: str = None) -> str:
    """
    Detect meeting type from transcript content.
    Returns the most likely meeting type based on keyword matches.
    """
    text = f"{title or ''} {transcript[:5000]}".lower()

    scores: Dict[str, int] = {}
    for meeting_type, keywords in MEETING_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        # Weight certain strong indicators more heavily
        for kw in keywords[:3]:  # First 3 keywords are strongest indicators
            if kw in text:
                score += 2
        if score > 0:
            scores[meeting_type] = score

    if scores:
        return max(scores, key=scores.get)
    return 'client_call'  # Default


def get_template(meeting_type: str) -> str:
    """Get the template for a meeting type."""
    return MEETING_TEMPLATES.get(meeting_type, MEETING_TEMPLATES['client_call'])


def get_template_instructions(meeting_type: str) -> str:
    """Get specific instructions for generating a summary of this meeting type."""

    instructions = {
        'contract_negotiation': """
Focus on:
- Specific contract terms discussed and their status (agreed/pending)
- Fee amounts and payment schedules mentioned
- Scope boundaries and deliverables
- Timeline and milestones
- Any legal or administrative requirements
- What's agreed vs what needs further discussion
""",
        'site_visit': """
Focus on:
- Physical observations at each area visited
- Construction progress or site conditions
- Issues or concerns identified with priority levels
- Photos or documents referenced
- Safety or regulatory observations
- Recommendations for next steps
""",
        'design_review': """
Focus on:
- Which drawings/documents were reviewed
- Client feedback on specific design elements
- What was approved vs needs revision
- Priority of requested changes
- Design decisions made
- Next deliverables expected
""",
        'kickoff': """
Focus on:
- Project scope and vision
- Team introductions and roles
- Key milestones and timeline
- Communication protocols
- Technical requirements discussed
- Immediate next steps for both parties
""",
        'client_call': """
Focus on:
- Key topics discussed and outcomes
- Decisions made during the call
- Action items with owners and deadlines
- Any concerns or blockers raised
- Next steps and follow-up timing
""",
        'internal': """
Focus on:
- Internal decisions made
- Task assignments and deadlines
- Items to communicate to clients
- Resource allocation discussed
- Project coordination points
""",
        'proposal_discussion': """
Focus on:
- Client questions about the proposal
- Fee negotiation points
- Scope clarifications
- Timeline discussions
- Changes requested to proposal
- Next steps toward signing
""",
    }

    return instructions.get(meeting_type, instructions['client_call'])


def build_prompt_with_template(
    meeting_type: str,
    context: Dict,
    transcript: str
) -> str:
    """
    Build a complete prompt for Claude with the appropriate template.

    Args:
        meeting_type: Detected or specified meeting type
        context: Dict with proposal, contacts, emails, previous meetings
        transcript: Full meeting transcript

    Returns:
        Complete prompt string for Claude
    """
    template = get_template(meeting_type)
    instructions = get_template_instructions(meeting_type)

    # Build context sections
    context_str = ""

    if context.get('proposal'):
        p = context['proposal']
        scope_parts = []
        if p.get('is_landscape'): scope_parts.append("Landscape")
        if p.get('is_architect'): scope_parts.append("Architecture")
        if p.get('is_interior'): scope_parts.append("Interior Design")
        scope = ", ".join(scope_parts) or "Design Services"

        context_str += f"""
PROPOSAL CONTEXT:
- Project Code: {p.get('project_code', 'Unknown')}
- Project Name: {p.get('project_name', 'Unknown')}
- Client: {p.get('client_company', 'Unknown')}
- Country: {p.get('country', 'Unknown')}
- Scope: {scope}
- Value: ${p.get('project_value', 0):,.0f}
- Status: {p.get('status', 'Unknown')}
- Contact: {p.get('contact_person', 'Unknown')}
"""

    if context.get('contacts'):
        contacts_list = "\n".join([
            f"  - {c.get('name', 'Unknown')} ({c.get('role', '')}) - {c.get('company', '')} - {c.get('email', '')}"
            for c in context['contacts'][:5]
        ])
        context_str += f"\nKNOWN CONTACTS:\n{contacts_list}\n"

    if context.get('emails'):
        emails_list = "\n".join([
            f"  - {e.get('date', '')}: {e.get('subject', '')} (from {e.get('sender_email', '')})"
            for e in context['emails'][:5]
        ])
        context_str += f"\nRECENT EMAILS:\n{emails_list}\n"

    if context.get('previous_meetings'):
        meetings_list = "\n".join([
            f"  - {m.get('meeting_date', '')}: {m.get('meeting_title', '')} - {m.get('summary_preview', '')}"
            for m in context['previous_meetings']
        ])
        context_str += f"\nPREVIOUS MEETINGS:\n{meetings_list}\n"

    # Truncate transcript if too long
    if len(transcript) > 50000:
        transcript = transcript[:50000] + "\n\n[TRANSCRIPT TRUNCATED]"

    prompt = f"""You are creating professional meeting notes for BENSLEY Design Studios.

This is a {meeting_type.replace('_', ' ').upper()} meeting.

{context_str}

MEETING DETAILS:
- Title: {context.get('title', 'Meeting')}
- Date: {context.get('date', 'Unknown')}
- Participants: {context.get('participants', 'See transcript')}

FULL TRANSCRIPT:
{transcript}

---

Generate meeting notes using this EXACT template format:

{template}

SPECIFIC INSTRUCTIONS FOR THIS MEETING TYPE:
{instructions}

IMPORTANT RULES:
1. Extract REAL information from the transcript - don't invent
2. If you can't determine something, omit it rather than guess
3. Use the project code format "XX BK-XXX" consistently
4. Identify action items by who said they would do what
5. Capture specific numbers, dates, and decisions mentioned
6. Include emojis for section headers as shown in template
7. Format tables properly with alignment
8. Be professional but natural in tone

Output ONLY the meeting notes - no preamble or explanation."""

    return prompt


# Convenience function to get all available meeting types
def get_meeting_types() -> List[str]:
    """Return list of all available meeting types."""
    return list(MEETING_TEMPLATES.keys())
