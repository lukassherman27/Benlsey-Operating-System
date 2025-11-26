#!/usr/bin/env python3
"""
Local Model Inference - Drop-in Replacement for Claude API
Uses Ollama for running local models with business context
"""

import json
import requests
import sqlite3
from typing import Dict, Optional
import os

# Configuration
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.environ.get("LOCAL_MODEL", "bensley-email-assistant")
FALLBACK_MODEL = "mistral"  # If custom model not available

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
SYSTEM_PROMPT_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/LOCAL_MODELS/system_prompt.txt"

class LocalModelService:
    """
    Local model service - compatible with existing AIService interface
    Can replace Claude API calls with local inference
    """

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self.ollama_url = OLLAMA_URL
        self.system_prompt = self._load_system_prompt()

        # Test connection
        if not self._test_connection():
            print("⚠️  Warning: Ollama not running. Start with: ollama serve")
            print("   Falling back to basic model...")
            self.model_name = FALLBACK_MODEL

    def _load_system_prompt(self) -> str:
        """Load system prompt with business context"""
        if os.path.exists(SYSTEM_PROMPT_PATH):
            with open(SYSTEM_PROMPT_PATH, 'r') as f:
                return f.read()

        # Fallback system prompt
        return """You are an email assistant for Bensley Design Studios.
Categorize emails and extract key information.
Return JSON format with category, subcategory, importance_score, and summary."""

    def _test_connection(self) -> bool:
        """Test if Ollama is running"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    def _call_ollama(self, prompt: str, temperature: float = 0.1) -> str:
        """Call Ollama API"""
        try:
            response = requests.post(self.ollama_url, json={
                "model": self.model_name,
                "prompt": prompt,
                "system": self.system_prompt,
                "temperature": temperature,
                "stream": False
            }, timeout=30)

            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                return None

        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return None

    def categorize_email(self, subject: str, sender: str, body_preview: str) -> Dict:
        """
        Categorize email - drop-in replacement for AIService.categorize_email()

        Args:
            subject: Email subject
            sender: Sender email
            body_preview: First 500 chars of email body

        Returns:
            Dict with category, subcategory, importance_score, summary
        """
        prompt = f"""Categorize this email:

Subject: {subject}
From: {sender}
Preview: {body_preview[:500]}

Return JSON only, no other text."""

        response = self._call_ollama(prompt)

        if not response:
            # Fallback to default
            return {
                "category": "general",
                "subcategory": None,
                "importance_score": 0.5,
                "summary": "Unable to process email",
                "error": "Model unavailable"
            }

        # Parse JSON response
        try:
            # Try to extract JSON from response
            result = json.loads(response)
            return {
                "category": result.get("category", "general"),
                "subcategory": result.get("subcategory"),
                "importance_score": float(result.get("importance_score", 0.5)),
                "summary": result.get("summary", ""),
                "project_code": result.get("project_code"),
                "people_mentioned": result.get("people_mentioned", []),
                "action_required": result.get("action_required", False)
            }
        except json.JSONDecodeError:
            # Model didn't return valid JSON, parse text response
            return {
                "category": "general",
                "subcategory": None,
                "importance_score": 0.5,
                "summary": response[:200],
                "error": "Invalid JSON response"
            }

    def summarize_email(self, subject: str, body: str) -> str:
        """
        Summarize email content

        Args:
            subject: Email subject
            body: Full email body

        Returns:
            2-3 sentence summary
        """
        prompt = f"""Summarize this email concisely (2-3 sentences):

Subject: {subject}

Body:
{body[:1000]}

Focus on: Who sent it, what they want, urgency, recommended action."""

        response = self._call_ollama(prompt, temperature=0.3)
        return response if response else "Unable to generate summary"

    def extract_project_code(self, text: str) -> Optional[str]:
        """
        Extract Bensley project code from text (format: XXX-XX-XX)

        Args:
            text: Email subject or body

        Returns:
            Project code if found, None otherwise
        """
        prompt = f"""Extract the Bensley project code from this text.
Format: XXX-XX-XX (e.g., MAL-24-02, THA-23-15)

Text: {text[:500]}

Return ONLY the project code, nothing else. If no code found, return "NONE"."""

        response = self._call_ollama(prompt, temperature=0.0)

        if response and response.strip() != "NONE":
            code = response.strip()
            # Validate format
            if len(code) >= 8 and '-' in code:
                return code

        return None

    def match_to_proposal(self, email_id: int, subject: str, body: str) -> Optional[int]:
        """
        Match email to proposal using AI

        Args:
            email_id: Email ID
            subject: Email subject
            body: Email body preview

        Returns:
            Proposal ID if matched, None otherwise
        """
        # Get active proposals from database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT proposal_id, project_code, project_name, client_company
            FROM proposals
            WHERE is_active_project = 1
            ORDER BY project_code
        """)
        proposals = cursor.fetchall()
        conn.close()

        if not proposals:
            return None

        # Format proposals for model
        proposals_text = "\n".join([
            f"- {p[1]}: {p[2]} ({p[3]})" for p in proposals[:20]
        ])

        prompt = f"""Match this email to a project:

Email Subject: {subject}
Email Preview: {body[:300]}

Active Projects:
{proposals_text}

Return ONLY the project code (e.g., MAL-24-02) that this email relates to.
If no match, return "NONE"."""

        response = self._call_ollama(prompt, temperature=0.0)

        if response and response.strip() != "NONE":
            # Find proposal ID by project code
            for proposal in proposals:
                if response.strip() in proposal[1]:  # Match project code
                    return proposal[0]

        return None


