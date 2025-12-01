# Agent 5: Intelligence & RAG Preparation

**Role:** Enhance AI query capabilities and prepare for Phase 2 RAG/Local LLM
**Owner:** `scripts/core/query_brain.py`, AI services, training data collection
**Do NOT touch:** Frontend, deployment, core data pipelines

---

## Context

You are responsible for:
1. Improving the natural language query interface
2. Adding meeting transcripts to query context
3. Collecting training data for future fine-tuning
4. Preparing architecture for RAG (Phase 2)

**Read these files FIRST:**
1. `CLAUDE.md` - Project context
2. `.claude/CODEBASE_INDEX.md` - Where things live
3. `scripts/core/query_brain.py` - Current query system
4. `backend/services/query_service.py` - API query handler

---

## Current State

**Query System:**
- `scripts/core/query_brain.py` - Handles natural language queries
- Uses Claude API for understanding
- Queries database based on interpreted intent
- Returns structured answers

**Training Data Tables (Already exist):**
- `training_data` - Store query/response pairs
- `ai_suggestions_queue` - AI-generated suggestions
- `learned_patterns` - Patterns to remember
- `document_intelligence` - Document analysis

**What's Missing:**
- Meeting transcripts not included in query context
- No training data being collected
- No RAG preparation

---

## Your Tasks (Priority Order)

### P1: Add Meeting Transcripts to Query Context

**File to edit:** `scripts/core/query_brain.py`

Find where context is gathered for queries and add meeting transcripts:

```python
def get_project_context(project_code: str) -> dict:
    """
    Gather all context for a project to answer queries.
    """
    context = {
        "project_info": get_project_info(project_code),
        "recent_emails": get_recent_emails(project_code),
        "invoices": get_invoices(project_code),
        "rfis": get_rfis(project_code),
        # ADD THIS:
        "meeting_transcripts": get_meeting_transcripts(project_code),
    }
    return context

def get_meeting_transcripts(project_code: str, limit: int = 5) -> list:
    """
    Get recent meeting transcripts for a project.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            audio_filename,
            summary,
            key_points,
            action_items,
            participants,
            meeting_type,
            sentiment,
            processed_date
        FROM meeting_transcripts
        WHERE detected_project_code = ?
           OR detected_project_code LIKE ?
        ORDER BY processed_date DESC
        LIMIT ?
    """, (project_code, f"%{project_code}%", limit))

    transcripts = []
    for row in cursor.fetchall():
        transcripts.append({
            "id": row[0],
            "filename": row[1],
            "summary": row[2],
            "key_points": json.loads(row[3] or "[]"),
            "action_items": json.loads(row[4] or "[]"),
            "participants": json.loads(row[5] or "[]"),
            "type": row[6],
            "sentiment": row[7],
            "date": row[8]
        })

    conn.close()
    return transcripts
```

**Update the prompt to include transcripts:**

```python
def build_query_prompt(query: str, context: dict) -> str:
    """
    Build prompt for Claude with all available context.
    """
    prompt = f"""You are a helpful assistant for Bensley Design Studios.
Answer the following question based on the project data provided.

## Question:
{query}

## Project Information:
{json.dumps(context['project_info'], indent=2)}

## Recent Emails ({len(context['recent_emails'])} total):
{format_emails_for_prompt(context['recent_emails'])}

## Meeting Transcripts ({len(context['meeting_transcripts'])} total):
{format_transcripts_for_prompt(context['meeting_transcripts'])}

## Open RFIs:
{format_rfis_for_prompt(context['rfis'])}

## Invoices:
{format_invoices_for_prompt(context['invoices'])}

Answer the question based on this data. If you cannot find relevant information,
say so clearly. Reference specific emails or meetings when possible.
"""
    return prompt

def format_transcripts_for_prompt(transcripts: list) -> str:
    """Format meeting transcripts for inclusion in prompt."""
    if not transcripts:
        return "No meeting transcripts available."

    lines = []
    for t in transcripts:
        lines.append(f"### Meeting: {t['filename']} ({t['date']})")
        lines.append(f"Type: {t['type']} | Sentiment: {t['sentiment']}")
        lines.append(f"Summary: {t['summary']}")
        if t['key_points']:
            lines.append("Key Points:")
            for point in t['key_points']:
                lines.append(f"  - {point}")
        if t['action_items']:
            lines.append("Action Items:")
            for item in t['action_items']:
                task = item.get('task', item) if isinstance(item, dict) else item
                lines.append(f"  - {task}")
        lines.append("")

    return "\n".join(lines)
```

---

### P1: Implement Training Data Collection

**File to edit:** `scripts/core/query_brain.py` or `backend/services/query_service.py`

