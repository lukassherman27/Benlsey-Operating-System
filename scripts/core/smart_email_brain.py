#!/usr/bin/env python3
"""
Smart Email Brain - Context-Aware Email Processing with Learning

This is the UPGRADED email processor that:
1. Feeds full business context to AI (proposals, projects, contacts)
2. Extracts suggestions for new information
3. Queues suggestions for human approval
4. Learns from approvals/rejections over time

Usage:
    python3 smart_email_brain.py --batch-size 100 --review
    python3 smart_email_brain.py --show-suggestions
    python3 smart_email_brain.py --approve-suggestion 123
"""
import sqlite3
import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')

# Add backend to path for AILearningService
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backend')
sys.path.insert(0, backend_path)

try:
    from services.ai_learning_service import AILearningService
    AI_LEARNING_ENABLED = True
except ImportError:
    AI_LEARNING_ENABLED = False
    print("⚠️ AILearningService not available - advanced suggestions disabled")


class SmartEmailBrain:
    def __init__(self):
        self.db_path = DB_PATH
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.api_calls = 0
        self.estimated_cost = 0.0
        self.suggestions_created = 0

        # Initialize AI Learning Service for advanced suggestions
        self.learning_service = None
        if AI_LEARNING_ENABLED:
            try:
                self.learning_service = AILearningService(DB_PATH)
                print("✅ AI Learning Service connected - suggestions will flow to learning system")
            except Exception as e:
                print(f"⚠️ AI Learning Service init failed: {e}")

        # Load context on init
        self.proposals = []
        self.contacts = []
        self.learned_patterns = []
        self.business_context = ""

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def load_context(self):
        """Load all business context for the AI"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 1. Load proposals (pre-contract opportunities)
        cursor.execute("""
            SELECT project_code, project_name, client_company, contact_person,
                   contact_email, status, country, location
            FROM proposals
            ORDER BY project_code
        """)
        self.proposals = [dict(row) for row in cursor.fetchall()]

        # 2. Load projects (won contracts - active and archived)
        cursor.execute("""
            SELECT project_code, project_title as project_name,
                   notes as client_info, status, country
            FROM projects
            ORDER BY project_code
        """)
        self.projects = [dict(row) for row in cursor.fetchall()]

        # 3. Load contacts
        cursor.execute("""
            SELECT name, email, role
            FROM contacts
            WHERE email IS NOT NULL
        """)
        self.contacts = [dict(row) for row in cursor.fetchall()]

        # 4. Load learned patterns (new schema from migration 032)
        cursor.execute("""
            SELECT pattern_name, pattern_type, condition, action, confidence_score
            FROM learned_patterns
            WHERE is_active = 1 AND confidence_score > 0.5
            ORDER BY confidence_score DESC
        """)
        self.learned_patterns = [dict(row) for row in cursor.fetchall()]

        conn.close()

        # Build context string
        self._build_business_context()

        print(f"Loaded context: {len(self.proposals)} proposals, {len(self.projects)} projects, {len(self.contacts)} contacts, {len(self.learned_patterns)} patterns")

    def _build_business_context(self):
        """Build the business context prompt section"""

        # Proposals summary - include ALL for accurate linking
        proposal_lines = []
        for p in self.proposals:  # ALL proposals
            line = f"  {p['project_code']}: {p['project_name'][:40]} [PROPOSAL]"
            if p['contact_person']:
                line += f" | Contact: {p['contact_person']}"
            if p['client_company']:
                line += f" | Client: {p['client_company'][:20]}"
            proposal_lines.append(line)

        # Projects summary - active and archived contracts
        project_lines = []
        for p in self.projects:  # ALL projects
            status = p.get('status') or 'active'
            name = p.get('project_name') or 'Unnamed Project'
            code = p.get('project_code') or 'NO-CODE'
            line = f"  {code}: {name[:40]} [{status.upper()}]"
            project_lines.append(line)

        # Contact emails for matching
        contact_emails = [c['email'] for c in self.contacts if c['email']]

        # Learned aliases and patterns
        aliases = [p for p in self.learned_patterns if p['pattern_type'] == 'project_alias']

        self.business_context = f"""
=== BENSLEY DESIGN STUDIO (BDS) BUSINESS CONTEXT ===

PROPOSALS (pre-contract opportunities - {len(self.proposals)} total):
{chr(10).join(proposal_lines)}

WON PROJECTS (active and archived contracts - {len(self.projects)} total):
{chr(10).join(project_lines)}

KNOWN CONTACTS ({len(contact_emails)} total):
{', '.join(contact_emails[:30])}...

LEARNED PROJECT ALIASES:
{chr(10).join([f"  {a['pattern_key']} → {a['pattern_value']}" for a in aliases[:20]])}

=== CRITICAL BUSINESS DISTINCTIONS ===

1. BENSLEY DESIGN STUDIO (BDS) - Main Design Business (is_bds_work = true):
   - Proposals: Pre-contract opportunities (codes: "24 BK-XXX", "25 BK-XXX")
   - Active Projects: Won contracts, design delivery in progress
   - Client Types: Hotels (Marriott, Ritz-Carlton, Four Seasons), Developers, Private Residences
   - Work includes: Master planning, architecture, interior design, landscape design
   - Categories for BDS: contract, design, financial, meeting, rfi

2. SHINTA MANI - Bill's Hotel Company (is_bds_work = false):

   A) SHINTA MANI AS CLIENT (is_bds_work = TRUE):
      - When BDS is DESIGNING a new Shinta Mani property
      - Proposal/contract for design services
      - Example: "Shinta Mani Mustang" - BDS designing new property

   B) SHINTA MANI OPERATIONS (is_bds_work = FALSE, category: "other/shinta_mani_ops"):
      - Hotel operations updates (occupancy, F&B, guest issues)
      - Staff matters at Shinta Mani hotels
      - Renovation updates on existing properties Bill owns
      - Keywords: "Wild", "Angkor", "Bensley Collection", room rates, guests

   C) SHINTA MANI FOUNDATION (is_bds_work = FALSE, category: "other/foundation"):
      - Charity work, community programs
      - Hospital, school projects in Cambodia
      - Donations, fundraising
      - Keywords: "foundation", "charity", "community", "donate"

3. BILL'S PERSONAL (is_bds_work = false, category: "other/personal"):
   - Land sales (e.g., Bali property sale)
   - Personal residences not client work
   - Social invitations, travel arrangements
   - Keywords: "personal", "private sale", "my land", "villa sale"

4. INTERNAL ADMIN (is_bds_work = false, category: "internal/admin"):
   - HR matters, staff issues, payroll
   - Office management, IT, supplies
   - Thai business registration, taxes
   - Internal team scheduling (vacation, sick leave)

=== SCHEDULING TYPES ===
- "meeting/client_presentation" - Presenting designs to clients
- "meeting/project_kickoff" - Starting new project
- "meeting/design_review" - Internal or client design review
- "design/deliverable_deadline" - Drawing submission deadlines
- "internal/team_schedule" - Staff vacation, internal meetings

=== KEY PEOPLE ===
- Bill Bensley (bill@bensley.com): Founder/Principal, design visionary. Some emails are personal.
- Brian Sherman (bsherman@bensley.com): Director, handles contracts, legal, financials
- Lukas Sherman (lukas@bensley.com): Business development, proposals, new clients
- Lek/Jiraporn: Thai accounting, invoices
- Thippawan (accountant@bensley.com): Financial controller

