"""Chunking FastAPI routes."""

from fastapi import APIRouter

from processing.models import ProcessingResult
from chunking.service import chunk

router = APIRouter(prefix="/chunk", tags=["chunking"])


@router.get("/health")
async def health():
    return {"status": "ok", "layer": "chunking"}


@router.post("")
async def chunk_document(processed: ProcessingResult):
    """Turn processed sections into embeddable chunks."""
    return await chunk(processed)
