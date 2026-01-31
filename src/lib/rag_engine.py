"""
Local RAG engine for German tax law queries.
Uses ChromaDB + sentence-transformers (fully local).
"""

import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path
from typing import Optional
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import VECTOR_DB_DIR, RAGConfig


class TaxRAG:
    """Local vector database for German tax law"""

    def __init__(self):
        """Initialize ChromaDB client and embedding model"""
        self.client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))

        # Load local embedding model (runs on CPU, no API needed)
        print(f"Loading embedding model: {RAGConfig.EMBEDDING_MODEL}")
        self.embedder = SentenceTransformer(RAGConfig.EMBEDDING_MODEL)

        # Get or create collections
        self.collections = {
            'tax_law': self.client.get_or_create_collection(
                name="tax_law",
                metadata={"description": "German tax code (EStG, AO)"}
            ),
            'forms': self.client.get_or_create_collection(
                name="forms",
                metadata={"description": "ELSTER form instructions"}
            ),
            'deductions': self.client.get_or_create_collection(
                name="deductions",
                metadata={"description": "Deduction rules and examples"}
            )
        }

    def query(self, question: str, collection: str = 'deductions', n_results: int = 3) -> dict:
        """
        Query the RAG database with a natural language question.

        Args:
            question: Natural language query (e.g., "Can I deduct internet costs for home office?")
            collection: Which collection to search ('tax_law', 'forms', 'deductions')
            n_results: Number of results to return

        Returns:
            Dictionary with answer, sources, and confidence
        """
        if collection not in self.collections:
            return {
                "answer": f"Unknown collection: {collection}",
                "sources": [],
                "confidence": 0.0
            }

        # Generate embedding for question
        query_embedding = self.embedder.encode([question]).tolist()

        # Search vector database
        results = self.collections[collection].query(
            query_embeddings=query_embedding,
            n_results=n_results
        )

        # Format results
        if not results['documents'] or not results['documents'][0]:
            return {
                "answer": "No relevant information found. This might be a rare tax scenario.",
                "sources": [],
                "confidence": 0.0
            }

        # Combine top results into answer
        sources = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            sources.append({
                "text": doc,
                "source": metadata.get('source', 'Unknown'),
                "section": metadata.get('section', ''),
                "confidence": 1 - distance  # Convert distance to similarity score
            })

        # Best answer is the top result
        answer = sources[0]['text'] if sources else "No information found"
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
            metadata: Metadata (source, section, year, etc.)
            collection: Which collection to add to
        """
        import uuid

        # Generate embedding
        embedding = self.embedder.encode([text]).tolist()

        # Add to collection
        self.collections[collection].add(
            embeddings=embedding,
            documents=[text],
            metadatas=[metadata],
            ids=[str(uuid.uuid4())]
        )

    def get_collection_count(self, collection: str = 'deductions') -> int:
        """Get number of documents in a collection"""
        return self.collections[collection].count()


# Global instance (lazy loaded)
_rag_instance: Optional[TaxRAG] = None


def get_rag() -> TaxRAG:
    """Get or create global RAG instance"""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = TaxRAG()
    return _rag_instance