def test_local_model():
    """Test local model with sample emails"""
    print("="*80)
    print("TESTING LOCAL MODEL INFERENCE")
    print("="*80)

    service = LocalModelService()

    # Test 1: Categorization
    print("\n1. Testing Email Categorization...")
    print("-"*80)

    test_email = {
        "subject": "Re: Fee proposal for MAL-24-02 - Maldives Resort",
        "sender": "client@luxuryhotels.com",
        "body": "Thanks for the proposal. The $2.5M fee is acceptable. Can we schedule a call next week to discuss the design timeline? We're hoping to break ground in Q2."
    }

    print(f"Subject: {test_email['subject']}")
    print(f"From: {test_email['sender']}")

    result = service.categorize_email(
        test_email['subject'],
        test_email['sender'],
        test_email['body']
    )

    print("\nResult:")
    print(json.dumps(result, indent=2))

    # Test 2: Project code extraction
    print("\n2. Testing Project Code Extraction...")
    print("-"*80)

    code = service.extract_project_code(test_email['subject'])
    print(f"Extracted code: {code}")

    # Test 3: Summarization
    print("\n3. Testing Summarization...")
    print("-"*80)

    summary = service.summarize_email(test_email['subject'], test_email['body'])
    print(f"Summary: {summary}")

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)


def batch_process_emails(limit: int = 10):
    """
    Process uncategorized emails with local model
    Demonstrates integration with database
    """
    print("="*80)
    print(f"BATCH PROCESSING {limit} EMAILS WITH LOCAL MODEL")
    print("="*80)

    service = LocalModelService()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get uncategorized emails
    cursor.execute("""
        SELECT e.email_id, e.subject, e.sender_email, e.body_preview
        FROM emails e
        LEFT JOIN email_content ec ON e.email_id = ec.email_id
        WHERE ec.category IS NULL
        LIMIT ?
    """, (limit,))

    emails = cursor.fetchall()

    if not emails:
        print("\n✓ All emails are categorized!")
        conn.close()
        return

    print(f"\nProcessing {len(emails)} uncategorized emails...\n")

    processed = 0
    for email_id, subject, sender, body in emails:
        print(f"[{processed+1}/{len(emails)}] {subject[:50]}...")

        # Categorize with local model
        result = service.categorize_email(subject, sender, body or "")

        # Save to database
        cursor.execute("""
            INSERT OR REPLACE INTO email_content
            (email_id, category, subcategory, importance_score, ai_summary, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (
            email_id,
            result['category'],
            result.get('subcategory'),
            result['importance_score'],
            result.get('summary', '')
        ))

        processed += 1

        if processed % 5 == 0:
            conn.commit()

    conn.commit()
    conn.close()

    print(f"\n✓ Processed {processed} emails with local model")
    print("="*80)


def compare_with_claude():
    """
    Compare local model vs Claude API results
    Useful for evaluating model accuracy
    """
    print("="*80)
    print("LOCAL MODEL vs CLAUDE API COMPARISON")
    print("="*80)
    print("\nThis compares existing Claude categorizations with local model.\n")

    service = LocalModelService()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get emails categorized by Claude
    cursor.execute("""
        SELECT e.email_id, e.subject, e.sender_email, e.body_preview,
               ec.category, ec.subcategory, ec.importance_score
        FROM emails e
        JOIN email_content ec ON e.email_id = ec.email_id
        WHERE ec.category IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 10
    """)

    emails = cursor.fetchall()
    conn.close()

    matches = 0
    total = len(emails)

    for email_id, subject, sender, body, claude_cat, claude_sub, claude_score in emails:
        # Get local model prediction
        local_result = service.categorize_email(subject, sender, body or "")

        match = (local_result['category'] == claude_cat)
        matches += match

        print(f"\nSubject: {subject[:60]}")
        print(f"Claude:  {claude_cat}/{claude_sub or 'none'} ({claude_score:.2f})")
        print(f"Local:   {local_result['category']}/{local_result.get('subcategory') or 'none'} ({local_result['importance_score']:.2f})")
        print(f"Match:   {'✓' if match else '✗'}")

    accuracy = (matches / total) * 100
    print("\n" + "="*80)
    print(f"ACCURACY: {accuracy:.1f}% ({matches}/{total} matches)")
    print("="*80)

    if accuracy < 70:
        print("\n⚠️  Low accuracy. Recommendations:")
        print("1. Add more human-verified training examples")
        print("2. Re-train the model with better data")
        print("3. Adjust the system prompt for better context")
    elif accuracy >= 90:
        print("\n✓ Excellent accuracy! Model is ready for production.")
    else:
        print("\n✓ Good accuracy. Add more training data to improve further.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 local_model_inference.py test          # Test model")
        print("  python3 local_model_inference.py process [N]   # Process N emails")
        print("  python3 local_model_inference.py compare       # Compare with Claude")
        sys.exit(1)

    command = sys.argv[1]

    if command == "test":
        test_local_model()
    elif command == "process":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        batch_process_emails(limit)
    elif command == "compare":
        compare_with_claude()
    else:
        print(f"Unknown command: {command}")