=== FEE/CONTRACT TERMS ===
- Mobilization Fee: Upfront payment (usually 15-20% of total)
- Design Phases: Schematic Design (SD), Design Development (DD), Construction Documents (CD)
- Construction Observation (CO): Site visits during construction
- NDA: Non-disclosure agreement (pre-proposal)
- LOI: Letter of Intent
- SOW/Scope of Work: Defines what BDS will deliver
"""

    # ==========================================================================
    # TIERED CATEGORIZATION - Skip AI for obvious cases
    # ==========================================================================

    def _tier1_pattern_categorization(self, email: Dict) -> Optional[Dict]:
        """
        Tier 1: Instant categorization for obvious patterns (NO AI cost).
        Returns full analysis dict if confident, None otherwise.
        """
        sender = email.get('sender_email', '').lower()
        subject = email.get('subject', '').lower()
        body = (email.get('body_full', '') or '')[:500].lower()

        # Social media / newsletters → Auto-categorize as non-BDS
        ignore_domains = ['linkedin.com', 'facebook.com', 'twitter.com',
                         'mailchimp.com', 'sendgrid.com', 'noreply',
                         'newsletter', 'marketing', 'promo']
        if any(d in sender for d in ignore_domains):
            return {
                'clean_body': '',
                'category': 'other',
                'subcategory': 'social_newsletter',
                'is_bds_work': False,
                'linked_project_code': None,
                'key_points': ['Auto-categorized: Newsletter/Social media'],
                'entities': {},
                'sentiment': 'neutral',
                'importance_score': 0.1,
                'ai_summary': 'Newsletter or social media notification - auto-categorized',
                'urgency_level': 'low',
                'action_required': False,
                'suggestions': {},
                '_tier': 1,
                '_confidence': 0.99
            }

        # Bensley internal emails (both .com and .co.id domains)
        if '@bensley.com' in sender or '@bensley.co.id' in sender:
            return {
                'clean_body': '',
                'category': 'internal',
                'subcategory': 'internal_communication',
                'is_bds_work': True,
                'linked_project_code': None,
                'key_points': ['Internal Bensley communication'],
                'entities': {},
                'sentiment': 'neutral',
                'importance_score': 0.5,
                'ai_summary': 'Internal email from Bensley team member',
                'urgency_level': 'low',
                'action_required': False,
                'suggestions': {},
                '_tier': 1,
                '_confidence': 0.95
            }

        # Invoices / payments
        if any(word in subject for word in ['invoice', 'payment', 'receipt', 'billing']):
            return {
                'clean_body': '',
                'category': 'financial',
                'subcategory': 'invoice_payment',
                'is_bds_work': True,
                'linked_project_code': None,
                'key_points': ['Financial document - invoice or payment related'],
                'entities': {},
                'sentiment': 'neutral',
                'importance_score': 0.7,
                'ai_summary': 'Invoice or payment related email',
                'urgency_level': 'medium',
                'action_required': False,
                'suggestions': {},
                '_tier': 1,
                '_confidence': 0.90
            }

        # Calendar / meeting invites
        if any(word in subject for word in ['meeting', 'calendar', 'invite', 'zoom', 'teams call']):
            return {
                'clean_body': '',
                'category': 'meeting',
                'subcategory': 'calendar_invite',
                'is_bds_work': True,
                'linked_project_code': None,
                'key_points': ['Meeting or calendar invitation'],
                'entities': {},
                'sentiment': 'neutral',
                'importance_score': 0.6,
                'ai_summary': 'Meeting invitation or calendar update',
                'urgency_level': 'medium',
                'action_required': False,
                'suggestions': {},
                '_tier': 1,
                '_confidence': 0.85
            }

        # Out-of-office / auto-replies - don't process these
        if any(phrase in body for phrase in ['out of office', 'automatic reply', 'auto-reply',
                                              'i am currently away', 'on vacation', 'on leave']):
            return {
                'clean_body': '',
                'category': 'other',
                'subcategory': 'auto_reply',
                'is_bds_work': False,
                'linked_project_code': None,
                'key_points': ['Auto-reply detected - no action needed'],
                'entities': {},
                'sentiment': 'neutral',
                'importance_score': 0.1,
                'ai_summary': 'Out-of-office or automatic reply - skipped',
                'urgency_level': 'low',
                'action_required': False,
                'suggestions': {},
                '_tier': 1,
                '_confidence': 0.95
            }

        # No-reply system emails
        if 'noreply' in sender or 'no-reply' in sender or 'donotreply' in sender:
            return {
                'clean_body': '',
                'category': 'other',
                'subcategory': 'system_notification',
                'is_bds_work': False,
                'linked_project_code': None,
                'key_points': ['System notification from no-reply address'],
                'entities': {},
                'sentiment': 'neutral',
                'importance_score': 0.2,
                'ai_summary': 'Automated system notification',
                'urgency_level': 'low',
                'action_required': False,
                'suggestions': {},
                '_tier': 1,
                '_confidence': 0.90
            }

        # RFI detection - high priority
        if any(phrase in subject for phrase in ['rfi', 'request for information', 'clarification needed']):
            return {
                'clean_body': '',
                'category': 'rfi',
                'subcategory': 'rfi_request',
                'is_bds_work': True,
                'linked_project_code': None,  # Will be linked in Tier 2
                'key_points': ['RFI detected - needs project linking'],
                'entities': {},
                'sentiment': 'neutral',
                'importance_score': 0.9,
                'ai_summary': 'Request for Information detected',
                'urgency_level': 'high',
                'action_required': True,
                'suggestions': {},
                '_tier': 1,
                '_confidence': 0.85
            }

        # Contract/legal documents
        if any(phrase in subject for phrase in ['contract', 'agreement', 'nda', 'mou', 'loi', 'amendment']):
            return {
                'clean_body': '',
                'category': 'contract',
                'subcategory': 'legal_document',
                'is_bds_work': True,
                'linked_project_code': None,
                'key_points': ['Contract or legal document detected'],
                'entities': {},
                'sentiment': 'neutral',
                'importance_score': 0.8,
                'ai_summary': 'Contract or legal document email',
                'urgency_level': 'medium',
                'action_required': False,
                'suggestions': {},
                '_tier': 1,
                '_confidence': 0.80
            }

        return None  # Not confident, proceed to Tier 2

    def _tier2_database_matching(self, email: Dict) -> Optional[Dict]:
        """
        Tier 2: Match against known contacts/projects (fast DB lookup).
        Returns analysis dict if matched, None otherwise.
        """
        sender = email.get('sender_email', '').lower().strip()
        subject = email.get('subject', '') or ''

        conn = self.get_connection()
        cursor = conn.cursor()

        # Check 1: Is sender a known proposal contact?
        cursor.execute("""
            SELECT p.project_code, p.project_name, p.client_company, p.status
            FROM proposals p
            WHERE LOWER(TRIM(p.contact_email)) = ?
            LIMIT 1
        """, (sender,))
        proposal = cursor.fetchone()

        if proposal:
            conn.close()
            return {
                'clean_body': '',
                'category': 'contract' if proposal['status'] in ('active', 'negotiating') else 'design',
                'subcategory': f"project_{proposal['status']}",
                'is_bds_work': True,
                'linked_project_code': proposal['project_code'],
                'key_points': [f"Email from known contact for {proposal['project_name']}"],
                'entities': {'companies': [proposal['client_company']] if proposal['client_company'] else []},
                'sentiment': 'neutral',
                'importance_score': 0.7,
                'ai_summary': f"Email from {proposal['project_code']} contact regarding {proposal['project_name']}",
                'urgency_level': 'medium',
                'action_required': False,
                'suggestions': {},
                '_tier': 2,
                '_confidence': 0.90,
                '_match_reason': 'sender_is_proposal_contact'
            }

        # NOTE: Removed domain-based company matching here too.
        # Reason: Hotel operators (Marriott, Four Seasons, etc.) work on MANY projects.
        # One domain ≠ one project. This caused incorrect linking.

        # Check 3: Smart weighted keyword matching
        # Uses same logic as link_emails_by_subject_keywords:
        # - City names, client names = 3 points
        # - Project words = 2 points
        # - Countries (if many projects) = 0.5 points
        import re

        keyword_index = self._build_smart_keyword_index(cursor)

        body = (email.get('body_full', '') or '')[:300].lower()
        text_to_match = f"{subject.lower()} {body}"

        # Find matching keywords with weighted scoring
        scores = {}
        match_reasons = {}

        for keyword, proposals_list in keyword_index.items():
            if re.search(rf'\b{re.escape(keyword)}\b', text_to_match):
                for p in proposals_list:
                    pid = p['proposal_id']
                    weight = p['weight']
                    if pid not in scores:
                        scores[pid] = 0
                        match_reasons[pid] = []
                    scores[pid] += weight
                    match_reasons[pid].append((keyword, weight))

        # Require score >= 3 (one city name, or country + project word)
        if scores:
            best_pid = max(scores, key=scores.get)
            best_score = scores[best_pid]

            if best_score >= 3:
                # Get project details
                cursor.execute("""
                    SELECT project_code, project_name FROM proposals WHERE proposal_id = ?
                """, (best_pid,))
                project = cursor.fetchone()

                if project:
                    conn.close()
                    confidence = min(0.5 + (best_score * 0.1), 0.90)
                    keywords = [f"{kw}" for kw, w in match_reasons[best_pid][:3]]

                    return {
                        'clean_body': '',
                        'category': 'contract',
                        'subcategory': 'smart_keyword_match',
                        'is_bds_work': True,
                        'linked_project_code': project['project_code'],
                        'key_points': [f"Score {best_score:.1f}: {', '.join(keywords)}"],
                        'entities': {'projects': [project['project_name']]},
                        'sentiment': 'neutral',
                        'importance_score': 0.7,
                        'ai_summary': f"Email about {project['project_name']} (matched: {', '.join(keywords[:2])})",
                        'urgency_level': 'medium',
                        'action_required': False,
                        'suggestions': {},
                        '_tier': 2,
                        '_confidence': confidence,
                        '_match_reason': f"score {best_score:.1f}: {', '.join(keywords)}"
                    }

        conn.close()
        return None  # Not confident, proceed to Tier 3

    def categorize_email_tiered(self, email: Dict) -> Dict:
        """
        Main tiered categorization entry point.
        Tries tiers in order, falls back to AI only if needed.
        """
        # Tier 1: Pattern matching (instant, free)
        result = self._tier1_pattern_categorization(email)
        if result:
            print(f"  ⚡ Tier 1: {result['category']}/{result['subcategory']} (conf: {result['_confidence']})")
            return result

        # Tier 2: Database matching (fast, free)
        result = self._tier2_database_matching(email)
        if result:
            print(f"  🔍 Tier 2: {result['category']}/{result['subcategory']} → {result['linked_project_code']} (conf: {result['_confidence']})")
            return result

        # Tier 3: Full AI analysis (expensive, last resort)
        print(f"  🤖 Tier 3: Using AI for full analysis...")
        return None  # Signal to use AI

    def analyze_email_with_context(self, email: Dict) -> Dict:
        """Analyze email WITH full business context"""

        body = email.get('body_full', '')[:3000]
        subject = email.get('subject', '')
        sender = email.get('sender_email', '')

        prompt = f"""{self.business_context}

