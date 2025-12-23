"""
Email Link Processor - Unified Service

This is the MAIN entry point for processing emails.

Flow:
1. Pattern matching (instant, no API cost)
2. GPT only for unknowns (~20% of emails)
3. Single review queue for uncertain links
4. Real learning from corrections

Usage:
    from backend.services.email_link_processor import process_emails, review_pending, apply_correction

    # Process emails
    result = process_emails(limit=100)
    print(f"Auto-linked: {result['auto_linked']}, Needs review: {result['needs_review']}")

    # Get pending reviews
    reviews = review_pending(limit=20)

    # Apply correction and learn
    apply_correction(suggestion_id=123, correct_code="25 BK-047")
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add backend to path if needed
if "backend" not in sys.path[0]:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.pattern_first_linker import PatternFirstLinker, get_pattern_linker
from services.gpt_suggestion_analyzer import GPTSuggestionAnalyzer
from services.context_bundler import get_context_bundler

logger = logging.getLogger(__name__)


def process_emails(
    email_ids: List[int] = None,
    limit: int = 100,
    use_gpt: bool = True,
    max_gpt_workers: int = 10,
    db_path: str = None,
) -> Dict[str, Any]:
    """
    Process emails with pattern-first approach.

    1. Try pattern matching first (instant)
    2. Auto-link high-confidence matches
    3. Send unknowns to GPT (if use_gpt=True)
    4. Create review suggestions for uncertain GPT results

    Args:
        email_ids: Specific IDs to process, or None for unlinked 2025 emails
        limit: Max emails to process
        use_gpt: Whether to call GPT for unknowns (default True)
        max_gpt_workers: Parallel GPT calls (default 10)
        db_path: Database path

    Returns:
        {
            "total": int,
            "auto_linked": int,      # Pattern matched, no GPT needed
            "gpt_analyzed": int,     # Sent to GPT
            "needs_review": int,     # Created review suggestions
            "skipped": int,          # Spam/internal skipped
            "cost_usd": float,       # GPT cost
            "time_seconds": float,
        }
    """
    start = datetime.now()
    db_path = db_path or os.environ.get("DATABASE_PATH", "database/bensley_master.db")

    linker = get_pattern_linker(db_path)

    # Step 1: Pattern matching
    logger.info(f"Step 1: Pattern matching for {limit} emails...")
    pattern_result = linker.process_batch(email_ids, limit)

    result = {
        "total": pattern_result["total"],
        "auto_linked": pattern_result["auto_linked"],
        "gpt_analyzed": 0,
        "needs_review": 0,
        "skipped": pattern_result["skipped_spam"],
        "cost_usd": 0.0,
    }

    logger.info(
        f"Pattern results: {result['auto_linked']} auto-linked, "
        f"{len(pattern_result['needs_gpt_ids'])} need GPT, "
        f"{result['skipped']} skipped"
    )

    # Step 2: GPT for unknowns
    needs_gpt_ids = pattern_result["needs_gpt_ids"]

    if use_gpt and needs_gpt_ids:
        logger.info(f"Step 2: GPT analysis for {len(needs_gpt_ids)} emails...")

        gpt_result = _analyze_with_gpt(needs_gpt_ids, max_gpt_workers, db_path)

        result["gpt_analyzed"] = gpt_result["analyzed"]
        result["cost_usd"] = gpt_result["cost_usd"]

        # Create review suggestions for GPT results
        if gpt_result["results"]:
            suggestions_created = linker.create_review_suggestions(
                needs_gpt_ids[:len(gpt_result["results"])],
                gpt_result["results"]
            )
            result["needs_review"] = suggestions_created

    result["time_seconds"] = round((datetime.now() - start).total_seconds(), 2)

    logger.info(
        f"Complete: {result['auto_linked']} auto-linked, "
        f"{result['gpt_analyzed']} GPT analyzed, "
        f"{result['needs_review']} need review, "
        f"${result['cost_usd']:.4f} cost, "
        f"{result['time_seconds']}s"
    )

    return result


def _analyze_with_gpt(
    email_ids: List[int],
    max_workers: int,
    db_path: str,
) -> Dict[str, Any]:
    """Run GPT analysis on emails that need it"""
    from services.base_service import BaseService

    class TempService(BaseService):
        pass

    svc = TempService(db_path)

    # Load emails
    placeholders = ",".join("?" * len(email_ids))
    emails = svc.execute_query(f"""
        SELECT email_id, sender_email, recipient_emails, subject,
               body_full, body_preview as body, date, folder, thread_id
        FROM emails WHERE email_id IN ({placeholders})
    """, tuple(email_ids))

    if not emails:
        return {"analyzed": 0, "cost_usd": 0, "results": []}

    # Get context
    bundler = get_context_bundler(db_path)
    context_prompt = bundler.format_for_prompt()

    # Analyze with GPT
    analyzer = GPTSuggestionAnalyzer()
    results = analyzer.analyze_batch([dict(e) for e in emails], context_prompt, max_workers)

    total_cost = sum(
        r.get("usage", {}).get("estimated_cost_usd", 0)
        for r in results if r.get("success")
    )

    return {
        "analyzed": len([r for r in results if r.get("success")]),
        "cost_usd": total_cost,
        "results": results,
    }


def review_pending(limit: int = 20, db_path: str = None) -> List[Dict[str, Any]]:
    """
    Get pending email_link suggestions for review.
    ONE queue - just links that need human approval.
    """
    db_path = db_path or os.environ.get("DATABASE_PATH", "database/bensley_master.db")

    from services.base_service import BaseService

    class TempService(BaseService):
        pass

    svc = TempService(db_path)

    return svc.execute_query("""
        SELECT
            s.suggestion_id,
            s.source_id as email_id,
            SUBSTR(e.date, 1, 10) as date,
            e.sender_email,
            e.subject,
            SUBSTR(e.body_full, 1, 300) as body_preview,
            json_extract(s.suggested_data, '$.project_code') as suggested_code,
            json_extract(s.suggested_data, '$.project_name') as suggested_name,
            json_extract(s.suggested_data, '$.reasoning') as reasoning,
            s.confidence_score as confidence
        FROM ai_suggestions s
        JOIN emails e ON s.source_id = e.email_id
        WHERE s.status = 'pending'
        AND s.suggestion_type = 'email_link'
        ORDER BY e.date ASC
        LIMIT ?
    """, (limit,))


def apply_correction(
    suggestion_id: int,
    action: str,
    correct_code: str = None,
    db_path: str = None,
) -> Dict[str, Any]:
    """
    Apply a correction and learn from it.

    Args:
        suggestion_id: The suggestion to act on
        action: "approve" | "correct" | "reject" | "skip"
        correct_code: If action="correct", the correct project code
        db_path: Database path

    Returns:
        {
            "success": bool,
            "action": str,
            "learned": bool,
            "pattern_created": str | None,
        }
    """
    db_path = db_path or os.environ.get("DATABASE_PATH", "database/bensley_master.db")

    linker = get_pattern_linker(db_path)

    # Get suggestion details
    suggestion = linker.execute_query("""
        SELECT s.*, e.sender_email
        FROM ai_suggestions s
        JOIN emails e ON s.source_id = e.email_id
        WHERE s.suggestion_id = ?
    """, (suggestion_id,), fetch_one=True)

    if not suggestion:
        return {"success": False, "error": "Suggestion not found"}

    email_id = suggestion["source_id"]
    suggested_data = json.loads(suggestion["suggested_data"])

    if action == "approve":
        # Apply the suggested link
        target_type = "proposal" if "proposal_id" in suggested_data else "project"
        target_id = suggested_data.get("proposal_id") or suggested_data.get("project_id")

        linker.apply_link(
            email_id,
            target_type,
            target_id,
            suggestion["confidence"],
            "approved_suggestion"
        )

        # Learn from approval
        learn_result = linker.learn_from_correction(
            email_id,
            target_type,
            target_id,
            suggested_data.get("project_code"),
            suggested_data.get("project_name"),
        )

        linker.execute_update(
            "UPDATE ai_suggestions SET status = 'approved' WHERE suggestion_id = ?",
            (suggestion_id,)
        )

        return {
            "success": True,
            "action": "approve",
            "learned": True,
            "pattern_created": learn_result.get("message"),
        }

    elif action == "correct":
        if not correct_code:
            return {"success": False, "error": "correct_code required for correction"}

        # Look up the correct target
        proposal = linker.execute_query("""
            SELECT proposal_id, project_name FROM proposals WHERE project_code = ?
        """, (correct_code,), fetch_one=True)

        project = None
        if not proposal:
            project = linker.execute_query("""
                SELECT project_id, project_title as project_name FROM projects WHERE project_code = ?
            """, (correct_code,), fetch_one=True)

        if not proposal and not project:
            return {"success": False, "error": f"Code {correct_code} not found"}

        target_type = "proposal" if proposal else "project"
        target_id = proposal["proposal_id"] if proposal else project["project_id"]
        target_name = proposal["project_name"] if proposal else project["project_name"]

        # Apply correct link
        linker.apply_link(email_id, target_type, target_id, 0.95, "corrected")

        # Learn from correction
        learn_result = linker.learn_from_correction(
            email_id, target_type, target_id, correct_code, target_name
        )

        linker.execute_update(
            "UPDATE ai_suggestions SET status = 'corrected' WHERE suggestion_id = ?",
            (suggestion_id,)
        )

        return {
            "success": True,
            "action": "correct",
            "learned": True,
            "pattern_created": learn_result.get("message"),
        }

    elif action == "reject":
        linker.execute_update(
            "UPDATE ai_suggestions SET status = 'rejected' WHERE suggestion_id = ?",
            (suggestion_id,)
        )
        return {"success": True, "action": "reject", "learned": False}

    elif action == "skip":
        # Mark as not project-related (INT-OPS, spam, etc)
        linker.execute_update(
            "UPDATE ai_suggestions SET status = 'skipped' WHERE suggestion_id = ?",
            (suggestion_id,)
        )
        return {"success": True, "action": "skip", "learned": False}

    return {"success": False, "error": f"Unknown action: {action}"}


def bulk_approve(suggestion_ids: List[int], db_path: str = None) -> Dict[str, Any]:
    """Approve multiple suggestions at once"""
    results = []
    for sid in suggestion_ids:
        result = apply_correction(sid, "approve", db_path=db_path)
        results.append(result)

    return {
        "total": len(suggestion_ids),
        "approved": sum(1 for r in results if r.get("success")),
        "patterns_learned": sum(1 for r in results if r.get("learned")),
    }


def bulk_reject(suggestion_ids: List[int], db_path: str = None) -> Dict[str, Any]:
    """Reject multiple suggestions at once"""
    db_path = db_path or os.environ.get("DATABASE_PATH", "database/bensley_master.db")
    linker = get_pattern_linker(db_path)

    placeholders = ",".join("?" * len(suggestion_ids))
    linker.execute_update(f"""
        UPDATE ai_suggestions SET status = 'rejected'
        WHERE suggestion_id IN ({placeholders})
    """, tuple(suggestion_ids))

    return {"total": len(suggestion_ids), "rejected": len(suggestion_ids)}


# CLI entry point
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process emails with pattern-first linking")
    parser.add_argument("--limit", type=int, default=100, help="Max emails to process")
    parser.add_argument("--no-gpt", action="store_true", help="Skip GPT analysis")
    parser.add_argument("--review", action="store_true", help="Show pending reviews instead")
    parser.add_argument("--db", type=str, help="Database path")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    if args.review:
        reviews = review_pending(limit=20, db_path=args.db)
        print(f"\n=== {len(reviews)} Pending Reviews ===\n")
        for r in reviews:
            print(f"[{r['suggestion_id']}] {r['date']} | {r['sender_email'][:30]}")
            print(f"  Subject: {r['subject'][:50]}")
            print(f"  Suggested: {r['suggested_code']} ({r['suggested_name']})")
            print(f"  Confidence: {r['confidence']:.0%}")
            print()
    else:
        result = process_emails(
            limit=args.limit,
            use_gpt=not args.no_gpt,
            db_path=args.db,
        )
        print(f"\n=== Results ===")
        print(f"Total:       {result['total']}")
        print(f"Auto-linked: {result['auto_linked']}")
        print(f"GPT analyzed:{result['gpt_analyzed']}")
        print(f"Need review: {result['needs_review']}")
        print(f"Skipped:     {result['skipped']}")
        print(f"Cost:        ${result['cost_usd']:.4f}")
        print(f"Time:        {result['time_seconds']}s")
