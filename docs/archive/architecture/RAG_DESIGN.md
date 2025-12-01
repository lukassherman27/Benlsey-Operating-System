# RAG System Design for BDS Operations Platform

**Status:** Phase 2 Preparation
**Target:** January 2026
**Last Updated:** November 26, 2025

---

## Overview

RAG (Retrieval Augmented Generation) will enhance the query system by:
1. Semantic search across all documents and emails
2. Better answers by finding relevant context automatically
3. Reduced API costs by using smaller context windows
4. Foundation for local LLM deployment

---

## Current State (Pre-RAG)

The query system currently uses:
- **Pattern matching** in `query_brain.py` for simple queries
- **GPT-4o** in `query_service.py` for AI-powered queries
- **Full database schema** passed to LLM for SQL generation
- **Training data collection** for future fine-tuning

**Limitations:**
- Cannot search by semantic meaning
- Limited to structured data queries
- Full context must be manually assembled
- Large prompts = higher API costs

---

## Components

### 1. Vector Database

**Choice:** ChromaDB (embedded, Python-native)

**Why ChromaDB:**
- No separate server needed
- Works well with existing SQLite setup
- Persistent storage to disk
- Easy migration to Qdrant/Pinecone later if needed
- Open source, active development

**Alternative considered:** Qdrant (better for large scale, but overkill for current needs)

### 2. Embedding Model

**Choice:** `all-MiniLM-L6-v2` (via sentence-transformers)

**Why:**
- Fast, lightweight (~80MB)
- Good quality for semantic search
- Runs locally, no API costs
- 384-dimensional embeddings (compact)
- Well-documented, widely used

**Alternative:** OpenAI `text-embedding-3-small` (better quality but adds API cost)

### 3. Documents to Embed

| Source | Current Count | Priority | Notes |
|--------|--------------|----------|-------|
| Emails (body) | ~3,356 | High | Main communication record |
| Meeting transcripts | ~10 | High | Rich discussion context |
| RFI descriptions | varies | Medium | Technical Q&A |
| Project notes | varies | Medium | Internal documentation |
| Contract text | varies | Low | Phase 2+ |

---

## Architecture

```
                         USER QUERY
           "What did client say about delays?"
                           |
                           v
    +--------------------------------------------------+
    |              QUERY PREPROCESSOR                   |
    |  - Detect if semantic search is beneficial        |
    |  - Extract key entities (project, date, person)   |
    +--------------------------------------------------+
                           |
            +--------------+--------------+
            |                             |
            v                             v
    +----------------+          +------------------+
    |  EMBED QUERY   |          | STRUCTURED QUERY |
    |  MiniLM-L6-v2  |          | (existing SQL)   |
    +----------------+          +------------------+
            |                             |
            v                             |
    +------------------+                  |
    | CHROMADB SEARCH  |                  |
    | Top 5 similar    |                  |
    | documents        |                  |
    +------------------+                  |
            |                             |
            +-------------+---------------+
                          |
                          v
    +--------------------------------------------------+
    |              BUILD CONTEXT PROMPT                 |
    |  - Retrieved documents from ChromaDB             |
    |  - Structured data from SQL queries              |
    |  - Meeting transcripts for project               |
    +--------------------------------------------------+
                          |
                          v
    +--------------------------------------------------+
    |            LLM GENERATES ANSWER                   |
    |  - Claude/GPT-4 (now)                            |
    |  - Local Llama 3.1 8B (Phase 2+)                 |
    +--------------------------------------------------+
                          |
                          v
    +--------------------------------------------------+
    |              LOG TRAINING DATA                    |
    |  - Query/response pair                           |
    |  - Context provided                              |
    |  - For future fine-tuning                        |
    +--------------------------------------------------+
```

---

## Implementation Plan

### Phase 2a: Basic RAG (Target: Dec 15-31, 2025)

1. **Install dependencies**
   ```bash
   pip install chromadb sentence-transformers
   ```

2. **Create embedding script** (`scripts/core/create_embeddings.py`)
   - Load emails from database
   - Generate embeddings in batches
   - Store in ChromaDB persistent collection

3. **Create search function**
   - Query embedding generation
   - Similarity search in ChromaDB
   - Return top-k results with metadata

4. **Test on sample queries**
   - "What did the client say about stone?"
   - "Any concerns about budget?"
   - "Timeline discussions for BK-095"

### Phase 2b: Integration (Target: Jan 1-15, 2026)

1. **Update query_service.py**
   - Add RAG pathway for semantic queries
   - Combine RAG results with structured data
   - Smart routing: SQL for structured, RAG for semantic

2. **Add transcript embeddings**
   - Embed meeting transcripts
   - Chunk long transcripts (~500 tokens each)
   - Store with project metadata

