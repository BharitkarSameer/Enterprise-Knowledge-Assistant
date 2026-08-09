"""ChromaDB backend — local persistent vector store (write-only for now)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

DEFAULT_PERSIST_DIR = Path("data") / "chroma"
DEFAULT_COLLECTION = "knowledge_chunks"


class ChromaStore:
    """
    Persist chunk embeddings + text + metadata in Chroma.

    Lookup / similarity search belongs in the retrieval layer later.
    Metadata values are Chroma-safe primitives (str/int/float/bool).
    `path` is stored as a JSON list string for round-tripping.
    """

    def __init__(
        self,
        persist_dir: str | Path = DEFAULT_PERSIST_DIR,
        collection_name: str = DEFAULT_COLLECTION,
    ) -> None:
        import chromadb

        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name

        self._client = chromadb.PersistentClient(path=str(self.persist_dir))
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def delete_by_document(self, document_id: str) -> int:
        """Remove existing chunks for a document before re-index."""
        existing = self._collection.get(where={"document_id": document_id})
        ids = existing.get("ids") or []
        if ids:
            self._collection.delete(ids=ids)
        return len(ids)

    def upsert(
        self,
        *,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> int:
        if not ids:
            return 0
        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        return len(ids)

    def count(self) -> int:
        return int(self._collection.count())