After every query/response, log it for future fine-tuning:

```python
def log_training_data(
    query: str,
    response: str,
    context: dict,
    model_used: str = "claude-3-opus"
):
    """
    Log query/response pair for future model fine-tuning.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ensure table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS training_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_text TEXT NOT NULL,
            response_text TEXT NOT NULL,
            context_provided TEXT,
            model_used TEXT,
            user_rating INTEGER,  -- 1-5 scale, NULL until rated
            feedback_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        INSERT INTO training_data (query_text, response_text, context_provided, model_used)
        VALUES (?, ?, ?, ?)
    """, (
        query,
        response,
        json.dumps(context),
        model_used
    ))

    conn.commit()
    conn.close()

# Call this after every successful query
def answer_query(query: str, project_code: str = None) -> str:
    context = get_project_context(project_code) if project_code else {}
    prompt = build_query_prompt(query, context)

    # Get response from Claude
    response = call_claude(prompt)

    # Log for training data
    log_training_data(query, response, context)

    return response
```

---

### P2: Test Query with Meeting Context

After adding transcripts to context, test these queries:

```bash
# Test query about meeting content
python scripts/core/query_brain.py --query "What did the client say about the stone architrave?" --project "22 BK-095"

# Test action items query
python scripts/core/query_brain.py --query "What are the pending action items for this project?" --project "22 BK-095"

# Test timeline query
python scripts/core/query_brain.py --query "Summarize all communications in the last month" --project "22 BK-095"
```

**Expected behavior:**
- Query should include meeting transcript summaries in context
- Response should reference specific meetings when relevant
- Action items from transcripts should be accessible

---

### P2: RAG Architecture Documentation

**Create file:** `docs/architecture/RAG_DESIGN.md`

```markdown
# RAG System Design for BDS Operations Platform

## Phase 2 Target: January 2026

## Overview

RAG (Retrieval Augmented Generation) will allow:
1. Semantic search across all documents and emails
2. Better answers by finding relevant context automatically
3. Reduced API costs by using smaller context windows
4. Foundation for local LLM deployment

## Components

### 1. Vector Database
**Choice:** ChromaDB (simple, embedded, Python-native)

**Why:**
- No separate server needed
- Works well with SQLite setup
- Easy to migrate to Qdrant later if needed

### 2. Embedding Model
**Choice:** `all-MiniLM-L6-v2` (via sentence-transformers)

**Why:**
- Fast, lightweight (80MB)
- Good quality for semantic search
- Runs locally, no API costs

### 3. Documents to Embed

| Source | Records | Priority |
|--------|---------|----------|
| Emails (body) | 3,356 | High |
| Meeting transcripts | 10+ | High |
| RFI descriptions | 3+ | Medium |
| Project notes | varies | Medium |

### 4. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     USER QUERY                          │
│           "What did client say about delays?"           │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    EMBED QUERY                          │
│           all-MiniLM-L6-v2 → [0.12, -0.34, ...]        │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              CHROMADB SIMILARITY SEARCH                 │
│        Find top 5 most similar documents/emails         │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                 BUILD CONTEXT PROMPT                    │
│      Add retrieved documents to Claude/LLM prompt       │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  LLM GENERATES ANSWER                   │
│        Claude (now) or Local Llama (Phase 2)           │
└─────────────────────────────────────────────────────────┘
```

## Implementation Plan

### Step 1: Install Dependencies
```bash
pip install chromadb sentence-transformers
```

### Step 2: Create Embeddings Script
```python
# scripts/core/create_embeddings.py

import chromadb
from sentence_transformers import SentenceTransformer
import sqlite3

model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="database/chroma")

def embed_emails():
    # Query all emails
    # Generate embeddings
    # Store in ChromaDB collection

def embed_transcripts():
    # Query all meeting transcripts
    # Generate embeddings
    # Store in ChromaDB collection
```

### Step 3: Update Query Brain
```python
def get_relevant_context(query: str, limit: int = 5) -> list:
    """
    Use RAG to find most relevant documents for query.
    """
    query_embedding = model.encode(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit
    )
    return results['documents']
```

## Timeline

- **Dec 15-31:** Install and test locally
- **Jan 1-7:** Generate embeddings for all content
- **Jan 8-15:** Integrate with query system
- **Jan 15+:** Production use

## Hardware Requirements

For local embeddings (no GPU needed):
- Mac M1/M2: Works great, ~100ms per embedding
- 4GB+ RAM recommended

