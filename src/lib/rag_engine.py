"""
Local RAG engine for German tax law queries.
Uses PostgreSQL + pgvector + Gemini API embeddings.
"""

import psycopg2
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector
import google.generativeai as genai
from pathlib import Path
from typing import Optional, List, Dict
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(str(Path(__file__).parent.parent))
from config import RAGConfig

# Database connection settings
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'german_tax',
    'user': 'tax_user',
    'password': 'tax_password_local_only'
}


class TaxRAG:
    """Local vector database for German tax law using pgvector + Gemini embeddings"""

    def __init__(self):
        """Initialize PostgreSQL connection and Gemini API"""
        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables. Please add it to .env file")

        genai.configure(api_key=api_key)
        print(f"✅ Gemini API configured (embedding-001, 768 dimensions)")

        self.embedding_dim = 768  # Gemini embedding-001 dimension

        # Connect to PostgreSQL
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()

        # Enable pgvector extension FIRST
        self.cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        self.conn.commit()

        # Now register vector type with psycopg2
        register_vector(self.conn)

        # Create tables if not exist
        self._init_tables()

    def _init_tables(self):
        """Create vector tables for each collection"""
        collections = ['tax_law', 'forms', 'deductions']

        for collection in collections:
            # Drop old full-text search table if exists
            self.cursor.execute(f"""
                DROP TABLE IF EXISTS {collection} CASCADE
            """)

            # Create new vector table
            self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {collection} (
                    id SERIAL PRIMARY KEY,
                    title TEXT,
                    text TEXT NOT NULL,
                    url TEXT,
                    section TEXT,
                    embedding vector({self.embedding_dim}),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index for fast vector search
            self.cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS {collection}_embedding_idx
                ON {collection} USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)

        self.conn.commit()
        print("✅ pgvector tables created")

    def _text_to_embedding(self, text: str) -> List[float]:
        """Convert text to embedding using Gemini API"""
        result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']

    def _query_to_embedding(self, query: str) -> List[float]:
        """Convert query to embedding using Gemini API"""
        result = genai.embed_content(
            model="models/embedding-001",
            content=query,
            task_type="retrieval_query"
        )
        return result['embedding']

    def query(self, question: str, collection: str = 'deductions', n_results: int = 3) -> dict:
        """
        Query the RAG database with a natural language question.

        Args:
            question: Natural language query
            collection: Which collection to search ('tax_law', 'forms', 'deductions')
            n_results: Number of results to return

        Returns:
            Dictionary with answer, sources, and confidence
        """
        if collection not in ['tax_law', 'forms', 'deductions']:
            return {
                "answer": f"Unknown collection: {collection}",
                "sources": [],
                "confidence": 0.0
            }

        # Generate embedding for question using Gemini
        query_embedding = self._query_to_embedding(question)

        # Search vector database using cosine similarity
        self.cursor.execute(f"""
            SELECT title, text, url, section, metadata, 1 - (embedding <=> %s::vector) as similarity
            FROM {collection}
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (query_embedding, query_embedding, n_results))

        results = self.cursor.fetchall()

        if not results:
            return {
                "answer": "No relevant information found. This might be a rare tax scenario.",
                "sources": [],
                "confidence": 0.0
            }

        # Format results
        sources = []
        for title, text, url, section, metadata, similarity in results:
            if metadata is None:
                metadata = {}

            # Extract snippet
            snippet = text[:300] + "..." if len(text) > 300 else text

            sources.append({
                "text": snippet,
                "title": title if title else "Unknown",
                "section": section if section else "",
                "source": metadata.get('source', 'Unknown') if isinstance(metadata, dict) else 'Unknown',
                "url": url if url else "",
                "confidence": float(similarity) if similarity else 0.0
            })

        # Best answer is the top result
        answer = results[0][1] if results else "No information found"
        avg_confidence = sum(s['confidence'] for s in sources) / len(sources) if sources else 0.0

        return {
            "answer": answer,
            "sources": sources,
            "confidence": round(avg_confidence, 2)
        }

    def add_document(self, text: str, metadata: dict, collection: str = 'deductions'):
        """
        Add a document to the RAG database.

        Args:
            text: Document text to embed
            metadata: Metadata (source, section, url, etc.)
            collection: Which collection to add to
        """
        # Generate embedding using Gemini
        embedding = self._text_to_embedding(text)

        # Extract fields from metadata
        title = metadata.get('title', '')
        url = metadata.get('url', '')
        section = metadata.get('section', '')

        # Add to database
        self.cursor.execute(f"""
            INSERT INTO {collection} (title, text, url, section, embedding, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (title, text, url, section, embedding, psycopg2.extras.Json(metadata)))

        self.conn.commit()

    def get_collection_count(self, collection: str = 'deductions') -> int:
        """Get number of documents in a collection"""
        try:
            self.cursor.execute(f"SELECT COUNT(*) FROM {collection}")
            return self.cursor.fetchone()[0]
        except:
            return 0

    def clear_collection(self, collection: str):
        """Clear all documents from a collection"""
        self.cursor.execute(f"DELETE FROM {collection}")
        self.conn.commit()

    def __del__(self):
        """Close database connection on cleanup"""
        if hasattr(self, 'cursor'):
            self.cursor.close()
        if hasattr(self, 'conn'):
            self.conn.close()


# Global instance (lazy loaded)
_rag_instance: Optional[TaxRAG] = None


def get_rag() -> TaxRAG:
    """Get or create global RAG instance"""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = TaxRAG()
    return _rag_instance
