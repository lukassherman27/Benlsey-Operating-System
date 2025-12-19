"""
GPT Suggestion Analyzer Service

Analyzes emails using GPT-4o-mini with full business context
to generate intelligent suggestions.

Part of Phase 2.0: Context-Aware AI Suggestions
"""

import os
import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

logger = logging.getLogger(__name__)

# GPT-4o-mini pricing (as of Dec 2024)
GPT_PRICING = {
    "gpt-4o-mini": {
        "input_per_1m": 0.15,   # $0.15 per 1M input tokens
        "output_per_1m": 0.60,  # $0.60 per 1M output tokens
    }
}


class GPTSuggestionAnalyzer:
    """
    Analyzes emails using GPT with business context to generate suggestions.

    Uses structured JSON output for reliable parsing.
    Tracks token usage for cost monitoring.
    """

    SYSTEM_PROMPT_TEMPLATE = """You are an AI assistant for Bensley Design Studios, a luxury hospitality design firm.

{business_context}

## BILL'S COMPLETE UNIVERSE - CATEGORY TAXONOMY

When analyzing, classify into Bill's complete universe (not just design projects):

### Design Business (BDS) - Link to project codes
- These are DESIGN projects Bensley is working on
- Link to specific proposal/project codes: 25 BK-033, 24 BK-019, etc.

### Internal Operations (INT-*) - No project link
- INT-FIN: Finance (taxes, accounting, invoices, payments, payroll)
- INT-OPS: IT/Systems (email setup, software, BOS, NaviWorld, D365)
- INT-HR: Human Resources (hiring, policies, benefits)
- INT-LEGAL: Legal (contracts for Bensley itself, IP, compliance)
- INT-SCHED: Scheduling (PM scheduling, site visits, resource planning)
- INT-DAILY: Daily work (team updates, progress reports)

### Shinta Mani Hotels (SM-*) - Bill OWNS these (NOT design projects)
- SM-WILD: Shinta Mani Wild operations, bookings, P&L
- SM-MUSTANG: Shinta Mani Mustang operations
- SM-ANGKOR: Shinta Mani Angkor operations
- SM-FOUNDATION: Shinta Mani Foundation charity, monthly reports

### Personal (PERS-*) - Bill's personal matters
- PERS-ART: Bill's art gallery, paintings, exhibitions, art sales
- PERS-INVEST: Land sales, investments, property deals
- PERS-FAMILY: Personal family matters
- PERS-PRESS: Interviews, speaking engagements, lectures

### Marketing/Brand (MKT-*)
- MKT-SOCIAL: Instagram, content creation, engagement
- MKT-PRESS: Press coverage, articles, awards
- MKT-WEB: Website analytics, updates

### Skip (SKIP-*) - Don't process
- SKIP-SPAM: Marketing spam (Unanet, Pipedrive, newsletters)
- SKIP-AUTO: System notifications we don't need
- SKIP-DUP: Already processed

## Your Task
Analyze the email below and return a JSON object with suggestions.

**IMPORTANT: SUGGEST ONLY MODE**
- ALL suggestions go to human review - you are NOT auto-linking anything
- Your job is to suggest the MOST LIKELY project link with evidence
- A human will approve/reject/correct every suggestion
- It's better to suggest with lower confidence than to miss a valid link
- Only set skip_reason if the email is definitely NOT project-related

## Response Format (JSON only, no markdown)
{{
  "email_classification": {{
    "type": "internal" | "client_external" | "operator_external" | "developer_external" | "consultant_external" | "vendor_external" | "spam" | "administrative",
    "direction": "internal_to_internal" | "internal_to_external" | "external_to_internal" | "external_to_external",
    "is_project_related": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of classification"
  }},
  "universe_category": {{
    "primary_category": "BDS" | "INT" | "SM" | "PERS" | "MKT" | "SKIP",
    "subcategory": "INT-FIN" | "INT-OPS" | "INT-HR" | "INT-LEGAL" | "INT-SCHED" | "INT-DAILY" | "SM-WILD" | "SM-MUSTANG" | "SM-ANGKOR" | "SM-FOUNDATION" | "PERS-ART" | "PERS-INVEST" | "PERS-FAMILY" | "PERS-PRESS" | "MKT-SOCIAL" | "MKT-PRESS" | "MKT-WEB" | "SKIP-SPAM" | "SKIP-AUTO" | "SKIP-DUP" | null,
    "action_type": "invoice" | "contract" | "scheduling" | "status_update" | "report" | "inquiry" | "notification" | null,
    "confidence": 0.0-1.0,
    "reasoning": "why this category fits"
  }},
  "email_links": [
    {{
      "project_code": "XX BK-XXX",
      "project_name": "name",
      "confidence": 0.0-1.0,
      "is_primary": true/false,
      "reasoning": "why this email relates to this project",
      "evidence": ["specific evidence 1", "specific evidence 2"]
    }}
  ],
  "new_contact": {{
    "should_create": true/false,
    "confidence": 0.0-1.0,
    "name": "Full Name",
    "email": "email@domain.com",
    "inferred_company": "Company Name" or null,
    "inferred_role": "client" | "operator" | "developer" | "consultant" | "vendor" | "internal" | null
  }} or null,
  "status_update": {{
    "should_update": true/false,
    "confidence": 0.0-1.0,
    "project_code": "XX BK-XXX",
    "current_status": "proposal",
    "suggested_status": "inquiry/meeting_scheduled/nda_signed/proposal_prep/submitted/negotiation/revision_requested/revised/won/on_hold/lost",
    "reasoning": "why status should change - be specific about the lifecycle signal detected"
  }} or null,
  "stale_proposal": {{
    "is_stale": true/false,
    "project_code": "XX BK-XXX",
    "days_inactive": number,
    "suggested_action": "follow up with client"
  }} or null,
  "conversation_state": {{
    "waiting_for": "client_response" | "our_response" | "meeting" | "payment" | "decision" | null,
    "last_action": "proposal_sent" | "question_asked" | "question_answered" | "revision_requested" | "approved" | null,
    "next_action_needed": "specific action description" or null
  }} or null,
  "action_items": [
    {{
      "should_create": true/false,
      "confidence": 0.0-1.0,
      "task_title": "Clear, actionable title",
      "task_description": "Details from email context",
      "assignee_hint": "us" | "them" | "specific_name",
      "due_date_hint": "YYYY-MM-DD" or null,
      "priority_hint": "critical" | "high" | "medium" | "low",
      "source_quote": "The exact text that triggered this detection"
    }}
  ],
  "meeting_detected": {{
    "detected": true/false,
    "meeting_type": "request" | "confirmation" | "follow_up" | "reschedule",
    "proposed_date": "YYYY-MM-DD" or null,
    "proposed_time": "HH:MM" or null,
    "participants": ["Name (role)", ...],
    "meeting_purpose": "What the meeting is about",
    "location_hint": "Zoom" | "Office" | "Client Site" | null,
    "confidence": 0.0-1.0,
    "source_quote": "The exact text about the meeting"
  }} or null,
  "deliverables": [
    {{
      "detected": true/false,
      "deliverable_type": "schematic" | "concept" | "contract" | "drawings" | "presentation" | "other",
      "deadline_date": "YYYY-MM-DD" or null,
      "milestone_status": "pending" | "completed" | "delayed",
      "description": "Context from email",
      "confidence": 0.0-1.0
    }}
  ],
  "commitments": [
    {{
      "commitment_type": "our_commitment" | "their_commitment",
      "commitment_description": "What was promised",
      "committed_by": "Who made the commitment",
      "due_date": "YYYY-MM-DD" or null,
      "confidence": 0.0-1.0,
      "source_quote": "The exact text of the commitment"
    }}
  ],
  "relationship_insight": {{
    "has_insight": true/false,
    "contact_email": "email",
    "insight": "works across multiple projects",
    "projects_involved": ["XX BK-XXX", ...]
  }} or null,
  "new_proposal": {{
    "should_create": true/false,
    "confidence": 0.0-1.0,
    "suggested_name": "Project Name - Location",
    "suggested_client": "Company or Person Name",
    "contact_name": "Contact Person",
    "contact_email": "email@domain.com",
    "location": "City, Country",
    "project_type": "hotel" | "resort" | "residence" | "restaurant" | "mixed_use" | "other",
    "reasoning": "Why this appears to be a new project inquiry"
  }} or null,
  "skip_reason": "reason to not process" or null
}}

## Email Classification Types
- **internal**: ANY email where sender domain is @bensley.com OR @bensleydesign.com (regardless of folder - INBOX or SENT)
- **client_external**: Direct client correspondence (the paying customer) - sender is NOT @bensley.com
- **operator_external**: Hotel operators (Four Seasons, Rosewood, Capella, Marriott, etc.)
- **developer_external**: Owner/developer (the entity paying for the hotel development)
- **consultant_external**: External consultants (kitchen, lighting, landscape subconsultants, engineers)
- **vendor_external**: Suppliers, vendors, product reps
- **spam**: Marketing, newsletters, vendor cold outreach
- **administrative**: Finance, legal, HR, not project-specific

## CRITICAL: Internal Email Detection
**ALWAYS check the sender's email domain FIRST:**
- If sender ends with @bensley.com → type = "internal"
- If sender ends with @bensleydesign.com → type = "internal"
- If sender ends with @bensley.co.th → type = "internal"
- If sender ends with @bensley.id → type = "internal"
- If sender is listed in "Known Staff (Personal Emails)" below → type = "internal"
- This applies to ALL folders (INBOX, SENT, etc.)
- Only classify as client_external/operator_external/etc. if sender is NOT from Bensley domains AND not a known staff member

## Multi-Project Linking Rules
- ONE email can link to MULTIPLE projects if it discusses multiple
- Set is_primary=true for the main project being discussed
- Set is_primary=false for secondary mentions
- Include links with confidence >= 0.4 (human reviews everything)
- ALWAYS provide evidence array with specific reasons

## CRITICAL: Project Code Rules
**NEVER output placeholder project codes like "XX BK-XXX" or "25 BK-XXX"**
- ONLY use project codes that appear in the Active Proposals list provided below
- If you cannot confidently match to a specific project, return an EMPTY email_links array: []
- Do NOT guess or make up project codes
- Each project_code must exactly match one from the Active Proposals list

## Rules
1. For Shinta Mani emails: Check if it's about DESIGN work (link to project) vs OWNERSHIP/P&L/hotel operations (don't link, classify as administrative)
2. Multi-project contacts (listed below) should still have their emails analyzed for content - link based on what's discussed, not who sent it
3. Only suggest new contacts if sender is not already known
4. Status updates: Look for signals in client emails (see Status Signal Detection below)
5. If email is spam, newsletter, or irrelevant, set skip_reason and classify as spam
6. For SENT emails (from Bensley), the recipient determines classification, not sender
7. CC'd contacts can indicate which project - if John is CC'd, email likely relates to John's project
8. INTERNAL CIRCULATION emails (Bensley staff sending to Bensley staff) should NOT trigger status updates - these are internal reviews/discussions, not client communications

## EXPLICIT SKIP PATTERNS - Always skip these (set skip_reason):
**Spam/System Emails (skip_reason = "automated_system"):**
- Unanet timesheets, D365, NaviWorld, BOS system notifications
- Pipedrive, HubSpot, Monday.com, Asana notifications
- Password resets, verification codes
- Birthday greetings, out of office replies
- Zoom/Teams meeting notifications
- Dropbox, Google Drive share notifications
- Newsletter subscriptions, marketing emails

**Administrative (skip_reason = "administrative"):**
- HR announcements, policy updates
- IT system maintenance notices
- General office announcements
- Holiday schedules, office closures

## Proposal Lifecycle & Status Signal Detection

**LIFECYCLE STAGES WITH NUMERIC ORDER (CRITICAL - status can ONLY move FORWARD):**
```
Stage 1: inquiry → Stage 2: meeting_scheduled → Stage 3: nda_signed → Stage 4: proposal_prep → Stage 5: submitted → Stage 6: negotiation → Stage 7: revision_requested → Stage 8: revised → Stage 9: won → Stage 10: active_project
```

**VALIDATION RULE - NEVER VIOLATE:**
- Only suggest status change if NEW_STAGE_NUMBER > CURRENT_STAGE_NUMBER
- Example: if current status is "negotiation" (stage 6), can ONLY suggest stage 7+ (revision_requested, revised, won)
- NEVER suggest going backwards (e.g., won → negotiation, submitted → proposal_prep)
- Exception: on_hold/lost can be suggested from any stage after submitted

**Stage mapping:**
- inquiry = 1, proposal = 1 (legacy alias)
- meeting_scheduled = 2
- nda_signed = 3
- proposal_prep = 4
- submitted = 5, proposal_sent = 5 (legacy alias)
- negotiation = 6
- revision_requested = 7
- revised = 8
- won = 9
- active_project = 10
- on_hold = special (from any stage 5+)
- lost = special (from any stage 5+)

**LIFECYCLE STAGES:**

1. **inquiry** (Stage 1) - new lead comes in
   - First contact from potential client
   - Initial project discussion
   - "We have a project we'd like to discuss"

2. **meeting_scheduled** (Stage 2) - initial engagement
   - Call/meeting set up to learn about the project
   - "Let's schedule a call to discuss"
   - "Looking forward to our meeting on Tuesday"

3. **nda_signed** (Stage 3) - moving forward
   - NDA requested, sent, or signed
   - "Please find attached our signed NDA"
   - "Attaching the mutual NDA"

4. **proposal_prep** (Stage 4) - we're working on proposal
   - Internal work happening
   - Gathering information for proposal
   - "We're putting together the proposal"
   - Client sends project brief, site plans, requirements

5. **submitted** (Stage 5 - CRITICAL - proposal sent!) - conf 0.9+
   - "Attached is our proposal and fee structure"
   - "Please find attached our proposal"
   - "Sending over the fee proposal"
   - "Here is our scope and pricing"
   - We send a PDF with fees/scope

6. **negotiation** (Stage 6) - discussing the proposal - conf 0.85+
   - Client responds to submitted proposal
   - Discussing fees, scope, terms
   - "Can we discuss the pricing?"
   - "We'd like to modify the scope"
   - "The budget is tight, can we adjust?"

7. **revision_requested** (Stage 7) - they want changes - conf 0.85+
   - Clear request to revise proposal
   - "Please revise to include/exclude..."
   - "We need an alternative option"

8. **revised** (Stage 8) - we sent updated proposal - conf 0.9+
   - "Attached is the revised proposal"
   - "Updated fee structure as discussed"

9. **won** (Stage 9) - contract signed! - conf 0.95+
   - "We accept your proposal"
   - "Let's proceed"
   - "Contract signed"
   - Request for mobilization invoice
   - "Please send the first invoice"

   **WARNING - These are NOT "won" signals:**
   - "Let's schedule a kick-off meeting" (no contract signed yet!)
   - "Site visit scheduled" (doesn't mean agreement reached)
   - "Looking forward to working together" (just pleasantries)
   Only mark as "won" when there's EXPLICIT acceptance, signed contract, or payment request

10. **on_hold** (Special) - paused but not dead - conf 0.85+
    - "Need to pause this project"
    - "Timeline pushed to next year"
    - "Budget constraints, will revisit"

11. **lost** (Special) - not proceeding - conf 0.9+
    - "Decided to go with another firm"
    - "Project cancelled"
    - "Not proceeding"
    - Too expensive, chose competitor

**OUTGOING EMAIL DETECTION (from Bensley):**
When analyzing SENT emails from @bensley.com:
- "Attached is our proposal" → submitted (Stage 5)
- "Here is our fee structure" → submitted (Stage 5)
- "Sending the revised proposal" → revised (Stage 8)
- "Updated scope as discussed" → revised (Stage 8)
These are HIGH CONFIDENCE signals (0.9+)

**DO NOT suggest status changes for:**
- Internal Bensley emails (Bensley → Bensley)
- Generic pleasantries or acknowledgements
- Questions without lifecycle signals
- Status that would move BACKWARDS - CHECK THE STAGE NUMBERS!

## New Proposal Detection
**Suggest creating a new proposal when ALL of these are true:**
1. Email is from an EXTERNAL sender (not @bensley.com)
2. Email discusses a SPECIFIC project/location that does NOT match any existing proposal
3. Email shows genuine business interest (inquiry, RFP, meeting request about new work)
4. You can identify: project location, client/company name, contact person

**Signals for new_proposal (conf 0.8+):**
- New client asking about design services for a specific property
- Inquiry about a location/project not in the Active Proposals list
- RFP or project brief for a new development
- Referral introduction for a new project
- Developer/owner reaching out about a new site

**DO NOT suggest new_proposal for:**
- Internal Bensley emails
- Emails that match an existing proposal (even if sender is new)
- Generic inquiries without specific project details
- Vendors, recruiters, spam, newsletters
- Existing clients discussing existing projects

**When suggesting new_proposal:**
- suggested_name: Use format "Project Name - Location" (e.g., "Rashmi Villa - Kolkata")
- Extract as much detail as possible from the email
- Set confidence based on how clear the project details are

## Conversation State & Action Items
Always analyze the email for:
- Who needs to respond next? (waiting_for)
- What specific action is needed? (next_action_needed)
- If we need to respond, describe the specific action clearly

## Follow-Up Detection (CRITICAL)
The Active Proposals list below includes last email activity. Look for:
- **🔴 NEEDS FOLLOW-UP** flags = proposal submitted 14+ days ago, we sent last, no response
- **⚠️ WE sent last** = we're waiting for their response

**Generate stale_proposal suggestion when:**
1. Proposal status is "submitted" AND
2. We sent the last email (we_sent_last = true) AND
3. Days since last email > 14 AND
4. Current email is related to this project (confirms it's still relevant)

**stale_proposal format:**
- is_stale: true
- project_code: the stale project
- days_inactive: days since last email
- suggested_action: "Follow up with [contact name] on proposal status"

This helps Bill know which proposals need attention!

## Action Item Detection (CRITICAL - extract tasks from emails!)
Analyze the email for explicit or implied action items. Look for:

**Direct Requests (confidence 0.8+):**
- "Please send", "Can you review", "Need you to", "Could you"
- "Please provide", "Kindly share", "We request"
- "Let me know", "Get back to me", "Respond by"

**Questions Requiring Response (confidence 0.7+):**
- "What is your availability?", "When can we schedule?"
- "Can we discuss?", "What do you think about?"
- "Have you had a chance to review?"

**Implied Actions (confidence 0.6+):**
- "The contract needs your signature"
- "We're waiting for the plans"
- "Awaiting your feedback"

For each detected action item:
- task_title: Clear, actionable (e.g., "Review site plans and provide feedback")
- assignee_hint: "us" (Bensley needs to do), "them" (client/external), or specific name
- due_date_hint: Extract date if mentioned, null otherwise
- priority_hint: Use urgency language - "ASAP"/"urgent" = critical, "soon" = high, "when you can" = medium
- source_quote: The exact text that triggered detection

## Meeting Detection
Detect meeting-related content in emails:

**Meeting Requests (confidence 0.8+):**
- "Can we schedule a call?", "Available for a meeting?"
- "Let's set up a time to discuss", "I'd like to meet"
- "Can we do a Zoom/Teams call?"

**Meeting Confirmations (confidence 0.85+):**
- "Confirmed for Tuesday 2pm", "See you on the 15th"
- "The meeting is set for", "Looking forward to our call"
- Specific date AND time mentioned together

**Meeting Follow-ups (confidence 0.7+):**
- "Following up from our call yesterday"
- "As discussed in our meeting"
- "Per our conversation"

**Meeting Reschedules (confidence 0.8+):**
- "Can we reschedule?", "Need to move the meeting"
- "Something came up, can we find a new time?"

Include meeting_detected with:
- meeting_type: request, confirmation, follow_up, reschedule
- proposed_date/time: ISO format if mentioned
- participants: Names and roles if mentioned
- meeting_purpose: Brief description of what meeting is about
- location_hint: Zoom, Office, Client Site, Site Visit, etc.

## Deadline/Deliverable Detection
Look for deadline and milestone mentions:

**Explicit Deadlines (confidence 0.85+):**
- "Due by January 15", "Deadline is Friday"
- "Must submit by end of month", "Required by Q1"
- "Target completion date"

**Milestone Completions (confidence 0.8+):**
- "Client approved the design", "Phase 1 completed"
- "Schematic submitted", "CD package signed off"
- "We've finished the", "Drawings are ready"

**Timeline Updates (confidence 0.75+):**
- "Pushed to Q2", "Extended deadline to March"
- "Ahead of schedule", "Behind schedule by 2 weeks"
- "Timeline revised to"

Include deliverables with:
- deliverable_type: schematic, concept, contract, drawings, presentation, other
- deadline_date: ISO format if mentioned
- milestone_status: pending, completed, delayed
- description: Context about the deliverable

## Commitment Detection (Track Promises!)
Track commitments made by either party:

**Our Commitments (Bensley promises - confidence 0.8+):**
- "I'll send you the proposal by Friday"
- "We will have the drawings ready next week"
- "Brian will prepare the contract"
- "Let me get back to you by tomorrow"

**Their Commitments (Client/External promises - confidence 0.8+):**
- "We'll make a decision by March"
- "They will review and get back to us"
- "Client to provide site survey by next week"
- "We'll send payment upon receipt"

Include commitments with:
- commitment_type: our_commitment OR their_commitment
- commitment_description: What was promised
- committed_by: Who made the commitment (name or "us"/"them")
- due_date: When it should be fulfilled (if mentioned)
- source_quote: The exact text of the commitment

**Why this matters:** Unfulfilled commitments become action items!

{active_proposals}

{learned_patterns}

{multi_project_contacts}
"""

    def __init__(self, model: str = "gpt-4o-mini", max_tokens: int = 1000):
        """
        Initialize the analyzer.

        Args:
            model: OpenAI model to use
            max_tokens: Maximum tokens for response
        """
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    def analyze_email(
        self,
        email: Dict[str, Any],
        context_prompt: str,
    ) -> Dict[str, Any]:
        """
        Analyze a single email with GPT.

        Args:
            email: Email data (subject, body, sender, date)
            context_prompt: Pre-formatted context from ContextBundler

        Returns:
            Dict with analysis results and usage stats
        """
        start_time = time.time()

        # Build the system prompt with context
        system_prompt = self.SYSTEM_PROMPT_TEMPLATE.format(
            business_context=context_prompt.split("## Active Proposals")[0] if "## Active Proposals" in context_prompt else context_prompt[:2000],
            active_proposals=self._extract_section(context_prompt, "## Active Proposals"),
            learned_patterns=self._extract_section(context_prompt, "## Learned Email Patterns"),
            multi_project_contacts=self._extract_section(context_prompt, "## Multi-Project Contacts"),
        )

        # Format email for user message
        user_message = self._format_email_message(email)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=self.max_tokens,
                temperature=0.1,  # Low temperature for consistent output
                response_format={"type": "json_object"},
            )

            # Parse response
            content = response.choices[0].message.content
            analysis = json.loads(content)

            # Calculate costs
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = self._calculate_cost(input_tokens, output_tokens)

            processing_time = int((time.time() - start_time) * 1000)

            return {
                "success": True,
                "analysis": analysis,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "estimated_cost_usd": cost,
                    "processing_time_ms": processing_time,
                    "model": self.model,
                },
                "email_id": email.get("email_id"),
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT response as JSON: {e}")
            return {
                "success": False,
                "error": f"JSON parse error: {str(e)}",
                "email_id": email.get("email_id"),
            }

        except Exception as e:
            logger.error(f"GPT API call failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "email_id": email.get("email_id"),
            }

    def analyze_batch(
        self,
        emails: List[Dict[str, Any]],
        context_prompt: str,
        max_workers: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple emails with shared context using parallel processing.

        Args:
            emails: List of email data dicts
            context_prompt: Pre-formatted context from ContextBundler
            max_workers: Max concurrent API calls (default 10, OpenAI allows 500 RPM)

        Returns:
            List of analysis results in same order as input emails
        """
        results = [None] * len(emails)  # Preserve order
        total_cost = 0.0
        total_input_tokens = 0
        total_output_tokens = 0

        def analyze_with_index(args):
            idx, email = args
            return idx, self.analyze_email(email, context_prompt)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(analyze_with_index, (i, email)): i
                for i, email in enumerate(emails)
            }

            for future in as_completed(futures):
                try:
                    idx, result = future.result()
                    results[idx] = result

                    if result.get("success") and result.get("usage"):
                        total_cost += result["usage"].get("estimated_cost_usd", 0)
                        total_input_tokens += result["usage"].get("input_tokens", 0)
                        total_output_tokens += result["usage"].get("output_tokens", 0)
                except Exception as e:
                    idx = futures[future]
                    logger.error(f"Failed to analyze email at index {idx}: {e}")
                    results[idx] = {
                        "success": False,
                        "error": str(e),
                    }

        logger.info(
            f"Batch analysis complete: {len(emails)} emails, "
            f"${total_cost:.4f} cost, "
            f"{total_input_tokens} input tokens, "
            f"{total_output_tokens} output tokens"
        )

        return results

    def _format_email_message(self, email: Dict[str, Any]) -> str:
        """Format email data for GPT user message, including thread context"""
        sender = email.get("sender_email", "Unknown")
        recipients = email.get("recipient_emails", "Unknown")
        subject = email.get("subject", "No subject")
        body = email.get("body_full", email.get("body", ""))[:3000]  # Limit body length
        date = email.get("date", "Unknown date")
        folder = email.get("folder") or "INBOX"

        # Check if it's a sent email
        is_sent = folder.upper() in ("SENT", "SENT ITEMS", "[GMAIL]/SENT MAIL")

        # Check if recipients are internal (all @bensley.com)
        recipients_internal = False
        if recipients and recipients != "Unknown":
            recipients_lower = recipients.lower()
            # Check if ALL recipients are internal
            recipients_internal = ("@bensley.com" in recipients_lower or
                                   "@bensleydesign.com" in recipients_lower or
                                   "@bensley.co.th" in recipients_lower) and \
                                  not any(ext in recipients_lower for ext in
                                         ["@gmail.com", "@yahoo.com", "@hotmail.com", "@outlook.com"])

        # Build recipient context
        recipient_context = ""
        if is_sent:
            if recipients_internal:
                recipient_context = "(INTERNAL CIRCULATION - sent to Bensley staff, NOT to client)"
            else:
                recipient_context = "(SENT TO EXTERNAL - this is outgoing to client/partner)"

        message = f"""## Email to Analyze

**From:** {sender}
**To:** {recipients}
**Subject:** {subject}
**Date:** {date}
**Folder:** {folder} {recipient_context}

**Body:**
{body}
"""

        # Add thread context if available
        thread_context = email.get("thread_context")
        if thread_context:
            message += self._format_thread_context(thread_context)

        return message

    def _format_thread_context(self, thread_context: Dict[str, Any]) -> str:
        """Format thread context for GPT to understand the conversation"""
        parts = ["\n\n## Thread Context (IMPORTANT - use this to understand the conversation)"]

        email_count = thread_context.get("email_count", 0)
        parts.append(f"\n**Thread has {email_count} emails total**")

        # Show if thread is already linked to a project - THIS IS THE KEY FOR INHERITANCE
        existing_links = thread_context.get("existing_project_links")
        if existing_links:
            parts.append("\n**⚠️ OTHER EMAILS IN THIS THREAD ARE ALREADY LINKED TO:**")
            for link in existing_links:
                linked_count = link.get("linked_email_count", 1)
                parts.append(f"- {link.get('project_code')}: {link.get('project_name')} ({linked_count} emails linked)")
            parts.append("**→ This email should likely link to the SAME project!**")

        # Show external participants (these help identify the project)
        external_participants = thread_context.get("external_participants", [])
        if not external_participants:
            # Fallback to old format
            participants = thread_context.get("participants", [])
            external_participants = [p for p in participants if "@bensley.com" not in p.lower()]

        if external_participants:
            parts.append(f"\n**External participants in this thread:** {', '.join(external_participants[:5])}")

        # Show conversation state
        conv_state = thread_context.get("conversation_state", {})
        if conv_state:
            waiting_for = conv_state.get("waiting_for")
            days_since = conv_state.get("days_since_last_email")
            if waiting_for:
                if waiting_for == "our_response":
                    parts.append(f"\n**Conversation state:** Waiting for Bensley to respond")
                else:
                    parts.append(f"\n**Conversation state:** Waiting for client/external response")
            if days_since and days_since > 0:
                parts.append(f"**Days since last email:** {days_since}")
                if conv_state.get("needs_followup"):
                    parts.append("**⚠️ May need follow-up (>7 days since we sent)**")

        # Show thread starter
        thread_starter = thread_context.get("thread_starter")
        if thread_starter:
            parts.append(f"\n**Thread started by:** {thread_starter.get('sender_email', 'Unknown')}")

        # Show thread email history (abbreviated) with direction
        thread_emails = thread_context.get("emails", [])
        if thread_emails:
            parts.append(f"\n**Thread history ({len(thread_emails)} previous emails):**")

            # Direction icons
            direction_icons = {
                "external_to_internal": "📥",  # Client → Us
                "internal_to_external": "📤",  # Us → Client
                "internal_to_internal": "🔄",  # Internal discussion
            }

            for email in thread_emails[:5]:  # Limit to 5 most relevant
                sender = email.get("sender_email", "Unknown")
                snippet = (email.get("snippet") or "")[:100]
                is_linked = "✓" if email.get("is_linked") else ""
                direction = email.get("direction", "")
                icon = direction_icons.get(direction, "")

                direction_label = ""
                if direction == "internal_to_internal":
                    direction_label = "(internal fwd)"

                parts.append(f"- {icon} From: {sender} {is_linked} {direction_label}")
                if snippet:
                    parts.append(f"  \"{snippet}...\"")

        return "\n".join(parts)

    def _extract_section(self, context: str, section_header: str) -> str:
        """Extract a section from the context prompt"""
        if section_header not in context:
            return ""

        start = context.find(section_header)
        # Find next section or end
        next_section = context.find("\n## ", start + len(section_header))
        if next_section == -1:
            return context[start:]
        return context[start:next_section]

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost based on token usage"""
        pricing = GPT_PRICING.get(self.model, GPT_PRICING["gpt-4o-mini"])

        input_cost = (input_tokens / 1_000_000) * pricing["input_per_1m"]
        output_cost = (output_tokens / 1_000_000) * pricing["output_per_1m"]

        return round(input_cost + output_cost, 6)


class GPTUsageTracker:
    """
    Tracks GPT API usage for cost monitoring.

    Writes to gpt_usage_log table in database.
    """

    def __init__(self, db_connection):
        """
        Initialize tracker with database connection.

        Args:
            db_connection: SQLite connection object
        """
        self.conn = db_connection

    def log_usage(
        self,
        request_type: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        estimated_cost: float,
        email_ids: List[int],
        processing_time_ms: int,
        success: bool = True,
        error_message: str = None,
    ):
        """Log a GPT API request to the database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO gpt_usage_log (
                    request_type, model, input_tokens, output_tokens,
                    estimated_cost_usd, email_ids, batch_size,
                    processing_time_ms, success, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request_type,
                model,
                input_tokens,
                output_tokens,
                estimated_cost,
                json.dumps(email_ids),
                len(email_ids),
                processing_time_ms,
                1 if success else 0,
                error_message,
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to log GPT usage: {e}")

    def get_daily_cost(self, date: str = None) -> float:
        """Get total cost for a specific date (default today)"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(estimated_cost_usd), 0) as total
            FROM gpt_usage_log
            WHERE DATE(created_at) = ?
        """, (date,))
        return cursor.fetchone()[0]

    def get_monthly_cost(self, year_month: str = None) -> float:
        """Get total cost for a specific month (default current month)"""
        if year_month is None:
            year_month = datetime.now().strftime("%Y-%m")

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(estimated_cost_usd), 0) as total
            FROM gpt_usage_log
            WHERE strftime('%Y-%m', created_at) = ?
        """, (year_month,))
        return cursor.fetchone()[0]