For local LLM (Phase 2+):
- Mac M2 Pro with 32GB RAM: Llama 3.1 8B
- Or GPU server for larger models
```

---

### P2: Prepare Embedding Script (Skeleton)

**Create file:** `scripts/core/create_embeddings.py`

```python
#!/usr/bin/env python3
"""
Create embeddings for RAG system.
Phase 2 preparation - do not run in production yet.
"""

import os
import sqlite3
import json

# Only import if installed
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    HAS_RAG_DEPS = True
except ImportError:
    HAS_RAG_DEPS = False
    print("RAG dependencies not installed. Run:")
    print("  pip install chromadb sentence-transformers")

DB_PATH = os.getenv("DATABASE_PATH", "database/bensley_master.db")
CHROMA_PATH = "database/chroma"

def check_dependencies():
    """Check if RAG dependencies are installed."""
    if not HAS_RAG_DEPS:
        print("Missing dependencies. This is Phase 2 preparation.")
        return False
    return True

def create_email_embeddings():
    """Generate embeddings for all emails."""
    if not check_dependencies():
        return

    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print("Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection("emails")

    print("Loading emails from database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT email_id, subject, body_preview, sender_email
        FROM emails
        WHERE body_preview IS NOT NULL
    """)

    batch_size = 100
    emails = cursor.fetchall()
    total = len(emails)

    print(f"Generating embeddings for {total} emails...")

    for i in range(0, total, batch_size):
        batch = emails[i:i+batch_size]

        documents = []
        metadatas = []
        ids = []

        for email_id, subject, body, sender in batch:
            text = f"{subject}\n{body}"
            documents.append(text)
            metadatas.append({
                "email_id": email_id,
                "subject": subject,
                "sender": sender,
                "type": "email"
            })
            ids.append(f"email_{email_id}")

        embeddings = model.encode(documents).tolist()

        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        print(f"  Processed {min(i+batch_size, total)}/{total}")

    conn.close()
    print("Done!")

def create_transcript_embeddings():
    """Generate embeddings for meeting transcripts."""
    if not check_dependencies():
        return

    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print("Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection("transcripts")

    print("Loading transcripts from database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, audio_filename, transcript, summary, detected_project_code
        FROM meeting_transcripts
        WHERE transcript IS NOT NULL
    """)

    transcripts = cursor.fetchall()
    print(f"Generating embeddings for {len(transcripts)} transcripts...")

    for tid, filename, transcript, summary, project_code in transcripts:
        # Embed the full transcript
        text = f"{summary}\n\n{transcript}"
        embedding = model.encode(text).tolist()

        collection.add(
            documents=[text],
            embeddings=[embedding],
            metadatas=[{
                "transcript_id": tid,
                "filename": filename,
                "project_code": project_code,
                "type": "transcript"
            }],
            ids=[f"transcript_{tid}"]
        )

    conn.close()
    print("Done!")

def search_similar(query: str, collection_name: str = "emails", limit: int = 5):
    """
    Search for documents similar to query.
    """
    if not check_dependencies():
        return []

    model = SentenceTransformer('all-MiniLM-L6-v2')
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(collection_name)

    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit
    )

    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--emails", action="store_true", help="Embed emails")
    parser.add_argument("--transcripts", action="store_true", help="Embed transcripts")
    parser.add_argument("--search", type=str, help="Test search query")

    args = parser.parse_args()

    if args.emails:
        create_email_embeddings()
    elif args.transcripts:
        create_transcript_embeddings()
    elif args.search:
        results = search_similar(args.search)
        print(json.dumps(results, indent=2))
    else:
        print("Usage:")
        print("  python create_embeddings.py --emails      # Embed all emails")
        print("  python create_embeddings.py --transcripts # Embed all transcripts")
        print("  python create_embeddings.py --search 'query'  # Test search")
```

---

## Files You Own

```
scripts/core/
├── query_brain.py           # EDIT - add transcript context
├── smart_email_brain.py     # Reference for patterns
└── create_embeddings.py     # NEW - RAG preparation

backend/services/
├── query_service.py         # EDIT - training data logging
└── ai_learning_service.py   # Reference (if exists)

docs/architecture/
└── RAG_DESIGN.md           # NEW - Phase 2 documentation
```

---

## When You're Done

1. Test query with meeting context works
2. Verify training data is being collected
3. Document RAG architecture for Phase 2
4. Create embedding script skeleton

---

## Do NOT

- Modify frontend (Agent 2's job)
- Touch deployment (Agent 3's job)
- Modify core data pipelines (Agent 4's job)
- Run embeddings in production yet (Phase 2)

---

**Estimated Time:** 6-8 hours total
**Start:** After Agent 1's transcript API is ready
**Checkpoint:** After query with meeting context works
**Phase 2 Prep:** RAG documentation and skeleton complete