=== EMAIL TO ANALYZE ===
From: {sender}
Subject: {subject}
Body:
{body}

=== ANALYSIS REQUIRED ===

Analyze this email using the business context above. Return JSON:

{{
    "clean_body": "Email body with signatures removed",
    "category": "contract|design|financial|meeting|rfi|administrative|internal|other",
    "subcategory": "Specific type (fee_discussion, nda_request, schedule_update, shinta_mani_ops, personal, etc.)",
    "is_bds_work": true/false,  // Is this Bensley Design Studio business?
    "linked_project_code": "Project code if identifiable (e.g., '24 BK-015'), or null",
    "key_points": ["bullet 1", "bullet 2"],
    "entities": {{
        "amounts": ["$X"],
        "dates": ["Dec 15"],
        "people": ["Name"],
        "companies": ["Company"],
        "projects": ["Project reference"]
    }},
    "sentiment": "positive|neutral|concerned|urgent",
    "importance_score": 0.0-1.0,
    "ai_summary": "One sentence summary",
    "urgency_level": "low|medium|high|critical",
    "action_required": true/false,

    "suggestions": {{
        "new_contact": {{
            "name": "If new contact discovered",
            "email": "their@email.com",
            "company": "Company name",
            "related_project": "Project code if known"
        }},
        "project_alias": {{
            "alias": "Nickname used in email",
            "project_code": "Actual project code it refers to"
        }},
        "missing_info": "Any important info we should track that's not in our system"
    }}
}}

LINKING RULES (CRITICAL - YOU MUST MATCH THESE):
- ALWAYS check EVERY proposal and project code above before deciding linked_project_code
- Link if ANY word or partial name matches:
  * "Wangsimni" appears in email? → MUST link to "25 BK-071: Wangsimni Project in Korea"
  * "Reliance" or "Monalisa" in email? → MUST link to "25 BK-044: Reliance Industries"
  * "Haeundae" or "MDM" or "Busan" in email? → MUST link to "25 BK-045: MDM World"
  * "Ritz Carlton" + "Nusa Dua" or "Bali"? → MUST link to "25 BK-033"
  * ANY location name (Seoul, India, Bodrum, Taiwan, etc.) matching a project? → LINK IT
- PARTIAL MATCHES COUNT: "Wangsimni Hotel" matches "Wangsimni Project" - SAME PROJECT
- ALWAYS set linked_project_code when ANY identifying info matches a proposal/project above
- When in doubt, LINK IT - false positives are easily fixed, missed links are not
- For project_alias suggestions: ALWAYS include the project_code if it relates to a known project

BDS WORK RULES:
- is_bds_work = TRUE for ANY email about a client project or proposal (even if just waiting/pending)
- is_bds_work = TRUE if it involves Reliance, MDM, any hotel brand, fee discussions, contracts
- is_bds_work = FALSE ONLY for: Shinta Mani hotel operations, foundation charity, Bill's personal land/properties, internal HR/payroll
- If email is from/about a proposal client (like Reliance, TARC, etc.) → is_bds_work = TRUE

