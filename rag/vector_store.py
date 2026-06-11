"""
StartupPilot AI — Vector Store

ChromaDB wrapper for storing and querying document embeddings.
Uses Sentence Transformers (all-MiniLM-L6-v2) for local embeddings.

Interview talking point:
    "I use ChromaDB as a persistent vector store with Sentence Transformer
     embeddings. Documents are chunked, embedded locally, and stored per-project.
     Agents query relevant context using semantic similarity search."
"""

import logging
import time
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.utils import embedding_functions
from langchain_core.documents import Document

from config import get_settings

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB-backed vector store for RAG.

    Each project gets its own collection, enabling project-scoped
    retrieval. Uses Sentence Transformers for embedding.

    Usage:
        store = VectorStore()
        store.add_documents("project-123", documents)
        results = store.query("project-123", "AI scheduling market size", top_k=5)
    """

    def __init__(self, persist_dir: Optional[str] = None) -> None:
        settings = get_settings()
        self._persist_dir = Path(persist_dir or settings.chroma_persist_dir)
        self._persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB persistent client
        self._client = chromadb.PersistentClient(
            path=str(self._persist_dir)
        )

        # Initialize Sentence Transformer embedding function
        self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model
        )

        logger.info(
            "VectorStore initialized. Persist: %s, Embedding: %s",
            self._persist_dir,
            settings.embedding_model,
        )
        self.prune_old_collections(max_age_days=7)
    def _get_collection(self, project_id: str) -> chromadb.Collection:
        """Get or create a collection for a project."""
        # Sanitize collection name (ChromaDB requirements)
        collection_name = f"project_{project_id.replace('-', '_')[:50]}"
        return self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._embedding_fn,
            metadata={"project_id": project_id, "created_at": time.time()},
        )
    def add_documents(
        self,
        project_id: str,
        documents: list[Document],
    ) -> int:
        """Add documents to the vector store for a project.

        Args:
            project_id: The project ID to scope the documents.
            documents: List of LangChain Document objects (already chunked).

        Returns:
            Number of documents added.
        """
        if not documents:
            logger.warning("No documents to add for project %s", project_id)
            return 0

        collection = self._get_collection(project_id)

        # Prepare data for ChromaDB
        ids = []
        texts = []
        metadatas = []

        for i, doc in enumerate(documents):
            doc_id = f"{project_id}_doc_{i}"
            ids.append(doc_id)
            texts.append(doc.page_content)
            metadatas.append({
                k: str(v) for k, v in doc.metadata.items()
                if isinstance(v, (str, int, float, bool))
            })

        # Upsert to handle duplicates gracefully
        collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
        )

        logger.info(
            "Added %d documents to project %s (collection: %s)",
            len(documents),
            project_id,
            collection.name,
        )

        return len(documents)

    def query(
        self,
        project_id: str,
        query_text: str,
        top_k: Optional[int] = None,
    ) -> list[dict]:
        """Query the vector store for relevant documents.

        Args:
            project_id: The project ID to search within.
            query_text: The search query.
            top_k: Number of results to return.

        Returns:
            List of dicts with keys: "content", "metadata", "distance"
        """
        settings = get_settings()
        k = top_k or settings.retrieval_top_k

        collection = self._get_collection(project_id)

        # Check if collection has any documents
        if collection.count() == 0:
            logger.debug("No documents in collection for project %s", project_id)
            return []

        # Query ChromaDB
        results = collection.query(
            query_texts=[query_text],
            n_results=min(k, collection.count()),
        )

        # Format results
        formatted = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                formatted.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                })

        logger.info(
            "Query '%s...' returned %d results for project %s",
            query_text[:50],
            len(formatted),
            project_id,
        )

        return formatted

    def get_collection_stats(self, project_id: str) -> dict:
        """Get statistics for a project's document collection."""
        collection = self._get_collection(project_id)
        return {
            "project_id": project_id,
            "collection_name": collection.name,
            "document_count": collection.count(),
        }

    def delete_project(self, project_id: str) -> None:
        """Delete all documents for a project."""
        collection_name = f"project_{project_id.replace('-', '_')[:50]}"
        try:
            self._client.delete_collection(collection_name)
            logger.info("Deleted collection for project %s", project_id)
        except Exception as e:
            logger.warning("Could not delete collection: %s", e)

    def list_collections(self) -> list[str]:
        """List all project collections in the vector store."""
        collections = self._client.list_collections()
        return [c.name for c in collections]

    def prune_old_collections(self, max_age_days: int = 7) -> None:
        """Prune collections that are older than max_age_days and not in active use."""
        try:
            collections = self._client.list_collections()
            now = time.time()
            cutoff = now - (max_age_days * 86400)
            
            for col in collections:
                # Do not delete demo collections
                if col.name == "project_demo_healthcare":
                    continue
                    
                meta = col.metadata or {}
                created_at = meta.get("created_at")
                
                if created_at is not None:
                    try:
                        created_at = float(created_at)
                        if created_at < cutoff:
                            logger.info("Pruning old collection: %s", col.name)
                            self._client.delete_collection(col.name)
                    except ValueError:
                        pass
        except Exception as e:
            logger.warning("Failed to prune old collections: %s", e)
