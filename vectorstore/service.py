"""
Core vector store logic.

Persists embedded chunks and exposes low-level similarity search
for the retrieval layer to orchestrate.
"""

from __future__ import annotations

import asyncio
import json

from embeddings.models import EmbeddingResult
from vectorstore.chroma import ChromaStore, DEFAULT_COLLECTION, DEFAULT_PERSIST_DIR
from vectorstore.models import SearchHit, UpsertResult

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


def _to_metadata(item, *, title: str | None, filename: str | None, model: str) -> dict:
    return {
        "document_id": item.document_id,
        "section_id": item.section_id,
        "heading": item.heading,
        "level": item.level,
        "path": json.dumps(item.path),
        "title": title or "",
        "filename": filename or "",
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

    By default, deletes existing rows for the same document_id / filename
    first so re-running the pipeline does not leave orphan chunks.
    Also collapses legacy duplicates that share the same section key.
    """
    if isinstance(embedded, dict):
        embedded = EmbeddingResult.model_validate(embedded)

    store = get_store(persist_dir=persist_dir)

    def _write() -> UpsertResult:
        if replace_document:
            store.delete_by_document(embedded.document_id)
            if embedded.filename:
                store.delete_by_filename(embedded.filename)

        ids = [item.chunk_id for item in embedded.items]
        embeddings = [item.embedding for item in embedded.items]
        documents = [item.content for item in embedded.items]
        metadatas = [
            _to_metadata(
                item,
                title=embedded.title,
                filename=embedded.filename,
                model=embedded.model,
            )
            for item in embedded.items
        ]

        count = store.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        # Clean any leftover random-id duplicates from older ingestions.
        store.dedupe_by_section_key()
        return UpsertResult(
            document_id=embedded.document_id,
            collection=store.collection_name,
            upserted=count,
            persist_dir=str(store.persist_dir),
        )

    return await asyncio.to_thread(_write)


async def search(
    query_vector: list[float],
    top_k: int = 5,
    *,
    document_id: str | None = None,
    persist_dir: str | None = None,
) -> list[SearchHit]:
    """Low-level vector similarity search (used by retrieval)."""
    store = get_store(persist_dir=persist_dir)
    where = {"document_id": document_id} if document_id else None

    def _query() -> list[SearchHit]:
        raw = store.search(query_vector, top_k=top_k, where=where)
        return [SearchHit.model_validate(item) for item in raw]

    return await asyncio.to_thread(_query)
