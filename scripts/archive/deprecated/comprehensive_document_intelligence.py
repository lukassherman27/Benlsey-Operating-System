#!/usr/bin/env python3
"""
COMPREHENSIVE DOCUMENT INTELLIGENCE SYSTEM

Processes ALL documents (contracts, invoices, proposals, etc.) and extracts:
- Document type classification
- Key data: scope, terms, fees, payment dates, milestones
- Cross-references with database
- Suggests database migrations and fixes

Budget: $20-50 for processing ~850 documents
Cost per doc: ~$0.02-0.05 = $17-42 total
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from openai import OpenAI
import PyPDF2
import io

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


class DocumentIntelligence:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY required")

        self.client = OpenAI(api_key=api_key)
        self.processed_count = 0
        self.total_cost = 0.0

    def extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages[:10]:  # First 10 pages max
                    text += page.extract_text()
                return text[:15000]  # Limit to ~15k chars
        except Exception as e:
            print(f"   ⚠️  PDF extraction failed: {e}")
            return ""

    def analyze_document(self, doc_id: int, file_path: str, filename: str, text_content: str = None) -> Optional[Dict]:
        """
        Use AI to deeply analyze document and extract ALL relevant data
        """

        # Use existing text_content if available, otherwise extract from PDF
        if text_content and len(text_content) > 100:
            text = text_content[:15000]  # Limit to 15k chars
        else:
            text = self.extract_pdf_text(file_path)

        if not text or len(text) < 100:
            print(f"   ⚠️  Insufficient text (len={len(text)})")
            return None

        # Get any project context for this document
        self.cursor.execute("""
            SELECT p.project_code, p.project_name, p.client_company, p.project_value
            FROM document_proposal_links dpl
            JOIN projects p ON dpl.proposal_id = p.proposal_id
            WHERE dpl.document_id = ?
            LIMIT 1
        """, (doc_id,))

        project = self.cursor.fetchone()
        project_context = ""
        if project:
            project_context = f"""
LINKED PROJECT:
- Code: {project['project_code']}
- Name: {project['project_name']}
- Client: {project['client_company']}
- Value: ${project['project_value'] or 0:,.0f}
"""

        prompt = f"""You are analyzing a business document to extract ALL relevant data.

FILENAME: {filename}

{project_context}

DOCUMENT TEXT (first 15k chars):
{text}

ANALYZE THIS DOCUMENT COMPREHENSIVELY:

1. CLASSIFICATION:
   - What type of document is this? (contract, invoice, proposal, NDA, schedule, amendment, etc.)
   - Confidence level in classification

2. KEY PARTIES:
   - Client/customer name and details
   - Vendor/service provider
   - Any other relevant parties

3. FINANCIAL INFORMATION:
   - Total contract value / invoice amount
   - Payment terms and schedule
   - Breakdown of fees (design fees, FF&E, etc.)
   - Currency
   - Any milestones tied to payments

4. PROJECT SCOPE (if applicable):
   - What services/deliverables are included?
   - Exclusions
   - Timeline and deadlines
   - Key milestones

5. DATES:
   - Contract date / invoice date
   - Start and end dates
   - Payment due dates
   - Any important deadlines

6. TERMS & CONDITIONS:
   - Payment terms (e.g., "Net 30")
   - Termination clauses
   - Ownership/IP rights
   - Liability limits
   - Any special conditions

7. STATUS INDICATORS:
   - Is this executed/signed?
   - Any pending items?
   - Version or amendment number

8. DATABASE MAPPING:
   - Which project_code should this link to? (if you can identify from content)
   - What data should be updated in the database?
   - Any data quality issues or conflicts with existing data?

