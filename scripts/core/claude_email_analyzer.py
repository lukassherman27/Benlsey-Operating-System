#!/usr/bin/env python3
"""
Claude Email Analyzer - Replace GPT with Claude CLI for email analysis

This script:
1. Gets unlinked emails that need analysis
2. Builds database context (proposals, contacts, patterns)
3. Generates suggestions for human review
4. Learns patterns from approvals

Unlike GPT which only sees email text, Claude CLI has full database context.

Usage:
    python scripts/core/claude_email_analyzer.py --limit 50
    python scripts/core/claude_email_analyzer.py --email-id 12345
    python scripts/core/claude_email_analyzer.py --dry-run
"""

import sqlite3
import json
import re
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = os.getenv('DATABASE_PATH', str(PROJECT_ROOT / 'database' / 'bensley_master.db'))


def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def extract_email_address(sender: str) -> str:
    """Extract just the email address from sender field"""
    if not sender:
        return ""
    match = re.search(r'<([^>]+@[^>]+)>', sender)
    if match:
        return match.group(1).lower().strip()
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', sender)
    if match:
        return match.group(0).lower().strip()
    return sender.lower().strip()


def get_unlinked_emails(conn, limit: int = 50, email_id: int = None) -> List[Dict]:
    """Get emails that need analysis - focus on PROPOSAL category that should be linked"""
    cursor = conn.cursor()

    if email_id:
        cursor.execute("""
            SELECT email_id, sender_email, recipient_emails, subject,
                   substr(body_full, 1, 2000) as body_preview, date, folder,
                   thread_id, primary_category
            FROM emails WHERE email_id = ?
        """, (email_id,))
    else:
        # Focus on PROPOSAL category emails that should be linked but aren't
        # Skip internal, operations categories (SM, SM-WILD, SCHEDULING, etc)
        cursor.execute("""
            SELECT e.email_id, e.sender_email, e.recipient_emails, e.subject,
                   substr(e.body_full, 1, 2000) as body_preview, e.date, e.folder,
                   e.thread_id, e.primary_category
            FROM emails e
            WHERE NOT EXISTS (SELECT 1 FROM email_proposal_links epl WHERE epl.email_id = e.email_id)
            AND NOT EXISTS (SELECT 1 FROM email_project_links eprl WHERE eprl.email_id = e.email_id)
            AND e.date LIKE '2025-%'
            AND e.primary_category IN ('PROPOSAL', 'PROJECT-CONTRACT', 'PROJECT-DESIGN', 'PROJECT-FINANCIAL', 'PROJECT')
            AND e.sender_email NOT LIKE '%@bensley.com%'
            AND e.sender_email NOT LIKE '%noreply%'
            AND e.sender_email NOT LIKE '%notification%'
            ORDER BY e.date DESC
            LIMIT ?
        """, (limit,))

    return [dict(row) for row in cursor.fetchall()]


def get_proposals_context(conn) -> List[Dict]:
    """Get all proposals for matching context"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT project_code, project_name, status,
               contact_email, contact_person,
               client_company
        FROM proposals
        WHERE project_code LIKE '2%'
        ORDER BY project_code DESC
    """)
    return [dict(row) for row in cursor.fetchall()]


def get_contacts_with_proposals(conn) -> Dict[str, List[str]]:
    """Get contacts and their linked proposals for pattern matching"""
    cursor = conn.cursor()

    # Use contact_project_mappings which tracks email-project relationships
    cursor.execute("""
        SELECT DISTINCT
            cpm.contact_email,
            cpm.project_code,
            COALESCE(p.project_name, cpm.project_code) as project_name
        FROM contact_project_mappings cpm
        LEFT JOIN proposals p ON cpm.project_code = p.project_code
        WHERE cpm.contact_email IS NOT NULL AND cpm.contact_email != ''
        ORDER BY cpm.contact_email
    """)

    contacts = {}
    for row in cursor.fetchall():
        email = row[0].lower() if row[0] else None
        if email:
            if email not in contacts:
                contacts[email] = []
            contacts[email].append({
                'code': row[1],
                'name': row[2]
            })

    # Also add proposal stakeholders
    cursor.execute("""
        SELECT DISTINCT
            ps.email,
            ps.project_code,
            COALESCE(p.project_name, ps.project_code) as project_name
        FROM proposal_stakeholders ps
        LEFT JOIN proposals p ON ps.project_code = p.project_code
        WHERE ps.email IS NOT NULL AND ps.email != ''
    """)

    for row in cursor.fetchall():
        email = row[0].lower() if row[0] else None
        if email:
            if email not in contacts:
                contacts[email] = []
            # Avoid duplicates
            if not any(c['code'] == row[1] for c in contacts[email]):
                contacts[email].append({
                    'code': row[1],
                    'name': row[2]
                })

    return contacts


