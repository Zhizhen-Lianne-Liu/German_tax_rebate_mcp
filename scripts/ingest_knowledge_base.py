#!/usr/bin/env python3
"""
Ingest German tax law documents into RAG vector database.

This script:
1. Reads markdown files from knowledge_base/
2. Chunks them into smaller pieces
3. Generates embeddings using local model
4. Stores in ChromaDB

Run once during setup, then again when adding new documents.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from lib.rag_engine import get_rag
from config import KNOWLEDGE_BASE_DIR
import re


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Text to chunk
        chunk_size: Target size in characters
        overlap: Overlap between chunks

    Returns:
        List of text chunks
    """
    # Split by paragraphs first
    paragraphs = text.split('\n\n')

    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_length = len(para)

        # If single paragraph is too long, split it
        if para_length > chunk_size:
            # Split by sentences
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sentence in sentences:
                if current_length + len(sentence) > chunk_size and current_chunk:
                    chunks.append(' '.join(current_chunk))
                    # Keep last sentence for overlap
                    current_chunk = [current_chunk[-1]] if current_chunk else []
                    current_length = len(current_chunk[0]) if current_chunk else 0
                current_chunk.append(sentence)
                current_length += len(sentence)
        else:
            if current_length + para_length > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_length = 0
            current_chunk.append(para)
            current_length += para_length

    # Add remaining chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


def ingest_markdown_file(file_path: Path, collection: str, rag: 'TaxRAG'):
    """Ingest a single markdown file"""
    print(f"  Processing: {file_path.name}")

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract title from first # heading
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else file_path.stem

    # Chunk the text
    chunks = chunk_text(content)

    # Add each chunk to RAG
    for i, chunk in enumerate(chunks):
        metadata = {
            'source': str(file_path.relative_to(KNOWLEDGE_BASE_DIR)),
            'title': title,
            'chunk': i + 1,
            'total_chunks': len(chunks)
        }
        rag.add_document(chunk, metadata, collection=collection)

    print(f"    Added {len(chunks)} chunks")


def main(force: bool = False):
    """Main ingestion process"""
    print("=" * 60)
    print("German Tax Knowledge Base Ingestion")
    print("=" * 60)

    # Initialize RAG
    print("\n1. Initializing RAG engine...")
    rag = get_rag()

    # Check if already populated
    if not force:
        deduction_count = rag.get_collection_count('deductions')
        if deduction_count > 0:
            print(f"\n⚠️  Database already contains {deduction_count} documents.")
            print("   Use --force to re-ingest.")
            response = input("   Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("   Aborted.")
                return

    # Process each category
    categories = {
        'deductions': 'Deduction rules and examples',
        'forms': 'ELSTER form instructions',
        'tax_law': 'German tax code sections'
    }

    total_files = 0

    for category, description in categories.items():
        print(f"\n2. Processing {category} ({description})...")
        category_dir = KNOWLEDGE_BASE_DIR / category

        if not category_dir.exists():
            print(f"   Creating directory: {category_dir}")
            category_dir.mkdir(parents=True, exist_ok=True)
            print(f"   ⚠️  Directory is empty. Add .md files to {category_dir}")
            continue

        # Find all markdown files
        md_files = list(category_dir.rglob('*.md'))

        if not md_files:
            print(f"   ⚠️  No .md files found in {category_dir}")
            continue

        for md_file in md_files:
            ingest_markdown_file(md_file, category, rag)
            total_files += 1

    # Summary
    print("\n" + "=" * 60)
    print("Ingestion Complete!")
    print("=" * 60)
    print(f"Files processed: {total_files}")
    print(f"Deductions collection: {rag.get_collection_count('deductions')} chunks")
    print(f"Forms collection: {rag.get_collection_count('forms')} chunks")
    print(f"Tax law collection: {rag.get_collection_count('tax_law')} chunks")
    print("\n✅ RAG database ready for queries!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest German tax knowledge base")
    parser.add_argument('--force', action='store_true', help='Force re-ingestion')
    args = parser.parse_args()

    try:
        main(force=args.force)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