Return detailed JSON:
{{
    "classification": {{
        "document_type": "contract|invoice|proposal|nda|schedule|amendment|other",
        "sub_type": "design_services|construction|ff&e|etc",
        "confidence": 0.95
    }},
    "parties": {{
        "client": "Company name",
        "vendor": "Bensley Design Studios",
        "other_parties": []
    }},
    "financials": {{
        "total_value": 250000.00,
        "currency": "USD",
        "payment_schedule": [
            {{"milestone": "Contract signing", "amount": 50000, "due_date": "2024-01-15"}},
            {{"milestone": "Concept approval", "amount": 100000, "due_date": "2024-03-01"}}
        ],
        "fee_breakdown": {{
            "design_fees": 200000,
            "ff_e": 50000,
            "reimbursables": 0
        }}
    }},
    "scope": {{
        "deliverables": ["Schematic design", "Design development", "Construction documents"],
        "exclusions": ["Construction management", "FF&E procurement"],
        "timeline": "6 months from contract signing",
        "square_footage": null,
        "number_of_rooms": null
    }},
    "dates": {{
        "contract_date": "2024-01-10",
        "start_date": "2024-01-15",
        "end_date": "2024-07-15",
        "payment_due_dates": ["2024-01-15", "2024-03-01", "2024-05-01"]
    }},
    "terms": {{
        "payment_terms": "Net 30 days from invoice date",
        "termination": "Either party may terminate with 30 days notice",
        "ip_ownership": "Client owns all deliverables upon final payment",
        "liability_limit": 250000,
        "special_conditions": []
    }},
    "status": {{
        "executed": true,
        "version": "1.0",
        "amendments": []
    }},
    "database_recommendations": {{
        "project_code": "BK-052",
        "suggested_updates": [
            {{"table": "projects", "field": "project_value", "current": 0, "suggested": 250000, "confidence": 0.95}},
            {{"table": "contract_terms", "action": "insert", "data": {{}}}},
            {{"table": "payment_milestones", "action": "insert", "data": {{}}}}
        ],
        "data_quality_issues": [
            "Project value in database (0) doesn't match contract ($250k)"
        ]
    }},
    "summary": "Brief 2-3 sentence summary of this document and its significance"
}}