def get_domain_patterns(conn) -> Dict[str, Dict]:
    """Get existing domain patterns"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pattern_key_normalized, target_code, target_name, confidence
        FROM email_learned_patterns
        WHERE pattern_type LIKE 'domain%' AND is_active = 1
        ORDER BY confidence DESC
    """)
    return {row[0]: {'code': row[1], 'name': row[2], 'conf': row[3]} for row in cursor.fetchall()}


def analyze_email(email: Dict, proposals: List[Dict], contacts: Dict, domains: Dict) -> Dict:
    """
    Analyze a single email and suggest proposal links.

    This is the core analysis logic that replaces GPT.
    Claude CLI can enhance this with additional context.
    """
    sender = extract_email_address(email.get('sender_email', ''))
    sender_domain = sender.split('@')[1] if '@' in sender else ''
    subject = email.get('subject', '') or ''
    body = email.get('body_preview', '') or ''
    text = f"{subject} {body}".lower()

    suggestions = []

    # 1. Check if sender email matches a known contact
    if sender in contacts:
        for proj in contacts[sender]:
            suggestions.append({
                'project_code': proj['code'],
                'project_name': proj['name'],
                'confidence': 0.90,
                'method': 'contact_match',
                'reasoning': f"Sender {sender} is a known contact for {proj['code']}"
            })

    # 2. Check domain patterns
    if sender_domain in domains:
        match = domains[sender_domain]
        suggestions.append({
            'project_code': match['code'],
            'project_name': match['name'],
            'confidence': match['conf'],
            'method': 'domain_pattern',
            'reasoning': f"Domain @{sender_domain} has pattern for {match['code']}"
        })

    # 3. Check for project codes in subject (e.g., [24 BK-058])
    code_pattern = r'\b(2[0-5]\s*BK-\d{3}(?:-[A-Z])?)\b'
    code_matches = re.findall(code_pattern, subject, re.IGNORECASE)
    for code in code_matches:
        normalized_code = re.sub(r'\s+', ' ', code.upper())
        # Find matching proposal
        for p in proposals:
            if p['project_code'] == normalized_code:
                suggestions.append({
                    'project_code': p['project_code'],
                    'project_name': p['project_name'],
                    'confidence': 0.98,
                    'method': 'code_in_subject',
                    'reasoning': f"Project code {normalized_code} explicitly in subject"
                })
                break

    # 4. Check for distinctive project name keywords in subject (high confidence)
    # This catches cases like "Fenfushi" that are unique identifiers
    subject_lower = subject.lower()
    for p in proposals:
        name = (p['project_name'] or '').lower()
        # Find distinctive words that are unique to this project
        distinctive = [w for w in name.split() if
                      len(w) > 5 and
                      w not in {'hotel', 'resort', 'villa', 'project', 'development', 'luxury'} and
                      w.isalpha()]  # Only alphabetic words

        for word in distinctive:
            if word in subject_lower:
                suggestions.append({
                    'project_code': p['project_code'],
                    'project_name': p['project_name'],
                    'confidence': 0.85,
                    'method': 'name_in_subject',
                    'reasoning': f"Distinctive name '{word}' found in subject"
                })
                break  # Only one match per project

    # 5. Check for project name keywords in body - be more selective
    generic_words = {
        'hotel', 'resort', 'villa', 'project', 'india', 'thailand', 'vietnam',
        'development', 'luxury', 'residences', 'indonesia', 'maldives', 'china',
        'design', 'private', 'residence', 'mixed-use', 'philippines', 'taiwan',
        'boutique', 'beach', 'mountain', 'landscape', 'garden', 'club', 'group'
    }

    for p in proposals:
        name = (p['project_name'] or '').lower()
        # Skip very short names
        if len(name) < 8:
            continue

        # Extract distinctive keywords (not generic)
        keywords = [w for w in name.split() if len(w) > 4 and w not in generic_words]

        # Need at least 2 keyword matches for generic name matching
        if not keywords:
            continue

        matches = sum(1 for kw in keywords if kw in text)

        # Only suggest if multiple distinctive keywords match
        if matches >= 2:
            suggestions.append({
                'project_code': p['project_code'],
                'project_name': p['project_name'],
                'confidence': 0.65 + (0.05 * matches),
                'method': 'keyword_match',
                'reasoning': f"Keywords from '{p['project_name']}' found: {matches} matches"
            })

    # 6. Check company/client patterns - be more specific
    generic_company_words = {'group', 'company', 'ltd', 'inc', 'corp', 'holdings', 'international', 'global'}

    for p in proposals:
        company = (p.get('client_company') or '').lower()
        if company and len(company) > 6:
            # Extract significant words (not generic company terms)
            words = [w for w in company.split() if len(w) > 4 and w not in generic_company_words]
            if not words:
                continue

            # Need at least one distinctive company word match
            matches = [w for w in words if w in text]
            if matches:
                suggestions.append({
                    'project_code': p['project_code'],
                    'project_name': p['project_name'],
                    'confidence': 0.70,
                    'method': 'company_match',
                    'reasoning': f"Client company '{company}' - found: {', '.join(matches)}"
                })

    # Deduplicate and sort by confidence
    seen = set()
    unique_suggestions = []
    for s in sorted(suggestions, key=lambda x: x['confidence'], reverse=True):
        if s['project_code'] not in seen:
            seen.add(s['project_code'])
            unique_suggestions.append(s)

    return {
        'email_id': email['email_id'],
        'sender': sender,
        'subject': subject[:100],
        'suggestions': unique_suggestions[:3],  # Top 3
        'analyzed_at': datetime.now().isoformat()
    }


