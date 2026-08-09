"""ChromaDB backend — local persistent vector store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_PERSIST_DIR = Path("data") / "chroma"
DEFAULT_COLLECTION = "knowledge_chunks"


class ChromaStore:
    """
    Persist chunk embeddings + text + metadata in Chroma.

    Exposes a low-level similarity query used by the retrieval layer.
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

    def delete_by_filename(self, filename: str) -> int:
        """Remove chunks previously stored for this source filename."""
        if not filename:
            return 0
        existing = self._collection.get(where={"filename": filename})
        ids = existing.get("ids") or []
        # Also match basename-only legacy rows if full path was stored.
        name = Path(filename).name
        if name != filename:
            extra = self._collection.get(where={"filename": name})
            ids = list(dict.fromkeys([*ids, *(extra.get("ids") or [])]))
        if ids:
            self._collection.delete(ids=ids)
        return len(ids)

    def dedupe_by_section_key(self) -> int:
        """
        Drop duplicate rows that share the same logical section key.

        Key = filename|title + path + heading. Keeps the first id seen.
        Cleans legacy random-id re-ingests.
        """
        data = self._collection.get(include=["metadatas"])
        ids = data.get("ids") or []
        metadatas = data.get("metadatas") or []
        seen: set[str] = set()
        to_delete: list[str] = []

        for chunk_id, metadata in zip(ids, metadatas, strict=True):
            meta = metadata or {}
            source = str(meta.get("filename") or meta.get("title") or "")
            path = str(meta.get("path") or "")
            heading = str(meta.get("heading") or "")
            key = f"{source.lower()}::{path}::{heading.lower()}"
            if key in seen:
                to_delete.append(chunk_id)
            else:
                seen.add(key)

        if to_delete:
            self._collection.delete(ids=to_delete)
        return len(to_delete)

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

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Low-level nearest-neighbor query over stored embeddings."""
        n_results = max(1, min(top_k, max(self.count(), 1)))
        kwargs: dict[str, Any] = {
            "query_embeddings": [query_vector],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        result = self._collection.query(**kwargs)
        hits: list[dict[str, Any]] = []

        ids = (result.get("ids") or [[]])[0]
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        for chunk_id, document, metadata, distance in zip(
            ids, documents, metadatas, distances, strict=True
        ):
            metadata = metadata or {}
            path_raw = metadata.get("path", "[]")
            try:
                path = json.loads(path_raw) if isinstance(path_raw, str) else list(path_raw)
            except json.JSONDecodeError:
                path = [p.strip() for p in str(path_raw).split(">") if p.strip()]

            distance_f = float(distance)
            score = 1.0 - distance_f

            hits.append(
                {
                    "chunk_id": chunk_id,
                    "document_id": str(metadata.get("document_id", "")),
                    "section_id": str(metadata.get("section_id", "")),
                    "heading": str(metadata.get("heading", "")),
                    "level": int(metadata.get("level", 0)),
                    "path": path,
                    "content": document or "",
                    "score": score,
                    "distance": distance_f,
                }
            )

        return hits

    def count(self) -> int:
        return int(self._collection.count())