OTHER RULES:
- Be conservative with action_required (only if explicit request to Bensley team)
- If you see a new contact not in our list, suggest adding them

Return ONLY valid JSON."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2000
            )

            result = response.choices[0].message.content.strip()
            self.api_calls += 1
            self.estimated_cost += 0.025  # Slightly higher due to context

            # Parse JSON
            if result.startswith('```'):
                result = result.split('```')[1]
                if result.startswith('json'):
                    result = result[4:]

            analysis = json.loads(result)
            return analysis

        except json.JSONDecodeError as e:
            print(f"  JSON error: {e}")
            print(f"  Raw response: {result[:200]}...")
            return self._default_analysis()
        except Exception as e:
            print(f"  API error: {e}")
            import traceback
            traceback.print_exc()
            return self._default_analysis()

    def _default_analysis(self) -> Dict:
        return {
            "clean_body": "",
            "category": "general",
            "subcategory": "",
            "is_bds_work": True,
            "linked_project_code": None,
            "key_points": [],
            "entities": {},
            "sentiment": "neutral",
            "importance_score": 0.5,
            "ai_summary": "Analysis failed",
            "urgency_level": "low",
            "action_required": False,
            "suggestions": {}
        }

    def store_analysis(self, email_id: int, analysis: Dict) -> bool:
        """Store analysis and queue any suggestions"""
        if not analysis:
            print("  ⚠️ No analysis returned")
            return False

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Store in email_content (now with linked_project_code and is_bds_work)
            cursor.execute("""
                INSERT OR REPLACE INTO email_content (
                    email_id, clean_body, category, subcategory,
                    key_points, entities, sentiment, importance_score,
                    ai_summary, urgency_level, action_required, processing_model,
                    linked_project_code, is_bds_work
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email_id,
                analysis.get('clean_body', ''),
                analysis.get('category', 'general'),
                analysis.get('subcategory', ''),
                json.dumps(analysis.get('key_points', [])),
                json.dumps(analysis.get('entities', {})),
                analysis.get('sentiment', 'neutral'),
                analysis.get('importance_score', 0.5),
                analysis.get('ai_summary', ''),
                analysis.get('urgency_level', 'low'),
                1 if analysis.get('action_required') else 0,
                'gpt-4o-mini-contextual',
                analysis.get('linked_project_code'),
                1 if analysis.get('is_bds_work') else 0
            ))

            # Update email with linked project if found
            if analysis.get('linked_project_code'):
                cursor.execute("""
                    UPDATE emails SET category = ?, stage = ?
                    WHERE email_id = ?
                """, (
                    analysis.get('category'),
                    'proposal' if analysis.get('is_bds_work') else 'other',
                    email_id
                ))

            # Queue suggestions (WITH DEDUP CHECKS)
            suggestions = analysis.get('suggestions') or {}

            # New contact suggestion - with dedup check
            new_contact = suggestions.get('new_contact') or {}
            contact_email = new_contact.get('email', '').strip()
            if contact_email and self._should_create_contact_suggestion(contact_email):
                contact = suggestions['new_contact']
                cursor.execute("""
                    INSERT INTO ai_suggestions_queue
                    (data_table, record_id, field_name, suggested_value, confidence, reasoning)
                    VALUES ('contacts', ?, 'new_contact', ?, 0.8, ?)
                """, (
                    email_id,
                    json.dumps(contact),
                    f"New contact found in email: {contact.get('name')} from {contact.get('company')}"
                ))
                self.suggestions_created += 1
            elif contact_email:
                print(f"  ⏭️ Skipped duplicate contact suggestion: {contact_email}")

            # Project alias suggestion - with dedup check
            project_alias = suggestions.get('project_alias') or {}
            alias_value = project_alias.get('alias', '').strip()
            if alias_value and self._should_create_alias_suggestion(alias_value):
                alias = project_alias
                cursor.execute("""
                    INSERT INTO ai_suggestions_queue
                    (data_table, record_id, field_name, suggested_value, confidence, reasoning)
                    VALUES ('learned_patterns', ?, 'project_alias', ?, 0.75, ?)
                """, (
                    email_id,
                    json.dumps(alias),
                    f"Project alias: '{alias.get('alias')}' may refer to {alias.get('project_code')}"
                ))
                self.suggestions_created += 1
            elif alias_value:
                print(f"  ⏭️ Skipped duplicate alias suggestion: {alias_value}")

            conn.commit()
            conn.close()

            # Generate advanced learning suggestions using AILearningService
            if self.learning_service and analysis.get('is_bds_work'):
                try:
                    learning_suggestions = self._generate_learning_suggestions(email_id, analysis)
                    if learning_suggestions > 0:
                        print(f"  🧠 {learning_suggestions} learning suggestion(s) created")
                except Exception as e:
                    print(f"  ⚠️ Learning service error: {e}")

            return True

        except Exception as e:
            print(f"  DB error: {e}")
            conn.close()
            return False

    def _generate_learning_suggestions(self, email_id: int, analysis: Dict) -> int:
        """Generate advanced suggestions using AILearningService"""
        if not self.learning_service:
            return 0

        suggestions_count = 0

        # Get email details for context
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM emails WHERE email_id = ?", (email_id,))
        email_row = cursor.fetchone()
        conn.close()

        if not email_row:
            return 0

        email = dict(email_row)
        project_code = analysis.get('linked_project_code')

        # 1. Follow-up suggestion if email needs action and no recent outbound
        if analysis.get('action_required') and project_code:
            self.learning_service._save_suggestion({
                'suggestion_type': 'follow_up_needed',
                'priority': 'high' if analysis.get('urgency_level') == 'critical' else 'medium',
                'confidence_score': analysis.get('importance_score', 0.7),
                'source_type': 'email',
                'source_id': email_id,
                'source_reference': f"Email: {email.get('subject', '')[:50]}",
                'title': f"Follow up required for {project_code}",
                'description': analysis.get('ai_summary', ''),
                'suggested_action': 'Review email and respond to client',
                'suggested_data': json.dumps({
                    'email_id': email_id,
                    'subject': email.get('subject'),
                    'sender': email.get('sender_email'),
                    'key_points': analysis.get('key_points', [])
                }),
                'target_table': 'proposals',
                'project_code': project_code,
                'status': 'pending'
            })
            suggestions_count += 1

        # 2. Fee/amount detection
        entities = analysis.get('entities', {})
        amounts = entities.get('amounts', [])
        if amounts and project_code:
            self.learning_service._save_suggestion({
                'suggestion_type': 'fee_change',
                'priority': 'high',
                'confidence_score': 0.75,
                'source_type': 'email',
                'source_id': email_id,
                'source_reference': f"Email: {email.get('subject', '')[:50]}",
                'title': f"Fee amount detected: {', '.join(amounts[:3])}",
                'description': f"Financial amounts mentioned in email regarding {project_code}",
                'suggested_action': 'Verify if fee update needed',
                'suggested_data': json.dumps({
                    'amounts': amounts,
                    'context': analysis.get('ai_summary', '')
                }),
                'target_table': 'contract_fee_breakdowns',
                'project_code': project_code,
                'status': 'pending'
            })
            suggestions_count += 1

        # 3. New contact from entities
        people = entities.get('people', [])
        companies = entities.get('companies', [])
        if people and project_code:
            for person in people[:2]:  # Limit to 2 per email
                # Check if it's not a known contact
                if not self._is_known_contact(person):
                    self.learning_service._save_suggestion({
                        'suggestion_type': 'new_contact',
                        'priority': 'medium',
                        'confidence_score': 0.7,
                        'source_type': 'email',
                        'source_id': email_id,
                        'source_reference': f"Email from {email.get('sender_email', '')}",
                        'title': f"New contact: {person}",
                        'description': f"Person mentioned in email about {project_code}",
                        'suggested_action': 'Add to contacts database',
                        'suggested_data': json.dumps({
                            'name': person,
                            'company': companies[0] if companies else None,
                            'related_project': project_code
                        }),
                        'target_table': 'contacts',
                        'project_code': project_code,
                        'status': 'pending'
                    })
                    suggestions_count += 1

        # 4. Deadline detection
        dates = entities.get('dates', [])
        if dates and project_code and analysis.get('urgency_level') in ['high', 'critical']:
            self.learning_service._save_suggestion({
                'suggestion_type': 'deadline_detected',
                'priority': 'high',
                'confidence_score': 0.8,
                'source_type': 'email',
                'source_id': email_id,
                'source_reference': f"Email: {email.get('subject', '')[:50]}",
                'title': f"Deadline mentioned: {', '.join(dates[:3])}",
                'description': f"Important date(s) mentioned for {project_code}",
                'suggested_action': 'Add to project milestones',
                'suggested_data': json.dumps({
                    'dates': dates,
                    'context': analysis.get('ai_summary', '')
                }),
                'target_table': 'project_milestones',
                'project_code': project_code,
                'status': 'pending'
            })
            suggestions_count += 1

        return suggestions_count

    def _is_known_contact(self, name: str) -> bool:
        """Check if a name is already in our contacts"""
        name_lower = name.lower()
        for contact in self.contacts:
            if contact.get('name', '').lower() in name_lower or name_lower in contact.get('name', '').lower():
                return True
        return False

    def _should_create_contact_suggestion(self, email: str) -> bool:
        """
        Check if we should create a contact suggestion - dedup check.
        Returns False if:
        1. Contact already exists in contacts table
        2. Already pending in suggestions queue
        3. Was previously rejected
        """
        if not email:
            return False

        email_lower = email.lower().strip()
        conn = self.get_connection()
        cursor = conn.cursor()

        # CHECK 1: Already in contacts table?
        cursor.execute("SELECT 1 FROM contacts WHERE LOWER(email) = ?", (email_lower,))
        if cursor.fetchone():
            conn.close()
            return False  # Already exists

        # CHECK 2: Already pending in suggestions?
        cursor.execute("""
            SELECT 1 FROM ai_suggestions_queue
            WHERE field_name = 'new_contact'
            AND LOWER(json_extract(suggested_value, '$.email')) = ?
            AND status = 'pending'
        """, (email_lower,))
        if cursor.fetchone():
            conn.close()
            return False  # Already suggested

        # CHECK 3: Previously rejected?
        cursor.execute("""
            SELECT 1 FROM ai_suggestions_queue
            WHERE field_name = 'new_contact'
            AND LOWER(json_extract(suggested_value, '$.email')) = ?
            AND status = 'rejected'
        """, (email_lower,))
        if cursor.fetchone():
            conn.close()
            return False  # Was rejected, don't suggest again

        conn.close()
        return True

    # ==========================================================================
    # EMAIL LINKING STRATEGIES - Run these to link unlinked emails
    # ==========================================================================

    def link_emails_by_sender(self) -> int:
        """
        Strategy 1: Link unlinked emails by matching sender to known contacts/proposals.
        Two approaches:
        A) Sender email matches proposal's contact_email directly
        B) Sender email matches a contact in contacts table linked to proposals
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Approach A: Direct match - sender email matches proposal's contact_email
        cursor.execute("""
            SELECT DISTINCT e.email_id, e.sender_email,
                   p.project_code, p.proposal_id, p.project_name
            FROM emails e
            JOIN proposals p ON LOWER(TRIM(e.sender_email)) = LOWER(TRIM(p.contact_email))
            WHERE e.email_id NOT IN (SELECT email_id FROM email_project_links)
              AND e.email_id NOT IN (SELECT email_id FROM email_proposal_links)
              AND p.contact_email IS NOT NULL
              AND p.proposal_id IS NOT NULL
        """)

        links_created = 0
        for row in cursor.fetchall():
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO email_proposal_links
                    (email_id, proposal_id, confidence_score, match_reasons, auto_linked, created_at)
                    VALUES (?, ?, 0.95, ?, 1, datetime('now'))
                """, (
                    row['email_id'],
                    row['proposal_id'],
                    f"Sender {row['sender_email']} is contact for {row['project_code']}"
                ))
                if cursor.rowcount > 0:
                    links_created += 1
            except Exception as e:
                print(f"  Error linking email {row['email_id']}: {e}")

        # NOTE: Removed domain-based company matching (Strategy A part B)
        # Reason: Hotel operators (Marriott, Four Seasons) work on MANY different projects
        # One company domain ≠ one project. Only direct contact_email match is reliable.

        conn.commit()
        conn.close()
        print(f"✅ Sender-based linking: {links_created} emails linked (direct contact matches only)")
        return links_created

    def _build_smart_keyword_index(self, cursor) -> dict:
        """
        Build a weighted keyword index for smart project matching.

        Keywords are categorized by uniqueness:
        - TIER_A (weight 3): Very unique - city names, brand names, client names
        - TIER_B (weight 2): Somewhat unique - distinctive descriptors
        - TIER_C (weight 1): Less unique - countries with multiple projects

        Returns: {keyword: [(proposal_id, project_code, weight), ...]}
        """
        import re

        cursor.execute("""
            SELECT proposal_id, project_code, project_name, location, country, client_company
            FROM proposals
            WHERE project_name IS NOT NULL OR location IS NOT NULL
        """)
        proposals = [dict(row) for row in cursor.fetchall()]

        # Count how many projects use each country (for weighting)
        cursor.execute("""
            SELECT LOWER(country) as country, COUNT(*) as cnt
            FROM proposals
            WHERE country IS NOT NULL
            GROUP BY LOWER(country)
        """)
        country_counts = {row['country']: row['cnt'] for row in cursor.fetchall()}

        # Generic words to ignore completely
        generic_words = {
            'project', 'phase', 'hotel', 'resort', 'villa', 'design', 'development',
            'luxury', 'beach', 'new', 'the', 'and', 'for', 'with', 'private',
            'residential', 'group', 'additional', 'services', 'star', 'high',
            'end', 'club', 'area', 'zone', 'keys', 'extension', 'center'
        }

        # Build weighted index
        keyword_index = {}

        for p in proposals:
            # TIER A: City/specific location names (weight 3)
            if p['location']:
                for word in re.split(r'[,\s\-/()\d]+', p['location']):
                    word = word.strip().lower()
                    if len(word) >= 3 and word not in generic_words:
                        # Skip if it's just the country name
                        if p['country'] and word == p['country'].lower():
                            continue
                        self._add_to_index(keyword_index, word, p, weight=3)

            # TIER A: Client/developer company names (weight 3)
            if p['client_company']:
                for word in re.split(r'[,\s\-/()\d]+', p['client_company']):
                    word = word.strip().lower()
                    if len(word) >= 3 and word not in generic_words:
                        self._add_to_index(keyword_index, word, p, weight=3)

            # TIER B: Distinctive words from project name (weight 2)
            if p['project_name']:
                # Look for brand names, unique descriptors
                brand_words = {'cheval', 'blanc', 'hyatt', 'ritz', 'carlton', 'millennium',
                              'sukhothai', 'santani', 'solaire', 'botanica', 'oasis'}
                for word in re.split(r'[,\s\-/()\d]+', p['project_name']):
                    word = word.strip().lower()
                    if len(word) >= 3 and word not in generic_words:
                        weight = 3 if word in brand_words else 2
                        self._add_to_index(keyword_index, word, p, weight=weight)

            # TIER C: Country names - lower weight if many projects there (weight 1)
            if p['country']:
                country = p['country'].strip().lower()
                if len(country) >= 3:
                    count = country_counts.get(country, 1)
                    # If 3+ projects in country, weight is only 0.5
                    weight = 0.5 if count >= 3 else 1
                    self._add_to_index(keyword_index, country, p, weight=weight)

        return keyword_index

    def _add_to_index(self, index: dict, keyword: str, proposal: dict, weight: float):
        """Helper to add keyword to index with weight"""
        if keyword not in index:
            index[keyword] = []
        index[keyword].append({
            'proposal_id': proposal['proposal_id'],
            'project_code': proposal['project_code'],
            'project_name': proposal['project_name'],
            'weight': weight
        })

    def link_emails_by_subject_keywords(self) -> int:
        """
        Strategy 2: Smart fuzzy match using weighted keyword index.

        Matching strategy:
        - City names, brand names, client names = 3 points each
        - Distinctive project words = 2 points each
        - Country names (if few projects there) = 1 point
        - Country names (if many projects there) = 0.5 points

        Requires score >= 3 to link (e.g., one city name, or country + project word)
        """
        import re

        conn = self.get_connection()
        cursor = conn.cursor()

        # Build the smart weighted keyword index
        keyword_index = self._build_smart_keyword_index(cursor)
        print(f"  Built weighted keyword index with {len(keyword_index)} terms")

        # Get unlinked emails
        cursor.execute("""
            SELECT email_id, subject, body_full FROM emails
            WHERE email_id NOT IN (SELECT email_id FROM email_project_links)
              AND email_id NOT IN (SELECT email_id FROM email_proposal_links)
              AND (subject IS NOT NULL OR body_full IS NOT NULL)
        """)

        links_created = 0
        for row in cursor.fetchall():
            # Combine subject and first part of body for matching
            text = f"{row['subject'] or ''} {(row['body_full'] or '')[:500]}".lower()

            # Find matching keywords with weighted scoring
            scores = {}  # proposal_id -> weighted score
            match_reasons = {}  # proposal_id -> [(keyword, weight), ...]

            for keyword, proposals_list in keyword_index.items():
                # Use word boundary matching to avoid partial matches
                if re.search(rf'\b{re.escape(keyword)}\b', text):
                    for p in proposals_list:
                        pid = p['proposal_id']
                        weight = p['weight']
                        if pid not in scores:
                            scores[pid] = 0
                            match_reasons[pid] = []
                        scores[pid] += weight
                        match_reasons[pid].append((keyword, weight))

            # Link to the proposal with the highest score (if score >= 3)
            # Score 3 = one city name, or country + distinctive word, or 1.5 city names
            if scores:
                best_pid = max(scores, key=scores.get)
                best_score = scores[best_pid]

                if best_score >= 3:  # Require score of at least 3
                    # Confidence based on score
                    confidence = min(0.5 + (best_score * 0.1), 0.95)
                    keywords_matched = [f"{kw}({w})" for kw, w in match_reasons[best_pid][:3]]

                    try:
                        cursor.execute("""
                            INSERT OR IGNORE INTO email_proposal_links
                            (email_id, proposal_id, confidence_score, match_reasons, auto_linked, created_at)
                            VALUES (?, ?, ?, ?, 1, datetime('now'))
                        """, (
                            row['email_id'],
                            best_pid,
                            confidence,
                            f"Score {best_score:.1f}: {', '.join(keywords_matched)}"
                        ))
                        if cursor.rowcount > 0:
                            links_created += 1
                    except Exception as e:
                        pass

        conn.commit()
        conn.close()
        print(f"✅ Smart keyword linking: {links_created} emails linked (score >= 3 required)")
        return links_created

    def link_emails_by_thread(self) -> int:
        """
        Strategy 3: If any email in a thread is linked, link all others in that thread.
        Uses thread_id field (derived from Gmail/IMAP threading).

        NOTE: Skip threads where ALL participants are @bensley.com (internal scheduling).
        These shouldn't auto-link to projects just because one email mentioned a project.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Find unlinked emails that share a thread_id with linked emails
        # BUT exclude threads where ALL emails are from/to @bensley.com only
        cursor.execute("""
            SELECT DISTINCT
                e.email_id,
                epl.proposal_id,
                e.thread_id,
                e.sender_email,
                e.recipient_emails
            FROM emails e
            JOIN emails linked_e ON e.thread_id = linked_e.thread_id
            JOIN email_proposal_links epl ON linked_e.email_id = epl.email_id
            WHERE e.email_id NOT IN (SELECT email_id FROM email_proposal_links)
              AND e.thread_id IS NOT NULL
              AND e.thread_id != ''
        """)

        links_created = 0
        skipped_internal = 0

        for row in cursor.fetchall():
            # Check if this is an internal-only thread (all bensley.com)
            sender = (row['sender_email'] or '').lower()
            recipients = (row['recipient_emails'] or '').lower()
            all_addresses = f"{sender} {recipients}"

            # Skip if ALL addresses are @bensley.com
            # (internal scheduling threads shouldn't auto-link)
            non_bensley = [addr for addr in all_addresses.split()
                          if '@' in addr and 'bensley.com' not in addr and 'bensley.co.id' not in addr]

            if not non_bensley:
                # All participants are Bensley internal - skip
                skipped_internal += 1
                continue

            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO email_proposal_links
                    (email_id, proposal_id, confidence_score, match_reasons, auto_linked, created_at)
                    VALUES (?, ?, 0.90, ?, 1, datetime('now'))
                """, (row['email_id'], row['proposal_id'], f"Same thread as linked email"))
                if cursor.rowcount > 0:
                    links_created += 1
            except Exception as e:
                print(f"  Error: {e}")

        conn.commit()
        conn.close()
        print(f"✅ Thread-based linking: {links_created} emails linked (skipped {skipped_internal} internal-only threads)")
        return links_created

    def link_emails_by_recurring_sender(self) -> int:
        """
        Strategy 4: If a sender has multiple emails already linked to a project,
        link their unlinked emails to the same project.

        Logic: If sender@example.com has 5 emails linked to "25 BK-045",
        and 3 unlinked emails, link those 3 to the same project.

        Requires at least 3 existing links to the same project to avoid false positives.
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Find senders with multiple emails linked to the same project
        cursor.execute("""
            SELECT
                e.sender_email,
                epl.proposal_id,
                p.project_code,
                COUNT(*) as link_count
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            JOIN proposals p ON epl.proposal_id = p.proposal_id
            WHERE e.sender_email IS NOT NULL
              AND e.sender_email NOT LIKE '%bensley.com%'
              AND e.sender_email NOT LIKE '%bensley.co.id%'
            GROUP BY e.sender_email, epl.proposal_id
            HAVING link_count >= 3
        """)

        sender_project_map = {}
        for row in cursor.fetchall():
            sender = row['sender_email'].lower().strip()
            if sender not in sender_project_map:
                sender_project_map[sender] = []
            sender_project_map[sender].append({
                'proposal_id': row['proposal_id'],
                'project_code': row['project_code'],
                'count': row['link_count']
            })

        print(f"  Found {len(sender_project_map)} senders with 3+ emails to same project")

        # For each sender, link their unlinked emails to their most common project
        links_created = 0

        for sender, projects in sender_project_map.items():
            # Get the project this sender emails most about
            best_project = max(projects, key=lambda x: x['count'])

            # Find unlinked emails from this sender
            cursor.execute("""
                SELECT email_id FROM emails
                WHERE LOWER(TRIM(sender_email)) = ?
                  AND email_id NOT IN (SELECT email_id FROM email_proposal_links)
                  AND email_id NOT IN (SELECT email_id FROM email_project_links)
            """, (sender,))

            unlinked = cursor.fetchall()

            for row in unlinked:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO email_proposal_links
                        (email_id, proposal_id, confidence_score, match_reasons, auto_linked, created_at)
                        VALUES (?, ?, 0.85, ?, 1, datetime('now'))
                    """, (
                        row['email_id'],
                        best_project['proposal_id'],
                        f"Recurring sender: {best_project['count']} emails to {best_project['project_code']}"
                    ))
                    if cursor.rowcount > 0:
                        links_created += 1
                except Exception as e:
                    pass

        conn.commit()
        conn.close()
        print(f"✅ Recurring sender linking: {links_created} emails linked")
        return links_created

    def run_all_linking_strategies(self) -> dict:
        """Run all linking strategies and return stats."""
        print("\n🔗 RUNNING EMAIL LINKING STRATEGIES")
        print("=" * 60)

        # Get baseline
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total,
                   (SELECT COUNT(DISTINCT email_id) FROM email_proposal_links) as linked_proposals,
                   (SELECT COUNT(DISTINCT email_id) FROM email_project_links) as linked_projects
            FROM emails
        """)
        before = dict(cursor.fetchone())
        conn.close()

        print(f"Before: {before['total']} emails, {before['linked_proposals']} linked to proposals, {before['linked_projects']} linked to projects")

        # Run strategies in order of precision (most precise first)
        sender_links = self.link_emails_by_sender()           # Strategy 1: Direct contact match
        keyword_links = self.link_emails_by_subject_keywords() # Strategy 2: Smart keyword matching
        thread_links = self.link_emails_by_thread()            # Strategy 3: Thread-based (skip internal)
        recurring_links = self.link_emails_by_recurring_sender() # Strategy 4: Recurring sender patterns

        # Get new stats
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total,
                   (SELECT COUNT(DISTINCT email_id) FROM email_proposal_links) as linked_proposals,
                   (SELECT COUNT(DISTINCT email_id) FROM email_project_links) as linked_projects
            FROM emails
        """)
        after = dict(cursor.fetchone())
        conn.close()

        total_new = sender_links + keyword_links + thread_links + recurring_links
        print(f"\nAfter: {after['total']} emails, {after['linked_proposals']} linked to proposals, {after['linked_projects']} linked to projects")
        print(f"Total new links: {total_new}")

        return {
            'sender_links': sender_links,
            'keyword_links': keyword_links,
            'thread_links': thread_links,
            'recurring_links': recurring_links,
            'total_new': total_new,
            'before': before,
            'after': after
        }

    def _should_create_alias_suggestion(self, alias: str) -> bool:
        """
        Check if we should create an alias suggestion - dedup check.
        Returns False if:
        1. Alias already exists in learned_patterns
        2. Already pending in suggestions queue
        3. Was previously rejected
        """
        if not alias:
            return False

        alias_lower = alias.lower().strip()
        conn = self.get_connection()
        cursor = conn.cursor()

        # CHECK 1: Already in learned_patterns?
        cursor.execute("""
            SELECT 1 FROM learned_patterns
            WHERE pattern_type = 'project_alias'
            AND LOWER(condition) LIKE ?
        """, (f'%{alias_lower}%',))
        if cursor.fetchone():
            conn.close()
            return False  # Already learned

        # CHECK 2: Already pending?
        cursor.execute("""
            SELECT 1 FROM ai_suggestions_queue
            WHERE field_name = 'project_alias'
            AND LOWER(json_extract(suggested_value, '$.alias')) = ?
            AND status = 'pending'
        """, (alias_lower,))
        if cursor.fetchone():
            conn.close()
            return False  # Already suggested

        # CHECK 3: Previously rejected?
        cursor.execute("""
            SELECT 1 FROM ai_suggestions_queue
            WHERE field_name = 'project_alias'
            AND LOWER(json_extract(suggested_value, '$.alias')) = ?
            AND status = 'rejected'
        """, (alias_lower,))
        if cursor.fetchone():
            conn.close()
            return False  # Was rejected

        conn.close()
        return True

    def get_emails_to_process(self, limit: int = 100, reprocess: bool = False) -> List[Dict]:
        """Get emails needing processing"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if reprocess:
            # Reprocess all emails with body content
            cursor.execute("""
                SELECT email_id, subject, sender_email, body_full, date
                FROM emails
                WHERE body_full IS NOT NULL AND LENGTH(body_full) > 50
                ORDER BY date DESC
                LIMIT ?
            """, (limit,))
        else:
            # Only unprocessed
            cursor.execute("""
                SELECT e.email_id, e.subject, e.sender_email, e.body_full, e.date
                FROM emails e
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
                WHERE ec.content_id IS NULL
                  AND e.body_full IS NOT NULL
                  AND LENGTH(e.body_full) > 50
                ORDER BY e.date DESC
                LIMIT ?
            """, (limit,))

        emails = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return emails

    def process_batch(self, emails: List[Dict]) -> Dict:
        """Process a batch of emails with context - using tiered categorization"""
        stats = {
            'processed': 0,
            'bds_work': 0,
            'other': 0,
            'suggestions': 0,
            'errors': 0,
            'tier1': 0,  # Categorized by pattern matching
            'tier2': 0,  # Categorized by database lookup
            'tier3': 0   # Required full AI analysis
        }

        for i, email in enumerate(emails, 1):
            print(f"\n[{i}/{len(emails)}] {email['email_id']}: {email['subject'][:50]}...")

            # Try tiered categorization first (saves API costs)
            analysis = self.categorize_email_tiered(email)

            if analysis:
                # Tiered categorization succeeded
                tier = analysis.get('_tier', 0)
                if tier == 1:
                    stats['tier1'] += 1
                elif tier == 2:
                    stats['tier2'] += 1
            else:
                # Fall back to full AI analysis (Tier 3)
                analysis = self.analyze_email_with_context(email)
                stats['tier3'] += 1

            if self.store_analysis(email['email_id'], analysis):
                stats['processed'] += 1

                if analysis.get('is_bds_work'):
                    stats['bds_work'] += 1
                else:
                    stats['other'] += 1

                project = analysis.get('linked_project_code') or 'None'
                print(f"  → {analysis.get('category')}/{analysis.get('subcategory')} | BDS: {analysis.get('is_bds_work')} | Project: {project}")
                print(f"  → {analysis.get('ai_summary', '')[:70]}...")

                if analysis.get('suggestions', {}).get('new_contact'):
                    print(f"  💡 Suggestion: New contact - {analysis['suggestions']['new_contact'].get('name')}")
                    stats['suggestions'] += 1
                if analysis.get('suggestions', {}).get('project_alias'):
                    print(f"  💡 Suggestion: Alias '{analysis['suggestions']['project_alias'].get('alias')}'")
                    stats['suggestions'] += 1
            else:
                stats['errors'] += 1

            time.sleep(0.5)

        return stats

    def show_pending_suggestions(self):
        """Show suggestions awaiting approval"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT suggestion_id, data_table, field_name, suggested_value, reasoning, created_at
            FROM ai_suggestions_queue
            WHERE status = 'pending'
            ORDER BY created_at DESC
            LIMIT 50
        """)

        suggestions = cursor.fetchall()
        conn.close()

        if not suggestions:
            print("\nNo pending suggestions!")
            return

        print(f"\n📋 PENDING SUGGESTIONS ({len(suggestions)}):")
        print("=" * 80)

        for s in suggestions:
            print(f"\n[{s['suggestion_id']}] {s['field_name']} → {s['data_table']}")
            print(f"    Value: {s['suggested_value'][:100]}...")
            print(f"    Reason: {s['reasoning']}")
            print(f"    Created: {s['created_at']}")

        print("\nTo approve: python3 smart_email_brain.py --approve 123")
        print("To reject:  python3 smart_email_brain.py --reject 123")

    def approve_suggestion(self, suggestion_id: int):
        """Approve and apply a suggestion"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM ai_suggestions_queue WHERE suggestion_id = ?
        """, (suggestion_id,))

        suggestion = cursor.fetchone()
        if not suggestion:
            print(f"Suggestion {suggestion_id} not found")
            return

        suggestion = dict(suggestion)
        value = json.loads(suggestion['suggested_value'])

        if suggestion['field_name'] == 'new_contact':
            # Add to contacts (notes field stores company info)
            cursor.execute("""
                INSERT OR IGNORE INTO contacts (name, email, notes)
                VALUES (?, ?, ?)
            """, (value.get('name'), value.get('email'), f"Company: {value.get('company')}"))
            print(f"✅ Added contact: {value.get('name')} ({value.get('email')})")

        elif suggestion['field_name'] == 'project_alias':
            # Add to learned_patterns
            cursor.execute("""
                INSERT OR REPLACE INTO learned_patterns
                (pattern_type, pattern_key, pattern_value, confidence, occurrences)
                VALUES ('project_alias', ?, ?, 0.9, 1)
            """, (value.get('alias'), value.get('project_code')))
            print(f"✅ Learned alias: '{value.get('alias')}' → {value.get('project_code')}")

        # Mark as applied
        cursor.execute("""
            UPDATE ai_suggestions_queue
            SET status = 'applied', applied_at = datetime('now')
            WHERE suggestion_id = ?
        """, (suggestion_id,))

        conn.commit()
        conn.close()

    def reject_suggestion(self, suggestion_id: int):
        """Reject a suggestion"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE ai_suggestions_queue
            SET status = 'rejected', reviewed_at = datetime('now')
            WHERE suggestion_id = ?
        """, (suggestion_id,))

        conn.commit()
        conn.close()
        print(f"❌ Rejected suggestion {suggestion_id}")


