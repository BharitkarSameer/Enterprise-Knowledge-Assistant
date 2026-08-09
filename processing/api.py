"""Processing FastAPI routes."""

from fastapi import APIRouter

from shared.models import IngestionEnvelope
from processing.service import process

router = APIRouter(prefix="/process", tags=["processing"])


@router.get("/health")
async def health():
    return {"status": "ok", "layer": "processing"}


@router.post("")
async def process_document(envelope: IngestionEnvelope):
    """Process an ingestion envelope into sections + blocks."""
    return await process(envelope)