def create_suggestion(conn, email_id: int, analysis: Dict, dry_run: bool = False) -> bool:
    """Create an ai_suggestion for human review"""
    if not analysis.get('suggestions'):
        return False

    top = analysis['suggestions'][0]

    # Get proposal ID
    cursor = conn.cursor()
    cursor.execute("SELECT proposal_id FROM proposals WHERE project_code = ?",
                   (top['project_code'],))
    row = cursor.fetchone()
    proposal_id = row[0] if row else None

    if not proposal_id:
        return False

    suggestion_data = {
        'email_id': email_id,
        'proposal_id': proposal_id,  # Required by email_link_handler
        'sender': analysis['sender'],
        'subject': analysis['subject'],
        'project_code': top['project_code'],
        'project_name': top['project_name'],
        'confidence': top['confidence'],
        'confidence_score': top['confidence'],  # Handler also checks this key
        'method': top['method'],
        'match_method': top['method'],  # Handler uses this key for link record
        'reasoning': top['reasoning'],
        'match_reason': top['reasoning'],  # Handler uses this key for link record
        'all_suggestions': analysis['suggestions']
    }

    if dry_run:
        print(f"  [DRY RUN] Would create suggestion: {top['project_code']} ({top['confidence']:.0%})")
        return True

    cursor.execute("""
        INSERT OR IGNORE INTO ai_suggestions
        (source_type, source_id, suggestion_type, title, description,
         suggested_data, confidence_score, project_code, proposal_id,
         status, created_at)
        VALUES ('email', ?, 'email_link', ?, ?, ?, ?, ?, ?, 'pending', datetime('now'))
    """, (
        email_id,
        f"Link to {top['project_code']}",
        top['reasoning'],
        json.dumps(suggestion_data),
        top['confidence'],
        top['project_code'],
        proposal_id
    ))
    conn.commit()
    return True


