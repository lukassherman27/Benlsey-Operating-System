"""
Query Service - AI-Powered Natural Language Queries

Enhanced with GPT-4o for true natural language understanding.
Falls back to pattern matching if AI is not available.
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
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

    def query(self, question: str, use_ai: bool = True) -> Dict[str, Any]:
        """
        Execute a natural language query with AI or pattern matching

        Args:
            question: Natural language question
            use_ai: Whether to use AI (True) or pattern matching (False)

        Returns:
            Dict with query results and metadata
        """
        # Use AI if enabled and requested
        if use_ai and self.ai_enabled:
            return self._query_with_ai(question)

        # Fall back to pattern matching
        return self._query_with_patterns(question)

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

        # Block dangerous operations
        dangerous_keywords = ['drop', 'delete', 'insert', 'update', 'alter', 'create', 'truncate']
        for keyword in dangerous_keywords:
            if keyword in sql_lower:
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
            "Show me all proposals from 2024",
            "Find all documents for BK-069",
            "Which proposals have low health scores?",
            "Show me emails from this month",
            "List all contacts",
            "Find proposals for hotel clients",
            "Show me active projects",
            "What emails are unread?",
            "Find all contracts",
            "Show proposals that need follow-up"
        ]

    def get_supported_query_types(self) -> List[Dict[str, Any]]:
        """Get information about supported query types"""
        return [
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
                    SUM(CASE WHEN correction_reason = 'correct' THEN 1 ELSE 0 END) as correct,
                    SUM(CASE WHEN correction_reason != 'correct' THEN 1 ELSE 0 END) as corrected
                FROM training_feedback
                WHERE feedback_type = 'query_correction'
            """, [])

            if feedback_count:
                stats['total_feedback'] = feedback_count[0]['total'] or 0
                stats['correct_queries'] = feedback_count[0]['correct'] or 0
                stats['corrected_queries'] = feedback_count[0]['corrected'] or 0
                total = stats['total_feedback']
                if total > 0:
                    stats['accuracy_rate'] = round(stats['correct_queries'] / total, 2)

            return stats

        except Exception as e:
            return {'error': str(e)}
