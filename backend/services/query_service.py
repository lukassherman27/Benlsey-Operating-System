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

# Add project root to path to import query_brain
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

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
