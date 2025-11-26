#!/usr/bin/env python3
"""
Document Intelligence Indexer
Scans, indexes, and extracts intelligence from proposal documents
"""
import sqlite3
import sys
import os
import re
from pathlib import Path
from datetime import datetime
import json
from openai import OpenAI

class DocumentIndexer:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Initialize OpenAI
        api_key = os.environ.get('OPENAI_API_KEY')
        self.ai_enabled = bool(api_key)
        if self.ai_enabled:
            self.client = OpenAI(api_key=api_key)
            print("✓ OpenAI enabled")
        else:
            print("⚠ OpenAI disabled - set OPENAI_API_KEY for AI features")

        self.run_migration()

    def run_migration(self):
        """Apply migration 008"""
        migration_path = Path(__file__).parent / "database" / "migrations" / "008_document_intelligence.sql"
        if migration_path.exists():
            with open(migration_path, 'r') as f:
                migration_sql = f.read()
                self.conn.executescript(migration_sql)
                self.conn.commit()
            print("✓ Migration 008 applied")

    def extract_text_from_file(self, file_path):
        """Extract text content from document"""
        file_ext = file_path.suffix.lower()

        try:
            if file_ext == '.pdf':
                return self.extract_from_pdf(file_path)
            elif file_ext in ['.docx', '.doc']:
                return self.extract_from_docx(file_path)
            elif file_ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return None
        except Exception as e:
            print(f"  ⚠ Error extracting text: {str(e)}")
            return None

    def extract_from_pdf(self, file_path):
        """Extract text from PDF"""
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except ImportError:
            print("  ⚠ pdfplumber not installed - run: pip install pdfplumber")
            return None
        except Exception as e:
            print(f"  ⚠ PDF extraction error: {str(e)}")
            return None

    def extract_from_docx(self, file_path):
        """Extract text from Word document"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except ImportError:
            print("  ⚠ python-docx not installed - run: pip install python-docx")
            return None
        except Exception as e:
            print(f"  ⚠ DOCX extraction error: {str(e)}")
            return None

    def extract_project_code(self, file_name, text_content):
        """Extract project code from filename or content"""
        # Try filename first (e.g., "25-033 The Ritz..." or "BK-033...")
        patterns = [
            r'(?:25-)?BK-(\d{3})',
            r'(?:25-)?(\d{3})\s',
            r'BK(\d{3})'
        ]

        for pattern in patterns:
            match = re.search(pattern, file_name, re.IGNORECASE)
            if match:
                code_num = match.group(1)
                return f"BK-{code_num}"

        # Try content if filename didn't work
        if text_content:
            for pattern in patterns:
                match = re.search(pattern, text_content[:1000], re.IGNORECASE)
                if match:
                    code_num = match.group(1)
                    return f"BK-{code_num}"

        return None

    def extract_intelligence_ai(self, file_name, text_content):
        """Extract key information using AI"""
        if not self.ai_enabled or not text_content:
            return None

        # Limit content to first 4000 characters for API
        content_sample = text_content[:4000]

        prompt = f"""Extract key information from this proposal document.

FILENAME: {file_name}

CONTENT:
{content_sample}

Extract and return as JSON:
{{
  "document_type": "proposal|contract|nda|mou|invoice|rfi|schedule",
  "project_code": "BK-XXX if found",
  "fee_amount": "number only, no currency symbols",
  "fee_currency": "USD|EUR|THB|etc",
  "scope_summary": "1-2 sentence summary of scope",
  "timeline": "project timeline if mentioned",
  "key_deliverables": ["list", "of", "deliverables"],
  "decision_makers": ["names", "of", "people"],
  "document_date": "YYYY-MM-DD if found",
  "status": "draft|final|signed",
  "executive_summary": "2-3 sentence summary of document"
}}