3. **UI integration**
   - Show "relevant documents" in query results
   - Link to source emails/transcripts
   - Confidence scores

### Phase 2c: Local LLM (Target: Jan 15+, 2026)

1. **Install Ollama**
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull llama3.1:8b
   ```

2. **Create local inference endpoint**
   - FastAPI wrapper around Ollama
   - Compatible API with OpenAI format
   - Fallback to cloud if local fails

3. **Hybrid strategy**
   - Local LLM for simple queries (fast, free)
   - Cloud API for complex queries (better quality)
   - Cost savings: 60-80% reduction in API costs

---

## Data Pipeline for Embeddings

```python
# Simplified flow
def create_embeddings_pipeline():
    """
    1. Load documents from SQLite
    2. Preprocess text (clean, chunk)
    3. Generate embeddings
    4. Store in ChromaDB with metadata
    5. Create index for fast search
    """
    pass
```

**Chunking Strategy:**
- Emails: No chunking (usually <500 tokens)
- Transcripts: Chunk at ~500 tokens with 50 token overlap
- Maintain sentence boundaries
- Store chunk index in metadata

**Metadata to Store:**
```python
{
    "source_type": "email" | "transcript" | "rfi",
    "source_id": 123,
    "project_code": "22 BK-095",
    "date": "2025-11-15",
    "chunk_index": 0,  # For chunked documents
    "total_chunks": 1
}
```

---

## Hardware Requirements

**For Local Embeddings (current setup works):**
- Mac M1/M2: ~100ms per embedding
- 4GB+ RAM recommended
- Embedding 3,000 emails: ~5 minutes

**For Local LLM (Phase 2c):**
- Mac M2 Pro with 32GB RAM: Llama 3.1 8B runs well
- GPU server alternative: RTX 3090/4090 for faster inference
- Quantized models (Q4_K_M) reduce memory by 4x

---

## API Changes

### New Endpoints (Phase 2)

```python
# Semantic search endpoint
@app.post("/api/query/semantic")
async def semantic_search(query: str, project_code: str = None, limit: int = 5):
    """
    Search for semantically similar documents.
    Returns relevant emails, transcripts, RFIs.
    """
    pass

# Hybrid query endpoint
@app.post("/api/query/ask-rag")
async def rag_query(
    question: str,
    project_code: str = None,
    use_rag: bool = True,
    use_local_llm: bool = False
):
    """
    Answer question using RAG-enhanced context.
    Combines semantic search with structured data.
    """
    pass
```

---

## Cost Analysis

**Current (Cloud API only):**
- ~$0.01-0.03 per query (GPT-4o)
- 100 queries/day = ~$60-90/month

**With RAG (Phase 2a-b):**
- Same per-query cost
- But better answers from semantic search
- Smaller context windows = 30% cost reduction

**With Local LLM (Phase 2c):**
- Simple queries: $0 (local)
- Complex queries: Still use cloud
- Estimated 60-80% cost reduction

---

## Monitoring & Evaluation

**Metrics to Track:**
- Query latency (target: <3s total)
- Semantic search recall (target: >80%)
- User satisfaction (thumbs up/down)
- API cost per query

**A/B Testing:**
- Compare RAG vs non-RAG answers
- Measure user preference
- Track which queries benefit from RAG

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Embedding quality | Medium | Use proven model (MiniLM), test extensively |
| ChromaDB scalability | Low | Current data size is small, easy to migrate |
| Local LLM quality | Medium | Start with cloud fallback, gradually increase local |
| Increased complexity | Medium | Modular design, comprehensive logging |

---

## Files to Create

```
scripts/core/
├── create_embeddings.py     # Generate and store embeddings
├── rag_search.py            # Semantic search functions
└── local_llm.py             # Ollama wrapper (Phase 2c)

database/
├── chroma/                  # ChromaDB persistent storage
│   ├── emails/              # Email embeddings collection
│   └── transcripts/         # Transcript embeddings collection

backend/services/
└── rag_service.py           # RAG integration service
```

---

## Success Criteria

1. Semantic search returns relevant documents for open-ended queries
2. Query answers reference specific emails/meetings when relevant
3. 30%+ reduction in API costs from smaller contexts
4. Query latency remains under 5 seconds
5. User feedback (thumbs up) rate >80%

---

## Next Steps

1. **Now:** Create `create_embeddings.py` skeleton (Phase 2 prep)
2. **Dec 15:** Install dependencies, test embedding generation
3. **Dec 20:** Embed all emails and transcripts
4. **Jan 1:** Integrate with query service
5. **Jan 15:** Deploy to production

---

*This document will be updated as implementation progresses.*
