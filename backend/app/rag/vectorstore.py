import logging
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings
from app.rag.embeddings import ollama_embedding_function

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Manages persistent ChromaDB vector storage for CMU-Africa documents.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        self.persist_dir = persist_directory or settings.CHROMA_PERSIST_DIR
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        self._client: Optional[chromadb.PersistentClient] = None
        self._collection = None

    def _init_client(self):
        """Initialize ChromaDB persistent client."""
        if self._client is None:
            os.makedirs(self.persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=ollama_embedding_function,
                metadata={"hnsw:space": "cosine"},
            )

    @property
    def collection(self):
        self._init_client()
        return self._collection

    def count(self) -> int:
        """Return the number of documents in the collection."""
        try:
            return self.collection.count()
        except Exception as e:
            logger.warning("Error counting ChromaDB documents: %s", e)
            return 0

    def is_empty(self) -> bool:
        """Check if collection has no documents."""
        return self.count() == 0

    def add_chunks(self, chunks: List[Dict[str, Any]], batch_size: int = 50) -> int:
        """
        Add a list of document chunk dicts into ChromaDB in batches.
        """
        if not chunks:
            return 0

        self._init_client()
        total_added = 0

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            ids = [item["id"] for item in batch]
            documents = [item["text"] for item in batch]
            metadatas = [item["metadata"] for item in batch]

            logger.info("Ingesting batch %d to %d into ChromaDB...", i, i + len(batch))
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
            total_added += len(batch)

        logger.info("Successfully added %d chunks to ChromaDB collection '%s'", total_added, self.collection_name)
        return total_added

    def query(self, query_text: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Perform semantic similarity search against the collection.
        Returns a list of matching results with text and metadata.
        """
        if not query_text.strip() or self.is_empty():
            return []

        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=min(top_k, self.count()),
            )

            docs = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            ids = results.get("ids", [[]])[0]

            matches: List[Dict[str, Any]] = []
            for idx, doc_text in enumerate(docs):
                meta = metadatas[idx] if idx < len(metadatas) else {}
                dist = distances[idx] if idx < len(distances) else 0.0
                # Cosine distance to similarity: similarity = 1 - distance
                similarity = round(1.0 - dist, 4) if dist is not None else 1.0

                matches.append(
                    {
                        "id": ids[idx] if idx < len(ids) else f"match_{idx}",
                        "text": doc_text,
                        "metadata": meta,
                        "score": similarity,
                    }
                )

            return matches
        except Exception as e:
            logger.error("Error executing vector search query '%s': %s", query_text, e, exc_info=True)
            return []


vector_store = VectorStore()
