#!/usr/bin/env python3
"""
Scrape German tax rules from official sources and embed them using Gemini API.

1. Scrapes from ELSTER, BMF, EStG websites
2. Generates embeddings using Gemini API
3. Stores in PostgreSQL with pgvector
"""

import sys
from pathlib import Path
import time
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from lib.rag_engine import get_rag

# Import the scraper
sys.path.append(str(Path(__file__).parent))
from scrape_elster import TaxRuleScraper


def main():
    """Scrape and embed German tax rules"""
    print("=" * 60)
    print("German Tax Rules: Scrape + Embed")
    print("=" * 60)

    # Check API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("\n❌ Error: GEMINI_API_KEY not found in .env file")
        print("   Please add your Gemini API key to .env")
        sys.exit(1)

    print(f"\n✅ Gemini API key found")

    # Step 1: Scrape content
    print("\n" + "=" * 60)
    print("STEP 1: Scraping content from official sources")
    print("=" * 60)

    # Don't init tables in scraper (RAG engine will do that with vector support)
    scraper = TaxRuleScraper(init_tables=False)
    all_documents = []

    try:
        # Scrape EStG (German Tax Code)
        all_documents.extend(scraper.scrape_estg_sections())

        # Scrape BMF Handbook
        all_documents.extend(scraper.scrape_bmf_handbook())

        # Scrape BMF Circulars
        all_documents.extend(scraper.scrape_bmf_circulars())

        # Add ELSTER Forms
        all_documents.extend(scraper.scrape_elster_forms())

        print(f"\n✅ Scraped {len(all_documents)} documents")

    except Exception as e:
        print(f"\n❌ Scraping error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Step 2: Initialize RAG with Gemini embeddings
    print("\n" + "=" * 60)
    print("STEP 2: Initializing Gemini embeddings + pgvector")
    print("=" * 60)

    try:
        rag = get_rag()
        print("✅ RAG engine initialized")

    except Exception as e:
        print(f"\n❌ RAG initialization error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Step 3: Embed and store documents
    print("\n" + "=" * 60)
    print("STEP 3: Generating embeddings and storing in pgvector")
    print("=" * 60)

    # Group by category
    by_category = {}
    for doc in all_documents:
        category = doc['category']
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(doc)

    total_stored = 0

    for category, docs in by_category.items():
        print(f"\n📦 Processing {category}: {len(docs)} documents")

        for i, doc in enumerate(docs, 1):
            try:
                print(f"  [{i}/{len(docs)}] {doc['title'][:50]}...")

                # Generate embedding and store
                metadata = {
                    'title': doc.get('title', 'Unknown'),
                    'source': doc.get('source', 'Unknown'),
                    'section': doc.get('section', ''),
                    'url': doc.get('url', '')
                }

                rag.add_document(
                    text=doc['text'],
                    metadata=metadata,
                    collection=category
                )

                total_stored += 1

                # Rate limiting
                if i % 5 == 0:
                    time.sleep(0.5)

            except Exception as e:
                print(f"    ❌ Error: {e}")
                # Continue with next document

    # Step 4: Show stats
    print("\n" + "=" * 60)
    print("COMPLETE: Database Statistics")
    print("=" * 60)

    print(f"  tax_law: {rag.get_collection_count('tax_law')} documents")
    print(f"  forms: {rag.get_collection_count('forms')} documents")
    print(f"  deductions: {rag.get_collection_count('deductions')} documents")
    print(f"\n✅ Successfully stored {total_stored}/{len(all_documents)} documents")
    print("   RAG database ready for queries!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
