"""Pipeline orchestration — runs index stages and emits live progress events."""

from __future__ import annotations

from typing import Any, AsyncIterator

from fastapi import UploadFile

from ingestion.service import ingest
from processing.service import process
from chunking.service import chunk
from embeddings.service import embed_chunks
from vectorstore.service import upsert

PIPELINE_STEPS = [
    "ingestion",
    "processing",
    "chunking",
    "embeddings",
    "vectorstore",
]


def _event(step: str, status: str, **detail: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"step": step, "status": status}
    if detail:
        payload["detail"] = detail
    return payload


async def iter_pipeline(file: UploadFile) -> AsyncIterator[dict[str, Any]]:
    """
    Run ingest → process → chunk → embed → upsert.
    Yields a progress event before/after each step for SSE clients.
    """
    try:
        yield _event("ingestion", "running")
        envelope = await ingest(file)
        yield _event(
            "ingestion",
            "done",
            filename=envelope.metadata.filename,
            file_type=envelope.metadata.file_type,
            document_id=envelope.metadata.document_id,
        )

        yield _event("processing", "running")
        processed = await process(envelope)
        yield _event(
            "processing",
            "done",
            title=processed.title,
            section_count=len(processed.sections),
        )

        yield _event("chunking", "running")
        chunked = await chunk(processed)
        yield _event(
            "chunking",
            "done",
            chunk_count=chunked.chunk_count,
        )

        yield _event("embeddings", "running")
        embedded = await embed_chunks(chunked)
        yield _event(
            "embeddings",
            "done",
            item_count=embedded.item_count,
            model=embedded.model,
            dimensions=embedded.dimensions,
        )

        yield _event("vectorstore", "running")
        stored = await upsert(embedded)
        yield _event(
            "vectorstore",
            "done",
            upserted=stored.upserted,
            collection=stored.collection,
            persist_dir=stored.persist_dir,
        )

        yield {
            "step": "complete",
            "status": "done",
            "summary": {
                "document_id": embedded.document_id,
                "title": embedded.title,
                "filename": envelope.metadata.filename,
                "section_count": len(processed.sections),
                "chunk_count": chunked.chunk_count,
                "embedded": embedded.item_count,
                "stored": stored.upserted,
                "model": embedded.model,
                "dimensions": embedded.dimensions,
                "collection": stored.collection,
                "persist_dir": stored.persist_dir,
            },
        }
    except Exception as exc:  # noqa: BLE001 - surface to SSE client
        yield {
            "step": "error",
            "status": "error",
            "detail": {"message": str(exc)},
        }


async def run_pipeline(file: UploadFile) -> dict[str, Any]:
    """Run the full pipeline and return the final summary (non-streaming)."""
    summary: dict[str, Any] = {}
    async for event in iter_pipeline(file):
        if event.get("step") == "complete":
            summary = event.get("summary") or {}
        if event.get("status") == "error":
            raise RuntimeError(
                (event.get("detail") or {}).get("message", "Pipeline failed")
            )
    return summary