Return ONLY valid JSON, no other text."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured information from business documents. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )

            result = response.choices[0].message.content.strip()

            # Try to parse JSON
            # Remove markdown code blocks if present
            if result.startswith('```'):
                result = result.split('```')[1]
                if result.startswith('json'):
                    result = result[4:]

            return json.loads(result)

        except Exception as e:
            print(f"  ⚠ AI extraction error: {str(e)}")
            return None

    def index_document(self, file_path):
        """Index a single document"""
        file_path = Path(file_path)

        if not file_path.exists():
            print(f"  ✗ File not found: {file_path}")
            return

        print(f"\n📄 {file_path.name}")

        # Check if already indexed
        self.cursor.execute("SELECT document_id FROM documents WHERE file_path = ?", (str(file_path),))
        existing = self.cursor.fetchone()
        if existing:
            print("  ⏭  Already indexed - skipping")
            return existing['document_id']

        # Get file metadata
        stat = file_path.stat()
        file_size = stat.st_size
        modified_date = datetime.fromtimestamp(stat.st_mtime).isoformat()

        # Extract text content
        print("  📖 Extracting text...")
        text_content = self.extract_text_from_file(file_path)

        if text_content:
            word_count = len(text_content.split())
            print(f"  ✓ Extracted {word_count} words")
        else:
            print("  ⚠ No text extracted")

        # Extract project code
        project_code = self.extract_project_code(file_path.name, text_content)
        if project_code:
            print(f"  🔗 Project: {project_code}")

        # Extract intelligence using AI
        intelligence = None
        if text_content and self.ai_enabled:
            print("  🧠 Extracting intelligence...")
            intelligence = self.extract_intelligence_ai(file_path.name, text_content)

            if intelligence:
                if intelligence.get('fee_amount'):
                    fee = intelligence['fee_amount']
                    currency = intelligence.get('fee_currency', 'USD')
                    print(f"  💰 Fee: {currency} {fee}")
                if intelligence.get('document_type'):
                    print(f"  📑 Type: {intelligence['document_type']}")

        # Insert document
        self.cursor.execute("""
            INSERT INTO documents
            (file_path, file_name, file_type, file_size, modified_date,
             text_content, document_type, project_code, document_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(file_path),
            file_path.name,
            file_path.suffix.lower(),
            file_size,
            modified_date,
            text_content,
            intelligence.get('document_type') if intelligence else None,
            project_code or (intelligence.get('project_code') if intelligence else None),
            intelligence.get('document_date') if intelligence else None,
            intelligence.get('status') if intelligence else None
        ))

        document_id = self.cursor.lastrowid

        # Insert intelligence if extracted
        if intelligence:
            self.cursor.execute("""
                INSERT INTO document_intelligence
                (document_id, fee_amount, fee_currency, scope_summary, timeline,
                 key_deliverables, decision_makers, executive_summary, model_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document_id,
                intelligence.get('fee_amount'),
                intelligence.get('fee_currency'),
                intelligence.get('scope_summary'),
                intelligence.get('timeline'),
                json.dumps(intelligence.get('key_deliverables', [])),
                json.dumps(intelligence.get('decision_makers', [])),
                intelligence.get('executive_summary'),
                'gpt-3.5-turbo'
            ))

        # Link to proposal if project code found
        if project_code:
            self.cursor.execute("SELECT proposal_id FROM proposals WHERE project_code = ?", (project_code,))
            proposal = self.cursor.fetchone()
            if proposal:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO document_proposal_links
                    (document_id, proposal_id, link_type)
                    VALUES (?, ?, ?)
                """, (document_id, proposal['proposal_id'], 'primary'))
                print(f"  ✓ Linked to proposal")

        self.conn.commit()
        print("  ✓ Indexed")

        return document_id

    def index_directory(self, directory_path, recursive=True):
        """Index all documents in a directory"""
        directory_path = Path(directory_path)

        print(f"\n{'='*80}")
        print(f"📂 INDEXING DIRECTORY: {directory_path}")
        print(f"{'='*80}")

        # Find all documents
        patterns = ['*.pdf', '*.docx', '*.doc']
        files = []

        if recursive:
            for pattern in patterns:
                files.extend(directory_path.rglob(pattern))
        else:
            for pattern in patterns:
                files.extend(directory_path.glob(pattern))

        print(f"\nFound {len(files)} documents\n")

        indexed_count = 0
        skipped_count = 0
        error_count = 0

        for file_path in files:
            try:
                result = self.index_document(file_path)
                if result:
                    indexed_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                error_count += 1

        print(f"\n{'='*80}")
        print(f"📊 INDEXING COMPLETE")
        print(f"{'='*80}")
        print(f"  ✓ Indexed: {indexed_count}")
        print(f"  ⏭  Skipped: {skipped_count}")
        print(f"  ✗ Errors: {error_count}")
        print(f"{'='*80}\n")

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 document_indexer.py <db_path> <directory_path>")
        print("Example: python3 document_indexer.py database/bensley_master.db ~/Desktop/BDS_SYSTEM/Latest\\ Proposals/")
        return

    db_path = sys.argv[1]
    directory_path = sys.argv[2]

    if not Path(db_path).exists():
        print(f"✗ Database not found: {db_path}")
        return

    if not Path(directory_path).exists():
        print(f"✗ Directory not found: {directory_path}")
        return

    indexer = DocumentIndexer(db_path)
    indexer.index_directory(directory_path)

if __name__ == "__main__":
    main()
