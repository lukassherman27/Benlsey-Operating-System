#!/usr/bin/env python3
"""
Create Embeddings for RAG System
Phase 2 Preparation - Do not run in production yet.

This script generates vector embeddings for:
- Emails (subject + body)
- Meeting transcripts (summary + transcript)
- RFIs (subject + description)

Uses ChromaDB for vector storage and sentence-transformers for embeddings.

Usage:
    python create_embeddings.py --emails      # Embed all emails
    python create_embeddings.py --transcripts # Embed all transcripts
    python create_embeddings.py --search 'query'  # Test semantic search
    python create_embeddings.py --stats       # Show embedding stats
"""

import os
import sys
import sqlite3
import json
import argparse
from pathlib import Path
from datetime import datetime

# Configuration
DB_PATH = os.getenv("DATABASE_PATH", "database/bensley_master.db")
CHROMA_PATH = "database/chroma"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
BATCH_SIZE = 100

# Check for dependencies
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    HAS_RAG_DEPS = True
except ImportError:
    HAS_RAG_DEPS = False


def check_dependencies() -> bool:
    """Check if RAG dependencies are installed."""
    if not HAS_RAG_DEPS:
        print("=" * 60)
        print("RAG dependencies not installed.")
        print("This is Phase 2 preparation - install when ready.")
        print()
        print("To install:")
        print("  pip install chromadb sentence-transformers")
        print("=" * 60)
        return False
    return True


def get_db_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =============================================================================
# EMAIL EMBEDDINGS
# =============================================================================

def create_email_embeddings(dry_run: bool = False):
    """
    Generate embeddings for all emails.

    Args:
        dry_run: If True, just count emails without creating embeddings
    """
    if not check_dependencies():
        return

    print("=" * 60)
    print("EMAIL EMBEDDINGS")
    print("=" * 60)

    # Load embedding model
    print(f"\nLoading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Connect to ChromaDB
    print(f"Connecting to ChromaDB at: {CHROMA_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Get or create collection
    collection = client.get_or_create_collection(
        name="emails",
        metadata={"description": "Email embeddings for semantic search"}
    )

    # Load emails from database
    print("\nLoading emails from database...")
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            email_id,
            subject,
            body_preview,
            sender_email,
            date
        FROM emails
        WHERE body_preview IS NOT NULL
          AND length(body_preview) > 10
    """)

    emails = cursor.fetchall()
    total = len(emails)
    print(f"Found {total} emails to embed")

    if dry_run:
        print("\n[DRY RUN] Would create embeddings for these emails.")
        conn.close()
        return

    # Process in batches
    print(f"\nGenerating embeddings in batches of {BATCH_SIZE}...")

    for i in range(0, total, BATCH_SIZE):
        batch = emails[i:i + BATCH_SIZE]

        documents = []
        metadatas = []
        ids = []

        for row in batch:
            email_id = row['email_id']
            subject = row['subject'] or ""
            body = row['body_preview'] or ""
            sender = row['sender_email'] or ""
            date = row['date'] or ""

            # Combine subject and body for embedding
            text = f"{subject}\n{body}"

            documents.append(text)
            metadatas.append({
                "email_id": email_id,
                "subject": subject[:200],  # Truncate for metadata
                "sender": sender,
                "date": date,
                "source_type": "email"
            })
            ids.append(f"email_{email_id}")

        # Generate embeddings
        embeddings = model.encode(documents).tolist()

        # Add to ChromaDB
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        progress = min(i + BATCH_SIZE, total)
        print(f"  Processed {progress}/{total} emails ({progress*100//total}%)")

    conn.close()
    print(f"\nDone! Created embeddings for {total} emails.")


# =============================================================================
# TRANSCRIPT EMBEDDINGS
# =============================================================================

def create_transcript_embeddings(dry_run: bool = False):
    """
    Generate embeddings for meeting transcripts.
    Chunks long transcripts for better retrieval.

    Args:
        dry_run: If True, just count transcripts without creating embeddings
    """
    if not check_dependencies():
        return

    print("=" * 60)
    print("TRANSCRIPT EMBEDDINGS")
    print("=" * 60)

    # Load embedding model
    print(f"\nLoading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Connect to ChromaDB
    print(f"Connecting to ChromaDB at: {CHROMA_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Get or create collection
    collection = client.get_or_create_collection(
        name="transcripts",
        metadata={"description": "Meeting transcript embeddings"}
    )

    # Load transcripts from database
    print("\nLoading transcripts from database...")
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            audio_filename,
            transcript,
            summary,
            detected_project_code,
            processed_date
        FROM meeting_transcripts
        WHERE transcript IS NOT NULL
    """)

    transcripts = cursor.fetchall()
    total = len(transcripts)
    print(f"Found {total} transcripts to embed")

    if dry_run:
        print("\n[DRY RUN] Would create embeddings for these transcripts.")
        conn.close()
        return

    # Process each transcript
    print("\nGenerating embeddings...")

    for row in transcripts:
        tid = row['id']
        filename = row['audio_filename'] or f"transcript_{tid}"
        transcript = row['transcript'] or ""
        summary = row['summary'] or ""
        project_code = row['detected_project_code'] or ""
        date = row['processed_date'] or ""

        # Combine summary and transcript
        # For long transcripts, we might want to chunk - but for now, use summary + first part
        text = f"Summary: {summary}\n\nTranscript: {transcript[:3000]}"

        # Generate embedding
        embedding = model.encode(text).tolist()

        # Add to ChromaDB
        collection.add(
            documents=[text],
            embeddings=[embedding],
            metadatas=[{
                "transcript_id": tid,
                "filename": filename,
                "project_code": project_code,
                "date": date,
                "source_type": "transcript"
            }],
            ids=[f"transcript_{tid}"]
        )

        print(f"  Embedded: {filename}")

    conn.close()
    print(f"\nDone! Created embeddings for {total} transcripts.")


# =============================================================================
# SEMANTIC SEARCH
# =============================================================================

def search_similar(
    query: str,
    collection_name: str = "emails",
    limit: int = 5,
    project_code: str = None
) -> list:
    """
    Search for documents similar to the query.

    Args:
        query: The search query
        collection_name: Which collection to search (emails, transcripts)
        limit: Number of results to return
        project_code: Optional filter by project code

    Returns:
        List of similar documents with metadata
    """
    if not check_dependencies():
        return []

    print(f"\nSearching {collection_name} for: '{query}'")

    # Load model and ChromaDB
    model = SentenceTransformer(EMBEDDING_MODEL)
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        collection = client.get_collection(collection_name)
    except Exception as e:
        print(f"Collection '{collection_name}' not found. Run --emails or --transcripts first.")
        return []

    # Generate query embedding
    query_embedding = model.encode(query).tolist()

    # Build where filter if project_code specified
    where_filter = None
    if project_code:
        where_filter = {"project_code": {"$eq": project_code}}

    # Search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit,
        where=where_filter
    )

    # Format results
    formatted = []
    if results and results['documents']:
        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i] if results['metadatas'] else {}
            distance = results['distances'][0][i] if results['distances'] else None

            formatted.append({
                "rank": i + 1,
                "text": doc[:500] + "..." if len(doc) > 500 else doc,
                "metadata": metadata,
                "similarity": 1 - distance if distance else None  # Convert distance to similarity
            })

    return formatted


