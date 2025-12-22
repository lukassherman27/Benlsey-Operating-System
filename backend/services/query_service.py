"""
Query Service - AI-Powered Natural Language Queries

Enhanced with GPT-4o for true natural language understanding.
Falls back to pattern matching if AI is not available.
"""

import sys
import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import OpenAI

# Add scripts/core to path to import query_brain
project_root = Path(__file__).parent.parent.parent
scripts_core_path = project_root / "scripts" / "core"
sys.path.insert(0, str(scripts_core_path))

from query_brain import QueryBrain
from .base_service import BaseService


class QueryService(BaseService):
    """Service for AI-powered natural language queries"""

    def __init__(self, db_path: str = None):
        super().__init__(db_path)
        self.query_brain = QueryBrain(str(self.db_path))

        # Initialize OpenAI if available
        api_key = os.environ.get('OPENAI_API_KEY')
        self.ai_enabled = bool(api_key)
        if self.ai_enabled:
            self.client = OpenAI(api_key=api_key)
            self._schema_cache = None  # Lazy load schema when needed
        else:
            self.client = None
            self._schema_cache = None

    def _get_schema(self) -> str:
        """Get database schema for AI context (with caching)"""
        # Return cached schema if available
        if self._schema_cache is not None:
            return self._schema_cache

        # Load schema from database using context manager
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sql FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)

            tables = cursor.fetchall()
            schema_text = "DATABASE SCHEMA:\n\n"

            for table in tables:
                if table['sql']:
                    schema_text += table['sql'] + "\n\n"

        # Cache for future use
        self._schema_cache = schema_text
        return schema_text

    def _get_financial_query_hints(self, question: str) -> str:
        """Get specialized hints for financial/invoice/payment questions"""
        q_lower = question.lower()

        # Detect financial query keywords
        financial_keywords = [
            'invoice', 'payment', 'paid', 'fee', 'breakdown', 'financial',
            'outstanding', 'overdue', 'invoiced', 'contract value', 'phase',
            'total', 'sum', 'amount', 'billing', 'revenue', 'money'
        ]

        if not any(kw in q_lower for kw in financial_keywords):
            return ""

        return """
FINANCIAL QUERY INSTRUCTIONS:
When the user asks about invoices, payments, fees, or financial data, use these guidelines:

KEY TABLES FOR FINANCIAL DATA:
1. projects - Has project_code, project_title, total_fee_usd (contract value)
2. project_fee_breakdown - Fee breakdown by phase. Columns:
   - project_code, discipline, phase, phase_fee_usd
   - total_invoiced, total_paid (aggregated from invoices)
   - scope (for projects with multiple scopes like "Main Tower", "Sale Center")
3. invoices - Individual invoices. Columns:
   - project_id (FK to projects), invoice_number, invoice_date, due_date
   - invoice_amount, payment_amount, payment_date, status
   - breakdown_id (links to project_fee_breakdown)

EXAMPLE QUERIES FOR FINANCIAL QUESTIONS:

1. "Show financial breakdown for [project]":
SELECT
    pfb.discipline,
    pfb.phase,
    pfb.scope,
    pfb.phase_fee_usd as fee,
    pfb.total_invoiced as invoiced,
    pfb.total_paid as paid,
    (pfb.phase_fee_usd - pfb.total_invoiced) as remaining_to_invoice,
    (pfb.total_invoiced - pfb.total_paid) as outstanding
FROM project_fee_breakdown pfb
JOIN projects p ON pfb.project_code = p.project_code
WHERE p.project_title LIKE '%[search term]%' OR p.project_code LIKE '%[search term]%'
ORDER BY CASE pfb.phase
    WHEN 'Mobilization' THEN 1
    WHEN 'Concept Design' THEN 2
    WHEN 'Schematic Design' THEN 3
    WHEN 'Design Development' THEN 4
    WHEN 'Construction Documents' THEN 5
    WHEN 'Construction Observation' THEN 6
    ELSE 7
END;

2. "Show total invoices and payments for [project]":
SELECT
    p.project_code,
    p.project_title,
    p.total_fee_usd as contract_value,
    SUM(pfb.phase_fee_usd) as total_phase_fees,
    SUM(pfb.total_invoiced) as total_invoiced,
    SUM(pfb.total_paid) as total_paid,
    SUM(pfb.phase_fee_usd) - SUM(pfb.total_invoiced) as remaining_to_invoice,
    SUM(pfb.total_invoiced) - SUM(pfb.total_paid) as outstanding
FROM projects p
LEFT JOIN project_fee_breakdown pfb ON p.project_code = pfb.project_code
WHERE p.project_title LIKE '%[search term]%' OR p.project_code LIKE '%[search term]%'
GROUP BY p.project_code;

3. "List all invoices for [project]":
SELECT
    i.invoice_number,
    i.invoice_date,
    i.invoice_amount,
    i.payment_amount,
    i.payment_date,
    i.status
FROM invoices i
JOIN projects p ON i.project_id = p.project_id
WHERE p.project_title LIKE '%[search term]%' OR p.project_code LIKE '%[search term]%'
ORDER BY i.invoice_date;

4. "What is outstanding/unpaid":
SELECT
    p.project_code,
    p.project_title,
    SUM(i.invoice_amount) - COALESCE(SUM(i.payment_amount), 0) as outstanding
FROM projects p
JOIN invoices i ON p.project_id = i.project_id
WHERE i.status != 'paid'
GROUP BY p.project_code
HAVING outstanding > 0
ORDER BY outstanding DESC;

IMPORTANT:
- Always use project_fee_breakdown for phase-level financial data
- Use projects.total_fee_usd for contract value
- Join projects to project_fee_breakdown using project_code
- Join invoices to projects using project_id
- CRITICAL FOR PROJECT NAME SEARCH: When user provides multiple words (e.g., "Wynn Marjan"),
  split them and match EACH word separately with AND! Example:
  - User says "Wynn Marjan" → Use: (project_title LIKE '%Wynn%' AND project_title LIKE '%Marjan%')
  - User says "Rosewood Hotel" → Use: (project_title LIKE '%Rosewood%' AND project_title LIKE '%Hotel%')
  - This ensures "Wynn Al Marjan Island Project" matches when user searches "Wynn Marjan"
  - Also check project_code: (project_code LIKE '%term%') as fallback
"""

    def query(self, question: str, use_ai: bool = True) -> Dict[str, Any]:
        """
        Execute a natural language query with AI or pattern matching

        Args:
            question: Natural language question
            use_ai: Whether to use AI (True) or pattern matching (False)

        Returns:
            Dict with query results and metadata
        """
        # Check for special report queries first
        status_report = self._check_status_report_query(question)
        if status_report:
            return status_report

        # Use AI if enabled and requested
        if use_ai and self.ai_enabled:
            return self._query_with_ai(question)

        # Fall back to pattern matching
        return self._query_with_patterns(question)

    def process_query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a natural language query - alias for query() used by router.

        Args:
            query: Natural language question
            context: Optional context dict (currently unused, for future expansion)

        Returns:
            Dict with query results and metadata
        """
        return self.query(query)

    def _check_status_report_query(self, question: str) -> Optional[Dict[str, Any]]:
        """
        Check if the question is asking for a project status report.

        Patterns detected:
        - "project status report for X"
        - "status report for X"
        - "financial report for X"
        - "show me X project status"
        - "full breakdown for X"
        """
        q_lower = question.lower()

        # Patterns that indicate a status report request
        status_patterns = [
            r'(?:project\s+)?status\s+report\s+(?:for\s+)?(.+)',
            r'financial\s+report\s+(?:for\s+)?(.+)',
            r'full\s+(?:financial\s+)?breakdown\s+(?:for\s+)?(.+)',
            r'(?:show\s+me\s+)?(.+?)\s+(?:project\s+)?status\s+report',
            r'(?:show\s+me\s+)?(.+?)\s+full\s+breakdown',
            r'project\s+report\s+(?:for\s+)?(.+)',
        ]

        for pattern in status_patterns:
            match = re.search(pattern, q_lower)
            if match:
                project_identifier = match.group(1).strip()
                # Clean up common trailing words
                for suffix in ['project', 'please', 'thanks', 'report']:
                    project_identifier = re.sub(rf'\s*{suffix}\s*$', '', project_identifier)

                if project_identifier and len(project_identifier) > 1:
                    return self._get_project_status_report(project_identifier)

        return None

    def _get_project_status_report(self, project_identifier: str) -> Dict[str, Any]:
        """
        Get comprehensive project status report.

        Returns structured report with summary, scope breakdown, and invoices.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Split search terms and build query for multi-word matches
                search_words = project_identifier.split()

                if len(search_words) == 1:
                    # Single word - simple search
                    cursor.execute("""
                        SELECT project_id, project_code, project_title, status, total_fee_usd, country, city
                        FROM projects
                        WHERE project_code = ?
                           OR project_code LIKE ?
                           OR project_title LIKE ?
                        LIMIT 1
                    """, (project_identifier, f"%{project_identifier}%", f"%{project_identifier}%"))
                else:
                    # Multi-word - each word must match
                    # Build dynamic WHERE clause: project_title LIKE '%word1%' AND project_title LIKE '%word2%'
                    conditions = " AND ".join([f"project_title LIKE ?" for _ in search_words])
                    params = [f"%{word}%" for word in search_words]

                    cursor.execute(f"""
                        SELECT project_id, project_code, project_title, status, total_fee_usd, country, city
                        FROM projects
                        WHERE ({conditions})
                           OR project_code LIKE ?
                        LIMIT 1
                    """, params + [f"%{project_identifier.replace(' ', '%')}%"])

                project_row = cursor.fetchone()
                if not project_row:
                    return {
                        'success': False,
                        'question': f"Project status report for {project_identifier}",
                        'error': f"Project not found: {project_identifier}",
                        'results': [],
                        'method': 'status_report'
                    }

                project = dict(project_row)
                project_code = project['project_code']
                project_id = project['project_id']

                # Get fee breakdown by scope
                cursor.execute("""
                    SELECT scope, discipline, phase, phase_fee_usd, total_invoiced, total_paid, breakdown_id
                    FROM project_fee_breakdown
                    WHERE project_code = ?
                    ORDER BY scope,
                        CASE phase
                            WHEN 'Mobilization' THEN 1
                            WHEN 'Concept Design' THEN 2
                            WHEN 'Design Development' THEN 3
                            WHEN 'Construction Documents' THEN 4
                            WHEN 'Construction Observation' THEN 5
                            WHEN 'Additional Services' THEN 6
                            ELSE 7
                        END
                """, (project_code,))

                breakdown_rows = cursor.fetchall()

                # Get all invoices
                cursor.execute("""
                    SELECT
                        i.invoice_number, i.description, i.invoice_amount, i.invoice_date,
                        i.payment_amount, i.payment_date, i.status, b.scope, b.phase
                    FROM invoices i
                    LEFT JOIN project_fee_breakdown b ON i.breakdown_id = b.breakdown_id
                    WHERE i.project_id = ?
                    ORDER BY i.invoice_date, i.invoice_number
                """, (project_id,))

                invoice_rows = cursor.fetchall()

            # Organize breakdown by scope
            scopes = {}
            for row in breakdown_rows:
                scope = row['scope'] or 'unassigned'
                if scope not in scopes:
                    scopes[scope] = {
                        'scope': scope,
                        'discipline': row['discipline'],
                        'phases': [],
                        'contract_total': 0,
                        'invoiced_total': 0,
                        'paid_total': 0
                    }

                phase_data = {
                    'phase': row['phase'],
                    'contract_fee': row['phase_fee_usd'] or 0,
                    'invoiced': row['total_invoiced'] or 0,
                    'paid': row['total_paid'] or 0
                }
                scopes[scope]['phases'].append(phase_data)
                scopes[scope]['contract_total'] += phase_data['contract_fee']
                scopes[scope]['invoiced_total'] += phase_data['invoiced']
                scopes[scope]['paid_total'] += phase_data['paid']

            # Calculate totals
            total_contract = project['total_fee_usd'] or sum(s['contract_total'] for s in scopes.values())
            total_invoiced = sum(s['invoiced_total'] for s in scopes.values())
            total_paid = sum(s['paid_total'] for s in scopes.values())
            total_outstanding = total_invoiced - total_paid

            # Get outstanding invoices
            outstanding = [dict(r) for r in invoice_rows if r['status'] == 'outstanding' or not r['payment_date']]

            # Build invoice lookup by scope and phase
            invoices_by_scope_phase = {}
            for inv in invoice_rows:
                inv_dict = dict(inv)
                scope = inv_dict.get('scope') or 'unassigned'
                phase = inv_dict.get('phase') or 'unassigned'
                key = (scope, phase)
                if key not in invoices_by_scope_phase:
                    invoices_by_scope_phase[key] = []
                invoices_by_scope_phase[key].append(inv_dict)

            # Check for additional services scope
            additional_services_fee = 0
            for scope_data in scopes.values():
                if 'additional' in scope_data['scope'].lower():
                    additional_services_fee = scope_data['contract_total']

            # Format beautiful summary
            lines = []
            lines.append("═" * 80)
            lines.append(f"  {project['project_title'].upper()}")
            lines.append(f"  Project Code: {project_code} | Status: {project['status']} | Country: {project['country'] or 'N/A'}")
            lines.append("═" * 80)
            lines.append("")

            # Big financial summary box
            lines.append("  💰 FINANCIAL SUMMARY")
            lines.append("  " + "─" * 76)
            lines.append(f"  │  CONTRACT VALUE:                                    ${total_contract:>15,.2f}  │")
            if additional_services_fee > 0:
                lines.append(f"  │    └─ Additional Services:                         ${additional_services_fee:>15,.2f}  │")
            lines.append("  " + "─" * 76)
            lines.append(f"  │  Total Invoiced:                                    ${total_invoiced:>15,.2f}  │")
            lines.append(f"  │  Total Paid:                                        ${total_paid:>15,.2f}  │")
            if total_outstanding > 0:
                lines.append(f"  │  ⚠️  OUTSTANDING:                                   ${total_outstanding:>15,.2f}  │")
            else:
                lines.append(f"  │  Outstanding:                                       ${total_outstanding:>15,.2f}  │")
            remaining = total_contract - total_invoiced
            lines.append(f"  │  Remaining to Invoice:                              ${remaining:>15,.2f}  │")
            lines.append("  " + "─" * 76)
            lines.append("")

            # Scope-by-scope breakdown with invoices per phase
            for scope_name, scope_data in scopes.items():
                scope_title = scope_name.replace('-', ' ').upper()
                scope_outstanding = scope_data['invoiced_total'] - scope_data['paid_total']

                lines.append("")
                lines.append("═" * 80)
                lines.append(f"  🏗️  {scope_title}")
                lines.append(f"  {scope_data['discipline']} | Contract: ${scope_data['contract_total']:,.2f}")
                if scope_outstanding > 0:
                    lines.append(f"  ⚠️ Outstanding: ${scope_outstanding:,.2f}")
                lines.append("═" * 80)

                # Each phase
                for phase_data in scope_data['phases']:
                    phase_name = phase_data['phase']
                    phase_fee = phase_data['contract_fee']
                    phase_invoiced = phase_data['invoiced']
                    phase_paid = phase_data['paid']
                    phase_outstanding = phase_invoiced - phase_paid
                    phase_remaining = phase_fee - phase_invoiced

                    lines.append("")
                    lines.append(f"  📌 {phase_name.upper()}")
                    lines.append(f"     Phase Fee: ${phase_fee:,.2f}")
                    lines.append("     " + "─" * 71)

                    # Get invoices for this scope/phase
                    phase_invoices = invoices_by_scope_phase.get((scope_name, phase_name), [])

                    if phase_invoices:
                        lines.append("     │ Invoice   │ Inv Date   │ Invoice Amt   │ % Fee │ Paid Amt     │ Paid Date  │")
                        lines.append("     " + "─" * 71)

                        for inv in phase_invoices:
                            inv_num = inv.get('invoice_number', 'N/A')[:9]
                            inv_date = inv.get('invoice_date', 'N/A')[:10] if inv.get('invoice_date') else 'N/A'
                            inv_amt = inv.get('invoice_amount') or 0
                            pct = (inv_amt / phase_fee * 100) if phase_fee > 0 else 0
                            paid_amt = inv.get('payment_amount') or 0
                            paid_date = inv.get('payment_date', '')[:10] if inv.get('payment_date') else '—'
                            status_icon = "✓" if paid_amt >= inv_amt else "⏳"

                            lines.append(f"     │ {inv_num:<9} │ {inv_date:<10} │ ${inv_amt:>11,.2f} │ {pct:>4.0f}% │ ${paid_amt:>10,.2f} │ {paid_date:<10} │ {status_icon}")

                        lines.append("     " + "─" * 71)

                    # Phase summary
                    status_emoji = "✅" if phase_outstanding == 0 and phase_remaining == 0 else ("⚠️" if phase_outstanding > 0 else "📋")
                    lines.append(f"     {status_emoji} Invoiced: ${phase_invoiced:,.2f} | Paid: ${phase_paid:,.2f} | Outstanding: ${phase_outstanding:,.2f} | To Invoice: ${phase_remaining:,.2f}")

            # Outstanding invoices summary at bottom
            if outstanding:
                lines.append("")
                lines.append("═" * 80)
                lines.append("  ⚠️  OUTSTANDING INVOICES REQUIRING ACTION")
                lines.append("═" * 80)
                for inv in outstanding:
                    amt = (inv['invoice_amount'] or 0) - (inv['payment_amount'] or 0)
                    inv_date = inv.get('invoice_date', 'N/A')[:10] if inv.get('invoice_date') else 'N/A'
                    lines.append(f"  • {inv['invoice_number']}: ${amt:,.2f} — {inv.get('scope', 'N/A').replace('-', ' ').title()} / {inv.get('phase', 'N/A')} (invoiced {inv_date})")
                lines.append("")
                lines.append(f"  TOTAL OUTSTANDING: ${sum((inv['invoice_amount'] or 0) - (inv['payment_amount'] or 0) for inv in outstanding):,.2f}")

            lines.append("")
            lines.append("═" * 80)

            summary_text = "\n".join(lines)

            return {
                'success': True,
                'question': f"Project status report for {project_identifier}",
                'results': [dict(r) for r in invoice_rows],
                'count': len(invoice_rows),
                'summary': summary_text,
                'method': 'status_report',
                'report_type': 'project_status_report',
                'project': project,
                'scopes': list(scopes.values()),
                'totals': {
                    'contract': total_contract,
                    'invoiced': total_invoiced,
                    'paid': total_paid,
                    'outstanding': total_outstanding
                }
            }

        except Exception as e:
            return {
                'success': False,
                'question': f"Project status report for {project_identifier}",
                'error': str(e),
                'results': [],
                'method': 'status_report'
            }

    def query_with_context(
        self,
        question: str,
        conversation_context: Optional[str] = None,
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a natural language query with conversation context.

        This method supports follow-up questions by including previous
        conversation history to understand references like "those projects"
        or "what's the total?".

        Args:
            question: Current question
            conversation_context: Previous conversation messages formatted as string
            use_ai: Whether to use AI

        Returns:
            Dict with query results and metadata
        """
        # If no context or AI not available, use regular query
        if not conversation_context or not use_ai or not self.ai_enabled:
            return self.query(question, use_ai)

        # Use AI with conversation context
        return self._query_with_ai_context(question, conversation_context)

    def _query_with_ai(self, question: str) -> Dict[str, Any]:
        """Execute query using GPT-4o to generate SQL"""
        try:
            # Generate SQL with AI
            sql_result = self._generate_sql_with_ai(question)

            if not sql_result or not sql_result.get('sql'):
                return {
                    'success': False,
                    'question': question,
                    'error': 'Could not understand question',
                    'results': []
                }

            sql = sql_result['sql']

            # Execute the query safely
            results = self._execute_safe_query(sql)

            # Generate natural language summary
            summary = self._generate_summary(question, results)

            # Log for training data
            self._log_successful_query(
                question=question,
                results=results,
                summary=summary,
                sql=sql,
                method='ai',
                confidence=sql_result.get('confidence')
            )

            return {
                'success': True,
                'question': question,
                'results': results,
                'count': len(results),
                'sql': sql,
                'summary': summary,
                'reasoning': sql_result.get('reasoning'),
                'confidence': sql_result.get('confidence'),
                'method': 'ai'
            }

        except Exception as e:
            return {
                'success': False,
                'question': question,
                'error': str(e),
                'results': [],
                'method': 'ai'
            }

    def _query_with_ai_context(self, question: str, conversation_context: str) -> Dict[str, Any]:
        """Execute query using GPT-4o with conversation context for follow-up questions"""
        try:
            # Generate SQL with AI using conversation context
            sql_result = self._generate_sql_with_context(question, conversation_context)

            if not sql_result or not sql_result.get('sql'):
                return {
                    'success': False,
                    'question': question,
                    'error': 'Could not understand question in context',
                    'results': []
                }

            sql = sql_result['sql']

            # Execute the query safely
            results = self._execute_safe_query(sql)

            # Generate natural language summary with context
            summary = self._generate_summary(question, results)

            # Log for training data
            self._log_successful_query(
                question=question,
                results=results,
                summary=summary,
                sql=sql,
                method='ai_with_context',
                confidence=sql_result.get('confidence')
            )

            return {
                'success': True,
                'question': question,
                'results': results,
                'count': len(results),
                'sql': sql,
                'summary': summary,
                'reasoning': sql_result.get('reasoning'),
                'confidence': sql_result.get('confidence'),
                'method': 'ai_with_context'
            }

        except Exception as e:
            return {
                'success': False,
                'question': question,
                'error': str(e),
                'results': [],
                'method': 'ai_with_context'
            }

    def _generate_sql_with_context(self, question: str, conversation_context: str) -> Optional[Dict[str, Any]]:
        """Use GPT-4o to generate SQL query using conversation context"""

        # Get schema (lazy loaded and cached)
        schema = self._get_schema()

        prompt = f"""You are a SQL expert for a design firm's operations database.

{schema}

CONVERSATION HISTORY:
{conversation_context}

IMPORTANT RULES:
1. ONLY use SELECT queries - no INSERT, UPDATE, DELETE, DROP
2. Use proper JOINs when needed
3. Limit results to 100 unless explicitly asked for more
4. Handle NULL values properly
5. Use LIKE for text searches with % wildcards
6. For date comparisons, use strftime or date() functions
7. Be careful with column names - check schema first
8. CRITICAL: Use the conversation history to understand context
   - If user says "those projects" or "these results", refer to the previous query
   - If user asks "what's the total?", calculate totals from previous result set
   - If user wants to "filter" or "narrow down", add WHERE clauses to previous SQL

CURRENT QUESTION: {question}

Based on the conversation history, generate a SQL query that answers this question.
If the question references previous results (e.g., "what's the total value?", "filter by...",
"how many of those..."), use the context from previous SQL queries to build the new query.

Respond in JSON format:
{{
    "sql": "SELECT ... FROM ... WHERE ...",
    "reasoning": "Brief explanation including how you used conversation context",
    "tables_used": ["table1", "table2"],
    "confidence": 85,
    "used_context": true
}}

If the question is unclear or cannot be answered with available data, set sql to null.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a SQL expert that generates safe, efficient queries. You excel at understanding follow-up questions using conversation context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            print(f"❌ AI SQL generation with context failed: {e}")
            return None

    def _query_with_patterns(self, question: str) -> Dict[str, Any]:
        """Execute query using pattern matching"""
        try:
            # Parse and execute query
            sql, params = self.query_brain.parse_query(question)

            # Execute the query
            results = self.execute_query(sql, params)

            return {
                'success': True,
                'question': question,
                'results': results,
                'count': len(results),
                'sql': sql,
                'params': params,
                'method': 'pattern_matching'
            }

        except Exception as e:
            return {
                'success': False,
                'question': question,
                'error': str(e),
                'results': [],
                'method': 'pattern_matching'
            }

    def _generate_sql_with_ai(self, question: str) -> Optional[Dict[str, Any]]:
        """Use GPT-4o to generate SQL query from natural language"""

        # Get schema (lazy loaded and cached)
        schema = self._get_schema()

        # Get financial query hints if this looks like a financial question
        financial_hints = self._get_financial_query_hints(question)

        prompt = f"""You are a SQL expert for a design firm's operations database.

{schema}

IMPORTANT RULES:
1. ONLY use SELECT queries - no INSERT, UPDATE, DELETE, DROP
2. Use proper JOINs when needed
3. Limit results to 100 unless explicitly asked for more
4. Handle NULL values properly
5. Use LIKE for text searches with % wildcards
6. For date comparisons, use strftime or date() functions
7. Be careful with column names - check schema first

{financial_hints}

USER QUESTION: {question}

Generate a safe SQL query that answers this question.
Respond in JSON format:
{{
    "sql": "SELECT ... FROM ... WHERE ...",
    "reasoning": "Brief explanation of what the query does",
    "tables_used": ["table1", "table2"],
    "confidence": 85
}}

If the question is unclear or cannot be answered with available data, set sql to null.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a SQL expert that generates safe, efficient queries for a design firm's database."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            print(f"❌ AI SQL generation failed: {e}")
            return None

    def _execute_safe_query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute SQL query safely (SELECT only)"""

        # Security check: only allow SELECT queries
        sql_lower = sql.lower().strip()
        if not sql_lower.startswith('select'):
            raise ValueError("Only SELECT queries are allowed")

        # Block dangerous operations (use word boundary to avoid false positives like 'updated_at')
        dangerous_keywords = ['drop', 'delete', 'insert', 'update', 'alter', 'create', 'truncate']
        for keyword in dangerous_keywords:
            if re.search(rf'\b{keyword}\b', sql_lower):
                raise ValueError(f"Operation '{keyword}' is not allowed")

        # Execute query
        return self.execute_query(sql, [])

    def _generate_summary(self, question: str, results: List[Dict]) -> str:
        """Generate natural language summary of results"""

        if not results:
            return "No results found."

        # For small result sets, generate detailed summary
        if len(results) <= 5:
            summary_prompt = f"""Question: {question}

Results: {json.dumps(results, indent=2, default=str)}

Provide a concise natural language summary of these results in 1-2 sentences.
Focus on the key information that answers the user's question."""
        else:
            # For large result sets, just summarize count and first few
            summary_prompt = f"""Question: {question}

Found {len(results)} results. First 3:
{json.dumps(results[:3], indent=2, default=str)}

Provide a concise natural language summary in 1-2 sentences."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Cheaper model for simple task
                messages=[
                    {"role": "system", "content": "You summarize database query results in clear, concise language."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.3,
                max_tokens=100
            )

            return response.choices[0].message.content.strip()

        except Exception:
            return f"Found {len(results)} results."

    def get_query_suggestions(self) -> List[str]:
        """Get example query suggestions for users"""
        return [
            # Financial queries
            "Show financial breakdown for Wynn Marjan",
            "What's the total outstanding for all projects?",
            "Show invoices and payments for 22 BK-095",
            "Which projects have unpaid invoices?",
            "Show phase breakdown for Rosewood",
            # Project queries
            "Show me all proposals from 2024",
            "Find all documents for BK-069",
            "Which proposals have low health scores?",
            "Show me active projects",
            "Show proposals that need follow-up",
            # Email queries
            "Show me emails from this month",
            "What emails are unread?",
            # Contact queries
            "List all contacts",
            "Find proposals for hotel clients"
        ]

    def get_supported_query_types(self) -> List[Dict[str, Any]]:
        """Get information about supported query types"""
        return [
            {
                'type': 'financial',
                'description': 'Query financial data, invoices, payments, and fee breakdowns',
                'examples': [
                    'Show financial breakdown for Wynn Marjan',
                    'What invoices are outstanding?',
                    'Show phase breakdown for 22 BK-095',
                    'Total payments for Rosewood project',
                    'Which projects have unpaid invoices?'
                ],
                'filters': ['project_name', 'project_code', 'status', 'phase']
            },
            {
                'type': 'proposals',
                'description': 'Query proposals and projects',
                'examples': [
                    'Show me all proposals',
                    'Find active projects',
                    'Which proposals are from 2024?'
                ],
                'filters': ['year', 'status', 'project_code', 'active/pending/completed']
            },
            {
                'type': 'emails',
                'description': 'Query emails and communication',
                'examples': [
                    'Show me emails from this month',
                    'Find emails for BK-069',
                    'What are the unread emails?'
                ],
                'filters': ['date', 'project_code', 'month/week/today']
            },
            {
                'type': 'documents',
                'description': 'Query documents and files',
                'examples': [
                    'Find all documents for BK-069',
                    'Show me PDFs',
                    'What documents were modified this week?'
                ],
                'filters': ['project_code', 'file_type']
            },
            {
                'type': 'contacts',
                'description': 'Query contacts and people',
                'examples': [
                    'List all contacts',
                    'Find contacts for hotel projects'
                ],
                'filters': ['email_count', 'first_seen/last_seen']
            }
        ]

    # =========================================================================
    # PATTERN-ENHANCED QUERIES (Integration with AI Learning System)
    # =========================================================================

    def _load_query_patterns(self) -> List[Dict]:
        """Load learned patterns relevant to query processing"""
        try:
            patterns = self.execute_query("""
                SELECT
                    pattern_id, pattern_name, pattern_type,
                    condition, action, confidence_score
                FROM learned_patterns
                WHERE is_active = 1
                AND pattern_type IN ('query_enhancement', 'sql_template', 'table_preference', 'column_mapping')
                AND confidence_score >= 0.6
                ORDER BY confidence_score DESC
                LIMIT 20
            """, [])
            return patterns
        except Exception:
            return []

    def _get_query_hints_from_patterns(self, question: str) -> str:
        """Generate query hints based on learned patterns and historical feedback"""
        hints = []

        # Load active patterns
        patterns = self._load_query_patterns()

        for pattern in patterns:
            try:
                condition = json.loads(pattern.get('condition') or '{}')
                action = json.loads(pattern.get('action') or '{}')

                # Check if pattern applies to this question
                keywords = condition.get('keywords', [])
                if any(kw.lower() in question.lower() for kw in keywords):
                    hint = action.get('sql_hint') or action.get('hint')
                    if hint:
                        hints.append(f"- {hint}")
            except (json.JSONDecodeError, TypeError):
                continue

        # Add table relationship hints based on common corrections
        correction_hints = self._get_correction_hints()
        hints.extend(correction_hints)

        if hints:
            return "\n\nLEARNED HINTS (from previous corrections):\n" + "\n".join(hints)
        return ""

    def _get_correction_hints(self) -> List[str]:
        """Get hints from recent query corrections in training feedback"""
        try:
            corrections = self.execute_query("""
                SELECT
                    original_value, corrected_value, correction_reason
                FROM training_feedback
                WHERE feedback_type = 'query_correction'
                AND status = 'approved'
                ORDER BY created_at DESC
                LIMIT 10
            """, [])

            hints = []
            for c in corrections:
                reason = c.get('correction_reason')
                if reason:
                    hints.append(f"- {reason}")
            return hints
        except Exception:
            return []

    def query_with_patterns(self, question: str, use_ai: bool = True) -> Dict[str, Any]:
        """
        Execute a query enhanced with learned patterns.
        This method applies pattern-based intelligence before generating SQL.
        """
        if not use_ai or not self.ai_enabled:
            return self._query_with_patterns(question)

        try:
            # Get pattern-based hints
            pattern_hints = self._get_query_hints_from_patterns(question)

            # Generate enhanced SQL
            sql_result = self._generate_sql_with_patterns(question, pattern_hints)

            if not sql_result or not sql_result.get('sql'):
                return {
                    'success': False,
                    'question': question,
                    'error': 'Could not understand question',
                    'results': [],
                    'method': 'pattern_enhanced'
                }

            sql = sql_result['sql']
            results = self._execute_safe_query(sql)
            summary = self._generate_summary(question, results)

            # Log for training data
            self._log_successful_query(
                question=question,
                results=results,
                summary=summary,
                sql=sql,
                method='pattern_enhanced',
                confidence=sql_result.get('confidence')
            )

            return {
                'success': True,
                'question': question,
                'results': results,
                'count': len(results),
                'sql': sql,
                'summary': summary,
                'reasoning': sql_result.get('reasoning'),
                'confidence': sql_result.get('confidence'),
                'patterns_used': sql_result.get('patterns_used', []),
                'method': 'pattern_enhanced'
            }

        except Exception as e:
            return {
                'success': False,
                'question': question,
                'error': str(e),
                'results': [],
                'method': 'pattern_enhanced'
            }

    def _generate_sql_with_patterns(self, question: str, pattern_hints: str) -> Optional[Dict[str, Any]]:
        """Generate SQL using AI with pattern-based enhancements"""
        schema = self._get_schema()

        prompt = f"""You are a SQL expert for a design firm's operations database.

{schema}

{pattern_hints}

IMPORTANT RULES:
1. ONLY use SELECT queries - no INSERT, UPDATE, DELETE, DROP
2. Use proper JOINs when needed
3. Limit results to 100 unless explicitly asked for more
4. Handle NULL values properly
5. Use LIKE for text searches with % wildcards
6. For date comparisons, use strftime or date() functions
7. Be careful with column names - check schema first
8. Pay attention to the LEARNED HINTS - these come from corrections to past queries

USER QUESTION: {question}

Generate a safe SQL query that answers this question.
Respond in JSON format:
{{
    "sql": "SELECT ... FROM ... WHERE ...",
    "reasoning": "Brief explanation of what the query does",
    "tables_used": ["table1", "table2"],
    "confidence": 85,
    "patterns_used": ["list any hints that influenced your query"]
}}

If the question is unclear or cannot be answered with available data, set sql to null.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a SQL expert that learns from previous corrections."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            print(f"❌ Pattern-enhanced SQL generation failed: {e}")
            return None

    def record_query_feedback(
        self,
        question: str,
        original_sql: str,
        was_correct: bool,
        corrected_sql: Optional[str] = None,
        correction_reason: Optional[str] = None,
        user_id: str = "admin"
    ) -> Dict[str, Any]:
        """
        Record feedback on a query result for the learning system.
        This helps improve future query generation.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Insert feedback into training_feedback
                cursor.execute("""
                    INSERT INTO training_feedback (
                        email_id, field_name, original_value, corrected_value,
                        feedback_type, status, corrected_by, correction_reason,
                        created_at
                    ) VALUES (
                        NULL, 'sql_query', ?, ?,
                        'query_correction', 'pending', ?, ?,
                        datetime('now')
                    )
                """, [
                    json.dumps({'question': question, 'sql': original_sql}),
                    json.dumps({'question': question, 'sql': corrected_sql or original_sql}),
                    user_id,
                    correction_reason or ('correct' if was_correct else 'incorrect')
                ])

                feedback_id = cursor.lastrowid

                # If it was incorrect and we have a correction, create a pattern suggestion
                if not was_correct and corrected_sql and correction_reason:
                    self._suggest_query_pattern(
                        question, original_sql, corrected_sql, correction_reason
                    )

                conn.commit()

                return {
                    'success': True,
                    'feedback_id': feedback_id,
                    'message': 'Feedback recorded for learning'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _suggest_query_pattern(
        self,
        question: str,
        original_sql: str,
        corrected_sql: str,
        correction_reason: str
    ):
        """Create a pattern suggestion from a query correction"""
        try:
            # Extract keywords from the question
            keywords = [w for w in question.lower().split()
                       if len(w) > 3 and w not in ('show', 'find', 'what', 'which', 'list', 'from', 'with', 'that')]

            condition = {
                'keywords': keywords[:5],
                'original_pattern': original_sql[:100]
            }

            action = {
                'sql_hint': correction_reason,
                'corrected_pattern': corrected_sql[:200]
            }

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO learned_patterns (
                        pattern_name, pattern_type, condition, action,
                        confidence_score, evidence_count, is_active,
                        created_at, last_used_at
                    ) VALUES (
                        ?, 'query_enhancement', ?, ?,
                        0.5, 1, 0,
                        datetime('now'), datetime('now')
                    )
                """, [
                    f"Query correction: {correction_reason[:50]}",
                    json.dumps(condition),
                    json.dumps(action)
                ])
                conn.commit()
        except Exception:
            pass  # Non-critical, don't fail the main operation

    def get_intelligent_suggestions(self, partial_query: str = "") -> List[Dict[str, str]]:
        """
        Get intelligent query suggestions based on:
        1. Learned patterns
        2. Common queries
        3. Recent successful queries
        """
        suggestions = []

        # Get pattern-based suggestions
        pattern_suggestions = self._get_pattern_suggestions(partial_query)
        suggestions.extend(pattern_suggestions)

        # Get recent successful queries
        recent_suggestions = self._get_recent_query_suggestions(partial_query)
        suggestions.extend(recent_suggestions)

        # Add default suggestions if we don't have enough
        if len(suggestions) < 5:
            defaults = self.get_query_suggestions()
            for d in defaults:
                if len(suggestions) < 10 and d not in [s.get('query') for s in suggestions]:
                    suggestions.append({'query': d, 'source': 'default'})

        return suggestions[:10]

    def _get_pattern_suggestions(self, partial_query: str) -> List[Dict[str, str]]:
        """Get suggestions from learned patterns"""
        try:
            patterns = self.execute_query("""
                SELECT pattern_name, action
                FROM learned_patterns
                WHERE is_active = 1
                AND pattern_type = 'query_template'
                AND confidence_score >= 0.7
                ORDER BY evidence_count DESC
                LIMIT 5
            """, [])

            suggestions = []
            for p in patterns:
                try:
                    action = json.loads(p.get('action') or '{}')
                    example = action.get('example_query')
                    if example:
                        suggestions.append({
                            'query': example,
                            'source': 'learned_pattern',
                            'pattern': p.get('pattern_name')
                        })
                except (json.JSONDecodeError, TypeError):
                    continue
            return suggestions
        except Exception:
            return []

    def _get_recent_query_suggestions(self, partial_query: str) -> List[Dict[str, str]]:
        """Get suggestions from recent successful queries"""
        try:
            # Check if we have a query_history table
            tables = self.execute_query("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='query_history'
            """, [])

            if not tables:
                return []

            recent = self.execute_query("""
                SELECT DISTINCT question, success_count
                FROM query_history
                WHERE success_count > 0
                ORDER BY last_used DESC
                LIMIT 5
            """, [])

            return [
                {'query': r['question'], 'source': 'recent', 'success_count': r['success_count']}
                for r in recent
            ]
        except Exception:
            return []

    # =========================================================================
    # TRAINING DATA COLLECTION - For future model fine-tuning
    # =========================================================================

    def log_training_data(
        self,
        query: str,
        response: str,
        context_json: Optional[str] = None,
        model_used: str = "gpt-4o",
        confidence: float = None,
        task_type: str = "query"
    ) -> Optional[int]:
        """
        Log query/response pair for future model fine-tuning.

        Args:
            query: The user's natural language question
            response: The AI-generated response
            context_json: JSON string of context provided
            model_used: Model used for generation
            confidence: Confidence score if available
            task_type: Type of task (query, summarize, etc.)

        Returns:
            training_id if successful, None otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO training_data (
                        task_type,
                        input_data,
                        output_data,
                        model_used,
                        confidence,
                        context_json,
                        feature_type,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    task_type,
                    query,
                    response,
                    model_used,
                    confidence,
                    context_json,
                    "natural_language_query"
                ))

                training_id = cursor.lastrowid
                conn.commit()
                return training_id

        except Exception as e:
            print(f"❌ Error logging training data: {e}")
            return None

    def _log_successful_query(
        self,
        question: str,
        results: List[Dict],
        summary: str,
        sql: str,
        method: str,
        confidence: float = None
    ):
        """
        Log a successful query for training data.
        Called automatically after successful AI queries.
        """
        try:
            # Prepare context
            context = {
                "sql_generated": sql,
                "result_count": len(results),
                "method": method,
                "first_results": results[:3] if results else []
            }

            # Log to training_data
            self.log_training_data(
                query=question,
                response=summary or f"Found {len(results)} results",
                context_json=json.dumps(context, default=str),
                model_used="gpt-4o" if method in ["ai", "ai_with_context", "pattern_enhanced"] else "pattern_matching",
                confidence=confidence,
                task_type="query"
            )
        except Exception:
            pass  # Non-critical, don't fail the main operation

    def get_project_status_report(self, project_search: str) -> Dict[str, Any]:
        """
        Get comprehensive project status report with all financial details.

        This returns a structured report showing:
        - Project summary (total contract, invoiced, paid, outstanding, remaining)
        - Breakdown by scope (for multi-scope projects)
        - Phase breakdown within each scope
        - All invoices with details

        Args:
            project_search: Project code or partial name to search

        Returns:
            Structured report dict
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Find the project - split search terms to match any
                search_terms = project_search.split()
                if len(search_terms) > 1:
                    # Build dynamic query for multiple terms
                    conditions = []
                    params = []
                    for term in search_terms:
                        conditions.append("(project_code LIKE ? OR project_title LIKE ?)")
                        params.extend([f"%{term}%", f"%{term}%"])
                    where_clause = " AND ".join(conditions)
                    cursor.execute(f"""
                        SELECT project_id, project_code, project_title, total_fee_usd
                        FROM projects
                        WHERE {where_clause}
                        LIMIT 1
                    """, params)
                else:
                    cursor.execute("""
                        SELECT project_id, project_code, project_title, total_fee_usd
                        FROM projects
                        WHERE project_code LIKE ? OR project_title LIKE ?
                        LIMIT 1
                    """, [f"%{project_search}%", f"%{project_search}%"])

                project = cursor.fetchone()
                if not project:
                    return {'success': False, 'error': f'Project not found: {project_search}'}

                project_id = project['project_id']
                project_code = project['project_code']

                # Get summary totals
                cursor.execute("""
                    SELECT
                        COALESCE(SUM(invoice_amount), 0) as total_invoiced,
                        COALESCE(SUM(payment_amount), 0) as total_paid
                    FROM invoices WHERE project_id = ?
                """, [project_id])
                invoice_totals = cursor.fetchone()

                summary = {
                    'project_code': project_code,
                    'project_title': project['project_title'],
                    'total_contract': project['total_fee_usd'] or 0,
                    'total_invoiced': invoice_totals['total_invoiced'],
                    'total_paid': invoice_totals['total_paid'],
                    'outstanding': invoice_totals['total_invoiced'] - invoice_totals['total_paid'],
                    'remaining_to_invoice': (project['total_fee_usd'] or 0) - invoice_totals['total_invoiced']
                }

                # Get scope breakdown
                cursor.execute("""
                    SELECT
                        scope,
                        SUM(phase_fee_usd) as contract,
                        SUM(total_invoiced) as invoiced,
                        SUM(total_paid) as paid,
                        SUM(total_invoiced) - SUM(total_paid) as outstanding,
                        SUM(phase_fee_usd) - SUM(total_invoiced) as remaining
                    FROM project_fee_breakdown
                    WHERE project_code = ?
                    GROUP BY scope
                    ORDER BY
                        CASE scope
                            WHEN 'indian-brasserie' THEN 1
                            WHEN 'mediterranean-restaurant' THEN 2
                            WHEN 'day-club' THEN 3
                            WHEN 'night-club' THEN 4
                            WHEN 'additional-services' THEN 5
                            ELSE 6
                        END
                """, [project_code])

                scopes = []
                for row in cursor.fetchall():
                    scopes.append({
                        'scope': row['scope'],
                        'contract': row['contract'],
                        'invoiced': row['invoiced'],
                        'paid': row['paid'],
                        'outstanding': row['outstanding'],
                        'remaining': row['remaining']
                    })

                # Get phase breakdown for each scope
                phases_by_scope = {}
                cursor.execute("""
                    SELECT
                        scope,
                        phase,
                        phase_fee_usd as contract,
                        total_invoiced as invoiced,
                        total_paid as paid,
                        percentage_invoiced as pct_invoiced
                    FROM project_fee_breakdown
                    WHERE project_code = ?
                    ORDER BY scope,
                        CASE phase
                            WHEN 'Mobilization' THEN 1
                            WHEN 'Concept Design' THEN 2
                            WHEN 'Schematic Design' THEN 3
                            WHEN 'Design Development' THEN 4
                            WHEN 'Construction Documents' THEN 5
                            WHEN 'Construction Observation' THEN 6
                            ELSE 7
                        END
                """, [project_code])

                for row in cursor.fetchall():
                    scope = row['scope']
                    if scope not in phases_by_scope:
                        phases_by_scope[scope] = []
                    phases_by_scope[scope].append({
                        'phase': row['phase'],
                        'contract': row['contract'],
                        'invoiced': row['invoiced'],
                        'paid': row['paid'],
                        'pct_invoiced': row['pct_invoiced']
                    })

                # Get all invoices
                cursor.execute("""
                    SELECT
                        i.invoice_number,
                        i.invoice_date,
                        i.invoice_amount,
                        i.payment_amount,
                        i.payment_date,
                        i.status,
                        b.scope,
                        b.phase
                    FROM invoices i
                    LEFT JOIN project_fee_breakdown b ON i.breakdown_id = b.breakdown_id
                    WHERE i.project_id = ?
                    ORDER BY i.invoice_date, i.invoice_number, b.scope
                """, [project_id])

                invoices = []
                for row in cursor.fetchall():
                    invoices.append({
                        'invoice_number': row['invoice_number'],
                        'invoice_date': row['invoice_date'],
                        'amount': row['invoice_amount'],
                        'paid': row['payment_amount'],
                        'paid_date': row['payment_date'],
                        'status': row['status'],
                        'scope': row['scope'],
                        'phase': row['phase'],
                        'outstanding': (row['invoice_amount'] or 0) - (row['payment_amount'] or 0)
                    })

                return {
                    'success': True,
                    'summary': summary,
                    'scopes': scopes,
                    'phases_by_scope': phases_by_scope,
                    'invoices': invoices
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about query usage and learning (alias for get_query_stats)"""
        return self.get_query_stats()

    def get_query_stats(self) -> Dict[str, Any]:
        """Get statistics about query usage and learning"""
        try:
            stats = {}

            # Count learned patterns for queries
            pattern_count = self.execute_query("""
                SELECT COUNT(*) as count
                FROM learned_patterns
                WHERE pattern_type IN ('query_enhancement', 'sql_template', 'query_template')
                AND is_active = 1
            """, [])
            stats['active_patterns'] = pattern_count[0]['count'] if pattern_count else 0

            # Count query feedback
            feedback_count = self.execute_query("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN incorporated = 1 THEN 1 ELSE 0 END) as incorporated,
                    SUM(CASE WHEN corrected_value IS NOT NULL THEN 1 ELSE 0 END) as corrected
                FROM training_feedback
                WHERE feedback_type = 'query_correction'
            """, [])

            if feedback_count:
                stats['total_feedback'] = feedback_count[0]['total'] or 0
                stats['incorporated'] = feedback_count[0]['incorporated'] or 0
                stats['corrected_queries'] = feedback_count[0]['corrected'] or 0

            return stats

        except Exception as e:
            return {'error': str(e)}

    # =========================================================================
    # ENHANCED CONTEXT AGGREGATION - Unified project intelligence
    # =========================================================================

    def get_full_project_context(self, project_search: str, generate_summary: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive context for a project combining all data sources:
        - Project info and financials
        - Recent emails with key topics
        - Meeting transcripts and action items
        - RFIs (open and recent)
        - Invoices and payment status
        - AI-generated summary of current state

        Args:
            project_search: Project code or partial name
            generate_summary: Whether to generate AI summary (default True)

        Returns:
            Comprehensive context dict
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Find the project
                project = self._find_project(cursor, project_search)
                if not project:
                    return {'success': False, 'error': f'Project not found: {project_search}'}

                project_code = project['project_code']
                project_id = project['project_id']

                # Get recent emails (last 30 days)
                cursor.execute("""
                    SELECT e.email_id, e.subject, e.sender_email, e.sender_name,
                           e.date, e.snippet, ec.category
                    FROM emails e
                    JOIN email_project_links epl ON e.email_id = epl.email_id
                    LEFT JOIN email_content ec ON e.email_id = ec.email_id
                    WHERE epl.project_code = ?
                    AND e.date >= date('now', '-30 days')
                    ORDER BY e.date DESC
                    LIMIT 20
                """, (project_code,))
                recent_emails = [dict(row) for row in cursor.fetchall()]

                # Get meeting transcripts
                cursor.execute("""
                    SELECT id, audio_filename, summary, key_points, action_items,
                           participants, meeting_type, sentiment, recorded_date
                    FROM meeting_transcripts
                    WHERE detected_project_code = ?
                       OR detected_project_code LIKE ?
                    ORDER BY COALESCE(recorded_date, processed_date) DESC
                    LIMIT 10
                """, (project_code, f"%{project_code}%"))
                transcripts = [dict(row) for row in cursor.fetchall()]

                # Get meetings
                cursor.execute("""
                    SELECT meeting_id, title, meeting_type, meeting_date, status,
                           participants, notes, outcome
                    FROM meetings
                    WHERE project_code = ?
                    ORDER BY meeting_date DESC
                    LIMIT 10
                """, (project_code,))
                meetings = [dict(row) for row in cursor.fetchall()]

                # Get RFIs
                cursor.execute("""
                    SELECT rfi_id, rfi_number, subject, description, status,
                           priority, date_sent, date_due, date_responded, assigned_to
                    FROM rfis
                    WHERE project_code = ?
                    ORDER BY date_sent DESC
                """, (project_code,))
                rfis = [dict(row) for row in cursor.fetchall()]

                # Get action items
                cursor.execute("""
                    SELECT action_id, description, due_date, priority, status,
                           assigned_to, created_at
                    FROM action_items
                    WHERE project_id = ?
                    ORDER BY
                        CASE status WHEN 'open' THEN 1 ELSE 2 END,
                        due_date ASC
                """, (project_id,))
                action_items = [dict(row) for row in cursor.fetchall()]

                # Get invoice summary
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_invoices,
                        SUM(invoice_amount) as total_invoiced,
                        SUM(payment_amount) as total_paid,
                        SUM(invoice_amount) - SUM(COALESCE(payment_amount, 0)) as outstanding,
                        COUNT(CASE WHEN status IN ('sent', 'overdue', 'outstanding') THEN 1 END) as unpaid_count
                    FROM invoices
                    WHERE project_id = ?
                """, (project_id,))
                invoice_summary = dict(cursor.fetchone())

                # Build context
                context = {
                    'success': True,
                    'project': {
                        'project_code': project['project_code'],
                        'project_title': project['project_title'],
                        'status': project['status'],
                        'total_fee': project['total_fee_usd'],
                        'country': project.get('country'),
                        'city': project.get('city')
                    },
                    'emails': {
                        'count': len(recent_emails),
                        'recent': recent_emails[:10],
                        'key_senders': self._extract_key_senders(recent_emails)
                    },
                    'meetings': {
                        'count': len(meetings),
                        'recent': meetings[:5],
                        'transcripts': transcripts[:5]
                    },
                    'rfis': {
                        'total': len(rfis),
                        'open': [r for r in rfis if r['status'] == 'open'],
                        'recent': rfis[:5]
                    },
                    'action_items': {
                        'total': len(action_items),
                        'open': [a for a in action_items if a['status'] == 'open'],
                        'overdue': [a for a in action_items
                                   if a['status'] == 'open' and a.get('due_date')
                                   and a['due_date'] < datetime.now().strftime('%Y-%m-%d')]
                    },
                    'financials': invoice_summary
                }

                # Generate AI summary if requested
                if generate_summary and self.ai_enabled:
                    context['ai_summary'] = self._generate_project_summary(context)

                return context

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _find_project(self, cursor, project_search: str) -> Optional[Dict]:
        """Find a project by code or partial name"""
        search_terms = project_search.split()
        if len(search_terms) > 1:
            conditions = " AND ".join([f"project_title LIKE ?" for _ in search_terms])
            params = [f"%{term}%" for term in search_terms]
            cursor.execute(f"""
                SELECT project_id, project_code, project_title, status, total_fee_usd, country, city
                FROM projects
                WHERE ({conditions}) OR project_code LIKE ?
                LIMIT 1
            """, params + [f"%{project_search.replace(' ', '%')}%"])
        else:
            cursor.execute("""
                SELECT project_id, project_code, project_title, status, total_fee_usd, country, city
                FROM projects
                WHERE project_code = ? OR project_code LIKE ? OR project_title LIKE ?
                LIMIT 1
            """, (project_search, f"%{project_search}%", f"%{project_search}%"))
        row = cursor.fetchone()
        return dict(row) if row else None

    def _extract_key_senders(self, emails: List[Dict]) -> List[Dict]:
        """Extract key email senders with frequency"""
        sender_counts = {}
        for email in emails:
            sender = email.get('sender_email', '')
            name = email.get('sender_name', '')
            if sender:
                if sender not in sender_counts:
                    sender_counts[sender] = {'email': sender, 'name': name, 'count': 0}
                sender_counts[sender]['count'] += 1
        return sorted(sender_counts.values(), key=lambda x: -x['count'])[:5]

    def _generate_project_summary(self, context: Dict) -> str:
        """Generate AI summary of project state"""
        try:
            summary_prompt = f"""Summarize the current state of this project in 2-3 sentences:

Project: {context['project']['project_title']} ({context['project']['project_code']})
Status: {context['project']['status']}

Recent Activity:
- {context['emails']['count']} emails in last 30 days
- {context['meetings']['count']} meetings
- {len(context['rfis']['open'])} open RFIs
- {len(context['action_items']['open'])} open action items
- {len(context['action_items'].get('overdue', []))} overdue items

Financials:
- Total Fee: ${context['project'].get('total_fee') or 0:,.2f}
- Invoiced: ${context['financials'].get('total_invoiced') or 0:,.2f}
- Outstanding: ${context['financials'].get('outstanding') or 0:,.2f}

Focus on what needs attention and the overall project health."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You provide concise project status summaries for a design firm."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return "Summary generation failed."

    def get_project_timeline(self, project_search: str, limit: int = 50) -> Dict[str, Any]:
        """
        Get chronological timeline of all events for a project.
        Combines: emails, meetings, RFIs, invoices, action items.

        Args:
            project_search: Project code or partial name
            limit: Maximum events to return

        Returns:
            Timeline of events sorted by date
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                project = self._find_project(cursor, project_search)
                if not project:
                    return {'success': False, 'error': f'Project not found: {project_search}'}

                project_code = project['project_code']
                project_id = project['project_id']

                events = []

                # Emails
                cursor.execute("""
                    SELECT e.date as event_date, 'email' as event_type,
                           e.subject as title, e.sender_name as detail,
                           e.email_id as ref_id
                    FROM emails e
                    JOIN email_project_links epl ON e.email_id = epl.email_id
                    WHERE epl.project_code = ?
                    ORDER BY e.date DESC
                    LIMIT ?
                """, (project_code, limit))
                events.extend([dict(row) for row in cursor.fetchall()])

                # Meetings
                cursor.execute("""
                    SELECT meeting_date as event_date, 'meeting' as event_type,
                           title, meeting_type as detail, meeting_id as ref_id
                    FROM meetings
                    WHERE project_code = ?
                    ORDER BY meeting_date DESC
                    LIMIT ?
                """, (project_code, limit))
                events.extend([dict(row) for row in cursor.fetchall()])

                # RFIs
                cursor.execute("""
                    SELECT date_sent as event_date, 'rfi' as event_type,
                           subject as title,
                           'RFI #' || rfi_number || ' - ' || status as detail,
                           rfi_id as ref_id
                    FROM rfis
                    WHERE project_code = ?
                    ORDER BY date_sent DESC
                """, (project_code,))
                events.extend([dict(row) for row in cursor.fetchall()])

                # Invoices
                cursor.execute("""
                    SELECT invoice_date as event_date, 'invoice' as event_type,
                           'Invoice #' || invoice_number as title,
                           '$' || printf('%.2f', invoice_amount) || ' - ' || status as detail,
                           invoice_id as ref_id
                    FROM invoices
                    WHERE project_id = ?
                    ORDER BY invoice_date DESC
                """, (project_id,))
                events.extend([dict(row) for row in cursor.fetchall()])

                # Action Items
                cursor.execute("""
                    SELECT created_at as event_date, 'action_item' as event_type,
                           description as title,
                           priority || ' priority - ' || status as detail,
                           action_id as ref_id
                    FROM action_items
                    WHERE project_id = ?
                    ORDER BY created_at DESC
                """, (project_id,))
                events.extend([dict(row) for row in cursor.fetchall()])

                # Sort all events by date
                events.sort(key=lambda x: x.get('event_date') or '', reverse=True)
                events = events[:limit]

                return {
                    'success': True,
                    'project': project,
                    'timeline': events,
                    'count': len(events)
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_outstanding_items(self, project_search: str) -> Dict[str, Any]:
        """
        Get all outstanding/pending items for a project:
        - Open RFIs
        - Open action items (especially overdue)
        - Unpaid invoices

        Args:
            project_search: Project code or partial name

        Returns:
            All outstanding items needing attention
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                project = self._find_project(cursor, project_search)
                if not project:
                    return {'success': False, 'error': f'Project not found: {project_search}'}

                project_code = project['project_code']
                project_id = project['project_id']
                today = datetime.now().strftime('%Y-%m-%d')

                # Open RFIs
                cursor.execute("""
                    SELECT rfi_id, rfi_number, subject, priority, date_due,
                           assigned_to, date_sent,
                           CASE WHEN date_due < ? THEN 1 ELSE 0 END as is_overdue
                    FROM rfis
                    WHERE project_code = ? AND status = 'open'
                    ORDER BY
                        CASE WHEN date_due < ? THEN 0 ELSE 1 END,
                        date_due ASC
                """, (today, project_code, today))
                open_rfis = [dict(row) for row in cursor.fetchall()]

                # Open action items
                cursor.execute("""
                    SELECT action_id, description, priority, due_date, assigned_to,
                           CASE WHEN due_date < ? THEN 1 ELSE 0 END as is_overdue
                    FROM action_items
                    WHERE project_id = ? AND status = 'open'
                    ORDER BY
                        CASE WHEN due_date < ? THEN 0 ELSE 1 END,
                        due_date ASC
                """, (today, project_id, today))
                open_actions = [dict(row) for row in cursor.fetchall()]

                # Unpaid invoices
                cursor.execute("""
                    SELECT invoice_id, invoice_number, invoice_amount,
                           COALESCE(payment_amount, 0) as paid,
                           invoice_amount - COALESCE(payment_amount, 0) as outstanding,
                           invoice_date, due_date,
                           CASE WHEN due_date < ? THEN 1 ELSE 0 END as is_overdue
                    FROM invoices
                    WHERE project_id = ?
                      AND (status IN ('sent', 'overdue', 'outstanding') OR payment_amount < invoice_amount)
                    ORDER BY
                        CASE WHEN due_date < ? THEN 0 ELSE 1 END,
                        due_date ASC
                """, (today, project_id, today))
                unpaid_invoices = [dict(row) for row in cursor.fetchall()]

                # Calculate summary
                total_outstanding = sum(i['outstanding'] for i in unpaid_invoices)
                overdue_rfis = len([r for r in open_rfis if r['is_overdue']])
                overdue_actions = len([a for a in open_actions if a['is_overdue']])
                overdue_invoices = len([i for i in unpaid_invoices if i['is_overdue']])

                return {
                    'success': True,
                    'project': project,
                    'summary': {
                        'total_items': len(open_rfis) + len(open_actions) + len(unpaid_invoices),
                        'overdue_count': overdue_rfis + overdue_actions + overdue_invoices,
                        'outstanding_amount': total_outstanding
                    },
                    'rfis': {
                        'open': open_rfis,
                        'count': len(open_rfis),
                        'overdue': overdue_rfis
                    },
                    'action_items': {
                        'open': open_actions,
                        'count': len(open_actions),
                        'overdue': overdue_actions
                    },
                    'invoices': {
                        'unpaid': unpaid_invoices,
                        'count': len(unpaid_invoices),
                        'overdue': overdue_invoices,
                        'total_outstanding': total_outstanding
                    }
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def search_communications(
        self,
        topic: str,
        project_search: Optional[str] = None,
        sender: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search across emails and meeting transcripts for a topic.
        Answers questions like "What did [client] say about [topic]?"

        Args:
            topic: Topic to search for
            project_search: Optional project to filter by
            sender: Optional sender/participant to filter by
            limit: Maximum results to return

        Returns:
            Matching communications with context
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                results = {
                    'emails': [],
                    'meetings': []
                }

                # Build email query
                email_conditions = ["(e.subject LIKE ? OR e.snippet LIKE ? OR e.body_full LIKE ?)"]
                email_params = [f"%{topic}%", f"%{topic}%", f"%{topic}%"]

                if project_search:
                    project = self._find_project(cursor, project_search)
                    if project:
                        email_conditions.append("epl.project_code = ?")
                        email_params.append(project['project_code'])

                if sender:
                    email_conditions.append("(e.sender_email LIKE ? OR e.sender_name LIKE ?)")
                    email_params.extend([f"%{sender}%", f"%{sender}%"])

                email_sql = f"""
                    SELECT DISTINCT e.email_id, e.subject, e.sender_email, e.sender_name,
                           e.date, e.snippet, epl.project_code
                    FROM emails e
                    LEFT JOIN email_project_links epl ON e.email_id = epl.email_id
                    WHERE {' AND '.join(email_conditions)}
                    ORDER BY e.date DESC
                    LIMIT ?
                """
                cursor.execute(email_sql, email_params + [limit])
                results['emails'] = [dict(row) for row in cursor.fetchall()]

                # Build meeting transcript query
                meeting_conditions = ["(mt.transcript LIKE ? OR mt.summary LIKE ? OR mt.key_points LIKE ?)"]
                meeting_params = [f"%{topic}%", f"%{topic}%", f"%{topic}%"]

                if project_search and project:
                    meeting_conditions.append("(mt.detected_project_code = ? OR mt.detected_project_code LIKE ?)")
                    meeting_params.extend([project['project_code'], f"%{project['project_code']}%"])

                if sender:
                    meeting_conditions.append("mt.participants LIKE ?")
                    meeting_params.append(f"%{sender}%")

                meeting_sql = f"""
                    SELECT mt.id, mt.audio_filename, mt.summary, mt.key_points,
                           mt.detected_project_code, mt.recorded_date, mt.participants
                    FROM meeting_transcripts mt
                    WHERE {' AND '.join(meeting_conditions)}
                    ORDER BY mt.recorded_date DESC
                    LIMIT ?
                """
                cursor.execute(meeting_sql, meeting_params + [limit])
                results['meetings'] = [dict(row) for row in cursor.fetchall()]

                # Also search scheduled meetings notes
                cursor.execute("""
                    SELECT meeting_id, title, meeting_date, notes, outcome, participants
                    FROM meetings
                    WHERE (notes LIKE ? OR outcome LIKE ? OR title LIKE ?)
                    ORDER BY meeting_date DESC
                    LIMIT ?
                """, (f"%{topic}%", f"%{topic}%", f"%{topic}%", limit))
                results['scheduled_meetings'] = [dict(row) for row in cursor.fetchall()]

                # Generate AI summary if we have results
                if self.ai_enabled and (results['emails'] or results['meetings']):
                    results['ai_summary'] = self._summarize_search_results(topic, results)

                return {
                    'success': True,
                    'topic': topic,
                    'total_results': len(results['emails']) + len(results['meetings']),
                    'results': results
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _summarize_search_results(self, topic: str, results: Dict) -> str:
        """Summarize search results with AI"""
        try:
            context = f"Topic searched: {topic}\n\n"

            if results['emails']:
                context += "Emails found:\n"
                for e in results['emails'][:5]:
                    context += f"- [{e.get('date', 'N/A')}] {e.get('subject', '')} (from {e.get('sender_name', e.get('sender_email', 'unknown'))})\n"

            if results['meetings']:
                context += "\nMeeting transcripts found:\n"
                for m in results['meetings'][:3]:
                    context += f"- [{m.get('recorded_date', 'N/A')}] {m.get('summary', 'No summary')[:100]}...\n"

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Summarize what was discussed about the topic based on the search results."},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return f"Found {len(results['emails'])} emails and {len(results['meetings'])} meeting transcripts mentioning '{topic}'."

    def get_pre_meeting_briefing(self, project_search: str) -> Dict[str, Any]:
        """
        Generate pre-meeting briefing for a project.

        Includes:
        - Project overview and current status
        - Last meeting notes and outcomes
        - Recent correspondence summary
        - Open issues (RFIs, action items)
        - Financial status
        - Key contacts

        Args:
            project_search: Project code or partial name

        Returns:
            Comprehensive briefing document
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                project = self._find_project(cursor, project_search)
                if not project:
                    return {'success': False, 'error': f'Project not found: {project_search}'}

                project_code = project['project_code']
                project_id = project['project_id']

                # Get client info
                cursor.execute("""
                    SELECT c.company_name, c.country
                    FROM clients c
                    JOIN projects p ON p.client_id = c.client_id
                    WHERE p.project_id = ?
                """, (project_id,))
                client_row = cursor.fetchone()
                client_info = dict(client_row) if client_row else {}

                # Get last meeting
                cursor.execute("""
                    SELECT title, meeting_date, meeting_type, notes, outcome, participants
                    FROM meetings
                    WHERE project_code = ? AND status = 'completed'
                    ORDER BY meeting_date DESC
                    LIMIT 1
                """, (project_code,))
                last_meeting = cursor.fetchone()
                last_meeting = dict(last_meeting) if last_meeting else None

                # Get last transcript
                cursor.execute("""
                    SELECT summary, key_points, action_items, recorded_date
                    FROM meeting_transcripts
                    WHERE detected_project_code = ? OR detected_project_code LIKE ?
                    ORDER BY COALESCE(recorded_date, processed_date) DESC
                    LIMIT 1
                """, (project_code, f"%{project_code}%"))
                last_transcript = cursor.fetchone()
                last_transcript = dict(last_transcript) if last_transcript else None

                # Get recent emails (last 14 days)
                cursor.execute("""
                    SELECT e.subject, e.sender_name, e.sender_email, e.date, e.snippet
                    FROM emails e
                    JOIN email_project_links epl ON e.email_id = epl.email_id
                    WHERE epl.project_code = ?
                    AND e.date >= date('now', '-14 days')
                    ORDER BY e.date DESC
                    LIMIT 10
                """, (project_code,))
                recent_emails = [dict(row) for row in cursor.fetchall()]

                # Get open issues
                outstanding = self.get_outstanding_items(project_code)

                # Get fee breakdown
                cursor.execute("""
                    SELECT scope, phase, phase_fee_usd, total_invoiced, total_paid
                    FROM project_fee_breakdown
                    WHERE project_code = ?
                    ORDER BY scope, phase
                """, (project_code,))
                fee_breakdown = [dict(row) for row in cursor.fetchall()]

                # Get key contacts (join with clients for company name)
                cursor.execute("""
                    SELECT DISTINCT c.name, c.email, cl.company_name as company, c.role
                    FROM contacts c
                    LEFT JOIN clients cl ON c.client_id = cl.client_id
                    JOIN emails e ON c.email = e.sender_email
                    JOIN email_project_links epl ON e.email_id = epl.email_id
                    WHERE epl.project_code = ?
                    ORDER BY c.name
                    LIMIT 10
                """, (project_code,))
                key_contacts = [dict(row) for row in cursor.fetchall()]

                briefing = {
                    'success': True,
                    'generated_at': datetime.now().isoformat(),
                    'project': {
                        **project,
                        'client': client_info
                    },
                    'last_meeting': last_meeting,
                    'last_transcript': last_transcript,
                    'recent_correspondence': {
                        'count': len(recent_emails),
                        'emails': recent_emails
                    },
                    'open_issues': outstanding.get('summary', {}) if outstanding.get('success') else {},
                    'open_rfis': outstanding.get('rfis', {}).get('open', []) if outstanding.get('success') else [],
                    'open_action_items': outstanding.get('action_items', {}).get('open', []) if outstanding.get('success') else [],
                    'financials': {
                        'total_fee': project.get('total_fee_usd'),
                        'breakdown': fee_breakdown,
                        'unpaid_invoices': outstanding.get('invoices', {}).get('unpaid', []) if outstanding.get('success') else []
                    },
                    'key_contacts': key_contacts
                }

                # Generate AI briefing summary
                if self.ai_enabled:
                    briefing['ai_briefing'] = self._generate_briefing_summary(briefing)

                return briefing

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _generate_briefing_summary(self, briefing: Dict) -> str:
        """Generate AI-powered briefing summary"""
        try:
            project = briefing['project']
            context = f"""Generate a concise pre-meeting briefing for: {project['project_title']}

Project Status: {project.get('status', 'Unknown')}
Total Fee: ${project.get('total_fee_usd') or 0:,.2f}

Last Meeting: {briefing['last_meeting']['meeting_date'] if briefing['last_meeting'] else 'None recorded'}
{briefing['last_meeting']['outcome'] if briefing['last_meeting'] and briefing['last_meeting'].get('outcome') else 'No outcome recorded'}

Open Issues:
- {briefing['open_issues'].get('total_items', 0)} open items
- {briefing['open_issues'].get('overdue_count', 0)} overdue
- ${briefing['open_issues'].get('outstanding_amount', 0):,.2f} outstanding payments

Recent Activity: {briefing['recent_correspondence']['count']} emails in last 14 days

Provide a 3-4 sentence briefing summary covering:
1. Current project phase/status
2. Key items to discuss
3. Any concerns or overdue items"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You create concise pre-meeting briefings for design project managers."},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return "Briefing summary generation failed."
