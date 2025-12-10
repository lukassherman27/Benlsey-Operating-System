"""
Context Bundler Service

Builds a rich context bundle for GPT-powered suggestion analysis.
Loads business context from markdown files, queries active work from database,
and includes learned patterns for intelligent email analysis.

Part of Phase 2.0: Context-Aware AI Suggestions
"""

import os
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .base_service import BaseService

logger = logging.getLogger(__name__)


class ContextBundler(BaseService):
    """
    Builds and caches context bundles for GPT analysis.

    The context bundle includes:
    - Business context from docs/context/business.md
    - Active proposals (code, name, client, status)
    - Active projects
    - Learned email patterns
    - Contact-project mappings
    - Multi-project contacts (to skip for linking)
    """

    # Cache settings
    CACHE_TTL_SECONDS = 300  # 5 minutes

    def __init__(self, db_path: str = None):
        super().__init__(db_path)
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_time: Optional[float] = None

        # Path to business context file
        self.business_md_path = self._find_business_md()

    def _find_business_md(self) -> Path:
        """Find the business.md file relative to project root"""
        # Try common locations
        possible_paths = [
            Path("docs/context/business.md"),
            Path("../docs/context/business.md"),
            Path(__file__).parent.parent.parent / "docs/context/business.md",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        # Fallback to environment variable
        env_path = os.getenv("BUSINESS_CONTEXT_PATH")
        if env_path:
            return Path(env_path)

        logger.warning("business.md not found, will use minimal context")
        return None

    def get_bundle(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get the context bundle, using cache if available.

        Args:
            force_refresh: If True, bypass cache and rebuild

        Returns:
            Dict containing all context sections
        """
        # Check cache validity
        if not force_refresh and self._is_cache_valid():
            logger.debug("Using cached context bundle")
            return self._cache

        # Build fresh bundle
        logger.info("Building fresh context bundle")
        start_time = time.time()

        bundle = {
            "built_at": datetime.now().isoformat(),
            "business_context": self._load_business_context(),
            "active_proposals": self._load_active_proposals(),
            "active_projects": self._load_active_projects(),
            "learned_patterns": self._load_learned_patterns(),
            "contact_mappings": self._load_contact_mappings(),
            "multi_project_contacts": self._load_multi_project_contacts(),
            "known_staff": self._load_known_staff(),
        }

        # Calculate token estimate for monitoring
        bundle["estimated_tokens"] = self._estimate_tokens(bundle)

        # Update cache
        self._cache = bundle
        self._cache_time = time.time()

        elapsed = time.time() - start_time

        # Detailed logging for debugging
        logger.info(
            f"Context bundle built in {elapsed:.2f}s | "
            f"Proposals: {len(bundle.get('active_proposals', []))} | "
            f"Projects: {len(bundle.get('active_projects', []))} | "
            f"Patterns: {len(bundle.get('learned_patterns', []))} | "
            f"Contact mappings: {len(bundle.get('contact_mappings', []))} | "
            f"Multi-project contacts: {len(bundle.get('multi_project_contacts', []))} | "
            f"Tokens: ~{bundle['estimated_tokens']}"
        )

        return bundle

    def _is_cache_valid(self) -> bool:
        """Check if cached bundle is still valid"""
        if self._cache is None or self._cache_time is None:
            return False

        age = time.time() - self._cache_time
        return age < self.CACHE_TTL_SECONDS

    def _load_business_context(self) -> str:
        """
        Load and summarize business.md for GPT context.

        We extract key sections that help GPT understand:
        - What Bensley does
        - Proposal vs Project distinction
        - Multi-context nature (BDS vs Shinta Mani ownership)
        """
        if not self.business_md_path or not self.business_md_path.exists():
            return self._get_minimal_business_context()

        try:
            content = self.business_md_path.read_text()

            # Extract key sections (keep it under ~500 tokens)
            summary = self._extract_key_sections(content)
            return summary

        except Exception as e:
            logger.error(f"Failed to load business.md: {e}")
            return self._get_minimal_business_context()

    def _extract_key_sections(self, content: str) -> str:
        """Extract the most relevant sections from business.md"""
        # Keep it focused for GPT context
        summary = """## Bensley Design Studios Context

**Who We Are:** World-renowned luxury hospitality design firm led by Bill Bensley.
Specializes in 5-star resorts, hotels, and private estates across Asia-Pacific.

**Design Disciplines:** Landscape Architecture, Architecture, Interior Design, Art Direction, Brand Experience.

**Key Clients:** Four Seasons, Rosewood, Capella, Shinta Mani (Bensley-owned).

**CRITICAL DISTINCTION - Proposals vs Projects:**
- PROPOSALS = Pre-contract, sales pipeline. Bill's #1 priority.
- PROJECTS = Won contracts, active delivery, billing.
Project codes follow format: "XX BK-XXX" (e.g., "24 BK-089")

**Multi-Context System:**
Bill receives emails about multiple business contexts:
- Bensley Design Studios (core business) → Track in proposals/projects
- Shinta Mani Hotels (investor/owner) → Track in emails only, NOT projects
- Shinta Mani Foundation (charity) → Track in emails only
- Personal matters (land sales, etc.) → Track in emails only

When analyzing emails, distinguish between:
- "Shinta Mani as client" (Bensley designing for SM) → Link to project
- "Shinta Mani as investment" (Bill receiving owner updates) → Do NOT link to project

**Project Phases:** CD (Concept) → SD (Schematic) → DD (Development) → CD (Construction Docs) → CA (Administration)
"""
        return summary

    def _get_minimal_business_context(self) -> str:
        """Fallback minimal context if business.md unavailable"""
        return """## Bensley Design Studios
Luxury hospitality design firm. Project codes: "XX BK-XXX".
PROPOSALS = sales pipeline (priority), PROJECTS = active contracts."""

    def _load_active_proposals(self) -> List[Dict[str, Any]]:
        """
        Load active proposals for context.

        Returns list of proposals with key fields for matching.
        Includes country and keywords to help GPT distinguish similar projects.
        Also includes last email activity for follow-up detection.
        """
        try:
            proposals = self.execute_query("""
                SELECT
                    p.proposal_id,
                    p.project_code,
                    p.project_name,
                    p.client_company,
                    p.country,
                    p.status,
                    p.health_score,
                    p.days_since_contact,
                    p.project_value,
                    p.phase as current_phase,
                    -- Last email activity for follow-up detection
                    last_email.last_email_date,
                    last_email.days_since_email,
                    last_email.last_sender,
                    last_email.we_sent_last,
                    last_email.email_count
                FROM proposals p
                LEFT JOIN (
                    SELECT
                        epl.proposal_id,
                        MAX(e.date) as last_email_date,
                        CAST(julianday('now') - julianday(MAX(e.date)) AS INTEGER) as days_since_email,
                        (SELECT sender_email FROM emails e2
                         JOIN email_proposal_links epl2 ON e2.email_id = epl2.email_id
                         WHERE epl2.proposal_id = epl.proposal_id
                         ORDER BY e2.date DESC LIMIT 1) as last_sender,
                        CASE WHEN (SELECT sender_email FROM emails e2
                                   JOIN email_proposal_links epl2 ON e2.email_id = epl2.email_id
                                   WHERE epl2.proposal_id = epl.proposal_id
                                   ORDER BY e2.date DESC LIMIT 1) LIKE '%@bensley%'
                             THEN 1 ELSE 0 END as we_sent_last,
                        COUNT(DISTINCT epl.email_id) as email_count
                    FROM email_proposal_links epl
                    JOIN emails e ON epl.email_id = e.email_id
                    GROUP BY epl.proposal_id
                ) last_email ON p.proposal_id = last_email.proposal_id
                WHERE p.status NOT IN ('lost', 'cancelled', 'archived')
                ORDER BY
                    CASE p.status
                        WHEN 'proposal' THEN 1
                        WHEN 'submitted' THEN 2
                        WHEN 'negotiation' THEN 3
                        WHEN 'won' THEN 4
                        ELSE 5
                    END,
                    p.project_code DESC
                LIMIT 100
            """)

            logger.info(f"Loaded {len(proposals)} active proposals")
            return proposals

        except Exception as e:
            logger.error(f"Failed to load proposals: {e}")
            return []

    def _load_active_projects(self) -> List[Dict[str, Any]]:
        """
        Load active projects for context.

        Returns list of projects with key fields for matching.
        """
        try:
            projects = self.execute_query("""
                SELECT
                    p.project_id,
                    p.project_code,
                    p.project_title as project_name,
                    c.company_name as client_company,
                    p.status,
                    p.current_phase
                FROM projects p
                LEFT JOIN clients c ON p.client_id = c.client_id
                WHERE p.status NOT IN ('completed', 'cancelled', 'archived', 'on_hold', 'Completed')
                ORDER BY p.project_code DESC
                LIMIT 50
            """)

            logger.info(f"Loaded {len(projects)} active projects")
            return projects

        except Exception as e:
            logger.error(f"Failed to load projects: {e}")
            return []

    def _load_learned_patterns(self) -> List[Dict[str, Any]]:
        """
        Load learned email patterns for enhanced matching.

        These patterns come from previous user approvals and help
        identify sender → project relationships.
        """
        try:
            patterns = self.execute_query("""
                SELECT
                    pattern_type,
                    pattern_key,
                    pattern_key_normalized,
                    target_type,
                    target_code,
                    target_name,
                    confidence,
                    times_correct
                FROM email_learned_patterns
                WHERE is_active = 1
                AND confidence >= 0.6
                ORDER BY confidence DESC, times_correct DESC
                LIMIT 200
            """)

            logger.info(f"Loaded {len(patterns)} learned patterns")
            return patterns

        except Exception as e:
            logger.error(f"Failed to load patterns: {e}")
            return []

    def _load_contact_mappings(self) -> List[Dict[str, Any]]:
        """
        Load contact-to-project mappings from learned patterns AND email links.

        Returns contacts with their associated projects for
        intelligent email-to-project linking.
        """
        try:
            # Get contact mappings from learned patterns (sender_to_proposal)
            pattern_mappings = self.execute_query("""
                SELECT DISTINCT
                    pattern_key as email,
                    target_code as project_code,
                    target_name as project_name,
                    confidence,
                    'pattern' as source
                FROM email_learned_patterns
                WHERE pattern_type IN ('sender_to_project', 'sender_to_proposal')
                AND is_active = 1
                AND confidence >= 0.6
                ORDER BY confidence DESC
                LIMIT 100
            """)

            # Also get high-confidence links from email_proposal_links
            link_mappings = self.execute_query("""
                SELECT DISTINCT
                    e.sender_email as email,
                    p.project_code,
                    p.project_name,
                    epl.confidence_score as confidence,
                    'link' as source
                FROM email_proposal_links epl
                JOIN emails e ON epl.email_id = e.email_id
                JOIN proposals p ON epl.proposal_id = p.proposal_id
                WHERE epl.confidence_score >= 0.8
                AND e.sender_email IS NOT NULL
                AND e.sender_email NOT LIKE '%@bensley.com'
                GROUP BY e.sender_email, p.project_code
                ORDER BY epl.confidence_score DESC
                LIMIT 100
            """)

            # Combine and dedupe
            all_mappings = pattern_mappings + link_mappings
            logger.info(f"Loaded {len(all_mappings)} contact mappings ({len(pattern_mappings)} from patterns, {len(link_mappings)} from links)")
            return all_mappings

        except Exception as e:
            logger.error(f"Failed to load contact mappings: {e}")
            return []

    def _load_multi_project_contacts(self) -> List[str]:
        """
        Load contacts that work across multiple projects.

        These contacts should NOT trigger automatic project linking
        because their emails could relate to any of several projects.
        """
        try:
            contacts = self.execute_query("""
                SELECT email
                FROM contact_context
                WHERE is_multi_project = 1
                OR email_handling_preference = 'categorize_only'
            """)

            emails = [c['email'] for c in contacts if c.get('email')]
            logger.info(f"Loaded {len(emails)} multi-project contacts")
            return emails

        except Exception as e:
            logger.error(f"Failed to load multi-project contacts: {e}")
            return []

    def _load_known_staff(self) -> List[Dict[str, Any]]:
        """
        Load staff members who use personal emails (not @bensley.com).

        These should be classified as 'internal' even though their
        email domain is not a Bensley domain.
        """
        try:
            # Get staff from contact_context where relationship_type = 'internal'
            # but email is NOT a Bensley domain
            staff = self.execute_query("""
                SELECT email, role, context_notes
                FROM contact_context
                WHERE relationship_type = 'internal'
                AND email NOT LIKE '%@bensley.com'
                AND email NOT LIKE '%@bensleydesign.com'
                AND email NOT LIKE '%@bensley.co.th'
                AND email NOT LIKE '%@bensley.id'
                AND confidence >= 0.6
            """)

            logger.info(f"Loaded {len(staff)} known staff with personal emails")
            return staff

        except Exception as e:
            logger.error(f"Failed to load known staff: {e}")
            return []

    def _estimate_tokens(self, bundle: Dict[str, Any]) -> int:
        """
        Estimate token count for the bundle.

        Rough estimate: ~4 characters per token for English text.
        """
        import json

        # Serialize relevant parts
        context_str = bundle.get("business_context", "")
        proposals_str = json.dumps(bundle.get("active_proposals", []))
        projects_str = json.dumps(bundle.get("active_projects", []))
        patterns_str = json.dumps(bundle.get("learned_patterns", []))

        total_chars = len(context_str) + len(proposals_str) + len(projects_str) + len(patterns_str)
        estimated_tokens = total_chars // 4

        return estimated_tokens

    def format_for_prompt(self) -> str:
        """
        Format the context bundle as a string for GPT prompt injection.

        Returns a formatted string optimized for token efficiency.
        """
        bundle = self.get_bundle()

        parts = []

        # Business context (already formatted)
        parts.append(bundle["business_context"])

        # Active proposals (compact format with country for disambiguation)
        parts.append("\n## Active Proposals (prioritize for email linking)")
        parts.append("Format: CODE: Name | Client | Country | Status | Last Activity")
        if bundle["active_proposals"]:
            for p in bundle["active_proposals"][:85]:  # Include all active proposals
                client = p.get('client_company') or '-'
                country = p.get('country') or '-'

                # Build activity string for follow-up detection
                days = p.get('days_since_email')
                we_sent = p.get('we_sent_last')
                status = p.get('status', 'unknown')

                activity = ""
                if days is not None and days > 0:
                    if we_sent:
                        activity = f" | ⚠️ {days}d ago (WE sent last - awaiting response)"
                    else:
                        activity = f" | {days}d ago (THEY sent last)"

                    # Flag stale submitted proposals
                    if status == 'submitted' and we_sent and days > 14:
                        activity += " 🔴 NEEDS FOLLOW-UP"
                elif p.get('email_count', 0) == 0:
                    activity = " | No emails linked"

                parts.append(
                    f"- {p.get('project_code', 'N/A')}: {p.get('project_name', 'Unknown')} | "
                    f"{client} | {country} | {status}{activity}"
                )
        else:
            parts.append("(No active proposals)")

        # Learned patterns (compact format) - include ALL pattern types
        parts.append("\n## Learned Email Patterns (MUST USE - high-confidence mappings from user corrections)")
        if bundle["learned_patterns"]:
            # Domain patterns (e.g., @bdlbali.com → 25 BK-033)
            domain_patterns = [p for p in bundle["learned_patterns"]
                              if "domain" in p.get("pattern_type", "")]
            if domain_patterns:
                parts.append("### Domain Mappings (emails from these domains MUST link to these projects):")
                for p in domain_patterns[:20]:
                    parts.append(
                        f"- {p.get('pattern_key_normalized', p.get('pattern_key', 'N/A'))} → "
                        f"{p.get('target_code', 'N/A')} ({p.get('target_name', 'Unknown')}) "
                        f"[conf: {p.get('confidence', 0):.2f}]"
                    )

            # Sender patterns (e.g., specific email addresses)
            sender_patterns = [p for p in bundle["learned_patterns"]
                              if "sender" in p.get("pattern_type", "")]
            if sender_patterns:
                parts.append("### Sender Mappings (emails from these senders MUST link to these projects):")
                for p in sender_patterns[:20]:
                    parts.append(
                        f"- {p.get('pattern_key_normalized', p.get('pattern_key', 'N/A'))} → "
                        f"{p.get('target_code', 'N/A')} ({p.get('target_name', 'Unknown')}) "
                        f"[conf: {p.get('confidence', 0):.2f}]"
                    )

            # Keyword patterns (e.g., subject keywords → project)
            keyword_patterns = [p for p in bundle["learned_patterns"]
                               if "keyword" in p.get("pattern_type", "") and "skip" not in p.get("pattern_type", "")]
            if keyword_patterns:
                parts.append("### Keyword Mappings (emails with these keywords in subject MUST link to these projects):")
                for p in keyword_patterns[:20]:
                    parts.append(
                        f"- \"{p.get('pattern_key', 'N/A')}\" → "
                        f"{p.get('target_code', 'N/A')} ({p.get('target_name', 'Unknown')}) "
                        f"[conf: {p.get('confidence', 0):.2f}]"
                    )

            # Internal category patterns (e.g., @naviworld.com → INT-OPS)
            internal_patterns = [p for p in bundle["learned_patterns"]
                                if "internal" in p.get("pattern_type", "")]
            if internal_patterns:
                parts.append("### Internal Category Mappings (link to internal categories, NOT projects):")
                for p in internal_patterns[:15]:
                    parts.append(
                        f"- {p.get('pattern_key', 'N/A')} → "
                        f"{p.get('target_code', 'N/A')} ({p.get('target_name', 'Unknown')})"
                    )

            # Skip patterns (e.g., cancelled projects)
            skip_patterns = [p for p in bundle["learned_patterns"]
                            if "skip" in p.get("pattern_type", "")]
            if skip_patterns:
                parts.append("### Skip Patterns (do NOT link these - cancelled/irrelevant):")
                for p in skip_patterns[:15]:
                    parts.append(
                        f"- {p.get('pattern_key', 'N/A')} → SKIP ({p.get('target_name', 'No reason')})"
                    )

            # Project redirect patterns (merged projects)
            redirect_patterns = [p for p in bundle["learned_patterns"]
                                if p.get("pattern_type") == "project_redirect"]
            if redirect_patterns:
                parts.append("### Project Redirects (merged projects - use the NEW code):")
                for p in redirect_patterns[:15]:
                    parts.append(
                        f"- {p.get('pattern_key', 'N/A')} → {p.get('target_code', 'N/A')} "
                        f"(merged into {p.get('target_name', 'Unknown')})"
                    )

        # Contact-to-project mappings (from approved links)
        if bundle.get("contact_mappings"):
            parts.append("\n## Known Contact-Project Associations (from approved links)")
            for m in bundle["contact_mappings"][:30]:
                parts.append(
                    f"- {m.get('email', 'N/A')} → {m.get('project_code', 'N/A')} ({m.get('project_name', 'Unknown')})"
                )

        # Multi-project contacts
        parts.append("\n## Multi-Project Contacts (DO NOT auto-link to single project)")
        if bundle["multi_project_contacts"]:
            parts.append(", ".join(bundle["multi_project_contacts"][:20]))

        # Known staff with personal emails
        parts.append("\n## Known Staff (Personal Emails - classify as INTERNAL)")
        if bundle.get("known_staff"):
            for s in bundle["known_staff"][:20]:
                role_info = f" ({s.get('role')})" if s.get('role') else ""
                parts.append(f"- {s.get('email', 'N/A')}{role_info}")
        else:
            parts.append("(None learned yet)")

        return "\n".join(parts)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the context bundle"""
        bundle = self.get_bundle()

        return {
            "built_at": bundle.get("built_at"),
            "estimated_tokens": bundle.get("estimated_tokens", 0),
            "proposal_count": len(bundle.get("active_proposals", [])),
            "project_count": len(bundle.get("active_projects", [])),
            "pattern_count": len(bundle.get("learned_patterns", [])),
            "contact_mapping_count": len(bundle.get("contact_mappings", [])),
            "multi_project_contact_count": len(bundle.get("multi_project_contacts", [])),
            "known_staff_count": len(bundle.get("known_staff", [])),
            "cache_valid": self._is_cache_valid(),
            "cache_age_seconds": time.time() - self._cache_time if self._cache_time else None,
        }


# Singleton instance for reuse
_bundler_instance: Optional[ContextBundler] = None


def get_context_bundler(db_path: str = None) -> ContextBundler:
    """Get or create the singleton ContextBundler instance"""
    global _bundler_instance

    if _bundler_instance is None:
        _bundler_instance = ContextBundler(db_path)

    return _bundler_instance
