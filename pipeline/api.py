"""Pipeline FastAPI routes — live SSE progress for indexing."""

from __future__ import annotations

import json

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import StreamingResponse

from pipeline.service import PIPELINE_STEPS, iter_pipeline

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/steps")
async def list_steps():
    """Step order the UI should render."""
    return {"steps": PIPELINE_STEPS}


@router.post("/ingest")
async def ingest_pipeline(file: UploadFile = File(...)):
    """
    Upload a document and stream indexing progress as Server-Sent Events.

    Each event looks like:
      {"step": "ingestion", "status": "running"|"done"|"error", "detail": {...}}
    Final success event:
      {"step": "complete", "status": "done", "summary": {...}}
    """

    async def event_stream():
        async for event in iter_pipeline(file):
            yield _sse(event)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