def print_search_results(results: list):
    """Pretty print search results."""
    if not results:
        print("No results found.")
        return

    print(f"\nFound {len(results)} results:\n")
    print("-" * 60)

    for r in results:
        print(f"\n#{r['rank']} (similarity: {r['similarity']:.3f})")
        print(f"Source: {r['metadata'].get('source_type', 'unknown')}")

        if r['metadata'].get('subject'):
            print(f"Subject: {r['metadata']['subject']}")
        if r['metadata'].get('filename'):
            print(f"File: {r['metadata']['filename']}")
        if r['metadata'].get('project_code'):
            print(f"Project: {r['metadata']['project_code']}")
        if r['metadata'].get('date'):
            print(f"Date: {r['metadata']['date']}")

        print(f"\nText preview:")
        print(f"  {r['text'][:300]}...")
        print("-" * 60)


# =============================================================================
# STATISTICS
# =============================================================================

def show_stats():
    """Show embedding statistics."""
    if not check_dependencies():
        return

    print("=" * 60)
    print("EMBEDDING STATISTICS")
    print("=" * 60)

    client = chromadb.PersistentClient(path=CHROMA_PATH)

    collections = client.list_collections()

    if not collections:
        print("\nNo embeddings created yet.")
        print("Run with --emails or --transcripts to create embeddings.")
        return

    print(f"\nChromaDB path: {CHROMA_PATH}")
    print(f"Collections found: {len(collections)}")
    print()

    for col in collections:
        collection = client.get_collection(col.name)
        count = collection.count()
        print(f"  {col.name}: {count} embeddings")

        # Show metadata
        if col.metadata:
            print(f"    Description: {col.metadata.get('description', 'N/A')}")

    # Show database stats for comparison
    print("\nSource data in SQLite:")
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM emails WHERE body_preview IS NOT NULL")
    email_count = cursor.fetchone()[0]
    print(f"  Emails with body: {email_count}")

    cursor.execute("SELECT COUNT(*) FROM meeting_transcripts WHERE transcript IS NOT NULL")
    transcript_count = cursor.fetchone()[0]
    print(f"  Meeting transcripts: {transcript_count}")

    conn.close()


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Create embeddings for RAG system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python create_embeddings.py --emails           # Embed all emails
    python create_embeddings.py --transcripts      # Embed all transcripts
    python create_embeddings.py --search 'budget'  # Test search
    python create_embeddings.py --stats            # Show statistics
    python create_embeddings.py --dry-run --emails # Preview without creating
        """
    )

    parser.add_argument("--emails", action="store_true",
                       help="Create embeddings for emails")
    parser.add_argument("--transcripts", action="store_true",
                       help="Create embeddings for meeting transcripts")
    parser.add_argument("--search", type=str,
                       help="Test semantic search with query")
    parser.add_argument("--collection", type=str, default="emails",
                       help="Collection to search (emails, transcripts)")
    parser.add_argument("--project", type=str,
                       help="Filter search by project code")
    parser.add_argument("--stats", action="store_true",
                       help="Show embedding statistics")
    parser.add_argument("--dry-run", action="store_true",
                       help="Preview what would be done without creating embeddings")

    args = parser.parse_args()

    # Handle commands
    if args.emails:
        create_email_embeddings(dry_run=args.dry_run)
    elif args.transcripts:
        create_transcript_embeddings(dry_run=args.dry_run)
    elif args.search:
        results = search_similar(
            args.search,
            collection_name=args.collection,
            project_code=args.project
        )
        print_search_results(results)
    elif args.stats:
        show_stats()
    else:
        # No args - show help
        parser.print_help()
        print("\n" + "=" * 60)
        print("PHASE 2 PREPARATION")
        print("=" * 60)
        print("\nThis script is ready for Phase 2 (January 2026).")
        print("Current status: Dependencies check...")
        check_dependencies()


if __name__ == "__main__":
    main()
