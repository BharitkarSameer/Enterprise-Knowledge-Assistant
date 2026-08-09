"""
Core vector store logic.

Persists embedded chunks (vector + full content + citation metadata).
Similarity lookup belongs in the retrieval layer.
"""

from __future__ import annotations

import asyncio
import json

from embeddings.models import EmbeddingResult
from vectorstore.chroma import ChromaStore, DEFAULT_COLLECTION, DEFAULT_PERSIST_DIR
from vectorstore.models import UpsertResult

_store: ChromaStore | None = None


def get_store(
    persist_dir: str | None = None,
    collection_name: str = DEFAULT_COLLECTION,
) -> ChromaStore:
    global _store
    if _store is None or (
        persist_dir is not None and str(_store.persist_dir) != str(persist_dir)
    ):
        _store = ChromaStore(
            persist_dir=persist_dir or DEFAULT_PERSIST_DIR,
            collection_name=collection_name,
        )
    return _store


def _to_metadata(item, *, title: str | None, model: str) -> dict:
    return {
        "document_id": item.document_id,
        "section_id": item.section_id,
        "heading": item.heading,
        "level": item.level,
        "path": json.dumps(item.path),
        "title": title or "",
        "model": model,
        "char_count": item.char_count,
    }


async def upsert(
    embedded: EmbeddingResult | dict,
    *,
    replace_document: bool = True,
    persist_dir: str | None = None,
) -> UpsertResult:
    """
    Store embedded chunks in Chroma.

    By default, deletes existing rows for the same document_id first
    so re-running the pipeline does not leave orphan chunks.
    """
    if isinstance(embedded, dict):
        embedded = EmbeddingResult.model_validate(embedded)

    store = get_store(persist_dir=persist_dir)

    def _write() -> UpsertResult:
        if replace_document:
            store.delete_by_document(embedded.document_id)

        ids = [item.chunk_id for item in embedded.items]
        embeddings = [item.embedding for item in embedded.items]
        documents = [item.content for item in embedded.items]
        metadatas = [
            _to_metadata(item, title=embedded.title, model=embedded.model)
            for item in embedded.items
        ]

        count = store.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        return UpsertResult(
            document_id=embedded.document_id,
            collection=store.collection_name,
            upserted=count,
            persist_dir=str(store.persist_dir),
        )

    return await asyncio.to_thread(_write)