def main():
    parser = argparse.ArgumentParser(description='Smart Email Brain - Context-Aware Processing')
    parser.add_argument('--batch-size', type=int, default=100)
    parser.add_argument('--reprocess', action='store_true', help='Reprocess emails even if already done')
    parser.add_argument('--show-suggestions', action='store_true')
    parser.add_argument('--approve', type=int, help='Approve suggestion by ID')
    parser.add_argument('--reject', type=int, help='Reject suggestion by ID')
    parser.add_argument('--link-emails', action='store_true', help='Run all email linking strategies')
    parser.add_argument('--yes', '-y', action='store_true')
    args = parser.parse_args()

    print("=" * 80)
    print("SMART EMAIL BRAIN - Context-Aware Processing with Learning")
    print("=" * 80)

    brain = SmartEmailBrain()

    if args.show_suggestions:
        brain.show_pending_suggestions()
        return

    if args.approve:
        brain.load_context()
        brain.approve_suggestion(args.approve)
        return

    if args.reject:
        brain.reject_suggestion(args.reject)
        return

    if args.link_emails:
        brain.run_all_linking_strategies()
        return

    # Load context
    print("\n📚 Loading business context...")
    brain.load_context()

    # Get emails
    emails = brain.get_emails_to_process(args.batch_size, args.reprocess)
    print(f"\n📧 Found {len(emails)} emails to process")

    if not emails:
        print("Nothing to process!")
        return

    est_cost = len(emails) * 0.025
    print(f"💰 Estimated cost: ${est_cost:.2f}")

    if not args.yes:
        confirm = input("\nProceed? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Cancelled")
            return

    # Process
    print("\n🚀 Processing with full context...")
    start = time.time()
    stats = brain.process_batch(emails)
    elapsed = time.time() - start

    print("\n" + "=" * 80)
    print("✅ COMPLETE")
    print("=" * 80)
    print(f"Processed: {stats['processed']}")
    print(f"BDS Work: {stats['bds_work']} | Other: {stats['other']}")
    print(f"Suggestions created: {stats['suggestions']}")
    print(f"Errors: {stats['errors']}")

    # Tiered categorization stats
    tier1 = stats.get('tier1', 0)
    tier2 = stats.get('tier2', 0)
    tier3 = stats.get('tier3', 0)
    total = tier1 + tier2 + tier3
    if total > 0:
        print(f"\n📊 Categorization Tiers:")
        print(f"  ⚡ Tier 1 (patterns): {tier1} ({tier1*100/total:.0f}%) - FREE")
        print(f"  🔍 Tier 2 (database): {tier2} ({tier2*100/total:.0f}%) - FREE")
        print(f"  🤖 Tier 3 (AI):       {tier3} ({tier3*100/total:.0f}%) - ${tier3 * 0.025:.2f}")
        print(f"  💰 AI Cost Saved: ${(tier1 + tier2) * 0.025:.2f}")

    print(f"\nTime: {elapsed/60:.1f} min | Actual Cost: ${brain.estimated_cost:.2f}")

    if brain.suggestions_created > 0:
        print(f"\n💡 {brain.suggestions_created} suggestions await your review!")
        print("   Run: python3 smart_email_brain.py --show-suggestions")


if __name__ == '__main__':
    main()