def auto_link_high_confidence(conn, email_id: int, analysis: Dict,
                               threshold: float = 0.90, dry_run: bool = False) -> bool:
    """Auto-link emails with very high confidence matches"""
    if not analysis.get('suggestions'):
        return False

    top = analysis['suggestions'][0]
    if top['confidence'] < threshold:
        return False

    # Methods that are safe to auto-link
    safe_methods = ['code_in_subject', 'contact_match']
    if top['method'] not in safe_methods:
        return False

    cursor = conn.cursor()
    cursor.execute("SELECT proposal_id FROM proposals WHERE project_code = ?",
                   (top['project_code'],))
    row = cursor.fetchone()
    if not row:
        return False

    proposal_id = row[0]

    if dry_run:
        print(f"  [DRY RUN] Would auto-link to {top['project_code']} ({top['confidence']:.0%})")
        return True

    cursor.execute("""
        INSERT OR IGNORE INTO email_proposal_links
        (email_id, proposal_id, confidence_score, match_method, created_at)
        VALUES (?, ?, ?, ?, datetime('now'))
    """, (email_id, proposal_id, top['confidence'], f"claude_{top['method']}"))

    # Update email category
    cursor.execute("""
        UPDATE emails SET primary_category = 'PROPOSAL'
        WHERE email_id = ? AND (primary_category IS NULL OR primary_category = '')
    """, (email_id,))

    conn.commit()
    return True


def main():
    parser = argparse.ArgumentParser(description='Claude Email Analyzer')
    parser.add_argument('--limit', type=int, default=50, help='Number of emails to analyze')
    parser.add_argument('--email-id', type=int, help='Analyze specific email')
    parser.add_argument('--dry-run', action='store_true', help='Show what would happen')
    parser.add_argument('--auto-link', action='store_true', help='Auto-link high confidence matches')
    parser.add_argument('--threshold', type=float, default=0.90, help='Auto-link confidence threshold')
    args = parser.parse_args()

    print("=" * 60)
    print("CLAUDE EMAIL ANALYZER")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    conn = get_db_connection()

    # Load context
    print("\nLoading context...")
    proposals = get_proposals_context(conn)
    print(f"  {len(proposals)} proposals loaded")

    contacts = get_contacts_with_proposals(conn)
    print(f"  {len(contacts)} contacts with proposal links")

    domains = get_domain_patterns(conn)
    print(f"  {len(domains)} domain patterns")

    # Get emails to analyze
    emails = get_unlinked_emails(conn, limit=args.limit, email_id=args.email_id)
    print(f"\n{len(emails)} emails to analyze")

    if not emails:
        print("No emails need analysis!")
        return

    # Analyze each email
    results = {
        'analyzed': 0,
        'suggestions_created': 0,
        'auto_linked': 0,
        'no_match': 0
    }

    print("\n" + "-" * 60)
    for email in emails:
        analysis = analyze_email(email, proposals, contacts, domains)
        results['analyzed'] += 1

        print(f"\n[{email['email_id']}] {email['subject'][:60]}...")
        print(f"  From: {analysis['sender']}")

        if not analysis['suggestions']:
            print(f"  No matches found")
            results['no_match'] += 1
            continue

        for i, s in enumerate(analysis['suggestions']):
            marker = "→" if i == 0 else " "
            print(f"  {marker} {s['project_code']}: {s['project_name'][:40]} ({s['confidence']:.0%}) [{s['method']}]")

        # Auto-link or create suggestion
        if args.auto_link:
            if auto_link_high_confidence(conn, email['email_id'], analysis,
                                         threshold=args.threshold, dry_run=args.dry_run):
                results['auto_linked'] += 1
                continue

        if create_suggestion(conn, email['email_id'], analysis, dry_run=args.dry_run):
            results['suggestions_created'] += 1

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Analyzed:            {results['analyzed']}")
    print(f"Auto-linked:         {results['auto_linked']}")
    print(f"Suggestions created: {results['suggestions_created']}")
    print(f"No match found:      {results['no_match']}")

    if args.dry_run:
        print("\n[DRY RUN - No changes made]")

    conn.close()


if __name__ == '__main__':
    main()