Be thorough but accurate. If information isn't in the document, use null.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use GPT-4o for complex extraction
                messages=[
                    {"role": "system", "content": "You are a document analysis AI that extracts comprehensive structured data from business documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temp for accuracy
                response_format={"type": "json_object"}
            )

            analysis = json.loads(response.choices[0].message.content)

            # Estimate cost (rough)
            input_tokens = len(prompt) // 4
            output_tokens = len(response.choices[0].message.content) // 4
            cost = (input_tokens * 0.0000025) + (output_tokens * 0.00001)
            self.total_cost += cost

            return analysis

        except Exception as e:
            print(f"   ⚠️  AI analysis failed: {e}")
            return None

    def process_document(self, doc_id: int):
        """Process a single document"""

        # Get document details
        self.cursor.execute("SELECT * FROM documents WHERE document_id = ?", (doc_id,))
        doc = self.cursor.fetchone()

        if not doc:
            return

        file_path = doc['file_path']
        filename = doc['file_name']
        text_content = doc['text_content'] if doc['text_content'] else ''

        print(f"\n📄 [{self.processed_count + 1}] {filename[:60]}...")

        # AI analysis (use existing text_content if available)
        analysis = self.analyze_document(doc_id, file_path, filename, text_content)

        if not analysis:
            print(f"   ❌ Analysis failed")
            return

        doc_type = analysis['classification']['document_type']
        confidence = analysis['classification']['confidence']

        print(f"   📊 Type: {doc_type} ({confidence*100:.0f}% confidence)")

        total_value = analysis['financials'].get('total_value', 0)
        if total_value and total_value != 0:
            print(f"   💰 Value: ${total_value:,.0f} {analysis['financials'].get('currency', 'USD')}")

        if analysis.get('summary'):
            print(f"   📝 {analysis['summary'][:100]}...")

        # Update database
        self._update_document_metadata(doc_id, analysis)

        # Apply database recommendations
        if analysis.get('database_recommendations'):
            self._apply_recommendations(doc_id, analysis['database_recommendations'])

        self.processed_count += 1

        if self.processed_count % 10 == 0:
            print(f"\n💰 Estimated cost so far: ${self.total_cost:.2f}")

    def _update_document_metadata(self, doc_id: int, analysis: Dict):
        """Update document table with extracted metadata"""

        doc_type = analysis['classification']['document_type']

        # Extract data from analysis
        financials = analysis.get('financials', {})
        scope = analysis.get('scope', {})

        # Convert lists/objects to strings for database
        deliverables = scope.get('deliverables', [])
        if isinstance(deliverables, list):
            deliverables_text = ', '.join(deliverables) if deliverables else ''
        else:
            deliverables_text = str(deliverables)

        # Store structured data in document_intelligence table
        self.cursor.execute("""
            INSERT OR REPLACE INTO document_intelligence (
                document_id, fee_amount, fee_currency, scope_summary,
                timeline, key_deliverables, special_terms,
                executive_summary, model_used, confidence_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_id,
            str(financials.get('total_value', '')) if financials.get('total_value') else '',
            str(financials.get('currency', '')),
            deliverables_text,
            str(scope.get('timeline', '')),
            json.dumps(scope.get('deliverables', [])),
            json.dumps(analysis.get('terms', {})),
            str(analysis.get('summary', '')),
            'gpt-4o',
            float(analysis['classification']['confidence'])
        ))

        # Update documents table with type and project code
        project_code = analysis.get('database_recommendations', {}).get('project_code')

        self.cursor.execute("""
            UPDATE documents
            SET document_type = ?,
                project_code = ?,
                modified_date = datetime('now')
            WHERE document_id = ?
        """, (doc_type, project_code, doc_id))

        self.conn.commit()

    def _apply_recommendations(self, doc_id: int, recommendations: Dict):
        """Apply database recommendations from AI analysis"""

        # For now, create suggestions for human review
        # Later can auto-apply high-confidence recommendations

        for update in recommendations.get('suggested_updates', []):
            if update.get('confidence', 0) < 0.9:
                # Low confidence - create suggestion for review
                import uuid
                suggestion_id = str(uuid.uuid4())

                self.cursor.execute("""
                    INSERT INTO ai_suggestions_queue (
                        id, project_code, suggestion_type, proposed_fix, evidence,
                        confidence, impact_type, impact_summary,
                        severity, bucket, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
                """, (
                    suggestion_id,
                    recommendations.get('project_code', 'SYSTEM'),
                    'document_data_extraction',
                    json.dumps(update),
                    json.dumps({'document_id': doc_id}),
                    update.get('confidence', 0.5),
                    'data_quality',
                    f"Document analysis suggests updating {update.get('table')}.{update.get('field')}",
                    'medium',
                    'needs_attention'
                ))

        self.conn.commit()

    def process_all_documents(self, limit: int = None):
        """Process all uncategorized documents"""

        print("=" * 80)
        print("📚 COMPREHENSIVE DOCUMENT INTELLIGENCE SYSTEM")
        print("=" * 80)
        print(f"\nBudget: $20-50 for ~850 documents")
        print(f"Expected cost: ~$0.02-0.05 per document = $17-42 total\n")

        # Get uncategorized documents with text content
        query = """
            SELECT document_id, file_name, file_path, text_content
            FROM documents
            WHERE (document_type IS NULL OR document_type = '')
            AND text_content IS NOT NULL
            AND length(text_content) > 100
            ORDER BY created_date DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        self.cursor.execute(query)
        documents = self.cursor.fetchall()

        print(f"Processing {len(documents)} documents...\n")

        for doc in documents:
            try:
                self.process_document(doc['document_id'])
            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue

        print("\n" + "=" * 80)
        print("✅ PROCESSING COMPLETE")
        print("=" * 80)
        print(f"\nProcessed: {self.processed_count} documents")
        print(f"Total cost: ${self.total_cost:.2f}")
        print(f"\nReview AI suggestions queue for recommended database updates.")

    def close(self):
        self.conn.close()


def main():
    import sys

    print("📚 COMPREHENSIVE DOCUMENT INTELLIGENCE SYSTEM")
    print("Processing all documents to extract contracts, invoices, proposals, etc.\n")

    # Check if user wants to run full or test
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        limit = 5
        print(f"🧪 TEST MODE: Processing {limit} documents only\n")
    else:
        limit = None
        print(f"🚀 FULL MODE: Processing ALL uncategorized documents\n")

    processor = DocumentIntelligence()

    try:
        processor.process_all_documents(limit=limit)
    finally:
        processor.close()


if __name__ == "__main__":
    main()
